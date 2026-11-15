"""The Water Vault engine: FAO-56 reference evapotranspiration, crop coefficients and the
daily root-zone water balance (PDT section 7).

The modules here are pure functions with no database and no configuration reads, so each can
be checked against the worked examples of FAO Irrigation and Drainage Paper 56. Parameter
values are passed in by the caller, who reads them from ``config/``.
"""
