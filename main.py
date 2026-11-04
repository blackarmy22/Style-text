# =========================================================
# ENGLISH STYLE FONT BOT (RENDER OPTIMIZED & ENV CHANNEL)
# =========================================================

import asyncio
from datetime import datetime
import html
import logging
import os
import sqlite3
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================================================
# RENDER / FLASK WEB SERVER
# =========================================================

app = Flask(__name__)


@app.get("/")
def home():
  return "English Style Font Bot is running", 200


@app.get("/health")
def health():
  return "OK", 200


# =========================================================
# BOT TOKEN & CONFIG (ENVIRONMENT VARIABLES)
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Channel name and link are read from Environment variables.
CHANNEL_ID = os.getenv("CHANNEL_ID", "@fontstylem").strip()
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/fontstylem").strip()

ADMIN_IDS = {
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip().isdigit()
}
USERS_DB = os.getenv("USERS_DB", "users.db")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================================================
# STANDARD CHARACTERS & HELPER
# =========================================================

UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"


def make_math_map(
    upper_start=None, lower_start=None, digit_start=None, exceptions=None
):
  mapping = {}
  if upper_start is not None:
    for i, char in enumerate(UPPER):
      mapping[char] = chr(upper_start + i)
  if lower_start is not None:
    for i, char in enumerate(LOWER):
      mapping[char] = chr(lower_start + i)
  if digit_start is not None:
    for i, char in enumerate(DIGITS):
      mapping[char] = chr(digit_start + i)
  if exceptions:
    mapping.update(exceptions)
  return mapping


# =========================================================
# UNICODE FONT MAPS
# =========================================================

BOLD_SERIF_MAP = make_math_map(0x1D400, 0x1D41A, 0x1D7CE)
ITALIC_SERIF_MAP = make_math_map(0x1D434, 0x1D44E, exceptions={"h": "ℎ"})
BOLD_ITALIC_MAP = make_math_map(0x1D468, 0x1D482)
SANS_MAP = make_math_map(0x1D5A0, 0x1D5BA, 0x1D7E2)
SANS_BOLD_MAP = make_math_map(0x1D5D4, 0x1D5EE, 0x1D7EC)
SANS_ITALIC_MAP = make_math_map(0x1D608, 0x1D622)
SANS_BOLD_ITALIC_MAP = make_math_map(0x1D63C, 0x1D656)
MONOSPACE_MAP = make_math_map(0x1D670, 0x1D68A, 0x1D7F6)
DOUBLE_STRUCK_MAP = make_math_map(
    0x1D538,
    0x1D552,
    0x1D7D8,
    exceptions={
        "C": "ℂ",
        "H": "ℍ",
        "N": "ℕ",
        "P": "ℙ",
        "Q": "ℚ",
        "R": "ℝ",
        "Z": "ℤ",
    },
)
FRAKTUR_MAP = make_math_map(
    0x1D504,
    0x1D51E,
    exceptions={"C": "ℭ", "H": "ℌ", "I": "ℑ", "R": "ℜ", "Z": "ℨ"},
)
BOLD_FRAKTUR_MAP = make_math_map(0x1D56C, 0x1D586)
SCRIPT_MAP = make_math_map(
    0x1D49C,
    0x1D4B6,
    exceptions={
        "B": "ℬ",
        "E": "ℰ",
        "F": "ℱ",
        "H": "ℋ",
        "I": "ℐ",
        "L": "ℒ",
        "M": "ℳ",
        "R": "ℛ",
        "e": "ℯ",
        "g": "ℊ",
        "o": "ℴ",
    },
)
BOLD_SCRIPT_MAP = make_math_map(0x1D4D0, 0x1D4EA)

SCRIPT_MAP.update({
    "B": "ℬ",
    "E": "ℰ",
    "F": "ℱ",
    "H": "ℋ",
    "I": "ℐ",
    "L": "ℒ",
    "M": "ℳ",
    "R": "ℛ",
    "e": "ℯ",
    "g": "ℊ",
    "o": "ℴ",
})
FRAKTUR_MAP.update({"C": "ℭ", "H": "ℌ", "I": "ℑ", "R": "ℜ", "Z": "ℨ"})
DOUBLE_STRUCK_MAP.update({
    "C": "ℂ",
    "H": "ℍ",
    "N": "ℕ",
    "P": "ℙ",
    "Q": "ℚ",
    "R": "ℝ",
    "Z": "ℤ",
})

FULLWIDTH_MAP = {}
for i, char in enumerate(UPPER):
  FULLWIDTH_MAP[char] = chr(0xFF21 + i)
for i, char in enumerate(LOWER):
  FULLWIDTH_MAP[char] = chr(0xFF41 + i)
for i, char in enumerate(DIGITS):
  FULLWIDTH_MAP[char] = chr(0xFF10 + i)


def apply_map(text, mapping):
  return "".join(mapping.get(char, char) for char in text)


SMALL_CAPS_MAP = {
    "a": "ᴀ",
    "b": "ʙ",
    "c": "ᴄ",
    "d": "ᴅ",
    "e": "ᴇ",
    "f": "ꜰ",
    "g": "ɢ",
    "h": "ʜ",
    "i": "ɪ",
    "j": "ᴊ",
    "k": "ᴋ",
    "l": "ʟ",
    "m": "ᴍ",
    "n": "ɴ",
    "o": "ᴏ",
    "p": "ᴘ",
    "q": "ǫ",
    "r": "ʀ",
    "s": "s",
    "t": "ᴛ",
    "u": "ᴜ",
    "v": "ᴠ",
    "w": "ᴡ",
    "x": "x",
    "y": "ʏ",
    "z": "ᴢ",
}


def small_caps(text):
  return "".join(SMALL_CAPS_MAP.get(char, char) for char in text)


CIRCLED_UPPER = "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ"
CIRCLED_LOWER = "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ"
CIRCLED_DIGITS = "⓪①②③④⑤⑥⑦⑧⑨"


