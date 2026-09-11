"""Modular cards component for the main dashboard view."""

import customtkinter as ctk
from typing import Callable, Optional
from ui.theme import THEME_COLORS


class BaseCard(ctk.CTkFrame):
    """Base class providing consistent styling and headers for dashboard cards."""

    def __init__(self, parent: ctk.CTkFrame, title: str, subtitle: str, **kwargs):
        super().__init__(
            parent,
            corner_radius=12,
            fg_color=(THEME_COLORS["card_light"], THEME_COLORS["card_dark"]),
            border_width=1,
            border_color=(THEME_COLORS["card_border_light"], THEME_COLORS["card_border_dark"]),
            **kwargs
        )
        self.pack_propagate(False)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))

        self.title_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self.title_label.pack(fill="x")

        self.subtitle_label = ctk.CTkLabel(
            header,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color="gray50",
            anchor="w"
        )
        self.subtitle_label.pack(fill="x")

        # Body
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=16, pady=(0, 14))


class SourceCard(BaseCard):
    """Card 1: Source directory picker and statistics badges."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        path_var: ctk.StringVar,
        on_browse: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, "📁 1. Source Folder", "Select image directory or book collection", **kwargs)

        input_row = ctk.CTkFrame(self.body, fg_color="transparent")
        input_row.pack(fill="x", pady=(4, 8))

        self.entry = ctk.CTkEntry(
            input_row,
            textvariable=path_var,
            placeholder_text="Choose folder...",
            height=34
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            input_row,
            text="Browse...",
            width=85,
            height=34,
            command=on_browse
        )
        self.browse_btn.pack(side="right")

        # Statistics badges
        self.stats_label = ctk.CTkLabel(
            self.body,
            text="No folder selected",
            font=ctk.CTkFont(size=12),
            text_color="gray50",
            anchor="w"
        )
        self.stats_label.pack(fill="x")


class CoverCard(BaseCard):
    """Card 2: Live cover thumbnail preview, auto-detection status, and pick buttons."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_choose_cover: Callable[[], None],
        on_reset_cover: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, "🖼️ 2. Cover Image", "Auto-detected or custom cover preview", **kwargs)

        preview_row = ctk.CTkFrame(self.body, fg_color="transparent")
        preview_row.pack(fill="both", expand=True)

        # Left: Thumbnail box
        self.thumb_box = ctk.CTkFrame(
            preview_row,
            width=80,
            height=110,
            corner_radius=8,
            fg_color=("gray85", "#262b35")
        )
        self.thumb_box.pack(side="left", padx=(0, 14))
        self.thumb_box.pack_propagate(False)

        self.thumb_label = ctk.CTkLabel(
            self.thumb_box,
            text="No\nCover",
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        )
        self.thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        # Right: Info & Buttons
        info_col = ctk.CTkFrame(preview_row, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)

        self.status_label = ctk.CTkLabel(
            info_col,
            text="No cover detected",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.pack(fill="x", pady=(0, 6))

        btn_row = ctk.CTkFrame(info_col, fg_color="transparent")
        btn_row.pack(fill="x")

        self.choose_btn = ctk.CTkButton(
            btn_row,
            text="Choose...",
            width=75,
            height=28,
            font=ctk.CTkFont(size=11),
            command=on_choose_cover
        )
        self.choose_btn.pack(side="left", padx=(0, 6))

        self.reset_btn = ctk.CTkButton(
            btn_row,
            text="Reset",
            width=65,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray85"),
            command=on_reset_cover
        )
        self.reset_btn.pack(side="left")


class MetadataCard(BaseCard):
    """Card 3: Book title, author, and language configuration."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        title_var: ctk.StringVar,
        author_var: ctk.StringVar,
        lang_var: ctk.StringVar,
        lang_options: list,
        **kwargs
    ):
        super().__init__(parent, "🏷️ 3. Metadata", "Book title, author, and language", **kwargs)

        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(grid, text="Title:", font=ctk.CTkFont(size=12), anchor="w").grid(row=0, column=0, sticky="w", pady=4)
        self.title_entry = ctk.CTkEntry(grid, textvariable=title_var, height=28)
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        # Author
        ctk.CTkLabel(grid, text="Author:", font=ctk.CTkFont(size=12), anchor="w").grid(row=1, column=0, sticky="w", pady=4)
        self.author_entry = ctk.CTkEntry(grid, textvariable=author_var, height=28)
        self.author_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)

        # Language
        ctk.CTkLabel(grid, text="Language:", font=ctk.CTkFont(size=12), anchor="w").grid(row=2, column=0, sticky="w", pady=4)
        self.lang_menu = ctk.CTkOptionMenu(
            grid,
            values=[opt[1] for opt in lang_options],
            variable=lang_var,
            height=28
        )
        self.lang_menu.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=4)


class LayoutCard(BaseCard):
    """Card 4: Manga Fixed-Layout and RTL reading progression switches."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        manga_var: ctk.BooleanVar,
        rtl_var: ctk.BooleanVar,
        on_manga_toggle: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, "🎨 4. Layout & Direction", "Manga / Comics reading optimizations", **kwargs)

        self.manga_switch = ctk.CTkSwitch(
            self.body,
            text="Manga / Fixed-Layout Mode",
            variable=manga_var,
            command=on_manga_toggle,
            font=ctk.CTkFont(size=12)
        )
        self.manga_switch.pack(anchor="w", pady=(8, 8))

        self.rtl_switch = ctk.CTkSwitch(
            self.body,
            text="Right-to-Left (RTL) Progression",
            variable=rtl_var,
            font=ctk.CTkFont(size=12)
        )
        self.rtl_switch.pack(anchor="w", pady=(0, 4))


