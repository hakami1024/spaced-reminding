import sqlite3
from contextlib import closing


# Initialize the database and create the table if it doesn't exist
def init_db():
    with sqlite3.connect('spaced_repetition.db') as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    task TEXT,
                    reminder_interval INTEGER,
                    next_reminder TIMESTAMP,
                    reminder_status TEXT DEFAULT 'active'
                )
            ''')
            conn.commit()


# Add a task to the database
def add_task(user_id, chat_id, task, interval_days, next_reminder):
    with sqlite3.connect('spaced_repetition.db') as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "INSERT INTO tasks (user_id, chat_id, task, reminder_interval, next_reminder, reminder_status) VALUES (?, ?, ?, ?, ?, 'active')",
                (user_id, chat_id, task, interval_days, next_reminder)
            )
            conn.commit()


# Get tasks due for reminders
def get_tasks_due():
    with sqlite3.connect('spaced_repetition.db') as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                f"SELECT * FROM tasks "
                f"WHERE next_reminder <= datetime('now') AND reminder_status = 'active'"
            )
            return cursor.fetchall()


# Set the status of a task (e.g., 'inactive', 'completed', etc.)
def set_status(task_id, status):
    with sqlite3.connect('spaced_repetition.db') as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "UPDATE tasks SET reminder_status = ? WHERE id = ?",
                (status, task_id)
            )
            conn.commit()


# Get the reminder interval of a specific task by its ID
def get_interval_by_id(task_id):
    with sqlite3.connect('spaced_repetition.db') as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT reminder_interval FROM tasks WHERE id = ?", (task_id,))
            current_interval = cursor.fetchone()[0]
    return current_interval


# Update the task for the next reminder and reset its status to 'active'
def update_task(task_id, interval_days, new_reminder):
    with sqlite3.connect('spaced_repetition.db') as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "UPDATE tasks SET reminder_interval = ?, next_reminder = ?, reminder_status='active' WHERE id = ?",
                (interval_days, new_reminder, task_id)
            )
            conn.commit()


# Delete a task from the database
def delete_task(task_id):
    with sqlite3.connect('spaced_repetition.db') as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
