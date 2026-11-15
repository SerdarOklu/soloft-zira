"""SQLAlchemy models for the 16 tables of PDT section 9.

Importing this package registers every table on ``Base.metadata``; Alembic and the
tests rely on that.
"""

from app.models.accounts import Organization, OrganizationType, Role, User
from app.models.analysis import (
    AnalysisRun,
    RotationScenario,
    SoilWaterBalance,
    Strategy,
    Variant,
    ZiraCard,
)
from app.models.base import Base
from app.models.data import (
    DataFetchJob,
    DataSource,
    JobStatus,
    RegionalObservation,
    SatelliteObservation,
    SensorCalibration,
    SensorObservation,
    WeatherObservation,
)
from app.models.fields import (
    CropCycle,
    CropType,
    CycleSource,
    CycleState,
    FarmerConstraint,
    Field,
    SeasonType,
    SoilProfile,
    WaterRegime,
)
from app.models.messages import MessageDraft

__all__ = [
    "AnalysisRun",
    "Base",
    "CropCycle",
    "CropType",
    "CycleSource",
    "CycleState",
    "DataFetchJob",
    "DataSource",
    "FarmerConstraint",
    "Field",
    "JobStatus",
    "MessageDraft",
    "Organization",
    "OrganizationType",
    "Role",
    "RotationScenario",
    "RegionalObservation",
    "SatelliteObservation",
    "SeasonType",
    "SensorCalibration",
    "SensorObservation",
    "SoilProfile",
    "SoilWaterBalance",
    "Strategy",
    "User",
    "Variant",
    "WaterRegime",
    "WeatherObservation",
    "ZiraCard",
]
