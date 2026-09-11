"""Application settings and information view."""

import customtkinter as ctk
from folder_to_epub.core.constants import APP_TITLE, APP_VERSION, SUPPORTED_EXTENSIONS
from folder_to_epub.ui.theme import THEME_COLORS


class SettingsView(ctk.CTkFrame):
    """Application metadata and configuration parameters."""

    def __init__(self, parent: ctk.CTkFrame):
        super().__init__(parent, fg_color="transparent")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="⚙️ Application Settings & Info",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(anchor="w")

        card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=(THEME_COLORS["card_light"], THEME_COLORS["card_dark"]),
            border_width=1,
            border_color=(THEME_COLORS["card_border_light"], THEME_COLORS["card_border_dark"])
        )
        card.pack(fill="both", expand=True, padx=24, pady=(10, 24))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        info_rows = [
            ("Application", f"{APP_TITLE} (Folder to EPUB)"),
            ("Version", APP_VERSION),
            ("Architecture", "Clean Architecture / Clean Code (Core, Services, CLI, UI)"),
            ("Supported Formats", ", ".join(sorted(SUPPORTED_EXTENSIONS))),
            ("EPUB Standard", "EPUB 3.0 (Pre-paginated & Manga RTL supported)"),
            ("Natural Sorting", "natsort (Strict alphanumeric ordering)"),
            ("Image Engine", "Pillow (Validation, dimensions inspection, MIME mapping)")
        ]

        for label, val in info_rows:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=8)

            lbl = ctk.CTkLabel(row, text=label + ":", font=ctk.CTkFont(size=13, weight="bold"), width=160, anchor="w")
            lbl.pack(side="left")

            val_lbl = ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=13), text_color="gray50", anchor="w")
            val_lbl.pack(side="left", fill="x", expand=True)
