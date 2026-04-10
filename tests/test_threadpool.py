import threading

from scheduler import ThreadPool, Task


def test_thread_pool_throughput():
    pool = ThreadPool(max_workers=2)
    results = []

    def work(n):
        results.append(n * n)

    for i in range(10):
        task = Task(timeout=0, repeat=False, func=work, n=i)
        pool.submit(task)

    pool.shutdown(wait=True)

    assert sorted(results) == [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]


def test_thread_pool_exception_resilience():
    pool = ThreadPool(max_workers=2)
    results = []

    def work(n):
        if n == 5:
            raise ValueError("Intentional error")
        results.append(n * n)

    for i in range(10):
        task = Task(timeout=0, repeat=False, func=work, n=i)
        pool.submit(task)

    pool.shutdown(wait=True)

    assert sorted(results) == [0, 1, 4, 9, 16, 36, 49, 64, 81]


def test_thread_pool_exception_handling():
    pool = ThreadPool(max_workers=1)
    errors = []

    handler_event = threading.Event()

    def error_handler(exception, task):
        errors.append(exception)
        handler_event.set()

    pool.set_error_handler(error_handler)

    def work():
        raise ValueError("Task failed intentionally")

    pool.submit(Task(timeout=0, repeat=False, func=work))

    success = handler_event.wait(timeout=5)

    assert success, "Error handler was not called within the timeout period"
    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)
    assert str(errors[0]) == "Task failed intentionally"

    pool.shutdown(wait=True)


def test_thread_pool_shutdown():
    pool = ThreadPool(max_workers=3)
    results = []

    def work(n):
        results.append(n * n)

    for i in range(5):
        task = Task(timeout=0, repeat=False, func=work, n=i)
        pool.submit(task)

    pool.shutdown(wait=True)

    assert sorted(results) == [0, 1, 4, 9, 16]
    workers = pool.__getattribute__("_ThreadPool__workers")
    assert len(workers) == 3
    for worker in workers:
        assert worker.is_alive() is False
