"""Background worker thread utility for executing long tasks without freezing UI."""

import threading
from typing import Callable, Any


class AsyncWorker:
    """Spawns tasks in background daemon threads."""

    @staticmethod
    def run(target: Callable[..., Any], *args: Any, **kwargs: Any) -> threading.Thread:
        """Starts a target function in a background daemon thread."""
        thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
