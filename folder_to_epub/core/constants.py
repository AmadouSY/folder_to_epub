"""Global domain constants for folder_to_epub."""

APP_NAME = "folder_to_epub"
APP_TITLE = "EPUB Forge"
APP_VERSION = "2.1.0"

# Formats supported by the scanner
SUPPORTED_EXTENSIONS = frozenset({'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'})

# Responsive page styling for EPUB 3
DEFAULT_CSS = """@page {
    margin: 0;
    padding: 0;
}
html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    text-align: center;
    background-color: #ffffff;
}
div.page-container {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
}
img.page-image {
    max-width: 100%;
    max-height: 100%;
    height: auto;
    width: auto;
    object-fit: contain;
    display: block;
    margin: 0 auto;
}
"""

AVAILABLE_LANGUAGES = (
    ("en", "en (English)"),
    ("fr", "fr (French)"),
    ("ja", "ja (Japanese)"),
    ("es", "es (Spanish)"),
    ("de", "de (German)"),
    ("it", "it (Italian)"),
    ("zh", "zh (Chinese)"),
    ("ko", "ko (Korean)"),
    ("pt", "pt (Portuguese)"),
    ("ru", "ru (Russian)"),
)