def circled(text):
  result = []
  for char in text:
    if char in UPPER:
      result.append(CIRCLED_UPPER[UPPER.index(char)])
    elif char in LOWER:
      result.append(CIRCLED_LOWER[LOWER.index(char)])
    elif char in DIGITS:
      result.append(CIRCLED_DIGITS[DIGITS.index(char)])
    else:
      result.append(char)
  return "".join(result)


NEGATIVE_CIRCLED_UPPER = "🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩"
NEGATIVE_CIRCLED_LOWER = "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ"


def filled_circled(text):
  result = []
  for char in text:
    if char in UPPER:
      result.append(NEGATIVE_CIRCLED_UPPER[UPPER.index(char)])
    elif char in LOWER:
      result.append(NEGATIVE_CIRCLED_LOWER[LOWER.index(char)])
    else:
      result.append(char)
  return "".join(result)


SQUARED_UPPER = "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉"


def squares(text):
  result = []
  for char in text:
    if char in UPPER:
      result.append(SQUARED_UPPER[UPPER.index(char)])
    elif char in LOWER:
      result.append(SQUARED_UPPER[LOWER.index(char)])
    else:
      result.append(char)
  return "".join(result)


NEGATIVE_SQUARED_UPPER = "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🅅🆆🆇🆈🆉"


def filled_squares(text):
  result = []
  for char in text:
    if char in UPPER:
      result.append(NEGATIVE_SQUARED_UPPER[UPPER.index(char)])
    elif char in LOWER:
      result.append(NEGATIVE_SQUARED_UPPER[LOWER.index(char)])
    else:
      result.append(char)
  return "".join(result)


PARENTHESIZED_MAP = {
    "a": "⒜",
    "b": "⒝",
    "c": "⒞",
    "d": "⒟",
    "e": "⒠",
    "f": "⒡",
    "g": "⒢",
    "h": "⒣",
    "i": "⒤",
    "j": "⒥",
    "k": "⒦",
    "l": "⒧",
    "m": "⒨",
    "n": "⒩",
    "o": "⒪",
    "p": "⒫",
    "q": "⒬",
    "r": "⒭",
    "s": "⒮",
    "t": "⒯",
    "u": "⒰",
    "v": "⒱",
    "w": "⒲",
    "x": "⒳",
    "y": "⒴",
    "z": "⒵",
    "A": "⒜",
    "B": "⒝",
    "C": "⒞",
    "D": "⒟",
    "E": "⒠",
    "F": "⒡",
    "G": "⒢",
    "H": "⒣",
    "I": "⒤",
    "J": "⒥",
    "K": "⒦",
    "L": "⒧",
    "M": "⒨",
    "N": "⒩",
    "O": "⒪",
    "P": "⒫",
    "Q": "⒬",
    "R": "⒭",
    "S": "⒮",
    "T": "⒯",
    "U": "⒰",
    "V": "⒱",
    "W": "⒲",
    "X": "⒳",
    "Y": "⒴",
    "Z": "⒵",
}


def parenthesized(text):
  return "".join(PARENTHESIZED_MAP.get(char, char) for char in text)


TINY_MAP = {
    "a": "ᵃ",
    "b": "ᵇ",
    "c": "ᶜ",
    "d": "ᵈ",
    "e": "ᵉ",
    "f": "ᶠ",
    "g": "ᵍ",
    "h": "ʰ",
    "i": "ⁱ",
    "j": "ʲ",
    "k": "ᵏ",
    "l": "ˡ",
    "m": "ᵐ",
    "n": "ⁿ",
    "o": "ᵒ",
    "p": "ᵖ",
    "q": "q",
    "r": "ʳ",
    "s": "ˢ",
    "t": "ᵗ",
    "u": "ᵘ",
    "v": "ᵛ",
    "w": "ʷ",
    "x": "ˣ",
    "y": "ʸ",
    "z": "ᶻ",
    "A": "ᴬ",
    "B": "ᴮ",
    "C": "ᶜ",
    "D": "ᴰ",
    "E": "ᴱ",
    "F": "ᶠ",
    "G": "ᴳ",
    "H": "ᴴ",
    "I": "ᴵ",
    "J": "ᴶ",
    "K": "ᴷ",
    "L": "ᴸ",
    "M": "ᴹ",
    "N": "ᴺ",
    "O": "ᴼ",
    "P": "ᴾ",
    "Q": "Q",
    "R": "ᴿ",
    "S": "ˢ",
    "T": "ᵀ",
    "U": "ᵁ",
    "V": "ⱽ",
    "W": "ᵂ",
    "X": "ˣ",
    "Y": "ʸ",
    "Z": "ᶻ",
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
}


def tiny(text):
  return "".join(TINY_MAP.get(char, char) for char in text)


COMIC_MAP = {
    "A": "Ⱥ",
    "a": "ɑ",
    "B": "Ɓ",
    "b": "ɓ",
    "C": "Ƈ",
    "c": "ƈ",
    "D": "Đ",
    "d": "ɗ",
    "E": "Ɛ",
    "e": "ɛ",
    "F": "Ƒ",
    "f": "ƒ",
    "G": "Ɠ",
    "g": "ɠ",
    "H": "Ħ",
    "h": "ɦ",
    "I": "Ɨ",
    "i": "ɨ",
    "J": "Ɉ",
    "j": "ʝ",
    "K": "Ƙ",
    "k": "ƙ",
    "L": "Ł",
    "l": "ł",
    "M": "Ɯ",
    "m": "ɱ",
    "N": "Ɲ",
    "n": "ɲ",
    "O": "Ø",
    "o": "ø",
    "P": "Ƥ",
    "p": "ƥ",
    "Q": "Ɋ",
    "q": "ɋ",
    "R": "Ʀ",
    "r": "ɍ",
    "S": "Ş",
    "s": "ʂ",
    "T": "Ŧ",
    "t": "ŧ",
    "U": "Ʉ",
    "u": "ʉ",
    "V": "Ʋ",
    "v": "ʋ",
    "W": "Ŵ",
    "w": "ŵ",
    "X": "Ӿ",
    "x": "ӿ",
    "Y": "Ƴ",
    "y": "ɏ",
    "Z": "Ƶ",
    "z": "ƶ",
}


