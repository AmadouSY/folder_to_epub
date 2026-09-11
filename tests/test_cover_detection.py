"""Tests root cover auto-detection in ScannerService, EpubBuilder, and GUI."""

import sys
import unittest
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from folder_to_epub.core.models import Book, ConversionConfig
from folder_to_epub.services.scanner import ScannerService
from folder_to_epub.services.converter import ConversionService
from folder_to_epub.ui.app import FolderToEpubApp


class TestCoverDetection(unittest.TestCase):
    """Tests automatic discovery of root cover image."""

    def test_root_cover_auto_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "test_book_with_cover"
            base_dir.mkdir()

            # 1. Root cover image
            root_cover = base_dir / "cover.jpg"
            Image.new('RGB', (400, 600), color=(255, 0, 0)).save(root_cover)

            # 2. Chapters
            chap1 = base_dir / "Chapter 01"
            chap1.mkdir()
            Image.new('RGB', (400, 600), color=(0, 255, 0)).save(chap1 / "01.jpg")

            chap2 = base_dir / "Chapter 02"
            chap2.mkdir()
            Image.new('RGB', (400, 600), color=(0, 0, 255)).save(chap2 / "01.jpg")

            # Test 1: ScannerService.find_cover
            detected = ScannerService.find_cover(base_dir)
            self.assertIsNotNone(detected)
            self.assertEqual(detected.name, "cover.jpg")

            # Test 2: ConversionService.convert_book
            book = ScannerService.scan_book(base_dir)
            self.assertIsNotNone(book)
            self.assertIsNotNone(book.cover_path)
            self.assertEqual(book.cover_path.name, "cover.jpg")

            output_epub = Path(temp_dir) / "output.epub"
            config = ConversionConfig(
                title="Book with Root Cover",
                author="Author",
                output_path=output_epub
            )
            ConversionService.convert_book(book=book, config=config)
            self.assertTrue(output_epub.exists())

            with zipfile.ZipFile(output_epub, 'r') as z:
                namelist = z.namelist()
                self.assertTrue(any('cover_cover.jpg' in n for n in namelist))

                root = ET.fromstring(z.read('EPUB/content.opf'))
                cover_item = root.find('.//{*}item[@properties="cover-image"]')
                self.assertIsNotNone(cover_item)
                self.assertIn("cover_cover.jpg", cover_item.attrib['href'])

            # Test 3: GUI State & Thumbnail
            app = FolderToEpubApp()
            app.source_dir = base_dir
            app.source_path_var.set(str(base_dir))
            app.analyze_source_directory()

            self.assertIsNotNone(app.auto_root_cover)
            self.assertEqual(app.auto_root_cover.name, "cover.jpg")
            self.assertIsNotNone(app.cover_thumbnail_image)
            app.destroy()


if __name__ == "__main__":
    unittest.main()
