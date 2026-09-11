import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

from folder_to_epub import detect_books, create_epub_batch
import gui


def test_batch_multi_book_processing():
    print("=== Test Batch Multi-Book Processing ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        collection_dir = Path(temp_dir) / "my_collection"
        collection_dir.mkdir()

        # Book 1: Multi-chapter structure with root cover
        book1_dir = collection_dir / "One Piece Vol 01"
        book1_dir.mkdir()
        # Cover
        c1 = book1_dir / "cover.jpg"
        Image.new('RGB', (200, 300), color=(255, 0, 0)).save(c1)
        # Chapters
        chap1 = book1_dir / "Chapter 01"
        chap1.mkdir()
        Image.new('RGB', (200, 300), color=(0, 255, 0)).save(chap1 / "01.jpg")
        Image.new('RGB', (200, 300), color=(0, 255, 0)).save(chap1 / "02.jpg")

        chap2 = book1_dir / "Chapter 02"
        chap2.mkdir()
        Image.new('RGB', (200, 300), color=(0, 0, 255)).save(chap2 / "01.jpg")

        # Book 2: Single-chapter (flat folder) structure with own cover
        book2_dir = collection_dir / "Naruto Vol 01"
        book2_dir.mkdir()
        c2 = book2_dir / "00_cover.png"
        Image.new('RGB', (200, 300), color=(255, 255, 0)).save(c2)
        Image.new('RGB', (200, 300), color=(255, 128, 0)).save(book2_dir / "page_01.jpg")
        Image.new('RGB', (200, 300), color=(255, 128, 0)).save(book2_dir / "page_02.jpg")

        # 1. Test detect_books()
        is_batch, detected_books = detect_books(collection_dir)
        print(f"detect_books() -> is_batch={is_batch}, book_count={len(detected_books)}")
        assert is_batch is True, "detect_books() should have detected batch mode!"
        assert len(detected_books) == 2, f"Expected 2 books, got {len(detected_books)}"

        book_titles = [b.title for b in detected_books]
        print(f"Detected books: {book_titles}")
        assert "One Piece Vol 01" in book_titles
        assert "Naruto Vol 01" in book_titles

        # Verify covers for each book
        b1 = next(b for b in detected_books if b.title == "One Piece Vol 01")
        b2 = next(b for b in detected_books if b.title == "Naruto Vol 01")
        assert b1.cover_path is not None and b1.cover_path.name == "cover.jpg"
        assert b2.cover_path is not None and b2.cover_path.name == "00_cover.png"
        print("[OK] Automatic detection of books and their respective covers valid!")

        # 2. Test create_epub_batch()
        out_dir = Path(temp_dir) / "output_epubs"
        created_files = create_epub_batch(
            books=detected_books,
            output_dir=out_dir,
            author="Oda & Kishimoto",
            language="en",
            is_manga=True,
            is_rtl=True
        )

        assert len(created_files) == 2, f"Expected 2 EPUB files, got {len(created_files)}"
        epub1 = out_dir / "One Piece Vol 01.epub"
        epub2 = out_dir / "Naruto Vol 01.epub"
        assert epub1.exists(), f"{epub1} does not exist!"
        assert epub2.exists(), f"{epub2} does not exist!"
        print(f"[OK] Generated EPUB files: {[f.name for f in created_files]}")

        # Verify integrity of first EPUB
        with zipfile.ZipFile(epub1, 'r') as z:
            root = ET.fromstring(z.read('EPUB/content.opf'))
            title_el = root.find('.//{*}title')
            assert title_el.text == "One Piece Vol 01", f"Incorrect title: {title_el.text}"
            cover_item = root.find('.//{*}item[@properties="cover-image"]')
            assert cover_item is not None and "cover_cover.jpg" in cover_item.attrib['href']
        print("[OK] EPUB archive 1 valid with proper metadata and cover!")

        # 3. Test in GUI
        app = gui.FolderToEpubApp()
        app.source_dir = collection_dir
        app.source_path_var.set(str(collection_dir))
        app._analyze_source_directory()

        assert app.is_batch_mode is True, "GUI did not switch to batch mode!"
        assert len(app.books) == 2, f"GUI found {len(app.books)} books instead of 2"
        assert "2 books" in app.card_source_stats.cget("text")
        print("[OK] GUI: Batch mode and book list correctly initialized!")
        app.destroy()

    print("\nALL BATCH MULTI-BOOK TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_batch_multi_book_processing()
