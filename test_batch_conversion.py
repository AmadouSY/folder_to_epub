import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

from folder_to_epub import detect_books, create_epub_batch
import gui


def test_batch_multi_book_processing():
    print("=== Test du Traitement par Lot (Batch Multi-Livres) ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        collection_dir = Path(temp_dir) / "ma_collection"
        collection_dir.mkdir()

        # Livre 1 : Structure multi-chapitres avec couverture racine
        book1_dir = collection_dir / "One Piece Vol 01"
        book1_dir.mkdir()
        # Couverture
        c1 = book1_dir / "cover.jpg"
        Image.new('RGB', (200, 300), color=(255, 0, 0)).save(c1)
        # Chapitres
        chap1 = book1_dir / "Chapitre 01"
        chap1.mkdir()
        Image.new('RGB', (200, 300), color=(0, 255, 0)).save(chap1 / "01.jpg")
        Image.new('RGB', (200, 300), color=(0, 255, 0)).save(chap1 / "02.jpg")

        chap2 = book1_dir / "Chapitre 02"
        chap2.mkdir()
        Image.new('RGB', (200, 300), color=(0, 0, 255)).save(chap2 / "01.jpg")

        # Livre 2 : Structure mono-chapitre (dossier plat) avec sa propre couverture
        book2_dir = collection_dir / "Naruto Vol 01"
        book2_dir.mkdir()
        c2 = book2_dir / "00_cover.png"
        Image.new('RGB', (200, 300), color=(255, 255, 0)).save(c2)
        Image.new('RGB', (200, 300), color=(255, 128, 0)).save(book2_dir / "page_01.jpg")
        Image.new('RGB', (200, 300), color=(255, 128, 0)).save(book2_dir / "page_02.jpg")

        # 1. Test de detect_books()
        is_batch, detected_books = detect_books(collection_dir)
        print(f"detect_books() -> is_batch={is_batch}, nb_livres={len(detected_books)}")
        assert is_batch is True, "detect_books() aurait du detecter le mode batch !"
        assert len(detected_books) == 2, f"Attendu 2 livres, obtenu {len(detected_books)}"

        book_titles = [b.title for b in detected_books]
        print(f"Livres detectes : {book_titles}")
        assert "One Piece Vol 01" in book_titles
        assert "Naruto Vol 01" in book_titles

        # Verifier les couvertures de chaque livre
        b1 = next(b for b in detected_books if b.title == "One Piece Vol 01")
        b2 = next(b for b in detected_books if b.title == "Naruto Vol 01")
        assert b1.cover_path is not None and b1.cover_path.name == "cover.jpg"
        assert b2.cover_path is not None and b2.cover_path.name == "00_cover.png"
        print("[OK] Detection automatique des livres et de leurs couvertures respectives valide !")

        # 2. Test de create_epub_batch()
        out_dir = Path(temp_dir) / "output_epubs"
        created_files = create_epub_batch(
            books=detected_books,
            output_dir=out_dir,
            author="Oda & Kishimoto",
            language="fr",
            is_manga=True,
            is_rtl=True
        )

        assert len(created_files) == 2, f"Attendu 2 fichiers EPUB, obtenu {len(created_files)}"
        epub1 = out_dir / "One Piece Vol 01.epub"
        epub2 = out_dir / "Naruto Vol 01.epub"
        assert epub1.exists(), f"{epub1} n'existe pas !"
        assert epub2.exists(), f"{epub2} n'existe pas !"
        print(f"[OK] Fichiers EPUB generes : {[f.name for f in created_files]}")

        # Verifier l'integrite du premier EPUB
        with zipfile.ZipFile(epub1, 'r') as z:
            root = ET.fromstring(z.read('EPUB/content.opf'))
            title_el = root.find('.//{*}title')
            assert title_el.text == "One Piece Vol 01", f"Titre incorrect : {title_el.text}"
            cover_item = root.find('.//{*}item[@properties="cover-image"]')
            assert cover_item is not None and "cover_cover.jpg" in cover_item.attrib['href']
        print("[OK] Archive EPUB 1 valide avec metadonnees et couverture propres !")

        # 3. Test dans l'interface graphique (GUI)
        app = gui.FolderToEpubApp()
        app.source_dir = collection_dir
        app.source_path_var.set(str(collection_dir))
        app._analyze_source_directory()

        assert app.is_batch_mode is True, "Le GUI n'a pas bascule en mode batch !"
        assert len(app.books) == 2, f"Le GUI a trouve {len(app.books)} livres au lieu de 2"
        assert "2 livres" in app.card_source_stats.cget("text")
        print("[OK] Interface graphique : Mode Batch et liste de livres correctement initialises !")
        app.destroy()

    print("\nTOUS LES TESTS BATCH MULTI-LIVRES ONT REUSSI AVEC SUCCES !")


if __name__ == "__main__":
    test_batch_multi_book_processing()
