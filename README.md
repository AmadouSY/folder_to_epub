# Folder to EPUB Converter (CLI & GUI)

Un outil Python complet (avec **Interface Graphique Moderne** et **Ligne de Commande CLI**) permettant de convertir une arborescence de dossiers d'images en un fichier EPUB propre, structuré et responsive, optimisé pour liseuses (Kindle, Kobo, Apple Books, Kobo Clara/Libra, etc.).

## 🚀 Fonctionnalités

- 🖥️ **Interface Graphique Moderne (CustomTkinter)** : Fenêtre intuitive avec aperçu miniature de la couverture, sélection interactive, suivi de la progression et ouverture en 1 clic.
- 🗂️ **Organisation par chapitres** : Chaque sous-dossier correspond à une entrée dans la Table des Matières (TOC). Supporte aussi les dossiers plats d'images.
- 🔢 **Tri naturel strict (`natsort`)** : Garantit que `2.jpg` apparaît avant `10.jpg`, et `Chapitre 2` avant `Chapitre 10`.
- 🖼️ **Support multi-formats & Pillow** : `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.bmp` (validation de l'intégrité et lecture des dimensions).
- 🏷️ **Détection intelligente de la couverture** : Recherche automatique à la racine d'une image contenant `cover` ou `couverture` (ex: `cover.jpg`, `00_cover.png`) si aucune n'est spécifiée, avec repli sur la 1ère image du 1er chapitre.
- 📱 **CSS responsive & minimal** : Empêche le décalage, le rognage ou le débordement des images.
- 🎨 **Mode Manga / Fixed-Layout (`--manga`, `--rtl`)** : Ajoute les métadonnées `pre-paginated`, `page-progression-direction="rtl"`, `zero-margin` pour une lecture optimale de droite à gauche.
- 🛡️ **Filtres de sécurité** : Ignore automatiquement les fichiers système et cachés (`.DS_Store`, `Thumbs.db`, `desktop.ini`, etc.).
- 📊 **Interface CLI avec Rich** : Barre de progression animée, tableaux récapitulatifs et logs détaillés.
- 🧵 **Multi-threading non-bloquant** : L'interface graphique reste toujours fluide lors des conversions volumineuses.

---

## 🛠️ Installation

```bash
pip install -r requirements.txt
```

---

## 🖥️ Utilisation de l'Interface Graphique (GUI)

Pour lancer l'interface graphique :

```bash
python gui.py
```
*ou directement :*
```bash
python folder_to_epub.py --gui
```
*(ou simplement en double-cliquant sur `gui.py` sous Windows)*

**Points forts du GUI :**
- 📁 Sélection de dossier avec détection automatique de la structure (mono ou multi-chapitres) et nombre de pages.
- 🖼️ Prévisualisation miniature en direct de la couverture détectée ou personnalisée.
- ⚡ Pré-remplissage automatique du titre et du nom de fichier de sortie.
- ⚙️ Switches pour le mode Manga / Fixed-Layout et lecture RTL (Droite à gauche).
- 📈 Barre de progression en temps réel avec console de logs intégrée.
- 📂 Boutons directs à la fin pour ouvrir l'EPUB ou son dossier dans l'Explorateur Windows.

---

## 📂 Structure attendue en entrée

```text
mon_livre/
├── Chapitre 01/
│   ├── 01.jpg
│   ├── 02.jpg
│   └── 10.jpg
└── Chapitre 02/
    ├── 01.jpg
    └── 02.jpg
```

*Note : Le script prend également en compte les dossiers simples (plat) contenant directement des images.*

---

## 💻 Commandes d'exécution

### 1. Utilisation de base

```bash
python folder_to_epub.py ./mon_livre
```
*Génère `mon_livre.epub` dans le dossier courant.*

### 2. Spécifier le nom de sortie et les métadonnées

```bash
python folder_to_epub.py ./mon_livre -o ./mon_roman_graphique.epub --title "Mon Roman Graphique" --author "Jean Dupont" --lang fr
```

### 3. Mode Manga / BD (Fixed-Layout & Lecture de Droite à Gauche)

```bash
python folder_to_epub.py ./manga_folder -o ./one_piece_v01.epub --title "One Piece Vol. 1" --author "Eiichiro Oda" --manga --rtl
```

### 4. Spécifier une image de couverture personnalisée

```bash
python folder_to_epub.py ./mon_livre -c ./custom_cover.jpg
```

---

## ⚙️ Options de la ligne de commande

| Option | Raccourci | Description |
| :--- | :--- | :--- |
| `source_dir` | *(Positionnel)* | Optionnel si `--gui` est utilisé. Dossier source contenant les images/chapitres. |
| `--gui` | `-g` | Lance l'interface graphique interactive (GUI). |
| `--output` | `-o` | Chemin du fichier EPUB généré (par défaut `<nom_du_dossier>.epub`). |
| `--title` | `-t` | Titre du livre (par défaut le nom du dossier source). |
| `--author` | `-a` | Nom de l'auteur (par défaut `Inconnu`). |
| `--lang` | `-l` | Code langue ISO (par défaut `fr`). |
| `--cover` | `-c` | Image de couverture spécifique. Par défaut : recherche une image à la racine contenant `cover` ou `couverture`, sinon prend la 1ère image du 1er chapitre. |
| `--manga` | | Active le Fixed-Layout EPUB 3 (`pre-paginated`) pour Mangas & BD. |
| `--rtl` | | Sens de lecture de droite à gauche (*Right-To-Left*). |
| `--verbose` | `-v` | Affiche plus de détails durant le traitement. |
