"""The files in config/ must load, and must still say what the PDT says."""

import pytest
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.parameters import Parameter, Soil, load_config


@pytest.fixture(scope="module")
def config():
    return load_config(get_settings().config_dir)


def test_config_loads(config):
    assert config.parameters.model_version


def test_core_defaults_match_pdt(config):
    get = config.parameters.get
    assert get("core", "n_seasons") == 25
    assert get("core", "history_years") == 10
    assert get("core", "eff_rain_fraction") == 0.80
    assert get("core", "fallow_efficiency") == 0.25
    assert get("core", "sufficiency_ratio") == 0.70
    assert get("core", "precip_source") in {"power", "gpm"}


def test_fao_reference_conditions(config):
    get = config.parameters.get
    assert get("corrections", "kc_ref_rh_min") == 45
    assert get("corrections", "kc_ref_u2") == 2.0
    assert get("corrections", "p_min") < get("corrections", "p_max")


def test_ndvi_threshold_is_flagged_unset(config):
    assert "field_memory.ndvi_cropped_threshold" in config.parameters.unset()


def test_team_assumptions_are_not_marked_final(config):
    for group, params in config.parameters.groups().items():
        for name, param in params.items():
            if param.basis == "team_assumption":
                assert param.status != "set", f"{group}.{name} needs sign-off"


def test_power_request_has_all_et0_inputs(config):
    requested = set(config.parameters.get("power_request", "parameters"))
    assert {"T2M_MAX", "T2M_MIN", "RH2M", "WS10M", "PS", "ALLSKY_SFC_SW_DWN"} <= requested
    assert "PRECTOTCORR" in requested


def test_crops(config):
    assert len(config.crops) == 8
    wheat = config.crops["winter_wheat"]
    assert wheat.kc_ini.frozen_soil == 0.4
    assert wheat.kc_ini.non_frozen_soil == 0.7
    assert wheat.zr_m == (1.5, 1.8)
    assert config.crops["chickpea"].is_legume


def test_soils(config):
    assert len(config.soils) == 9
    assert config.soils["loam"].taw_mm_per_m == (130, 180)
    assert config.soils["loam"].taw_mid == 155


def test_only_the_konya_profile_is_implemented(config):
    implemented = [name for name, p in config.climate.profiles.items() if p.implemented]
    assert implemented == ["semi_arid_continental"]
    assert config.climate.default_profile == "semi_arid_continental"


def test_data_sources(config):
    assert config.data_sources["landsat8"].collection_id == "landsat-c2-l2"
    assert config.data_sources["power"].access == "power_daily_api"


def test_parameter_rejects_value_without_status_agreement():
    with pytest.raises(ValidationError):
        Parameter(value=None, basis="fao56", status="set")
    with pytest.raises(ValidationError):
        Parameter(value=1, basis="design_decision", status="to_be_set")


def test_soil_rejects_inverted_range():
    with pytest.raises(ValidationError):
        Soil(name_tr="x", taw_mm_per_m=(200, 100), rew_mm=(1, 2))
