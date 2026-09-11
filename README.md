# Folder to EPUB Converter (CLI & GUI)

A modern, production-grade Python application designed with **Clean Architecture** and **Clean Code** principles to convert image directories, manga/comic folder structures, and **`.cbz` / `.zip` archives** into clean, structured, and responsive EPUB 3 eBooks optimized for e-readers (Kindle, Kobo, Apple Books, reMarkable, etc.).

---

## 🏛️ Architecture & Clean Code Design

The project is structured into a clean top-level package (`folder_to_epub`) with clear separation across domain entities, use-case services, and presentation adapters:

```text
folder_to_epub/
├── pyproject.toml                       # Modern PEP 517/621 packaging
├── requirements.txt                     # Dependencies
├── README.md                            # Documentation
├── .gitignore                           # Git ignore rules
├── cli.py                               # CLI launcher shortcut
├── gui.py                               # GUI launcher shortcut
│
├── folder_to_epub/                      # Unified package
│   ├── __init__.py                      # Package exports
│   ├── __main__.py                      # Enables 'python -m folder_to_epub'
│   │
│   ├── core/                            # Domain Layer (Pure entities & rules)
│   │   ├── constants.py                 # Image/archive formats, CSS styles, languages
│   │   ├── exceptions.py                # Domain exceptions hierarchy
│   │   └── models.py                    # Book, Chapter, ImagePage, ConversionConfig
│   │
│   ├── services/                        # Application / Use Cases Layer
│   │   ├── archive.py                   # ArchiveService (.cbz, .zip parsing & fast cover extraction)
│   │   ├── scanner.py                   # ScannerService (inspection, sorting, cover discovery)
│   │   ├── builder.py                   # EpubBuilder (EPUB 3 assembly & styling)
│   │   └── converter.py                 # ConversionService (single & batch orchestration)
│   │
│   ├── cli/                             # Presentation Layer: CLI
│   │   ├── parser.py                    # Argument parsing
│   │   ├── renderer.py                  # Rich console presentation
│   │   └── main.py                      # CLI execution flow
│   │
│   └── ui/                              # Presentation Layer: Modern CustomTkinter GUI
│       ├── theme.py                     # Design tokens & color system
│       ├── worker.py                    # AsyncWorker for non-blocking execution
│       ├── app.py                       # FolderToEpubApp window coordinator
│       ├── components/                  # Modular UI components (Sidebar, Hero, Banner, Cards)
│       └── views/                       # Independent views (Dashboard, Books, Logs, Settings)
│
└── tests/                               # Standardized test suite
    ├── __init__.py
    ├── test_sorting.py                  # Natural sorting tests
    ├── test_cover_detection.py          # Root cover discovery tests
    ├── test_batch_conversion.py         # Multi-book batch packaging tests
    └── test_archive_support.py          # Direct .cbz and .zip archive tests
```

---

## 🚀 Key Features

- 📦 **Direct Archive Support (`.cbz`, `.zip`)**: Convert comic archives directly without manual unzipping. Pass a single `.cbz` or a collection folder containing multiple archives.
- ⚡ **Ultra-Fast In-Memory Cover Extraction**: Instantly generates GUI thumbnail previews from `.cbz` archives without unpacking hundreds of megabytes.
- 🖥️ **Modern Dashboard GUI (CustomTkinter)**: Intuitive window with live cover thumbnail preview, dual folder/archive selection, real-time progress bar, and 1-click open actions.
- 📚 **Multi-Book Batch Mode**: Automatically detects when a folder contains multiple books (folders or `.cbz` archives) and converts each into its own EPUB file.
- 🗂️ **Chapter Organization**: Subfolders map to entries in the Table of Contents (TOC). Also handles flat image directories.
- 🔢 **Strict Natural Sorting (`natsort`)**: Ensures that `2.jpg` precedes `10.jpg`, and `Chapter 2` precedes `Chapter 10`.
- 🖼️ **Multi-Format Image Support & Pillow Validation**: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.bmp` (validates image integrity and extracts dimensions).
- 🏷️ **Smart Cover Auto-Detection**: Searches for an image containing `cover` (e.g., `cover.jpg`, `00_cover.png`), falling back gracefully to the first page.
- 📱 **Responsive & Minimal CSS**: Prevents image shifts, clipping, and overflow across e-reader screens.
- 🎨 **Manga / Fixed-Layout Mode (`--manga`, `--rtl`)**: Configures EPUB 3 metadata with `pre-paginated`, `page-progression-direction="rtl"`, and `zero-margin` for ideal right-to-left reading.
- 🛡️ **Safety Filters**: Automatically filters out OS hidden/system artifacts (`.DS_Store`, `Thumbs.db`, `desktop.ini`).
- 📊 **Rich CLI**: Progress animations, summary tables, and verbose logging.
- 🧵 **Non-Blocking Multi-Threading**: GUI remains responsive throughout large conversions.

---

## 🛠️ Installation

```bash
pip install -r requirements.txt
```

*(Optional: Install in editable developer mode)*
```bash
pip install -e .
```

---

## 🖥️ Launching the Application

### 1. Graphical User Interface (GUI)
```bash
python gui.py
```
*or via module execution:*
```bash
python -m folder_to_epub --gui
```

### 2. Command-Line Interface (CLI)
```bash
python cli.py ./my_book
```
*or via module execution:*
```bash
python -m folder_to_epub ./my_book
```

---

## 💻 CLI Commands & Examples

### Basic Folder Conversion
```bash
python -m folder_to_epub ./my_book
```

### Direct `.cbz` Comic / Manga Conversion
```bash
python -m folder_to_epub ./One_Piece_Vol_01.cbz -o ./One_Piece_Vol_01.epub --manga --rtl
```

### Batch Conversion of Archive Collection
```bash
python -m folder_to_epub ./my_cbz_collection/ --batch -o ./output_epubs/
```

### Custom Title, Author, and Language
```bash
python -m folder_to_epub ./my_book -o ./my_novel.epub --title "My Novel" --author "Author" --lang en
```

---

## ⚙️ Command-Line Arguments

| Option | Shorthand | Description |
| :--- | :--- | :--- |
| `source_dir` | *(Positional)* | Source directory, or path to a `.cbz` / `.zip` archive file. |
| `--gui` | `-g` | Launch the Graphical User Interface. |
| `--batch` | `-b` | Force multi-book batch mode (supports folders and archives). |
| `--output` | `-o` | Output EPUB path (or destination directory in batch mode). |
| `--title` | `-t` | eBook title (defaults to directory/archive name). |
| `--author` | `-a` | Author name (default: `Unknown`). |
| `--lang` | `-l` | Language code (default: `en`). |
| `--cover` | `-c` | Custom cover image file. |
| `--manga` | | Enable EPUB 3 Fixed-Layout (`pre-paginated`). |
| `--rtl` | | Set reading progression from Right-To-Left. |
| `--verbose` | `-v` | Show verbose output. |

---

## 🧪 Running the Test Suite

```bash
python -m unittest discover -s tests -p "test_*.py"
```
