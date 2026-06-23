# James Audio & Srt Generator Web Tool Design

Date: 2026-06-22

## Goal

Build a paid private web tool named `James Audio & Srt Generator`.

The product’s main job is:

```text
Myanmar transcript / text -> Myanmar MP3 audio + accurate SRT
```

The first launch version is a Gradio-based MVP with a premium dashboard look, manual VIP/VVIP access control, and admin-managed users. It is not a full subscription SaaS yet.

## Brand and UI Direction

- Product name: `James Audio & Srt Generator`
- Logo: `C:\Users\James\Downloads\Telegram Desktop\photo_2026-06-22_18-57-59.jpg`
- Theme: black background, purple glow, yellow highlights
- Chosen layout: Premium dashboard

The UI will use a dashboard structure:

- Top brand bar with logo, product name, and current plan badge
- Left sidebar navigation
- Main generator page
- Download output panel
- Admin controls for the owner

## User Plans

The system uses time-based access.

- `1 month` = VIP
- `3 months` = VIP
- `6 months` = VVIP
- `1 year` = VVIP
- `Lifetime` = VVIP / Lifetime

Payment is handled manually outside the app at first, such as KPay, Wave, or bank transfer. After payment confirmation, the admin grants or extends access.

## Authentication

MVP login will use PIN/password style access.

Each user has:

- User ID
- PIN or password
- Plan type
- Expiry date
- Status: active, expired, disabled
- Optional device/session metadata

The admin has a master login that reveals the admin panel.

## Main User Features

The first version focuses on text/transcript based generation.

User can:

- Paste Myanmar transcript/text
- Choose Myanmar voice
- Choose SRT format
- Choose file name
- Generate MP3
- Generate SRT
- Preview/download MP3
- Download SRT

SRT formatting rules:

- Standard SRT timestamp format: `00:00:00,000`
- Myanmar-safe line breaks
- Avoid splitting Myanmar words awkwardly
- Support single line and two-line formats

## TTS Providers

The safe first providers are:

1. Microsoft/Edge/Azure-style Myanmar voices
   - `my-MM-NilarNeural`
   - `my-MM-ThihaNeural`

2. Optional Gemini API mode
   - User/admin can provide Gemini API key later
   - Supports Gemini voices such as Aoede, Kore, Leda, Zephyr, Charon, Puck
   - Good future path for multi-speaker or emotion control

The app must not depend on scraping `speechsynthesis.online` for paid generation. That site appears to use Microsoft/Azure voices and Cloudflare Turnstile; scraping it would be unstable and risky for a paid product.

Display voice names can be branded for users, for example:

- `အကိုလေး` -> male Myanmar voice
- `မြမြ` -> female Myanmar voice

Internally, the app should keep the real provider voice IDs separate from the display labels.

## Admin Panel

Admin can:

- View all users
- Search by User ID or PIN
- Create user
- Edit PIN/password
- Grant 1 month VIP
- Grant 3 months VIP
- Grant 6 months VVIP
- Grant 1 year VVIP
- Grant lifetime VVIP
- Revoke access
- Disable/enable user
- Reset device/session record
- View recent generated jobs

Admin panel will be built into the same Gradio app for MVP speed.

## Data Storage

MVP storage should be simple and portable:

- SQLite database for users, plans, jobs, and settings
- Output files saved under an `outputs/` folder
- Generated MP3/SRT paths stored in job history

Proposed tables:

- `users`
- `plans`
- `jobs`
- `settings`

## Generation Flow

1. User logs in with PIN/password.
2. App checks if user is active and not expired.
3. User pastes Myanmar transcript.
4. User selects voice and SRT format.
5. Backend generates MP3 from text.
6. Backend measures MP3 duration.
7. Backend segments transcript into subtitle blocks.
8. Backend writes SRT with standard timestamps.
9. App returns MP3 and SRT download files.
10. Job is recorded in history.

## Error Handling

The app should show clear messages for:

- Wrong PIN/password
- Expired plan
- Disabled user
- Empty text
- TTS provider error
- Internet/API failure
- File generation failure

Generated files should use safe filenames and avoid overwriting by adding timestamps when needed.

## Out of Scope for First MVP

The first MVP will not include:

- Automatic KPay/Wave payment integration
- Full Stripe-style subscription billing
- Public self-registration
- Heavy audio-only Whisper transcription
- Mobile app
- Complex analytics

These can be added after the first paid launch proves demand.

## Testing Plan

Verify:

- Login works for normal user and admin
- Expired user cannot generate
- VIP/VVIP plan labels and expiry dates work
- Myanmar text generates MP3 and SRT
- SRT timestamps are valid
- Myanmar line breaks do not split words badly
- Admin can create, extend, revoke, and disable users
- Output files download correctly

## Deployment Direction

Start with:

- Gradio + Python
- SQLite
- Koyeb or small VPS
- Manual payment confirmation

Expected early hosting cost: low CPU hosting, around `$10-$30/month` depending on provider and traffic.

If usage grows, upgrade to:

- FastAPI backend
- React/Next.js frontend
- PostgreSQL
- Dedicated job queue
- Official paid TTS API keys

