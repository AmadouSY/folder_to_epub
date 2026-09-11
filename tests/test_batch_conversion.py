"""Tests multi-book batch detection and conversion."""

import sys
import unittest
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from folder_to_epub.core.models import ConversionConfig
from folder_to_epub.services.scanner import ScannerService
from folder_to_epub.services.converter import ConversionService
from folder_to_epub.ui.app import FolderToEpubApp


class TestBatchConversion(unittest.TestCase):
    """Tests multi-book collection detection and batch packaging."""

    def test_batch_multi_book_processing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            collection_dir = Path(temp_dir) / "my_collection"
            collection_dir.mkdir()

            # Book 1: Multi-chapter book with root cover
            book1_dir = collection_dir / "One Piece Vol 01"
            book1_dir.mkdir()
            Image.new('RGB', (200, 300), color=(255, 0, 0)).save(book1_dir / "cover.jpg")
            chap1 = book1_dir / "Chapter 01"
            chap1.mkdir()
            Image.new('RGB', (200, 300), color=(0, 255, 0)).save(chap1 / "01.jpg")
            Image.new('RGB', (200, 300), color=(0, 255, 0)).save(chap1 / "02.jpg")
            chap2 = book1_dir / "Chapter 02"
            chap2.mkdir()
            Image.new('RGB', (200, 300), color=(0, 0, 255)).save(chap2 / "01.jpg")

            # Book 2: Flat folder book
            book2_dir = collection_dir / "Naruto Vol 01"
            book2_dir.mkdir()
            Image.new('RGB', (200, 300), color=(255, 255, 0)).save(book2_dir / "00_cover.png")
            Image.new('RGB', (200, 300), color=(255, 128, 0)).save(book2_dir / "page_01.jpg")
            Image.new('RGB', (200, 300), color=(255, 128, 0)).save(book2_dir / "page_02.jpg")

            # 1. Test ScannerService.detect_books
            is_batch, detected_books = ScannerService.detect_books(collection_dir)
            self.assertTrue(is_batch)
            self.assertEqual(len(detected_books), 2)

            book_titles = [b.title for b in detected_books]
            self.assertIn("One Piece Vol 01", book_titles)
            self.assertIn("Naruto Vol 01", book_titles)

            b1 = next(b for b in detected_books if b.title == "One Piece Vol 01")
            b2 = next(b for b in detected_books if b.title == "Naruto Vol 01")
            self.assertIsNotNone(b1.cover_path)
            self.assertEqual(b1.cover_path.name, "cover.jpg")
            self.assertIsNotNone(b2.cover_path)
            self.assertEqual(b2.cover_path.name, "00_cover.png")

            # 2. Test ConversionService.convert_batch
            out_dir = Path(temp_dir) / "output_epubs"
            config = ConversionConfig(
                title="Collection",
                author="Oda & Kishimoto",
                language="en",
                is_manga=True,
                is_rtl=True
            )
            created_epubs = ConversionService.convert_batch(
                books=detected_books,
                output_dir=out_dir,
                base_config=config
            )

            self.assertEqual(len(created_epubs), 2)
            epub1 = out_dir / "One Piece Vol 01.epub"
            epub2 = out_dir / "Naruto Vol 01.epub"
            self.assertTrue(epub1.exists())
            self.assertTrue(epub2.exists())

            # Verify integrity of first EPUB
            with zipfile.ZipFile(epub1, 'r') as z:
                root = ET.fromstring(z.read('EPUB/content.opf'))
                title_el = root.find('.//{*}title')
                self.assertEqual(title_el.text, "One Piece Vol 01")
                cover_item = root.find('.//{*}item[@properties="cover-image"]')
                self.assertIsNotNone(cover_item)
                self.assertIn("cover_cover.jpg", cover_item.attrib['href'])

            # 3. Test GUI batch mode
            app = FolderToEpubApp()
            app.source_dir = collection_dir
            app.source_path_var.set(str(collection_dir))
            app.analyze_source_directory()

            self.assertTrue(app.is_batch_mode)
            self.assertEqual(len(app.books), 2)
            self.assertIn("2 books", app.dashboard_view.source_card.stats_label.cget("text"))
            app.destroy()


if __name__ == "__main__":
    unittest.main()
