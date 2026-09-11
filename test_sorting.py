import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from folder_to_epub import collect_chapters_and_images, create_epub


def test_natural_sorting_order():
    """
    Teste rigoureusement l'ordre de tri naturel des sous-dossiers (chapitres)
    et des fichiers d'images pour s'assurer que 'Chapitre 2' vient bien avant 'Chapitre 10',
    et que 'page 2.jpg' vient bien avant 'page 10.jpg'.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "manga_test_sort"
        base_dir.mkdir()

        # Dossiers dans un ordre désordonné avec des nombres à 1, 2 et 3 chiffres (sans zéro initial)
        # En tri alphabétique pur (ASCII/lexicographique), l'ordre serait :
        # Chapitre 1, Chapitre 10, Chapitre 100, Chapitre 2, Chapitre 20
        # En tri naturel (natsort), l'ordre attendu est :
        # Chapitre 1, Chapitre 2, Chapitre 10, Chapitre 20, Chapitre 100
        chapter_names = [
            "Chapitre 100",
            "Chapitre 2",
            "Chapitre 20",
            "Chapitre 1",
            "Chapitre 10"
        ]

        expected_chapter_order = [
            "Chapitre 1",
            "Chapitre 2",
            "Chapitre 10",
            "Chapitre 20",
            "Chapitre 100"
        ]

        # Fichiers d'images dans chaque chapitre
        image_names = ["10.jpg", "1.jpg", "2.jpg", "20.jpg", "100.jpg"]
        expected_image_order = ["1.jpg", "2.jpg", "10.jpg", "20.jpg", "100.jpg"]

        for chap in chapter_names:
            chap_path = base_dir / chap
            chap_path.mkdir()
            for img_name in image_names:
                img_path = chap_path / img_name
                # Créer une petite image valide
                img = Image.new('RGB', (100, 100), color=(200, 100, 50))
                img.save(img_path)

        print("1. Test de collect_chapters_and_images()...")
        chapters = collect_chapters_and_images(base_dir)

        # Vérifier l'ordre des chapitres
        extracted_chapter_titles = [c.title for c in chapters]
        print(f"Ordre des chapitres extrait : {extracted_chapter_titles}")
        assert extracted_chapter_titles == expected_chapter_order, (
            f"Échec du tri des chapitres !\nObtenu  : {extracted_chapter_titles}\nAttendu : {expected_chapter_order}"
        )
        print("[OK] Ordre des sous-dossiers (chapitres) valide !")

        # Vérifier l'ordre des images dans chaque chapitre
        for chap in chapters:
            extracted_images = [p.file_path.name for p in chap.pages]
            assert extracted_images == expected_image_order, (
                f"Echec du tri des images pour {chap.title} !\nObtenu  : {extracted_images}\nAttendu : {expected_image_order}"
            )
        print("[OK] Ordre des fichiers d'images dans chaque chapitre valide !")

        print("\n2. Test de l'ordre dans le fichier EPUB final...")
        output_epub = Path(temp_dir) / "test_sort.epub"
        create_epub(
            chapters=chapters,
            output_file=output_epub,
            title="Test Natural Sorting",
            author="Tester"
        )
        assert output_epub.exists(), "Le fichier EPUB n'a pas ete genere."

        # Inspecter la table des matières et la colonne vertébrale (spine) dans l'OPF
        with zipfile.ZipFile(output_epub, 'r') as z:
            container_xml = z.read('META-INF/container.xml')
            root = ET.fromstring(container_xml)
            opf_path = root.find('.//{*}rootfile').attrib['full-path']
            opf_xml = z.read(opf_path)
            opf_root = ET.fromstring(opf_xml)

            # Vérifier l'ordre des items dans le spine
            manifest_items = {
                item.attrib['id']: item.attrib['href']
                for item in opf_root.findall('.//{*}item')
            }
            spine_itemrefs = [
                itemref.attrib['idref']
                for itemref in opf_root.findall('.//{*}itemref')
            ]
            spine_files = [manifest_items[idref] for idref in spine_itemrefs if idref in manifest_items]

            print(f"Items du spine : {spine_files[:3]} ... {spine_files[-2:]}")
            # Le premier élément du spine est la navigation 'nav.xhtml', suivi des 25 pages dans l'ordre exact
            expected_spine = ["nav.xhtml"] + [f"pages/page_{i:04d}.xhtml" for i in range(1, 26)]
            assert spine_files == expected_spine, f"L'ordre du spine n'est pas sequentiel ! Obtenu: {spine_files}"
            print("[OK] Ordre sequentiel de toutes les pages dans le spine EPUB valide !")

            # Vérifier nav.xhtml pour la table des matières (TOC)
            nav_content = z.read('EPUB/nav.xhtml').decode('utf-8')
            print("Verification de l'ordre dans la Table des Matieres (nav.xhtml)...")
            for idx in range(len(expected_chapter_order) - 1):
                c1 = expected_chapter_order[idx]
                c2 = expected_chapter_order[idx + 1]
                pos1 = nav_content.find(c1)
                pos2 = nav_content.find(c2)
                assert pos1 != -1 and pos2 != -1, f"Chapitre introuvable dans nav.xhtml : {c1} ou {c2}"
                assert pos1 < pos2, f"Ordre incorrect dans la TOC : '{c1}' (pos {pos1}) apres '{c2}' (pos {pos2})"

        print("[OK] Ordre dans la Table des Matieres (TOC) et le Spine EPUB valide avec succes !")
        print("\nTOUS LES TESTS DE TRI NATUREL ONT REUSSI AVEC SUCCES !")


if __name__ == "__main__":
    test_natural_sorting_order()
