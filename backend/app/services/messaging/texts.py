"""The words of a draft: templates from config/message_templates.yaml filled with the numbers."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.core.parameters import Config
from app.schemas.rotation import RotationOut
from app.services.messaging.events import Event

LOCALES = ("tr", "en")


def _number(value: float) -> str:
    return str(round(value))


def _date(day: date, locale: str, config: Config) -> str:
    return f"{day.day} {config.messages.months[locale][day.month - 1]} {day.year}"


def crop_name(key: str | None, locale: str, config: Config) -> str:
    if key is None:
        return ""
    if locale == "tr":
        crop = config.crops.get(key)
        return crop.name_tr if crop else key
    return config.messages.crop_names_en.get(key, key)


def _mid_sentence(name: str) -> str:
    return name[:1].lower() + name[1:]


def _template(config: Config, name: str, locale: str) -> str:
    return config.messages.templates[name][locale]


def render(
    event: Event,
    *,
    locale: str,
    config: Config,
    field_name: str,
    comparison: RotationOut | None = None,
) -> str:
    """The message for ``event``. Raises KeyError for a type with no template."""
    if locale not in LOCALES:
        raise ValueError(f"Unsupported language: {locale}")
    payload = event.payload
    when = _date(event.day, locale, config)
    disclaimer = config.messages.disclaimer[locale]

    if event.type == "decision":
        kind = "crop" if payload["planned_crop"] is not None else "fallow"
        level = "ok" if payload["above_threshold"] else "low"
        body = _template(config, f"decision_{kind}_{level}", locale).format(
            date=when,
            storage=_number(payload["storage_mm"]),
            taw=_number(payload["taw_mm"]),
            threshold=_number(payload["threshold_mm"]),
            crop=_mid_sentence(crop_name(payload["planned_crop"], locale, config)),
        )
        return f"{body}\n\n{disclaimer}"
    if event.type == "heavy_rain":
        return _template(config, "heavy_rain", locale).format(
            date=when,
            rain=_number(payload["rain_mm"]),
            storage=_number(payload["storage_mm"]),
            taw=_number(payload["taw_mm"]),
        )
    if event.type == "leaching":
        return _template(config, "leaching", locale).format(
            date=when, drained=_number(payload["drained_mm"])
        )
    if event.type == "stress":
        return _template(config, "stress", locale).format(
            date=when, crop=crop_name(payload["crop"], locale, config), days=payload["days"]
        )
    if event.type == "harvest":
        name = "harvest_ok" if payload["sufficient"] else "harvest_short"
        return _template(config, name, locale).format(
            date=when,
            crop=crop_name(payload["crop"], locale, config),
            pct=_number(payload["ratio"] * 100),
            days=payload["stress_days"],
        )
    if event.type == "card":
        if comparison is None:
            raise ValueError("The field card needs the rotation comparison")
        return _card(event, locale, config, field_name, comparison, when, disclaimer)
    raise KeyError(event.type)


def _strategy_name(key: str, comparison: RotationOut, locale: str, config: Config) -> str:
    if key == "B":
        return _template(config, "card_flexible_name", locale)
    sown = next(s for s in comparison.strategies if s.key == key).crops
    names = [crop_name(crop, locale, config) for crop in sown]
    if key == "A" and None in comparison.rotation:
        names.append("nadas" if locale == "tr" else "fallow")
    if key == "C":
        # A's crops first, then the legume it adds.
        ordered = [c for c in comparison.rotation if c and c in sown]
        ordered += [c for c in sown if c not in ordered]
        names = [crop_name(crop, locale, config) for crop in ordered]
    # Only the first name keeps its capital: "Kışlık buğday – mercimek".
    names = [n if i == 0 else n[:1].lower() + n[1:] for i, n in enumerate(names)]
    return " – ".join(names)


def _card(
    event: Event,
    locale: str,
    config: Config,
    field_name: str,
    comparison: RotationOut,
    when: str,
    disclaimer: str,
) -> str:
    payload: dict[str, Any] = event.payload
    lines = [
        _template(config, "card_head", locale).format(
            date=when,
            field=field_name,
            storage=_number(payload["storage_mm"]),
            taw=_number(payload["taw_mm"]),
        ),
        "",
    ]
    for strategy in comparison.strategies:
        m = strategy.metrics
        lines.append(
            _template(config, "card_line", locale).format(
                key=strategy.key,
                name=_strategy_name(strategy.key, comparison, locale, config),
                valid=m.valid,
                sufficient=m.sufficient,
                low=m.sufficient_low,
                high=m.sufficient_high,
            )
        )
    lines += ["", _template(config, "card_unchecked", locale)]
    if comparison.provisional:
        lines.append(_template(config, "card_provisional", locale))
    lines += ["", f"_{disclaimer}_"]
    return "\n".join(lines)
