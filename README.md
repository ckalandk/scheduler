# schedcore

![Tests](https://github.com/ckalandk/scheduler/actions/workflows/tests.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.13t%20%7C%203.14%20%7C%203.14t-blue)
![Linter: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

A lightweight, thread-safe, and zero-dependency concurrent task scheduling engine for Python.

`schedcore` allows you to schedule tasks to execute in the future, handle recurring tasks, and process them concurrently using a custom-built, lightweight thread pool—all without the overhead of heavy third-party libraries.

## 🚀 Features

* **Zero Dependencies:** Built entirely using Python's standard library (`threading`, `queue`, `time`).
* **Custom Execution Engine:** Uses a custom ThreadPool designed for absolute bare-metal performance.
* **Thread-Safe Architecture:** Protected by condition variables and thread-safe queues to prevent race conditions and spurious wakeups.
* **Configurable error handling:** uses callback function for error handling which can be supplied via `set_error_handler()`
* **Graceful Shutdown:** Implements the "Poison Pill" pattern to ensure all background OS threads terminate cleanly without leaking memory.
* **Modern Python:** Fully type-hinted and compatible with Python 3.10+.

## 🛠️ Installation

This project uses [uv](https://github.com/astral-sh/uv), you can easily set it up for local development.

1. Clone the repository:

   ```bash
   git clone [https://github.com/ckalandk/scheduler.git](https://github.com/ckalandk/schedcore.git)
   cd schedcore
   ```

2. Install the package in editable mode using uv:

```bash
    uv sync
```

## 📖 Quick Start

The following example, demonstrate how to start a scheduler, submit tasks and
gracefully shut it down

```python
import time
from schedcore import Scheduler, Task

# 1. Define your tasks
def greet(name: str):
    print(f"[{time.strftime('%X')}] Hello, {name}!")

def recurring_ping():
    print(f"[{time.strftime('%X')}] Ping...")

def raise_error():
    raise ValuerError("Task raised and exception")

def error_handler(exception, task):
    print(f"Task: {task} didn't execute du to an exception: {exception})

# 2. Initialize the Scheduler (automatically sizes the ThreadPool based on CPU cores)
scheduler = Scheduler(workers=4)
scheduler.set_error_handler(error_hander)

scheduler.start()

print(f"[{time.strftime('%X')}] Scheduler started.")

# 3. Schedule tasks
# Runs once, 2 seconds from now
task_one = Task(timeout=2, repeat=False, func=greet, name="Alice")
scheduler.schedule(task_one)

# Runs repeatedly, every 1.5 seconds
task_two = Task(timeout=1.5, repeat=True, func=recurring_ping)
scheduler.schedule(task_two)

# 4. Keep the main thread alive to watch the background threads work
try:
    time.sleep(6)
except KeyboardInterrupt:
    pass
finally:
    # 5. Cleanly shut down all background threads
    print("Shutting down gracefully...")
    scheduler.request_stop()
```

## 🧠 Architecture Overview

This library is split into three core components:

1. `Task`: A lightweight container that holds the target function,
(stored internally in a `functools.partial`), and its timing requirements (`timeout`, `repeat`).

2. `ThreadPool`: A custom-built worker pool utilizing `queue.Queue`.
It bypasses the heavy machinery of `concurrent.futures.ThreadPoolExecutor`
for fire-and-forget tasks, ensuring maximum throughput.

3. `Scheduler`: The orchestrator. It uses a `queue.PriorityQueue` and a `threading.Condition`
to precisely calculate time deltas and hand off tasks to the `ThreadPool` at the exact right microsecond.

## 🧪 Running Tests

To run the test suite:

```bash
uv run pytest -v
```

## 📄 License

MIT License. See LICENSE for more information.
