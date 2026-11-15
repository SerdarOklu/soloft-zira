# 0018: Passwordless sign-in for farmers

**Status:** Implemented and tested locally, 15 November 2026. Not deployed. Needs a working
WhatsApp gateway (Green API QR scanned) before the code path works in production.

## Decision

A farmer signs in without a password in one of two ways:

1. **A WhatsApp code.** The farmer types their phone number; Zira sends a 6-digit code to that
   number through the existing Green API gateway (decision 0012); the code opens a session.
2. **A one-time link.** A cooperative user (or an admin) presses "Giriş linki" next to a farmer;
   the link is shown once and handed over by that person. The farmer opens it and taps a button.

Staff (admin, agronomist, cooperative user) keep their e-mail and password. Both passwordless
ways work for `farmer` accounts only, so a stolen SIM or a forwarded link never opens a staff
account. The two buttons on the sign-in screen only choose how to prove who you are; the role
always comes from the account on the server.

## Rules

- **Code:** 6 digits, valid 10 minutes, 5 wrong guesses kill it, at most 3 codes an hour per
  account, a new code replaces the old one, used once. Only an HMAC-SHA256 of the code (keyed with
  the server secret and the account id) is stored.
- **Link:** 32 random bytes, valid 24 hours, used once, a new link replaces the old one. Only an
  HMAC of the secret is stored. The page does not use the link when it loads; the farmer taps a
  button, so a chat app that previews the address does not burn it. The page sends no Referer.
- **No account enumeration.** Asking for a code answers the same for a known number, an unknown
  one and a malformed one. Every failed sign-in answers 401 without saying which part was wrong.
- **Session:** the same httpOnly cookie as the password sign-in, but 30 days
  (`FARMER_SESSION_DAYS`), because a farmer's phone is personal. A closed account loses access at
  once (the user is loaded on every request). Staff sessions stay 12 hours.
- **Phone numbers** are stored on the user (`users.phone`, digits with country code) and belong
  to one account. A number on two accounts gets no code.
- **Creating a farmer:** the password field is now optional. Left empty, the account gets a random
  password nobody knows, so the farmer signs in by code or link. A password may still be set.
  Other roles still need one.

## What changed

- Migration `0005`: `users.phone` and the `login_tokens` table. No existing row was touched.
- Backend: `POST /auth/code/request`, `/auth/code/verify`, `/auth/link/redeem`,
  `POST /users/{id}/login-link`, `phone` on user create and update.
- Frontend: the sign-in screen (farmer by default, staff on the second button), the link page
  `/login/link`, cooperative panel (phone field, optional password, link button).

## Known limits and open points

- **Green API is not the official WhatsApp API.** Delivery is not guaranteed and the sending
  number can be blocked. The link is the fallback, and the screen says so.
- **The instance must be authorised** (QR scanned) or code requests answer "unavailable".
- **Anyone can ask for a code for a number** (up to 3 an hour per account); that can annoy a
  farmer with unwanted messages but cannot sign anyone in.
- **The nginx sign-in limit does not cover this path.** The browser reaches the backend through
  the Next.js server over the Docker network, so the nginx `login` zone (decision 0008) never
  sees it. The limits above live in the backend (per account), not per address. The password
  sign-in has the same gap; closing it is a separate piece of work.
- **No token revocation on sign-out** (as before): a signed-out farmer token stays valid until it
  expires, now up to 30 days. Revoke by closing the account.
- **Passkeys and e-mail** were not added: no mail service exists, and passkeys cannot do the
  first sign-in alone.
