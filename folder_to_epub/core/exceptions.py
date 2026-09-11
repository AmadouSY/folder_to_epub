"""Domain-level exceptions."""


class FolderToEpubError(Exception):
    """Base exception for all domain errors."""
    pass


class InvalidSourceError(FolderToEpubError):
    """Raised when the given source directory does not exist or is invalid."""
    pass


class NoImagesFoundError(FolderToEpubError):
    """Raised when no valid images are discovered in the source path."""
    pass


class InvalidImageError(FolderToEpubError):
    """Raised when an image fails decoding or validation."""
    pass


class EpubGenerationError(FolderToEpubError):
    """Raised when EPUB assembly or writing encounters an unrecoverable failure."""
    pass