class DestinationCard(BaseCard):
    """Card 5: EPUB output path and direct file/folder opening actions."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        path_var: ctk.StringVar,
        on_browse_output: Callable[[], None],
        on_open_epub: Callable[[], None],
        on_open_folder: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, "💾 5. EPUB Destination", "Output file or destination folder", **kwargs)

        row1 = ctk.CTkFrame(self.body, fg_color="transparent")
        row1.pack(fill="x", pady=(4, 8))

        self.entry = ctk.CTkEntry(
            row1,
            textvariable=path_var,
            placeholder_text="Output location...",
            height=34
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            row1,
            text="Browse...",
            width=85,
            height=34,
            command=on_browse_output
        )
        self.browse_btn.pack(side="right")

        # Open action buttons
        actions_row = ctk.CTkFrame(self.body, fg_color="transparent")
        actions_row.pack(fill="x")

        self.open_epub_btn = ctk.CTkButton(
            actions_row,
            text="📖 Open EPUB",
            width=110,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray85"),
            state="disabled",
            command=on_open_epub
        )
        self.open_epub_btn.pack(side="left", padx=(0, 8))

        self.open_dir_btn = ctk.CTkButton(
            actions_row,
            text="📂 Open Folder",
            width=110,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray85"),
            state="disabled",
            command=on_open_folder
        )
        self.open_dir_btn.pack(side="left")


class StatusCard(BaseCard):
    """Card 6: Real-time activity log snippet with quick link to Activity Log view."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_view_logs: Callable[[], None],
        **kwargs
    ):
        super().__init__(parent, "📋 6. Status & Activity", "Latest conversion events and logs", **kwargs)

        self.log_snippet = ctk.CTkLabel(
            self.body,
            text="Application ready. Awaiting folder selection.",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
            anchor="w",
            wraplength=350,
            justify="left"
        )
        self.log_snippet.pack(fill="both", expand=True, pady=(4, 6))

        self.view_logs_btn = ctk.CTkButton(
            self.body,
            text="Open Activity Log ➔",
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=THEME_COLORS["accent_blue"],
            hover_color=("gray90", "#262b35"),
            command=on_view_logs
        )
        self.view_logs_btn.pack(anchor="w")
