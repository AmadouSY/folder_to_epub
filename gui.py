#!/usr/bin/env python3
"""
Folder to EPUB Converter - GUI Entry Point
==========================================
Clean facade and direct launcher for the modern CustomTkinter Graphical User Interface.
"""

from ui.app import FolderToEpubApp, main

__all__ = ["FolderToEpubApp", "main"]

if __name__ == "__main__":
    main()
