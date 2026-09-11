"""Sidebar navigation and theme selector component."""

import customtkinter as ctk
from typing import Callable, Dict
from ui.theme import THEME_COLORS


class SidebarComponent:
    """Manages the left sidebar UI, tabs, and appearance switcher."""

    def __init__(
        self,
        parent: ctk.CTk,
        on_navigate: Callable[[str], None],
        on_theme_change: Callable[[str], None]
    ):
        self.parent = parent
        self.on_navigate = on_navigate
        self.on_theme_change = on_theme_change
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

        self.frame = ctk.CTkFrame(
            parent,
            width=210,
            corner_radius=0,
            fg_color=(THEME_COLORS["sidebar_light"], THEME_COLORS["sidebar_dark"])
        )
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_rowconfigure(5, weight=1)

        self._build_brand()
        self._build_navigation()
        self._build_footer()

    def _build_brand(self) -> None:
        """Renders the top branding block."""
        brand_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=16, pady=(24, 20), sticky="ew")

        logo_icon = ctk.CTkLabel(brand_frame, text="📚", font=ctk.CTkFont(size=26))
        logo_icon.pack(side="left", padx=(0, 10))

        brand_text_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_text_box.pack(side="left", fill="x")

        brand_title = ctk.CTkLabel(
            brand_text_box,
            text="EPUB Forge",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        brand_title.pack(anchor="w")

        brand_subtitle = ctk.CTkLabel(
            brand_text_box,
            text="Pro Converter",
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        )
        brand_subtitle.pack(anchor="w")

    def _build_navigation(self) -> None:
        """Renders the navigation menu items."""
        nav_items = [
            ("dashboard", "⚡ Dashboard"),
            ("chapters", "📚 Books & Chapters"),
            ("logs", "📋 Activity Log"),
            ("settings", "⚙️ Settings")
        ]

        for idx, (view_id, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.frame,
                text=label,
                anchor="w",
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="normal"),
                fg_color="transparent",
                text_color=("gray20", "gray85"),
                hover_color=("gray85", "#262b35"),
                command=lambda v=view_id: self.on_navigate(v)
            )
            btn.grid(row=idx, column=0, padx=12, pady=4, sticky="ew")
            self.nav_buttons[view_id] = btn

    def _build_footer(self) -> None:
        """Renders the theme switcher at the bottom."""
        footer_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer_frame.grid(row=6, column=0, padx=16, pady=16, sticky="s")

        theme_label = ctk.CTkLabel(
            footer_frame,
            text="APPEARANCE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray50"
        )
        theme_label.pack(anchor="w", pady=(0, 4))

        theme_switch = ctk.CTkSegmentedButton(
            footer_frame,
            values=["System", "Dark", "Light"],
            command=self.on_theme_change,
            height=26,
            font=ctk.CTkFont(size=11)
        )
        theme_switch.set("System")
        theme_switch.pack(fill="x")

    def set_active_tab(self, active_view_id: str) -> None:
        """Updates button highlighting to reflect active tab."""
        for v_id, btn in self.nav_buttons.items():
            if v_id == active_view_id:
                btn.configure(
                    fg_color=(THEME_COLORS["accent_blue"], THEME_COLORS["accent_blue"]),
                    text_color="#ffffff"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray20", "gray85")
                )