def comic(text):
  return apply_map(text, COMIC_MAP)


QUNI_MAP = {
    "A": "Ⱥ",
    "a": "Ⱥ",
    "B": "Ɓ",
    "b": "ƀ",
    "C": "Ƈ",
    "c": "ƈ",
    "D": "Đ",
    "d": "đ",
    "E": "Ɇ",
    "e": "ɇ",
    "F": "Ƒ",
    "f": "ƒ",
    "G": "Ǥ",
    "g": "ǥ",
    "H": "Ħ",
    "h": "ħ",
    "I": "Ɨ",
    "i": "ɨ",
    "J": "Ɉ",
    "j": "ɉ",
    "K": "Ƙ",
    "k": "ƙ",
    "L": "Ł",
    "l": "ł",
    "M": "M",
    "m": "ɱ",
    "N": "Ŋ",
    "n": "ŋ",
    "O": "Ø",
    "o": "ø",
    "P": "Ƥ",
    "p": "ƥ",
    "Q": "Ɋ",
    "q": "ɋ",
    "R": "Ɍ",
    "r": "ɍ",
    "S": "Ş",
    "s": "ş",
    "T": "Ŧ",
    "t": "ŧ",
    "U": "Ʉ",
    "u": "ʉ",
    "V": "Ʋ",
    "v": "ʋ",
    "W": "Ŵ",
    "w": "ŵ",
    "X": "Ӿ",
    "x": "ӿ",
    "Y": "Ɏ",
    "y": "ɏ",
    "Z": "Ƶ",
    "z": "ƶ",
}


def quni(text):
  return apply_map(text, QUNI_MAP)


SPECIAL_MAP = {
    "A": "Λ",
    "B": "β",
    "C": "C",
    "D": "ᗪ",
    "E": "Σ",
    "F": "Ғ",
    "G": "Ɠ",
    "H": "卄",
    "I": "I",
    "J": "Ј",
    "K": "Ҡ",
    "L": "Ł",
    "M": "爪",
    "N": "И",
    "O": "Ө",
    "P": "尸",
    "Q": "Q",
    "R": "尺",
    "S": "Ѕ",
    "T": "Ŧ",
    "U": "Ц",
    "V": "Ѵ",
    "W": "Ш",
    "X": "Ж",
    "Y": "Ұ",
    "Z": "乙",
    "a": "α",
    "b": "в",
    "c": "¢",
    "d": "∂",
    "e": "є",
    "f": "ƒ",
    "g": "ɠ",
    "h": "н",
    "i": "ι",
    "j": "נ",
    "k": "к",
    "l": "ℓ",
    "m": "м",
    "n": "η",
    "o": "σ",
    "p": "ρ",
    "q": "զ",
    "r": "я",
    "s": "ѕ",
    "t": "т",
    "u": "υ",
    "v": "ν",
    "w": "ω",
    "x": "χ",
    "y": "у",
    "z": "z",
}


def special(text):
  return apply_map(text, SPECIAL_MAP)


UPSIDE_DOWN_MAP = {
    "a": "ɐ",
    "b": "q",
    "c": "ɔ",
    "d": "p",
    "e": "ǝ",
    "f": "ɟ",
    "g": "ƃ",
    "h": "ɥ",
    "i": "ᴉ",
    "j": "ɾ",
    "k": "ʞ",
    "l": "ʃ",
    "m": "ɯ",
    "n": "u",
    "o": "o",
    "p": "d",
    "q": "b",
    "r": "ɹ",
    "s": "s",
    "t": "ʇ",
    "u": "n",
    "v": "ʌ",
    "w": "ʍ",
    "x": "x",
    "y": "ʎ",
    "z": "z",
    "A": "∀",
    "B": "ᗺ",
    "C": "Ɔ",
    "D": "◖",
    "E": "Ǝ",
    "F": "Ⅎ",
    "G": "Ꭾ",
    "H": "H",
    "I": "I",
    "J": "Ⴑ",
    "K": "⋊",
    "L": "⅃",
    "M": "M",
    "N": "N",
    "O": "O",
    "P": "Ԁ",
    "Q": "Q",
    "R": "Я",
    "S": "S",
    "T": "⊥",
    "U": "∩",
    "V": "Λ",
    "W": "M",
    "X": "X",
    "Y": "⅄",
    "Z": "Z",
    "0": "0",
    "1": "Ɩ",
    "2": "ᄅ",
    "3": "Ɛ",
    "4": "ㄣ",
    "5": "ϛ",
    "6": "9",
    "7": "ㄥ",
    "8": "8",
    "9": "6",
}


def upside_down(text):
  return "".join(UPSIDE_DOWN_MAP.get(char, char) for char in reversed(text))


def reverse_text(text):
  return text[::-1]


MIRROR_MAP = {
    "A": "A",
    "B": "ᗺ",
    "C": "Ɔ",
    "D": "◖",
    "E": "Ǝ",
    "F": "Ⅎ",
    "G": "Ꭾ",
    "H": "H",
    "I": "I",
    "J": "Ⴑ",
    "K": "⋊",
    "L": "⅃",
    "M": "M",
    "N": "И",
    "O": "O",
    "P": "Ԁ",
    "Q": "Q",
    "R": "Я",
    "S": "S",
    "T": "⊥",
    "U": "∩",
    "V": "Λ",
    "W": "M",
    "X": "X",
    "Y": "⅄",
    "Z": "Z",
    "a": "ɒ",
    "b": "d",
    "c": "ↄ",
    "d": "b",
    "e": "ɘ",
    "f": "ɟ",
    "g": "ᵷ",
    "h": "ʜ",
    "i": "i",
    "j": "ɾ",
    "k": "ʞ",
    "l": "l",
    "m": "m",
    "n": "n",
    "o": "o",
    "p": "q",
    "q": "p",
    "r": "ɿ",
    "s": "s",
    "t": "t",
    "u": "u",
    "v": "v",
    "w": "w",
    "x": "x",
    "y": "y",
    "z": "z",
}


