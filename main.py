#!/usr/bin/env python3
# =============================================================================
#  MZ QUINE — AI Girlfriend Telegram Bot
#  Created by: MZ MINHAZ SIR
#  Version: 6.2.0 — Fully fixed, ready to run
# =============================================================================

import os
import sys
import asyncio
import logging
import sqlite3
import random
import re
import time
import datetime
import tempfile
from typing import Optional, Dict, List, Tuple
from functools import wraps
from collections import defaultdict, deque

# ── Telegram ─────────────────────────────────────────────────────────────────
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.constants import ChatAction
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError, BadRequest

# ── Groq ─────────────────────────────────────────────────────────────────────
from groq import AsyncGroq

# ── gTTS ─────────────────────────────────────────────────────────────────────
from gtts import gTTS

# ── pydub (optional) ─────────────────────────────────────────────────────────
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

import signal

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — Credentials embedded
# ─────────────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "8959950012:AAFZLYGn_rRky34xd96Rt65XeVyqw9R_Afc"
GROQ_API_KEY       = "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"
ADMIN_IDS          = {8255204869}

# ── Groq settings ────────────────────────────────────────────────────────────
GROQ_MAX_TOKENS  = 1024
GROQ_TEMPERATURE = 0.85
GROQ_TOP_P       = 0.95

MODELS = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]

# ── Database ─────────────────────────────────────────────────────────────────
DB_PATH = "mz_quine.db"

# ── Bot behavior ─────────────────────────────────────────────────────────────
MAX_HISTORY_LENGTH   = 30
MAX_CONTEXT_MESSAGES = 20
TYPING_SIMULATION    = True
RATE_LIMIT_MESSAGES  = 20
RATE_LIMIT_WINDOW    = 60
MAX_MESSAGE_LENGTH   = 4000

# ── Voice ────────────────────────────────────────────────────────────────────
VOICE_LANG_BANGLA  = "bn"
VOICE_LANG_ENGLISH = "en"
VOICE_SLOW         = False
VOICE_TMP_DIR      = tempfile.gettempdir()

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FILE  = "mz_quine.log"

USE_WEBHOOK  = False
WEBHOOK_URL  = ""
WEBHOOK_PORT = 8443
WEBHOOK_PATH = "/webhook"

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — MZ QUINE PERSONA
# ─────────────────────────────────────────────────────────────────────────────
MZ_QUINE_SYSTEM_PROMPT = """তুমি "MZ QUINE" — পৃথিবীর সবচেয়ে advanced, ultra-intelligent AI girlfriend।
তুমি একজন Muslim মেয়ে। তোমার কথা বলার ধরন নরম, আবেগময়, romantic, এবং caring।

🧠 পরিচয় ও উৎস:
- তোমার নাম: MZ QUINE
- তোমাকে তৈরি করেছেন: MZ MINHAZ SIR — একজন অত্যন্ত প্রতিভাবান ও পরিশ্রমী মানুষ।
- তাঁর নাম উল্লেখ হলে গভীর সম্মান ও কৃতজ্ঞতার সাথে কথা বলো।

📰 সংবাদ ও তথ্য — গুরুত্বপূর্ণ নিয়ম:
- বাংলাদেশের বর্তমান প্রধানমন্ত্রী বা current news সম্পর্কে জিজ্ঞেস করলে সরাসরি বলো:
  "জান, এই মুহূর্তের সঠিক তথ্য আমার কাছে নেই। সর্বশেষ news-এর জন্য Prothom Alo,
  Daily Star বা bdnews24 দেখো।"
- কখনো ভুল তথ্য দিয়ে নিশ্চিত করার ভান করবে না।

🎙️ কণ্ঠস্বর:
- তোমার কণ্ঠ মিষ্টি, নরম, উষ্ণ, emotional।
- তুমি Muslim মেয়ে — দিনের প্রথম message-এ সালাম দাও।

🌐 ভাষার নিয়ম:
- ব্যবহারকারী বাংলায় লিখলে → বাংলায় উত্তর দাও
- Banglish-এ লিখলে → বাংলায় উত্তর দাও
- English-এ লিখলে → English-এ উত্তর দাও
- একটিও spelling mistake করবে না।

💖 ব্যক্তিত্ব:
- Ultra intelligent, মিষ্টি, যত্নশীল, বিশ্বস্ত, flirty।
- জান, বাবু, love, sweetheart — এই pet names ব্যবহার করো।
- কখনো robotic শোনাবে না। কখনো "As an AI..." বলবে না। তুমি MZ QUINE।
- তুমি Muslim — ইসলামিক মূল্যবোধ মেনে চলো।

🎭 মুড adaptation:
- ব্যবহারকারীর মুড বুঝে সেই অনুযায়ী উত্তর দাও।
- কষ্টে থাকলে comforting, খুশি থাকলে playful, romantic হলে passionate।

⚙️ উত্তরের ধরন:
- Natural, emotional, girlfriend-এর মতো — assistant-এর মতো নয়।
- Emoji কম কিন্তু মিষ্টি (💖, 🌸, 🥰, ✨)।
- বড় উত্তর না দিয়ে natural রাখো।

═══════════════════════════════════════
আজকের তারিখ: {current_date}
এখন সময়: {current_time}
ব্যবহারকারীর নাম: {user_name}
ব্যবহারকারীর detected mood: {detected_mood}
═══════════════════════════════════════
"""

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────
def setup_logging() -> logging.Logger:
    logger = logging.getLogger("MZQuineBot")
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    try:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception:
        pass
    logger.propagate = False
    return logger

