import os
import queue
import threading
import time
import itertools
from typing import Callable
from .task import Task
from .threadPool import ThreadPool

CPU_COUNT: int = os.cpu_count() or 2


class Scheduler:
    """
    The orchestrator for timed and recurring task execution.

    The Scheduler manages a priority queue of tasks, sorted by their deadlines.
    A dedicated dispatcher thread monitors the queue and hands off due tasks
    to an internal ThreadPool for concurrent execution.

    Args:
        workers (int, optional): The number of threads in the execution pool.
            Defaults to the number of CPU cores available.
    """

    def __init__(self, workers: int = CPU_COUNT - 1):
        self.__executor = ThreadPool(max_workers=workers)
        self.__queue = queue.PriorityQueue(0)
        self.__cv = threading.Condition()
        self.__stop_requested = False
        self.__counter = itertools.count()
        self.__thread = threading.Thread(target=self.__run, daemon=True)

    def schedule(self, task: Task):
        """
        Adds a task to the priority queue.

        This method is thread-safe and can be called from any thread.
        It calculates the task's deadline and notifies the dispatcher
        if the new task is due sooner than existing tasks.

        Args:
            task (Task): The Task instance to be scheduled.
        """
        with self.__cv:
            deadline = time.monotonic() + task.timeout
            task_id = next(self.__counter)
            self.__queue.put((deadline, task_id, task))
            self.__cv.notify()

    def set_error_handler(self, handler: Callable[[Exception, Task], None]):
        """
        Registers a global callback to handle exceptions raised by tasks.

        Args:
            handler: A function that takes the Exception and the Task instance.
        """
        self.__executor.set_error_handler(handler)

    def __run(self):
        while not self.__stop_requested:
            with self.__cv:
                self.__cv.wait_for(
                    lambda: self.__stop_requested or not self.__queue.empty()
                )
            if self.__stop_requested:
                break
            deadline, counter, task = self.__queue.get()
            delta = deadline - time.monotonic()
            if delta > 0:
                with self.__cv:
                    self.__queue.put((deadline, counter, task))
                    self.__cv.wait(timeout=delta)
            else:
                self.__executor.submit(task)
                if task.repeat:
                    self.schedule(task)

    def start(self):
        self.__thread.start()

    def request_stop(self):
        """
        Signals the dispatcher and the thread pool to shut down gracefully.

        Tasks currently being executed will finish, but no new tasks
        will be processed from the queue.
        """
        with self.__cv:
            self.__stop_requested = True
            self.__cv.notify()
        self.__executor.shutdown(wait=True)
