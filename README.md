# Folder to EPUB Converter (CLI & GUI)

A comprehensive Python tool featuring both a **Modern Graphical User Interface (GUI)** and a **Command-Line Interface (CLI)** to convert an image folder tree into a clean, structured, and responsive EPUB file optimized for e-readers (Kindle, Kobo, Apple Books, Kobo Clara/Libra, reMarkable, etc.).

---

## 🏛️ Architecture & Clean Code Design

The project is structured according to **Clean Architecture** and **SOLID** principles, ensuring separation of concerns, testability, and maintainability:

```text
folder_to_epub/
├── core/                        # Domain Layer (Independent of UI/CLI)
│   ├── constants.py             # Formats, responsive CSS, and application metadata
│   ├── exceptions.py            # Domain-specific exceptions hierarchy
│   └── models.py                # ImagePage, ChapterData, BookData, ConversionConfig
│
├── services/                    # Application / Use Cases Layer
│   ├── scanner.py               # File scanning, natural sorting, and cover detection
│   ├── builder.py               # Pure EPUB 3 document assembly & styling
│   └── converter.py             # Single and multi-book batch orchestration
│
├── cli/                         # Presentation Layer: Command-Line Interface
│   ├── parser.py                # Argument parsing and documentation
│   ├── renderer.py              # Rich terminal panels, tables, and progress bars
│   └── main.py                  # CLI command flow
│
├── ui/                          # Presentation Layer: Graphical User Interface
│   ├── theme.py                 # Design tokens and color palette
│   ├── worker.py                # Asynchronous worker thread manager
│   ├── components/              # Modular UI widgets
│   │   ├── sidebar.py           # Navigation sidebar and appearance switcher
│   │   ├── hero_header.py       # Dynamic status hero header
│   │   ├── action_banner.py     # Main CTA button and progress bar
│   │   └── cards.py             # 6 modular dashboard cards
│   ├── views/                   # Application screens
│   │   ├── dashboard_view.py    # Main workspace
│   │   ├── books_view.py        # Books & chapters explorer
│   │   ├── logs_view.py         # Activity log console
│   │   └── settings_view.py     # Information & preferences
│   └── app.py                   # FolderToEpubApp window coordinator
│
├── folder_to_epub.py            # Backward-compatible CLI entry point & public facade
└── gui.py                       # Backward-compatible GUI launcher facade
```

---

## 🚀 Features

- 🖥️ **Modern Graphical User Interface (CustomTkinter)**: Intuitive window with live cover thumbnail preview, interactive folder selection, real-time progress bar, and 1-click open actions.
- 📚 **Multi-Book Batch Mode**: Automatically detects when a folder contains multiple books (e.g., an entire manga or comic collection) and converts each into its own EPUB file with independent chapters and covers.
- 🗂️ **Chapter Organization**: Each subfolder maps to an entry in the Table of Contents (TOC). Also handles flat folders of images directly.
- 🔢 **Strict Natural Sorting (`natsort`)**: Ensures that `2.jpg` precedes `10.jpg`, and `Chapter 2` precedes `Chapter 10`.
- 🖼️ **Multi-Format Image Support & Pillow Validation**: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.bmp` (validates image integrity and extracts dimensions).
- 🏷️ **Smart Cover Auto-Detection**: Searches for an image file in the root folder containing `cover` (e.g., `cover.jpg`, `00_cover.png`) when none is specified, falling back gracefully to the first page of the first chapter.
- 📱 **Responsive & Minimal CSS**: Prevents image shifts, clipping, and overflow across e-reader screens.
- 🎨 **Manga / Fixed-Layout Mode (`--manga`, `--rtl`)**: Configures EPUB 3 metadata with `pre-paginated`, `page-progression-direction="rtl"`, and `zero-margin` for ideal right-to-left reading.
- 🛡️ **Safety Filters**: Automatically filters out OS hidden/system artifacts (`.DS_Store`, `Thumbs.db`, `desktop.ini`, etc.).
- 📊 **Rich CLI**: Progress animations, summary tables, and verbose logging.
- 🧵 **Non-Blocking Multi-Threading**: GUI remains responsive throughout large conversions.

---

## 🛠️ Installation

```bash
pip install -r requirements.txt
```

---

## 🖥️ Graphical User Interface (GUI) Usage

Launch the GUI using:

```bash
python gui.py
```
*or via the CLI flag:*
```bash
python folder_to_epub.py --gui
```
*(or simply by double-clicking `gui.py` on Windows)*

**GUI Highlights:**
- 📁 Folder selection with automatic structure inspection (single book vs. batch collection, chapters count, and total pages).
- 🖼️ Live cover thumbnail preview of automatically detected or manually chosen covers.
- ⚡ Smart pre-filling for book title and output file name.
- ⚙️ Toggle switches for Manga / Fixed-Layout and Right-to-Left (RTL) reading direction.
- 📈 Real-time progress bar with an embedded activity log panel.
- 📂 Direct completion buttons to open the generated EPUB or reveal it in File Explorer.

---

## 📂 Expected Input Directory Structure

### Single Book (Multi-Chapter):
```text
my_book/
├── cover.jpg          <-- (Optional: auto-detected as cover)
├── Chapter 01/
│   ├── 01.jpg
│   ├── 02.jpg
│   └── 10.jpg
└── Chapter 02/
    ├── 01.jpg
    └── 02.jpg