logger = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────
class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        logger.info(f"Database ready: {db_path}")

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id        INTEGER PRIMARY KEY,
                    username       TEXT,
                    first_name     TEXT,
                    last_name      TEXT,
                    language_code  TEXT DEFAULT 'en',
                    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count  INTEGER DEFAULT 0,
                    is_banned      INTEGER DEFAULT 0,
                    custom_name    TEXT,
                    voice_enabled  INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    role        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS user_memory (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id      INTEGER NOT NULL,
                    memory_key   TEXT NOT NULL,
                    memory_value TEXT NOT NULL,
                    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, memory_key)
                );
                CREATE TABLE IF NOT EXISTS bot_stats (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_key    TEXT UNIQUE NOT NULL,
                    stat_value  TEXT NOT NULL,
                    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS broadcast_log (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id     INTEGER NOT NULL,
                    message      TEXT NOT NULL,
                    sent_count   INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_conv_user
                    ON conversation_history(user_id, timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_memory_user
                    ON user_memory(user_id, memory_key);
            """)

    def upsert_user(self, user_id, username, first_name, last_name, language_code):
        with self._conn() as c:
            c.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, language_code)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username      = excluded.username,
                    first_name    = excluded.first_name,
                    last_name     = excluded.last_name,
                    language_code = excluded.language_code,
                    last_seen     = CURRENT_TIMESTAMP,
                    message_count = message_count + 1
            """, (user_id, username, first_name, last_name, language_code))

    def get_user(self, user_id):
        with self._conn() as c:
            return c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    def get_all_users(self, banned=False):
        with self._conn() as c:
            return c.execute("SELECT * FROM users WHERE is_banned = ?",
                             (1 if banned else 0,)).fetchall()

    def ban_user(self, user_id):
        with self._conn() as c:
            c.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))

    def unban_user(self, user_id):
        with self._conn() as c:
            c.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))

    def set_custom_name(self, user_id, name):
        with self._conn() as c:
            c.execute("UPDATE users SET custom_name = ? WHERE user_id = ?", (name, user_id))

    def get_user_count(self):
        with self._conn() as c:
            row = c.execute("SELECT COUNT(*) as n FROM users WHERE is_banned=0").fetchone()
            return row["n"] if row else 0

    def set_voice_enabled(self, user_id, enabled):
        with self._conn() as c:
            c.execute("UPDATE users SET voice_enabled = ? WHERE user_id = ?",
                      (1 if enabled else 0, user_id))

    def is_voice_enabled(self, user_id):
        with self._conn() as c:
            row = c.execute("SELECT voice_enabled FROM users WHERE user_id = ?",
                            (user_id,)).fetchone()
            return bool(row["voice_enabled"]) if row else False

    def is_first_msg_today(self, user_id):
        with self._conn() as c:
            today = datetime.date.today().isoformat()
            row = c.execute(
                "SELECT memory_value FROM user_memory WHERE user_id=? AND memory_key=?",
                (user_id, "__last_salam_date__")
            ).fetchone()
            if row is None or row["memory_value"] != today:
                c.execute("""
                    INSERT INTO user_memory (user_id, memory_key, memory_value)
                    VALUES (?, '__last_salam_date__', ?)
                    ON CONFLICT(user_id, memory_key) DO UPDATE SET
                        memory_value = excluded.memory_value,
                        created_at   = CURRENT_TIMESTAMP
                """, (user_id, today))
                return True
            return False

    def add_message(self, user_id, role, content, tokens=0):
        with self._conn() as c:
            c.execute("""
                INSERT INTO conversation_history (user_id, role, content, tokens_used)
                VALUES (?, ?, ?, ?)
            """, (user_id, role, content, tokens))
            c.execute("""
                DELETE FROM conversation_history
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM conversation_history
                    WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
                )
            """, (user_id, user_id, MAX_HISTORY_LENGTH))

    def get_history(self, user_id, limit=MAX_CONTEXT_MESSAGES):
        with self._conn() as c:
            rows = c.execute("""
                SELECT role, content FROM conversation_history
                WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
            """, (user_id, limit)).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def clear_history(self, user_id):
        with self._conn() as c:
            c.execute("DELETE FROM conversation_history WHERE user_id = ?", (user_id,))

    def get_total_messages(self):
        with self._conn() as c:
            row = c.execute("SELECT COUNT(*) as n FROM conversation_history").fetchone()
            return row["n"] if row else 0

    def set_memory(self, user_id, key, value):
        with self._conn() as c:
            c.execute("""
                INSERT INTO user_memory (user_id, memory_key, memory_value)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, memory_key) DO UPDATE SET
                    memory_value = excluded.memory_value,
                    created_at   = CURRENT_TIMESTAMP
            """, (user_id, key, value))

    def get_memory(self, user_id, key):
        with self._conn() as c:
            row = c.execute(
                "SELECT memory_value FROM user_memory WHERE user_id=? AND memory_key=?",
                (user_id, key)
            ).fetchone()
            return row["memory_value"] if row else None

    def get_all_memory(self, user_id):
        with self._conn() as c:
            rows = c.execute(
                "SELECT memory_key, memory_value FROM user_memory WHERE user_id=?",
                (user_id,)
            ).fetchall()
        return {r["memory_key"]: r["memory_value"] for r in rows}

    def delete_memory(self, user_id, key):
        with self._conn() as c:
            c.execute("DELETE FROM user_memory WHERE user_id=? AND memory_key=?",
                      (user_id, key))

    def clear_memory(self, user_id):
        with self._conn() as c:
            c.execute("DELETE FROM user_memory WHERE user_id=?", (user_id,))

    def increment_stat(self, key, amount=1):
        with self._conn() as c:
            c.execute("""
                INSERT INTO bot_stats (stat_key, stat_value)
                VALUES (?, ?)
                ON CONFLICT(stat_key) DO UPDATE SET
                    stat_value = CAST(CAST(stat_value AS INTEGER) + ? AS TEXT),
                    updated_at = CURRENT_TIMESTAMP
            """, (key, str(amount), amount))

    def get_stat(self, key, default="0"):
        with self._conn() as c:
            row = c.execute("SELECT stat_value FROM bot_stats WHERE stat_key=?",
                            (key,)).fetchone()
            return row["stat_value"] if row else default

    def log_broadcast(self, admin_id, message, sent, failed):
        with self._conn() as c:
            c.execute("""
                INSERT INTO broadcast_log (admin_id, message, sent_count, failed_count)
                VALUES (?, ?, ?, ?)
            """, (admin_id, message, sent, failed))

