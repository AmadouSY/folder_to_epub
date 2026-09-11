#!/usr/bin/env python3
"""
Folder to EPUB Converter (CLI)
==============================
Un outil CLI Python permettant de convertir une arborescence de dossiers contenant des images
en un livre numérique EPUB propre, structuré et optimisé pour liseuses (Kindle, Kobo, Bookeen, Apple Books, etc.).

Structure source attendue :
--------------------------
dossier_source/
├── Chapitre 01/
│   ├── 01.jpg
│   ├── 02.jpg
│   └── 03.jpg
└── Chapitre 02/
    ├── 01.jpg
    └── 02.jpg

Exemple d'utilisation :
-----------------------
$ python folder_to_epub.py ./mon_livre -o ./mon_livre.epub --title "Mon Super Manga" --author "Auteur" --lang fr
$ python folder_to_epub.py ./mon_livre --manga --rtl
"""

import argparse
import sys
import uuid
import mimetypes
from pathlib import Path
from typing import List, Tuple, Optional, Dict

try:
    from PIL import Image
except ImportError:
    sys.exit("Erreur : La bibliothèque 'Pillow' est requise. Installez-la avec 'pip install Pillow'.")

try:
    from natsort import natsorted
except ImportError:
    sys.exit("Erreur : La bibliothèque 'natsort' est requise. Installez-la avec 'pip install natsort'.")

try:
    import ebooklib
    from ebooklib import epub
except ImportError:
    sys.exit("Erreur : La bibliothèque 'EbookLib' est requise. Installez-la avec 'pip install EbookLib'.")

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Formats d'images supportés
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

# Feuille de style CSS par défaut épurée et responsive
DEFAULT_CSS = """@page {
    margin: 0;
    padding: 0;
}
html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    text-align: center;
    background-color: #ffffff;
}
div.page-container {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
}
img.page-image {
    max-width: 100%;
    max-height: 100%;
    height: auto;
    width: auto;
    object-fit: contain;
    display: block;
    margin: 0 auto;
}
"""


class ImagePage:
    """Représente une page image avec ses métadonnées."""
    def __init__(self, file_path: Path, chapter_title: str, page_index: int):
        self.file_path = file_path
        self.chapter_title = chapter_title
        self.page_index = page_index
        self.width: int = 0
        self.height: int = 0
        self.mime_type: str = "image/jpeg"
        self.is_valid: bool = False
        self._inspect_image()

    def _inspect_image(self):
        """Valide l'image avec Pillow et extrait ses dimensions et son type MIME."""
        ext = self.file_path.suffix.lower()
        if ext in ('.jpg', '.jpeg'):
            self.mime_type = 'image/jpeg'
        elif ext == '.png':
            self.mime_type = 'image/png'
        elif ext == '.webp':
            self.mime_type = 'image/webp'
        elif ext == '.gif':
            self.mime_type = 'image/gif'
        elif ext == '.bmp':
            self.mime_type = 'image/bmp'
        else:
            self.mime_type = mimetypes.guess_type(self.file_path)[0] or 'image/jpeg'

        try:
            with Image.open(self.file_path) as img:
                img.verify()
            # Réouverture après verify() pour lire la taille
            with Image.open(self.file_path) as img:
                self.width, self.height = img.size
                self.is_valid = True
        except Exception:
            self.is_valid = False


class ChapterData:
    """Représente un chapitre regroupant ses images."""
    def __init__(self, title: str, folder_path: Optional[Path] = None):
        self.title = title
        self.folder_path = folder_path
        self.pages: List[ImagePage] = []


def is_hidden_or_system_file(path: Path) -> bool:
    """Vérifie si un fichier ou dossier est caché (ex: .DS_Store, Thumbs.db, .git)."""
    name = path.name
    if name.startswith('.') or name.startswith('~$'):
        return True
    if name.lower() in ('thumbs.db', 'desktop.ini', 'ehthumbs.db'):
        return True
    return False