def mirror(text):
  return "".join(MIRROR_MAP.get(char, char) for char in text[::-1])


def serif_italic(text):
  return apply_map(text, ITALIC_SERIF_MAP)


# =========================================================
# NEW CUSTOM STYLES (ستایلە نوێیەکان کە داواکردوون)
# =========================================================

# 1. A̷b̷c̷d̷e̷f̷g̷ (Slash Strike)
def style_slash_strike(text):
  return "".join(f"{c}\u0337" if c.strip() else c for c in text)


# 2. ᗩᗷᑕᗪEᖴG (Sans Bubbles)
SANS_CIRCLED_UPPER = "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"
SANS_CIRCLED_LOWER = "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"


def style_sans_bubbles(text):
  result = []
  for char in text:
    if char in UPPER:
      result.append(SANS_CIRCLED_UPPER[UPPER.index(char)])
    elif char in LOWER:
      result.append(SANS_CIRCLED_LOWER[LOWER.index(char)])
    else:
      result.append(char)
  return "".join(result)


# 3. Ⱥҍçժҽƒց (Quni Custom Variant)
QU_CUSTOM_MAP = {
    "A": "Ⱥ",
    "a": "Ⱥ",
    "B": "ҍ",
    "b": "ҍ",
    "C": "ç",
    "c": "ç",
    "D": "ժ",
    "d": "ժ",
    "E": "ҽ",
    "e": "ҽ",
    "F": "ƒ",
    "f": "ƒ",
    "G": "ց",
    "g": "ց",
    "H": "Ħ",
    "h": "հ",
    "I": "Ӏ",
    "i": "ɪ",
    "J": "Ꭻ",
    "j": "ʝ",
    "K": "Ƙ",
    "k": "ƙ",
    "L": "ᒪ",
    "l": "ℓ",
    "M": "ℳ",
    "m": "ɱ",
    "N": "ℕ",
    "n": "ղ",
    "O": "Ꝋ",
    "o": "ℴ",
    "P": "℘",
    "p": "ƥ",
    "Q": "ⵕ",
    "q": "զ",
    "R": "℟",
    "r": "ɾ",
    "S": "Ꮪ",
    "s": "ʂ",
    "T": "Ͳ",
    "t": "ƭ",
    "U": "ℱ",
    "u": "ʉ",
    "V": "℣",
    "v": "ѵ",
    "W": "Ꮤ",
    "w": "𝕨",
    "X": "Ӿ",
    "x": "ҳ",
    "Y": "Ƴ",
    "y": "ყ",
    "Z": "ℤ",
    "z": "ȥ",
}


def style_qu_custom(text):
  return apply_map(text, QU_CUSTOM_MAP)


# 4. A҉b҉c҉d҉e҉f҉g҉ (Corrupted Fire)
def style_corrupted_fire(text):
  return "".join(f"{c}\u0489" if c.strip() else c for c in text)


# 5. ﾑ乃ᄃり乇ｷム (Ansi Style)
ANSI_MAP = {
    "A": "ﾑ",
    "a": "ﾑ",
    "B": "乃",
    "b": "乃",
    "C": "ᄃ",
    "c": "ᄃ",
    "D": "り",
    "d": "り",
    "E": "乇",
    "e": "乇",
    "F": "ｷ",
    "f": "ｷ",
    "G": "ム",
    "g": "ム",
    "H": "ዘ",
    "h": "ዘ",
    "I": "ٱ",
    "i": "ٱ",
    "J": "ﾌ",
    "j": "ﾌ",
    "K": "ӄ",
    "k": "ӄ",
    "L": "ረ",
    "l": "ረ",
    "M": "Ꮇ",
    "m": "Ꮇ",
    "N": "Ռ",
    "n": "Ռ",
    "O": "Ꝋ",
    "o": "Ꝋ",
    "P": "℘",
    "p": "℘",
    "Q": "զ",
    "q": "զ",
    "R": "R",
    "r": "ʀ",
    "S": "Տ",
    "s": "Տ",
    "T": "ፕ",
    "t": "ፕ",
    "U": "ሀ",
    "u": "ሀ",
    "V": "ሀ",
    "v": "ሀ",
    "W": "ሠ",
    "w": "ሠ",
    "X": "Ӿ",
    "x": "Ӿ",
    "Y": "ሃ",
    "y": "ሃ",
    "Z": "ℤ",
    "z": "ℤ",
}


def style_ansi(text):
  return apply_map(text, ANSI_MAP)


# 6. 卂乃匚ᗪ乇千Ꮆ (Wide Style)
WIDE_MAP = {
    "A": "卂",
    "a": "卂",
    "B": "乃",
    "b": "乃",
    "C": "匚",
    "c": "匚",
    "D": "ᗪ",
    "d": "ᗪ",
    "E": "乇",
    "e": "乇",
    "F": "千",
    "f": "千",
    "G": "Ꮆ",
    "g": "Ꮆ",
    "H": "卄",
    "h": "卄",
    "I": "丨",
    "i": "丨",
    "J": "ﾌ",
    "j": "ﾌ",
    "K": "Ҝ",
    "k": "Ҝ",
    "L": "ㄥ",
    "l": "ㄥ",
    "M": "爪",
    "m": "爪",
    "N": "ℕ",
    "n": "ℕ",
    "O": "ㄖ",
    "o": "ㄖ",
    "P": "尸",
    "p": "尸",
    "Q": "Ɋ",
    "q": "Ɋ",
    "R": "尺",
    "r": "尺",
    "S": "丂",
    "s": "丂",
    "T": "ㄒ",
    "t": "ㄒ",
    "U": "ㄩ",
    "u": "ㄩ",
    "V": "ᐯ",
    "v": "ᐯ",
    "W": "山",
    "w": "山",
    "X": "乂",
    "x": "乂",
    "Y": "ㄚ",
    "y": "ㄚ",
    "Z": "乙",
    "z": "乙",
}


