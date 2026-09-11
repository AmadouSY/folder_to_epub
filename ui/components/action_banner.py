"""Action banner component containing progress indicators, batch toggle, and primary CTA."""

import customtkinter as ctk
from typing import Callable
from ui.theme import THEME_COLORS


class ActionBannerComponent:
    """Manages the action toolbar with convert button, batch switch, and progress bar."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        batch_var: ctk.BooleanVar,
        on_batch_toggle: Callable[[], None],
        on_convert_click: Callable[[], None]
    ):
        self.parent = parent
        self.batch_var = batch_var
        self.on_batch_toggle = on_batch_toggle
        self.on_convert_click = on_convert_click

        self.frame = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=(THEME_COLORS["card_light"], THEME_COLORS["card_dark"]),
            border_width=1,
            border_color=(THEME_COLORS["card_border_light"], THEME_COLORS["card_border_dark"])
        )
        self.frame.pack(fill="x", padx=20, pady=(0, 16))

        inner = ctk.CTkFrame(self.frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=14)

        # Left: Status description & Batch switch
        left_box = ctk.CTkFrame(inner, fg_color="transparent")
        left_box.pack(side="left", fill="x", expand=True)

        self.action_status_label = ctk.CTkLabel(
            left_box,
            text="Ready to convert",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self.action_status_label.pack(fill="x")

        controls_row = ctk.CTkFrame(left_box, fg_color="transparent")
        controls_row.pack(fill="x", pady=(4, 0))

        self.batch_switch = ctk.CTkSwitch(
            controls_row,
            text="Multi-Book (Batch) Mode",
            variable=self.batch_var,
            command=self.on_batch_toggle,
            font=ctk.CTkFont(size=12)
        )
        self.batch_switch.pack(side="left")

        # Center/Right: Progress display
        self.progress_container = ctk.CTkFrame(inner, fg_color="transparent")
        self.progress_container.pack(side="left", fill="x", expand=True, padx=20)

        self.progress_label = ctk.CTkLabel(
            self.progress_container,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray50"
        )
        self.progress_label.pack(anchor="e")

        self.progress_bar = ctk.CTkProgressBar(self.progress_container, height=10)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", pady=(2, 0))

        # Right: Big CTA Button
        self.convert_button = ctk.CTkButton(
            inner,
            text="🚀 Convert to EPUB",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            corner_radius=8,
            fg_color=THEME_COLORS["accent_blue"],
            hover_color=THEME_COLORS["accent_blue_hover"],
            command=self.on_convert_click
        )
        self.convert_button.pack(side="right")

    def set_status(self, text: str) -> None:
        self.action_status_label.configure(text=text)

    def set_progress(self, ratio: float, label: str = "") -> None:
        self.progress_bar.set(ratio)
        self.progress_label.configure(text=label or f"{int(ratio * 100)}%")

    def set_button_state(self, enabled: bool, text: str = "") -> None:
        self.convert_button.configure(state="normal" if enabled else "disabled")
        if text:
            self.convert_button.configure(text=text)
