"""Background daemon thread worker for asynchronous tasks."""

import threading
from typing import Callable, Any


class AsyncWorker:
    """Dispatches heavy tasks to background daemon threads."""

    @staticmethod
    def run(target: Callable[..., Any], *args: Any, **kwargs: Any) -> threading.Thread:
        thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
