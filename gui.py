#!/usr/bin/env python3
"""
Folder to EPUB Converter - Modern GUI
=====================================
Modern, responsive and intuitive user interface inspired by dashboard design
(Bitdefender style) with full support for:
- Single Book Mode (single or multi-chapter)
- Multi-Book Mode (Batch processing)
"""

import os
import sys
import threading
from pathlib import Path
from typing import Optional, List

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
except ImportError:
    sys.exit("Error: 'customtkinter' is required. Install it using 'pip install customtkinter'.")

try:
    from PIL import Image, ImageTk
except ImportError:
    sys.exit("Error: 'Pillow' is required. Install it using 'pip install Pillow'.")

# Import conversion engine from folder_to_epub.py
from folder_to_epub import (
    collect_chapters_and_images,
    create_epub,
    create_epub_batch,
    find_root_cover,
    detect_books,
    ChapterData,
    BookData,
    SUPPORTED_EXTENSIONS
)


class FolderToEpubApp(ctk.CTk):
    """Main application window with modern Dashboard / Sidebar layout."""

    def __init__(self):
        super().__init__()

        # Main window configuration
        self.title("Folder to EPUB Converter")
        self.geometry("1080x760")
        self.minsize(940, 640)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # State variables
        self.source_dir: Optional[Path] = None
        self.output_file: Optional[Path] = None
        self.custom_cover_file: Optional[Path] = None
        self.auto_root_cover: Optional[Path] = None
        
        # Books and chapters data
        self.is_batch_mode: bool = False
        self.books: List[BookData] = []
        self.chapters: List[ChapterData] = []
        self.total_images_count: int = 0
        
        self.is_converting: bool = False
        self.cover_thumbnail_image: Optional[ctk.CTkImage] = None

        # Tk control variables
        self.title_var = ctk.StringVar(value="")
        self.author_var = ctk.StringVar(value="Unknown")
        self.lang_var = ctk.StringVar(value="en")
        self.manga_mode_var = ctk.BooleanVar(value=False)
        self.rtl_mode_var = ctk.BooleanVar(value=False)
        self.batch_switch_var = ctk.BooleanVar(value=False)
        self.source_path_var = ctk.StringVar(value="")
        self.output_path_var = ctk.StringVar(value="")
        self.cover_path_var = ctk.StringVar(value="")

        # Color palette
        self.colors = {
            "sidebar_light": "#f4f5f8",
            "sidebar_dark": "#16191f",
            "card_light": "#ffffff",
            "card_dark": "#1e222b",
            "card_border_light": "#e2e6ea",
            "card_border_dark": "#2b303c",
            "accent_blue": "#1a73e8",
            "accent_blue_hover": "#1557b0",
            "success_green": "#0f9d58",
            "hero_bg_light": "#ffffff",
            "hero_bg_dark": "#1f242d"
        }

        # Build UI layout
        self._build_main_layout()

        # Display dashboard view by default
        self._show_view("dashboard")

    def _build_main_layout(self):
        """Sets up overall layout with left sidebar and dynamic view container."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Left Sidebar
        self._build_sidebar()

        # 2. Main Content Container
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray94", "#121418"))
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Build individual views
        self.views = {}
        self._build_dashboard_view()
        self._build_chapters_view()
        self._build_logs_view()
        self._build_settings_view()

    def _build_sidebar(self):
        """Constructs the sidebar with logo, navigation tabs, and theme selector."""
        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=210,
            corner_radius=0,
            fg_color=(self.colors["sidebar_light"], self.colors["sidebar_dark"])
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        # Brand / App Header
        brand_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=16, pady=(24, 20), sticky="ew")

        logo_icon = ctk.CTkLabel(
            brand_frame,
            text="📚",
            font=ctk.CTkFont(size=26)
        )
        logo_icon.pack(side="left", padx=(0, 10))

        brand_text_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_text_box.pack(side="left", fill="x")

        brand_title = ctk.CTkLabel(
            brand_text_box,
            text="EPUB Forge",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        brand_title.pack(anchor="w")

        brand_sub = ctk.CTkLabel(
            brand_text_box,
            text="Pro Converter",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        )
        brand_sub.pack(anchor="w")

        # Separator
        sep = ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=("gray80", "gray25"))
        sep.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 15))

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "⚡ Dashboard"),
            ("chapters", "📚 Books & Chapters"),
            ("logs", "📋 Activity Log"),
            ("settings", "⚙️ Settings")
        ]

        for idx, (view_id, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=label,
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray20", "gray85"),
                hover_color=("gray85", "gray25"),
                font=ctk.CTkFont(size=13, weight="normal"),
                command=lambda v=view_id: self._show_view(v)
            )
            btn.grid(row=idx, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[view_id] = btn

        # Bottom sidebar: theme selector
        bottom_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        bottom_frame.grid(row=6, column=0, padx=14, pady=16, sticky="ew")

        theme_lbl = ctk.CTkLabel(bottom_frame, text="Theme:", font=ctk.CTkFont(size=11), text_color="gray")
        theme_lbl.pack(anchor="w", pady=(0, 4))

        self.theme_menu = ctk.CTkSegmentedButton(
            bottom_frame,
            values=["System", "Dark", "Light"],
            command=self._change_theme
        )
        self.theme_menu.set("System")
        self.theme_menu.pack(fill="x")

    def _show_view(self, view_name: str):
        """Switches display to the chosen navigation tab."""
        for v_id, view_frame in self.views.items():
            view_frame.grid_forget()

        if view_name in self.views:
            self.views[view_name].grid(row=0, column=0, sticky="nsew")

        # Update button active states
        for v_id, btn in self.nav_buttons.items():
            if v_id == view_name:
                btn.configure(
                    fg_color=(self.colors["accent_blue"], self.colors["accent_blue"]),
                    text_color="#ffffff",
                    font=ctk.CTkFont(size=13, weight="bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray20", "gray85"),
                    font=ctk.CTkFont(size=13, weight="normal")
                )

    # -------------------------------------------------------------
    # VIEW 1: DASHBOARD
    # -------------------------------------------------------------
    def _build_dashboard_view(self):
        """Constructs main dashboard view with Hero header, action banner, and cards grid."""
        dash_scroll = ctk.CTkScrollableFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.views["dashboard"] = dash_scroll

        # 1. HERO HEADER
        hero_frame = ctk.CTkFrame(dash_scroll, fg_color="transparent")
        hero_frame.pack(fill="x", padx=28, pady=(24, 12))

        self.status_icon_badge = ctk.CTkLabel(
            hero_frame,
            text="🛡️",
            font=ctk.CTkFont(size=44),
            width=65,
            height=65
        )
        self.status_icon_badge.pack(side="left", padx=(0, 16))

        hero_text_box = ctk.CTkFrame(hero_frame, fg_color="transparent")
        hero_text_box.pack(side="left", fill="x", expand=True)

        self.hero_status_title = ctk.CTkLabel(
            hero_text_box,
            text="Ready to Convert",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        self.hero_status_title.pack(anchor="w")

        self.hero_status_sub = ctk.CTkLabel(
            hero_text_box,
            text="Select a folder containing your images or books to begin.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.hero_status_sub.pack(anchor="w", pady=(2, 0))

        # 2. MAIN ACTION BANNER
        self._build_action_banner(dash_scroll)

        # 3. INTERACTIVE CARDS GRID
        self._build_cards_grid(dash_scroll)

    def _build_action_banner(self, parent):
        """Action banner showing project status, batch toggle, and primary CTA."""
        self.action_banner = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=(self.colors["card_light"], self.colors["hero_bg_dark"]),
            border_width=1,
            border_color=(self.colors["card_border_light"], self.colors["card_border_dark"])
        )
        self.action_banner.pack(fill="x", padx=28, pady=(0, 18))

        top_row = ctk.CTkFrame(self.action_banner, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(16, 12))

        # Status info
        banner_info = ctk.CTkFrame(top_row, fg_color="transparent")
        banner_info.pack(side="left", fill="x", expand=True)

        info_header = ctk.CTkFrame(banner_info, fg_color="transparent")
        info_header.pack(anchor="w")

        banner_icon = ctk.CTkLabel(info_header, text="⚡", font=ctk.CTkFont(size=16))
        banner_icon.pack(side="left", padx=(0, 6))

        self.banner_title = ctk.CTkLabel(
            info_header,
            text="Project Status",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.banner_title.pack(side="left")

        self.banner_desc = ctk.CTkLabel(
            banner_info,
            text="No folder analyzed yet. Click 'Browse' to load your book or collection.",
            font=ctk.CTkFont(size=12),
            text_color=("gray30", "gray65"),
            justify="left",
            anchor="w"
        )
        self.banner_desc.pack(anchor="w", pady=(4, 0))

        # Action buttons and Batch toggle
        btn_box = ctk.CTkFrame(top_row, fg_color="transparent")
        btn_box.pack(side="right", padx=(10, 0))

        self.batch_switch = ctk.CTkSwitch(
            btn_box,
            text="Multi-Book Mode (Batch)",
            variable=self.batch_switch_var,
            command=self._on_batch_toggle,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.batch_switch.pack(side="left", padx=(0, 16))

        self.main_convert_btn = ctk.CTkButton(
            btn_box,
            text="🚀 Convert to EPUB",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color=self.colors["accent_blue"],
            hover_color=self.colors["accent_blue_hover"],
            command=self._start_conversion
        )
        self.main_convert_btn.pack(side="right")

        # Integrated progress bar
        prog_row = ctk.CTkFrame(self.action_banner, fg_color="transparent")
        prog_row.pack(fill="x", padx=20, pady=(0, 14))

        self.progress_bar = ctk.CTkProgressBar(
            prog_row,
            height=8,
            corner_radius=4,
            progress_color=self.colors["accent_blue"]
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 14))
        self.progress_bar.set(0.0)

        self.progress_label = ctk.CTkLabel(
            prog_row,
            text="0%",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=40
        )
        self.progress_label.pack(side="right")

    def _build_cards_grid(self, parent):
        """Constructs modular grid of action cards."""
        grid_container = ctk.CTkFrame(parent, fg_color="transparent")
        grid_container.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        grid_container.grid_columnconfigure(0, weight=1)
        grid_container.grid_columnconfigure(1, weight=1)

        # ---- CARD 1: SOURCE FOLDER ----
        c1 = self._create_card(grid_container, "📁 Source Folder (Images / Books)", row=0, col=0)
        
        self.card_source_path_lbl = ctk.CTkLabel(
            c1,
            textvariable=self.source_path_var,
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.card_source_path_lbl.pack(fill="x", padx=16, pady=(4, 8))

        c1_btn_row = ctk.CTkFrame(c1, fg_color="transparent")
        c1_btn_row.pack(fill="x", padx=16, pady=(0, 14))

        browse_src_btn = ctk.CTkButton(
            c1_btn_row,
            text="Browse Folder...",
            height=32,
            corner_radius=6,
            command=self._browse_source_directory
        )
        browse_src_btn.pack(side="left")

        self.card_source_stats = ctk.CTkLabel(
            c1_btn_row,
            text="0 chapters • 0 images",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray30", "gray70")
        )
        self.card_source_stats.pack(side="right")

        # ---- CARD 2: COVER & THUMBNAIL ----
        c2 = self._create_card(grid_container, "🖼️ Cover & Thumbnail Preview", row=0, col=1)

        c2_content = ctk.CTkFrame(c2, fg_color="transparent")
        c2_content.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        self.thumb_label = ctk.CTkLabel(
            c2_content,
            text="No\nPreview",
            width=70,
            height=95,
            fg_color=("gray88", "gray22"),
            corner_radius=6
        )
        self.thumb_label.pack(side="left", padx=(0, 14))

        c2_actions = ctk.CTkFrame(c2_content, fg_color="transparent")
        c2_actions.pack(side="left", fill="both", expand=True)

        self.cover_status_lbl = ctk.CTkLabel(
            c2_actions,
            text="Cover: Automatic (1st page)",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.cover_status_lbl.pack(anchor="w", pady=(0, 8))

        c2_btns = ctk.CTkFrame(c2_actions, fg_color="transparent")
        c2_btns.pack(anchor="w")

        self.change_cover_btn = ctk.CTkButton(
            c2_btns,
            text="Browse...",
            width=90,
            height=30,
            corner_radius=6,
            command=self._browse_custom_cover
        )
        self.change_cover_btn.pack(side="left", padx=(0, 8))

        self.clear_cover_btn = ctk.CTkButton(
            c2_btns,
            text="Reset",
            width=80,
            height=30,
            corner_radius=6,
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            text_color=("gray10", "gray90"),
            command=self._clear_custom_cover
        )
        self.clear_cover_btn.pack(side="left")

        # ---- CARD 3: METADATA ----
        c3 = self._create_card(grid_container, "📝 Metadata & Author", row=1, col=0)

        c3_form = ctk.CTkFrame(c3, fg_color="transparent")
        c3_form.pack(fill="x", padx=16, pady=(4, 14))

        ctk.CTkLabel(c3_form, text="Title:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", pady=4)
        self.title_entry = ctk.CTkEntry(c3_form, textvariable=self.title_var, height=30, placeholder_text="Book title")
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        ctk.CTkLabel(c3_form, text="Author:", font=ctk.CTkFont(size=12)).grid(row=1, column=0, sticky="w", pady=4)
        self.author_entry = ctk.CTkEntry(c3_form, textvariable=self.author_var, height=30, placeholder_text="Author")
        self.author_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)

        ctk.CTkLabel(c3_form, text="Language:", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", pady=4)
        self.lang_menu = ctk.CTkOptionMenu(
            c3_form,
            variable=self.lang_var,
            values=["en", "fr", "ja", "es", "de", "it", "ko", "zh"],
            height=30,
            width=100
        )
        self.lang_menu.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=4)
        c3_form.grid_columnconfigure(1, weight=1)

        # ---- CARD 4: FORMATTING & READING OPTIONS ----
        c4 = self._create_card(grid_container, "⚙️ Formatting & Reading Options", row=1, col=1)

        c4_content = ctk.CTkFrame(c4, fg_color="transparent")
        c4_content.pack(fill="x", padx=16, pady=(6, 14))

        self.manga_switch = ctk.CTkSwitch(
            c4_content,
            text="Manga / Comic Mode (Fixed-Layout EPUB 3)",
            variable=self.manga_mode_var,
            command=self._on_manga_toggle,
            font=ctk.CTkFont(size=12)
        )
        self.manga_switch.pack(anchor="w", pady=(0, 10))

        self.rtl_switch = ctk.CTkSwitch(
            c4_content,
            text="Right-To-Left Reading Direction (RTL)",
            variable=self.rtl_mode_var,
            font=ctk.CTkFont(size=12)
        )
        self.rtl_switch.pack(anchor="w", pady=(0, 8))

        badge_info = ctk.CTkLabel(
            c4_content,
            text="ℹ️ Optimized for Kindle, Kobo, and Apple Books.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        badge_info.pack(anchor="w")

        # ---- CARD 5: OUTPUT DESTINATION ----
        c5 = self._create_card(grid_container, "📦 Output Destination", row=2, col=0)

        self.card_output_lbl = ctk.CTkLabel(
            c5,
            textvariable=self.output_path_var,
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.card_output_lbl.pack(fill="x", padx=16, pady=(4, 8))

        c5_btn_row = ctk.CTkFrame(c5, fg_color="transparent")
        c5_btn_row.pack(fill="x", padx=16, pady=(0, 14))

        self.browse_out_btn = ctk.CTkButton(
            c5_btn_row,
            text="Change Location...",
            height=32,
            corner_radius=6,
            command=self._browse_output_file
        )
        self.browse_out_btn.pack(side="left")

        self.open_file_btn = ctk.CTkButton(
            c5_btn_row,
            text="📖 Open",
            width=75,
            height=32,
            corner_radius=6,
            fg_color=self.colors["success_green"],
            hover_color="#0b8043",
            command=self._open_output_file
        )
        self.open_folder_btn = ctk.CTkButton(
            c5_btn_row,
            text="📂 Folder",
            width=80,
            height=32,
            corner_radius=6,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self._open_output_folder
        )

        # ---- CARD 6: SUMMARY & ACTIVITY ----
        c6 = self._create_card(grid_container, "📊 Summary & Activity", row=2, col=1)

        c6_content = ctk.CTkFrame(c6, fg_color="transparent")
        c6_content.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        self.card_log_preview = ctk.CTkLabel(
            c6_content,
            text="Log: System ready.\nNo active conversion.",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=("gray30", "gray70"),
            justify="left",
            anchor="w"
        )
        self.card_log_preview.pack(fill="x", pady=(0, 8))

        see_logs_btn = ctk.CTkButton(
            c6_content,
            text="View full activity log ➜",
            height=30,
            corner_radius=6,
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=self.colors["accent_blue"],
            command=lambda: self._show_view("logs")
        )
        see_logs_btn.pack(anchor="w")

    def _create_card(self, parent, title: str, row: int, col: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=(self.colors["card_light"], self.colors["card_dark"]),
            border_width=1,
            border_color=(self.colors["card_border_light"], self.colors["card_border_dark"])
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        title_lbl = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        title_lbl.pack(fill="x", padx=16, pady=(12, 4))
        return card

    # -------------------------------------------------------------
    # VIEW 2: BOOKS & CHAPTERS EXPLORER
    # -------------------------------------------------------------
    def _build_chapters_view(self):
        chapters_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.views["chapters"] = chapters_frame

        header = ctk.CTkFrame(chapters_frame, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 12))

        self.chapters_view_title = ctk.CTkLabel(
            header,
            text="📚 Books & Chapters",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.chapters_view_title.pack(anchor="w")

        self.chapters_view_sub = ctk.CTkLabel(
            header,
            text="Preview of items ready to be converted into EPUB.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60")
        )
        self.chapters_view_sub.pack(anchor="w", pady=(2, 0))

        self.chapters_scroll = ctk.CTkScrollableFrame(chapters_frame, corner_radius=12)
        self.chapters_scroll.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        self.empty_chapters_lbl = ctk.CTkLabel(
            self.chapters_scroll,
            text="No folder selected.\nLoad a folder from the Dashboard.",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.empty_chapters_lbl.pack(pady=50)

    def _update_chapters_view_list(self):
        for widget in self.chapters_scroll.winfo_children():
            widget.destroy()

        if self.is_batch_mode and self.books:
            self.chapters_view_title.configure(text=f"📚 Collection: {len(self.books)} Books Detected")
            self.chapters_view_sub.configure(text="Each book below will be generated as an independent .epub file.")

            for idx, book in enumerate(self.books, start=1):
                row = ctk.CTkFrame(
                    self.chapters_scroll,
                    corner_radius=8,
                    fg_color=(self.colors["card_light"], self.colors["card_dark"]),
                    border_width=1,
                    border_color=(self.colors["card_border_light"], self.colors["card_border_dark"])
                )
                row.pack(fill="x", pady=5, padx=4)

                badge = ctk.CTkLabel(
                    row,
                    text=f"#{idx:02d}",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    width=45,
                    text_color=self.colors["accent_blue"]
                )
                badge.pack(side="left", padx=10, pady=12)

                if book.cover_path and book.cover_path.exists():
                    try:
                        with Image.open(book.cover_path) as c_img:
                            c_copy = c_img.convert("RGB")
                            c_copy.thumbnail((45, 60), Image.Resampling.LANCZOS)
                            t_img = ctk.CTkImage(light_image=c_copy, dark_image=c_copy, size=c_copy.size)
                            cov_lbl = ctk.CTkLabel(row, image=t_img, text="", width=45)
                            cov_lbl.pack(side="left", padx=(0, 10))
                    except Exception:
                        pass

                title_info = ctk.CTkFrame(row, fg_color="transparent")
                title_info.pack(side="left", fill="x", expand=True, pady=8)

                c_title = ctk.CTkLabel(title_info, text=book.title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
                c_title.pack(anchor="w")

                c_sub = ctk.CTkLabel(
                    title_info,
                    text=f"Folder: {book.folder_path.name} • Cover: {book.cover_path.name if book.cover_path else '1st page'}",
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                    anchor="w"
                )
                c_sub.pack(anchor="w")

                stats_box = ctk.CTkFrame(row, fg_color="transparent")
                stats_box.pack(side="right", padx=14)

                ch_badge = ctk.CTkLabel(
                    stats_box,
                    text=f"{len(book.chapters)} chap.",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=("gray90", "gray25"),
                    corner_radius=6,
                    width=65,
                    height=26
                )
                ch_badge.pack(side="left", padx=(0, 6))

                pg_badge = ctk.CTkLabel(
                    stats_box,
                    text=f"{book.total_images} pages",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=(self.colors["accent_blue"], self.colors["accent_blue"]),
                    text_color="#ffffff",
                    corner_radius=6,
                    width=75,
                    height=26
                )
                pg_badge.pack(side="left")

        elif self.chapters:
            self.chapters_view_title.configure(text=f"📖 Book Chapters ({len(self.chapters)} chapters)")
            self.chapters_view_sub.configure(text="Sequential list of chapters composing this digital book.")

            for idx, chap in enumerate(self.chapters, start=1):
                row = ctk.CTkFrame(
                    self.chapters_scroll,
                    corner_radius=8,
                    fg_color=(self.colors["card_light"], self.colors["card_dark"]),
                    border_width=1,
                    border_color=(self.colors["card_border_light"], self.colors["card_border_dark"])
                )
                row.pack(fill="x", pady=4, padx=4)

                badge = ctk.CTkLabel(
                    row,
                    text=f"#{idx:02d}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    width=45,
                    text_color=self.colors["accent_blue"]
                )
                badge.pack(side="left", padx=10, pady=10)

                title_info = ctk.CTkFrame(row, fg_color="transparent")
                title_info.pack(side="left", fill="x", expand=True, pady=8)

                c_title = ctk.CTkLabel(title_info, text=chap.title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
                c_title.pack(anchor="w")

                first_img = chap.pages[0].file_path.name if chap.pages else "No image"
                c_sub = ctk.CTkLabel(
                    title_info,
                    text=f"First page: {first_img}",
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                    anchor="w"
                )
                c_sub.pack(anchor="w")

                pages_badge = ctk.CTkLabel(
                    row,
                    text=f"{len(chap.pages)} pages",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    fg_color=("gray90", "gray25"),
                    corner_radius=6,
                    width=80,
                    height=26
                )
                pages_badge.pack(side="right", padx=14)
        else:
            self.empty_chapters_lbl = ctk.CTkLabel(
                self.chapters_scroll,
                text="No valid content found in this folder.",
                font=ctk.CTkFont(size=13),
                text_color="gray"
            )
            self.empty_chapters_lbl.pack(pady=50)

    # -------------------------------------------------------------
    # VIEW 3: ACTIVITY LOG
    # -------------------------------------------------------------
    def _build_logs_view(self):
        logs_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.views["logs"] = logs_frame

        header = ctk.CTkFrame(logs_frame, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 12))

        ctk.CTkLabel(header, text="📋 Detailed Activity Log", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        clear_btn = ctk.CTkButton(
            header,
            text="Clear Log",
            width=120,
            height=32,
            corner_radius=6,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self._clear_logs
        )
        clear_btn.pack(side="right")

        self.full_log_textbox = ctk.CTkTextbox(
            logs_frame,
            corner_radius=12,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=(self.colors["card_light"], self.colors["card_dark"]),
            border_width=1,
            border_color=(self.colors["card_border_light"], self.colors["card_border_dark"]),
            state="disabled"
        )
        self.full_log_textbox.pack(fill="both", expand=True, padx=28, pady=(0, 24))

    # -------------------------------------------------------------
    # VIEW 4: SETTINGS
    # -------------------------------------------------------------
    def _build_settings_view(self):
        settings_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.views["settings"] = settings_frame

        header = ctk.CTkFrame(settings_frame, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 16))

        ctk.CTkLabel(header, text="⚙️ Settings & Information", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")

        content = ctk.CTkScrollableFrame(settings_frame, corner_radius=12)
        content.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        info_card = ctk.CTkFrame(
            content,
            corner_radius=12,
            fg_color=(self.colors["card_light"], self.colors["card_dark"]),
            border_width=1,
            border_color=(self.colors["card_border_light"], self.colors["card_border_dark"])
        )
        info_card.pack(fill="x", pady=8, padx=4)

        ctk.CTkLabel(info_card, text="ℹ️ About EPUB Forge", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(14, 4))
        desc = (
            "Folder to EPUB Converter (EPUB Forge)\n"
            "Version 2.5 • Multi-Book Batch Processing & Single Book Engine.\n\n"
            "• Natural alphanumeric sorting (natsort)\n"
            "• Automatic detection of book collections and individual covers\n"
            "• Fixed-Layout EPUB 3 and Manga Right-To-Left (RTL) reading support\n"
            "• Non-blocking multi-threaded conversion with live progress tracking."
        )
        ctk.CTkLabel(info_card, text=desc, justify="left", font=ctk.CTkFont(size=12), text_color=("gray30", "gray70")).pack(anchor="w", padx=16, pady=(0, 14))

    # -------------------------------------------------------------
    # CALLBACKS & LOGIC
    # -------------------------------------------------------------

    def _change_theme(self, choice: str):
        mapping = {"System": "System", "Dark": "Dark", "Light": "Light"}
        ctk.set_appearance_mode(mapping.get(choice, "System"))

    def _on_manga_toggle(self):
        if self.manga_mode_var.get():
            self.rtl_mode_var.set(True)

    def _on_batch_toggle(self):
        if self.source_dir and self.source_dir.exists():
            self._analyze_source_directory(force_batch=self.batch_switch_var.get())

    def _browse_source_directory(self):
        folder = filedialog.askdirectory(title="Select Source Folder (Images or Collection)")
        if not folder:
            return

        source_path = Path(folder)
        self.source_dir = source_path
        self.source_path_var.set(str(source_path))

        self._analyze_source_directory(force_batch=None)

    def _analyze_source_directory(self, force_batch: Optional[bool] = None):
        if not self.source_dir or not self.source_dir.exists():
            return

        self._log(f"Scanning folder: {self.source_dir} (force_batch={force_batch})...")
        try:
            is_batch, detected_books = detect_books(self.source_dir, force_batch=force_batch)

            if not detected_books:
                self.hero_status_title.configure(text="⚠️ No Images Found")
                self.hero_status_sub.configure(text="The selected folder contains no valid images (JPG, PNG, WEBP, GIF).")
                self.status_icon_badge.configure(text="⚠️")
                self.card_source_stats.configure(text="0 images")
                self._update_cover_thumbnail(None)
                self._log("Warning: No valid images found in this folder.")
                return

            self.books = detected_books
            self.is_batch_mode = is_batch and len(detected_books) > 1
            self.batch_switch_var.set(self.is_batch_mode)

            if self.is_batch_mode:
                # BATCH MODE
                self.total_images_count = sum(b.total_images for b in self.books)
                default_out_dir = self.source_dir.parent / f"{self.source_dir.name}_epubs"
                self.output_file = default_out_dir
                self.output_path_var.set(str(default_out_dir))

                stats_text = f"{len(self.books)} books • {self.total_images_count} total pages"
                self.card_source_stats.configure(text=stats_text)

                self.hero_status_title.configure(text=f"Collection Ready ({len(self.books)} Books)")
                self.hero_status_sub.configure(text=f"{self.source_dir.name} ({stats_text})")
                self.status_icon_badge.configure(text="📚")

                self.banner_title.configure(text=f"Batch Mode: {len(self.books)} EPUBs to Create")
                self.banner_desc.configure(text="Each book subdirectory will be compiled into an independent .epub file in the output folder.")
                self.main_convert_btn.configure(text=f"🚀 Convert {len(self.books)} Books")

                # Cover card
                first_cover = self.books[0].cover_path if self.books else None
                self._update_cover_thumbnail(first_cover)
                self.cover_status_lbl.configure(text=f"Individual covers ({len(self.books)} books)")
                self.change_cover_btn.configure(state="disabled")
                self.clear_cover_btn.configure(state="disabled")

                # Metadata card
                self.title_entry.configure(state="disabled", placeholder_text="[Folder names used as titles]")
                self.title_var.set("")

                # Destination card
                self.browse_out_btn.configure(text="Change Output Directory...")

                self._log(f"Batch scan successful: {len(self.books)} books detected ({self.total_images_count} total pages).")

            else:
                # SINGLE BOOK MODE
                single_book = self.books[0]
                self.chapters = single_book.chapters
                self.total_images_count = single_book.total_images
                self.auto_root_cover = single_book.cover_path

                if not self.title_var.get() or self.title_var.get() == "Unknown":
                    self.title_var.set(single_book.title)

                default_out_file = self.source_dir.parent / f"{single_book.title}.epub"
                self.output_file = default_out_file
                self.output_path_var.set(str(default_out_file))

                stats_text = f"{len(self.chapters)} chapter(s) • {self.total_images_count} page(s)"
                self.card_source_stats.configure(text=stats_text)

                self.hero_status_title.configure(text="Ready to Convert")
                self.hero_status_sub.configure(text=f"{self.source_dir.name} ({stats_text})")
                self.status_icon_badge.configure(text="🛡️")

                self.banner_title.configure(text=f"Book Ready: {self.title_var.get() or self.source_dir.name}")
                self.banner_desc.configure(text=f"Analysis complete: {stats_text}. Click 'Convert to EPUB'.")
                self.main_convert_btn.configure(text="🚀 Convert to EPUB")

                # Cover card
                self.change_cover_btn.configure(state="normal")
                self.clear_cover_btn.configure(state="normal")
                if self.auto_root_cover:
                    self.cover_status_lbl.configure(text=f"Root Cover: {self.auto_root_cover.name}")
                    self._update_cover_thumbnail(self.auto_root_cover)
                else:
                    self.cover_status_lbl.configure(text="Automatic (1st page)")
                    first_page = self.chapters[0].pages[0].file_path if (self.chapters and self.chapters[0].pages) else None
                    self._update_cover_thumbnail(first_page)

                # Metadata card
                self.title_entry.configure(state="normal")

                # Destination card
                self.browse_out_btn.configure(text="Change File Destination...")

                self._log(f"Single book scan successful: {len(self.chapters)} chapters, {self.total_images_count} images.")

            self._update_chapters_view_list()

        except Exception as e:
            self.hero_status_title.configure(text="Error during analysis")
            self.hero_status_sub.configure(text=str(e))
            self.status_icon_badge.configure(text="❌")
            self._log(f"Analysis error: {e}")

    def _update_cover_thumbnail(self, image_path: Optional[Path]):
        if not image_path or not image_path.exists():
            self.thumb_label.configure(image=None, text="No\nPreview")
            return

        try:
            with Image.open(image_path) as img:
                img_rgb = img.convert("RGB")
                img_rgb.thumbnail((80, 110), Image.Resampling.LANCZOS)
                self.cover_thumbnail_image = ctk.CTkImage(
                    light_image=img_rgb,
                    dark_image=img_rgb,
                    size=img_rgb.size
                )
                self.thumb_label.configure(image=self.cover_thumbnail_image, text="")
        except Exception:
            self.thumb_label.configure(image=None, text="Image\nError")

    def _browse_custom_cover(self):
        filetypes = [
            ("Images", "*.jpg *.jpeg *.png *.webp *.gif *.bmp"),
            ("All Files", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="Choose Cover Image", filetypes=filetypes)
        if file_path:
            p = Path(file_path)
            self.custom_cover_file = p
            self.cover_path_var.set(str(p))
            self.cover_status_lbl.configure(text=f"Custom: {p.name}")
            self._update_cover_thumbnail(p)
            self._log(f"Custom cover selected: {p.name}")

    def _clear_custom_cover(self):
        self.custom_cover_file = None
        self.cover_path_var.set("")
        if self.auto_root_cover and self.auto_root_cover.exists():
            self.cover_status_lbl.configure(text=f"Root Cover: {self.auto_root_cover.name}")
            self._update_cover_thumbnail(self.auto_root_cover)
        elif self.chapters and self.chapters[0].pages:
            self.cover_status_lbl.configure(text="Automatic (1st page)")
            self._update_cover_thumbnail(self.chapters[0].pages[0].file_path)
        else:
            self.cover_status_lbl.configure(text="No image")
            self._update_cover_thumbnail(None)
        self._log("Custom cover reset to automatic.")

    def _browse_output_file(self):
        initial_dir = self.source_dir.parent if self.source_dir else None

        if self.is_batch_mode:
            folder = filedialog.askdirectory(title="Choose EPUB Output Directory", initialdir=initial_dir)
            if folder:
                self.output_file = Path(folder)
                self.output_path_var.set(str(self.output_file))
        else:
            initial_file = f"{self.title_var.get() or 'book'}.epub"
            file_path = filedialog.asksaveasfilename(
                title="Save EPUB As...",
                initialdir=initial_dir,
                initialfile=initial_file,
                defaultextension=".epub",
                filetypes=[("EPUB eBook", "*.epub"), ("All Files", "*.*")]
            )
            if file_path:
                self.output_file = Path(file_path)
                self.output_path_var.set(str(self.output_file))

    def _log(self, msg: str):
        self.card_log_preview.configure(text=f"Latest action:\n{msg}")
        self.full_log_textbox.configure(state="normal")
        self.full_log_textbox.insert("end", f"{msg}\n")
        self.full_log_textbox.see("end")
        self.full_log_textbox.configure(state="disabled")

    def _clear_logs(self):
        self.full_log_textbox.configure(state="normal")
        self.full_log_textbox.delete("1.0", "end")
        self.full_log_textbox.configure(state="disabled")

    def _start_conversion(self):
        if self.is_converting:
            return

        if not self.source_dir or not self.source_dir.exists():
            messagebox.showwarning("Missing Folder", "Please select a valid source folder.")
            return

        out_str = self.output_path_var.get().strip()
        if not out_str:
            messagebox.showwarning("Missing Destination", "Please specify a valid destination path.")
            return

        author = self.author_var.get().strip() or "Unknown"
        lang = self.lang_var.get().strip() or "en"
        is_manga = self.manga_mode_var.get()
        is_rtl = self.rtl_mode_var.get()

        self.is_converting = True
        self.main_convert_btn.configure(state="disabled", text="⏳ Converting...")
        self.progress_bar.set(0.0)
        self.progress_label.configure(text="0%")
        self.open_file_btn.pack_forget()
        self.open_folder_btn.pack_forget()

        if self.is_batch_mode:
            out_dir = Path(out_str)
            self.output_file = out_dir

            self.hero_status_title.configure(text="Batch conversion in progress...")
            self.hero_status_sub.configure(text=f"Generating {len(self.books)} EPUB books...")
            self.status_icon_badge.configure(text="⚙️")
            self.banner_title.configure(text=f"Processing {len(self.books)} books...")

            self._log("\n" + "=" * 50)
            self._log(f"Starting BATCH conversion ({len(self.books)} books)")
            self._log(f"Output directory: {out_dir}")

            thread = threading.Thread(
                target=self._worker_batch_conversion,
                args=(self.books, out_dir, author, lang, is_manga, is_rtl),
                daemon=True
            )
            thread.start()

        else:
            self.output_file = Path(out_str)
            if not self.output_file.name.lower().endswith(".epub"):
                self.output_file = self.output_file.with_suffix(".epub")
                self.output_path_var.set(str(self.output_file))

            title = self.title_var.get().strip() or self.source_dir.name
            cover_to_use = self.custom_cover_file if (self.custom_cover_file and self.custom_cover_file.exists()) else self.auto_root_cover

            self.hero_status_title.configure(text="Conversion in progress...")
            self.hero_status_sub.configure(text=f"Generating '{title}'...")
            self.status_icon_badge.configure(text="⚙️")

            self._log("\n" + "=" * 50)
            self._log(f"Starting conversion: '{title}' ({self.total_images_count} pages)")
            self._log(f"Output file: {self.output_file}")

            thread = threading.Thread(
                target=self._worker_single_conversion,
                args=(self.chapters, self.output_file, title, author, lang, cover_to_use, self.source_dir, is_manga, is_rtl),
                daemon=True
            )
            thread.start()

    def _worker_single_conversion(self, chapters, output_file, title, author, lang, custom_cover, source_dir, is_manga, is_rtl):
        def on_progress(current: int, total: int, chapter_title: str):
            ratio = current / total if total > 0 else 0.0
            percent = int(ratio * 100)
            self.after(0, self._update_progress, ratio, percent, f"{chapter_title} (Page {current}/{total})")

        try:
            res_path = create_epub(
                chapters=chapters,
                output_file=output_file,
                title=title,
                author=author,
                language=lang,
                custom_cover_path=custom_cover,
                source_dir=source_dir,
                is_manga=is_manga,
                is_rtl=is_rtl,
                progress_callback=on_progress
            )
            self.after(0, self._on_single_success, res_path)
        except Exception as e:
            self.after(0, self._on_conversion_error, str(e))

    def _worker_batch_conversion(self, books: List[BookData], output_dir: Path, author: str, lang: str, is_manga: bool, is_rtl: bool):
        total_books = len(books)

        def on_batch_progress(b_idx: int, tot_b: int, book: BookData, curr_p: int, tot_p: int):
            book_ratio = (curr_p / tot_p) if tot_p > 0 else 0.0
            overall_ratio = ((b_idx - 1) + book_ratio) / tot_b
            percent = int(overall_ratio * 100)
            msg = f"Book {b_idx}/{tot_b}: {book.title} (Page {curr_p}/{tot_p})"
            self.after(0, self._update_progress, overall_ratio, percent, msg)

        try:
            generated_files = create_epub_batch(
                books=books,
                output_dir=output_dir,
                author=author,
                language=lang,
                is_manga=is_manga,
                is_rtl=is_rtl,
                progress_callback=on_batch_progress
            )
            self.after(0, self._on_batch_success, generated_files, output_dir)
        except Exception as e:
            self.after(0, self._on_conversion_error, str(e))

    def _update_progress(self, ratio: float, percent: int, desc: str):
        self.progress_bar.set(ratio)
        self.progress_label.configure(text=f"{percent}%")
        self.banner_desc.configure(text=f"Processing: {desc}")

    def _on_single_success(self, output_path: Path):
        self.is_converting = False
        self.main_convert_btn.configure(state="normal", text="🚀 Convert to EPUB")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="100%")

        size_mb = output_path.stat().st_size / (1024 * 1024)
        self.hero_status_title.configure(text="EPUB Book Generated Successfully!")
        self.hero_status_sub.configure(text=f"Created file: {output_path.name} ({size_mb:.2f} MB)")
        self.status_icon_badge.configure(text="✅")

        self.banner_title.configure(text="Conversion Completed Successfully")
        self.banner_desc.configure(text=f"Your book is ready: {output_path.name} ({size_mb:.2f} MB)")

        self.open_file_btn.pack(side="right", padx=(4, 0))
        self.open_folder_btn.pack(side="right", padx=(4, 0))

        self._log(f"✔ Success! EPUB created: {output_path} ({size_mb:.2f} MB)")
        self._log("=" * 50)

        messagebox.showinfo(
            "Conversion Successful",
            f"Congratulations! Your digital book was generated successfully.\n\nFile: {output_path.name}\nSize: {size_mb:.2f} MB"
        )

    def _on_batch_success(self, generated_files: List[Path], output_dir: Path):
        self.is_converting = False
        self.main_convert_btn.configure(state="normal", text=f"🚀 Convert {len(self.books)} Books")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="100%")

        self.hero_status_title.configure(text="Collection Generated Successfully!")
        self.hero_status_sub.configure(text=f"{len(generated_files)} EPUB files created in: {output_dir.name}")
        self.status_icon_badge.configure(text="✅")

        self.banner_title.configure(text=f"Success: {len(generated_files)} Books Converted")
        self.banner_desc.configure(text=f"All files have been saved to: {output_dir}")

        self.open_folder_btn.pack(side="right", padx=(4, 0))

        self._log(f"✔ Batch Success! {len(generated_files)} EPUB books generated in: {output_dir}")
        for gf in generated_files:
            size_mb = gf.stat().st_size / (1024 * 1024)
            self._log(f"  • {gf.name} ({size_mb:.2f} MB)")
        self._log("=" * 50)

        messagebox.showinfo(
            "Collection Converted Successfully",
            f"Congratulations! All {len(generated_files)} books were converted successfully.\n\nDirectory: {output_dir}"
        )

    def _on_conversion_error(self, error_message: str):
        self.is_converting = False
        btn_text = f"🚀 Convert {len(self.books)} Books" if self.is_batch_mode else "🚀 Convert to EPUB"
        self.main_convert_btn.configure(state="normal", text=btn_text)

        self.hero_status_title.configure(text="Conversion Error")
        self.hero_status_sub.configure(text=error_message)
        self.status_icon_badge.configure(text="❌")

        self.banner_title.configure(text="Conversion Failed")
        self.banner_desc.configure(text=f"An error occurred: {error_message}")

        self._log(f"❌ ERROR: {error_message}")
        messagebox.showerror("Conversion Error", f"Conversion failed:\n\n{error_message}")

    def _open_output_folder(self):
        if self.output_file:
            folder = self.output_file if self.output_file.is_dir() else self.output_file.parent
            if folder.exists():
                if sys.platform == "win32":
                    os.startfile(folder)
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.Popen(["open", folder])
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", folder])

    def _open_output_file(self):
        if self.output_file and self.output_file.exists() and self.output_file.is_file():
            if sys.platform == "win32":
                os.startfile(self.output_file)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", self.output_file])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", self.output_file])


def main():
    app = FolderToEpubApp()
    app.mainloop()


if __name__ == "__main__":
    main()
