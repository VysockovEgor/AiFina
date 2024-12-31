import sqlite3
import os
name_db = 'db/liderbord.db'
def create_database():
    conn = sqlite3.connect(name_db)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id STRING PRIMARY KEY,
            words_read INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def update_words_read(user_id, words):
    conn = sqlite3.connect(name_db)
    cursor = conn.cursor()


    cursor.execute('SELECT words_read FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        new_words = result[0] + words
        cursor.execute('UPDATE users SET words_read = ? WHERE id = ?', (new_words, user_id))
    else:
        cursor.execute('INSERT INTO users (id, words_read) VALUES (?, ?)', (user_id, words))

    conn.commit()
    conn.close()
def get_sorted_users():
    conn = sqlite3.connect(name_db)
    cursor = conn.cursor()

    # Извлекаем данные и сортируем по убыванию words_read
    cursor.execute('SELECT id, words_read FROM users ORDER BY words_read DESC')
    sorted_users = cursor.fetchall()

    conn.close()

    # Возвращаем список отсортированных пользователей
    return sorted_users

def get_user_rating(user_id):
    conn = sqlite3.connect(name_db)
    cursor = conn.cursor()

    cursor.execute('SELECT id, words_read FROM users ORDER BY words_read DESC')
    users = cursor.fetchall()

    conn.close()

    for rank, (uid, words) in enumerate(users, start=1):
        if uid == user_id:
            return words,rank, len(users)
    update_words_read(user_id, 0)
    return 0, len(users), len(users)

if os.path.exists(name_db):
    create_database()
#update_words_read('@Arsiik228', 2500)