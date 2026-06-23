from __future__ import annotations

import os

import gradio as gr

from .admin import create_paid_user, delete_user, disable_user, grant_plan, revoke_user
from .auth import login_with_pin
import base64

from .config import APP_NAME, default_db_path, default_logo_path, default_output_dir
from .database import create_user, get_user_by_pin, init_db, list_users, search_users
from .generator import generate_for_user
from .models import PlanGrant, PlanTier, edge_voice_options, emotion_options, gemini_voice_options, voice_display_options

CSS = """
.gradio-container { background: #050508 !important; color: #f7f2ff !important; }
.james-hero { display: flex; align-items: center; gap: 16px; padding: 18px; border-radius: 20px; background: linear-gradient(135deg,#090913,#120a22); border: 1px solid rgba(255,209,41,.25); }
.james-logo { width: 72px; height: 72px; object-fit: cover; border-radius: 18px; border: 1px solid rgba(255,209,41,.45); box-shadow: 0 0 28px rgba(123,67,255,.42); background: #000; }
.james-title { color: #ffd129; font-size: 30px; font-weight: 900; }
.james-subtitle { color: #cfc8ff; }
.premium-panel { border: 1px solid #ffd129 !important; border-radius: 12px !important; padding: 14px !important; background: #0d1320 !important; }
.premium-subpanel { border: 1px solid #00d19a !important; border-radius: 12px !important; padding: 14px !important; background: #101827 !important; }
.james-chip { color: #fff !important; background: #6b4cff !important; border-radius: 7px !important; padding: 4px 8px !important; display: inline-block; font-weight: 800; }
button.primary { background: linear-gradient(90deg,#ffd129,#7b43ff) !important; color: #050505 !important; }
"""


def _users_table(rows: list[dict]) -> list[list[str]]:
    return [
        [
            row["user_id"],
            row["pin"],
            row["plan_tier"],
            row["expires_at"] or "lifetime/none",
            row["status"],
            str(row.get("job_count", 0)),
        ]
        for row in rows
    ]


def logo_html() -> str:
    logo_path = default_logo_path()
    if not logo_path.is_file():
        return "<div class='james-logo'></div>"
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"<img class='james-logo' src='data:image/jpeg;base64,{encoded}' />"


def ensure_free_user(db_path) -> str:
    free_pin = "FREE-DEMO"
    user = get_user_by_pin(db_path, free_pin)
    if user is None:
        user = create_user(db_path, pin=free_pin, plan_tier=PlanTier.NONE, expires_at=None)
    return user["user_id"]


def selected_user_id_from_table(table_value, index) -> str:
    if index is None:
        return ""
    row_index = index[0] if isinstance(index, (list, tuple)) else index
    if hasattr(table_value, "iloc"):
        try:
            return str(table_value.iloc[row_index, 0])
        except Exception:
            return ""
    if isinstance(table_value, dict):
        rows = table_value.get("data") or []
        try:
            return str(rows[row_index][0])
        except Exception:
            return ""
    try:
        return str(table_value[row_index][0])
    except Exception:
        return ""


def target_user_id_from_target_or_search(db_path, target_user_id: str, search_query: str) -> str:
    clean_target = target_user_id.strip()
    if clean_target:
        return clean_target
    clean_query = search_query.strip()
    if not clean_query:
        raise ValueError("Target User ID required. Search PIN/User ID or select a table row first.")
    rows = search_users(db_path, clean_query)
    if not rows:
        raise ValueError(f"User not found for search: {clean_query}")
    return rows[0]["user_id"]


def remember_admin_payload(is_admin: bool, remember: bool) -> dict[str, bool]:
    if is_admin and remember:
        return {"admin_remembered": True}
    return {}


def should_restore_admin(memory: dict | None) -> bool:
    return bool(isinstance(memory, dict) and memory.get("admin_remembered") is True)


