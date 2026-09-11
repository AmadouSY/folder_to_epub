"""Books and chapters explorer view."""

import customtkinter as ctk
from typing import TYPE_CHECKING
from ui.theme import THEME_COLORS

if TYPE_CHECKING:
    from ui.app import FolderToEpubApp


class BooksView(ctk.CTkFrame):
    """Visual explorer detailing detected books, chapters, and pages."""

    def __init__(self, parent: ctk.CTkFrame, app: 'FolderToEpubApp'):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="📚 Books & Chapters Explorer",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(anchor="w")

        self.summary_label = ctk.CTkLabel(
            header,
            text="No source directory loaded.",
            font=ctk.CTkFont(size=13),
            text_color="gray50"
        )
        self.summary_label.pack(anchor="w", pady=(2, 0))

        # Scrollable list container
        self.list_scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            fg_color=(THEME_COLORS["card_light"], THEME_COLORS["card_dark"]),
            border_width=1,
            border_color=(THEME_COLORS["card_border_light"], THEME_COLORS["card_border_dark"])
        )
        self.list_scroll.pack(fill="both", expand=True, padx=24, pady=(10, 24))

        self.empty_label = ctk.CTkLabel(
            self.list_scroll,
            text="Select a folder on the Dashboard to inspect its books and chapters.",
            font=ctk.CTkFont(size=13),
            text_color="gray50"
        )
        self.empty_label.pack(pady=40)

    def refresh(self) -> None:
        """Populates the list with detected books or chapters."""
        for child in self.list_scroll.winfo_children():
            child.destroy()

        if self.app.is_batch_mode and self.app.books:
            self.summary_label.configure(
                text=f"Batch Collection: {len(self.app.books)} book(s) discovered."
            )
            for idx, book in enumerate(self.app.books, start=1):
                item = ctk.CTkFrame(self.list_scroll, fg_color=("gray90", "#262b35"), corner_radius=8)
                item.pack(fill="x", padx=10, pady=6)

                icon = ctk.CTkLabel(item, text="📖", font=ctk.CTkFont(size=20))
                icon.pack(side="left", padx=12, pady=10)

                col = ctk.CTkFrame(item, fg_color="transparent")
                col.pack(side="left", fill="x", expand=True, pady=8)

                title_lbl = ctk.CTkLabel(col, text=f"{idx}. {book.title}", font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
                title_lbl.pack(fill="x")

                cov_str = book.cover_path.name if book.cover_path else "1st page"
                sub_lbl = ctk.CTkLabel(
                    col,
                    text=f"{len(book.chapters)} chapter(s) • {book.total_images} pages • Cover: {cov_str}",
                    font=ctk.CTkFont(size=11),
                    text_color="gray50",
                    anchor="w"
                )
                sub_lbl.pack(fill="x")

        elif self.app.chapters:
            self.summary_label.configure(
                text=f"Single Book: {len(self.app.chapters)} chapter(s), {self.app.total_images_count} total pages."
            )
            for idx, chap in enumerate(self.app.chapters, start=1):
                item = ctk.CTkFrame(self.list_scroll, fg_color=("gray90", "#262b35"), corner_radius=8)
                item.pack(fill="x", padx=10, pady=4)

                icon = ctk.CTkLabel(item, text="📑", font=ctk.CTkFont(size=16))
                icon.pack(side="left", padx=12, pady=8)

                title_lbl = ctk.CTkLabel(item, text=f"{idx}. {chap.title}", font=ctk.CTkFont(size=12, weight="bold"))
                title_lbl.pack(side="left", pady=8)

                pages_lbl = ctk.CTkLabel(
                    item,
                    text=f"{len(chap.pages)} pages",
                    font=ctk.CTkFont(size=11),
                    text_color="gray50"
                )
                pages_lbl.pack(side="right", padx=16, pady=8)

        else:
            lbl = ctk.CTkLabel(
                self.list_scroll,
                text="No folder loaded. Select a source directory on the Dashboard.",
                font=ctk.CTkFont(size=13),
                text_color="gray50"
            )
            lbl.pack(pady=40)
