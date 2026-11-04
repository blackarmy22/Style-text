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


NEGATIVE_SQUARED_UPPER = "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉"


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


# لێرەدا فەنکشنە بنەڕەتییەکان وەک خۆیان دانراون
def bold_serif(text): return apply_map(text, BOLD_SERIF_MAP)
def italic_serif(text): return apply_map(text, ITALIC_SERIF_MAP)
def bold_italic(text): return apply_map(text, BOLD_ITALIC_MAP)
def sans(text): return apply_map(text, SANS_MAP)
def sans_bold(text): return apply_map(text, SANS_BOLD_MAP)
def sans_italic(text): return apply_map(text, SANS_ITALIC_MAP)
def sans_bold_italic(text): return apply_map(text, SANS_BOLD_ITALIC_MAP)
def script(text): return apply_map(text, SCRIPT_MAP)
def bold_script(text): return apply_map(text, BOLD_SCRIPT_MAP)
def gothic(text): return apply_map(text, FRAKTUR_MAP)
def bold_gothic(text): return apply_map(text, BOLD_FRAKTUR_MAP)
def double_struck(text): return apply_map(text, DOUBLE_STRUCK_MAP)
def monospace(text): return apply_map(text, MONOSPACE_MAP)
def fullwidth(text): return apply_map(text, FULLWIDTH_MAP)


# =========================================================
# THE 9 NEW USER CUSTOM STYLES ADDED HERE
# =========================================================

def custom_style_1(text):
    return "".join(char + "\u0336" for char in text)

SQUARE_CAPS_MAP = {
    "A": "ᗩ", "B": "ᗷ", "C": "ᑕ", "D": "ᗪ", "E": "E", "F": "ᖴ", "G": "G",
    "H": "ᕼ", "I": "I", "J": "ᒍ", "K": "K", "L": "ᒪ", "M": "ᗰ", "N": "ᑎ",
    "O": "O", "P": "ᑭ", "Q": "ⵕ", "R": "ᖇ", "S": "Տ", "T": "T", "U": "ᑌ",
    "V": "ᐯ", "W": "ᗯ", "X": "᙭", "Y": "Ƴ", "Z": "Ȝ",
    "a": "ᵅ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "f": "ᶠ", "g": "ᵍ",
    "h": "ʰ", "i": "ⁱ", "j": "ʲ", "k": "ᵏ", "l": "ˡ", "m": "ᵐ", "n": "ⁿ",
    "o": "ᵒ", "p": "ᵖ", "q": "𐌵", "r": "ʳ", "s": "ˢ", "t": "ᵗ", "u": "ᵘ",
    "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ"
}
def custom_style_2(text):
    return apply_map(text, SQUARE_CAPS_MAP)

CUSTOM_COMIC_MAP = {
    "A": "Ⱥ", "a": "Ⱥ", "B": "ҍ", "b": "ҍ", "C": "ç", "c": "ç",
    "D": "ժ", "d": "ժ", "E": "ҽ", "e": "ҽ", "F": "ƒ", "f": "ƒ",
    "G": "ց", "g": "ց", "H": "ℋ", "h": "ԋ", "I": "İ", "i": "į",
    "J": "Ĵ", "j": "ʝ", "K": "Ҡ", "k": "ƙ", "L": "Լ", "l": "ℓ",
    "M": "ℳ", "m": "ɱ", "N": "ղ", "n": "ղ", "O": "Ø", "o": "ø",
    "P": "Ƥ", "p": "ƥ", "Q": "ⵕ", "q": "զ", "R": "ℛ", "r": "ɾ",
    "S": "Տ", "s": "ʂ", "T": "Ƭ", "t": "ƭ", "U": "Մ", "u": "ʉ",
    "V": "Ʋ", "v": "ʋ", "W": "Ɯ", "w": "ŵ", "X": "Ӿ", "x": "ӿ",
    "Y": "Ƴ", "y": "ɏ", "Z": "ȥ", "z": "ȥ"
}
def custom_style_3(text):
    return apply_map(text, CUSTOM_COMIC_MAP)

def custom_style_4(text):
    return "".join(char + "\u035d" for char in text)

