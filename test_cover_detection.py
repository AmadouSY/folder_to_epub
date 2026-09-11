import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

from folder_to_epub import collect_chapters_and_images, create_epub, find_root_cover
import gui


def test_root_cover_auto_detection():
    print("=== Test Root Cover Auto-Detection ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "test_book_with_cover"
        base_dir.mkdir()

        # 1. Create a root cover image: 'cover.jpg' (Red)
        root_cover = base_dir / "cover.jpg"
        img_cover = Image.new('RGB', (400, 600), color=(255, 0, 0))
        img_cover.save(root_cover)

        # 2. Create chapter subdirectories with their own pages (Green and Blue)
        chap1 = base_dir / "Chapter 01"
        chap1.mkdir()
        img_page1 = chap1 / "01.jpg"
        img_p1 = Image.new('RGB', (400, 600), color=(0, 255, 0))
        img_p1.save(img_page1)

        chap2 = base_dir / "Chapter 02"
        chap2.mkdir()
        img_page2 = chap2 / "01.jpg"
        img_p2 = Image.new('RGB', (400, 600), color=(0, 0, 255))
        img_p2.save(img_page2)

        # Test 1: find_root_cover
        detected = find_root_cover(base_dir)
        assert detected is not None, "find_root_cover could not find cover.jpg!"
        assert detected.name == "cover.jpg", f"Incorrect filename: {detected.name}"
        print("[OK] find_root_cover() successfully detected:", detected.name)

        # Test 2: create_epub without specifying custom_cover_path
        chapters = collect_chapters_and_images(base_dir)
        output_epub = Path(temp_dir) / "output.epub"
        create_epub(
            chapters=chapters,
            output_file=output_epub,
            title="Book with Root Cover",
            author="Test Author",
            custom_cover_path=None,  # No explicit cover specified
            source_dir=base_dir
        )
        assert output_epub.exists(), "EPUB file not generated!"

        # Verify that the cover inside the EPUB is indeed cover.jpg (and not 01.jpg)
        with zipfile.ZipFile(output_epub, 'r') as z:
            namelist = z.namelist()
            print("Files in EPUB:", [n for n in namelist if 'cover' in n])
            assert any('cover_cover.jpg' in n for n in namelist), "Cover cover.jpg not present in EPUB!"

            # Verify in content.opf
            root = ET.fromstring(z.read('EPUB/content.opf'))
            cover_item = root.find('.//{*}item[@properties="cover-image"]')
            assert cover_item is not None, "cover-image item not found in content.opf!"
            assert "cover_cover.jpg" in cover_item.attrib['href'], f"Unexpected href: {cover_item.attrib['href']}"
            print("[OK] EPUB cover properly references the root image:", cover_item.attrib['href'])

        # Test 3: GUI check
        app = gui.FolderToEpubApp()
        app.source_dir = base_dir
        app.source_path_var.set(str(base_dir))
        app._analyze_source_directory()

        assert app.auto_root_cover is not None, "GUI did not detect auto_root_cover!"
        assert app.auto_root_cover.name == "cover.jpg", f"Unexpected GUI cover name: {app.auto_root_cover.name}"
        assert app.cover_thumbnail_image is not None, "Cover thumbnail was not updated in GUI!"
        print("[OK] GUI correctly detected and displayed root cover:", app.auto_root_cover.name)
        app.destroy()

    print("\nALL ROOT COVER AUTO-DETECTION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_root_cover_auto_detection()
