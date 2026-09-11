"""Hero header banner component displaying status, icon, and dynamic message."""

import customtkinter as ctk
from ui.theme import THEME_COLORS, STATUS_ICONS


class HeroHeaderComponent:
    """Renders the top dynamic hero status banner."""

    def __init__(self, parent: ctk.CTkFrame):
        self.parent = parent
        self.frame = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=(THEME_COLORS["hero_bg_light"], THEME_COLORS["hero_bg_dark"]),
            border_width=1,
            border_color=(THEME_COLORS["card_border_light"], THEME_COLORS["card_border_dark"])
        )
        self.frame.pack(fill="x", padx=20, pady=(16, 10))

        content = ctk.CTkFrame(self.frame, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=16)

        # Status icon badge
        self.status_badge = ctk.CTkLabel(
            content,
            text=STATUS_ICONS["shield"],
            font=ctk.CTkFont(size=36),
            width=50
        )
        self.status_badge.pack(side="left", padx=(0, 16))

        # Texts container
        text_box = ctk.CTkFrame(content, fg_color="transparent")
        text_box.pack(side="left", fill="both", expand=True)

        self.hero_title = ctk.CTkLabel(
            text_box,
            text="Welcome to EPUB Forge",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        )
        self.hero_title.pack(fill="x")

        self.hero_subtitle = ctk.CTkLabel(
            text_box,
            text="Select a source directory containing images, chapters, or a multi-book collection.",
            font=ctk.CTkFont(size=13),
            text_color="gray50",
            anchor="w"
        )
        self.hero_subtitle.pack(fill="x", pady=(2, 0))

    def update_state(self, icon_key: str, title: str, subtitle: str) -> None:
        """Updates the status icon, title, and subtitle text."""
        icon_str = STATUS_ICONS.get(icon_key, icon_key)
        self.status_badge.configure(text=icon_str)
        self.hero_title.configure(text=title)
        self.hero_subtitle.configure(text=subtitle)
