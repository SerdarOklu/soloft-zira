"""Message drafts: write them from the model's events, approve them, send the approved ones.

Zira never sends on its own. A draft waits for an agronomist (or an admin); only an approved
draft goes to the farmer, and only when the WhatsApp gateway is configured on the server.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.parameters import Config
from app.models import Field, MessageDraft, User
from app.services.messaging import texts
from app.services.messaging.events import Thresholds, detect_events
from app.services.messaging.greenapi import (
    GatewayError,
    GreenApiClient,
    normalise_phone,
)
from app.services.water.rotation import simulate
from app.services.water.rotation_service import rotation_comparison
from app.services.water.vault import VaultError

PENDING, APPROVED, SENT, REJECTED, FAILED = "pending", "approved", "sent", "rejected", "failed"


class DraftError(Exception):
    """A draft action that cannot be done; ``code`` is shown to the user in their language."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _thresholds(config: Config) -> Thresholds:
    values = config.messages.thresholds
    return Thresholds(
        heavy_rain_mm=float(values["heavy_rain_mm"].value),
        leaching_mm=float(values["leaching_mm"].value),
        stress_day_marks=tuple(int(v) for v in values["stress_day_marks"].value),
    )


def generate_drafts(
    session: Session,
    field: Field,
    *,
    rotation: list[str | None],
    season_year: int,
    locale: str,
    recipient_phone: str | None,
    config: Config,
) -> tuple[list[MessageDraft], int]:
    """Write drafts for the events of the season that starts on the decision day of
    ``season_year``. Events that already have a draft are skipped. Returns the new drafts and
    the number skipped."""
    if locale not in texts.LOCALES:
        raise DraftError("unsupported_locale")
    phone = normalise_phone(recipient_phone) if recipient_phone else None

    inputs: dict = {}
    comparison = rotation_comparison(session, field, rotation, config, inputs_out=inputs)
    days = inputs["days"]
    plan_a = inputs["plan_a"]
    years = inputs["years"]
    crops = inputs["crops"]
    params = inputs["middle_params"]
    decision = (inputs["decision_month"], inputs["decision_day"])

    start = date(season_year, *decision)
    last_day = days[-1]
    if start > last_day or start < days[0]:
        raise VaultError(
            "season_outside_record", first_date=days[0].isoformat(), last_date=last_day.isoformat()
        )
    end = min(date(season_year + 1, *decision) - timedelta(days=1), last_day)

    trace: list = []
    results = simulate(
        days, inputs["rain"], inputs["et0"], crops=crops, plan=plan_a, params=params, trace=trace
    )

    def crop_for_year(year: int) -> str | None:
        if year in plan_a:
            return plan_a[year]
        return rotation[(year - years[0]) % len(rotation)]

    events = detect_events(
        trace,
        results,
        window=(start, end),
        crop_for_year=crop_for_year,
        decision=decision,
        taw_mm=inputs["reference_taw"],
        flex_threshold_mm=inputs["flex_threshold_mm"],
        thresholds=_thresholds(config),
        season_lengths={key: crop.length for key, crop in crops.items()},
        sowing_dates={key: (crop.sow_month, crop.sow_day) for key, crop in crops.items()},
        sufficient_for=lambda result: result.is_sufficient(params),
        with_card=end == last_day,
    )

    existing = {
        (row.event_type, row.event_date)
        for row in session.execute(
            select(MessageDraft.event_type, MessageDraft.event_date).where(
                MessageDraft.field_id == field.id
            )
        )
    }
    created: list[MessageDraft] = []
    skipped = 0
    for event in events:
        if (event.type, event.day) in existing:
            skipped += 1
            continue
        draft = MessageDraft(
            field_id=field.id,
            event_type=event.type,
            event_date=event.day,
            locale=locale,
            body=texts.render(
                event, locale=locale, config=config, field_name=field.name, comparison=comparison
            ),
            payload={k: v for k, v in event.payload.items()},
            status=PENDING,
            recipient_phone=phone,
        )
        session.add(draft)
        created.append(draft)
    session.flush()
    return created, skipped


def edit(draft: MessageDraft, *, body: str | None, recipient_phone: str | None) -> None:
    if draft.status not in (PENDING, FAILED):
        raise DraftError("not_editable")
    if body is not None:
        if not body.strip():
            raise DraftError("empty_body")
        draft.body = body.strip()
    if recipient_phone is not None:
        draft.recipient_phone = normalise_phone(recipient_phone) if recipient_phone else None


def reject(draft: MessageDraft, user: User) -> None:
    if draft.status not in (PENDING, FAILED, APPROVED):
        raise DraftError("not_rejectable")
    draft.status = REJECTED
    draft.decided_by = user.id
    draft.decided_at = datetime.now(UTC)


def approve(draft: MessageDraft, user: User, *, gateway: GreenApiClient | None) -> None:
    """Approve and try to send. Without a gateway the draft stays approved and waits."""
    if draft.status not in (PENDING, FAILED):
        raise DraftError("not_approvable")
    if not draft.recipient_phone:
        raise DraftError("no_recipient")
    draft.status = APPROVED
    draft.decided_by = user.id
    draft.decided_at = datetime.now(UTC)
    draft.error = None
    send(draft, gateway=gateway)


def send(draft: MessageDraft, *, gateway: GreenApiClient | None) -> None:
    """Send an approved draft. A failure is recorded on the draft, not raised."""
    if draft.status not in (APPROVED, FAILED):
        raise DraftError("not_sendable")
    if not draft.recipient_phone:
        raise DraftError("no_recipient")
    if gateway is None:
        draft.status = APPROVED
        draft.error = "gateway_not_configured"
        return
    try:
        draft.provider_message_id = gateway.send_text(draft.recipient_phone, draft.body)
    except (GatewayError, ValueError) as error:
        draft.status = FAILED
        draft.error = str(error)
        return
    draft.status = SENT
    draft.sent_at = datetime.now(UTC)
    draft.error = None


def get_draft(session: Session, draft_id: uuid.UUID) -> MessageDraft | None:
    return session.get(MessageDraft, draft_id)