def voice_dropdown_for_engine(engine: str):
    if engine == "Gemini API (Key Required)":
        voices = gemini_voice_options()
        return gr.update(
            choices=list(voices.keys()),
            value="Aoede (မ - လွတ်လပ်ပေါ့ပါး)",
            label="[V1] Voice (Gemini)",
        )
    voices = edge_voice_options()
    return gr.update(
        choices=list(voices.keys()),
        value="အကိုလေး ( 🇲🇲 - ကျား)",
        label="[V1] Voice",
    )


def build_app() -> gr.Blocks:
    db_path = default_db_path()
    output_dir = default_output_dir()
    init_db(db_path)

    with gr.Blocks(title=APP_NAME) as app:
        session_user_id = gr.State("")
        session_is_admin = gr.State(False)
        admin_memory = browser_state_or_session_state({})

        gr.HTML(
            f"""
            <div class='james-hero'>
              {logo_html()}
              <div>
                <div class='james-title'>{APP_NAME}</div>
                <div class='james-subtitle'>Myanmar transcript ကို MP3 အသံ + SRT subtitle အဖြစ်ထုတ်ပေးမယ်</div>
              </div>
            </div>
            """
        )

        with gr.Tab("Free Tool"):
            gr.Markdown("### 🎁 Free Marketing Tool\nLogin မလိုဘဲ စမ်းသုံးနိုင်ပါတယ်။ Free plan က 500 characters အထိပဲ ထုတ်ပေးမယ်။")
            free_text = gr.Textbox(label="Free Myanmar Text", lines=8, placeholder="မြန်မာစာထည့်ပါ...")
            with gr.Row():
                free_voice = gr.Dropdown(choices=list(edge_voice_options().keys()), value="မြမြ", label="Free Voice")
                free_srt_format = gr.Radio(choices=["Single Line", "2 Lines"], value="Single Line", label="Free SRT Format")
            free_btn = gr.Button("Generate Free MP3 & SRT", variant="primary")
            free_status = gr.Markdown("")
            free_audio = gr.Audio(label="Free Audio Preview")
            free_mp3 = gr.File(label="Free MP3 Download")
            free_srt = gr.File(label="Free SRT Download")

        with gr.Tab("Login"):
            pin = gr.Textbox(label="PIN / Admin Password", type="password")
            remember_admin = gr.Checkbox(value=True, label="Remember admin on this browser")
            login_btn = gr.Button("🚀 Login", variant="primary")
            forget_admin_btn = gr.Button("Forget saved admin login")
            login_status = gr.Markdown("Login ဝင်ရန် PIN ထည့်ပါ။")

            with gr.Column(visible=False) as admin_panel:
                admin_panel_marker = gr.Textbox(label="Admin Panel", visible=False)
                admin_status = gr.Markdown("Admin login required.")
                with gr.Row():
                    new_pin = gr.Textbox(label="New User PIN")
                    plan = gr.Dropdown(
                        choices=["1 month", "3 months", "6 months", "1 year", "lifetime"],
                        value="1 month",
                        label="Plan",
                    )
                    create_btn = gr.Button("Create / Grant User", variant="primary")
                search = gr.Textbox(label="Search User ID or PIN")
                refresh_btn = gr.Button("Refresh Users")
                users = gr.Dataframe(headers=["User ID", "PIN", "Plan", "Expires", "Status", "Jobs"], datatype=["str"] * 6)
                selected_user_id = gr.Textbox(label="Target User ID")
                with gr.Row():
                    grant_1m = gr.Button("Grant 1M VIP")
                    grant_3m = gr.Button("Grant 3M VIP")
                    grant_6m = gr.Button("Grant 6M VVIP")
                    grant_1y = gr.Button("Grant 1Y VVIP")
                    grant_life = gr.Button("Grant Lifetime")
                with gr.Row():
                    revoke_btn = gr.Button("Revoke")
                    disable_btn = gr.Button("Disable")
                    delete_btn = gr.Button("Delete User")

        with gr.Tab("Generator"):
            current_user = gr.Markdown("Not logged in")
            transcript = gr.Textbox(label="Myanmar Transcript", lines=12)

            with gr.Group(elem_classes=["premium-panel"]):
                gr.Markdown("### 🎙️ Myanmar Multi-Speaker TTS & SRT Generator")
                with gr.Row():
                    tts_engine = gr.Radio(
                        choices=["Free Edge TTS", "Gemini API (Key Required)"],
                        value="Free Edge TTS",
                        label="TTS Engine",
                    )
                    api_key = gr.Textbox(
                        label="Gemini API Key",
                        type="password",
                        placeholder="Enter your API Key...",
                    )
                    gemini_model = gr.Radio(
                        choices=["Gemini 3.1 Flash", "Gemini 2.5 Flash"],
                        value="Gemini 3.1 Flash",
                        label="Gemini Model",
                    )

            with gr.Group(elem_classes=["premium-subpanel"]):
                with gr.Accordion("Pronunciation Rules (အသံထွက်ပြင်ဆင်ရန်)", open=True):
                    pronunciation_rules = gr.Textbox(
                        label="Pronunciation Rules (အသံထွက်ပြင်ဆင်ရန်)",
                        lines=3,
                        placeholder="ဥပမာ - Myanmar_TTSaa => မြန်မာ တီတီအက်စ်အေ",
                    )

                file_name = gr.Textbox(value="Myanmar_TTSaa", label="သိမ်းမယ့်ဖိုင် နာမည် (File Name)")
                voice = gr.Dropdown(
                    choices=list(edge_voice_options().keys()),
                    value="အကိုလေး ( 🇲🇲 - ကျား)",
                    label="[VIP] Voice",
                )
                gr.Button("🔊 အသံ (Voice) အသံစမ်းနားထောင်မည်")

                with gr.Row():
                    emotion = gr.Dropdown(
                        choices=emotion_options(),
                        value="Movie Recap (ဇာတ်လမ်းပြော)",
                        label="ခံစားမှု / အသံပုံစံ (Emotion)",
                    )
                    srt_format = gr.Radio(
                        choices=["Single Line", "2 Lines", "YouTube"],
                        value="Single Line",
                        label="SRT Format Type",
                    )

                with gr.Accordion("Advanced Settings (အသံ အမြန်နှုန်း/အသံအနိမ့်အမြင့်)", open=True):
                    pitch = gr.Slider(-50, 50, value=0, step=1, label="Base Tone (Pitch)")
                    rate = gr.Slider(-50, 100, value=40, step=1, label="Base Speed (Rate)")
                    volume_boost = gr.Slider(0, 20, value=10, step=1, label="Volume Booster (+dB)")

            generate_btn = gr.Button("Generate MP3 & SRT", variant="primary")
            generate_status = gr.Markdown("")
            audio_out = gr.Audio(label="Output Audio")
            mp3_file = gr.File(label="MP3 Download")
            srt_file = gr.File(label="SRT Download")

        def admin_unlocked_outputs(message: str, memory: dict | None = None):
            return (
                message,
                "ADMIN",
                True,
                "Logged in: ADMIN • LIFETIME",
                gr.update(visible=True),
                "Admin panel ready.",
                _users_table(list_users(db_path)),
                memory or {},
            )

        def do_login(pin_value: str, remember_value: bool):
            result = login_with_pin(db_path, pin_value)
            if not result.ok:
                return result.message, "", False, "Not logged in", gr.update(visible=False), "Admin login required.", [], {}
            admin_text = "Admin panel ready." if result.is_admin else "Admin login required."
            user_text = f"Logged in: {result.user_id} • {result.plan_tier.value}"
            memory = remember_admin_payload(result.is_admin, remember_value)
            return (
                result.message,
                result.user_id,
                result.is_admin,
                user_text,
                gr.update(visible=result.is_admin),
                admin_text,
                _users_table(list_users(db_path)) if result.is_admin else [],
                memory,
            )

        login_btn.click(
            do_login,
            inputs=[pin, remember_admin],
            outputs=[login_status, session_user_id, session_is_admin, current_user, admin_panel, admin_status, users, admin_memory],
        )

        def restore_saved_admin(memory: dict | None):
            if should_restore_admin(memory):
                return admin_unlocked_outputs("Saved admin login restored.", memory)
            return "", "", False, "Not logged in", gr.update(visible=False), "Admin login required.", [], {}

        app.load(
            restore_saved_admin,
            inputs=[admin_memory],
            outputs=[login_status, session_user_id, session_is_admin, current_user, admin_panel, admin_status, users, admin_memory],
        )

        def forget_saved_admin():
            return "Saved admin login cleared.", "", False, "Not logged in", gr.update(visible=False), "Admin login required.", [], {}

        forget_admin_btn.click(
            forget_saved_admin,
            inputs=[],
            outputs=[login_status, session_user_id, session_is_admin, current_user, admin_panel, admin_status, users, admin_memory],
        )

        tts_engine.change(voice_dropdown_for_engine, inputs=[tts_engine], outputs=[voice])

        def do_free_generate(text: str, voice_label: str, fmt: str):
            free_user_id = ensure_free_user(db_path)
            result = generate_for_user(
                db_path,
                output_dir,
                free_user_id,
                text,
                voice_label,
                fmt,
                "free_james_output",
            )
            return result.message, str(result.mp3_path), str(result.mp3_path), str(result.srt_path)

        free_btn.click(
            do_free_generate,
            inputs=[free_text, free_voice, free_srt_format],
            outputs=[free_status, free_audio, free_mp3, free_srt],
        )

        def do_generate(
            user_id: str,
            text: str,
            engine: str,
            key: str,
            gemini_model_label: str,
            rules: str,
            name: str,
            voice_label: str,
            emotion_label: str,
            fmt: str,
            pitch_value: int | float,
            rate_value: int | float,
            volume_value: int | float,
        ):
            if not user_id or user_id == "ADMIN":
                raise gr.Error("User login required.")
            result = generate_for_user(
                db_path,
                output_dir,
                user_id,
                text,
                voice_label,
                fmt,
                name,
                pronunciation_rules=rules,
                rate=rate_value,
                pitch=pitch_value,
                volume_boost=volume_value,
                emotion=emotion_label,
                engine=engine,
                api_key=key,
                gemini_model=gemini_model_label,
            )
            return result.message, str(result.mp3_path), str(result.mp3_path), str(result.srt_path)

        generate_btn.click(
            do_generate,
            inputs=[
                session_user_id,
                transcript,
                tts_engine,
                api_key,
                gemini_model,
                pronunciation_rules,
                file_name,
                voice,
                emotion,
                srt_format,
                pitch,
                rate,
                volume_boost,
            ],
            outputs=[generate_status, audio_out, mp3_file, srt_file],
        )

        grant_map = {
            "1 month": PlanGrant.ONE_MONTH,
            "3 months": PlanGrant.THREE_MONTHS,
            "6 months": PlanGrant.SIX_MONTHS,
            "1 year": PlanGrant.ONE_YEAR,
            "lifetime": PlanGrant.LIFETIME,
        }

        def require_admin(is_admin: bool):
            if not is_admin:
                raise gr.Error("Admin login required.")

        def do_create(is_admin: bool, pin_value: str, plan_label: str):
            require_admin(is_admin)
            try:
                create_paid_user(db_path, pin_value.strip(), grant_map[plan_label])
            except Exception as exc:
                raise gr.Error(str(exc)) from exc
            return _users_table(list_users(db_path)), "User created."

        create_btn.click(do_create, inputs=[session_is_admin, new_pin, plan], outputs=[users, admin_status])

        def do_search(is_admin: bool, query: str):
            require_admin(is_admin)
            rows = search_users(db_path, query) if query.strip() else list_users(db_path)
            target = rows[0]["user_id"] if rows else ""
            return _users_table(rows), target

        refresh_btn.click(do_search, inputs=[session_is_admin, search], outputs=[users, selected_user_id])
        search.submit(do_search, inputs=[session_is_admin, search], outputs=[users, selected_user_id])

        def grant_action(is_admin: bool, user_id: str, query: str, grant: PlanGrant):
            require_admin(is_admin)
            try:
                resolved_user_id = target_user_id_from_target_or_search(db_path, user_id, query)
                grant_plan(db_path, resolved_user_id, grant)
            except Exception as exc:
                raise gr.Error(str(exc)) from exc
            return _users_table(list_users(db_path)), f"Updated {resolved_user_id}", resolved_user_id

        grant_1m.click(lambda a, u, q: grant_action(a, u, q, PlanGrant.ONE_MONTH), [session_is_admin, selected_user_id, search], [users, admin_status, selected_user_id])
        grant_3m.click(lambda a, u, q: grant_action(a, u, q, PlanGrant.THREE_MONTHS), [session_is_admin, selected_user_id, search], [users, admin_status, selected_user_id])
        grant_6m.click(lambda a, u, q: grant_action(a, u, q, PlanGrant.SIX_MONTHS), [session_is_admin, selected_user_id, search], [users, admin_status, selected_user_id])
        grant_1y.click(lambda a, u, q: grant_action(a, u, q, PlanGrant.ONE_YEAR), [session_is_admin, selected_user_id, search], [users, admin_status, selected_user_id])
        grant_life.click(lambda a, u, q: grant_action(a, u, q, PlanGrant.LIFETIME), [session_is_admin, selected_user_id, search], [users, admin_status, selected_user_id])

        def do_revoke(is_admin: bool, user_id: str, query: str):
            require_admin(is_admin)
            try:
                resolved_user_id = target_user_id_from_target_or_search(db_path, user_id, query)
                revoke_user(db_path, resolved_user_id)
            except Exception as exc:
                raise gr.Error(str(exc)) from exc
            return _users_table(list_users(db_path)), f"Revoked {resolved_user_id}", resolved_user_id

        def do_disable(is_admin: bool, user_id: str, query: str):
            require_admin(is_admin)
            try:
                resolved_user_id = target_user_id_from_target_or_search(db_path, user_id, query)
                disable_user(db_path, resolved_user_id)
            except Exception as exc:
                raise gr.Error(str(exc)) from exc
            return _users_table(list_users(db_path)), f"Disabled {resolved_user_id}", resolved_user_id

        def do_delete(is_admin: bool, user_id: str, query: str):
            require_admin(is_admin)
            try:
                resolved_user_id = target_user_id_from_target_or_search(db_path, user_id, query)
                delete_user(db_path, resolved_user_id)
            except Exception as exc:
                raise gr.Error(str(exc)) from exc
            return _users_table(list_users(db_path)), f"Deleted {resolved_user_id}", ""

        revoke_btn.click(do_revoke, [session_is_admin, selected_user_id, search], [users, admin_status, selected_user_id])
        disable_btn.click(do_disable, [session_is_admin, selected_user_id, search], [users, admin_status, selected_user_id])
        delete_btn.click(do_delete, [session_is_admin, selected_user_id, search], [users, admin_status, selected_user_id])

        def select_user(table_value, evt: gr.SelectData):
            return selected_user_id_from_table(table_value, evt.index)

        users.select(select_user, inputs=[users], outputs=[selected_user_id])

    return app


def main() -> None:
    build_app().queue().launch(css=CSS, **launch_kwargs_from_env())


def launch_kwargs_from_env() -> dict[str, int | str]:
    return {
        "server_name": os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
        "server_port": int(os.getenv("PORT", os.getenv("GRADIO_SERVER_PORT", "7860"))),
    }


def browser_state_or_session_state(default_value: dict):
    browser_state_cls = getattr(gr, "BrowserState", None)
    if browser_state_cls is not None:
        return browser_state_cls(default_value)
    return gr.State(default_value)
