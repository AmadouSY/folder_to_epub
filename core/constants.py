"""Global constants and configuration defaults for folder_to_epub."""

APP_TITLE = "EPUB Forge"
APP_VERSION = "2.0.0"

# Set of supported image file extensions (lowercase)
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

# Default CSS styling for generated EPUB pages
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

# Common languages supported with human-readable labels
AVAILABLE_LANGUAGES = [
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
]
