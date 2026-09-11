"""Modern GUI application controller."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

from folder_to_epub.core.constants import APP_TITLE, AVAILABLE_LANGUAGES
from folder_to_epub.core.models import Book, Chapter, ConversionConfig, ProgressEvent
from folder_to_epub.services.archive import ArchiveService
from folder_to_epub.services.scanner import ScannerService
from folder_to_epub.services.converter import ConversionService
from folder_to_epub.ui.theme import THEME_COLORS
from folder_to_epub.ui.worker import AsyncWorker
from folder_to_epub.ui.components.sidebar import SidebarComponent
from folder_to_epub.ui.views.dashboard_view import DashboardView
from folder_to_epub.ui.views.books_view import BooksView
from folder_to_epub.ui.views.logs_view import LogsView
from folder_to_epub.ui.views.settings_view import SettingsView


class FolderToEpubApp(ctk.CTk):
    """Main window coordinator managing views, application state, and background tasks."""

    def __init__(self):
        super().__init__()

        self.title(f"{APP_TITLE} - Modern GUI")
        self.geometry("1080x760")
        self.minsize(940, 640)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # State
        self.source_dir: Optional[Path] = None
        self.output_file: Optional[Path] = None
        self.custom_cover_file: Optional[Path] = None
        self.auto_root_cover: Optional[Path] = None

        self.is_batch_mode: bool = False
        self.books: List[Book] = []
        self.chapters: List[Chapter] = []
        self.total_images_count: int = 0
        self.is_converting: bool = False
        self.cover_thumbnail_image: Optional[ctk.CTkImage] = None

        # Form variables
        self.title_var = ctk.StringVar(value="")
        self.author_var = ctk.StringVar(value="Unknown")
        self.lang_var = ctk.StringVar(value=AVAILABLE_LANGUAGES[0][1])
        self.manga_mode_var = ctk.BooleanVar(value=False)
        self.rtl_mode_var = ctk.BooleanVar(value=False)
        self.batch_switch_var = ctk.BooleanVar(value=False)
        self.source_path_var = ctk.StringVar(value="")
        self.output_path_var = ctk.StringVar(value="")

        self._build_layout()
        self.show_view("dashboard")
        self.log(f"{APP_TITLE} started. Ready.")

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Left Sidebar
        self.sidebar = SidebarComponent(
            self,
            on_navigate=self.show_view,
            on_theme_change=self.on_theme_change
        )

        # 2. Main View Container
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
        """Activates a view and updates sidebar highlight."""
        for v_id, view_widget in self.views.items():
            if v_id == view_id:
                view_widget.grid(row=0, column=0, sticky="nsew")
            else:
                view_widget.grid_forget()

        self.sidebar.set_active_tab(view_id)
        if view_id == "chapters":
            self.books_view.refresh()

    def on_theme_change(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)
        self.log(f"Appearance theme switched to: {mode}")

    def log(self, message: str) -> None:
        self.logs_view.append_log(message)
        self.dashboard_view.status_card.log_snippet.configure(text=message)

    # -------------------------------------------------------------------------
    # Directory Analysis
    # -------------------------------------------------------------------------

    def on_browse_source(self) -> None:
        directory = filedialog.askdirectory(title="Select Folder with Images or Books")
        if not directory:
            return

        self.source_dir = Path(directory)
        self.source_path_var.set(str(self.source_dir))
        self.analyze_source_directory()

    def on_browse_archive(self) -> None:
        """Invoked when user clicks Archive button to select a .cbz or .zip directly."""
        filename = filedialog.askopenfilename(
            title="Select Comic or Manga Archive",
            filetypes=[("Comic / Zip Archives", "*.cbz;*.zip"), ("All Files", "*.*")]
        )
        if not filename:
            return

        self.source_dir = Path(filename)
        self.source_path_var.set(str(self.source_dir))
        self.analyze_source_directory()

    def analyze_source_directory(self) -> None:
        """Inspects directory or archive for batch books or single book structure."""
        if not self.source_dir or not self.source_dir.exists():
            return

        self.log(f"Analyzing source: {self.source_dir}")

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
                f"Multi-book batch collection with {self.total_images_count} total pages."
            )
            self.dashboard_view.action_banner.set_status(f"Batch collection: {len(self.books)} books")
            self.dashboard_view.action_banner.set_button_state(True, f"🚀 Convert {len(self.books)} Books")
            self.dashboard_view.source_card.stats_label.configure(
                text=f"{len(self.books)} books (Batch mode) • {self.total_images_count} total pages"
            )

            out_dir = self.source_dir.parent / f"{self.source_dir.stem if ArchiveService.is_archive(self.source_dir) else self.source_dir.name}_epubs"
            self.output_file = out_dir
            self.output_path_var.set(str(out_dir))

            # Cover preview from first book
            if self.books and self.books[0].is_archive and self.books[0].archive_path:
                cover_data = ArchiveService.get_cover_bytes(self.books[0].archive_path)
                self._update_cover_preview(None, is_auto=True, archive_cover=cover_data)
            else:
                first_cov = self.books[0].cover_path if self.books else None
                self.auto_root_cover = first_cov
                self._update_cover_preview(first_cov, is_auto=True)
            self.log(f"Batch collection detected: {len(self.books)} books.")

        elif detected_books and detected_books[0].is_archive:
            # Single archive book
            single_book = detected_books[0]
            self.books = [single_book]
            self.chapters = single_book.chapters
            self.total_images_count = single_book.total_images

            self.dashboard_view.hero.update_state(
                "shield",
                "Archive Ready to Convert",
                f"Loaded archive '{single_book.title}' ({self.total_images_count} estimated pages)."
            )
            self.dashboard_view.action_banner.set_status(f"Archive book ready ({self.source_dir.suffix.upper()})")
            self.dashboard_view.action_banner.set_button_state(True, "🚀 Convert to EPUB")
            self.dashboard_view.source_card.stats_label.configure(
                text=f"Archive: {self.source_dir.name} • {self.total_images_count} pages"
            )

            if not self.title_var.get():
                self.title_var.set(single_book.title)

            out_epub = self.source_dir.with_suffix('.epub')
            self.output_file = out_epub
            self.output_path_var.set(str(out_epub))

            cover_data = ArchiveService.get_cover_bytes(self.source_dir)
            self._update_cover_preview(self.custom_cover_file, is_auto=True, archive_cover=cover_data)
            self.log(f"Loaded archive book: {single_book.title} ({self.total_images_count} pages).")

        else:
            self.books = []
            self.chapters = ScannerService.scan_chapters(self.source_dir)
            self.total_images_count = sum(c.page_count for c in self.chapters)

            if not self.chapters:
                self.dashboard_view.hero.update_state(
                    "alert",
                    "No Images Discovered",
                    "The selected folder does not contain supported images."
                )
                self.dashboard_view.action_banner.set_status("No images detected")
                self.dashboard_view.action_banner.set_button_state(False)
                self.dashboard_view.source_card.stats_label.configure(text="0 images found")
                self.log("Warning: No valid images found.")
                return

            self.dashboard_view.hero.update_state(
                "shield",
                "Ready to Convert",
                f"Loaded '{self.source_dir.name}' ({len(self.chapters)} chapters, {self.total_images_count} pages)."
            )
            self.dashboard_view.action_banner.set_status("Single book ready for conversion")
            self.dashboard_view.action_banner.set_button_state(True, "🚀 Convert to EPUB")
            self.dashboard_view.source_card.stats_label.configure(
                text=f"{len(self.chapters)} chapter(s) • {self.total_images_count} pages"
            )

            if not self.title_var.get():
                self.title_var.set(self.source_dir.name)

            out_epub = self.source_dir.with_suffix('.epub')
            self.output_file = out_epub
            self.output_path_var.set(str(out_epub))

            self.auto_root_cover = ScannerService.find_cover(self.source_dir)
            cover_to_show = self.custom_cover_file or self.auto_root_cover
            if not cover_to_show and self.chapters and self.chapters[0].pages:
                cover_to_show = self.chapters[0].pages[0].file_path

            self._update_cover_preview(cover_to_show, is_auto=(cover_to_show == self.auto_root_cover))
            self.log(f"Loaded single book: {len(self.chapters)} chapters, {self.total_images_count} pages.")

    def on_batch_toggle(self) -> None:
        if not self.source_dir:
            return
        is_checked = self.batch_switch_var.get()
        is_batch, detected_books = ScannerService.detect_books(self.source_dir, force_batch=is_checked)
        self.is_batch_mode = is_batch
        self.analyze_source_directory()

    def on_manga_toggle(self) -> None:
        if self.manga_mode_var.get():
            self.rtl_mode_var.set(True)

    # -------------------------------------------------------------------------
    # Cover Management
    # -------------------------------------------------------------------------

    def on_choose_cover(self) -> None:
        chosen = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.gif")]
        )
        if chosen:
            self.custom_cover_file = Path(chosen)
            self._update_cover_preview(self.custom_cover_file, is_auto=False)
            self.log(f"Custom cover chosen: {self.custom_cover_file.name}")

    def on_reset_cover(self) -> None:
        self.custom_cover_file = None
        cover_to_show = self.auto_root_cover
        if not cover_to_show and self.chapters and self.chapters[0].pages:
            cover_to_show = self.chapters[0].pages[0].file_path
        self._update_cover_preview(cover_to_show, is_auto=True)
        self.log("Cover reset to automatic detection.")

    def _update_cover_preview(
        self,
        image_path: Optional[Path] = None,
        is_auto: bool = True,
        archive_cover: Optional[tuple] = None
    ) -> None:
        import io
        card = self.dashboard_view.cover_card

        # Check in-memory archive cover bytes
        if archive_cover and not image_path:
            try:
                filename, data = archive_cover
                with Image.open(io.BytesIO(data)) as img:
                    img_copy = img.copy()
                    img_copy.thumbnail((80, 110))
                    self.cover_thumbnail_image = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
                    card.thumb_label.configure(text="", image=self.cover_thumbnail_image)
                card.status_label.configure(text=f"Archive: {filename}")
                return
            except Exception as e:
                self.log(f"Archive cover error: {e}")

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
            self.log(f"Thumbnail generation error: {e}")

    # -------------------------------------------------------------------------
    # Destination & File Actions
    # -------------------------------------------------------------------------

    def on_browse_output(self) -> None:
        if self.is_batch_mode:
            dest = filedialog.askdirectory(title="Select Destination Directory for EPUBs")
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
        if self.output_file and self.output_file.exists() and self.output_file.is_file():
            if sys.platform.startswith('win'):
                os.startfile(self.output_file)
            else:
                subprocess.run(['xdg-open', str(self.output_file)])

    def on_open_folder(self) -> None:
        folder = self.output_file if (self.output_file and self.output_file.is_dir()) else (self.output_file.parent if self.output_file else None)
        if folder and folder.exists():
            if sys.platform.startswith('win'):
                os.startfile(folder)
            else:
                subprocess.run(['xdg-open', str(folder)])

    # -------------------------------------------------------------------------
    # Conversion Worker
    # -------------------------------------------------------------------------

    def on_convert_click(self) -> None:
        if self.is_converting:
            return
        if not self.source_dir or not self.source_dir.exists():
            messagebox.showwarning("Warning", "Select a valid source directory or archive first.")
            return

        self.is_converting = True
        self.dashboard_view.action_banner.set_button_state(False, "Converting...")
        self.dashboard_view.action_banner.set_progress(0.0, "0%")
        self.dashboard_view.hero.update_state("gear", "Conversion in Progress...", "Building EPUB files. Please wait.")
        self.log("Conversion task started.")

        AsyncWorker.run(self._run_conversion)

    def _run_conversion(self) -> None:
        try:
            selected_lang_str = self.lang_var.get()
            lang_code = selected_lang_str.split()[0] if selected_lang_str else "en"

            base_config = ConversionConfig(
                title=self.title_var.get() or (self.source_dir.stem if ArchiveService.is_archive(self.source_dir) else self.source_dir.name),
                author=self.author_var.get() or "Unknown",
                language=lang_code,
                is_manga=self.manga_mode_var.get(),
                is_rtl=self.rtl_mode_var.get()
            )

            if self.is_batch_mode:
                out_dir = Path(self.output_path_var.get()) if self.output_path_var.get() else self.source_dir.parent / f"{self.source_dir.stem if ArchiveService.is_archive(self.source_dir) else self.source_dir.name}_epubs"

                def on_batch_progress(ev: ProgressEvent):
                    ratio = (ev.current_book_index - 1) / ev.total_books + (ev.current_step / max(ev.total_steps, 1)) / ev.total_books
                    lbl = f"Book {ev.current_book_index}/{ev.total_books} (p. {ev.current_step}/{ev.total_steps})"
                    self.after(0, lambda r=ratio, l=lbl: self.dashboard_view.action_banner.set_progress(r, l))

                created = ConversionService.convert_batch(
                    books=self.books,
                    output_dir=out_dir,
                    base_config=base_config,
                    progress_callback=on_batch_progress
                )
                self.after(0, lambda: self._on_success(out_dir, is_batch=True, count=len(created)))

            else:
                out_epub = Path(self.output_path_var.get()) if self.output_path_var.get() else self.source_dir.with_suffix('.epub')
                base_config.output_path = out_epub
                base_config.custom_cover_path = self.custom_cover_file or self.auto_root_cover
                base_config.source_dir = self.source_dir

                if self.books and self.books[0].is_archive:
                    single_book = self.books[0]
                else:
                    single_book = Book(
                        title=self.title_var.get() or self.source_dir.name,
                        folder_path=self.source_dir,
                        chapters=self.chapters,
                        cover_path=self.custom_cover_file or self.auto_root_cover
                    )

                def on_single_progress(ev: ProgressEvent):
                    ratio = ev.current_step / max(ev.total_steps, 1)
                    lbl = f"{int(ratio * 100)}% ({ev.current_step}/{ev.total_steps})"
                    self.after(0, lambda r=ratio, l=lbl: self.dashboard_view.action_banner.set_progress(r, l))

                final_epub = ConversionService.convert_book(
                    book=single_book,
                    config=base_config,
                    progress_callback=on_single_progress
                )
                self.after(0, lambda: self._on_success(final_epub, is_batch=False))

        except Exception as e:
            self.after(0, lambda err=str(e): self._on_error(err))

    def _on_success(self, destination: Path, is_batch: bool = False, count: int = 1) -> None:
        self.is_converting = False
        self.dashboard_view.action_banner.set_progress(1.0, "100%")
        btn_text = f"🚀 Convert {len(self.books)} Books" if self.is_batch_mode else "🚀 Convert to EPUB"
        self.dashboard_view.action_banner.set_button_state(True, btn_text)

        self.dashboard_view.destination_card.open_dir_btn.configure(state="normal")
        if not is_batch:
            self.dashboard_view.destination_card.open_epub_btn.configure(state="normal")

        msg = f"Batch completed: {count} books created in {destination.name}" if is_batch else f"EPUB created successfully: {destination.name}"
        self.dashboard_view.hero.update_state("check", "Conversion Completed!", msg)
        self.log(f"SUCCESS: {destination.resolve()}")
        messagebox.showinfo("Success", f"EPUB eBook successfully generated!\n\nDestination:\n{destination.resolve()}")

    def _on_error(self, error_msg: str) -> None:
        self.is_converting = False
        btn_text = f"🚀 Convert {len(self.books)} Books" if self.is_batch_mode else "🚀 Convert to EPUB"
        self.dashboard_view.action_banner.set_button_state(True, btn_text)
        self.dashboard_view.hero.update_state("alert", "Conversion Error", error_msg)
        self.log(f"ERROR: {error_msg}")
        messagebox.showerror("Error", f"Conversion failed:\n\n{error_msg}")


def main():
    app = FolderToEpubApp()
    app.mainloop()


if __name__ == "__main__":
    main()