```

### Multi-Book Collection (Batch Mode):
```text
my_collection/
├── One Piece Vol 01/
│   ├── cover.jpg
│   ├── Chapter 01/
│   └── Chapter 02/
└── Naruto Vol 01/
    ├── 00_cover.png
    ├── page_01.jpg
    └── page_02.jpg
```

*Note: Flat single-folder books containing images directly are also fully supported.*

---

## 💻 CLI Commands & Examples

### 1. Basic Conversion

```bash
python folder_to_epub.py ./my_book
```
*Generates `my_book.epub` in the current working directory.*

### 2. Custom Output Path and Metadata

```bash
python folder_to_epub.py ./my_book -o ./my_graphic_novel.epub --title "My Graphic Novel" --author "John Doe" --lang en
```

### 3. Manga / Comic Mode (Fixed-Layout & Right-to-Left)

```bash
python folder_to_epub.py ./manga_folder -o ./one_piece_v01.epub --title "One Piece Vol. 1" --author "Eiichiro Oda" --manga --rtl
```

### 4. Custom Cover Image

```bash
python folder_to_epub.py ./my_book -c ./custom_cover.jpg
```

### 5. Multi-Book Batch Processing

```bash
python folder_to_epub.py ./my_collection --batch -o ./output_epubs/
```
*Creates an `.epub` file for every book subfolder inside the output directory.*

---

## ⚙️ Command-Line Arguments

| Option | Shorthand | Description |
| :--- | :--- | :--- |
| `source_dir` | *(Positional)* | Optional if `--gui` is used. Source directory containing images/chapters. |
| `--gui` | `-g` | Launch the interactive Graphical User Interface (GUI). |
| `--batch` | `-b` | Enable multi-book batch mode (generates one EPUB per subfolder). |
| `--output` | `-o` | Output EPUB filepath (or output directory in batch mode). |
| `--title` | `-t` | Book title (defaults to source directory name). |
| `--author` | `-a` | Author name (defaults to `Unknown`). |
| `--lang` | `-l` | ISO language code (defaults to `en`). |
| `--cover` | `-c` | Custom cover image file. Defaults to root image containing `cover`, otherwise first page. |
| `--manga` | | Enable EPUB 3 Fixed-Layout (`pre-paginated`) for comics & manga. |
| `--rtl` | | Set reading direction to Right-To-Left (RTL). |
| `--verbose` | `-v` | Display detailed processing output. |
