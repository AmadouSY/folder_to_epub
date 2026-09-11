import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_sample_book(base_dir: Path):
    """Crée une arborescence de test avec plusieurs chapitres et images numérotées non triviales (ex: 2.jpg, 10.jpg)."""
    base_dir.mkdir(parents=True, exist_ok=True)
    
    chapters = {
        "Chapitre 01": ["1.jpg", "2.jpg", "10.jpg"],
        "Chapitre 02": ["01.jpg", "02.jpg", "03.jpg"],
        "Chapitre 10": ["cover.png", "page_1.png"]
    }

    colors = ["#FF5733", "#33FF57", "#3357FF", "#F033FF", "#33FFF0"]
    color_idx = 0

    for chap_name, files in chapters.items():
        chap_dir = base_dir / chap_name
        chap_dir.mkdir(exist_ok=True)

        for filename in files:
            file_path = chap_dir / filename
            img = Image.new('RGB', (800, 1200), color=colors[color_idx % len(colors)])
            draw = ImageDraw.Draw(img)
            text = f"{chap_name}\n{filename}"
            # Centrer le texte
            draw.text((100, 500), text, fill=(255, 255, 255))
            img.save(file_path)
            color_idx += 1

if __name__ == "__main__":
    test_dir = Path("./sample_book")
    create_sample_book(test_dir)
    print(f"Dossier de test créé sous : {test_dir.resolve()}")
