"""Domain-specific exceptions for folder_to_epub."""


class FolderToEpubError(Exception):
    """Base exception for all folder_to_epub errors."""
    pass


class InvalidSourceError(FolderToEpubError):
    """Raised when the specified source path does not exist or is not a directory."""
    pass


class NoImagesFoundError(FolderToEpubError):
    """Raised when no valid images were discovered in the source directory."""
    pass


class InvalidImageError(FolderToEpubError):
    """Raised when an image file cannot be read, decoded, or validated."""
    pass


class EpubGenerationError(FolderToEpubError):
    """Raised when EPUB packaging or file writing fails."""
    pass
