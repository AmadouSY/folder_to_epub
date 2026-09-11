"""Main application controller for the Graphical User Interface (GUI)."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

from core.constants import APP_TITLE, AVAILABLE_LANGUAGES
from core.models import BookData, ChapterData, ConversionConfig
from services.scanner import ScannerService
from services.converter import ConversionService
from ui.theme import THEME_COLORS
from ui.worker import AsyncWorker
from ui.components.sidebar import SidebarComponent
from ui.views.dashboard_view import DashboardView
from ui.views.books_view import BooksView
from ui.views.logs_view import LogsView
from ui.views.settings_view import SettingsView


class FolderToEpubApp(ctk.CTk):
    """Main application window and coordinator between UI views and services."""

    def __init__(self):
        super().__init__()

        # Main window configuration
        self.title(f"{APP_TITLE} - Modern GUI")
        self.geometry("1080x760")
        self.minsize(940, 640)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Application state
        self.source_dir: Optional[Path] = None
        self.output_file: Optional[Path] = None
        self.custom_cover_file: Optional[Path] = None
        self.auto_root_cover: Optional[Path] = None

        self.is_batch_mode: bool = False
        self.books: List[BookData] = []
        self.chapters: List[ChapterData] = []
        self.total_images_count: int = 0
        self.is_converting: bool = False
        self.cover_thumbnail_image: Optional[ctk.CTkImage] = None

        # Control variables
        self.title_var = ctk.StringVar(value="")
        self.author_var = ctk.StringVar(value="Unknown")
        self.lang_var = ctk.StringVar(value=AVAILABLE_LANGUAGES[0][1])
        self.manga_mode_var = ctk.BooleanVar(value=False)
        self.rtl_mode_var = ctk.BooleanVar(value=False)
        self.batch_switch_var = ctk.BooleanVar(value=False)
        self.source_path_var = ctk.StringVar(value="")
        self.output_path_var = ctk.StringVar(value="")
        self.cover_path_var = ctk.StringVar(value="")

        # Build UI layout
        self._build_layout()
        self.show_view("dashboard")
        self.log(f"{APP_TITLE} initialized. Clean Architecture ready.")

    @property
    def card_source_stats(self) -> ctk.CTkLabel:
        """Backward-compatibility property exposing the stats label."""
        return self.dashboard_view.source_card.stats_label

    def _build_layout(self) -> None:
        """Sets up window grid, sidebar, and view container."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Left Sidebar
        self.sidebar = SidebarComponent(
            self,
            on_navigate=self.show_view,
            on_theme_change=self.on_theme_change
        )

        # 2. Dynamic View Container
        self.container = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=(THEME_COLORS["surface_light"], THEME_COLORS["surface_dark"])
        )
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # 3. Instantiate Views
        self.dashboard_view = DashboardView(self.container, self)
        self.books_view = BooksView(self.container, self)
        self.logs_view = LogsView(self.container)
        self.settings_view = SettingsView(self.container)

        self.views = {
            "dashboard": self.dashboard_view,
            "chapters": self.books_view,
            "logs": self.logs_view,
            "settings": self.settings_view
        }

    def show_view(self, view_id: str) -> None:
        """Displays the requested view and updates sidebar tab highlight."""
        for v_id, view_widget in self.views.items():
            if v_id == view_id:
                view_widget.grid(row=0, column=0, sticky="nsew")
            else:
                view_widget.grid_forget()

        self.sidebar.set_active_tab(view_id)
        if view_id == "chapters":
            self.books_view.refresh()

    def on_theme_change(self, mode: str) -> None:
        """Switches the appearance mode between System, Dark, and Light."""
        ctk.set_appearance_mode(mode)
        self.log(f"Theme changed to: {mode}")

    def log(self, message: str) -> None:
        """Appends log text to the console and status card."""
        self.logs_view.append_log(message)
        self.dashboard_view.status_card.log_snippet.configure(text=message)

    # -------------------------------------------------------------------------
    # Directory Inspection & Analysis
    # -------------------------------------------------------------------------

    def on_browse_source(self) -> None:
        """Invoked when user clicks Browse for source directory."""
        directory = filedialog.askdirectory(title="Select Folder with Images or Books")
        if not directory:
            return

        self.source_dir = Path(directory)
        self.source_path_var.set(str(self.source_dir))
        self._analyze_source_directory()

    def _analyze_source_directory(self) -> None:
        """Analyzes directory to determine structure, books, chapters, and covers."""
        if not self.source_dir or not self.source_dir.exists():
            return

        self.log(f"Inspecting directory: {self.source_dir}")

        # Check for batch multi-books
        is_batch, detected_books = ScannerService.detect_books(
            self.source_dir,
            force_batch=self.batch_switch_var.get() if self.batch_switch_var.get() else None
        )

        self.is_batch_mode = is_batch and len(detected_books) > 1
        self.batch_switch_var.set(self.is_batch_mode)

        if self.is_batch_mode:
            self.books = detected_books
            self.chapters = []
            self.total_images_count = sum(b.total_images for b in self.books)

            self.dashboard_view.hero.update_state(
                "books",
                f"Collection Ready ({len(self.books)} Books)",
                f"Detected multi-book batch collection with {self.total_images_count} total pages."
            )
            self.dashboard_view.action_banner.set_status(f"Batch collection detected: {len(self.books)} books")
            self.dashboard_view.action_banner.set_button_state(True, f"🚀 Convert {len(self.books)} Books")

            self.dashboard_view.source_card.stats_label.configure(
                text=f"{len(self.books)} books (Batch mode) • {self.total_images_count} total pages"
            )

            # Pre-fill batch output destination folder
            out_dir = self.source_dir.parent / f"{self.source_dir.name}_epubs"
            self.output_file = out_dir
            self.output_path_var.set(str(out_dir))

            # Cover thumbnail from first book if present
            first_cov = self.books[0].cover_path if self.books else None
            self.auto_root_cover = first_cov
            self._update_cover_preview(first_cov, is_auto=True)
            self.log(f"Batch mode activated with {len(self.books)} books.")

        else:
            # Single book
            self.books = []
            self.chapters = ScannerService.collect_chapters_and_images(self.source_dir)
            self.total_images_count = sum(len(c.pages) for c in self.chapters)

            if not self.chapters:
                self.dashboard_view.hero.update_state(
                    "alert",
                    "No Images Found",
                    "The selected directory contains no supported images."
                )
                self.dashboard_view.action_banner.set_status("No images detected")
                self.dashboard_view.action_banner.set_button_state(False)
                self.dashboard_view.source_card.stats_label.configure(text="0 images found")
                self.log("Warning: No valid images found.")
                return

            self.dashboard_view.hero.update_state(
                "shield",
                "Ready to Convert",
                f"Loaded '{self.source_dir.name}' with {len(self.chapters)} chapter(s) and {self.total_images_count} page(s)."
            )
            self.dashboard_view.action_banner.set_status("Single book ready for conversion")
            self.dashboard_view.action_banner.set_button_state(True, "🚀 Convert to EPUB")

            self.dashboard_view.source_card.stats_label.configure(
                text=f"{len(self.chapters)} chapter(s) • {self.total_images_count} pages"
            )

            # Pre-fill title & output path
            if not self.title_var.get():
                self.title_var.set(self.source_dir.name)

            out_epub = self.source_dir.with_suffix('.epub')
            self.output_file = out_epub
            self.output_path_var.set(str(out_epub))

            # Check root cover
            self.auto_root_cover = ScannerService.find_root_cover(self.source_dir)
            cover_to_show = self.custom_cover_file or self.auto_root_cover
            if not cover_to_show and self.chapters and self.chapters[0].pages:
                cover_to_show = self.chapters[0].pages[0].file_path

            self._update_cover_preview(cover_to_show, is_auto=(cover_to_show == self.auto_root_cover))
            self.log(f"Loaded single book: {len(self.chapters)} chapter(s), {self.total_images_count} pages.")

    def on_batch_toggle(self) -> None:
        """Handles manual toggle of the batch switch."""
        if not self.source_dir:
            return
        is_checked = self.batch_switch_var.get()
        is_batch, detected_books = ScannerService.detect_books(self.source_dir, force_batch=is_checked)
        self.is_batch_mode = is_batch
        self._analyze_source_directory()

    def on_manga_toggle(self) -> None:
        """Automatically checks RTL when Manga mode is turned on."""
        if self.manga_mode_var.get():
            self.rtl_mode_var.set(True)

    # -------------------------------------------------------------------------
    # Cover Management
    # -------------------------------------------------------------------------

    def on_choose_cover(self) -> None:
        """Allows user to select a custom cover image."""
        chosen = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.gif")]
        )
        if chosen:
            self.custom_cover_file = Path(chosen)
            self._update_cover_preview(self.custom_cover_file, is_auto=False)
            self.log(f"Custom cover selected: {self.custom_cover_file.name}")

    def on_reset_cover(self) -> None:
        """Resets cover to automatic detection."""
        self.custom_cover_file = None
        cover_to_show = self.auto_root_cover
        if not cover_to_show and self.chapters and self.chapters[0].pages:
            cover_to_show = self.chapters[0].pages[0].file_path
        self._update_cover_preview(cover_to_show, is_auto=True)
        self.log("Cover reset to auto-detection.")

    def _update_cover_preview(self, image_path: Optional[Path], is_auto: bool = True) -> None:
        """Generates and displays an 80x110 thumbnail in CoverCard."""
        card = self.dashboard_view.cover_card
        if not image_path or not image_path.exists():
            card.thumb_label.configure(text="No\nCover", image=None)
            card.status_label.configure(text="No cover detected")
            self.cover_thumbnail_image = None
            return

        try:
            with Image.open(image_path) as img:
                img_copy = img.copy()
                img_copy.thumbnail((80, 110))
                self.cover_thumbnail_image = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
                card.thumb_label.configure(text="", image=self.cover_thumbnail_image)

            status_text = f"Auto: {image_path.name}" if is_auto else f"Custom: {image_path.name}"
            card.status_label.configure(text=status_text)
        except Exception as e:
            card.thumb_label.configure(text="Error", image=None)
            card.status_label.configure(text="Failed to load cover")
            self.log(f"Cover thumbnail error: {e}")

    # -------------------------------------------------------------------------
    # Output Destination & Actions
    # -------------------------------------------------------------------------

    def on_browse_output(self) -> None:
        """Allows user to select destination file or folder."""
        if self.is_batch_mode:
            dest = filedialog.askdirectory(title="Select Output Directory for EPUBs")
            if dest:
                self.output_file = Path(dest)
                self.output_path_var.set(str(self.output_file))
        else:
            dest = filedialog.asksaveasfilename(
                title="Save EPUB As",
                defaultextension=".epub",
                filetypes=[("EPUB eBook", "*.epub")]
            )
            if dest:
                self.output_file = Path(dest)
                self.output_path_var.set(str(self.output_file))

    def on_open_epub(self) -> None:
        """Opens the created EPUB file in the default system viewer."""
        if self.output_file and self.output_file.exists() and self.output_file.is_file():
            if sys.platform.startswith('win'):
                os.startfile(self.output_file)
            else:
                subprocess.run(['xdg-open', str(self.output_file)])

    def on_open_folder(self) -> None:
        """Opens the folder containing generated EPUB(s) in file explorer."""
        folder = self.output_file if (self.output_file and self.output_file.is_dir()) else (self.output_file.parent if self.output_file else None)
        if folder and folder.exists():
            if sys.platform.startswith('win'):
                os.startfile(folder)
            else:
                subprocess.run(['xdg-open', str(folder)])

    # -------------------------------------------------------------------------
    # Conversion Orchestration
    # -------------------------------------------------------------------------

    def on_convert_click(self) -> None:
        """Validates and triggers background conversion."""
        if self.is_converting:
            return

        if not self.source_dir or not self.source_dir.exists():
            messagebox.showwarning("Warning", "Please select a valid source directory first.")
            return

        self.is_converting = True
        self.dashboard_view.action_banner.set_button_state(False, "Converting...")
        self.dashboard_view.action_banner.set_progress(0.0, "0%")
        self.dashboard_view.hero.update_state("gear", "Conversion in Progress...", "Generating EPUB eBooks. Please wait.")
        self.log("Conversion started...")

        # Run conversion in background thread
        AsyncWorker.run(self._run_conversion)

    def _run_conversion(self) -> None:
        """Background thread worker for single or batch conversion."""
        try:
            # Extract ISO language code from dropdown label
            selected_lang_str = self.lang_var.get()
            lang_code = selected_lang_str.split()[0] if selected_lang_str else "en"

            if self.is_batch_mode:
                out_dir = Path(self.output_path_var.get()) if self.output_path_var.get() else self.source_dir.parent / f"{self.source_dir.name}_epubs"

                def on_batch_progress(b_idx, total_b, book, curr_p, total_p):
                    ratio = (b_idx - 1) / total_b + (curr_p / max(total_p, 1)) / total_b
                    lbl = f"Book {b_idx}/{total_b} (p. {curr_p}/{total_p})"
                    self.after(0, lambda r=ratio, l=lbl: self._update_progress_ui(r, l))

                created_files = ConversionService.convert_batch(
                    books=self.books,
                    output_dir=out_dir,
                    author=self.author_var.get() or "Unknown",
                    language=lang_code,
                    is_manga=self.manga_mode_var.get(),
                    is_rtl=self.rtl_mode_var.get(),
                    progress_callback=on_batch_progress
                )
                self.after(0, lambda: self._on_conversion_success(out_dir, is_batch=True, count=len(created_files)))

            else:
                out_epub = Path(self.output_path_var.get()) if self.output_path_var.get() else self.source_dir.with_suffix('.epub')

                def on_single_progress(curr, total, chap):
                    ratio = curr / max(total, 1)
                    lbl = f"{int(ratio * 100)}% ({curr}/{total})"
                    self.after(0, lambda r=ratio, l=lbl: self._update_progress_ui(r, l))

                final_epub = ConversionService.convert_single_book(
                    book=BookData(
                        title=self.title_var.get() or self.source_dir.name,
                        folder_path=self.source_dir,
                        chapters=self.chapters,
                        cover_path=self.custom_cover_file or self.auto_root_cover
                    ),
                    config=ConversionConfig(
                        title=self.title_var.get() or self.source_dir.name,
                        author=self.author_var.get() or "Unknown",
                        language=lang_code,
                        output_path=out_epub,
                        custom_cover_path=self.custom_cover_file or self.auto_root_cover,
                        source_dir=self.source_dir,
                        is_manga=self.manga_mode_var.get(),
                        is_rtl=self.rtl_mode_var.get()
                    ),
                    progress_callback=on_single_progress
                )
                self.after(0, lambda: self._on_conversion_success(final_epub, is_batch=False))

        except Exception as e:
            self.after(0, lambda err=str(e): self._on_conversion_error(err))

    def _update_progress_ui(self, ratio: float, label: str) -> None:
        """Thread-safe update of the progress bar and status."""
        self.dashboard_view.action_banner.set_progress(ratio, label)

    def _on_conversion_success(self, destination: Path, is_batch: bool = False, count: int = 1) -> None:
        """Invoked upon successful completion of conversion."""
        self.is_converting = False
        self.dashboard_view.action_banner.set_progress(1.0, "100%")
        btn_text = f"🚀 Convert {len(self.books)} Books" if self.is_batch_mode else "🚀 Convert to EPUB"
        self.dashboard_view.action_banner.set_button_state(True, btn_text)

        # Enable Open buttons
        self.dashboard_view.destination_card.open_dir_btn.configure(state="normal")
        if not is_batch:
            self.dashboard_view.destination_card.open_epub_btn.configure(state="normal")

        msg = f"Batch completed: {count} books created in {destination.name}" if is_batch else f"EPUB created successfully: {destination.name}"
        self.dashboard_view.hero.update_state("check", "Conversion Completed!", msg)
        self.log(f"SUCCESS: {destination.resolve()}")

        messagebox.showinfo("Success", f"EPUB eBook successfully created!\n\nDestination:\n{destination.resolve()}")

    def _on_conversion_error(self, error_msg: str) -> None:
        """Invoked if an exception is raised during conversion."""
        self.is_converting = False
        btn_text = f"🚀 Convert {len(self.books)} Books" if self.is_batch_mode else "🚀 Convert to EPUB"
        self.dashboard_view.action_banner.set_button_state(True, btn_text)
        self.dashboard_view.hero.update_state("alert", "Conversion Error", error_msg)
        self.log(f"ERROR: {error_msg}")
        messagebox.showerror("Conversion Error", f"An error occurred during EPUB generation:\n\n{error_msg}")


def main():
    """Launches the modern GUI application."""
    app = FolderToEpubApp()
    app.mainloop()


if __name__ == "__main__":
    main()