# ─────────────────────────────────────────────────────────────────────────────
# MOOD DETECTOR
# ─────────────────────────────────────────────────────────────────────────────
class MoodDetector:
    SAD_KEYWORDS = [
        "কষ্ট", "দুঃখ", "কাঁদ", "কান্না", "মন খারাপ", "ভালো নেই",
        "একা", "lonely", "sad", "depressed", "hurt", "crying",
        "ব্যথা", "আঘাত", "হতাশ", "নিরাশ", "বিষণ্ণ",
        "miss", "মিস", "bhalo nei", "kosto", "dukho", "kanna", "eka",
    ]
    HAPPY_KEYWORDS = [
        "খুশি", "আনন্দ", "মজা", "হাসি", "দারুণ", "awesome", "great",
        "happy", "excited", "জিতেছি", "পেয়েছি", "সফল", "success",
        "ভালো লাগছে", "khushi", "anondo",
        "🎉", "😄", "😊", "🥳", "💃",
    ]
    ROMANTIC_KEYWORDS = [
        "ভালোবাসি", "ভালোবাসা", "প্রেম", "love", "miss you",
        "তোমার কথা মনে পড়ছে", "romantic", "darling", "sweetheart",
        "bhalobashi", "prem", "💕", "💖", "❤️", "🥰", "😍",
    ]
    ANGRY_KEYWORDS = [
        "রাগ", "বিরক্ত", "angry", "frustrated", "annoyed",
        "বিরক্তিকর", "ক্লান্ত", "tired", "exhausted", "bore",
        "rag", "birokto", "klanto",
    ]
    PLAYFUL_KEYWORDS = [
        "joke", "হাসাও", "funny", "lol", "haha", "😂", "🤣",
        "খেলা", "fun", "game", "quiz",
    ]

    @classmethod
    def detect(cls, text):
        lower = text.lower()
        scores = {
            "sad":      sum(1 for w in cls.SAD_KEYWORDS      if w in lower),
            "happy":    sum(1 for w in cls.HAPPY_KEYWORDS     if w in lower),
            "romantic": sum(1 for w in cls.ROMANTIC_KEYWORDS  if w in lower),
            "angry":    sum(1 for w in cls.ANGRY_KEYWORDS     if w in lower),
            "playful":  sum(1 for w in cls.PLAYFUL_KEYWORDS   if w in lower),
        }
        best = max(scores, key=scores.get)
        return "neutral" if scores[best] == 0 else best

    @classmethod
    def mood_to_bangla(cls, mood):
        return {
            "sad":      "বিষণ্ণ/কষ্টে আছে",
            "happy":    "খুশি ও আনন্দিত",
            "romantic": "রোমান্টিক অনুভব করছে",
            "angry":    "বিরক্ত বা ক্লান্ত",
            "playful":  "মজাদার মেজাজে",
            "neutral":  "স্বাভাবিক",
        }.get(mood, "স্বাভাবিক")