CYRILLIC_MIX_MAP = {
    "A": "ﾑ", "a": "ﾑ", "B": "乃", "b": "乃", "C": "ᄃ", "c": "ᄃ",
    "D": "り", "d": "り", "E": "乇", "e": "乇", "F": "ｷ", "f": "ｷ",
    "G": "G", "g": "g", "H": "ん", "h": "ん", "I": "ﾉ", "i": "ﾉ",
    "J": "ﾌ", "j": "ﾌ", "K": "Ƙ", "k": "Ƙ", "L": "ﾚ", "l": "ﾚ",
    "M": "爪", "m": "爪", "N": "刀", "n": "刀", "O": "の", "o": "の",
    "P": "尸", "p": "尸", "Q": "Q", "q": "q", "R": "尺", "r": "尺",
    "S": "丂", "s": "丂", "T": "丁", "t": "丁", "U": "Ц", "u": "Ц",
    "V": "√", "v": "√", "W": "Ш", "w": "Ш", "X": "ﾒ", "x": "ﾒ",
    "Y": "ㄚ", "y": "ㄚ", "Z": "乙", "z": "乙"
}
def custom_style_5(text):
    return apply_map(text, CYRILLIC_MIX_MAP)

AESTHETIC_WIDE_MAP = {
    "A": "卂", "a": "卂", "B": "乃", "b": "乃", "C": "匚", "c": "匚",
    "D": "ᗪ", "d": "ᗪ", "E": "乇", "e": "乇", "F": "千", "f": "千",
    "G": "Ꮆ", "g": "Ꮆ", "H": "ᕼ", "h": "ᕼ", "I": "丨", "i": "丨",
    "J": "ᒍ", "j": "ᒍ", "K": "Ҝ", "k": "Ҝ", "L": "ㄥ", "l": "ㄥ",
    "M": "爪", "m": "爪", "N": "几", "n": "几", "O": "ㄖ", "o": "ㄖ",
    "P": "卩", "p": "卩", "Q": "Q", "q": "Q", "R": "尺", "r": "尺",
    "S": "丂", "s": "丂", "T": "ㄒ", "t": "ㄒ", "U": "ㄩ", "u": "ㄩ",
    "V": "ᐯ", "v": "ᐯ", "W": "山", "w": "山", "X": "乂", "x": "乂",
    "Y": "ㄚ", "y": "ㄚ", "Z": "乙", "z": "乙"
}
def custom_style_6(text):
    return apply_map(text, AESTHETIC_WIDE_MAP)

BUBBLE_CURSIVE_MAP = {
    "A": "ꪖ", "a": "ꪖ", "B": "Ⴆ", "b": "Ⴆ", "C": "ꪜ", "c": "ꪜ",
    "D": "ԃ", "d": "ԃ", "E": "ꫀ", "e": "ꫀ", "F": "ᠻ", "f": "ᠻ",
    "G": "ɠ", "g": "ɠ", "H": "ԗ", "h": "ԗ", "I": "ⅈ", "i": "ⅈ",
    "J": "𝕛", "j": "𝕛", "K": "𝕜", "k": "𝕜", "L": "ꪶ", "l": "ꪶ",
    "M": "ꪑ", "m": "ꪑ", "N": "ꪀ", "n": "ꪀ", "O": "ꪮ", "o": "ꪮ",
    "P": "ρ", "p": "ρ", "Q": "Ɋ", "q": "Ɋ", "R": "᥅", "r": "᥅",
    "S": "ડ", "s": "ડ", "T": "𝕥", "t": "𝕥", "U": "ꪊ", "u": "ꪊ",
    "V": "᭙", "v": "᭙", "W": "᭙", "w": "᭙", "X": "᥊", "x": "᥊",
    "Y": "ꪗ", "y": "ꪗ", "Z": "᭄", "z": "᭄"
}
def custom_style_7(text):
    return apply_map(text, BUBBLE_CURSIVE_MAP)

SMALL_LOWER_MAP = {
    "A": "ą", "a": "ą", "B": "ც", "b": "ც", "C": "ƈ", "c": "ƈ",
    "D": "ɖ", "d": "ɖ", "E": "ɛ", "e": "ɛ", "F": "ʄ", "f": "ʄ",
    "G": "ɠ", "g": "ɠ", "H": "ɦ", "h": "ɦ", "I": "ɩ", "i": "ɩ",
    "J": "ʝ", "j": "ʝ", "K": "ƙ", "k": "ƙ", "L": "Ɩ", "l": "Ɩ",
    "M": "ɱ", "m": "ɱ", "N": "ɳ", "n": "ɳ", "O": "ɵ", "o": "ɵ",
    "P": "ƥ", "p": "ƥ", "Q": "զ", "q": "զ", "R": "ɼ", "r": "ɼ",
    "S": "ʂ", "s": "ʂ", "T": "ƭ", "t": "ƭ", "U": "ʉ", "u": "ʉ",
    "V": "ʋ", "v": "ʋ", "W": "ɯ", "w": "ɯ", "X": "ҳ", "x": "ҳ",
    "Y": "ყ", "y": "ყ", "Z": "ȥ", "z": "ȥ"
}
def custom_style_8(text):
    return apply_map(text, SMALL_LOWER_MAP)

