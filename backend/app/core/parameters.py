"""Loads and validates the files in ``config/``.

The parameter sheet is the source of truth; ``config/*.yaml`` mirrors it and this
module is the only place the backend reads those files. Nothing here computes
anything: it checks shape and ranges so a bad edit fails at start-up, not mid-run.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Basis = Literal["fao56", "zira_definition", "team_assumption", "design_decision"]
Status = Literal["set", "needs_signoff", "to_be_set", "optional"]
Range = tuple[float, float]


class Parameter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Any = None
    unit: str | None = None
    basis: Basis
    status: Status
    note: str | None = None

    @model_validator(mode="after")
    def _value_matches_status(self) -> Parameter:
        if self.status in ("set", "needs_signoff") and self.value is None:
            raise ValueError(f"status '{self.status}' requires a value")
        if self.status == "to_be_set" and self.value is not None:
            raise ValueError("status 'to_be_set' must not carry a value")
        return self


class ParameterSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_version: str
    core: dict[str, Parameter]
    corrections: dict[str, Parameter]
    field_memory: dict[str, Parameter]
    sensors: dict[str, Parameter]
    power_request: dict[str, Parameter]

    def groups(self) -> dict[str, dict[str, Parameter]]:
        return {
            "core": self.core,
            "corrections": self.corrections,
            "field_memory": self.field_memory,
            "sensors": self.sensors,
            "power_request": self.power_request,
        }

    def get(self, group: str, name: str) -> Any:
        return self.groups()[group][name].value

    def unset(self) -> list[str]:
        """Names of parameters an analysis cannot run without."""
        return [
            f"{group}.{name}"
            for group, params in self.groups().items()
            for name, param in params.items()
            if param.status == "to_be_set"
        ]

    def needing_signoff(self) -> list[str]:
        return [
            f"{group}.{name}"
            for group, params in self.groups().items()
            for name, param in params.items()
            if param.status == "needs_signoff"
        ]


class WheatKcIni(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frozen_soil: float
    non_frozen_soil: float


class Crop(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_tr: str
    season_type: Literal["winter", "summer", "perennial"] | None
    is_legume: bool
    kc_ini: float | WheatKcIni
    kc_mid: float | Range
    kc_end: float | Range
    height_m: float = Field(gt=0)
    zr_m: Range
    p: float = Field(gt=0, lt=1)
    stage_lengths_days: list[int] | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _ranges_ordered(self) -> Crop:
        for name in ("kc_mid", "kc_end", "zr_m"):
            value = getattr(self, name)
            if isinstance(value, tuple) and value[0] > value[1]:
                raise ValueError(f"{name}: low bound is above high bound")
        if self.stage_lengths_days is not None and len(self.stage_lengths_days) != 4:
            raise ValueError("stage_lengths_days needs four values: ini, dev, mid, late")
        return self


class Soil(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_tr: str
    taw_mm_per_m: Range
    rew_mm: Range

    @model_validator(mode="after")
    def _ranges_ordered(self) -> Soil:
        for name in ("taw_mm_per_m", "rew_mm"):
            low, high = getattr(self, name)
            if low > high:
                raise ValueError(f"{name}: low bound is above high bound")
        return self

    @property
    def taw_mid(self) -> float:
        low, high = self.taw_mm_per_m
        return (low + high) / 2


class ClimateProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_tr: str
    example: str | None = None
    implemented: bool
    dominant_risk: str
    enables: list[str]
    overrides: dict[str, str] = Field(default_factory=dict)


class SiteCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enables: list[str]
    data_source: str
    note: str | None = None


class ClimateProfiles(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_profile: str
    profiles: dict[str, ClimateProfile]
    site_conditions: dict[str, SiteCondition]

    @model_validator(mode="after")
    def _default_exists_and_is_implemented(self) -> ClimateProfiles:
        default = self.profiles.get(self.default_profile)
        if default is None:
            raise ValueError(f"default_profile '{self.default_profile}' is not defined")
        if not default.implemented:
            raise ValueError("default_profile must be an implemented profile")
        return self


class DataSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    role: str
    access: Literal["power_daily_api", "stac_cog", "earth_engine"]
    collection_id: str | None = None
    collection_id_before_2023_12_04: str | None = None
    resolution: str
    priority: Literal["first", "high", "medium", "optional"]
    scale_warning: str


class DemoIrrigation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float = Field(gt=0, le=1)
    basis: Basis
    note: str | None = None


class DemoCrop(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sowing_date: str = Field(pattern=r"^\d{2}-\d{2}$")
    stage_lengths_days: list[int] = Field(min_length=4, max_length=4)
    kc_ini_variant: Literal["frozen_soil", "non_frozen_soil"] | None = None
    source: str


class DemoThreshold(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float = Field(gt=0, lt=1)
    basis: Basis
    note: str | None = None


class RotationDemo(BaseModel):
    """Provisional season values for the rotation comparison (config/rotation_demo.yaml)."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["provisional_demo"]
    strategy_c_legume: str
    irrigation_efficiency: DemoIrrigation
    ndvi_cropped_threshold: DemoThreshold
    crops: dict[str, DemoCrop]


class MessageValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Any


class MessageTemplates(BaseModel):
    """Draft WhatsApp texts and the events that raise them (config/message_templates.yaml)."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["draft_texts"]
    thresholds: dict[str, MessageValue]
    months: dict[str, list[str]]
    crop_names_en: dict[str, str]
    disclaimer: dict[str, str]
    templates: dict[str, dict[str, str]]

    @model_validator(mode="after")
    def _every_template_has_both_languages(self) -> MessageTemplates:
        for name, texts in self.templates.items():
            if set(texts) != {"tr", "en"}:
                raise ValueError(f"template '{name}' needs exactly tr and en")
        for lang in ("tr", "en"):
            if len(self.months.get(lang, [])) != 12:
                raise ValueError(f"months.{lang} needs 12 names")
        return self


class Config(BaseModel):
    parameters: ParameterSet
    crops: dict[str, Crop]
    soils: dict[str, Soil]
    climate: ClimateProfiles
    data_sources: dict[str, DataSource]
    rotation_demo: RotationDemo
    messages: MessageTemplates

    @model_validator(mode="after")
    def _cross_references(self) -> Config:
        legume = self.parameters.get("core", "legume_crop")
        if legume not in self.crops:
            raise ValueError(f"core.legume_crop '{legume}' is not in crops.yaml")
        if not self.crops[legume].is_legume:
            raise ValueError(f"core.legume_crop '{legume}' is not marked as a legume")
        demo_legume = self.rotation_demo.strategy_c_legume
        if demo_legume not in self.crops or not self.crops[demo_legume].is_legume:
            raise ValueError(f"rotation_demo.strategy_c_legume '{demo_legume}' is not a legume")
        for key in self.rotation_demo.crops:
            if key not in self.crops:
                raise ValueError(f"rotation_demo crop '{key}' is not in crops.yaml")
        return self


def _read(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_config(config_dir: Path) -> Config:
    return Config(
        parameters=ParameterSet(**_read(config_dir / "parameters.yaml")),
        crops=_read(config_dir / "crops.yaml")["crops"],
        soils=_read(config_dir / "soils.yaml")["soils"],
        climate=ClimateProfiles(**_read(config_dir / "climate_profiles.yaml")),
        data_sources=_read(config_dir / "data_sources.yaml")["sources"],
        rotation_demo=RotationDemo(**_read(config_dir / "rotation_demo.yaml")),
        messages=MessageTemplates(**_read(config_dir / "message_templates.yaml")),
    )


@lru_cache
def get_config() -> Config:
    from app.core.config import get_settings

    return load_config(get_settings().config_dir)