def style_wide(text):
  return apply_map(text, WIDE_MAP)


# 7. ꪖ᥇ᥴᦔꫀᠻᧁ (Cursive Curly)
CURSIVE_MAP = {
    "A": "ꪖ",
    "a": "ꪖ",
    "B": "᥇",
    "b": "᥇",
    "C": "ᥴ",
    "c": "ᥴ",
    "D": "ᦔ",
    "d": "ᦔ",
    "E": "ꫀ",
    "e": "ꫀ",
    "F": "ᠻ",
    "f": "ᠻ",
    "G": "ᧁ",
    "g": "ᧁ",
    "H": "ꫝ",
    "h": "ꫝ",
    "I": "ỉ",
    "i": "ỉ",
    "J": "𝕛",
    "j": "𝕛",
    "K": "𝕜",
    "k": "𝕜",
    "L": "ꪶ",
    "l": "ꪶ",
    "M": "ꪑ",
    "m": "ꪑ",
    "N": "ꪀ",
    "n": "ꪀ",
    "O": "ꪮ",
    "o": "ꪮ",
    "P": "ᖯ",
    "p": "ᖯ",
    "Q": "𝕢",
    "q": "𝕢",
    "R": "᥅",
    "r": "᥅",
    "S": "ડ",
    "s": "ડ",
    "T": "𝕥",
    "t": "𝕥",
    "U": "ꪊ",
    "u": "ꪊ",
    "V": "᥎",
    "v": "᥎",
    "W": "᭙",
    "w": "᭙",
    "X": "᙭",
    "x": "᙭",
    "Y": "ꪗ",
    "y": "ꪗ",
    "Z": "𝕫",
    "z": "𝕫",
}


def style_cursive(text):
  return apply_map(text, CURSIVE_MAP)


# 8. ąცƈɖɛʄɠ (Tiny Lower)
TINY_LOWER_MAP = {
    "A": "ą",
    "a": "ą",
    "B": "ც",
    "b": "ც",
    "C": "ƈ",
    "c": "ƈ",
    "D": "ɖ",
    "d": "ɖ",
    "E": "ɛ",
    "e": "ɛ",
    "F": "ʄ",
    "f": "ʄ",
    "G": "ɠ",
    "g": "ɠ",
    "H": "ɦ",
    "h": "ɦ",
    "I": "ɪ",
    "i": "ɪ",
    "J": "ʝ",
    "j": "ʝ",
    "K": "ƙ",
    "k": "ƙ",
    "L": "Ɩ",
    "l": "Ɩ",
    "M": "ɱ",
    "m": "ɱ",
    "N": "ղ",
    "n": "ղ",
    "O": "օ",
    "o": "օ",
    "P": "ք",
    "p": "ք",
    "Q": "զ",
    "q": "զ",
    "R": "ɾ",
    "r": "ɾ",
    "S": "ʂ",
    "s": "ʂ",
    "T": "ɬ",
    "t": "ɬ",
    "U": "ʊ",
    "u": "ʊ",
    "V": "ʋ",
    "v": "ʋ",
    "W": "ɯ",
    "w": "ɯ",
    "X": "ӿ",
    "x": "ӿ",
    "Y": "ყ",
    "y": "ყ",
    "Z": "ȥ",
    "z": "ȥ",
}


def style_tiny_lower(text):
  return apply_map(text, TINY_LOWER_MAP)


# 9. Äß¢Ðê£g (Accent Style)
ACCENT_MAP = {
    "A": "Ä",
    "a": "ä",
    "B": "ß",
    "b": "b",
    "C": "¢",
    "c": "¢",
    "D": "Ð",
    "d": "đ",
    "E": "Ê",
    "e": "ê",
    "F": "£",
    "f": "£",
    "G": "Ğ",
    "g": "ğ",
    "H": "Ĥ",
    "h": "ĥ",
    "I": "Î",
    "i": "î",
    "J": "Ĵ",
    "j": "ĵ",
    "K": "Ķ",
    "k": "ķ",
    "L": "Ĺ",
    "l": "ĺ",
    "M": "M",
    "m": "m",
    "N": "Ñ",
    "n": "ñ",
    "O": "Ö",
    "o": "ö",
    "P": "Þ",
    "p": "þ",
    "Q": "Q",
    "q": "q",
    "R": "Ŕ",
    "r": "ŕ",
    "S": "Ş",
    "s": "ş",
    "T": "Ť",
    "t": "ť",
    "U": "Û",
    "u": "û",
    "V": "V",
    "v": "v",
    "W": "Ŵ",
    "w": "ŵ",
    "X": "X",
    "x": "x",
    "Y": "Ý",
    "y": "ý",
    "Z": "Ź",
    "z": "ź",
}


def style_accent(text):
  return apply_map(text, ACCENT_MAP)


# =========================================================
# STYLE FUNCTIONS DICTIONARY
# =========================================================

