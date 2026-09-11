import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def verify_epub(epub_path: Path):
    print(f"=== Verifying {epub_path.name} ===")
    with zipfile.ZipFile(epub_path, 'r') as z:
        file_list = z.namelist()
        print(f"Total files in EPUB archive: {len(file_list)}")
        print("First files:", file_list[:10])

        # Read content.opf
        container_xml = z.read('META-INF/container.xml')
        root = ET.fromstring(container_xml)
        opf_path = root.find('.//{*}rootfile').attrib['full-path']
        print(f"OPF path: {opf_path}")

        opf_content = z.read(opf_path).decode('utf-8')
        print("\n--- OPF Extract ---")
        lines = opf_content.splitlines()
        for line in lines[:35]:
            print(line)


if __name__ == "__main__":
    verify_epub(Path("sample_book.epub"))
    print("\n")
    verify_epub(Path("manga_test.epub"))
