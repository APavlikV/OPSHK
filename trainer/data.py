import logging
import os
import psycopg2
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

MOVES = [
    ("ДЗ", "ТР"), ("ДЗ", "СС"), ("ДЗ", "ГДН"),
    ("ТР", "ДЗ"), ("ТР", "СС"), ("ТР", "ТР"), ("ТР", "ГДН"),
    ("СС", "ДЗ"), ("СС", "СС"), ("СС", "ТР")
]

DEFENSE_MOVES = {
    "Гедан барай": {
        "control_defense": ["ТР", "ДЗ"],
        "counterattack": ["СС", "ТР", "ГДН"],
        "attack_defense": ["СС", "ТР", "ГДН"]
    },
    "Аге уке": {
        "control_defense": ["СС"],
        "counterattack": ["СС", "ТР"],
        "attack_defense": ["ДЗ"]
    },
    "Сото уке": {
        "control_defense": ["СС", "ТР"],
        "counterattack": ["СС", "ДЗ"],
        "attack_defense": ["СС", "ТР", "ДЗ"]
    },
    "Учи уке": {
        "control_defense": ["СС"],
        "counterattack": ["ТР", "ДЗ"],
        "attack_defense": ["СС", "ТР", "ДЗ"]
    }
}

CONTROL_PHRASES = {
    "ДЗ": ["метит в голову", "целится в нос", "хочет захватить волосы"],
    "СС": ["метит в печень", "целится в центр", "хочет пробить пузо"],
    "ТР": ["метит в трахею", "целится в грудь", "идёт за сердцем"]
}

ATTACK_PHRASES = {
    "ДЗ": ["бьёт в нос", "атакует челюсть", "наносит удар в голову"],
    "СС": ["бьёт в печень", "атакует селезёнку", "идёт в центр"],
    "ТР": ["бьёт в трахею", "атакует грудь", "целит в сердце"],
    "ГДН": ["бьёт по ногам", "атакует живот", "цели в пах"]
}

DEFENSE_PHRASES = {
    "Гедан барай": ["ставит Гедан барай", "закрывает Гедан барай"],
    "Аге уке": ["подбрасывает Аге уке", "выставляет Аге уке"],
    "Сото уке": ["ставит Сото уке", "блокирует Сото уке"],
    "Учи уке": ["ставит Учи уке", "держит Учи уке"]
}

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            connect_timeout=5
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                fighter_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS fights (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                fight_type VARCHAR(20),
                score INT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS profiles (
                user_id BIGINT PRIMARY KEY,
                life INT DEFAULT 100,
                strength INT DEFAULT 10,
                agility INT DEFAULT 5,
                spirit INT DEFAULT 1,
                belt VARCHAR(20) DEFAULT 'Yellow'
            );
        """)
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

def save_fighter(user_id: int, fighter_name: str):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, fighter_name)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET fighter_name = EXCLUDED.fighter_name;
        """, (user_id, fighter_name))
        cursor.execute("""
            INSERT INTO profiles (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING;
        """, (user_id,))
        conn.commit()
        logger.info(f"Saved fighter: {user_id}, {fighter_name}")
    except Exception as e:
        logger.error(f"Save fighter failed: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

def save_fight(user_id: int, fight_type: str, score: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fights (user_id, fight_type, score)
            VALUES (%s, %s, %s);
        """, (user_id, fight_type, score))
        conn.commit()
        logger.info(f"Saved fight: {user_id}, {fight_type}, {score}")
    except Exception as e:
        logger.error(f"Save fight failed: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()
