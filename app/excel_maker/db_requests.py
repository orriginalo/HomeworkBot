from rich import print
import sqlite3 as sql

def get_homeworks():
    with sql.connect("Database.db") as conn:
        cursor = conn.execute("SELECT id, from_date, subject, task, to_date FROM homeworks")
        result = cursor.fetchall()
    return result

def get_users():
    with sql.connect("Database.db") as conn:
        cursor = conn.execute("SELECT id, role, username FROM users")
        result = cursor.fetchall()
    return result

def get_schedule():
    with sql.connect("Database.db") as conn:
        cursor = conn.execute("SELECT timestamp, subject, weeknumber FROM schedule ORDER BY timestamp")
        result = cursor.fetchall()
    return result

# print(get_homeworks())
# print(get_users())
# print(get_schedule())