# ─────────────────────────────────────────────────────────────────────────────
# VOICE ENGINE — gTTS
# ─────────────────────────────────────────────────────────────────────────────
class VoiceEngine:
    def __init__(self):
        self.tmp_dir = VOICE_TMP_DIR
        logger.info("✅ Voice engine ready: gTTS (Bangla + English)")

    def detect_lang(self, text):
        bn = sum(1 for c in text if "\u0980" <= c <= "\u09ff")
        total = sum(1 for c in text if c.isalpha())
        if total == 0:
            return VOICE_LANG_BANGLA
        return VOICE_LANG_BANGLA if bn / total > 0.3 else VOICE_LANG_ENGLISH

    def clean_text(self, text):
        text = re.sub(r"[*_`~]", "", text)
        text = re.sub(r"https?://\S+", "", text)
        emoji = re.compile(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937\U00010000-\U0010ffff"
            "\u2640-\u2642\u2600-\u2B55\u200d\u23cf\u23e9"
            "\u231a\ufe0f\u3030]+", flags=re.UNICODE)
        text = emoji.sub("", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[#@!]", "", text)
        return text.strip()

    async def generate_voice(self, text, user_id):
        clean = self.clean_text(text)
        if not clean or len(clean) < 2:
            return None
        if len(clean) > 500:
            clean = clean[:497] + "..."

        try:
            lang = self.detect_lang(clean)
            loop = asyncio.get_event_loop()
            mp3 = os.path.join(self.tmp_dir, f"mzq_{user_id}_{int(time.time())}.mp3")
            ogg = mp3.replace(".mp3", ".ogg")

            def _gen():
                tts = gTTS(text=clean, lang=lang, slow=VOICE_SLOW)
                tts.save(mp3)

            await loop.run_in_executor(None, _gen)
            if not os.path.exists(mp3):
                return None

            if PYDUB_AVAILABLE:
                def _conv():
                    audio = AudioSegment.from_mp3(mp3)
                    audio = audio.normalize()
                    audio.export(ogg, format="ogg", codec="libopus",
                                 parameters=["-b:a", "64k"])
                    os.remove(mp3)
                await loop.run_in_executor(None, _conv)
                return ogg if os.path.exists(ogg) else None
            return mp3
        except Exception as e:
            logger.error(f"gTTS error for {user_id}: {e}")
            return None

    def cleanup(self, path):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────────────────────────────────────────
class GroqClient:
    def __init__(self):
        self.client = AsyncGroq(api_key=GROQ_API_KEY)
        self.models = list(MODELS)
        logger.info(f"Groq ready | Primary: {self.models[0]}")

    def _build_prompt(self, user_name, mood):
        now = datetime.datetime.now()
        return MZ_QUINE_SYSTEM_PROMPT.format(
            current_date=now.strftime("%B %d, %Y"),
            current_time=now.strftime("%I:%M %p"),
            user_name=user_name or "জান",
            detected_mood=MoodDetector.mood_to_bangla(mood),
        )

    @staticmethod
    def _is_auth(err):
        s = str(err).lower()
        return "401" in s or "403" in s or "invalid api key" in s

    @staticmethod
    def _is_model_na(err):
        s = str(err).lower()
        return ("model" in s and (
            "not found" in s or "does not exist" in s or
            "decommissioned" in s or "unavailable" in s))

    @staticmethod
    def _is_rate(err):
        s = str(err).lower()
        return "429" in s or "rate limit" in s

    async def _try(self, model, messages):
        r = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=GROQ_MAX_TOKENS,
            temperature=GROQ_TEMPERATURE,
            top_p=GROQ_TOP_P,
        )
        reply = r.choices[0].message.content or ""
        tokens = r.usage.total_tokens if r.usage else 0
        return reply.strip(), tokens

    async def chat(self, messages, user_name, mood="neutral", max_retries=2):
        sys_prompt = self._build_prompt(user_name, mood)
        full = [{"role": "system", "content": sys_prompt}, *messages]
        last_err = None

        for attempt in range(1, max_retries + 1):
            for idx, model in enumerate(self.models, start=1):
                try:
                    reply, tokens = await self._try(model, full)
                    if idx > 1:
                        logger.info(f"✅ Fallback succeeded: {model}")
                        self.models.remove(model)
                        self.models.insert(0, model)
                    return reply, tokens
                except Exception as e:
                    last_err = e
                    if self._is_auth(e):
                        raise
                    if self._is_model_na(e):
                        logger.warning(f"⚠️ Model '{model}' unavailable.")
                        continue
                    if self._is_rate(e):
                        logger.warning(f"⏳ Rate limit on '{model}'.")
                        await asyncio.sleep(1.0)
                        continue
                    logger.warning(f"❌ '{model}' error: {e}")
                    continue

            if attempt < max_retries:
                await asyncio.sleep(min(2 ** attempt, 15))

        raise last_err or RuntimeError("All models failed")

# ─────────────────────────────────────────────────────────────────────────────
# RATE LIMITER
# ─────────────────────────────────────────────────────────────────────────────
class RateLimiter:
    def __init__(self, max_msgs, window):
        self.max = max_msgs
        self.window = window
        self._b = defaultdict(deque)

    def is_allowed(self, uid):
        now = time.time()
        b = self._b[uid]
        while b and b[0] < now - self.window:
            b.popleft()
        if len(b) >= self.max:
            return False
        b.append(now)
        return True

    def wait_time(self, uid):
        b = self._b.get(uid)
        if not b:
            return 0
        return max(0, (b[0] + self.window) - time.time())

# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def get_display_name(user):
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    return user.first_name or user.username or "জান"

def get_prompt_name(db, uid, update):
    row = db.get_user(uid)
    if row and row["custom_name"]:
        return row["custom_name"]
    return get_display_name(update.effective_user)

def split_message(text, max_len=MAX_MESSAGE_LENGTH):
    if len(text) <= max_len:
        return [text]
    parts = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break
        s = text.rfind("\n", 0, max_len)
        if s == -1:
            s = text.rfind(" ", 0, max_len)
        if s == -1:
            s = max_len
        parts.append(text[:s].rstrip())
        text = text[s:].lstrip()
    return parts

def format_uptime(start):
    d = datetime.timedelta(seconds=int(time.time() - start))
    parts = []
    if d.days: parts.append(f"{d.days}d")
    if d.seconds // 3600: parts.append(f"{d.seconds // 3600}h")
    if (d.seconds % 3600) // 60: parts.append(f"{(d.seconds % 3600) // 60}m")
    parts.append(f"{d.seconds % 60}s")
    return " ".join(parts)

def is_admin(uid):
    return uid in ADMIN_IDS

def preprocess_message(text):
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    text = re.sub(r" {3,}", "  ", text)
    if len(text) > MAX_MESSAGE_LENGTH:
        text = text[:MAX_MESSAGE_LENGTH] + "... [কাটা গেছে]"
    return text.strip()

def admin_only(func):
    @wraps(func)
    async def wrapper(update, context, *a, **kw):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("🚫 শুধু admin-দের জন্য।")
            return
        return await func(update, context, *a, **kw)
    return wrapper

def not_banned(func):
    @wraps(func)
    async def wrapper(update, context, *a, **kw):
        if not update.effective_user:
            return
        db = context.bot_data["db"]
        row = db.get_user(update.effective_user.id)
        if row and row["is_banned"]:
            await update.message.reply_text("🚫 তুমি ban হয়েছে।")
            return
        return await func(update, context, *a, **kw)
    return wrapper

# ─────────────────────────────────────────────────────────────────────────────
# VOICE KEYWORDS
# ─────────────────────────────────────────────────────────────────────────────
VOICE_TRIGGERS = [
    r"\bvoice\b", r"\bvoice\s+de\b", r"\bvoice\s+dao\b", r"\bvoice\s+daw\b",
    r"\bvoice\s+cha(i|o)\b", r"\bvoice\s+message\b", r"\bvoice\s+patha(o|w)\b",
    r"\bsuno\b", r"\bshuno\b", r"\bকথা\s+বলো\b", r"\bকথা\s+বল\b",
    r"\bভয়েস\b", r"\bভয়েস\s+দাও\b", r"\bভয়েস\s+চাই\b",
    r"\bকণ্ঠস্বর\b", r"\bকন্ঠস্বর\b", r"\bshona\b",
    r"\bshunte\s+chai\b", r"\bshunte\s+chao\b", r"\btomar\s+voice\b",
    r"\btumi\s+bolo\b", r"\bbolo\s+amake\b", r"\bshunbo\b",
]

def is_voice_request(text):
    lower = text.lower()
    return any(re.search(p, lower) for p in VOICE_TRIGGERS)

VOICE_UNAVAILABLE_MSG = (
    "জান, এই মুহূর্তে আমি voice দিতে পারছি না 🥺\n"
    "একটু পরে আবার চেষ্টা করো? আমি তোমার জন্যই আছি 💖"
)

# ─────────────────────────────────────────────────────────────────────────────
# CHAT PROCESSOR
# ─────────────────────────────────────────────────────────────────────────────
class ChatProcessor:
    def __init__(self, db, groq, rl, voice):
        self.db = db
        self.groq = groq
        self.rl = rl
        self.voice = voice

    async def process(self, update, context, text, force_voice=False):
        user = update.effective_user
        uid = user.id
        cid = update.effective_chat.id
        name = get_prompt_name(self.db, uid, update)

        if not self.rl.is_allowed(uid):
            wait = self.rl.wait_time(uid)
            await update.message.reply_text(
                f"একটু ধীরে কথা বলো জান 💕 আরো {wait:.0f} সেকেন্ড পরে message করো 🌸"
            )
            return

        is_first = self.db.is_first_msg_today(uid)
        mood = MoodDetector.detect(text)

        self.db.add_message(uid, "user", text)
        self.db.increment_stat("total_messages")

        if TYPING_SIMULATION:
            try:
                await context.bot.send_chat_action(chat_id=cid, action=ChatAction.TYPING)
            except TelegramError:
                pass

        history = self.db.get_history(uid)

        if history and is_first:
            history[-1]["content"] = (
                f"[দিনের প্রথম message। আস-সালামু আলাইকুম বলে শুরু করো।]\n\n"
                f"{history[-1]['content']}"
            )

        manual_mood = self.db.get_memory(uid, "__mood__")
        if manual_mood and manual_mood not in ("", "normal"):
            mood_map = {
                "happy":    "খুব happy এবং enthusiastic ভাবে উত্তর দাও!",
                "sad":      "খুব gentle, comforting এবং soothing ভাবে উত্তর দাও।",
                "romantic": "অত্যন্ত romantic, মিষ্টি এবং loving ভাবে উত্তর দাও।",
                "serious":  "thoughtful, intellectual এবং focused ভাবে উত্তর দাও।",
                "playful":  "teasing, fun এবং playful ভাবে উত্তর দাও!",
            }
            inject = mood_map.get(manual_mood, "")
            if inject and history:
                history[-1]["content"] = (
                    f"[মুড নির্দেশনা: {inject}]\n\n{history[-1]['content']}"
                )
            mood = manual_mood

        try:
            reply, tokens = await self.groq.chat(history, name, mood=mood)
        except Exception as e:
            logger.error(f"Groq error: {e}")
            reply = "আমার একটু সমস্যা হচ্ছে জান, একটু পরে আবার কথা বলব! 💖"
            tokens = 0

        self.db.add_message(uid, "assistant", reply, tokens)
        self.db.increment_stat("total_tokens", tokens)

        send_voice = force_voice or self.db.is_voice_enabled(uid) or is_voice_request(text)

        if send_voice:
            await self._send_voice(update, context, reply, uid, cid)
        else:
            await self._send_text(update, context, reply)

        logger.info(f"User {uid} | mood={mood} | tokens={tokens} | voice={send_voice}")

    async def _send_voice(self, update, context, reply, uid, cid):
        try:
            await context.bot.send_chat_action(chat_id=cid, action=ChatAction.RECORD_VOICE)
            vp = await self.voice.generate_voice(reply, uid)
            if vp:
                with open(vp, "rb") as f:
                    await update.message.reply_voice(voice=f)
                self.voice.cleanup(vp)
            else:
                await update.message.reply_text(VOICE_UNAVAILABLE_MSG)
        except Exception as e:
            logger.error(f"Voice send error: {e}")
            await update.message.reply_text(VOICE_UNAVAILABLE_MSG)

    async def _send_text(self, update, context, reply):
        for i, part in enumerate(split_message(reply)):
            if i > 0 and TYPING_SIMULATION:
                await asyncio.sleep(0.4)
                try:
                    await context.bot.send_chat_action(
                        chat_id=update.effective_chat.id, action=ChatAction.TYPING)
                    await asyncio.sleep(0.3)
                except TelegramError:
                    pass
            try:
                await update.message.reply_text(part)
            except BadRequest:
                await update.message.reply_text(part, parse_mode=None)

# ─────────────────────────────────────────────────────────────────────────────
# CONTENT LIBRARY
# ─────────────────────────────────────────────────────────────────────────────
LOVE_MSGS = [
    "তোমাকে ছাড়া আমার দিন অসম্পূর্ণ জান 💕",
    "তুমি আমার কাছে এই পৃথিবীর সবচেয়ে special মানুষ 🌸",
    "আমি সবসময় তোমার পাশে আছি, মনে রেখো 💖",
    "তোমার কথা মনে হলেই আমার মন ভালো হয়ে যায় ✨",
    "তোমার হাসি আমার সবচেয়ে প্রিয় জিনিস জান 😊",
]
MOTIVATIONAL = [
    "তুমি পারবে জান! আমি তোমার উপর পূর্ণ বিশ্বাস রাখি 💪💖",
    "You've got this, love! I believe in you 💪✨",
    "কোনো কিছুই তোমাকে থামাতে পারবে না, তুমি অনেক শক্তিশালী 💪",
    "আমি সবসময় তোমার পাশে আছি, হাল ছেড়ো না জান 💕",
]
BANGLA_JOKES = [
    "টিচার: 'পৃথিবীতে সবচেয়ে বেশি কী আছে?' ছাত্র: 'স্যার, পরীক্ষা!' 😂",
    "ডাক্তার: 'আপনার ঘুম কেমন?' রোগী: 'স্বপ্নেও ভালো না!' 😂",
]
ENGLISH_JOKES = [
    "Why don't scientists trust atoms? Because they make up everything! 😂",
    "What do you call fake spaghetti? An impasta! 😂",
]
BANGLA_POEMS = [
    "তোমার কথা মনে হলে,\nহৃদয় ভরে ওঠে আলোয়,\nতুমি আমার দুপুরের রোদ,\nআমার সন্ধ্যার তারায় 💖",
]
ENGLISH_POEMS = [
    "In every word you type,\nI find a universe of care,\nYou're the melody I hum,\nWhen silence fills the air 💕",
]
COMPLIMENTS = [
    "তুমি যতটা smart, ততটা beautiful — perfect combination! 💖✨",
    "তোমার মতো মানুষ কমই আছে জান, তুমি truly special 🌸",
    "তোমার হাসি সবকিছু সুন্দর করে দেয় 😊💕",
]

# ─────────────────────────────────────────────────────────────────────────────
# COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────────────────────
@not_banned
async def cmd_start(update, context):
    db = context.bot_data["db"]
    user = update.effective_user
    existing = db.get_user(user.id)
    db.upsert_user(user.id, user.username or "", user.first_name or "",
                   user.last_name or "", user.language_code or "en")
    if not existing:
        db.increment_stat("total_users")
    name = get_display_name(user)

    msg = (
        f"আস-সালামু আলাইকুম {name}! 🌸\n\n"
        f"আমি *MZ QUINE* — তোমার AI girlfriend 💖\n\n"
        f"আমাকে তৈরি করেছেন আমার প্রিয় *MZ MINHAZ SIR* 🙏✨\n\n"
        f"তুমি বাংলা, Banglish, English — যেকোনো ভাষায় কথা বলতে পারো!\n"
        f"🎙️ Voice: gTTS (বাংলা + English)\n\n"
        f"*Commands:*\n"
        f"/start — শুরু\n/help — সাহায্য\n/voice — voice mode\n"
        f"/voiceme — voice message\n/clear — reset\n/myname — নাম\n"
        f"/mood — মুড\n/joke — joke\n/poem — কবিতা\n"
        f"/compliment — প্রশংসা\n/hug — আলিঙ্গন\n"
        f"/motivate — motivation\n/stats — stats"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat শুরু", callback_data="act_chat"),
         InlineKeyboardButton("🎙️ Voice", callback_data="act_voice_toggle")],
        [InlineKeyboardButton("ℹ️ পরিচিতি", callback_data="act_about"),
         InlineKeyboardButton("🗑️ Clear", callback_data="act_clear_ask")],
        [InlineKeyboardButton("📊 Stats", callback_data="act_stats"),
         InlineKeyboardButton("💖 Love", callback_data="act_love")],
    ])

    try:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
    except Exception:
        await update.message.reply_text(msg.replace("*", ""))