STYLE_FUNCTIONS = {
    "Bold Serif": lambda x: apply_map(x, BOLD_SERIF_MAP),
    "Italic Serif": lambda x: apply_map(x, ITALIC_SERIF_MAP),
    "Bold Italic": lambda x: apply_map(x, BOLD_ITALIC_MAP),
    "Sans Bold": lambda x: apply_map(x, SANS_BOLD_MAP),
    "Sans Italic": lambda x: apply_map(x, SANS_ITALIC_MAP),
    "Sans Bold Italic": lambda x: apply_map(x, SANS_BOLD_ITALIC_MAP),
    "Script": lambda x: apply_map(x, SCRIPT_MAP),
    "Bold Script": lambda x: apply_map(x, BOLD_SCRIPT_MAP),
    "Gothic": lambda x: apply_map(x, FRAKTUR_MAP),
    "Gothic Bold": lambda x: apply_map(x, BOLD_FRAKTUR_MAP),
    "Double Struck": lambda x: apply_map(x, DOUBLE_STRUCK_MAP),
    "Sans": lambda x: apply_map(x, SANS_MAP),
    "Monospace": lambda x: apply_map(x, MONOSPACE_MAP),
    "Fullwidth": lambda x: apply_map(x, FULLWIDTH_MAP),
    "Serif Italic": serif_italic,
    "Small Caps": small_caps,
    "Tiny": tiny,
    "Comic": comic,
    "Circled": circled,
    "Filled Circled": filled_circled,
    "Squares": squares,
    "Filled Squares": filled_squares,
    "Upside Down": upside_down,
    "Mirror": mirror,
    "Reverse": reverse_text,
    "QUNI": quni,
    "Special": special,
    "Parenthesized": parenthesized,
    "Alternating Bold": alternating_bold,
    "Alternating Sans": alternating_sans,
    "Alternating Script": alternating_script,
    "Alternating Gothic": alternating_gothic,
    "Alternating Double": alternating_double,
    "Alternating Monospace": alternating_mono,
    "Alternating Fullwidth": alternating_fullwidth,
    "Alternating Italic": alternating_italic,
    # ستایلە نوێیەکان بە تەواوی لێرەدا قایمکراون:
    "Slash Strike": style_slash_strike,
    "Sans Bubbles": style_sans_bubbles,
    "Quni Custom": style_qu_custom,
    "Corrupted Fire": style_corrupted_fire,
    "Ansi Style": style_ansi,
    "Wide Style": style_wide,
    "Cursive Curly": style_cursive,
    "Tiny Lower": style_tiny_lower,
    "Accent Style": style_accent,
}

STYLE_NAMES = list(STYLE_FUNCTIONS.keys())
ITEMS_PER_PAGE = 9  # ٩ ستایل لە هەر پەڕەیەکدا نیشان دەدرێت بۆ ئەوەی پەڕەبەپەڕە بێت


def convert_text(text: str, style_name: str) -> str:
  function = STYLE_FUNCTIONS.get(style_name)
  if function is None:
    return text
  try:
    return function(text)
  except Exception as error:
    logger.error("Style conversion error [%s]: %s", style_name, error)
    return text


def style_button_text(style_name: str) -> str:
  preview = convert_text(style_name, style_name)
  if len(preview) > 28:
    preview = preview[:28]
  return preview


