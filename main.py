# =========================================================
# ENGLISH STYLE FONT BOT (RENDER OPTIMIZED & ENV CHANNEL)
# =========================================================

import logging
import html
import sqlite3
import os
import asyncio
from flask import Flask
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
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


def make_math_map(upper_start=None, lower_start=None, digit_start=None, exceptions=None):
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
    0x1D538, 0x1D552, 0x1D7D8,
    exceptions={"C": "ℂ", "H": "ℍ", "N": "ℕ", "P": "ℙ", "Q": "ℚ", "R": "ℝ", "Z": "ℤ"},
)
FRAKTUR_MAP = make_math_map(
    0x1D504, 0x1D51E,
    exceptions={"C": "ℭ", "H": "ℌ", "I": "ℑ", "R": "ℜ", "Z": "ℨ"},
)
BOLD_FRAKTUR_MAP = make_math_map(0x1D56C, 0x1D586)
SCRIPT_MAP = make_math_map(
    0x1D49C, 0x1D4B6,
    exceptions={"B": "ℬ", "E": "ℰ", "F": "ℱ", "H": "ℋ", "I": "ℐ", "L": "ℒ", "M": "ℳ", "R": "ℛ", "e": "ℯ", "g": "ℊ", "o": "ℴ"},
)
BOLD_SCRIPT_MAP = make_math_map(0x1D4D0, 0x1D4EA)

