"""Tests natural alphanumeric sorting order for chapters, image files, TOC, and spine."""

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
from folder_to_epub.services.builder import EpubBuilder


class TestNaturalSorting(unittest.TestCase):
    """Verifies natural alphanumeric sorting across chapters, images, and EPUB spine."""

    def test_natural_sorting_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "manga_test_sort"
            base_dir.mkdir()

            chapter_names = [
                "Chapter 100",
                "Chapter 2",
                "Chapter 20",
                "Chapter 1",
                "Chapter 10"
            ]
            expected_chapter_order = [
                "Chapter 1",
                "Chapter 2",
                "Chapter 10",
                "Chapter 20",
                "Chapter 100"
            ]
            image_names = ["10.jpg", "1.jpg", "2.jpg", "20.jpg", "100.jpg"]
            expected_image_order = ["1.jpg", "2.jpg", "10.jpg", "20.jpg", "100.jpg"]

            for chap in chapter_names:
                chap_path = base_dir / chap
                chap_path.mkdir()
                for img_name in image_names:
                    img_path = chap_path / img_name
                    img = Image.new('RGB', (100, 100), color=(200, 100, 50))
                    img.save(img_path)

            chapters = ScannerService.scan_chapters(base_dir)

            extracted_chapter_titles = [c.title for c in chapters]
            self.assertEqual(extracted_chapter_titles, expected_chapter_order)

            for chap in chapters:
                extracted_images = [p.file_path.name for p in chap.pages]
                self.assertEqual(extracted_images, expected_image_order)

            output_epub = Path(temp_dir) / "test_sort.epub"
            book = Book(
                title="Test Natural Sorting",
                folder_path=base_dir,
                chapters=chapters
            )
            config = ConversionConfig(
                title="Test Natural Sorting",
                author="Tester",
                output_path=output_epub
            )
            builder = EpubBuilder(book=book, config=config)
            builder.build()

            self.assertTrue(output_epub.exists())

            with zipfile.ZipFile(output_epub, 'r') as z:
                container_xml = z.read('META-INF/container.xml')
                root = ET.fromstring(container_xml)
                opf_path = root.find('.//{*}rootfile').attrib['full-path']
                opf_xml = z.read(opf_path)
                opf_root = ET.fromstring(opf_xml)

                manifest_items = {
                    item.attrib['id']: item.attrib['href']
                    for item in opf_root.findall('.//{*}item')
                }
                spine_itemrefs = [
                    itemref.attrib['idref']
                    for itemref in opf_root.findall('.//{*}itemref')
                ]
                spine_files = [manifest_items[idref] for idref in spine_itemrefs if idref in manifest_items]

                expected_spine = ["nav.xhtml"] + [f"pages/page_{i:04d}.xhtml" for i in range(1, 26)]
                self.assertEqual(spine_files, expected_spine)

                nav_content = z.read('EPUB/nav.xhtml').decode('utf-8')
                for idx in range(len(expected_chapter_order) - 1):
                    c1 = expected_chapter_order[idx]
                    c2 = expected_chapter_order[idx + 1]
                    pos1 = nav_content.find(c1)
                    pos2 = nav_content.find(c2)
                    self.assertNotEqual(pos1, -1)
                    self.assertNotEqual(pos2, -1)
                    self.assertLess(pos1, pos2)


if __name__ == "__main__":
    unittest.main()