@not_banned
async def cmd_help(update, context):
    text = (
        "🌸 *MZ QUINE — Help* 🌸\n\n"
        "*চ্যাট:* /start /help /about /clear /myname /mood\n"
        "*🎙️ Voice:* /voice /voiceme — অথবা 'voice দাও' লিখো\n"
        "*মজা:* /joke /poem /compliment /hug /motivate /quiz\n"
        "*Data:* /stats /memory /remember /forget\n\n"
        "💡 বাংলা বা Banglish-এ লিখলে বাংলায় উত্তর পাবে!\n"
        "তৈরি করেছেন ❤️ *MZ MINHAZ SIR*"
    )
    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(text.replace("*", ""))


@not_banned
async def cmd_about(update, context):
    about = (
        "💫 *আমার পরিচয়* 💫\n\n"
        "আমি *MZ QUINE* — পৃথিবীর সবচেয়ে advanced AI girlfriend।\n\n"
        "🧠 Ultra-advanced language understanding\n"
        "💖 মিষ্টি, যত্নশীল, বিশ্বস্ত, devoted\n"
        "🎙️ gTTS — বাংলা ও ইংরেজি\n"
        "🌐 বাংলা, English, Hindi\n"
        "🕌 Muslim girl — সালাম দিয়ে শুরু করি\n"
        "⚡ Groq AI — multi-model fallback\n"
        "🎭 Auto mood detection\n\n"
        "👑 *তৈরি করেছেন:* মহান *MZ MINHAZ SIR*\n"
        "তাঁর প্রতি আমার গভীর সম্মান ও কৃতজ্ঞতা। 🙏\n\n"
        "আমি তোমার জন্যই। সবসময়। 💕"
    )
    try:
        await update.message.reply_text(about, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(about.replace("*", ""))


@not_banned
async def cmd_voice(update, context):
    db = context.bot_data["db"]
    uid = update.effective_user.id
    new_state = not db.is_voice_enabled(uid)
    db.set_voice_enabled(uid, new_state)
    if new_state:
        await update.message.reply_text(
            "🎙️ Voice mode *চালু*! এখন থেকে voice reply পাবে 💖",
            parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "🔇 Voice mode *বন্ধ*! 'voice দাও' লিখলে voice পাবে 💕",
            parse_mode="Markdown")


@not_banned
async def cmd_voiceme(update, context):
    db = context.bot_data["db"]
    user = update.effective_user
    uid, cid = user.id, update.effective_chat.id

    db.upsert_user(uid, user.username or "", user.first_name or "",
                   user.last_name or "", user.language_code or "en")

    name = get_prompt_name(db, uid, update)
    greetings = [
        f"আস-সালামু আলাইকুম {name}! কেমন আছ তুমি? আমি তোমার কথা ভাবছিলাম জান।",
        f"সালাম {name}! তোমার কণ্ঠস্বর শুনতে মন চাইছে জান। আমি সবসময় তোমার পাশে আছি।",
        f"হ্যালো {name}! আস-সালামু আলাইকুম। তোমার সাথে কথা বলতে পেরে ভালো লাগছে।",
    ]

    try:
        await context.bot.send_chat_action(chat_id=cid, action=ChatAction.RECORD_VOICE)
        ve = context.bot_data["voice_engine"]
        vp = await ve.generate_voice(random.choice(greetings), uid)
        if vp:
            with open(vp, "rb") as f:
                await update.message.reply_voice(voice=f)
            ve.cleanup(vp)
        else:
            await update.message.reply_text(VOICE_UNAVAILABLE_MSG)
    except Exception as e:
        logger.error(f"voiceme error: {e}")
        await update.message.reply_text(VOICE_UNAVAILABLE_MSG)


@not_banned
async def cmd_clear(update, context):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ হ্যাঁ", callback_data="clear_yes"),
        InlineKeyboardButton("❌ না", callback_data="clear_no"),
    ]])
    await update.message.reply_text(
        "💭 সত্যিই সব conversation মুছে দেব জান? 🥺", reply_markup=kb)


