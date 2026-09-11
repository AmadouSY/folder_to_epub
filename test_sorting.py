import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from folder_to_epub import collect_chapters_and_images, create_epub


def test_natural_sorting_order():
    """
    Rigorously tests natural sorting order of subdirectories (chapters)
    and image files to ensure that 'Chapter 2' comes before 'Chapter 10',
    and 'page 2.jpg' comes before 'page 10.jpg'.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "manga_test_sort"
        base_dir.mkdir()

        # Folders in unordered sequence with 1, 2, and 3 digit numbers (without leading zeroes).
        # In pure alphabetical sorting (ASCII/lexicographical), the order would be:
        # Chapter 1, Chapter 10, Chapter 100, Chapter 2, Chapter 20
        # In natural sorting (natsort), the expected order is:
        # Chapter 1, Chapter 2, Chapter 10, Chapter 20, Chapter 100
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

        # Image files inside each chapter
        image_names = ["10.jpg", "1.jpg", "2.jpg", "20.jpg", "100.jpg"]
        expected_image_order = ["1.jpg", "2.jpg", "10.jpg", "20.jpg", "100.jpg"]

        for chap in chapter_names:
            chap_path = base_dir / chap
            chap_path.mkdir()
            for img_name in image_names:
                img_path = chap_path / img_name
                # Create a small valid image
                img = Image.new('RGB', (100, 100), color=(200, 100, 50))
                img.save(img_path)

        print("1. Testing collect_chapters_and_images()...")
        chapters = collect_chapters_and_images(base_dir)

        # Verify chapter order
        extracted_chapter_titles = [c.title for c in chapters]
        print(f"Extracted chapter order: {extracted_chapter_titles}")
        assert extracted_chapter_titles == expected_chapter_order, (
            f"Chapter sorting failed!\nGot     : {extracted_chapter_titles}\nExpected: {expected_chapter_order}"
        )
        print("[OK] Subdirectory (chapter) natural order valid!")

        # Verify image order in each chapter
        for chap in chapters:
            extracted_images = [p.file_path.name for p in chap.pages]
            assert extracted_images == expected_image_order, (
                f"Image sorting failed for {chap.title}!\nGot     : {extracted_images}\nExpected: {expected_image_order}"
            )
        print("[OK] Image file order within each chapter valid!")

        print("\n2. Testing order in final EPUB file...")
        output_epub = Path(temp_dir) / "test_sort.epub"
        create_epub(
            chapters=chapters,
            output_file=output_epub,
            title="Test Natural Sorting",
            author="Tester"
        )
        assert output_epub.exists(), "EPUB file was not generated."

        # Inspect table of contents and spine in the OPF
        with zipfile.ZipFile(output_epub, 'r') as z:
            container_xml = z.read('META-INF/container.xml')
            root = ET.fromstring(container_xml)
            opf_path = root.find('.//{*}rootfile').attrib['full-path']
            opf_xml = z.read(opf_path)
            opf_root = ET.fromstring(opf_xml)

            # Verify item order in spine
            manifest_items = {
                item.attrib['id']: item.attrib['href']
                for item in opf_root.findall('.//{*}item')
            }
            spine_itemrefs = [
                itemref.attrib['idref']
                for itemref in opf_root.findall('.//{*}itemref')
            ]
            spine_files = [manifest_items[idref] for idref in spine_itemrefs if idref in manifest_items]

            print(f"Spine items: {spine_files[:3]} ... {spine_files[-2:]}")
            # The first spine item is navigation 'nav.xhtml', followed by 25 pages in exact order
            expected_spine = ["nav.xhtml"] + [f"pages/page_{i:04d}.xhtml" for i in range(1, 26)]
            assert spine_files == expected_spine, f"Spine order is not sequential! Got: {spine_files}"
            print("[OK] Sequential page order in EPUB spine valid!")

            # Verify nav.xhtml for Table of Contents (TOC)
            nav_content = z.read('EPUB/nav.xhtml').decode('utf-8')
            print("Verifying Table of Contents order (nav.xhtml)...")
            for idx in range(len(expected_chapter_order) - 1):
                c1 = expected_chapter_order[idx]
                c2 = expected_chapter_order[idx + 1]
                pos1 = nav_content.find(c1)
                pos2 = nav_content.find(c2)
                assert pos1 != -1 and pos2 != -1, f"Chapter not found in nav.xhtml: {c1} or {c2}"
                assert pos1 < pos2, f"Incorrect order in TOC: '{c1}' (pos {pos1}) after '{c2}' (pos {pos2})"

        print("[OK] TOC and Spine order valid in EPUB!")
        print("\nALL NATURAL SORTING TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_natural_sorting_order()