def build_style_keyboard(page: int = 0, selected_index: int = -1):
  total_pages = (len(STYLE_NAMES) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
  page = max(0, min(page, total_pages - 1))

  start_idx = page * ITEMS_PER_PAGE
  end_idx = min(start_idx + ITEMS_PER_PAGE, len(STYLE_NAMES))

  buttons = []
  current_row = []

  for index in range(start_idx, end_idx):
    style_name = STYLE_NAMES[index]
    button_text = style_button_text(style_name)
    if index == selected_index:
      button_text = "✓ " + button_text
    current_row.append(
        InlineKeyboardButton(
            text=button_text, callback_data=f"style:{index}:{page}"
        )
    )
    if len(current_row) == 3:
      buttons.append(current_row)
      current_row = []

  if current_row:
    buttons.append(current_row)

  # دوگمەکانی هاتوچۆ (پێشتر و داهاتوو) بۆ سیستەمی پەڕەبەپەڕە
  nav_row = []
  if page > 0:
    nav_row.append(
        InlineKeyboardButton(
            text="⬅️ پێشتر", callback_data=f"page:{page - 1}:{selected_index}"
        )
    )

  nav_row.append(
      InlineKeyboardButton(
          text=f"📄 {page + 1}/{total_pages}", callback_data="noop"
      )
  )

  if page < total_pages - 1:
    nav_row.append(
        InlineKeyboardButton(
            text="داهاتوو ➡️", callback_data=f"page:{page + 1}:{selected_index}"
        )
    )

  if nav_row:
    buttons.append(nav_row)

  return InlineKeyboardMarkup(buttons)


# =========================================================
# DATABASE OPERATIONS
# =========================================================


def init_users_db():
  conn = sqlite3.connect(USERS_DB, timeout=30, check_same_thread=False)
  try:
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
        """)
    conn.commit()
  finally:
    conn.close()


def track_user(user):
  if not user:
    return False
  now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  conn = sqlite3.connect(USERS_DB, timeout=30, check_same_thread=False)
  try:
    conn.execute("PRAGMA busy_timeout = 30000")
    existing = conn.execute(
        "SELECT user_id FROM users WHERE user_id = ?", (user.id,)
    ).fetchone()
    is_new = existing is None
    conn.execute(
        """
            INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_seen = excluded.last_seen
        """,
        (user.id, user.username, user.first_name, user.last_name, now, now),
    )
    conn.commit()
    return is_new
  finally:
    conn.close()


async def notify_admin_new_user(bot, user):
  if not user:
    return
  username = f"@{user.username}" if user.username else "بێ Username"
  name = user.full_name or "بێ ناو"
  text = (
      "🆕 <b>بەکارهێنەری نوێ!</b>\n\n"
      f"👤 ناو: {html.escape(name)}\n"
      f"📛 Username: {html.escape(username)}\n"
      f"🆔 User ID: <code>{user.id}</code>"
  )
  keyboard = InlineKeyboardMarkup(
      [[InlineKeyboardButton("👤 View Profile", url=f"tg://user?id={user.id}")]]
  )
  for admin_id in ADMIN_IDS:
    try:
      await bot.send_message(
          chat_id=admin_id, text=text, parse_mode="HTML", reply_markup=keyboard
      )
    except Exception as error:
      logger.error("Failed to notify admin %s: %s", admin_id, error)


def get_users():
  conn = sqlite3.connect(USERS_DB, timeout=30, check_same_thread=False)
  try:
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn.execute(
        "SELECT user_id, username, first_name, last_name, first_seen, last_seen"
        " FROM users ORDER BY last_seen DESC"
    ).fetchall()
  finally:
    conn.close()


def is_admin(user_id):
  return user_id in ADMIN_IDS


def get_user_by_id(user_id):
  conn = sqlite3.connect(USERS_DB, timeout=30, check_same_thread=False)
  try:
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn.execute(
        "SELECT user_id, username, first_name, last_name, first_seen, last_seen"
        " FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
  finally:
    conn.close()


def profile_keyboard(user_id):
  return InlineKeyboardMarkup(
      [[InlineKeyboardButton("👤 View Profile", url=f"tg://user?id={user_id}")]]
  )


def format_user_profile(user):
  user_id, username, first_name, last_name, first_seen, last_seen = user
  name = " ".join(x for x in [first_name, last_name] if x) or "بێ ناو"
  uname = f"@{username}" if username else "بێ username"
  return (
      "👤 زانیاری بەکارهێنەر\n\n"
      f"📛 ناو: {html.escape(name)}\n"
      f"🔗 Username: {html.escape(uname)}\n"
      f"🆔 User ID: <code>{user_id}</code>\n"
      f"🕐 یەکەم جار: {html.escape(first_seen)}\n"
      f"🕐 دوا جار: {html.escape(last_seen)}"
  )


async def user_command(update, context):
  if not update.effective_user or not is_admin(update.effective_user.id):
    if update.message:
      await update.message.reply_text("❌ ئەم فرمانە تەنها بۆ ئەدمینە.")
    return
  if not update.message or not context.args:
    await update.message.reply_text("ℹ️ شێوازی بەکارهێنان:\n/user USER_ID")
    return
  try:
    user_id = int(context.args[0])
  except ValueError:
    await update.message.reply_text("❌ User ID دەبێت ژمارە بێت.")
    return
  user = get_user_by_id(user_id)
  if not user:
    await update.message.reply_text(
        "❌ ئەم User ID ـیە لە دیتابەیسەکەدا نییە."
    )
    return
  await update.message.reply_text(
      format_user_profile(user),
      parse_mode="HTML",
      reply_markup=profile_keyboard(user_id),
  )


async def user_profile_callback(update, context):
  query = update.callback_query
  if not query or not query.from_user or not is_admin(query.from_user.id):
    if query:
      await query.answer("❌ تەنها ئەدمین دەتوانێت ئەمە ببینێت.", show_alert=True)
    return
  try:
    user_id = int((query.data or "").split(":", 1)[1])
  except (ValueError, IndexError):
    return
  user = get_user_by_id(user_id)
  if not user:
    return
  await query.answer()
  await query.message.reply_text(
      format_user_profile(user),
      parse_mode="HTML",
      reply_markup=profile_keyboard(user_id),
  )


async def users_command(update, context):
  if not update.effective_user or not is_admin(update.effective_user.id):
    if update.message:
      await update.message.reply_text("❌ ئەم فرمانە تەنها بۆ ئەدمینە.")
    return
  users = get_users()
  if not users:
    await update.message.reply_text("📭 هیچ بەکارهێنەرێک تۆمار نەکراوە.")
    return
  chunk_size = 10
  for start_index in range(0, len(users), chunk_size):
    chunk = users[start_index : start_index + chunk_size]
    lines = [
        f"👥 کۆی گشتی بەکارهێنەران: {len(users)}",
        f"📄 بەکارهێنەرەکان {start_index + 1} - {start_index + len(chunk)}",
        "",
    ]
    keyboard = []
    for i, (
        user_id,
        username,
        first_name,
        last_name,
        first_seen,
        last_seen,
    ) in enumerate(chunk, start_index + 1):
      name = " ".join(x for x in [first_name, last_name] if x) or "بێ ناو"
      uname = f"@{username}" if username else "بێ username"
      lines.append(
          f"{i}. {html.escape(name)} | {html.escape(uname)}\n"
          f"🆔 <code>{user_id}</code>\n🕐 یەکەم: {first_seen} | دوا: {last_seen}"
      )
      keyboard.append([
          InlineKeyboardButton(
              f"👤 View Profile — {name[:35]}",
              callback_data=f"profile:{user_id}",
          )
      ])
    await update.message.reply_text(
        "\n\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# FORCE JOIN HELPERS
# =========================================================


async def is_subscribed(bot, user_id):
  try:
    member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    return member.status in (
        "member",
        "administrator",
        "creator",
    ) or (member.status == "restricted" and getattr(member, "is_member", False))
  except Exception as error:
    logger.error("Subscription check failed: %s", error)
    return False


def force_join_keyboard():
  return InlineKeyboardMarkup([
      [InlineKeyboardButton("📢 جۆینی چەناڵ", url=CHANNEL_LINK)],
      [InlineKeyboardButton("✅ پشکنینی جۆین", callback_data="check_join")],
  ])


async def require_subscription(update, context):
  user = update.effective_user
  if not user:
    return False
  if await is_subscribed(context.bot, user.id):
    return True
  text = (
      "🔒 بۆ بەکارهێنانی بۆتەکە، سەرەتا دەبێت جۆینی چەناڵەکەمان بکەیت.\n\n"
      "1️⃣ لەسەر «📢 جۆینی چەناڵ» دابگرە\n"
      "2️⃣ پاشان «✅ پشکنینی جۆین» دابگرە"
  )
  if update.message:
    await update.message.reply_text(text=text, reply_markup=force_join_keyboard())
  return False


async def check_join(update, context):
  query = update.callback_query
  if not query:
    return
  if await is_subscribed(context.bot, query.from_user.id):
    await query.answer("✅ جۆینەکەت پشتڕاست کرایەوە.", show_alert=True)
    try:
      await query.edit_message_text(
          text="✅ جۆینەکەت پشتڕاست کرایەوە.\n\n"
          "ئێستا دەقێکی ئینگلیزی بنێرە بۆ گۆڕینی ستایل."
      )
    except Exception:
      pass
  else:
    await query.answer("❌ هێشتا جۆینی چەناڵەکەت نەکردووە.", show_alert=True)


# =========================================================
# BOT HANDLERS
# =========================================================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message:
    return
  is_new = track_user(update.effective_user)
  if is_new:
    await notify_admin_new_user(context.bot, update.effective_user)
  if not await require_subscription(update, context):
    return
  await update.message.reply_text(
      text="ئێستا دەقێکی ئینگلیزی بنێرە بۆ گۆڕینی ستایل."
  )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message:
    return
  is_new = track_user(update.effective_user)
  if is_new:
    await notify_admin_new_user(context.bot, update.effective_user)
  if not await require_subscription(update, context):
    return
  if not update.message.text:
    return
  user_text = update.message.text
  if not user_text.strip():
    return
  if len(user_text) > 4000:
    await update.message.reply_text(
        "⚠️ تکایە دەقەکەت کورتتر بکەوە؛ زۆرترین قەبارەی پشتیوانیکراو ٤٠٠٠ پیتە."
    )
    return
  context.user_data["current_text"] = user_text
  context.user_data["selected_style"] = -1
  context.user_data["current_page"] = 0
  keyboard = build_style_keyboard(page=0, selected_index=-1)
  safe_text = html.escape(user_text)
  sent_message = await update.message.reply_text(
      text=safe_text, reply_markup=keyboard, parse_mode="HTML"
  )
  context.user_data["style_message_id"] = sent_message.message_id


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  if not query:
    return
  is_new = track_user(query.from_user)
  if is_new:
    await notify_admin_new_user(context.bot, query.from_user)
  if not await is_subscribed(context.bot, query.from_user.id):
    await query.answer(
        "❌ بۆ بەکارهێنانی بۆتەکە دەبێت سەرەتا جۆینی چەناڵ بکەیت.",
        show_alert=True,
    )
    try:
      await query.message.reply_text(
          text="🔒 سەرەتا جۆینی چەناڵەکە بکە، پاشان بگەڕێوە بۆ بۆتەکە.",
          reply_markup=force_join_keyboard(),
      )
    except Exception:
      pass
    return

  data = query.data or ""
  if data == "noop":
    await query.answer()
    return

  # بەڕێوەبردنی گۆڕینی پەڕەکان (Pagination Handler)
  if data.startswith("page:"):
    try:
      parts = data.split(":")
      target_page = int(parts[1])
      selected_index = int(parts[2])
    except (ValueError, IndexError):
      return
    await query.answer()
    context.user_data["current_page"] = target_page
    selected_style = context.user_data.get("selected_style", -1)
    keyboard = build_style_keyboard(
        page=target_page, selected_index=selected_style
    )
    try:
      await query.edit_message_reply_markup(reply_markup=keyboard)
    except Exception as error:
      if "Message is not modified" not in str(error):
        logger.error("Pagination markup edit failed: %s", error)
    return

  if not data.startswith("style:"):
    return

  try:
    parts = data.split(":")
    style_index = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0
  except (ValueError, IndexError):
    return

  if style_index < 0 or style_index >= len(STYLE_NAMES):
    return

  current_message_id = context.user_data.get("style_message_id")
  if (
      current_message_id
      and query.message
      and query.message.message_id != current_message_id
  ):
    await query.answer("ئەم بەشەی ستایلە چالاک نییە.", show_alert=True)
    return

  user_text = context.user_data.get("current_text", "")
  if not user_text:
    try:
      await query.edit_message_text(text="تکایە دەقێکی نوێ بنێرە.")
    except Exception:
      pass
    return

  await query.answer()
  style_name = STYLE_NAMES[style_index]
  styled_text = convert_text(user_text, style_name)
  context.user_data["selected_style"] = style_index
  context.user_data["current_page"] = page
  keyboard = build_style_keyboard(page=page, selected_index=style_index)
  safe_styled_text = html.escape(styled_text)
  try:
    await query.edit_message_text(
        text=safe_styled_text, reply_markup=keyboard, parse_mode="HTML"
    )
  except Exception as error:
    if "Message is not modified" not in str(error):
      logger.error("Message edit failed: %s", error)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
  logger.error("Unhandled exception:", exc_info=context.error)


# =========================================================
# MAIN ASYNC ENGINE (FULLY NON-BLOCKING FOR RENDER)
# =========================================================


async def main():
  init_users_db()

  if not BOT_TOKEN:
    raise ValueError(
        "Missing BOT_TOKEN environment variable in Render > Environment"
    )

  application = ApplicationBuilder().token(BOT_TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(CommandHandler("users", users_command))
  application.add_handler(CommandHandler("user", user_command))
  application.add_handler(
      CallbackQueryHandler(user_profile_callback, pattern=r"^profile:\d+$")
  )
  application.add_handler(CallbackQueryHandler(check_join, pattern=r"^check_join$"))
  application.add_handler(
      CallbackQueryHandler(button_click, pattern=r"^(style:\d+:\d+|page:\d+:\-?\d+|noop)$")
  )
  application.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
  )
  application.add_error_handler(error_handler)

  port = int(os.environ.get("PORT", 10000))
  from werkzeug.serving import run_simple

  # Run Flask in background without blocking asyncio event loop.
  loop = asyncio.get_running_loop()
  loop.run_in_executor(
      None,
      lambda: run_simple("0.0.0.0", port, app, use_reloader=False, threaded=True),
  )

  logger.info("Flask server up and listening on port %d", port)
  logger.info("Bot starting Telegram Polling...")

  async with application:
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except (KeyboardInterrupt, SystemExit):
    pass