def collect_chapters_and_images(source_dir: Path) -> List[ChapterData]:
    """
    Parcourt le dossier source et extrait les chapitres et leurs images triés naturellement.
    Prend en charge à la fois :
    1. La structure sous-dossiers = chapitres
    2. Un dossier plat avec directement des images (= 1 chapitre unique)
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"Le dossier source '{source_dir}' n'existe pas.")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"Le chemin source '{source_dir}' n'est pas un dossier.")

    chapters: List[ChapterData] = []

    # Lister les éléments du dossier source avec natsort
    children = [p for p in source_dir.iterdir() if not is_hidden_or_system_file(p)]
    subdirs = natsorted([p for p in children if p.is_dir()], key=lambda p: p.name)
    direct_images = natsorted([p for p in children if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS], key=lambda p: p.name)

    if subdirs:
        # Structure multi-chapitres
        for subdir in subdirs:
            chapter = ChapterData(title=subdir.name, folder_path=subdir)
            image_files = natsorted(
                [p for p in subdir.iterdir() if p.is_file() and not is_hidden_or_system_file(p) and p.suffix.lower() in SUPPORTED_EXTENSIONS],
                key=lambda p: p.name
            )
            for idx, img_path in enumerate(image_files, start=1):
                page = ImagePage(img_path, chapter_title=subdir.name, page_index=idx)
                if page.is_valid:
                    chapter.pages.append(page)
            
            if chapter.pages:
                chapters.append(chapter)

    elif direct_images:
        # Structure mono-chapitre (images directement à la racine)
        chapter = ChapterData(title=source_dir.name, folder_path=source_dir)
        for idx, img_path in enumerate(direct_images, start=1):
            page = ImagePage(img_path, chapter_title=source_dir.name, page_index=idx)
            if page.is_valid:
                chapter.pages.append(page)
        if chapter.pages:
            chapters.append(chapter)

    return chapters


def find_root_cover(source_dir: Path) -> Optional[Path]:
    """
    Recherche à la racine du dossier source une image valide contenant 'cover' dans son nom (insensible à la casse).
    Exemples : cover.jpg, Cover.png, 00_cover.webp, etc.
    Retourne le chemin Path du premier fichier trouvé (trié naturellement), ou None.
    """
    if not source_dir or not source_dir.exists() or not source_dir.is_dir():
        return None

    candidates = []
    for p in source_dir.iterdir():
        if p.is_file() and not is_hidden_or_system_file(p) and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            stem_lower = p.stem.lower()
            if 'cover' in stem_lower or 'couverture' in stem_lower:
                candidates.append(p)

    if candidates:
        return natsorted(candidates, key=lambda p: p.name)[0]
    return None


def create_epub(
    chapters: List[ChapterData],
    output_file: Path,
    title: str,
    author: str,
    language: str = "fr",
    custom_cover_path: Optional[Path] = None,
    source_dir: Optional[Path] = None,
    is_manga: bool = False,
    is_rtl: bool = False,
    progress_callback=None
) -> Path:
    """Génère le fichier EPUB à partir des chapitres et des images."""

    book = epub.EpubBook()
    book.set_identifier(f"urn:uuid:{uuid.uuid4()}")
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    # Sens de lecture et métadonnées Manga / Fixed-Layout si activé
    if is_manga or is_rtl:
        book.set_direction('rtl')
        # Métadonnées Fixed-Layout standard EPUB 3
        book.add_metadata(None, 'meta', 'pre-paginated', {'property': 'rendition:layout'})
        book.add_metadata(None, 'meta', 'auto', {'property': 'rendition:orientation'})
        book.add_metadata(None, 'meta', 'auto', {'property': 'rendition:spread'})
        book.add_metadata(None, 'meta', 'comic', {'property': 'book-type'})
        book.add_metadata(None, 'meta', 'true', {'property': 'zero-gutter'})
        book.add_metadata(None, 'meta', 'true', {'property': 'zero-margin'})

    # Ajout du fichier CSS
    style_item = epub.EpubItem(
        uid="style_css",
        file_name="style/style.css",
        media_type="text/css",
        content=DEFAULT_CSS.encode('utf-8')
    )
    book.add_item(style_item)

    # Gestion de l'image de couverture
    cover_page: Optional[ImagePage] = None
    if custom_cover_path and custom_cover_path.exists():
        cover_page = ImagePage(custom_cover_path, "Couverture", 0)
    else:
        # Recherche par défaut : image à la racine du dossier contenant 'cover' dans le nom
        root_cover = None
        if source_dir:
            root_cover = find_root_cover(source_dir)
        elif chapters and chapters[0].folder_path:
            # Recherche dans le dossier parent (si sous-dossiers) ou dans le dossier du chapitre
            parent_dir = chapters[0].folder_path.parent
            root_cover = find_root_cover(parent_dir) or find_root_cover(chapters[0].folder_path)

        if root_cover and root_cover.exists():
            cover_page = ImagePage(root_cover, "Couverture", 0)
        elif chapters and chapters[0].pages:
            cover_page = chapters[0].pages[0]

    if cover_page and cover_page.is_valid:
        with open(cover_page.file_path, 'rb') as f:
            cover_data = f.read()
        book.set_cover(f"cover_{cover_page.file_path.name}", cover_data)

    spine_items = ['nav']
    toc_items = []
    total_pages_count = sum(len(c.pages) for c in chapters)
    processed_pages = 0

    img_counter = 1
    page_counter = 1

    for chap_idx, chapter in enumerate(chapters, start=1):
        chapter_xhtml_pages = []

        for page in chapter.pages:
            img_ext = page.file_path.suffix.lower()
            img_filename = f"images/img_{img_counter:04d}{img_ext}"
            
            # 1. Ajouter la ressource image dans l'EPUB
            with open(page.file_path, 'rb') as f:
                img_data = f.read()

            img_item = epub.EpubItem(
                uid=f"img_{img_counter:04d}",
                file_name=img_filename,
                media_type=page.mime_type,
                content=img_data
            )
            book.add_item(img_item)

            # 2. Créer la page XHTML associée
            page_filename = f"pages/page_{page_counter:04d}.xhtml"
            page_title = f"{chapter.title} - Page {page.page_index}"

            # Chemin relatif de l'image par rapport au fichier XHTML (pages/ -> images/)
            rel_img_path = f"../{img_filename}"
            rel_css_path = "../style/style.css"

            viewport_meta = f'<meta name="viewport" content="width={page.width}, height={page.height}" />' if page.width and page.height else ''

            xhtml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{language}">
<head>
    <meta charset="utf-8" />
    <title>{page_title}</title>
    {viewport_meta}
    <link rel="stylesheet" type="text/css" href="{rel_css_path}" />
</head>
<body>
    <div class="page-container">
        <img class="page-image" src="{rel_img_path}" alt="{page_title}" />
    </div>
</body>
</html>
"""
            xhtml_item = epub.EpubHtml(
                title=page_title,
                file_name=page_filename,
                lang=language,
                uid=f"page_{page_counter:04d}"
            )
            xhtml_item.set_content(xhtml_content.encode('utf-8'))
            xhtml_item.add_item(style_item)
            book.add_item(xhtml_item)

            chapter_xhtml_pages.append(xhtml_item)
            spine_items.append(xhtml_item)

            img_counter += 1
            page_counter += 1
            processed_pages += 1

            if progress_callback:
                progress_callback(processed_pages, total_pages_count, chapter.title)

        # Ajouter le chapitre à la Table des Matières (pointant vers sa première page)
        if chapter_xhtml_pages:
            toc_link = epub.Link(
                href=chapter_xhtml_pages[0].file_name,
                title=chapter.title,
                uid=f"toc_chap_{chap_idx:03d}"
            )
            toc_items.append(toc_link)

    book.toc = toc_items
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine_items

    # Écriture du fichier final
    output_file.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_file), book, {})
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Convertit un dossier d'images organisé en sous-dossiers de chapitres en un fichier EPUB.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Exemples d'utilisation :
  python folder_to_epub.py ./mon_livre
  python folder_to_epub.py ./manga_folder -o ./manga.epub --title "One Piece Vol 1" --author "Oda" --manga --rtl
