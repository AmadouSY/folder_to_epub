import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

from folder_to_epub import collect_chapters_and_images, create_epub, find_root_cover
import gui


def test_root_cover_auto_detection():
    print("=== Test de la detection automatique de couverture a la racine ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "test_book_with_cover"
        base_dir.mkdir()

        # 1. Créer une image de couverture à la racine : 'cover.jpg' (couleur Rouge)
        root_cover = base_dir / "cover.jpg"
        img_cover = Image.new('RGB', (400, 600), color=(255, 0, 0))
        img_cover.save(root_cover)

        # 2. Créer des sous-dossiers de chapitres avec leurs propres images (couleur Verte)
        chap1 = base_dir / "Chapitre 01"
        chap1.mkdir()
        img_page1 = chap1 / "01.jpg"
        img_p1 = Image.new('RGB', (400, 600), color=(0, 255, 0))
        img_p1.save(img_page1)

        chap2 = base_dir / "Chapitre 02"
        chap2.mkdir()
        img_page2 = chap2 / "01.jpg"
        img_p2 = Image.new('RGB', (400, 600), color=(0, 0, 255))
        img_p2.save(img_page2)

        # Test 1 : find_root_cover
        detected = find_root_cover(base_dir)
        assert detected is not None, "find_root_cover n'a pas trouve l'image cover.jpg !"
        assert detected.name == "cover.jpg", f"Nom incorrect : {detected.name}"
        print("[OK] find_root_cover() a bien detecte :", detected.name)

        # Test 2 : create_epub sans specifier custom_cover_path
        chapters = collect_chapters_and_images(base_dir)
        output_epub = Path(temp_dir) / "output.epub"
        create_epub(
            chapters=chapters,
            output_file=output_epub,
            title="Livre avec Couverture Racine",
            author="Auteur Test",
            custom_cover_path=None, # Aucun cover explicite spécifié
            source_dir=base_dir
        )
        assert output_epub.exists(), "Fichier EPUB non genere !"

        # Vérifier que le cover dans l'EPUB est bien cover.jpg (et non 01.jpg)
        with zipfile.ZipFile(output_epub, 'r') as z:
            namelist = z.namelist()
            print("Fichiers dans l'EPUB :", [n for n in namelist if 'cover' in n])
            assert any('cover_cover.jpg' in n for n in namelist), "La couverture cover.jpg n'est pas presente dans l'EPUB !"

            # Verifier dans content.opf
            root = ET.fromstring(z.read('EPUB/content.opf'))
            cover_item = root.find('.//{*}item[@properties="cover-image"]')
            assert cover_item is not None, "Item cover-image introuvable dans content.opf !"
            assert "cover_cover.jpg" in cover_item.attrib['href'], f"href inattendu : {cover_item.attrib['href']}"
            print("[OK] La couverture de l'EPUB utilise bien l'image racine :", cover_item.attrib['href'])

        # Test 3 : Vérification dans le GUI
        app = gui.FolderToEpubApp()
        app.source_dir = base_dir
        app.source_path_var.set(str(base_dir))
        app._analyze_source_directory()

        assert app.auto_root_cover is not None, "Le GUI n'a pas detecte auto_root_cover !"
        assert app.auto_root_cover.name == "cover.jpg", f"Nom GUI inattendu : {app.auto_root_cover.name}"
        assert app.cover_thumbnail_image is not None, "La miniature n'a pas ete mise a jour dans le GUI !"
        print("[OK] Le GUI a correctement detecte et affiche la couverture racine :", app.auto_root_cover.name)
        app.destroy()

    print("\nTOUS LES TESTS DE DETECTION DE COUVERTURE RACINE ONT REUSSI AVEC SUCCES !")


if __name__ == "__main__":
    test_root_cover_auto_detection()
