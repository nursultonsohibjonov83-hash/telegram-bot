# -*- coding: utf-8 -*-
import sqlite3
from datetime import date
from config import DB_NAME

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id    INTEGER PRIMARY KEY,
        username   TEXT,
        full_name  TEXT,
        real_name  TEXT,
        group_name TEXT,
        phone      TEXT,
        joined     TEXT DEFAULT CURRENT_TIMESTAMP,
        is_blocked INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS results (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER,
        subject    TEXT,
        total_q    INTEGER,
        correct    INTEGER,
        score      REAL,
        finished_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily (
        user_id   INTEGER,
        test_date TEXT,
        done      INTEGER DEFAULT 0,
        score     REAL DEFAULT 0,
        PRIMARY KEY(user_id, test_date)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS rewards (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER,
        score      REAL,
        subject    TEXT,
        phone      TEXT,
        method     TEXT,
        status     TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        paid_at    TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        subject    TEXT,
        question   TEXT,
        option_a   TEXT,
        option_b   TEXT,
        option_c   TEXT,
        option_d   TEXT,
        answer     TEXT,
        added_by   INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def add_user(user_id, username, full_name):
    conn = get_conn()
    conn.execute('INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)',
                 (user_id, username, full_name))
    conn.commit()
    conn.close()

def update_user_profile(user_id, real_name, group_name):
    conn = get_conn()
    conn.execute('UPDATE users SET real_name=?, group_name=? WHERE user_id=?',
                 (real_name, group_name, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_conn()
    user = conn.execute('SELECT * FROM users WHERE user_id=?', (user_id,)).fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_conn()
    users = conn.execute('SELECT * FROM users WHERE is_blocked=0').fetchall()
    conn.close()
    return users

def block_user(user_id):
    conn = get_conn()
    conn.execute('UPDATE users SET is_blocked=1 WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()

def save_result(user_id, subject, total_q, correct, score):
    conn = get_conn()
    conn.execute('INSERT INTO results (user_id, subject, total_q, correct, score) VALUES (?,?,?,?,?)',
                 (user_id, subject, total_q, correct, score))
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = get_conn()
    stats = conn.execute('''
        SELECT COUNT(*) AS total_tests,
               ROUND(MAX(score),1) AS best_score,
               ROUND(AVG(score),1) AS avg_score,
               SUM(correct) AS total_correct,
               SUM(total_q) AS total_questions
        FROM results WHERE user_id=?
    ''', (user_id,)).fetchone()
    conn.close()
    return stats

def get_subject_stats(user_id, subject):
    conn = get_conn()
    stats = conn.execute('''
        SELECT COUNT(*) AS cnt, ROUND(AVG(score),1) AS avg_s, ROUND(MAX(score),1) AS best_s
        FROM results WHERE user_id=? AND subject=?
    ''', (user_id, subject)).fetchone()
    conn.close()
    return stats

def get_leaderboard(limit=10):
    conn = get_conn()
    rows = conn.execute('''
        SELECT u.real_name, u.full_name, u.username, u.group_name,
               ROUND(MAX(r.score),1) AS best,
               ROUND(AVG(r.score),1) AS avg,
               COUNT(r.id) AS cnt
        FROM results r
        JOIN users u ON u.user_id = r.user_id
        WHERE u.is_blocked=0
        GROUP BY r.user_id
        ORDER BY best DESC, avg DESC
        LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return rows

def daily_done(user_id):
    today = date.today().isoformat()
    conn = get_conn()
    row = conn.execute('SELECT done FROM daily WHERE user_id=? AND test_date=?', (user_id, today)).fetchone()
    conn.close()
    return row and row['done'] == 1

def mark_daily_done(user_id, score):
    today = date.today().isoformat()
    conn = get_conn()
    conn.execute('INSERT OR REPLACE INTO daily (user_id, test_date, done, score) VALUES (?,?,1,?)',
                 (user_id, today, score))
    conn.commit()
    conn.close()

def get_questions(subject=None, limit=None):
    import random
    conn = get_conn()
    if subject:
        rows = conn.execute('SELECT * FROM questions WHERE subject=?', (subject,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM questions').fetchall()
    conn.close()
    qs = [dict(r) for r in rows]
    if qs: random.shuffle(qs)
    return qs[:limit] if limit else qs

def get_subjects():
    conn = get_conn()
    rows = conn.execute('SELECT DISTINCT subject FROM questions ORDER BY subject').fetchall()
    conn.close()
    return [r['subject'] for r in rows]

def add_question(subject, question, a, b, c, d, answer, admin_id):
    conn = get_conn()
    conn.execute('''INSERT INTO questions (subject, question, option_a, option_b, option_c, option_d, answer, added_by)
                    VALUES (?,?,?,?,?,?,?,?)''', (subject, question, a, b, c, d, answer.upper(), admin_id))
    conn.commit()
    conn.close()

def delete_question(q_id):
    conn = get_conn()
    conn.execute('DELETE FROM questions WHERE id=?', (q_id,))
    conn.commit()
    conn.close()

def get_questions_count():
    conn = get_conn()
    row = conn.execute('SELECT COUNT(*) AS cnt FROM questions').fetchone()
    conn.close()
    return row['cnt']

def add_reward_request(user_id, score, subject, phone, method):
    conn = get_conn()
    conn.execute('INSERT INTO rewards (user_id, score, subject, phone, method) VALUES (?,?,?,?,?)',
                 (user_id, score, subject, phone, method))
    conn.commit()
    conn.close()

def get_pending_rewards():
    conn = get_conn()
    rows = conn.execute('''
        SELECT r.*, u.full_name, u.real_name, u.username, u.group_name
        FROM rewards r JOIN users u ON u.user_id=r.user_id
        WHERE r.status='pending' ORDER BY r.created_at
    ''').fetchall()
    conn.close()
    return rows

def mark_reward_paid(reward_id):
    conn = get_conn()
    conn.execute("UPDATE rewards SET status='paid', paid_at=CURRENT_TIMESTAMP WHERE id=?", (reward_id,))
    conn.commit()
    conn.close()

def already_claimed_reward(user_id, subject):
    conn = get_conn()
    row = conn.execute('''SELECT id FROM rewards WHERE user_id=? AND subject=?
                          AND status IN ('pending','paid') LIMIT 1''', (user_id, subject)).fetchone()
    conn.close()
    return row is not None
