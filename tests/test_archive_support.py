"""Tests direct archive (.cbz, .zip) support across scanner, converter, and GUI."""

import io
import sys
import unittest
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from folder_to_epub.core.models import ConversionConfig
from folder_to_epub.services.archive import ArchiveService
from folder_to_epub.services.scanner import ScannerService
from folder_to_epub.services.converter import ConversionService
from folder_to_epub.ui.app import FolderToEpubApp


def _create_synthetic_cbz(cbz_path: Path, chapter_images: dict, cover_img: bool = True):
    """Helper to create a realistic .cbz / .zip comic archive."""
    with zipfile.ZipFile(cbz_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        if cover_img:
            img = Image.new('RGB', (300, 450), color=(255, 0, 0))
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            z.writestr('cover.jpg', buf.getvalue())

        for chap, files in chapter_images.items():
            for f in files:
                img = Image.new('RGB', (300, 450), color=(0, 200, 100))
                buf = io.BytesIO()
                img.save(buf, format='JPEG')
                entry_name = f"{chap}/{f}" if chap else f
                z.writestr(entry_name, buf.getvalue())


class TestArchiveSupport(unittest.TestCase):
    """Verifies direct .cbz and .zip archive parsing, cover preview, and conversion."""

    def test_archive_inspection_and_cover_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cbz_file = Path(temp_dir) / "manga_vol_01.cbz"
            _create_synthetic_cbz(
                cbz_file,
                {"Chapter 01": ["01.jpg", "02.jpg"], "Chapter 02": ["01.jpg"]},
                cover_img=True
            )

            self.assertTrue(ArchiveService.is_archive(cbz_file))
            self.assertFalse(ArchiveService.is_archive(Path(temp_dir)))

            count, chapters = ArchiveService.inspect_archive(cbz_file)
            self.assertEqual(count, 4)  # 1 cover + 3 pages
            self.assertIn("Chapter 01", chapters)
            self.assertIn("Chapter 02", chapters)

            cover_info = ArchiveService.get_cover_bytes(cbz_file)
            self.assertIsNotNone(cover_info)
            cov_name, cov_bytes = cover_info
            self.assertEqual(cov_name, "cover.jpg")
            self.assertGreater(len(cov_bytes), 0)

    def test_single_cbz_conversion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cbz_file = Path(temp_dir) / "Solo_Leveling_Vol_01.cbz"
            _create_synthetic_cbz(
                cbz_file,
                {"Chapter 01": ["01.jpg", "02.jpg"], "Chapter 02": ["01.jpg"]},
                cover_img=True
            )

            # Scanner detection
            is_batch, books = ScannerService.detect_books(cbz_file)
            self.assertFalse(is_batch)
            self.assertEqual(len(books), 1)
            book = books[0]
            self.assertTrue(book.is_archive)
            self.assertEqual(book.title, "Solo_Leveling_Vol_01")
            self.assertEqual(book.total_images, 4)

            # Conversion
            out_epub = Path(temp_dir) / "Solo_Leveling_Vol_01.epub"
            config = ConversionConfig(
                title="Solo Leveling Vol 01",
                author="Chugong",
                language="en",
                output_path=out_epub,
                is_manga=True,
                is_rtl=True
            )
            created = ConversionService.convert_book(book=book, config=config)
            self.assertTrue(out_epub.exists())
            self.assertEqual(created, out_epub)

            # Check inside generated EPUB
            with zipfile.ZipFile(out_epub, 'r') as z:
                manifest = z.namelist()
                self.assertTrue(any('cover_cover.jpg' in n for n in manifest))
                root = ET.fromstring(z.read('EPUB/content.opf'))
                title_el = root.find('.//{*}title')
                self.assertEqual(title_el.text, "Solo Leveling Vol 01")

    def test_batch_archive_collection_conversion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            collection_dir = Path(temp_dir) / "manga_archives"
            collection_dir.mkdir()

            arc1 = collection_dir / "Berserk_Vol_01.cbz"
            arc2 = collection_dir / "Berserk_Vol_02.zip"

            _create_synthetic_cbz(arc1, {"Ch 01": ["1.jpg", "2.jpg"]})
            _create_synthetic_cbz(arc2, {"Ch 02": ["1.jpg", "2.jpg", "3.jpg"]})

            # Detect collection
            is_batch, books = ScannerService.detect_books(collection_dir)
            self.assertTrue(is_batch)
            self.assertEqual(len(books), 2)
            titles = [b.title for b in books]
            self.assertIn("Berserk_Vol_01", titles)
            self.assertIn("Berserk_Vol_02", titles)

            # Convert batch
            out_dir = Path(temp_dir) / "output_epubs"
            config = ConversionConfig(
                title="Berserk Collection",
                author="Kentaro Miura",
                language="en",
                is_manga=True,
                is_rtl=True
            )
            created_files = ConversionService.convert_batch(
                books=books,
                output_dir=out_dir,
                base_config=config
            )
            self.assertEqual(len(created_files), 2)
            self.assertTrue((out_dir / "Berserk_Vol_01.epub").exists())
            self.assertTrue((out_dir / "Berserk_Vol_02.epub").exists())

    def test_gui_with_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cbz_file = Path(temp_dir) / "One_Piece_Vol_01.cbz"
            _create_synthetic_cbz(cbz_file, {"Chapitre 01": ["01.jpg", "02.jpg"]})

            app = FolderToEpubApp()
            app.source_dir = cbz_file
            app.source_path_var.set(str(cbz_file))
            app.analyze_source_directory()

            self.assertFalse(app.is_batch_mode)
            self.assertEqual(len(app.books), 1)
            self.assertTrue(app.books[0].is_archive)
            self.assertIsNotNone(app.cover_thumbnail_image)
            self.assertIn("One_Piece_Vol_01", app.title_var.get())
            app.destroy()


if __name__ == "__main__":
    unittest.main()
