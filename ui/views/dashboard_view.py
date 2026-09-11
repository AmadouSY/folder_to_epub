"""Dashboard view presenting the primary modular workspace."""

import customtkinter as ctk
from typing import TYPE_CHECKING
from ui.components.hero_header import HeroHeaderComponent
from ui.components.action_banner import ActionBannerComponent
from ui.components.cards import (
    SourceCard,
    CoverCard,
    MetadataCard,
    LayoutCard,
    DestinationCard,
    StatusCard
)
from core.constants import AVAILABLE_LANGUAGES

if TYPE_CHECKING:
    from ui.app import FolderToEpubApp


class DashboardView(ctk.CTkScrollableFrame):
    """Primary dashboard screen container with hero, action banner, and cards."""

    def __init__(self, parent: ctk.CTkFrame, app: 'FolderToEpubApp'):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        # 1. Hero header component
        self.hero = HeroHeaderComponent(self)

        # 2. Action banner component
        self.action_banner = ActionBannerComponent(
            self,
            batch_var=app.batch_switch_var,
            on_batch_toggle=app.on_batch_toggle,
            on_convert_click=app.on_convert_click
        )

        # 3. 2-Column Cards Grid
        self.cards_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.cards_grid.grid_columnconfigure(0, weight=1)
        self.cards_grid.grid_columnconfigure(1, weight=1)

        # Card 1: Source
        self.source_card = SourceCard(
            self.cards_grid,
            path_var=app.source_path_var,
            on_browse=app.on_browse_source,
            height=140
        )
        self.source_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 16), sticky="nsew")

        # Card 2: Cover
        self.cover_card = CoverCard(
            self.cards_grid,
            on_choose_cover=app.on_choose_cover,
            on_reset_cover=app.on_reset_cover,
            height=140
        )
        self.cover_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 16), sticky="nsew")

        # Card 3: Metadata
        self.metadata_card = MetadataCard(
            self.cards_grid,
            title_var=app.title_var,
            author_var=app.author_var,
            lang_var=app.lang_var,
            lang_options=AVAILABLE_LANGUAGES,
            height=180
        )
        self.metadata_card.grid(row=1, column=0, padx=(0, 8), pady=(0, 16), sticky="nsew")

        # Card 4: Layout & Direction
        self.layout_card = LayoutCard(
            self.cards_grid,
            manga_var=app.manga_mode_var,
            rtl_var=app.rtl_mode_var,
            on_manga_toggle=app.on_manga_toggle,
            height=180
        )
        self.layout_card.grid(row=1, column=1, padx=(8, 0), pady=(0, 16), sticky="nsew")

        # Card 5: EPUB Destination
        self.destination_card = DestinationCard(
            self.cards_grid,
            path_var=app.output_path_var,
            on_browse_output=app.on_browse_output,
            on_open_epub=app.on_open_epub,
            on_open_folder=app.on_open_folder,
            height=140
        )
        self.destination_card.grid(row=2, column=0, padx=(0, 8), pady=(0, 16), sticky="nsew")

        # Card 6: Status & Activity
        self.status_card = StatusCard(
            self.cards_grid,
            on_view_logs=lambda: app.show_view("logs"),
            height=140
        )
        self.status_card.grid(row=2, column=1, padx=(8, 0), pady=(0, 16), sticky="nsew")
