"""Activity log console view."""

import customtkinter as ctk
from folder_to_epub.ui.theme import THEME_COLORS


class LogsView(ctk.CTkFrame):
    """Activity log console display."""

    def __init__(self, parent: ctk.CTkFrame):
        super().__init__(parent, fg_color="transparent")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="📋 Activity Log Console",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(side="left")

        clear_btn = ctk.CTkButton(
            header,
            text="Clear Log",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray85"),
            command=self.clear
        )
        clear_btn.pack(side="right")

        self.text_box = ctk.CTkTextbox(
            self,
            corner_radius=12,
            fg_color=(THEME_COLORS["card_light"], THEME_COLORS["card_dark"]),
            border_width=1,
            border_color=(THEME_COLORS["card_border_light"], THEME_COLORS["card_border_dark"]),
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.text_box.pack(fill="both", expand=True, padx=24, pady=(10, 24))

    def append_log(self, text: str) -> None:
        self.text_box.insert("end", text + "\n")
        self.text_box.see("end")

    def clear(self) -> None:
        self.text_box.delete("1.0", "end")