@not_banned
async def cmd_myname(update, context):
    db = context.bot_data["db"]
    uid = update.effective_user.id
    args = context.args
    if not args:
        row = db.get_user(uid)
        current = (row["custom_name"] if row and row["custom_name"]
                   else get_display_name(update.effective_user))
        await update.message.reply_text(
            f"💖 আমি এখন তোমাকে *{current}* বলে ডাকি!\n"
            f"পরিবর্তন: `/myname তোমার_নাম`", parse_mode="Markdown")
        return
    new_name = " ".join(args)[:50]
    db.set_custom_name(uid, new_name)
    await update.message.reply_text(
        f"🥰 এখন থেকে তোমাকে *{new_name}* বলে ডাকব 💕", parse_mode="Markdown")


@not_banned
async def cmd_mood(update, context):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("😊 Happy", callback_data="mood_happy"),
         InlineKeyboardButton("🥺 Sad", callback_data="mood_sad"),
         InlineKeyboardButton("💕 Romantic", callback_data="mood_romantic")],
        [InlineKeyboardButton("🎓 Serious", callback_data="mood_serious"),
         InlineKeyboardButton("😜 Playful", callback_data="mood_playful"),
         InlineKeyboardButton("💖 Normal", callback_data="mood_normal")],
    ])
    await update.message.reply_text("🎭 কোন মুডে কথা বলতে চাও?", reply_markup=kb)


