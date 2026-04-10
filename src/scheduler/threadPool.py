import os
import queue
import threading
from typing import Callable, Optional
from .task import Task
import logging

logger = logging.getLogger("scheduler")


class ThreadPool:
    """
    A fixed-size pool of reusable worker threads.

    This pool manages a set of background OS threads that wait for tasks
    to arrive in a thread-safe queue. It is designed for high-throughput,
    fire-and-forget execution without the overhead of creating new threads
    for every task.

    Args:
        max_workers (int): The number of worker threads to spawn.
    """

    def __init__(self, max_workers: int | None = None):
        self.__max_workers: int = max_workers or (os.cpu_count() or 2) * 5
        self.__queue: queue.Queue[Task | None] = queue.Queue()
        self.__workers: list[threading.Thread] = []
        self.__error_handler: Optional[Callable[[Exception, Task], None]] = None
        self.__setup_workers()

    def set_error_handler(self, handler: Callable[[Exception, Task], None]):
        """
        Sets a custom error handler for exceptions raised during task execution.

        The handler should be a callable that accepts two arguments:
        - exception: The Exception instance that was raised.
        - task: The Task instance that caused the exception.

        Args:
            handler (Callable[[Exception, Task], None]): The error handler function.
        """
        self.__error_handler = handler

    def submit(self, task: Task):
        """
        Submits a task to the queue for execution by the next available worker.

        Args:
            task (Task): The Task instance to be executed.
        """
        self.__queue.put(task)

    def __worker_loop(self):
        while True:
            task = self.__queue.get()
            if task is None:
                break
            try:
                task()
            except Exception as e:
                if self.__error_handler:
                    try:
                        self.__error_handler(e, task)
                    except Exception as handler_error:
                        logger.exception(f"Error in error handler: {handler_error}")
                else:
                    logger.exception(f"Task execution failed: {e}")

    def shutdown(self, wait: bool = True):
        """
        Signals all threads to stop and cleans up the pool.

        This method send a 'Poison Pill': it injects a 'None'
        into the queue for every worker thread. Each thread will
        receive one 'None' and exit its loop.

        Args:
            wait (bool): If True, blocks the caller until all currently
                queued tasks and the shutdown signals are processed.
        """
        for _ in self.__workers:
            self.__queue.put(None)
        if wait:
            for worker in self.__workers:
                worker.join()

    def __setup_workers(self):
        for _ in range(self.__max_workers):
            worker = threading.Thread(target=self.__worker_loop, daemon=True)
            worker.start()
            self.__workers.append(worker)
