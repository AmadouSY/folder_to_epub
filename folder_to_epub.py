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


class BookData:
    """Représente un livre complet regroupant ses chapitres, sa couverture et ses métadonnées."""
    def __init__(self, title: str, folder_path: Path, chapters: List[ChapterData], cover_path: Optional[Path] = None):
        self.title = title
        self.folder_path = folder_path
        self.chapters = chapters
        self.cover_path = cover_path
        self.total_images = sum(len(c.pages) for c in chapters)


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


def detect_books(source_dir: Path, force_batch: Optional[bool] = None) -> Tuple[bool, List[BookData]]:
    """
    Analyse un dossier pour déterminer s'il s'agit d'un livre unique ou d'une collection (multi-livres).
    - Si force_batch est True : chaque sous-dossier valide est traité comme un livre indépendant.
    - Si force_batch est False : le dossier entier est traité comme un livre unique.
    - Si force_batch est None (auto) :
        Recherche si les sous-dossiers contiennent eux-mêmes des sous-dossiers avec des images
        (structure à 2 niveaux : Livre / Chapitre / images), ou si plusieurs sous-dossiers ont
        chacun leur propre image de couverture. Si oui, active le mode batch.
    Retourne (is_batch, liste_de_BookData).
    """
    if not source_dir.exists() or not source_dir.is_dir():
        return False, []

    children = [p for p in source_dir.iterdir() if not is_hidden_or_system_file(p)]
    subdirs = natsorted([p for p in children if p.is_dir()], key=lambda p: p.name)
    direct_images = [p for p in children if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]

    is_batch = False
    if force_batch is True:
        is_batch = True
    elif force_batch is False:
        is_batch = False
    else:
        # Détection automatique
        if subdirs and not direct_images:
            has_nested_subdirs = False
            covers_count = 0
            for sd in subdirs:
                sd_children = [p for p in sd.iterdir() if not is_hidden_or_system_file(p)]
                if any(p.is_dir() for p in sd_children):
                    has_nested_subdirs = True
                if find_root_cover(sd):
                    covers_count += 1
            if has_nested_subdirs or covers_count >= 2:
                is_batch = True

    if is_batch and subdirs:
        books: List[BookData] = []
        for sd in subdirs:
            try:
                chaps = collect_chapters_and_images(sd)
                if chaps and sum(len(c.pages) for c in chaps) > 0:
                    cov = find_root_cover(sd)
                    books.append(BookData(title=sd.name, folder_path=sd, chapters=chaps, cover_path=cov))
            except Exception:
                continue
        if books:
            return True, books

    # Mode livre unique (mono ou multi-chapitres)
    try:
        chaps = collect_chapters_and_images(source_dir)
        cov = find_root_cover(source_dir)
        single = BookData(title=source_dir.name, folder_path=source_dir, chapters=chaps, cover_path=cov)
        return False, [single] if (chaps and single.total_images > 0) else []
    except Exception:
        return False, []


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