# Fix special Unicode characters in Script, Fraktur, and Double Struck maps.
SCRIPT_MAP.update({
    "B": "ℬ", "E": "ℰ", "F": "ℱ", "H": "ℋ", "I": "ℐ",
    "L": "ℒ", "M": "ℳ", "R": "ℛ", "e": "ℯ", "g": "ℊ", "o": "ℴ",
})
FRAKTUR_MAP.update({"C": "ℭ", "H": "ℌ", "I": "ℑ", "R": "ℜ", "Z": "ℨ"})
DOUBLE_STRUCK_MAP.update({
    "C": "ℂ", "H": "ℍ", "N": "ℕ", "P": "ℙ",
    "Q": "ℚ", "R": "ℝ", "Z": "ℤ",
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
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ",
    "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ",
    "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ",
    "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x",
    "y": "ʏ", "z": "ᴢ",
}


def small_caps(text):
    return "".join(SMALL_CAPS_MAP.get(char.lower(), char) for char in text)


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


def filled_circled(text):
    return "".join(
        NEGATIVE_CIRCLED_UPPER[UPPER.index(char.upper())]
        if char.upper() in UPPER else char
        for char in text
    )


SQUARED_UPPER = "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉"


def squares(text):
    return "".join(
        SQUARED_UPPER[UPPER.index(char.upper())]
        if char.isalpha() and char.upper() in UPPER else char
        for char in text
    )


NEGATIVE_SQUARED_UPPER = "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🅅🆆🆇🆈🆉"


def filled_squares(text):
    return "".join(
        NEGATIVE_SQUARED_UPPER[UPPER.index(char.upper())]
        if char.isalpha() and char.upper() in UPPER else char
        for char in text
    )


PARENTHESIZED_MAP = {
    "a": "⒜", "b": "⒝", "c": "⒞", "d": "⒟", "e": "⒠", "f": "⒡",
    "g": "⒢", "h": "⒣", "i": "⒤", "j": "⒥", "k": "⒦", "l": "⒧",
    "m": "⒨", "n": "⒩", "o": "⒪", "p": "⒫", "q": "⒬", "r": "⒭",
    "s": "⒮", "t": "⒯", "u": "⒰", "v": "⒱", "w": "⒲", "x": "⒳",
    "y": "⒴", "z": "⒵",
}


def parenthesized(text):
    return "".join(PARENTHESIZED_MAP.get(char.lower(), char) for char in text)


TINY_MAP = {
    "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "f": "ᶠ",
    "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ", "k": "ᵏ", "l": "ˡ",
    "m": "ᵐ", "n": "ⁿ", "o": "ᵒ", "p": "ᵖ", "q": "q", "r": "ʳ",
    "s": "ˢ", "t": "ᵗ", "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ",
    "y": "ʸ", "z": "ᶻ", "A": "ᴬ", "B": "ᴮ", "C": "ᶜ", "D": "ᴰ",
    "E": "ᴱ", "F": "ᶠ", "G": "ᴳ", "H": "ᴴ", "I": "ᴵ", "J": "ᴶ",
    "K": "ᴷ", "L": "ᴸ", "M": "ᴹ", "N": "ᴺ", "O": "ᴼ", "P": "ᴾ",
    "Q": "Q", "R": "ᴿ", "S": "ˢ", "T": "ᵀ", "U": "ᵁ", "V": "ⱽ",
    "W": "ᵂ", "X": "ˣ", "Y": "ʸ", "Z": "ᶻ", "0": "⁰", "1": "¹",
    "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷",
    "8": "⁸", "9": "⁹",
}


def tiny(text):
    return "".join(TINY_MAP.get(char, char) for char in text)


COMIC_MAP = {
    "A": "Ⱥ", "a": "ɑ", "B": "Ɓ", "b": "ɓ", "C": "Ƈ", "c": "ƈ",
    "D": "Đ", "d": "ɗ", "E": "Ɛ", "e": "ɛ", "F": "Ƒ", "f": "ƒ",
    "G": "Ɠ", "g": "ɠ", "H": "Ħ", "h": "ɦ", "I": "Ɨ", "i": "ɨ",
    "J": "Ɉ", "j": "ʝ", "K": "Ƙ", "k": "ƙ", "L": "Ł", "l": "ł",
    "M": "Ɯ", "m": "ɱ", "N": "Ɲ", "n": "ɲ", "O": "Ø", "o": "ø",
    "P": "Ƥ", "p": "ƥ", "Q": "Ɋ", "q": "ɋ", "R": "Ʀ", "r": "ɍ",
    "S": "Ş", "s": "ʂ", "T": "Ŧ", "t": "ŧ", "U": "Ʉ", "u": "ʉ",
    "V": "Ʋ", "v": "ʋ", "W": "Ŵ", "w": "ŵ", "X": "Ӿ", "x": "ӿ",
    "Y": "Ƴ", "y": "ɏ", "Z": "Ƶ", "z": "ƶ",
}


def comic(text):
    return apply_map(text, COMIC_MAP)


QUNI_MAP = {
    "A": "Ⱥ", "a": "Ⱥ", "B": "Ɓ", "b": "ƀ", "C": "Ƈ", "c": "ƈ",
    "D": "Đ", "d": "đ", "E": "Ɇ", "e": "ɇ", "F": "Ƒ", "f": "ƒ",
    "G": "Ǥ", "g": "ǥ", "H": "Ħ", "h": "ħ", "I": "Ɨ", "i": "ɨ",
    "J": "Ɉ", "j": "ɉ", "K": "Ƙ", "k": "ƙ", "L": "Ł", "l": "ł",
    "M": "M", "m": "ɱ", "N": "Ŋ", "n": "ŋ", "O": "Ø", "o": "ø",
    "P": "Ƥ", "p": "ƥ", "Q": "Ɋ", "q": "ɋ", "R": "Ɍ", "r": "ɍ",
    "S": "Ş", "s": "ş", "T": "Ŧ", "t": "ŧ", "U": "Ʉ", "u": "ʉ",
    "V": "Ʋ", "v": "ʋ", "W": "Ŵ", "w": "ŵ", "X": "Ӿ", "x": "ӿ",
    "Y": "Ɏ", "y": "ɏ", "Z": "Ƶ", "z": "ƶ",
}


def quni(text):
    return apply_map(text, QUNI_MAP)


SPECIAL_MAP = {
    "A": "Λ", "B": "β", "C": "C", "D": "ᗪ", "E": "Σ", "F": "Ғ",
    "G": "Ɠ", "H": "卄", "I": "I", "J": "Ј", "K": "Ҡ", "L": "Ł",
    "M": "爪", "N": "И", "O": "Ө", "P": "尸", "Q": "Q", "R": "尺",
    "S": "Ѕ", "T": "Ŧ", "U": "Ц", "V": "Ѵ", "W": "Ш", "X": "Ж",
    "Y": "Ұ", "Z": "乙", "a": "α", "b": "в", "c": "¢", "d": "∂",
    "e": "є", "f": "ƒ", "g": "ɠ", "h": "н", "i": "ι", "j": "נ",
    "k": "к", "l": "ℓ", "m": "м", "n": "η", "o": "σ", "p": "ρ",
    "q": "զ", "r": "я", "s": "ѕ", "t": "т", "u": "υ", "v": "ν",
    "w": "ω", "x": "χ", "y": "у", "z": "z",
}


def special(text):
    return apply_map(text, SPECIAL_MAP)


UPSIDE_DOWN_MAP = {
    "a": "ɐ", "b": "q", "c": "ɔ", "d": "p", "e": "ǝ", "f": "ɟ",
    "g": "ƃ", "h": "ɥ", "i": "ᴉ", "j": "ɾ", "k": "ʞ", "l": "ʃ",
    "m": "ɯ", "n": "u", "o": "o", "p": "d", "q": "b", "r": "ɹ",
    "s": "s", "t": "ʇ", "u": "n", "v": "ʌ", "w": "ʍ", "x": "x",
    "y": "ʎ", "z": "z", "A": "∀", "B": "ᗺ", "C": "Ɔ", "D": "◖",
    "E": "Ǝ", "F": "Ⅎ", "G": "Ꭾ", "H": "H", "I": "I", "J": "Ⴑ",
    "K": "⋊", "L": "⅃", "M": "M", "N": "N", "O": "O", "P": "Ԁ",
    "Q": "Q", "R": "Я", "S": "S", "T": "⊥", "U": "∩", "V": "Λ",
    "W": "M", "X": "X", "Y": "⅄", "Z": "Z", "0": "0", "1": "Ɩ",
    "2": "ᄅ", "3": "Ɛ", "4": "ㄣ", "5": "ϛ", "6": "9", "7": "ㄥ",
    "8": "8", "9": "6",
}


def upside_down(text):
    return "".join(UPSIDE_DOWN_MAP.get(char, char) for char in reversed(text))


def reverse_text(text):
    return text[::-1]


MIRROR_MAP = {
    "A": "A", "B": "ᗺ", "C": "Ɔ", "D": "◖", "E": "Ǝ", "F": "Ⅎ",
    "G": "Ꭾ", "H": "H", "I": "I", "J": "Ⴑ", "K": "⋊", "L": "⅃",
    "M": "M", "N": "И", "O": "O", "P": "Ԁ", "Q": "Q", "R": "Я",
    "S": "S", "T": "⊥", "U": "∩", "V": "Λ", "W": "M", "X": "X",
    "Y": "⅄", "Z": "Z", "a": "ɒ", "b": "d", "c": "ↄ", "d": "b",
    "e": "ɘ", "f": "ɟ", "g": "ᵷ", "h": "ʜ", "i": "i", "j": "ɾ",
    "k": "ʞ", "l": "l", "m": "m", "n": "n", "o": "o", "p": "q",
    "q": "p", "r": "ɿ", "s": "s", "t": "t", "u": "u", "v": "v",
    "w": "w", "x": "x", "y": "y", "z": "z",
}


def mirror(text):
    return "".join(MIRROR_MAP.get(char, char) for char in text[::-1])


def identity(text):
    return text


def serif(text):
    return text


def serif_italic(text):
    return apply_map(text, ITALIC_SERIF_MAP)


def gothic_style(text):
    return apply_map(text, FRAKTUR_MAP)


def typewriter(text):
    return apply_map(text, MONOSPACE_MAP)


# Functions for the 4 new styles
def strikethrough(text):
    return "".join(char + "\u0336" for char in text)


def zalgo_text(text):
    return "".join(char + "\u033d" for char in text)


CYRILLIC_MAP = {
    "A": "Ҽ", "a": "Ҽ", "B": "Ɓ", "b": "ƀ", "C": "С", "c": "с",
    "D": "Đ", "d": "đ", "E": "Ӗ", "e": "Ҹ", "F": "Ғ", "f": "ƒ",
    "G": "Ҕ", "g": "ӷ", "H": "Ԝ", "i": "ɪ", "I": "І", "L": "Լ",
    "l": "ℓ", "M": "Ɱ", "N": "Ͷ", "n": "ᴎ", "O": "Ꙭ", "o": "ꙭ",
    "R": "Я", "r": "ɼ", "S": "Ş", "s": "ş", "T": "Ͳ", "t": "ƭ",
    "U": "Ս", "u": "υ", "V": "Ѵ", "v": "ѵ", "W": "Ш", "w": "ш",
    "X": "Ӿ", "x": "ӿ", "Y": "Ұ", "y": "ұ", "Z": "乙", "z": "ƶ"
}

def cyrillic_glitch(text):
    return apply_map(text, CYRILLIC_MAP)


DECORATIVE_MAP = {
    "A": "Ｅ", "a": "𝚎", "B": "𐌁", "b": "𝕓", "C": "𐌂", "c": "𝕔",
    "D": "𐌃", "d": "𝕕", "E": "𐌄", "e": "𝚎", "F": "𐌅", "f": "𝕗",
    "G": "𐌆", "g": "𝕘", "H": "𐌇", "h": "𝕙", "I": "𐌈", "i": "𝔦",
    "J": "𐌉", "j": "𝕛", "K": "𐌊", "k": "𝕜", "L": "𐌋", "l": "𝕝",
    "M": "𐌌", "m": "𝕞", "N": "𐌍", "n": "𝕟", "O": "𐌎", "o": "𝔬",
    "P": "𐌏", "p": "𝕡", "Q": "𐌐", "q": "𝕢", "R": "𐌑", "r": "𝕣",
    "S": "𐌒", "s": "𝕤", "T": "𐌓", "t": "𝕥", "U": "𐌔", "u": "𝔲",
    "V": "𐌕", "v": "𝔳", "W": "𐌖", "w": "𝔴", "X": "𐌗", "x": "𝔵",
    "Y": "𐌘", "y": "𝔶", "Z": "𐌙", "z": "𝔷"
}

def decorative_arrows(text):
    return apply_map(text, DECORATIVE_MAP)


def case_map(text, mapping, mode):
    if mode == "upper":
        text = text.upper()
    elif mode == "lower":
        text = text.lower()
    return apply_map(text, mapping)


def bold_serif_caps(text): return case_map(text, BOLD_SERIF_MAP, "upper")
def bold_serif_lower(text): return case_map(text, BOLD_SERIF_MAP, "lower")
def italic_serif_caps(text): return case_map(text, ITALIC_SERIF_MAP, "upper")
def italic_serif_lower(text): return case_map(text, ITALIC_SERIF_MAP, "lower")
def bold_italic_caps(text): return case_map(text, BOLD_ITALIC_MAP, "upper")
def bold_italic_lower(text): return case_map(text, BOLD_ITALIC_MAP, "lower")
def sans_caps(text): return case_map(text, SANS_MAP, "upper")
def sans_lower(text): return case_map(text, SANS_MAP, "lower")
def sans_bold_lower(text): return case_map(text, SANS_BOLD_MAP, "lower")
def sans_italic_caps(text): return case_map(text, SANS_ITALIC_MAP, "upper")
def sans_italic_lower(text): return case_map(text, SANS_ITALIC_MAP, "lower")
def sans_bold_italic_caps(text): return case_map(text, SANS_BOLD_ITALIC_MAP, "upper")
def sans_bold_italic_lower(text): return case_map(text, SANS_BOLD_ITALIC_MAP, "lower")
def script_caps(text): return case_map(text, SCRIPT_MAP, "upper")
def script_lower(text): return case_map(text, SCRIPT_MAP, "lower")
def bold_script_caps(text): return case_map(text, BOLD_SCRIPT_MAP, "upper")
def bold_script_lower(text): return case_map(text, BOLD_SCRIPT_MAP, "lower")
def gothic_caps(text): return case_map(text, FRAKTUR_MAP, "upper")
def gothic_lower(text): return case_map(text, FRAKTUR_MAP, "lower")
def bold_gothic_caps(text): return case_map(text, BOLD_FRAKTUR_MAP, "upper")
def bold_gothic_lower(text): return case_map(text, BOLD_FRAKTUR_MAP, "lower")
def double_struck_caps(text): return case_map(text, DOUBLE_STRUCK_MAP, "upper")
def double_struck_lower(text): return case_map(text, DOUBLE_STRUCK_MAP, "lower")
def monospace_caps(text): return case_map(text, MONOSPACE_MAP, "upper")
def monospace_lower(text): return case_map(text, MONOSPACE_MAP, "lower")
def fullwidth_caps(text): return case_map(text, FULLWIDTH_MAP, "upper")
def fullwidth_lower(text): return case_map(text, FULLWIDTH_MAP, "lower")


def alternating(text, map_a, map_b):
    result = []
    letter_index = 0
    for char in text:
        if char.isalpha():
            result.append(map_a.get(char, char) if letter_index % 2 == 0 else map_b.get(char, char))
            letter_index += 1
        else:
            result.append(char)
    return "".join(result)


def alternating_bold(text): return alternating(text, BOLD_SERIF_MAP, BOLD_ITALIC_MAP)
def alternating_sans(text): return alternating(text, SANS_MAP, SANS_BOLD_MAP)
def alternating_script(text): return alternating(text, SCRIPT_MAP, BOLD_SCRIPT_MAP)
def alternating_gothic(text): return alternating(text, FRAKTUR_MAP, BOLD_FRAKTUR_MAP)
def alternating_double(text): return alternating(text, DOUBLE_STRUCK_MAP, BOLD_SERIF_MAP)
def alternating_mono(text): return alternating(text, MONOSPACE_MAP, SANS_MAP)
def alternating_fullwidth(text): return alternating(text, FULLWIDTH_MAP, BOLD_SERIF_MAP)
def alternating_italic(text): return alternating(text, ITALIC_SERIF_MAP, BOLD_ITALIC_MAP)


def bold_title(text): return apply_map(text.title(), BOLD_SERIF_MAP)
def script_title(text): return apply_map(text.title(), SCRIPT_MAP)
def gothic_title(text): return apply_map(text.title(), FRAKTUR_MAP)
def sans_title(text): return apply_map(text.title(), SANS_MAP)
def double_title(text): return apply_map(text.title(), DOUBLE_STRUCK_MAP)
def mono_title(text): return apply_map(text.title(), MONOSPACE_MAP)


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
    "Sans": lambda x: apply_map(x, SANS_MAP),
    "Monospace": lambda x: apply_map(x, MONOSPACE_MAP),
    "Fullwidth": lambda x: apply_map(x, FULLWIDTH_MAP),
    "Typewriter": typewriter,
    "Serif": serif,
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
    "Strikethrough": strikethrough,
    "Zalgo": zalgo_text,
    "Cyrillic": cyrillic_glitch,
    "Decorative": decorative_arrows,
    "Bold Serif Caps": bold_serif_caps,
    "Bold Serif Lower": bold_serif_lower,
    "Italic Serif Caps": italic_serif_caps,
    "Italic Serif Lower": italic_serif_lower,
    "Bold Italic Caps": bold_italic_caps,
    "Bold Italic Lower": bold_italic_lower,
    "Sans Caps": sans_caps,
    "Sans Lower": sans_lower,
    "Sans Bold Lower": sans_bold_lower,
    "Sans Italic Caps": sans_italic_caps,
    "Sans Italic Lower": sans_italic_lower,
    "Sans Bold Italic Caps": sans_bold_italic_caps,
    "Sans Bold Italic Lower": sans_bold_italic_lower,
    "Script Caps": script_caps,
    "Script Lower": script_lower,
    "Bold Script Caps": bold_script_caps,
    "Bold Script Lower": bold_script_lower,
    "Gothic Caps": gothic_caps,
    "Gothic Lower": gothic_lower,
    "Bold Gothic Caps": bold_gothic_caps,
    "Bold Gothic Lower": bold_gothic_lower,
    "Double Struck Caps": double_struck_caps,
    "Double Struck Lower": double_struck_lower,
    "Monospace Caps": monospace_caps,
    "Monospace Lower": monospace_lower,
    "Fullwidth Caps": fullwidth_caps,
    "Fullwidth Lower": fullwidth_lower,
    "Alternating Bold": alternating_bold,
    "Alternating Sans": alternating_sans,
    "Alternating Script": alternating_script,
    "Alternating Gothic": alternating_gothic,
    "Alternating Double": alternating_double,
    "Alternating Monospace": alternating_mono,
    "Alternating Fullwidth": alternating_fullwidth,
    "Alternating Italic": alternating_italic,
    "Bold Title": bold_title,
    "Script Title": script_title,
    "Gothic Title": gothic_title,
    "Sans Title": sans_title,
    "Double Title": double_title,
    "Mono Title": mono_title,
}

