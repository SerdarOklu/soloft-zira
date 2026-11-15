# Configuration

Model values live here, not in code. The backend loads these files at start-up through
`backend/app/core/parameters.py` and refuses to start if their shape or ranges are wrong.

| File | Contents | Source |
| --- | --- | --- |
| `parameters.yaml` | Core model parameters, FAO correction constants, Field Memory and sensor settings, the NASA POWER request | Parameter sheet, "Parametreler" |
| `crops.yaml` | Crop coefficients, height, root depth, depletion fraction | Parameter sheet, "Ürünler"; FAO-56 Tables 12 and 22 |
| `soils.yaml` | Available water and readily evaporable water by soil texture | Parameter sheet, "Topraklar"; FAO-56 Table 19 |
| `climate_profiles.yaml` | Which extra variables each climate and site condition switches on | PDT sections 8.2 and 8.3 |
| `rotation_demo.yaml` | PROVISIONAL stage lengths, sowing dates, irrigation efficiency and NDVI cropped threshold and sensor band | FAO-56 Table 11; not signed off (decision 0012) |
| `message_templates.yaml` | WhatsApp draft wording (Turkish, English) and event thresholds | Draft texts for agronomist review |
| `data_sources.yaml` | NASA sources: role, collection, resolution, scale warning | PDT section 6 |

## Source of truth

The "Zira Parametre Tablosu" sheet is the source of truth. These files mirror revision 6
of it (14 November 2026). When the sheet changes, change the matching file in the same
pull request and say so in the description.

Per-field values (coordinate, polygon, soil analysis, crop history, farmer constraints) are
not configuration. They belong to the Field Profile in the database (PDT section 5).

## Status of a parameter

Every entry in `parameters.yaml` has a `basis` and a `status`:

- `set`: has a usable value.
- `needs_signoff`: a team assumption or design decision. Usable for demos only until an
  agronomist confirms it.
- `to_be_set`: no value yet. An analysis that needs it must refuse to run.
- `optional`: may stay unset.

`GET /api/v1/meta` lists the parameters in the last two groups, so the open items are
visible on a running system.

## Changing a value

1. Change the sheet.
2. Change the YAML file.
3. Run `cd backend && uv run pytest`: `tests/test_config.py` pins the values the PDT
   states, so a change to one of those needs the test and the PDT updated too.
4. Raise `model_version` in `parameters.yaml` if the change alters results.