def create_epub_batch(
    books: List[BookData],
    output_dir: Path,
    author: str = "Inconnu",
    language: str = "fr",
    is_manga: bool = False,
    is_rtl: bool = False,
    progress_callback=None
) -> List[Path]:
    """
    Génère un fichier EPUB pour chaque livre d'une collection en mode batch.
    progress_callback(book_idx, total_books, book, current_page, total_pages_in_book)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_epubs: List[Path] = []
    total_books = len(books)

    for b_idx, book in enumerate(books, start=1):
        out_epub = output_dir / f"{book.title}.epub"

        def on_book_page_progress(curr, tot, chap_title):
            if progress_callback:
                progress_callback(b_idx, total_books, book, curr, tot)

        create_epub(
            chapters=book.chapters,
            output_file=out_epub,
            title=book.title,
            author=author,
            language=language,
            custom_cover_path=book.cover_path,
            source_dir=book.folder_path,
            is_manga=is_manga,
            is_rtl=is_rtl,
            progress_callback=on_book_page_progress
        )
        generated_epubs.append(out_epub)

    return generated_epubs


def main():
    parser = argparse.ArgumentParser(
        description="Convertit un dossier d'images organisé en sous-dossiers de chapitres en un fichier EPUB.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Exemples d'utilisation :
  python folder_to_epub.py ./mon_livre
  python folder_to_epub.py ./manga_folder -o ./manga.epub --title "One Piece Vol 1" --author "Oda" --manga --rtl
  python folder_to_epub.py ./ma_collection --batch -o ./epubs_sortie/
"""
    )
    parser.add_argument("source_dir", nargs="?", type=Path, default=None, help="Chemin vers le dossier source contenant les sous-dossiers de chapitres et les images.")
    parser.add_argument("-g", "--gui", action="store_true", help="Lance l'interface graphique interactive (GUI).")
    parser.add_argument("-b", "--batch", action="store_true", help="Active le mode multi-livres (génère un fichier EPUB pour chaque sous-dossier de livre).")
    parser.add_argument("-o", "--output", type=Path, help="Chemin du fichier EPUB de sortie (ou dossier de sortie en mode batch).")
    parser.add_argument("-t", "--title", type=str, help="Titre du livre numérique (ignoré en mode batch où les noms de sous-dossiers sont utilisés).")
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

    # 1. Analyse et détection : Mode Multi-Livres (Batch) ou Livre Unique
    is_batch, detected_books = detect_books(source_path, force_batch=True if args.batch else None)

    if is_batch and len(detected_books) > 1:
        # MODE MULTI-LIVRES (BATCH)
        out_dir = args.output.resolve() if args.output else source_path.parent / f"{source_path.name}_epubs"
        if out_dir.suffix.lower() == ".epub":
            out_dir = out_dir.parent

        if console:
            console.print(Panel.fit(
                f"[bold cyan]Mode Traitement par Lot (Batch Multi-Livres)[/bold cyan]\n"
                f"[yellow]Dossier Collection :[/yellow] {source_path}\n"
                f"[yellow]Dossier de sortie  :[/yellow] {out_dir}\n"
                f"[yellow]Livres détectés    :[/yellow] {len(detected_books)}\n"
                f"[yellow]Mode Manga/BD      :[/yellow] {'Oui' if args.manga else 'Non'} | [yellow]Sens RTL :[/yellow] {'Oui' if args.rtl else 'Non'}",
                title="Configuration Batch"
            ))

            table = Table(title="Livres à convertir")
            table.add_column("N°", justify="right", style="cyan")
            table.add_column("Titre du livre", style="magenta")
            table.add_column("Chapitres", justify="right", style="blue")
            table.add_column("Pages", justify="right", style="green")
            table.add_column("Couverture", style="yellow")

            for idx, b in enumerate(detected_books, start=1):
                cov_str = b.cover_path.name if b.cover_path else "1ère page"
                table.add_row(str(idx), b.title, str(len(b.chapters)), str(b.total_images), cov_str)
            console.print(table)
            console.print("")

        if RICH_AVAILABLE and console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                overall_task = progress.add_task("[bold cyan]Progression globale des livres...", total=len(detected_books))
                current_book_task = progress.add_task("[bold magenta]Page en cours...", total=1)

                def update_batch_progress(b_idx, total_b, book, curr_p, total_p):
                    progress.update(overall_task, completed=b_idx - 1, description=f"[bold cyan]Livre {b_idx}/{total_b} : {book.title}")
                    progress.update(current_book_task, total=total_p, completed=curr_p, description=f"[bold magenta]{book.title} (p. {curr_p}/{total_p})")

                created_files = create_epub_batch(
                    books=detected_books,
                    output_dir=out_dir,
                    author=args.author,
                    language=args.lang,
                    is_manga=args.manga,
                    is_rtl=args.rtl,
                    progress_callback=update_batch_progress
                )
                progress.update(overall_task, completed=len(detected_books))
        else:
            print(f"Génération de {len(detected_books)} livres EPUB...")
            created_files = create_epub_batch(
                books=detected_books,
                output_dir=out_dir,
                author=args.author,
                language=args.lang,
                is_manga=args.manga,
                is_rtl=args.rtl
            )

        if console:
            console.print(f"\n[bold green]Succès ! {len(created_files)} livres EPUB ont été générés dans :[/bold green]\n[cyan]{out_dir}[/cyan]")
        else:
            print(f"Succès ! {len(created_files)} fichiers EPUB créés dans : {out_dir}")
        return

    # MODE LIVRE UNIQUE
    book_title = args.title or source_path.name
    output_file = args.output or source_path.with_suffix('.epub')

    if console:
        console.print(Panel.fit(
            f"[bold cyan]Générateur EPUB (Livre Unique)[/bold cyan]\n"
            f"[yellow]Source :[/yellow] {source_path}\n"
            f"[yellow]Sortie :[/yellow] {output_file}\n"
            f"[yellow]Titre :[/yellow] {book_title} | [yellow]Auteur :[/yellow] {args.author} | [yellow]Langue :[/yellow] {args.lang}\n"
            f"[yellow]Mode Manga/BD :[/yellow] {'Oui' if args.manga else 'Non'} | [yellow]Sens RTL :[/yellow] {'Oui' if args.rtl else 'Non'}",
            title="Configuration"
        ))

    chapters = collect_chapters_and_images(source_path)
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
