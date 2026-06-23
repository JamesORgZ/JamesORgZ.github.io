# James SRT Studio — Audio/Video to SRT Tool Design

Date: 2026-06-22

## Goal

Build a Windows desktop tool for James that accepts an audio or video file and exports an accurate `.srt` subtitle file.

The tool must:

- Work offline after initial setup/model installation.
- Preserve the spoken language exactly; it must transcribe, not translate.
- Support the user's main languages: Burmese/Myanmar and English.
- Output standard SRT timestamps in `HH:MM:SS,mmm` format, for example `00:00:00,000`.
- Use the provided James Mini Recap logo and theme colors derived from the logo.
- Place an easy-to-open launcher/tool on the user's Desktop.

## Approved User Requirements

- Use the provided logo:
  `C:\Users\James\Desktop\Logo\Jamesrecap\Picsart_26-04-09_21-45-34-093.png`
- Theme colors should follow the logo:
  - dark navy / black background
  - gold / yellow primary accent
  - electric blue secondary accent
  - white text
- Offline use is acceptable even if the AI model is large, around 3–5 GB.
- Use a high-accuracy local model.
- Main transcription languages are Burmese/Myanmar and English.
- Do not translate output.
- Subtitle line limit:
  - maximum 25 characters per line
  - for Burmese, never split inside a syllable, combining-mark sequence, or visually connected word unit
  - prefer natural Burmese phrase/word boundaries

## Architecture

The app will use a local-first pipeline:

1. User selects or drops an audio/video file.
2. FFmpeg converts it to normalized audio:
   - 16 kHz
   - mono
   - WAV/PCM working file
3. Faster Whisper transcribes locally:
   - preferred model: `large-v3`
   - task: `transcribe`
   - language: auto-detect
   - word timestamps enabled
   - VAD enabled when useful
4. Subtitle formatter groups recognized words/segments into readable subtitle blocks.
5. Burmese-aware line wrapper enforces max 25 characters without unsafe Myanmar text breaks.
6. SRT writer exports a `.srt` next to the source file or into a chosen output folder.
7. UI shows progress and preview.

## Model and Offline Behavior

Use `faster-whisper` with the CTranslate2 `large-v3` model.

Preferred runtime:

- GPU: NVIDIA RTX 3060 Ti, CUDA, `float16` or `int8_float16`
- Fallback: CPU, `int8`

Offline behavior:

- The model will be installed/downloaded during setup.
- After the model exists locally, transcription must not require internet.
- If the model is missing and internet is unavailable, the app should show a clear setup error instead of failing silently.

## Desktop App UX

Approved main screen:

- App title: `James SRT Studio`
- Logo at top
- Drag-and-drop / Browse file area
- Settings:
  - Language: Auto Detect
  - Model: Large V3 Accurate
  - Max line length: 25
- `Generate SRT` button
- progress bar and status messages
- SRT preview box
- `Open Output Folder` button after generation

## SRT Formatting

Timestamp format:

```text
1
00:00:00,000 --> 00:00:03,500
မောင်မောင်ကနေမကောင်းလို့
အပြင်မသွားဘူး
```

Rules:

- Use comma milliseconds, not frame-style colons.
- Subtitle numbers start at 1.
- Avoid overly long subtitle blocks.
- Prefer readable phrase boundaries.
- Avoid splitting Burmese inside combining marks or dependent vowels.
- Keep each visual line at or below 25 characters when possible.

## Burmese Line Breaking Strategy

The formatter will treat Myanmar text carefully:

- Build grapheme-like clusters so dependent vowel signs, tone marks, medials, virama/asat, and related marks stay attached.
- Prefer splitting on:
  - spaces
  - punctuation
  - natural phrase endings such as `လို့`, `တော့`, `ပြီး`, `မယ်`, `တယ်`, `ပါ`, `ခဲ့`
- If a phrase is longer than 25 characters, split only at safe Myanmar cluster boundaries.
- Never split by raw Unicode code point in a way that separates combining marks from their base.

## Error Handling

The app should show clear errors for:

- unsupported/corrupt media file
- FFmpeg missing or failing
- model missing
- internet unavailable during first model setup
- CUDA/GPU unavailable
- out-of-memory on GPU
- permission denied writing output file

GPU fallback:

- If CUDA fails, retry on CPU and show that CPU mode is slower.

## Testing Plan

Use test-driven development for core non-UI logic before implementation:

- timestamp formatting tests
- SRT writer tests
- Burmese-safe line wrapping tests
- English line wrapping tests
- subtitle grouping tests
- FFmpeg availability/preprocessing tests where practical
- app launch smoke test

Example Burmese wrapping test:

- Input: `မောင်မောင်ကနေမကောင်းလို့အပြင်မသွားဘူး`
- Expected wrapped output:
  - `မောင်မောင်ကနေမကောင်းလို့`
  - `အပြင်မသွားဘူး`

## Packaging

Recommended deliverable:

- App folder under Desktop, for example:
  `C:\Users\James\Desktop\James SRT Studio`
- Desktop launcher:
  `James SRT Studio`
- Model folder included or downloaded during setup into the app data/model folder.

Packaging as a single `.exe` may not be ideal because the model is multiple GB. A desktop launcher pointing to the app folder is more reliable and easier to repair/update.

## Open Constraints

- Exact transcription accuracy depends on audio quality, background noise, speaker clarity, and Whisper's Burmese support.
- The app can preserve language and avoid translation, but it cannot guarantee perfect words for unclear audio.
- Very long audio files may take time, especially in CPU fallback mode.

