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
        "မြမြ": "my-MM-NilarNeural",
        "အကိုလေး": "my-MM-ThihaNeural",
        "နီလာ": "my-MM-NilarNeural",
        "သီဟ": "my-MM-ThihaNeural",
        "အကိုလေး ( 🇲🇲 - ကျား)": male_mm,
        "မြမြ (🇲🇲 - မ)": female_mm,
        "စိုးကြီး (🇲🇲 - ကျား)": male_mm,
        "စာဥ (🇲🇲 - မ)": female_mm,
        "သခင်ကြီး (🇲🇲 - ကျား)": male_mm,
        "ချောစု (🇲🇲 - မ)": female_mm,
        "Chou Pro Lay (🇲🇲 - ကျား)": male_mm,
        "ကရင်မ (🇲🇲 - မ)": female_mm,
        "တက်ပု (🇲🇲 - ကျား)": male_mm,
        "ညှပ်စိ (🇲🇲 - မ)": female_mm,
        "တာဇံ(🇲🇲 - ကျား)": male_mm,
        "ဂျိမ်း (🇺🇸 - ကျား)": "en-US-GuyNeural",
        "ဆိုဖီယာ (🇺🇸 - မ)": "en-US-AriaNeural",
        "မိုက်ကယ် (🇬🇧 - ကျား)": "en-GB-RyanNeural",
        "ဂျနီဖာ (🇬🇧 - မ)": "en-GB-SoniaNeural",
    }


def gemini_voice_options() -> dict[str, str]:
    return {
        "Aoede (မ - လွတ်လပ်ပေါ့ပါး)": "Aoede",
        "Callirrhoe (မ - သက်တောင့်သက်သာ)": "Callirrhoe",
        "Kore (မ - တည်ကြည်ပြတ်သား)": "Kore",
        "Leda (မ - ငယ်ရွယ်ဖျတ်လတ်)": "Leda",
        "Zephyr (မ - တက်ကြွလန်းဆန်း)": "Zephyr",
        "Charon (ကျား - သတင်းကြေညာ)": "Charon",
        "Fenrir (ကျား - စိတ်အားထက်သန်)": "Fenrir",
        "Iapetus (ကျား - ရှင်းလင်းပြတ်သား)": "Iapetus",
        "Orus (ကျား - တည်ငြိမ်)": "Orus",
        "Puck (ကျား - မြူးကြွပျော်ရွှင်)": "Puck",
        "Sulafat (မ - အားမာန်အပြည့်)": "Sulafat",
        "Achernar (မ - ယုံကြည်မှုရှိ)": "Achernar",
        "Achird (ကျား - ချိုသာ)": "Achird",
        "Algenib (ကျား - လေးနက်)": "Algenib",
        "Algieba (ကျား - ဆွဲဆောင်မှုရှိ)": "Algieba",
        "Alnilam (ကျား - ခေတ်ဆန်)": "Alnilam",
        "Autonoe (မ - ရိုးရှင်း)": "Autonoe",
        "Despina (မ - နူးညံ့)": "Despina",
        "Enceladus (ကျား - ပြတ်သား)": "Enceladus",
        "Erinome (မ - တက်ကြွ)": "Erinome",
        "Gacrux (မ - ဩဇာရှိ)": "Gacrux",
        "Laomedeia (မ - ဖော်ရွေ)": "Laomedeia",
        "Pulcherrima (မ - ကြည်လင်)": "Pulcherrima",
        "Rasalgethi (ကျား - သွက်လက်)": "Rasalgethi",
        "Sadachbia (ကျား - တည်ကြည်)": "Sadachbia",
        "Sadaltager (ကျား - ယဉ်ကျေး)": "Sadaltager",
        "Schedar (ကျား - ရှင်းလင်း)": "Schedar",
        "Umbriel (ကျား - စွဲမက်ဖွယ်)": "Umbriel",
        "Vindemiatrix (မ - သန့်စင်)": "Vindemiatrix",
        "Zubenelgenubi (ကျား - ထူးခြား)": "Zubenelgenubi",
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