ACCENT_LATIN_MAP = {
    "A": "Ä", "a": "ä", "B": "ß", "b": "ß", "C": "¢", "c": "¢",
    "D": "Ð", "d": "ð", "E": "Ê", "e": "ê", "F": "ℱ", "f": "ƒ",
    "G": "Ĝ", "g": "ĝ", "H": "Ĥ", "h": "ĥ", "I": "Î", "i": "î",
    "J": "Ĵ", "j": "ĵ", "K": "Ķ", "k": "ķ", "L": "Ł", "l": "ł",
    "M": "Ḿ", "m": "ḿ", "N": "Ñ", "n": "ñ", "O": "Ö", "o": "ö",
    "P": "Ƥ", "p": "ƥ", "Q": "ℚ", "q": "ℚ", "R": "Ŕ", "r": "ŕ",
    "S": "Š", "s": "š", "T": "Ť", "t": "ť", "U": "Ü", "u": "ü",
    "V": "Ṽ", "v": "ṽ", "W": "Ŵ", "w": "ŵ", "X": "Ẍ", "x": "ẍ",
    "Y": "Ý", "y": "ý", "Z": "Ž", "z": "ž"
}
def custom_style_9(text):
    return apply_map(text, ACCENT_LATIN_MAP)


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
    # گشت ستایلە کۆنەکان
    "Bold Serif": bold_serif,
    "Italic Serif": italic_serif,
    "Bold Italic": bold_italic,
    "Sans Bold": sans_bold,
    "Sans Italic": sans_italic,
    "Sans Bold Italic": sans_bold_italic,
    "Script": script,
    "Bold Script": bold_script,
    "Gothic": gothic,
    "Gothic Bold": bold_gothic,
    "Double Struck": double_struck,
    "Sans": sans,
    "Monospace": monospace,
    "Fullwidth": fullwidth,
    "Typewriter": typewriter,
    "Outline": double_struck,
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
    # 9 ستایلە نوێیەکەت
    "Strikethrough": custom_style_1,
    "Square Caps": custom_style_2,
    "Comic Alphanumeric": custom_style_3,
    "Glitch Text": custom_style_4,
    "Cyrillic Mix": custom_style_5,
    "Aesthetic Wide": custom_style_6,
    "Bubble Cursive": custom_style_7,
    "Small Lower": custom_style_8,
    "Accentuated Latin": custom_style_9,
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


def build_style_keyboard(selected_index: int = -1, page: int = 0):
    ITEMS_PER_PAGE = 15  # 5 ڕیز بە 3 دانەیی
    total_styles = len(STYLE_NAMES)
    total_pages = (total_styles + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    page = max(0, min(page, total_pages - 1))
    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_styles)

    buttons = []
    page_styles = STYLE_NAMES[start_idx:end_idx]

    for i in range(0, len(page_styles), 3):
        row = []
        for j in range(i, min(i + 3, len(page_styles))):
            style_name = page_styles[j]
            index = start_idx + j
            button_text = style_button_text(style_name)
            if index == selected_index:
                button_text = "✓ " + button_text
            row.append(InlineKeyboardButton(text=button_text, callback_data=f"style:{index}:{page}"))
        buttons.append(row)

    # دوگمەکانی گەڕان بەناو پەڕەکاندا
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ پاشوو", callback_data=f"page:{page - 1}:{selected_index}"))
    
    nav_row.append(InlineKeyboardButton(text=f"📄 {page + 1} / {total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="دواتر ➡️", callback_data=f"page:{page + 1}:{selected_index}"))
    
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
    keyboard = build_style_keyboard(selected_index=-1, page=0)
    safe_text = html.escape(user_text)
    await update.message.reply_text(
        text=safe_text, reply_markup=keyboard, parse_mode="HTML"
    )


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
    
    # گۆڕینی پەڕەکان
    if data.startswith("page:"):
        try:
            parts = data.split(":")
            target_page = int(parts[1])
            selected_index = int(parts[2])
        except (ValueError, IndexError):
            return
        
        await query.answer()
        keyboard = build_style_keyboard(selected_index=selected_index, page=target_page)
        try:
            await query.edit_message_reply_markup(reply_markup=keyboard)
        except Exception as error:
            if "Message is not modified" not in str(error):
                logger.error("Pagination markup edit failed: %s", error)
        return

    if data == "noop":
        await query.answer()
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
    keyboard = build_style_keyboard(selected_index=style_index, page=page)
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
    application.add_handler(CallbackQueryHandler(button_click, pattern=r"^(style:\d+:\d+|style:\d+|page:\d+:\d+|noop)$"))
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
