#!/usr/bin/env python3
"""
Folder to EPUB Converter - Interface Graphique Moderne
=====================================================
Interface utilisateur moderne, responsive et intuitive inspirée du design
tableau de bord (style Bitdefender) avec prise en charge complète du :
- Mode Livre Unique (mono ou multi-chapitres)
- Mode Multi-Livres (Batch / Traitement par lot)
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
    sys.exit("Erreur : La bibliothèque 'customtkinter' est requise. Installez-la avec 'pip install customtkinter'.")

try:
    from PIL import Image, ImageTk
except ImportError:
    sys.exit("Erreur : La bibliothèque 'Pillow' est requise. Installez-la avec 'pip install Pillow'.")

# Importer la logique de conversion depuis folder_to_epub.py
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
    """Application principale avec mise en page Dashboard / Sidebar moderne."""

    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre principale
        self.title("Folder to EPUB Converter")
        self.geometry("1080x760")
        self.minsize(940, 640)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Variables d'état
        self.source_dir: Optional[Path] = None
        self.output_file: Optional[Path] = None
        self.custom_cover_file: Optional[Path] = None
        self.auto_root_cover: Optional[Path] = None
        
        # Données de livres et chapitres
        self.is_batch_mode: bool = False
        self.books: List[BookData] = []
        self.chapters: List[ChapterData] = []
        self.total_images_count: int = 0
        
        self.is_converting: bool = False
        self.cover_thumbnail_image: Optional[ctk.CTkImage] = None

        # Variables de contrôle Tk
        self.title_var = ctk.StringVar(value="")
        self.author_var = ctk.StringVar(value="Inconnu")
        self.lang_var = ctk.StringVar(value="fr")
        self.manga_mode_var = ctk.BooleanVar(value=False)
        self.rtl_mode_var = ctk.BooleanVar(value=False)
        self.batch_switch_var = ctk.BooleanVar(value=False)
        self.source_path_var = ctk.StringVar(value="")
        self.output_path_var = ctk.StringVar(value="")
        self.cover_path_var = ctk.StringVar(value="")

        # Palette de couleurs adaptées
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

        # Construction de l'interface principale
        self._build_main_layout()

        # Afficher la vue principale par défaut
        self._show_view("dashboard")

    def _build_main_layout(self):
        """Met en place la structure globale avec barre latérale et zone de contenu."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Barre latérale gauche (Sidebar)
        self._build_sidebar()

        # 2. Zone de contenu principale (Conteneur dynamique)
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray94", "#121418"))
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Création des différentes vues
        self.views = {}
        self._build_dashboard_view()
        self._build_chapters_view()
        self._build_logs_view()
        self._build_settings_view()

    def _build_sidebar(self):
        """Construit la barre latérale avec logo, navigation et sélecteur de thème."""
        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=210,
            corner_radius=0,
            fg_color=(self.colors["sidebar_light"], self.colors["sidebar_dark"])
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        # Logo / Titre de l'application
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
            text="Convertisseur Pro",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60")
        )
        brand_sub.pack(anchor="w")

        # Séparateur subtil
        sep = ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=("gray80", "gray25"))
        sep.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 15))

        # Boutons de navigation
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "⚡ Tableau de bord"),
            ("chapters", "📚 Livres & Chapitres"),
            ("logs", "📋 Journal d'activité"),
            ("settings", "⚙️ Paramètres")
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

        # Bas de la barre latérale : thème et informations
        bottom_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        bottom_frame.grid(row=6, column=0, padx=14, pady=16, sticky="ew")

        theme_lbl = ctk.CTkLabel(bottom_frame, text="Thème :", font=ctk.CTkFont(size=11), text_color="gray")
        theme_lbl.pack(anchor="w", pady=(0, 4))

        self.theme_menu = ctk.CTkSegmentedButton(
            bottom_frame,
            values=["Système", "Sombre", "Clair"],
            command=self._change_theme
        )
        self.theme_menu.set("Système")
        self.theme_menu.pack(fill="x")

    def _show_view(self, view_name: str):
        """Bascule l'affichage vers l'onglet sélectionné."""
        for v_id, view_frame in self.views.items():
            view_frame.grid_forget()

        if view_name in self.views:
            self.views[view_name].grid(row=0, column=0, sticky="nsew")

        # Mise à jour visuelle des boutons de la sidebar
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
    # VUE 1 : TABLEAU DE BORD (DASHBOARD)
    # -------------------------------------------------------------
    def _build_dashboard_view(self):
        """Vue principale avec en-tête Hero, bannière d'action et cartes modulaires."""
        dash_scroll = ctk.CTkScrollableFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.views["dashboard"] = dash_scroll

        # 1. En-tête HERO (Statut visuel avec grande typographie)
        hero_frame = ctk.CTkFrame(dash_scroll, fg_color="transparent")
        hero_frame.pack(fill="x", padx=28, pady=(24, 12))

        # Badge d'icône d'état dynamique à gauche
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
            text="Prêt à convertir",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        self.hero_status_title.pack(anchor="w")

        self.hero_status_sub = ctk.CTkLabel(
            hero_text_box,
            text="Sélectionnez un dossier contenant vos images ou livres pour commencer.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.hero_status_sub.pack(anchor="w", pady=(2, 0))

        # 2. BANNIÈRE D'ACTION PRINCIPALE
        self._build_action_banner(dash_scroll)

        # 3. GRILLE DE CARTES INTERACTIVES
        self._build_cards_grid(dash_scroll)

    def _build_action_banner(self, parent):
        """Bannière supérieure mettant en avant la conversion, le mode et la progression."""
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

        # Informations textuelles
        banner_info = ctk.CTkFrame(top_row, fg_color="transparent")
        banner_info.pack(side="left", fill="x", expand=True)

        info_header = ctk.CTkFrame(banner_info, fg_color="transparent")
        info_header.pack(anchor="w")

        banner_icon = ctk.CTkLabel(info_header, text="⚡", font=ctk.CTkFont(size=16))
        banner_icon.pack(side="left", padx=(0, 6))

        self.banner_title = ctk.CTkLabel(
            info_header,
            text="Statut du Projet",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.banner_title.pack(side="left")

        self.banner_desc = ctk.CTkLabel(
            banner_info,
            text="Aucun dossier analysé pour le moment. Cliquez sur 'Parcourir' pour charger votre livre ou collection.",
            font=ctk.CTkFont(size=12),
            text_color=("gray30", "gray65"),
            justify="left",
            anchor="w"
        )
        self.banner_desc.pack(anchor="w", pady=(4, 0))

        # Boutons d'action et bascule Batch à droite
        btn_box = ctk.CTkFrame(top_row, fg_color="transparent")
        btn_box.pack(side="right", padx=(10, 0))

        self.batch_switch = ctk.CTkSwitch(
            btn_box,
            text="Mode Multi-Livres (Batch)",
            variable=self.batch_switch_var,
            command=self._on_batch_toggle,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.batch_switch.pack(side="left", padx=(0, 16))

        self.main_convert_btn = ctk.CTkButton(
            btn_box,
            text="🚀 Convertir en EPUB",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            corner_radius=8,
            fg_color=self.colors["accent_blue"],
            hover_color=self.colors["accent_blue_hover"],
            command=self._start_conversion
        )
        self.main_convert_btn.pack(side="right")

        # Barre de progression intégrée dans la bannière
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
        """Grille de cartes au design moderne et modulaire."""
        grid_container = ctk.CTkFrame(parent, fg_color="transparent")
        grid_container.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        grid_container.grid_columnconfigure(0, weight=1)
        grid_container.grid_columnconfigure(1, weight=1)

        # ---- CARTE 1 : DOSSIER SOURCE ----
        c1 = self._create_card(grid_container, "📁 Dossier Source des Images / Livres", row=0, col=0)
        
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
            text="Parcourir le dossier...",
            height=32,
            corner_radius=6,
            command=self._browse_source_directory
        )
        browse_src_btn.pack(side="left")

        self.card_source_stats = ctk.CTkLabel(
            c1_btn_row,
            text="0 chapitre • 0 image",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray30", "gray70")
        )
        self.card_source_stats.pack(side="right")

        # ---- CARTE 2 : COUVERTURE & APERÇU ----
        c2 = self._create_card(grid_container, "🖼️ Couverture & Miniature", row=0, col=1)

        c2_content = ctk.CTkFrame(c2, fg_color="transparent")
        c2_content.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        self.thumb_label = ctk.CTkLabel(
            c2_content,
            text="Aucun\nAperçu",
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
            text="Couverture : Automatique (1ère page)",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        self.cover_status_lbl.pack(anchor="w", pady=(0, 8))

        c2_btns = ctk.CTkFrame(c2_actions, fg_color="transparent")
        c2_btns.pack(anchor="w")

        self.change_cover_btn = ctk.CTkButton(
            c2_btns,
            text="Choisir...",
            width=90,
            height=30,
            corner_radius=6,
            command=self._browse_custom_cover
        )
        self.change_cover_btn.pack(side="left", padx=(0, 8))

        self.clear_cover_btn = ctk.CTkButton(
            c2_btns,
            text="Réinitialiser",
            width=95,
            height=30,
            corner_radius=6,
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            text_color=("gray10", "gray90"),
            command=self._clear_custom_cover
        )
        self.clear_cover_btn.pack(side="left")

        # ---- CARTE 3 : MÉTADONNÉES ----
        c3 = self._create_card(grid_container, "📝 Métadonnées & Auteur", row=1, col=0)

        c3_form = ctk.CTkFrame(c3, fg_color="transparent")
        c3_form.pack(fill="x", padx=16, pady=(4, 14))

        ctk.CTkLabel(c3_form, text="Titre :", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", pady=4)
        self.title_entry = ctk.CTkEntry(c3_form, textvariable=self.title_var, height=30, placeholder_text="Titre du livre")
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        ctk.CTkLabel(c3_form, text="Auteur :", font=ctk.CTkFont(size=12)).grid(row=1, column=0, sticky="w", pady=4)
        self.author_entry = ctk.CTkEntry(c3_form, textvariable=self.author_var, height=30, placeholder_text="Auteur")
        self.author_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)

        ctk.CTkLabel(c3_form, text="Langue :", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", pady=4)
        self.lang_menu = ctk.CTkOptionMenu(
            c3_form,
            variable=self.lang_var,
            values=["fr", "en", "ja", "es", "de", "it", "ko", "zh"],
            height=30,
            width=100
        )
        self.lang_menu.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=4)
        c3_form.grid_columnconfigure(1, weight=1)

        # ---- CARTE 4 : FORMATAGE & OPTIONS MANGA ----
        c4 = self._create_card(grid_container, "⚙️ Formatage & Lecture", row=1, col=1)

        c4_content = ctk.CTkFrame(c4, fg_color="transparent")
        c4_content.pack(fill="x", padx=16, pady=(6, 14))

        self.manga_switch = ctk.CTkSwitch(
            c4_content,
            text="Mode Manga / BD (Fixed-Layout EPUB 3)",
            variable=self.manga_mode_var,
            command=self._on_manga_toggle,
            font=ctk.CTkFont(size=12)
        )
        self.manga_switch.pack(anchor="w", pady=(0, 10))

        self.rtl_switch = ctk.CTkSwitch(
            c4_content,
            text="Sens Droite à Gauche (RTL Japonais)",
            variable=self.rtl_mode_var,
            font=ctk.CTkFont(size=12)
        )
        self.rtl_switch.pack(anchor="w", pady=(0, 8))

        badge_info = ctk.CTkLabel(
            c4_content,
            text="ℹ️ S'applique à tous les livres convertis.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        badge_info.pack(anchor="w")

        # ---- CARTE 5 : DESTINATION EPUB ----
        c5 = self._create_card(grid_container, "📦 Destination & Sortie", row=2, col=0)

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
            text="Changer l'emplacement...",
            height=32,
            corner_radius=6,
            command=self._browse_output_file
        )
        self.browse_out_btn.pack(side="left")

        self.open_file_btn = ctk.CTkButton(
            c5_btn_row,
            text="📖 Ouvrir",
            width=75,
            height=32,
            corner_radius=6,
            fg_color=self.colors["success_green"],
            hover_color="#0b8043",
            command=self._open_output_file
        )
        self.open_folder_btn = ctk.CTkButton(
            c5_btn_row,
            text="📂 Dossier",
            width=80,
            height=32,
            corner_radius=6,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self._open_output_folder
        )

        # ---- CARTE 6 : STATISTIQUES & LIENS RAPIDES ----
        c6 = self._create_card(grid_container, "📊 Résumé & Activité", row=2, col=1)

        c6_content = ctk.CTkFrame(c6, fg_color="transparent")
        c6_content.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        self.card_log_preview = ctk.CTkLabel(
            c6_content,
            text="Journal : Système prêt.\nAucune conversion active.",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=("gray30", "gray70"),
            justify="left",
            anchor="w"
        )
        self.card_log_preview.pack(fill="x", pady=(0, 8))

        see_logs_btn = ctk.CTkButton(
            c6_content,
            text="Consulter le journal complet ➜",
            height=30,
            corner_radius=6,
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=self.colors["accent_blue"],
            command=lambda: self._show_view("logs")
        )
        see_logs_btn.pack(anchor="w")

    def _create_card(self, parent, title: str, row: int, col: int) -> ctk.CTkFrame:
        """Crée une carte visuelle modulaire."""
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
    # VUE 2 : EXPLORATEUR DE LIVRES & CHAPITRES
    # -------------------------------------------------------------
    def _build_chapters_view(self):
        """Vue détaillée affichant les livres ou chapitres détectés."""
        chapters_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.views["chapters"] = chapters_frame

        header = ctk.CTkFrame(chapters_frame, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 12))

        self.chapters_view_title = ctk.CTkLabel(
            header,
            text="📚 Livres & Chapitres",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.chapters_view_title.pack(anchor="w")

        self.chapters_view_sub = ctk.CTkLabel(
            header,
            text="Aperçu des éléments prêts à être convertis en EPUB.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60")
        )
        self.chapters_view_sub.pack(anchor="w", pady=(2, 0))

        self.chapters_scroll = ctk.CTkScrollableFrame(chapters_frame, corner_radius=12)
        self.chapters_scroll.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        self.empty_chapters_lbl = ctk.CTkLabel(
            self.chapters_scroll,
            text="Aucun dossier sélectionné.\nChargez un dossier depuis le Tableau de Bord.",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.empty_chapters_lbl.pack(pady=50)

    def _update_chapters_view_list(self):
        """Met à jour dynamiquement la liste affichée selon le mode (Livre unique ou Batch)."""
        for widget in self.chapters_scroll.winfo_children():
            widget.destroy()

        if self.is_batch_mode and self.books:
            self.chapters_view_title.configure(text=f"📚 Collection : {len(self.books)} Livres Détectés")
            self.chapters_view_sub.configure(text="Chaque livre ci-dessous sera généré sous forme d'un fichier .epub distinct.")

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

                # Thumbnail de couverture si disponible
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
                    text=f"Dossier : {book.folder_path.name} • Couverture : {book.cover_path.name if book.cover_path else '1ère page'}",
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                    anchor="w"
                )
                c_sub.pack(anchor="w")

                # Badges chapitres et pages
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
            self.chapters_view_title.configure(text=f"📖 Chapitres du Livre ({len(self.chapters)} chapitres)")
            self.chapters_view_sub.configure(text="Liste séquentielle des chapitres qui composent ce livre numérique.")

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

                first_img = chap.pages[0].file_path.name if chap.pages else "Aucune image"
                c_sub = ctk.CTkLabel(
                    title_info,
                    text=f"Première page : {first_img}",
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
                text="Aucun contenu trouvé dans ce dossier.",
                font=ctk.CTkFont(size=13),
                text_color="gray"
            )
            self.empty_chapters_lbl.pack(pady=50)

    # -------------------------------------------------------------
    # VUE 3 : JOURNAL & LOGS
    # -------------------------------------------------------------
    def _build_logs_view(self):
        """Vue dédiée pour la console de logs en grand format."""
        logs_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.views["logs"] = logs_frame

        header = ctk.CTkFrame(logs_frame, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 12))

        ctk.CTkLabel(header, text="📋 Journal d'Activité Détaillé", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        clear_btn = ctk.CTkButton(
            header,
            text="Effacer le journal",
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
    # VUE 4 : PARAMÈTRES
    # -------------------------------------------------------------
    def _build_settings_view(self):
        """Vue des paramètres et préférences."""
        settings_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.views["settings"] = settings_frame

        header = ctk.CTkFrame(settings_frame, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 16))

        ctk.CTkLabel(header, text="⚙️ Paramètres & Informations", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")

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

        ctk.CTkLabel(info_card, text="ℹ️ À Propos d'EPUB Forge", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(14, 4))
        desc = (
            "Folder to EPUB Converter (EPUB Forge)\n"
            "Version 2.5 • Traitement par lot (Batch Multi-Livres) & Livre Unique.\n\n"
            "• Tri naturel alphanumérique strict (natsort)\n"
            "• Détection intelligente des collections de livres et de leurs couvertures\n"
            "• Support Fixed-Layout EPUB 3 et orientation Manga Droite à Gauche (RTL)\n"
            "• Architecture multi-threadée non-bloquante avec suivi de progression temps réel."
        )
        ctk.CTkLabel(info_card, text=desc, justify="left", font=ctk.CTkFont(size=12), text_color=("gray30", "gray70")).pack(anchor="w", padx=16, pady=(0, 14))

    # -------------------------------------------------------------
    # LOGIQUE DE CONVERSION ET CALLBACKS
    # -------------------------------------------------------------

    def _change_theme(self, choice: str):
        mapping = {"Système": "System", "Sombre": "Dark", "Clair": "Light"}
        ctk.set_appearance_mode(mapping.get(choice, "System"))

    def _on_manga_toggle(self):
        if self.manga_mode_var.get():
            self.rtl_mode_var.set(True)

    def _on_batch_toggle(self):
        """Réaction quand l'utilisateur bascule manuellement le switch Batch."""
        if self.source_dir and self.source_dir.exists():
            self._analyze_source_directory(force_batch=self.batch_switch_var.get())

    def _browse_source_directory(self):
        """Sélectionne un dossier source et lance l'analyse."""
        folder = filedialog.askdirectory(title="Sélectionner le dossier source des images ou de la collection")
        if not folder:
            return

        source_path = Path(folder)
        self.source_dir = source_path
        self.source_path_var.set(str(source_path))

        self._analyze_source_directory(force_batch=None)

    def _analyze_source_directory(self, force_batch: Optional[bool] = None):
        """Analyse le dossier et configure l'UI pour Livre Unique ou Batch."""
        if not self.source_dir or not self.source_dir.exists():
            return

        self._log(f"Analyse du dossier : {self.source_dir} (force_batch={force_batch})...")
        try:
            is_batch, detected_books = detect_books(self.source_dir, force_batch=force_batch)

            if not detected_books:
                self.hero_status_title.configure(text="⚠️ Aucune image trouvée")
                self.hero_status_sub.configure(text="Le dossier sélectionné ne contient aucune image valide (JPG, PNG, WEBP, GIF).")
                self.status_icon_badge.configure(text="⚠️")
                self.card_source_stats.configure(text="0 image")
                self._update_cover_thumbnail(None)
                self._log("Attention : aucune image valide trouvée dans ce dossier.")
                return

            self.books = detected_books
            self.is_batch_mode = is_batch and len(detected_books) > 1
            self.batch_switch_var.set(self.is_batch_mode)

            if self.is_batch_mode:
                # --- MODE BATCH MULTI-LIVRES ---
                self.total_images_count = sum(b.total_images for b in self.books)
                default_out_dir = self.source_dir.parent / f"{self.source_dir.name}_epubs"
                self.output_file = default_out_dir
                self.output_path_var.set(str(default_out_dir))

                stats_text = f"{len(self.books)} livres • {self.total_images_count} pages au total"
                self.card_source_stats.configure(text=stats_text)

                self.hero_status_title.configure(text=f"Collection Prête ({len(self.books)} Livres)")
                self.hero_status_sub.configure(text=f"{self.source_dir.name} ({stats_text})")
                self.status_icon_badge.configure(text="📚")

                self.banner_title.configure(text=f"Mode Multi-Livres : {len(self.books)} EPUBs à créer")
                self.banner_desc.configure(text=f"Chaque sous-dossier sera compilé en fichier .epub indépendant dans le dossier de destination.")
                self.main_convert_btn.configure(text=f"🚀 Convertir les {len(self.books)} livres")

                # Carte Couverture
                first_cover = self.books[0].cover_path if self.books else None
                self._update_cover_thumbnail(first_cover)
                self.cover_status_lbl.configure(text=f"Couvertures individuelles ({len(self.books)} livres)")
                self.change_cover_btn.configure(state="disabled")
                self.clear_cover_btn.configure(state="disabled")

                # Carte Métadonnées
                self.title_entry.configure(state="disabled", placeholder_text="[Noms des sous-dossiers]")
                self.title_var.set("")

                # Carte Destination
                self.browse_out_btn.configure(text="Changer le dossier de sortie...")

                self._log(f"Scan Batch réussi : {len(self.books)} livres détectés ({self.total_images_count} pages au total).")

            else:
                # --- MODE LIVRE UNIQUE ---
                single_book = self.books[0]
                self.chapters = single_book.chapters
                self.total_images_count = single_book.total_images
                self.auto_root_cover = single_book.cover_path

                if not self.title_var.get() or self.title_var.get() == "Inconnu":
                    self.title_var.set(single_book.title)

                default_out_file = self.source_dir.parent / f"{single_book.title}.epub"
                self.output_file = default_out_file
                self.output_path_var.set(str(default_out_file))

                stats_text = f"{len(self.chapters)} chapitre(s) • {self.total_images_count} page(s)"
                self.card_source_stats.configure(text=stats_text)

                self.hero_status_title.configure(text="Prêt à convertir")
                self.hero_status_sub.configure(text=f"{self.source_dir.name} ({stats_text})")
                self.status_icon_badge.configure(text="🛡️")

                self.banner_title.configure(text=f"Livre prêt : {self.title_var.get() or self.source_dir.name}")
                self.banner_desc.configure(text=f"Analyse terminée avec succès : {stats_text}. Cliquez sur 'Convertir en EPUB'.")
                self.main_convert_btn.configure(text="🚀 Convertir en EPUB")

                # Carte Couverture
                self.change_cover_btn.configure(state="normal")
                self.clear_cover_btn.configure(state="normal")
                if self.auto_root_cover:
                    self.cover_status_lbl.configure(text=f"Racine : {self.auto_root_cover.name}")
                    self._update_cover_thumbnail(self.auto_root_cover)
                else:
                    self.cover_status_lbl.configure(text="Automatique (1ère page)")
                    first_page = self.chapters[0].pages[0].file_path if (self.chapters and self.chapters[0].pages) else None
                    self._update_cover_thumbnail(first_page)

                # Carte Métadonnées
                self.title_entry.configure(state="normal")

                # Carte Destination
                self.browse_out_btn.configure(text="Changer le fichier de sortie...")

                self._log(f"Scan Livre Unique réussi : {len(self.chapters)} chapitres, {self.total_images_count} images.")

            self._update_chapters_view_list()

        except Exception as e:
            self.hero_status_title.configure(text="Erreur lors de l'analyse")
            self.hero_status_sub.configure(text=str(e))
            self.status_icon_badge.configure(text="❌")
            self._log(f"Erreur d'analyse : {e}")

    def _update_cover_thumbnail(self, image_path: Optional[Path]):
        """Met à jour la miniature affichée dans la carte Couverture."""
        if not image_path or not image_path.exists():
            self.thumb_label.configure(image=None, text="Aucun\nAperçu")
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
            self.thumb_label.configure(image=None, text="Erreur\nImage")

    def _browse_custom_cover(self):
        """Choisit une image de couverture personnalisée en mode livre unique."""
        filetypes = [
            ("Images", "*.jpg *.jpeg *.png *.webp *.gif *.bmp"),
            ("Tous les fichiers", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="Choisir une image de couverture", filetypes=filetypes)
        if file_path:
            p = Path(file_path)
            self.custom_cover_file = p
            self.cover_path_var.set(str(p))
            self.cover_status_lbl.configure(text=f"Personnalisée : {p.name}")
            self._update_cover_thumbnail(p)
            self._log(f"Couverture manuelle sélectionnée : {p.name}")

    def _clear_custom_cover(self):
        """Réinitialise la couverture personnalisée."""
        self.custom_cover_file = None
        self.cover_path_var.set("")
        if self.auto_root_cover and self.auto_root_cover.exists():
            self.cover_status_lbl.configure(text=f"Racine : {self.auto_root_cover.name}")
            self._update_cover_thumbnail(self.auto_root_cover)
        elif self.chapters and self.chapters[0].pages:
            self.cover_status_lbl.configure(text="Automatique (1ère page)")
            self._update_cover_thumbnail(self.chapters[0].pages[0].file_path)
        else:
            self.cover_status_lbl.configure(text="Aucune image")
            self._update_cover_thumbnail(None)
        self._log("Couverture personnalisée réinitialisée.")

    def _browse_output_file(self):
        """Permet de changer l'emplacement d'enregistrement selon le mode."""
        initial_dir = self.source_dir.parent if self.source_dir else None

        if self.is_batch_mode:
            folder = filedialog.askdirectory(title="Choisir le dossier de réception des fichiers EPUB", initialdir=initial_dir)
            if folder:
                self.output_file = Path(folder)
                self.output_path_var.set(str(self.output_file))
        else:
            initial_file = f"{self.title_var.get() or 'livre'}.epub"
            file_path = filedialog.asksaveasfilename(
                title="Enregistrer sous...",
                initialdir=initial_dir,
                initialfile=initial_file,
                defaultextension=".epub",
                filetypes=[("Livre EPUB", "*.epub"), ("Tous les fichiers", "*.*")]
            )
            if file_path:
                self.output_file = Path(file_path)
                self.output_path_var.set(str(self.output_file))

    def _log(self, msg: str):
        """Ajoute un message de journal."""
        self.card_log_preview.configure(text=f"Dernière action :\n{msg}")
        self.full_log_textbox.configure(state="normal")
        self.full_log_textbox.insert("end", f"{msg}\n")
        self.full_log_textbox.see("end")
        self.full_log_textbox.configure(state="disabled")

    def _clear_logs(self):
        self.full_log_textbox.configure(state="normal")
        self.full_log_textbox.delete("1.0", "end")
        self.full_log_textbox.configure(state="disabled")

    def _start_conversion(self):
        """Valide et démarre la conversion (Livre unique ou Batch)."""
        if self.is_converting:
            return

        if not self.source_dir or not self.source_dir.exists():
            messagebox.showwarning("Dossier manquant", "Veuillez sélectionner un dossier source valide.")
            return

        out_str = self.output_path_var.get().strip()
        if not out_str:
            messagebox.showwarning("Destination manquante", "Veuillez indiquer un chemin de sortie valide.")
            return

        author = self.author_var.get().strip() or "Inconnu"
        lang = self.lang_var.get().strip() or "fr"
        is_manga = self.manga_mode_var.get()
        is_rtl = self.rtl_mode_var.get()

        self.is_converting = True
        self.main_convert_btn.configure(state="disabled", text="⏳ Conversion...")
        self.progress_bar.set(0.0)
        self.progress_label.configure(text="0%")
        self.open_file_btn.pack_forget()
        self.open_folder_btn.pack_forget()

        if self.is_batch_mode:
            # Conversion Batch
            out_dir = Path(out_str)
            self.output_file = out_dir

            self.hero_status_title.configure(text="Conversion par lot en cours...")
            self.hero_status_sub.configure(text=f"Génération de {len(self.books)} livres EPUB...")
            self.status_icon_badge.configure(text="⚙️")
            self.banner_title.configure(text=f"Traitement de {len(self.books)} livres...")

            self._log("\n" + "=" * 50)
            self._log(f"Démarrage de la conversion BATCH ({len(self.books)} livres)")
            self._log(f"Dossier de sortie : {out_dir}")

            thread = threading.Thread(
                target=self._worker_batch_conversion,
                args=(self.books, out_dir, author, lang, is_manga, is_rtl),
                daemon=True
            )
            thread.start()

        else:
            # Conversion Livre Unique
            self.output_file = Path(out_str)
            if not self.output_file.name.lower().endswith(".epub"):
                self.output_file = self.output_file.with_suffix(".epub")
                self.output_path_var.set(str(self.output_file))

            title = self.title_var.get().strip() or self.source_dir.name
            cover_to_use = self.custom_cover_file if (self.custom_cover_file and self.custom_cover_file.exists()) else self.auto_root_cover

            self.hero_status_title.configure(text="Conversion en cours...")
            self.hero_status_sub.configure(text=f"Génération de '{title}'...")
            self.status_icon_badge.configure(text="⚙️")

            self._log("\n" + "=" * 50)
            self._log(f"Démarrage de la conversion : '{title}' ({self.total_images_count} pages)")
            self._log(f"Fichier de sortie : {self.output_file}")

            thread = threading.Thread(
                target=self._worker_single_conversion,
                args=(self.chapters, self.output_file, title, author, lang, cover_to_use, self.source_dir, is_manga, is_rtl),
                daemon=True
            )
            thread.start()

    def _worker_single_conversion(self, chapters, output_file, title, author, lang, custom_cover, source_dir, is_manga, is_rtl):
        """Exécute la création d'un livre unique en tâche de fond."""
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
        """Exécute la création de plusieurs livres en tâche de fond."""
        total_books = len(books)

        def on_batch_progress(b_idx: int, tot_b: int, book: BookData, curr_p: int, tot_p: int):
            book_ratio = (curr_p / tot_p) if tot_p > 0 else 0.0
            overall_ratio = ((b_idx - 1) + book_ratio) / tot_b
            percent = int(overall_ratio * 100)
            msg = f"Livre {b_idx}/{tot_b} : {book.title} (Page {curr_p}/{tot_p})"
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
        self.banner_desc.configure(text=f"Traitement : {desc}")

    def _on_single_success(self, output_path: Path):
        self.is_converting = False
        self.main_convert_btn.configure(state="normal", text="🚀 Convertir en EPUB")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="100%")

        size_mb = output_path.stat().st_size / (1024 * 1024)
        self.hero_status_title.configure(text="Livre EPUB généré avec succès !")
        self.hero_status_sub.configure(text=f"Fichier créé : {output_path.name} ({size_mb:.2f} Mo)")
        self.status_icon_badge.configure(text="✅")

        self.banner_title.configure(text="Conversion terminée avec succès")
        self.banner_desc.configure(text=f"Votre livre est prêt : {output_path.name} ({size_mb:.2f} Mo)")

        self.open_file_btn.pack(side="right", padx=(4, 0))
        self.open_folder_btn.pack(side="right", padx=(4, 0))

        self._log(f"✔ Succès ! EPUB généré : {output_path} ({size_mb:.2f} Mo)")
        self._log("=" * 50)

        messagebox.showinfo(
            "Conversion Réussie",
            f"Le livre numérique a été généré avec succès !\n\nFichier : {output_path.name}\nTaille : {size_mb:.2f} Mo"
        )

    def _on_batch_success(self, generated_files: List[Path], output_dir: Path):
        self.is_converting = False
        self.main_convert_btn.configure(state="normal", text=f"🚀 Convertir les {len(self.books)} livres")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="100%")

        self.hero_status_title.configure(text=f"Collection générée avec succès !")
        self.hero_status_sub.configure(text=f"{len(generated_files)} fichiers EPUB créés dans : {output_dir.name}")
        self.status_icon_badge.configure(text="✅")

        self.banner_title.configure(text=f"Succès : {len(generated_files)} livres convertis")
        self.banner_desc.configure(text=f"Tous les fichiers ont été enregistrés dans : {output_dir}")

        self.open_folder_btn.pack(side="right", padx=(4, 0))

        self._log(f"✔ Succès Batch ! {len(generated_files)} livres EPUB générés dans : {output_dir}")
        for gf in generated_files:
            size_mb = gf.stat().st_size / (1024 * 1024)
            self._log(f"  • {gf.name} ({size_mb:.2f} Mo)")
        self._log("=" * 50)

        messagebox.showinfo(
            "Collection Convertie avec Succès",
            f"Félicitations ! Les {len(generated_files)} livres ont été convertis avec succès.\n\nDossier : {output_dir}"
        )

    def _on_conversion_error(self, error_message: str):
        self.is_converting = False
        btn_text = f"🚀 Convertir les {len(self.books)} livres" if self.is_batch_mode else "🚀 Convertir en EPUB"
        self.main_convert_btn.configure(state="normal", text=btn_text)

        self.hero_status_title.configure(text="Erreur lors de la conversion")
        self.hero_status_sub.configure(text=error_message)
        self.status_icon_badge.configure(text="❌")

        self.banner_title.configure(text="Échec de la conversion")
        self.banner_desc.configure(text=f"Une erreur est survenue : {error_message}")

        self._log(f"❌ ERREUR : {error_message}")
        messagebox.showerror("Erreur de conversion", f"Échec de la conversion :\n\n{error_message}")

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
