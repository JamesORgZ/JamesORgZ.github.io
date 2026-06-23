from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class PlanTier(str, Enum):
    NONE = "NONE"
    VIP = "VIP"
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
PlanGrant.SIX_MONTHS = PlanGrant("6 months", 180, PlanTier.VIP)
PlanGrant.ONE_YEAR = PlanGrant("1 year", 365, PlanTier.VIP)
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
        "မြန်မာကျား ၁": male_mm,
        "မြန်မာမ ၂": female_mm,
        "ဇာတ်လိုက်ကျား ၃": male_mm,
        "ပုလဲဖြူမ ၄": female_mm,
        "မိုးကြိုးကျား ၅": male_mm,
        "ပျားရည်မ ၆": female_mm,
        "ရုပ်ရှင်ကျား ၇": male_mm,
        "လီလီမ ၈": female_mm,
        "နဂါးကျား ၉": male_mm,
        "ပတ္တမြားမ ၁၀": female_mm,
        "အမေရိကန်ကျား ၁": "en-US-GuyNeural",
        "အမေရိကန်မ ၂": "en-US-AriaNeural",
        "ဗြိတိန်ကျား ၁": "en-GB-RyanNeural",
        "ဗြိတိန်မ ၂": "en-GB-SoniaNeural",
    }


def gemini_voice_options() -> dict[str, str]:
    return {
        "ကြယ်နု ၁": "Aoede",
        "လေပြေ ၂": "Callirrhoe",
        "မင်းသမီး ၃": "Kore",
        "ငယ်ရွယ် ၄": "Leda",
        "နေခြည် ၅": "Zephyr",
        "သတင်းကျား ၆": "Charon",
        "မီးတောက်ကျား ၇": "Fenrir",
        "ကြည်လင်ကျား ၈": "Iapetus",
        "တည်ငြိမ်ကျား ၉": "Orus",
        "ပျော်ရွှင်ကျား ၁၀": "Puck",
        "အားမာန်မ ၁၁": "Sulafat",
        "ယုံကြည်မ ၁၂": "Achernar",
        "ချိုသာကျား ၁၃": "Achird",
        "လေးနက်ကျား ၁၄": "Algenib",
        "ဆွဲဆောင်ကျား ၁၅": "Algieba",
        "ခေတ်ဆန်ကျား ၁၆": "Alnilam",
        "ရိုးရှင်းမ ၁၇": "Autonoe",
        "နူးညံ့မ ၁၈": "Despina",
        "ပြတ်သားကျား ၁၉": "Enceladus",
        "တက်ကြွမ ၂၀": "Erinome",
        "ဩဇာမ ၂၁": "Gacrux",
        "ဖော်ရွေမ ၂၂": "Laomedeia",
        "ပုံဆောင်မ ၂၃": "Pulcherrima",
        "သွက်လက်ကျား ၂၄": "Rasalgethi",
        "တည်ကြည်ကျား ၂၅": "Sadachbia",
        "ယဉ်ကျေးကျား ၂၆": "Sadaltager",
        "သန့်ရှင်းကျား ၂၇": "Schedar",
        "စွဲမက်ကျား ၂၈": "Umbriel",
        "သန့်စင်မ ၂၉": "Vindemiatrix",
        "ထူးခြားကျား ၃၀": "Zubenelgenubi",
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

