from __future__ import annotations

import queue
import sys
import threading
from importlib.resources import files
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from .constants import APP_NAME, DEFAULT_MAX_LINE_CHARS, SUPPORTED_EXTENSIONS, THEME
from .model_setup import ensure_burmese_asr_model, ensure_model
from .constants import desktop_dir
from .pipeline import generate_srt, generate_srt_from_original_text, generate_tts_mp3_and_srt


def asset_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        internal_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
        candidates = [
            internal_dir / "src" / "james_srt_studio" / "assets" / name,
            internal_dir / "james_srt_studio" / "assets" / name,
            exe_dir / "assets" / name,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
    return Path(files("james_srt_studio").joinpath(f"assets/{name}"))


class JamesSrtApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("960x760")
        self.configure(fg_color=THEME["background"])
        icon_path = asset_path("logo.ico")
        if icon_path.is_file():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass
        ctk.set_appearance_mode("dark")
        self.selected_file: Path | None = None
        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        self._build_ui()
        self.after(200, self._poll_events)

    def _build_ui(self) -> None:
        root = ctk.CTkFrame(self, fg_color=THEME["background"])
        root.pack(fill="both", expand=True, padx=24, pady=24)

        logo_path = asset_path("logo.png")
        if logo_path.is_file():
            image = ctk.CTkImage(Image.open(logo_path), size=(110, 110))
            logo_label = ctk.CTkLabel(root, image=image, text="")
            logo_label.image = image
            logo_label.pack(pady=(0, 8))

        ctk.CTkLabel(
            root,
            text=APP_NAME,
            text_color=THEME["gold"],
            font=("Segoe UI", 32, "bold"),
        ).pack()

        ctk.CTkLabel(
            root,
            text="Audio only သို့မဟုတ် Audio + Original Text ဖြင့် SRT ထုတ်ပေးမယ်",
            text_color=THEME["muted"],
            font=("Segoe UI", 15),
        ).pack(pady=(4, 20))

        self.file_label = ctk.CTkLabel(
            root,
            text="No file selected",
            text_color=THEME["text"],
            fg_color=THEME["panel"],
            corner_radius=16,
            height=74,
            font=("Segoe UI", 16),
        )
        self.file_label.pack(fill="x", pady=(0, 12))

        ctk.CTkButton(
            root,
            text="Browse Audio/Video",
            command=self._browse_file,
            fg_color=THEME["gold_dark"],
            hover_color=THEME["gold"],
            text_color="#06101E",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(0, 14))

        settings = ctk.CTkFrame(root, fg_color=THEME["panel"], corner_radius=16)
        settings.pack(fill="x", pady=(0, 14))
        settings.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(
            settings,
            text="Mode:",
            text_color=THEME["text"],
        ).grid(row=0, column=0, padx=(18, 8), pady=14)
        self.mode_var = ctk.StringVar(value="Audio + Original Text")
        self.mode_menu = ctk.CTkOptionMenu(
            settings,
            variable=self.mode_var,
            values=["Audio + Original Text", "Text → MP3 + SRT", "Audio Only"],
            command=lambda _value: self._sync_mode_ui(),
            fg_color=THEME["gold_dark"],
            button_color=THEME["gold_dark"],
            button_hover_color=THEME["gold"],
            text_color="#06101E",
            width=180,
        )
        self.mode_menu.grid(row=0, column=1, sticky="w", pady=14)
        ctk.CTkLabel(
            settings,
            text="Language:",
            text_color=THEME["text"],
        ).grid(row=0, column=2, padx=(18, 8), pady=14)
        self.language_var = ctk.StringVar(value="Burmese")
        self.language_menu = ctk.CTkOptionMenu(
            settings,
            variable=self.language_var,
            values=["Burmese", "English", "Auto"],
            fg_color=THEME["gold_dark"],
            button_color=THEME["gold_dark"],
            button_hover_color=THEME["gold"],
            text_color="#06101E",
        )
        self.language_menu.grid(row=0, column=3, sticky="w", pady=14)
        ctk.CTkLabel(
            settings,
            text="SRT: Original Text Align / ASR fallback",
            text_color=THEME["text"],
        ).grid(row=0, column=4, padx=(12, 18), pady=14)

        self.original_text_box = ctk.CTkTextbox(
            root,
            fg_color=THEME["panel"],
            text_color=THEME["text"],
            height=130,
            font=("Myanmar Text", 14),
        )
        self.original_text_box.pack(fill="x", pady=(0, 12))
        self.original_text_box.insert(
            "1.0",
            "Original text / TTS text ကိုဒီမှာထည့်ပါ။ SRT text paste လုပ်ရင်လည်း timestamp/number တွေကိုဖယ်ပြီး text ကို align လုပ်မယ်။",
        )

        self.generate_button = ctk.CTkButton(
            root,
            text="Generate SRT",
            command=self._start_generation,
            fg_color=THEME["blue"],
            hover_color=THEME["gold"],
            text_color="#06101E",
            height=44,
            font=("Segoe UI", 18, "bold"),
        )
        self.generate_button.pack(fill="x", pady=(0, 12))

        self.progress = ctk.CTkProgressBar(root, progress_color=THEME["gold"])
        self.progress.set(0)
        self.progress.pack(fill="x", pady=(0, 10))

        self.status_label = ctk.CTkLabel(root, text="Ready", text_color=THEME["muted"])
        self.status_label.pack(anchor="w")

        self.preview = ctk.CTkTextbox(root, fg_color="#020712", text_color=THEME["text"], height=210)
        self.preview.pack(fill="both", expand=True, pady=(10, 0))
        self.preview.insert("1.0", "SRT preview will appear here...")
        self._sync_mode_ui()

    def _browse_file(self) -> None:
        patterns = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
        filename = filedialog.askopenfilename(
            title="Choose audio/video",
            filetypes=[("Media files", patterns), ("All files", "*.*")],
        )
        if filename:
            self.selected_file = Path(filename)
            self.file_label.configure(text=str(self.selected_file))

    def _start_generation(self) -> None:
        if self.mode_var.get() != "Text → MP3 + SRT" and self.selected_file is None:
            messagebox.showwarning(APP_NAME, "Audio/video file အရင်ရွေးပါ။")
            return
        self.generate_button.configure(state="disabled")
        self.progress.set(0.10)
        self.status_label.configure(text="Starting...")
        thread = threading.Thread(target=self._run_generation, daemon=True)
        thread.start()

    def _progress(self, message: str) -> None:
        self.events.put(("status", message))

    def _run_generation(self) -> None:
        try:
            if self.mode_var.get() == "Text → MP3 + SRT":
                text = self.original_text_box.get("1.0", "end").strip()
                output_dir = Path.home() / "Downloads" / "Music"
                base_name = "James_TTS"
                mp3_path, srt_path = generate_tts_mp3_and_srt(
                    text,
                    output_dir=output_dir,
                    base_name=base_name,
                    language_code=self._language_code() or "my",
                    progress=self._progress,
                )
                self.events.put(("done_tts", f"{mp3_path}|{srt_path}"))
                return
            if self.mode_var.get() == "Audio + Original Text":
                original_text = self.original_text_box.get("1.0", "end").strip()
                out_path = generate_srt_from_original_text(
                    self.selected_file,
                    original_text=original_text,
                    progress=self._progress,
                )
            else:
                self._progress("Checking local model...")
                model_dir = ensure_model(progress=self._progress)
                language_code = self._language_code()
                burmese_model_dir = None
                if language_code == "my":
                    burmese_model_dir = ensure_burmese_asr_model(progress=self._progress)
                out_path = generate_srt(
                    self.selected_file,
                    model_path_or_id=model_dir,
                    language_code=language_code,
                    burmese_model_dir=burmese_model_dir,
                    max_chars=DEFAULT_MAX_LINE_CHARS,
                    progress=self._progress,
                )
            self.events.put(("done", str(out_path)))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _language_code(self) -> str | None:
        value = self.language_var.get()
        if value == "Burmese":
            return "my"
        if value == "English":
            return "en"
        return None

    def _sync_mode_ui(self) -> None:
        if self.mode_var.get() in ("Audio + Original Text", "Text → MP3 + SRT"):
            self.original_text_box.configure(state="normal")
        else:
            self.original_text_box.configure(state="disabled")

    def _poll_events(self) -> None:
        while not self.events.empty():
            kind, message = self.events.get_nowait()
            if kind == "status":
                self.status_label.configure(text=message)
                self.progress.set(min(0.85, self.progress.get() + 0.12))
            elif kind == "done":
                self.progress.set(1)
                self.status_label.configure(text=f"Done: {message}")
                self.generate_button.configure(state="normal")
                out_path = Path(message)
                if out_path.exists():
                    self.preview.delete("1.0", "end")
                    self.preview.insert("1.0", out_path.read_text(encoding="utf-8-sig")[:4000])
            elif kind == "done_tts":
                mp3_text, srt_text = message.split("|", 1)
                self.progress.set(1)
                self.status_label.configure(text=f"Done: {mp3_text} / {srt_text}")
                self.generate_button.configure(state="normal")
                srt_path = Path(srt_text)
                if srt_path.exists():
                    self.preview.delete("1.0", "end")
                    self.preview.insert("1.0", srt_path.read_text(encoding="utf-8-sig")[:4000])
            elif kind == "error":
                self.progress.set(0)
                self.status_label.configure(text="Error")
                self.generate_button.configure(state="normal")
                messagebox.showerror(APP_NAME, message)
        self.after(200, self._poll_events)


def main() -> None:
    app = JamesSrtApp()
    app.mainloop()


if __name__ == "__main__":
    main()
