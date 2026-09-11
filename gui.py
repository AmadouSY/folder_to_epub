#!/usr/bin/env python3
"""
Folder to EPUB Converter - Interface Graphique (GUI)
===================================================
Interface graphique moderne et intuitive basée sur CustomTkinter
pour convertir des dossiers d'images ou de chapitres en livres EPUB.
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
    ChapterData,
    SUPPORTED_EXTENSIONS
)


class FolderToEpubApp(ctk.CTk):
    """Application principale CustomTkinter pour convertir des dossiers d'images en EPUB."""

    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre principale
        self.title("Folder to EPUB Converter")
        self.geometry("820x780")
        self.minsize(700, 600)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Variables d'état
        self.source_dir: Optional[Path] = None
        self.output_file: Optional[Path] = None
        self.custom_cover_file: Optional[Path] = None
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
        self.source_path_var = ctk.StringVar(value="")
        self.output_path_var = ctk.StringVar(value="")
        self.cover_path_var = ctk.StringVar(value="")

        # Construction de l'interface
        self._build_ui()

    def _build_ui(self):
        """Construit l'ensemble des éléments de l'interface utilisateur."""
        # Conteneur principal défilable pour s'adapter à toutes les résolutions
        self.scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # 1. En-tête (Header)
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="📚 Folder to EPUB Converter",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(side="left")

        # Sélecteur de thème (Dark / Light / System)
        self.theme_menu = ctk.CTkOptionMenu(
            header_frame,
            values=["Système", "Sombre", "Clair"],
            width=110,
            command=self._change_theme
        )
        self.theme_menu.pack(side="right")
        theme_label = ctk.CTkLabel(header_frame, text="Thème :", text_color="gray")
        theme_label.pack(side="right", padx=8)

        # 2. Section Dossier Source
        self._build_source_section()

        # 3. Section Métadonnées & Destination
        self._build_metadata_section()

        # 4. Section Options de Lecture (Manga / RTL)
        self._build_options_section()

        # 5. Section Progression & Action
        self._build_action_section()

    def _build_source_section(self):
        """Section de sélection et d'analyse du dossier source."""
        source_frame = ctk.CTkFrame(self.scroll_frame)
        source_frame.pack(fill="x", padx=20, pady=8)

        section_title = ctk.CTkLabel(
            source_frame,
            text="📁 Dossier Source des Images",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        section_title.pack(anchor="w", padx=15, pady=(12, 6))

        # Champ de sélection du dossier
        path_row = ctk.CTkFrame(source_frame, fg_color="transparent")
        path_row.pack(fill="x", padx=15, pady=(0, 10))

        self.source_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.source_path_var,
            placeholder_text="Sélectionnez un dossier contenant vos images ou chapitres..."
        )
        self.source_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            path_row,
            text="Parcourir...",
            width=110,
            command=self._browse_source_directory
        )
        browse_btn.pack(side="right")

        # Zone d'aperçu / scan du dossier
        self.scan_info_frame = ctk.CTkFrame(source_frame, fg_color=("gray90", "gray17"))
        self.scan_info_frame.pack(fill="x", padx=15, pady=(0, 12))

        # Miniature de la couverture
        self.thumb_label = ctk.CTkLabel(
            self.scan_info_frame,
            text="Aperçu\nCouverture",
            width=90,
            height=120,
            fg_color=("gray85", "gray22"),
            corner_radius=6
        )
        self.thumb_label.pack(side="left", padx=12, pady=10)

        # Texte descriptif de l'analyse
        self.scan_details_label = ctk.CTkLabel(
            self.scan_info_frame,
            text="Aucun dossier sélectionné.\nVeuillez choisir un dossier contenant des images ou sous-dossiers.",
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.scan_details_label.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    def _build_metadata_section(self):
        """Section pour configurer les métadonnées et la destination."""
        meta_frame = ctk.CTkFrame(self.scroll_frame)
        meta_frame.pack(fill="x", padx=20, pady=8)

        meta_title = ctk.CTkLabel(
            meta_frame,
            text="📝 Métadonnées & Fichier de Sortie",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        meta_title.pack(anchor="w", padx=15, pady=(12, 8))

        # Grille pour Titre, Auteur, Langue
        grid = ctk.CTkFrame(meta_frame, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=(0, 8))

        # Titre
        ctk.CTkLabel(grid, text="Titre du livre :", anchor="w").grid(row=0, column=0, sticky="w", pady=4)
        self.title_entry = ctk.CTkEntry(grid, textvariable=self.title_var, placeholder_text="Titre du livre")
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=(8, 15), pady=4)

        # Auteur
        ctk.CTkLabel(grid, text="Auteur :", anchor="w").grid(row=0, column=2, sticky="w", pady=4)
        self.author_entry = ctk.CTkEntry(grid, textvariable=self.author_var, placeholder_text="Auteur")
        self.author_entry.grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=4)

        grid.columnconfigure(1, weight=3)
        grid.columnconfigure(3, weight=2)

        # Deuxième ligne de grille : Langue & Couverture
        grid2 = ctk.CTkFrame(meta_frame, fg_color="transparent")
        grid2.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(grid2, text="Langue :", anchor="w").grid(row=0, column=0, sticky="w", pady=4)
        self.lang_menu = ctk.CTkOptionMenu(
            grid2,
            variable=self.lang_var,
            values=["fr", "en", "ja", "es", "de", "it", "ko", "zh"],
            width=100
        )
        self.lang_menu.grid(row=0, column=1, sticky="w", padx=(8, 20), pady=4)

        # Couverture personnalisée
        ctk.CTkLabel(grid2, text="Couverture perso (opt.) :", anchor="w").grid(row=0, column=2, sticky="w", pady=4)
        cover_box = ctk.CTkFrame(grid2, fg_color="transparent")
        cover_box.grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=4)

        self.cover_entry = ctk.CTkEntry(
            cover_box,
            textvariable=self.cover_path_var,
            placeholder_text="Image de couverture..."
        )
        self.cover_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        browse_cover_btn = ctk.CTkButton(
            cover_box,
            text="Parcourir",
            width=75,
            command=self._browse_custom_cover
        )
        browse_cover_btn.pack(side="left", padx=(0, 4))

        clear_cover_btn = ctk.CTkButton(
            cover_box,
            text="✕",
            width=32,
            fg_color="gray",
            hover_color="gray40",
            command=self._clear_custom_cover
        )
        clear_cover_btn.pack(side="left")

        grid2.columnconfigure(3, weight=1)

        # Fichier EPUB de sortie
        out_row = ctk.CTkFrame(meta_frame, fg_color="transparent")
        out_row.pack(fill="x", padx=15, pady=(4, 12))

        ctk.CTkLabel(out_row, text="Fichier de sortie :", anchor="w").pack(side="left", padx=(0, 8))
        self.output_entry = ctk.CTkEntry(
            out_row,
            textvariable=self.output_path_var,
            placeholder_text="Chemin vers le fichier .epub à générer"
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_out_btn = ctk.CTkButton(
            out_row,
            text="Enregistrer sous...",
            width=130,
            command=self._browse_output_file
        )
        browse_out_btn.pack(side="right")

    def _build_options_section(self):
        """Section des réglages de lecture (Manga / BD, Fixed-Layout, RTL)."""
        options_frame = ctk.CTkFrame(self.scroll_frame)
        options_frame.pack(fill="x", padx=20, pady=8)

        options_title = ctk.CTkLabel(
            options_frame,
            text="⚙️ Options de Lecture & Formatage",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        options_title.pack(anchor="w", padx=15, pady=(12, 8))

        switches_row = ctk.CTkFrame(options_frame, fg_color="transparent")
        switches_row.pack(fill="x", padx=15, pady=(0, 12))

        self.manga_switch = ctk.CTkSwitch(
            switches_row,
            text="Mode Manga / BD (Fixed-Layout & Plein écran liseuse)",
            variable=self.manga_mode_var,
            command=self._on_manga_toggle
        )
        self.manga_switch.pack(side="left", padx=(0, 30), pady=4)

        self.rtl_switch = ctk.CTkSwitch(
            switches_row,
            text="Sens de lecture Droite à Gauche (RTL)",
            variable=self.rtl_mode_var
        )
        self.rtl_switch.pack(side="left", pady=4)

    def _build_action_section(self):
        """Section pour lancer la conversion, voir la barre de progression et les logs."""
        action_frame = ctk.CTkFrame(self.scroll_frame)
        action_frame.pack(fill="x", padx=20, pady=(8, 20))

        # Bouton principal de conversion
        self.convert_btn = ctk.CTkButton(
            action_frame,
            text="🚀 Convertir en EPUB",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            command=self._start_conversion
        )
        self.convert_btn.pack(fill="x", padx=15, pady=(15, 10))

        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(action_frame)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 6))
        self.progress_bar.set(0.0)

        # Statut textuel
        status_row = ctk.CTkFrame(action_frame, fg_color="transparent")
        status_row.pack(fill="x", padx=15, pady=(0, 8))

        self.status_label = ctk.CTkLabel(
            status_row,
            text="Prêt à convertir.",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left")

        self.percent_label = ctk.CTkLabel(
            status_row,
            text="0%",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.percent_label.pack(side="right")

        # Console de logs intégrée
        self.log_textbox = ctk.CTkTextbox(
            action_frame,
            height=130,
            font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled"
        )
        self.log_textbox.pack(fill="x", padx=15, pady=(0, 10))

        # Boutons d'actions après succès (masqués initialement)
        self.post_actions_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        self.post_actions_frame.pack(fill="x", padx=15, pady=(0, 12))

        self.open_folder_btn = ctk.CTkButton(
            self.post_actions_frame,
            text="📂 Ouvrir le dossier contenant l'EPUB",
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self._open_output_folder
        )
        self.open_file_btn = ctk.CTkButton(
            self.post_actions_frame,
            text="📖 Ouvrir le livre EPUB",
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self._open_output_file
        )

    # --- Callbacks et Logique ---

    def _change_theme(self, choice: str):
        """Change le thème de l'application."""
        mapping = {"Système": "System", "Sombre": "Dark", "Clair": "Light"}
        ctk.set_appearance_mode(mapping.get(choice, "System"))

    def _on_manga_toggle(self):
        """Active automatiquement le sens RTL si le mode Manga est coché."""
        if self.manga_mode_var.get():
            self.rtl_mode_var.set(True)

    def _browse_source_directory(self):
        """Sélectionne un dossier source et analyse son contenu."""
        folder = filedialog.askdirectory(title="Sélectionner le dossier source des images")
        if not folder:
            return

        source_path = Path(folder)
        self.source_dir = source_path
        self.source_path_var.set(str(source_path))

        # Proposer un titre par défaut basé sur le nom du dossier
        if not self.title_var.get() or self.title_var.get() == "Inconnu":
            self.title_var.set(source_path.name)

        # Proposer un chemin de sortie par défaut dans le dossier parent
        default_output = source_path.parent / f"{source_path.name}.epub"
        self.output_file = default_output
        self.output_path_var.set(str(default_output))

        # Lancer l'analyse du dossier
        self._analyze_source_directory()

    def _analyze_source_directory(self):
        """Analyse l'arborescence et met à jour les informations et l'aperçu."""
        if not self.source_dir or not self.source_dir.exists():
            return

        self._log(f"Analyse du dossier : {self.source_dir}...")
        try:
            self.chapters = collect_chapters_and_images(self.source_dir)
            self.total_images_count = sum(len(c.pages) for c in self.chapters)

            if not self.chapters or self.total_images_count == 0:
                self.scan_details_label.configure(
                    text="⚠️ Aucune image valide trouvée dans ce dossier !\nFormats acceptés : JPG, PNG, WEBP, GIF, BMP."
                )
                self._update_cover_thumbnail(None)
                self._log("Attention : aucune image valide trouvée.")
                return

            # Détails trouvés
            is_flat = len(self.chapters) == 1 and self.chapters[0].folder_path == self.source_dir
            structure_str = "Dossier plat (1 chapitre unique)" if is_flat else f"Structure avec {len(self.chapters)} chapitres / sous-dossiers"

            details = [
                f"✔ Structure détectée : {structure_str}",
                f"✔ Chapitres : {len(self.chapters)}",
                f"✔ Total d'images : {self.total_images_count} page(s)",
            ]

            # Afficher les premiers chapitres en résumé
            sample_chaps = ", ".join([f"'{c.title}' ({len(c.pages)}p)" for c in self.chapters[:3]])
            if len(self.chapters) > 3:
                sample_chaps += f" et {len(self.chapters) - 3} autres..."
            details.append(f"Aperçu : {sample_chaps}")

            self.scan_details_label.configure(text="\n".join(details))
            self._log(f"Scan terminé : {len(self.chapters)} chapitres, {self.total_images_count} images.")

            # Mise à jour de la miniature
            cover_img_path = self.chapters[0].pages[0].file_path if self.chapters[0].pages else None
            self._update_cover_thumbnail(cover_img_path)

        except Exception as e:
            self.scan_details_label.configure(text=f"Erreur d'analyse : {str(e)}")
            self._log(f"Erreur lors de l'analyse : {e}")

    def _update_cover_thumbnail(self, image_path: Optional[Path]):
        """Met à jour l'image miniature affichée dans l'interface."""
        if not image_path or not image_path.exists():
            self.thumb_label.configure(image=None, text="Aperçu\nCouverture")
            return

        try:
            with Image.open(image_path) as img:
                # Créer une copie convertie en RGB pour l'affichage
                img_copy = img.convert("RGB")
                img_copy.thumbnail((120, 160), Image.Resampling.LANCZOS)
                self.cover_thumbnail_image = ctk.CTkImage(
                    light_image=img_copy,
                    dark_image=img_copy,
                    size=img_copy.size
                )
                self.thumb_label.configure(image=self.cover_thumbnail_image, text="")
        except Exception as err:
            self.thumb_label.configure(image=None, text="Erreur\nImage")

    def _browse_custom_cover(self):
        """Sélectionne une image de couverture personnalisée."""
        filetypes = [
            ("Images", "*.jpg *.jpeg *.png *.webp *.gif *.bmp"),
            ("Tous les fichiers", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="Choisir une image de couverture", filetypes=filetypes)
        if file_path:
            p = Path(file_path)
            self.custom_cover_file = p
            self.cover_path_var.set(str(p))
            self._update_cover_thumbnail(p)
            self._log(f"Couverture personnalisée sélectionnée : {p.name}")

    def _clear_custom_cover(self):
        """Supprime la couverture personnalisée sélectionnée."""
        self.custom_cover_file = None
        self.cover_path_var.set("")
        if self.chapters and self.chapters[0].pages:
            self._update_cover_thumbnail(self.chapters[0].pages[0].file_path)
        else:
            self._update_cover_thumbnail(None)
        self._log("Couverture personnalisée réinitialisée.")

    def _browse_output_file(self):
        """Permet de choisir l'emplacement de sauvegarde du fichier EPUB."""
        initial_dir = self.source_dir.parent if self.source_dir else None
        initial_file = f"{self.title_var.get() or 'livre'}.epub"
        file_path = filedialog.asksaveasfilename(
            title="Enregistrer le fichier EPUB sous...",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".epub",
            filetypes=[("Livre numérique EPUB", "*.epub"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            self.output_file = Path(file_path)
            self.output_path_var.set(str(self.output_file))

    def _log(self, message: str):
        """Ajoute un message dans la console de logs."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _start_conversion(self):
        """Valide les paramètres et lance la conversion dans un thread séparé."""
        if self.is_converting:
            return

        # 1. Validations
        if not self.source_dir or not self.source_dir.exists():
            messagebox.showwarning("Dossier manquant", "Veuillez sélectionner un dossier source valide.")
            return

        if not self.chapters or self.total_images_count == 0:
            messagebox.showwarning("Aucune image", "Le dossier sélectionné ne contient aucune image valide.")
            return

        out_str = self.output_path_var.get().strip()
        if not out_str:
            messagebox.showwarning("Fichier de sortie manquant", "Veuillez indiquer un chemin pour le fichier EPUB.")
            return

        self.output_file = Path(out_str)
        if not self.output_file.name.lower().endswith(".epub"):
            self.output_file = self.output_file.with_suffix(".epub")
            self.output_path_var.set(str(self.output_file))

        title = self.title_var.get().strip() or self.source_dir.name
        author = self.author_var.get().strip() or "Inconnu"
        lang = self.lang_var.get().strip() or "fr"
        is_manga = self.manga_mode_var.get()
        is_rtl = self.rtl_mode_var.get()
        custom_cover = self.custom_cover_file if (self.custom_cover_file and self.custom_cover_file.exists()) else None

        # 2. Préparation de l'UI
        self.is_converting = True
        self.convert_btn.configure(state="disabled", text="⏳ Conversion en cours...")
        self.progress_bar.set(0.0)
        self.percent_label.configure(text="0%")
        self.status_label.configure(text="Démarrage de la conversion...", text_color=("black", "white"))
        self.open_folder_btn.pack_forget()
        self.open_file_btn.pack_forget()

        self._log("\n" + "=" * 50)
        self._log(f"Début de la conversion : '{title}'")
        self._log(f"Destination : {self.output_file}")
        self._log(f"Options : Manga={is_manga}, RTL={is_rtl}, Langue={lang}")

        # 3. Lancement dans un thread d'arrière-plan
        thread = threading.Thread(
            target=self._worker_conversion,
            args=(self.chapters, self.output_file, title, author, lang, custom_cover, is_manga, is_rtl),
            daemon=True
        )
        thread.start()

    def _worker_conversion(self, chapters, output_file, title, author, lang, custom_cover, is_manga, is_rtl):
        """Exécute la création de l'EPUB en arrière-plan."""
        def on_progress(current: int, total: int, chapter_title: str):
            ratio = current / total if total > 0 else 0.0
            percent = int(ratio * 100)
            self.after(0, self._update_progress, ratio, percent, current, total, chapter_title)

        try:
            res_path = create_epub(
                chapters=chapters,
                output_file=output_file,
                title=title,
                author=author,
                language=lang,
                custom_cover_path=custom_cover,
                is_manga=is_manga,
                is_rtl=is_rtl,
                progress_callback=on_progress
            )
            self.after(0, self._on_conversion_success, res_path)
        except Exception as e:
            self.after(0, self._on_conversion_error, str(e))

    def _update_progress(self, ratio: float, percent: int, current: int, total: int, chapter_title: str):
        """Met à jour les indicateurs de progression de façon thread-safe."""
        self.progress_bar.set(ratio)
        self.percent_label.configure(text=f"{percent}%")
        self.status_label.configure(text=f"Traitement : {chapter_title} (Page {current}/{total})")

    def _on_conversion_success(self, output_path: Path):
        """Gère la fin réussie de la conversion."""
        self.is_converting = False
        self.convert_btn.configure(state="normal", text="🚀 Convertir en EPUB")
        self.progress_bar.set(1.0)
        self.percent_label.configure(text="100%")
        self.status_label.configure(
            text=f"✔ Conversion terminée avec succès ! ({output_path.name})",
            text_color=("green", "#2ecc71")
        )

        size_mb = output_path.stat().st_size / (1024 * 1024)
        self._log(f"✔ Succès ! Fichier généré : {output_path} ({size_mb:.2f} Mo)")
        self._log("=" * 50)

        # Afficher les boutons d'ouverture
        self.open_folder_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.open_file_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

        messagebox.showinfo(
            "Conversion réussie",
            f"Le livre EPUB a été généré avec succès !\n\nFichier : {output_path.name}\nTaille : {size_mb:.2f} Mo"
        )

    def _on_conversion_error(self, error_message: str):
        """Gère une erreur survenue pendant la conversion."""
        self.is_converting = False
        self.convert_btn.configure(state="normal", text="🚀 Convertir en EPUB")
        self.status_label.configure(
            text="❌ Une erreur est survenue lors de la conversion.",
            text_color=("red", "#e74c3c")
        )
        self._log(f"❌ ERREUR : {error_message}")
        messagebox.showerror("Erreur de conversion", f"Échec de la conversion :\n\n{error_message}")

    def _open_output_folder(self):
        """Ouvre le dossier contenant le fichier généré dans l'explorateur."""
        if self.output_file and self.output_file.exists():
            folder = self.output_file.parent
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", folder])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", folder])

    def _open_output_file(self):
        """Ouvre le fichier EPUB avec le lecteur par défaut du système."""
        if self.output_file and self.output_file.exists():
            if sys.platform == "win32":
                os.startfile(self.output_file)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", self.output_file])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", self.output_file])


def main():
    """Point d'entrée de l'interface graphique."""
    app = FolderToEpubApp()
    app.mainloop()


if __name__ == "__main__":
    main()