"""
    )
    parser.add_argument("source_dir", nargs="?", type=Path, default=None, help="Chemin vers le dossier source contenant les sous-dossiers de chapitres et les images.")
    parser.add_argument("-g", "--gui", action="store_true", help="Lance l'interface graphique interactive (GUI).")
    parser.add_argument("-o", "--output", type=Path, help="Chemin du fichier EPUB de sortie (par défaut : <nom_du_dossier>.epub).")
    parser.add_argument("-t", "--title", type=str, help="Titre du livre numérique (par défaut : nom du dossier source).")
    parser.add_argument("-a", "--author", type=str, default="Inconnu", help="Auteur du livre (par défaut : 'Inconnu').")
    parser.add_argument("-l", "--lang", type=str, default="fr", help="Code langue du livre (par défaut : 'fr').")
    parser.add_argument("-c", "--cover", type=Path, help="Chemin optionnel vers une image de couverture personnalisée.")
    parser.add_argument("--manga", action="store_true", help="Active le formatage Fixed-Layout optimisé pour Mangas et BD.")
    parser.add_argument("--rtl", action="store_true", help="Définit le sens de lecture de droite à gauche (Right-To-Left).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Affiche les détails d'exécution.")

    args = parser.parse_args()

    # Si le mode GUI est demandé ou si aucun argument n'est fourni
    if args.gui or args.source_dir is None:
        try:
            from gui import main as launch_gui
            launch_gui()
            return
        except ImportError as e:
            print(f"Erreur : Impossible de charger l'interface graphique ({e}). Installez 'customtkinter'.", file=sys.stderr)
            if args.source_dir is None:
                parser.print_help()
                sys.exit(1)

    console = Console() if RICH_AVAILABLE else None

    source_path = args.source_dir.resolve()
    if not source_path.exists() or not source_path.is_dir():
        msg = f"Erreur : Le dossier source '{source_path}' n'existe pas ou n'est pas un répertoire valide."
        if console:
            console.print(f"[bold red]{msg}[/bold red]")
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    book_title = args.title or source_path.name
    output_file = args.output or source_path.with_suffix('.epub')

    if console:
        console.print(Panel.fit(
            f"[bold cyan]Générateur EPUB à partir de dossiers d'images[/bold cyan]\n"
            f"[yellow]Source :[/yellow] {source_path}\n"
            f"[yellow]Sortie :[/yellow] {output_file}\n"
            f"[yellow]Titre :[/yellow] {book_title} | [yellow]Auteur :[/yellow] {args.author} | [yellow]Langue :[/yellow] {args.lang}\n"
            f"[yellow]Mode Manga/BD :[/yellow] {'Oui' if args.manga else 'Non'} | [yellow]Sens RTL :[/yellow] {'Oui' if args.rtl else 'Non'}",
            title="Configuration"
        ))

    # 1. Collecte et analyse des dossiers et images
    try:
        chapters = collect_chapters_and_images(source_path)
    except Exception as e:
        if console:
            console.print(f"[bold red]Erreur lors de la lecture des dossiers : {e}[/bold red]")
        else:
            print(f"Erreur lors de la lecture des dossiers : {e}", file=sys.stderr)
        sys.exit(1)

    if not chapters:
        msg = "Erreur : Aucune image valide n'a été trouvée dans le dossier source ou ses sous-dossiers."
        if console:
            console.print(f"[bold red]{msg}[/bold red]")
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    total_images = sum(len(c.pages) for c in chapters)

    if console:
        table = Table(title="Chapitres détectés")
        table.add_column("Index", justify="right", style="cyan")
        table.add_column("Nom du chapitre", style="magenta")
        table.add_column("Nombre de pages", justify="right", style="green")

        for idx, chap in enumerate(chapters, start=1):
            table.add_row(str(idx), chap.title, str(len(chap.pages)))
        
        console.print(table)
        console.print(f"[bold green]Total : {len(chapters)} chapitre(s), {total_images} page(s) image(s).[/bold green]\n")

    # Détection automatique d'une couverture à la racine si non spécifiée
    cover_to_use = args.cover
    if not cover_to_use:
        auto_cover = find_root_cover(source_path)
        if auto_cover:
            cover_to_use = auto_cover
            if console:
                console.print(f"[bold cyan]ℹ Couverture racine détectée :[/bold cyan] [yellow]{auto_cover.name}[/yellow]")
            else:
                print(f"ℹ Couverture racine détectée : {auto_cover.name}")

    # 2. Génération de l'EPUB
    if RICH_AVAILABLE and console:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[bold cyan]Génération de l'EPUB...", total=total_images)

            def update_progress(current, total, current_chap):
                progress.update(task, completed=current, description=f"[bold cyan]Traitement : {current_chap}")

            final_epub = create_epub(
                chapters=chapters,
                output_file=output_file,
                title=book_title,
                author=args.author,
                language=args.lang,
                custom_cover_path=cover_to_use,
                source_dir=source_path,
                is_manga=args.manga,
                is_rtl=args.rtl,
                progress_callback=update_progress
            )
    else:
        print(f"Génération de l'EPUB pour {total_images} pages...")
        final_epub = create_epub(
            chapters=chapters,
            output_file=output_file,
            title=book_title,
            author=args.author,
            language=args.lang,
            custom_cover_path=cover_to_use,
            source_dir=source_path,
            is_manga=args.manga,
            is_rtl=args.rtl
        )

    if console:
        console.print(f"\n[bold green]Succès ! Le fichier EPUB a été généré avec succès :[/bold green]\n[cyan]{final_epub.resolve()}[/cyan]")
    else:
        print(f"Succès ! Fichier EPUB créé : {final_epub.resolve()}")


if __name__ == "__main__":
    main()
