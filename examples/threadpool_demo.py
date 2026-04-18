from schedcore import Scheduler, Task
import time


# 1. Define your tasks
def greet(name: str):
    print(f"[{time.strftime('%X')}] Hello, {name}!")


def recurring_ping():
    print(f"[{time.strftime('%X')}] Ping...")


def raise_error():
    raise ValueError("Task raised and exception")


def error_handler(exception, task):
    print(f"Task: {task} didn't execute du to an exception: {exception}")


if __name__ == "__main__":
    scheduler = Scheduler(workers=4)
    scheduler.set_error_handler(error_handler)

    scheduler.start()

    print(f"[{time.strftime('%X')}] Scheduler started.")

    task_one = Task(interval=2, repeat=False, func=greet, name="Alice")
    scheduler.schedule(task_one)

    task_two = Task(interval=1.5, repeat=True, func=recurring_ping)
    scheduler.schedule(task_two)

    task_three = Task(interval=3, repeat=False, func=raise_error)
    scheduler.schedule(task_three)

    try:
        time.sleep(6)
    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down gracefully...")
        scheduler.request_stop()
