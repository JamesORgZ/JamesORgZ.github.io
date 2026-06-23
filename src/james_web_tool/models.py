from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class PlanTier(str, Enum):
    NONE = "NONE"
    VIP = "VIP"
    VVIP = "VVIP"
    LIFETIME = "LIFETIME"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"


@dataclass(frozen=True)
class PlanGrant:
    label: str
    days: int | None
    tier: PlanTier

    ONE_MONTH = None
    THREE_MONTHS = None
    SIX_MONTHS = None
    ONE_YEAR = None
    LIFETIME = None


PlanGrant.ONE_MONTH = PlanGrant("1 month", 30, PlanTier.VIP)
PlanGrant.THREE_MONTHS = PlanGrant("3 months", 90, PlanTier.VIP)
PlanGrant.SIX_MONTHS = PlanGrant("6 months", 180, PlanTier.VVIP)
PlanGrant.ONE_YEAR = PlanGrant("1 year", 365, PlanTier.VVIP)
PlanGrant.LIFETIME = PlanGrant("lifetime", None, PlanTier.LIFETIME)


@dataclass(frozen=True)
class LoginResult:
    ok: bool
    is_admin: bool
    user_id: str
    message: str
    plan_tier: PlanTier = PlanTier.NONE


@dataclass(frozen=True)
class GenerationResult:
    mp3_path: Path
    srt_path: Path
    message: str


def edge_voice_options() -> dict[str, str]:
    male_mm = "my-MM-ThihaNeural"
    female_mm = "my-MM-NilarNeural"
    return {
        "James Hero MM-01 (Male)": male_mm,
        "James Velvet MM-02 (Female)": female_mm,
        "James Cinema MM-03 (Male)": male_mm,
        "James Pearl MM-04 (Female)": female_mm,
        "James Thunder MM-05 (Male)": male_mm,
        "James Honey MM-06 (Female)": female_mm,
        "James Pro MM-07 (Male)": male_mm,
        "James Lily MM-08 (Female)": female_mm,
        "James Dragon MM-09 (Male)": male_mm,
        "James Ruby MM-10 (Female)": female_mm,
        "James Pulse US-01 (Male)": "en-US-GuyNeural",
        "James Luna US-02 (Female)": "en-US-AriaNeural",
        "James Royal UK-01 (Male)": "en-GB-RyanNeural",
        "James Rose UK-02 (Female)": "en-GB-SoniaNeural",
    }


def gemini_voice_options() -> dict[str, str]:
    return {
        "James Nova G-01 (Female)": "Aoede",
        "James Breeze G-02 (Female)": "Callirrhoe",
        "James Crown G-03 (Female)": "Kore",
        "James Youth G-04 (Female)": "Leda",
        "James Shine G-05 (Female)": "Zephyr",
        "James Anchor G-06 (Male)": "Charon",
        "James Fire G-07 (Male)": "Fenrir",
        "James Clear G-08 (Male)": "Iapetus",
        "James Calm G-09 (Male)": "Orus",
        "James Spark G-10 (Male)": "Puck",
        "James Power G-11 (Female)": "Sulafat",
        "James Trust G-12 (Female)": "Achernar",
        "James Sweet G-13 (Male)": "Achird",
        "James Deep G-14 (Male)": "Algenib",
        "James Charm G-15 (Male)": "Algieba",
        "James Modern G-16 (Male)": "Alnilam",
        "James Simple G-17 (Female)": "Autonoe",
        "James Soft G-18 (Female)": "Despina",
        "James Sharp G-19 (Male)": "Enceladus",
        "James Active G-20 (Female)": "Erinome",
        "James Aura G-21 (Female)": "Gacrux",
        "James Friendly G-22 (Female)": "Laomedeia",
        "James Crystal G-23 (Female)": "Pulcherrima",
        "James Swift G-24 (Male)": "Rasalgethi",
        "James Prime G-25 (Male)": "Sadachbia",
        "James Noble G-26 (Male)": "Sadaltager",
        "James Clean G-27 (Male)": "Schedar",
        "James Magnet G-28 (Male)": "Umbriel",
        "James Pure G-29 (Female)": "Vindemiatrix",
        "James Titan G-30 (Male)": "Zubenelgenubi",
    }


def emotion_options() -> list[str]:
    return [
        "Movie Recap (ဇာတ်လမ်းပြော)",
        "Storytelling (ပုံပြင်ပြော)",
        "Excited (စိတ်လှုပ်ရှား)",
        "Sad (ဝမ်းနည်း)",
        "Angry (ဒေါသထွက်)",
        "Serious/News (သတင်းကြေညာ/တည်ငြိမ်)",
        "Suspense/Thriller (သည်းထိတ်ရင်ဖို)",
        "Romantic/Soft (ချစ်စရာ/နူးညံ့)",
        "Sarcastic/Funny (ဟာသ/နောက်ပြောင်)",
        "Documentary (မှတ်တမ်းရုပ်ရှင်)",
    ]


def voice_display_options() -> dict[str, str]:
    return edge_voice_options() | gemini_voice_options()
