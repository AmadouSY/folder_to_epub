import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def verify_epub(epub_path: Path):
    print(f"=== Vérification de {epub_path.name} ===")
    with zipfile.ZipFile(epub_path, 'r') as z:
        file_list = z.namelist()
        print(f"Nombre total de fichiers dans le zip EPUB : {len(file_list)}")
        print("Premiers fichiers :", file_list[:10])

        # Lire content.opf
        container_xml = z.read('META-INF/container.xml')
        root = ET.fromstring(container_xml)
        opf_path = root.find('.//{*}rootfile').attrib['full-path']
        print(f"Chemin OPF : {opf_path}")

        opf_content = z.read(opf_path).decode('utf-8')
        print("\n--- Extrait du OPF ---")
        lines = opf_content.splitlines()
        for line in lines[:35]:
            print(line)

if __name__ == "__main__":
    verify_epub(Path("sample_book.epub"))
    print("\n")
    verify_epub(Path("manga_test.epub"))