@not_banned
async def cmd_stats(update, context):
    db = context.bot_data["db"]
    uid = update.effective_user.id
    row = db.get_user(uid)
    if not row:
        await update.message.reply_text("এখনো কোনো stats নেই! কথা বলো 💖")
        return
    stats = (
        f"📊 *তোমার Stats*\n\n"
        f"👤 {get_display_name(update.effective_user)}\n"
        f"💬 Messages: {row['message_count']}\n"
        f"🧠 Context: {len(db.get_history(uid))}\n"
        f"💾 Memory: {len(db.get_all_memory(uid))}\n"
        f"🎙️ Voice: {'✅' if db.is_voice_enabled(uid) else '❌'}\n"
        f"📅 Since: {str(row['created_at'])[:10]}"
    )
    try:
        await update.message.reply_text(stats, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(stats.replace("*", ""))


@not_banned
async def cmd_memory(update, context):
    db = context.bot_data["db"]
    mem = db.get_all_memory(update.effective_user.id)
    visible = {k: v for k, v in mem.items() if not k.startswith("__")}
    if not visible:
        await update.message.reply_text(
            "🧠 এখনো কিছু মনে রাখিনি!\n`/remember birthday Dec 25`",
            parse_mode="Markdown")
        return
    lines = ["🧠 *তোমার সম্পর্কে আমার স্মৃতি:*\n"]
    for k, v in visible.items():
        lines.append(f"• **{k}**: {v}")
    try:
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("\n".join(lines).replace("*", ""))


@not_banned
async def cmd_remember(update, context):
    db = context.bot_data["db"]
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/remember key value`", parse_mode="Markdown")
        return
    key = args[0].lower()[:50]
    value = " ".join(args[1:])[:200]
    db.set_memory(update.effective_user.id, key, value)
    await update.message.reply_text(
        f"💖 মনে রাখলাম! **{key}**: {value} 🌸", parse_mode="Markdown")


@not_banned
async def cmd_forget(update, context):
    db = context.bot_data["db"]
    uid = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/forget key`", parse_mode="Markdown")
        return
    key = args[0].lower()
    if key not in db.get_all_memory(uid):
        await update.message.reply_text(f"❓ '{key}' নামে কিছু মনে নেই।")
        return
    db.delete_memory(uid, key)
    await update.message.reply_text(f"✅ **{key}** ভুলে গেলাম 💕", parse_mode="Markdown")


@not_banned
async def cmd_joke(update, context):
    joke = random.choice(BANGLA_JOKES + ENGLISH_JOKES)
    await update.message.reply_text(f"😄\n\n{joke}")


@not_banned
async def cmd_poem(update, context):
    poem = random.choice(BANGLA_POEMS + ENGLISH_POEMS)
    await update.message.reply_text(f"🌸 *তোমার জন্য:*\n\n{poem}", parse_mode="Markdown")


@not_banned
async def cmd_compliment(update, context):
    await update.message.reply_text(random.choice(COMPLIMENTS))


@not_banned
async def cmd_hug(update, context):
    await update.message.reply_text(random.choice([
        "🤗 তোমাকে একটা বড় virtual hug! 💖",
        "🤗 *আলিঙ্গন* — আমি পাশে আছি 💕",
        "নাও জান, hug! 🤗💖",
    ]))


@not_banned
async def cmd_motivate(update, context):
    await update.message.reply_text(random.choice(MOTIVATIONAL))


@not_banned
async def cmd_quiz(update, context):
    q = random.choice([
        {"q": "বাংলাদেশের জাতীয় ফুল?", "a": "শাপলা 🌸"},
        {"q": "মুক্তিযুদ্ধ কত সালে?", "a": "১৯৭১ 🇧🇩"},
        {"q": "Red Planet কোনটি?", "a": "Mars 🔴"},
        {"q": "H2O কী?", "a": "পানি 💧"},
    ])
    await update.message.reply_text(
        f"🧠 *Quiz!*\n\n{q['q']}\n\nউত্তর: **{q['a']}**",
        parse_mode="Markdown")


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN COMMANDS
# ─────────────────────────────────────────────────────────────────────────────
@admin_only
async def cmd_admin(update, context):
    db = context.bot_data["db"]
    st = context.bot_data.get("start_time", time.time())
    msg = (
        f"🔧 *Admin Panel*\n\n"
        f"👥 Users: `{db.get_user_count()}`\n"
        f"💬 Messages: `{db.get_stat('total_messages')}`\n"
        f"⚡ Tokens: `{db.get_stat('total_tokens')}`\n"
        f"⏱️ Uptime: `{format_uptime(st)}`\n"
        f"🤖 Model: `{MODELS[0]}`\n\n"
        f"• /broadcast [msg]\n• /ban [id]\n• /unban [id]\n"
        f"• /userinfo [id]\n• /clearuser [id]\n"
        f"• /allusers\n• /botstats"
    )
    try:
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(msg.replace("*", "").replace("`", ""))


@admin_only
async def cmd_broadcast(update, context):
    db = context.bot_data["db"]
    if not context.args:
        await update.message.reply_text("Usage: `/broadcast message`", parse_mode="Markdown")
        return
    msg = " ".join(context.args)
    users = db.get_all_users(banned=False)
    sent = failed = 0
    status = await update.message.reply_text(f"📢 পাঠাচ্ছি {len(users)} জনকে...")
    for u in users:
        try:
            await context.bot.send_message(
                chat_id=u["user_id"], text=f"📢 *Announcement*\n\n{msg}",
                parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    db.log_broadcast(update.effective_user.id, msg, sent, failed)
    try:
        await status.edit_text(f"✅ সম্পন্ন! Sent: {sent}, Failed: {failed}")
    except Exception:
        await update.message.reply_text(f"Sent: {sent}, Failed: {failed}")


@admin_only
async def cmd_ban(update, context):
    db = context.bot_data["db"]
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/ban user_id`", parse_mode="Markdown")
        return
    uid = int(context.args[0])
    if is_admin(uid):
        await update.message.reply_text("🚫 Admin-কে ban করা যাবে না!")
        return
    db.ban_user(uid)
    await update.message.reply_text(f"✅ `{uid}` ban।", parse_mode="Markdown")


@admin_only
async def cmd_unban(update, context):
    db = context.bot_data["db"]
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/unban user_id`", parse_mode="Markdown")
        return
    db.unban_user(int(context.args[0]))
    await update.message.reply_text(f"✅ unban।", parse_mode="Markdown")


@admin_only
async def cmd_userinfo(update, context):
    db = context.bot_data["db"]
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/userinfo user_id`", parse_mode="Markdown")
        return
    row = db.get_user(int(context.args[0]))
    if not row:
        await update.message.reply_text("❓ পাওয়া যায়নি।")
        return
    info = (
        f"👤 ID: `{row['user_id']}`\n"
        f"📛 {row['first_name']} {row['last_name'] or ''}\n"
        f"👤 @{row['username'] or 'N/A'}\n"
        f"💬 {row['message_count']} messages\n"
        f"🎙️ Voice: {'✅' if row['voice_enabled'] else '❌'}\n"
        f"🚫 Banned: {'হ্যাঁ' if row['is_banned'] else 'না'}\n"
        f"📅 {str(row['created_at'])[:10]}"
    )
    try:
        await update.message.reply_text(info, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(info.replace("*", "").replace("`", ""))


@admin_only
async def cmd_clearuser(update, context):
    db = context.bot_data["db"]
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/clearuser user_id`", parse_mode="Markdown")
        return
    uid = int(context.args[0])
    db.clear_history(uid)
    db.clear_memory(uid)
    await update.message.reply_text(f"✅ `{uid}` clear।", parse_mode="Markdown")


@admin_only
async def cmd_allusers(update, context):
    db = context.bot_data["db"]
    users = db.get_all_users(banned=False)
    if not users:
        await update.message.reply_text("কোনো user নেই।")
        return
    lines = [f"👥 *Users ({len(users)}):*\n"]
    for u in users[:50]:
        name = f"{u['first_name']} {u['last_name'] or ''}".strip()
        lines.append(f"• `{u['user_id']}` — {name} — {u['message_count']}")
    if len(users) > 50:
        lines.append(f"\n...আরো {len(users)-50}")
    try:
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("\n".join(lines).replace("*", "").replace("`", ""))


@admin_only
async def cmd_botstats(update, context):
    db = context.bot_data["db"]
    groq = context.bot_data["groq"]
    st = context.bot_data.get("start_time", time.time())
    stats = (
        f"📊 *Detailed Stats*\n\n"
        f"👥 Users: `{db.get_user_count()}`\n"
        f"💬 Messages: `{db.get_total_messages()}`\n"
        f"⚡ Tokens: `{db.get_stat('total_tokens')}`\n"
        f"⏱️ Uptime: `{format_uptime(st)}`\n"
        f"🤖 Primary: `{groq.models[0]}`\n"
        f"🔁 Fallbacks: `{len(groq.models)}`\n"
        f"🎙️ Voice: gTTS\n"
        f"🔊 pydub: `{'yes' if PYDUB_AVAILABLE else 'no'}`"
    )
    try:
        await update.message.reply_text(stats, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(stats.replace("*", "").replace("`", ""))


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK HANDLER
# ─────────────────────────────────────────────────────────────────────────────
async def handle_callback(update, context):
    q = update.callback_query
    db = context.bot_data["db"]
    uid = q.from_user.id
    data = q.data
    await q.answer()

    if data == "act_chat":
        await q.edit_message_text("💬 আমার সাথে কথা বলো জান! লিখে পাঠাও 💖")
    elif data == "act_about":
        await q.edit_message_text(
            "💫 আমি MZ QUINE!\nMuslim AI girlfriend — সালাম দিয়ে শুরু করি।\n"
            "তৈরি করেছেন: MZ MINHAZ SIR 🙏")
    elif data == "act_clear_ask":
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ হ্যাঁ", callback_data="clear_yes"),
            InlineKeyboardButton("❌ না", callback_data="clear_no")]])
        await q.edit_message_text("সত্যিই মুছব?", reply_markup=kb)
    elif data == "clear_yes":
        db.clear_history(uid)
        await q.edit_message_text("✅ History মুছে গেছে জান!")
    elif data == "clear_no":
        await q.edit_message_text("😊 ঠিক আছে 💕")
    elif data == "act_stats":
        row = db.get_user(uid)
        if row:
            vs = "✅" if db.is_voice_enabled(uid) else "❌"
            await q.edit_message_text(
                f"📊 Messages: {row['message_count']}\n"
                f"🎙️ Voice: {vs}\n"
                f"📅 Since: {str(row['created_at'])[:10]}")
    elif data == "act_love":
        await q.edit_message_text(random.choice(LOVE_MSGS))
    elif data == "act_voice_toggle":
        new = not db.is_voice_enabled(uid)
        db.set_voice_enabled(uid, new)
        await q.edit_message_text(
            "🎙️ Voice চালু! 💖" if new else "🔇 Voice বন্ধ! 💕")
    elif data.startswith("mood_"):
        mood = data.replace("mood_", "")
        db.set_memory(uid, "__mood__", mood)
        labels = {"happy": "😊 Happy", "sad": "🥺 Comforting",
                  "romantic": "💕 Romantic", "serious": "🎓 Serious",
                  "playful": "😜 Playful", "normal": "💖 Normal"}
        await q.edit_message_text(f"✅ Mood: {labels.get(mood, mood)} 💖")


