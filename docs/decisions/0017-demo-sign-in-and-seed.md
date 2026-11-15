# 0017: Demo sign-in by role, and a seeded demo for a jury

**Status:** Accepted for the demo, 15 November 2026.

## Decision

- **Role picker, no password.** With `DEMO_ROLE_LOGIN=true` the sign-in screen first shows one
  button per role (admin, agronomist, cooperative, farmer). `GET /api/v1/auth/demo/roles` lists
  them and `POST /api/v1/auth/demo/login {role}` signs in. Off by default, in every environment.
- **Only the demo accounts can be entered this way.** The endpoint signs in the seeded
  `demo-<role>@demo.zira` accounts and nothing else; a real user is never picked by role. The demo
  accounts get a random password that is thrown away, so the password form cannot open them.
- **Ordinary sign-in stays.** "Sign in with my account" on the picker, and the whole password and
  farmer WhatsApp flow, work as before when the flag is off.
- **Seed.** `python -m app.cli seed-demo [--fetch-weather] [--drafts-for YEAR]` is safe to repeat.
  It creates the demo cooperative, the four accounts, a demo field near Kulu (about 7 ha, loam)
  linked to the demo farmer, and a placeholder sensor calibration for the simulator. With
  `--fetch-weather` it fetches real NASA POWER data (about 9,100 days); with `--drafts-for` it writes
  message drafts from the real model, with no recipient, so nothing can be sent until a person types
  a number and approves.

## Risk, and why it is acceptable only for the demo

With the flag on, anyone who opens the site can act as an admin or an agronomist: see every field,
approve a message, and, if the Green API gateway is paired and a draft has a phone number, send a
WhatsApp message to that number. Turn the flag on for the jury and off again afterwards; unpair or
leave unconfigured the WhatsApp gateway on the demo server unless a send is wanted.

## Open

1. The demo field is a real-looking polygon near Kulu; its MODIS and Landsat NDVI have not been
   checked for a clear cropped-fallow signal. Fetch it in Field Memory and confirm before the demo.
2. The sensor calibration (wilting point 0.15, field capacity 0.31) is a placeholder for the simulator.
3. Satellite NDVI, the confirmed history and simulated sensor readings are not seeded: the first two
   need the network and a person, the third is `simulator/zira_sensor_sim.py`.