STYLE_NAMES = list(STYLE_FUNCTIONS.keys())


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


def build_style_keyboard(selected_index: int = -1):
    buttons = []
    for i in range(0, len(STYLE_NAMES), 3):
        row = []
        for index in range(i, min(i + 3, len(STYLE_NAMES))):
            style_name = STYLE_NAMES[index]
            button_text = style_button_text(style_name)
            if index == selected_index:
                button_text = "✓ " + button_text
            row.append(InlineKeyboardButton(text=button_text, callback_data=f"style:{index}"))
        buttons.append(row)
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
        conn.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_seen = excluded.last_seen
        """, (user.id, user.username, user.first_name, user.last_name, now, now))
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
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 View Profile", url=f"tg://user?id={user.id}")]
    ])
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
            "SELECT user_id, username, first_name, last_name, first_seen, last_seen "
            "FROM users ORDER BY last_seen DESC"
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
            "SELECT user_id, username, first_name, last_name, first_seen, last_seen "
            "FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def profile_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 View Profile", url=f"tg://user?id={user_id}")]
    ])


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
        await update.message.reply_text("❌ ئەم User ID ـیە لە دیتابەیسەکەدا نییە.")
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
        chunk = users[start_index:start_index + chunk_size]
        lines = [
            f"👥 کۆی گشتی بەکارهێنەران: {len(users)}",
            f"📄 بەکارهێنەرەکان {start_index + 1} - {start_index + len(chunk)}",
            "",
        ]
        keyboard = []
        for i, (user_id, username, first_name, last_name, first_seen, last_seen) in enumerate(
            chunk, start_index + 1
        ):
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
        return (
            member.status in ("member", "administrator", "creator")
            or (
                member.status == "restricted"
                and getattr(member, "is_member", False)
            )
        )
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
    await update.message.reply_text(text="ئێستا دەقێکی ئینگلیزی بنێرە بۆ گۆڕینی ستایل.")


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
    keyboard = build_style_keyboard(selected_index=-1)
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
    await query.answer()
    data = query.data or ""
    if not data.startswith("style:"):
        return
    try:
        style_index = int(data.split(":", 1)[1])
    except (ValueError, IndexError):
        return
    if style_index < 0 or style_index >= len(STYLE_NAMES):
        return
    current_message_id = context.user_data.get("style_message_id")
    if current_message_id and query.message and query.message.message_id != current_message_id:
        await query.answer("ئەم بەشەی ستایلە چالاک نییە.", show_alert=True)
        return
    user_text = context.user_data.get("current_text", "")
    if not user_text:
        try:
            await query.edit_message_text(text="تکایە دەقێکی نوێ بنێرە.")
        except Exception:
            pass
        return
    style_name = STYLE_NAMES[style_index]
    styled_text = convert_text(user_text, style_name)
    context.user_data["selected_style"] = style_index
    keyboard = build_style_keyboard(selected_index=style_index)
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
        raise ValueError("Missing BOT_TOKEN environment variable in Render > Environment")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("user", user_command))
    application.add_handler(
        CallbackQueryHandler(user_profile_callback, pattern=r"^profile:\d+$")
    )
    application.add_handler(CallbackQueryHandler(check_join, pattern=r"^check_join$"))
    application.add_handler(CallbackQueryHandler(button_click, pattern=r"^style:\d+$"))
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