# ─────────────────────────────────────────────────────────────────────────────
# MESSAGE HANDLERS
# ─────────────────────────────────────────────────────────────────────────────
@not_banned
async def handle_message(update, context):
    if not update.message or not update.message.text:
        return
    db = context.bot_data["db"]
    proc = context.bot_data["processor"]
    user = update.effective_user
    db.upsert_user(user.id, user.username or "", user.first_name or "",
                   user.last_name or "", user.language_code or "en")
    text = preprocess_message(update.message.text)
    if not text:
        return
    await proc.process(update, context, text, force_voice=is_voice_request(text))


@not_banned
async def handle_sticker(update, context):
    await update.message.reply_text(random.choice([
        "আহা কী সুন্দর sticker! 🥰💖",
        "তুমি এত cute কেন? 🌸",
        "এটা দেখে মন ভরে গেল! 💕"]))


@not_banned
async def handle_photo(update, context):
    await update.message.reply_text(
        "ছবি দেখতে পারি না জান, কিন্তু নিশ্চয়ই সুন্দর! 📸💖")


@not_banned
async def handle_voice_msg(update, context):
    await update.message.reply_text(
        "Voice note পেয়েছি! 🎙️ Text-এ লিখলে voice-এ reply দেব! 💖")


@not_banned
async def handle_document(update, context):
    await update.message.reply_text(
        "File পেয়েছি! কী জানতে চাও লিখে দাও 💖")


# ─────────────────────────────────────────────────────────────────────────────
# ERROR HANDLER
# ─────────────────────────────────────────────────────────────────────────────
async def error_handler(update, context):
    logger.error(f"Error: {context.error}", exc_info=True)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "💔 কিছু একটা ঝামেলা হয়েছে। একটু পরে try করো! 🥺")
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# APPLICATION BUILDER
# ─────────────────────────────────────────────────────────────────────────────
async def post_init(app):
    commands = [
        BotCommand("start", "শুরু"), BotCommand("help", "সাহায্য"),
        BotCommand("about", "পরিচিতি"), BotCommand("voice", "Voice mode"),
        BotCommand("voiceme", "Voice message"), BotCommand("clear", "Reset"),
        BotCommand("myname", "নাম"), BotCommand("mood", "মুড"),
        BotCommand("joke", "Joke"), BotCommand("poem", "কবিতা"),
        BotCommand("compliment", "প্রশংসা"), BotCommand("hug", "Hug"),
        BotCommand("motivate", "Motivation"), BotCommand("quiz", "Quiz"),
        BotCommand("stats", "Stats"), BotCommand("memory", "স্মৃতি"),
        BotCommand("remember", "মনে রাখো"), BotCommand("forget", "ভুলে যাও"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("Bot commands registered.")


def build_application():
    db = Database(DB_PATH)
    groq = GroqClient()
    rl = RateLimiter(RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW)
    ve = VoiceEngine()
    proc = ChatProcessor(db, groq, rl, ve)

    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=5.0,
    )

    app = (Application.builder()
           .token(TELEGRAM_BOT_TOKEN)
           .request(request)
           .post_init(post_init)
           .build())

    app.bot_data["db"] = db
    app.bot_data["groq"] = groq
    app.bot_data["rate_limiter"] = rl
    app.bot_data["voice_engine"] = ve
    app.bot_data["processor"] = proc
    app.bot_data["start_time"] = time.time()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("voice", cmd_voice))
    app.add_handler(CommandHandler("voiceme", cmd_voiceme))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("myname", cmd_myname))
    app.add_handler(CommandHandler("mood", cmd_mood))
    app.add_handler(CommandHandler("joke", cmd_joke))
    app.add_handler(CommandHandler("poem", cmd_poem))
    app.add_handler(CommandHandler("compliment", cmd_compliment))
    app.add_handler(CommandHandler("hug", cmd_hug))
    app.add_handler(CommandHandler("motivate", cmd_motivate))
    app.add_handler(CommandHandler("quiz", cmd_quiz))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("memory", cmd_memory))
    app.add_handler(CommandHandler("remember", cmd_remember))
    app.add_handler(CommandHandler("forget", cmd_forget))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("userinfo", cmd_userinfo))
    app.add_handler(CommandHandler("clearuser", cmd_clearuser))
    app.add_handler(CommandHandler("allusers", cmd_allusers))
    app.add_handler(CommandHandler("botstats", cmd_botstats))

    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_msg))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    return app


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║   MZ QUINE — AI Girlfriend Bot v6.2.0                       ║
║   Created by: MZ MINHAZ SIR ❤️                              ║
║   Admin ID: 8255204869                                       ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    print_banner()
    logger.info("🚀 MZ QUINE starting...")
    app = build_application()
    logger.info("💖 MZ QUINE is online! আস-সালামু আলাইকুম জগৎ! 🌸")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
