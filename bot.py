# =========================================================
# ENGLISH STYLE FONT BOT
# =========================================================
import logging
import html
import sqlite3
import os
import threading
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
# FLASK WEB SERVER (RENDER)
# =========================================================
app = Flask(__name__)


@app.route("/")
def home():
    return "English Style Font Bot is running!", 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


def run_web_server():
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


# =========================================================
# BOT TOKEN (READ FROM ENVIRONMENT VARIABLE)
# On Render: Environment -> add  BOT_TOKEN = your token
# =========================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# =========================================================
# FORCE JOIN CHANNEL
# =========================================================
CHANNEL_ID = "@technology_kurdishB"
CHANNEL_LINK = "https://t.me/technology_kurdishB"

# =========================================================
# USER TRACKING / ADMIN
# =========================================================
ADMIN_IDS = {8728499382}
USERS_DB = "users.db"

# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================================================
# STANDARD CHARACTERS
# =========================================================
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"
STD_A = UPPER + LOWER + DIGITS


# =========================================================
# HELPER: CREATE UNICODE MATHEMATICAL ALPHABET
# =========================================================
def make_math_map(
    upper_start=None,
    lower_start=None,
    digit_start=None,
    exceptions=None,
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
BOLD_SERIF_MAP = make_math_map(
    upper_start=0x1D400,
    lower_start=0x1D41A,
    digit_start=0x1D7CE,
)

ITALIC_SERIF_MAP = make_math_map(
    upper_start=0x1D434,
    lower_start=0x1D44E,
    exceptions={"h": "ℎ"},
)

BOLD_ITALIC_MAP = make_math_map(
    upper_start=0x1D468,
    lower_start=0x1D482,
)

SANS_MAP = make_math_map(
    upper_start=0x1D5A0,
    lower_start=0x1D5BA,
    digit_start=0x1D7E2,
)

SANS_BOLD_MAP = make_math_map(
    upper_start=0x1D5D4,
    lower_start=0x1D5EE,
    digit_start=0x1D7EC,
)

SANS_ITALIC_MAP = make_math_map(
    upper_start=0x1D608,
    lower_start=0x1D622,
)

SANS_BOLD_ITALIC_MAP = make_math_map(
    upper_start=0x1D63C,
    lower_start=0x1D656,
)

MONOSPACE_MAP = make_math_map(
    upper_start=0x1D670,
    lower_start=0x1D68A,
    digit_start=0x1D7F6,
)

DOUBLE_STRUCK_MAP = make_math_map(
    upper_start=0x1D538,
    lower_start=0x1D552,
    digit_start=0x1D7D8,
    exceptions={
        "C": "ℂ",
        "H": "ℍ",
        "N": "ℕ",
        "P": "ℙ",
        "Q": "ℚ",
        "R": "ℝ",
        "Z": "ℤ",
        "e": "ℯ",
        "i": "𝕚",
        "j": "𝕛",
    },
)

FRAKTUR_MAP = make_math_map(
    upper_start=0x1D504,
    lower_start=0x1D51E,
    exceptions={
        "C": "ℭ",
        "H": "ℌ",
        "I": "ℑ",
        "R": "ℜ",
        "Z": "ℨ",
    },
)

BOLD_FRAKTUR_MAP = make_math_map(
    upper_start=0x1D56C,
    lower_start=0x1D586,
)

SCRIPT_MAP = make_math_map(
    upper_start=0x1D49C,
    lower_start=0x1D4B6,
    exceptions={
        "B": "ℬ",
        "C": "ℭ",
        "E": "ℰ",
        "F": "ℱ",
        "H": "ℋ",
        "I": "ℐ",
        "L": "ℒ",
        "M": "ℳ",
        "R": "ℛ",
        "Z": "ℤ",
        "e": "ℯ",
        "g": "ℊ",
        "o": "ℴ",
    },
)

BOLD_SCRIPT_MAP = make_math_map(
    upper_start=0x1D4D0,
    lower_start=0x1D4EA,
)

FULLWIDTH_MAP = {}
for _i, _c in enumerate(UPPER):
    FULLWIDTH_MAP[_c] = chr(0xFF21 + _i)
for _i, _c in enumerate(LOWER):
    FULLWIDTH_MAP[_c] = chr(0xFF41 + _i)
for _i, _c in enumerate(DIGITS):
    FULLWIDTH_MAP[_c] = chr(0xFF10 + _i)


# =========================================================
# BASIC MAP CONVERTER
# =========================================================
def apply_map(text, mapping):
    return "".join(mapping.get(char, char) for char in text)


# =========================================================
# SMALL CAPS
# =========================================================
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
    return "".join(
        SMALL_CAPS_MAP.get(char.lower(), char) for char in text
    )


# =========================================================
# CIRCLED
# =========================================================
CIRCLED_UPPER = (
    "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿ"
    "ⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉ"
    "ⓊⓋⓌⓍⓎⓏ"
)
CIRCLED_LOWER = (
    "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙ"
    "ⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣ"
    "ⓤⓥⓦⓧⓨⓩ"
)
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


# =========================================================
# FILLED CIRCLED
# =========================================================
NEGATIVE_CIRCLED_UPPER = (
    "🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙"
    "🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣"
    "🅤🅥🅦🅧🅨🅩"
)


def filled_circled(text):
    result = []
    for char in text:
        if char.upper() in UPPER:
            result.append(NEGATIVE_CIRCLED_UPPER[UPPER.index(char.upper())])
        else:
            result.append(char)
    return "".join(result)


# =========================================================
# SQUARES
# =========================================================
SQUARED_UPPER = (
    "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹"
    "🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃"
    "🅄🅅🅆🅇🅈🅉"
)


def squares(text):
    result = []
    for char in text:
        if char.isalpha() and char.upper() in UPPER:
            result.append(SQUARED_UPPER[UPPER.index(char.upper())])
        else:
            result.append(char)
    return "".join(result)


# =========================================================
# FILLED SQUARES
# =========================================================
NEGATIVE_SQUARED_UPPER = (
    "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹"
    "🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃"
    "🆄🆅🆆🆇🆈🆉"
)


def filled_squares(text):
    result = []
    for char in text:
        if char.isalpha() and char.upper() in UPPER:
            result.append(NEGATIVE_SQUARED_UPPER[UPPER.index(char.upper())])
        else:
            result.append(char)
    return "".join(result)


# =========================================================
# PARENTHESIZED
# =========================================================
PARENTHESIZED_MAP = {
    "a": "⒜", "b": "⒝", "c": "⒞", "d": "⒟", "e": "⒠",
    "f": "⒡", "g": "⒢", "h": "⒣", "i": "⒤", "j": "⒥",
    "k": "⒦", "l": "⒧", "m": "⒨", "n": "⒩", "o": "⒪",
    "p": "⒫", "q": "⒬", "r": "⒭", "s": "⒮", "t": "⒯",
    "u": "⒰", "v": "⒱", "w": "⒲", "x": "⒳", "y": "⒴",
    "z": "⒵",
}


def parenthesized(text):
    return "".join(
        PARENTHESIZED_MAP.get(char.lower(), char) for char in text
    )


# =========================================================
# TINY
# =========================================================
TINY_MAP = {
    "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ",
    "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ",
    "k": "ᵏ", "l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ",
    "p": "ᵖ", "q": "q", "r": "ʳ", "s": "ˢ", "t": "ᵗ",
    "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ",
    "z": "ᶻ",
    "A": "ᴬ", "B": "ᴮ", "C": "ᶜ", "D": "ᴰ", "E": "ᴱ",
    "F": "ᶠ", "G": "ᴳ", "H": "ᴴ", "I": "ᴵ", "J": "ᴶ",
    "K": "ᴷ", "L": "ᴸ", "M": "ᴹ", "N": "ᴺ", "O": "ᴼ",
    "P": "ᴾ", "Q": "Q", "R": "ᴿ", "S": "ˢ", "T": "ᵀ",
    "U": "ᵁ", "V": "ⱽ", "W": "ᵂ", "X": "ˣ", "Y": "ʸ",
    "Z": "ᶻ",
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
}


def tiny(text):
    return apply_map(text, TINY_MAP)


# =========================================================
# COMIC
# =========================================================
COMIC_MAP = {
    "A": "Ⱥ", "a": "ɑ",
    "B": "Ɓ", "b": "ɓ",
    "C": "Ƈ", "c": "ƈ",
    "D": "Đ", "d": "ɗ",
    "E": "Ɛ", "e": "ɛ",
    "F": "Ƒ", "f": "ƒ",
    "G": "Ɠ", "g": "ɠ",
    "H": "Ħ", "h": "ɦ",
    "I": "Ɨ", "i": "ɨ",
    "J": "Ɉ", "j": "ʝ",
    "K": "Ƙ", "k": "ƙ",
    "L": "Ł", "l": "ł",
    "M": "Ɯ", "m": "ɱ",
    "N": "Ɲ", "n": "ɲ",
    "O": "Ø", "o": "ø",
    "P": "Ƥ", "p": "ƥ",
    "Q": "Ɋ", "q": "ɋ",
    "R": "Ʀ", "r": "ɍ",
    "S": "Ş", "s": "ʂ",
    "T": "Ŧ", "t": "ŧ",
    "U": "Ʉ", "u": "ʉ",
    "V": "Ʋ", "v": "ʋ",
    "W": "Ŵ", "w": "ŵ",
    "X": "Ӿ", "x": "ӿ",
    "Y": "Ƴ", "y": "ɏ",
    "Z": "Ƶ", "z": "ƶ",
}


def comic(text):
    return apply_map(text, COMIC_MAP)


# =========================================================
# QUNI
# =========================================================
QUNI_MAP = {
    "A": "Ⱥ", "a": "Ⱥ",
    "B": "Ɓ", "b": "ƀ",
    "C": "Ƈ", "c": "ƈ",
    "D": "Đ", "d": "đ",
    "E": "Ɇ", "e": "ɇ",
    "F": "Ƒ", "f": "ƒ",
    "G": "Ǥ", "g": "ǥ",
    "H": "Ħ", "h": "ħ",
    "I": "Ɨ", "i": "ɨ",
    "J": "Ɉ", "j": "ɉ",
    "K": "Ƙ", "k": "ƙ",
    "L": "Ł", "l": "ł",
    "M": "Ɱ", "m": "ɱ",
    "N": "Ŋ", "n": "ŋ",
    "O": "Ø", "o": "ø",
    "P": "Ƥ", "p": "ƥ",
    "Q": "Ɋ", "q": "ɋ",
    "R": "Ɍ", "r": "ɍ",
    "S": "Ş", "s": "ş",
    "T": "Ŧ", "t": "ŧ",
    "U": "Ʉ", "u": "ʉ",
    "V": "Ʋ", "v": "ʋ",
    "W": "Ŵ", "w": "ŵ",
    "X": "Ӿ", "x": "ӿ",
    "Y": "Ɏ", "y": "ɏ",
    "Z": "Ƶ", "z": "ƶ",
}


def quni(text):
    return apply_map(text, QUNI_MAP)


# =========================================================
# SPECIAL
# =========================================================
SPECIAL_MAP = {
    "A": "Λ", "B": "β", "C": "C", "D": "ᗪ", "E": "Σ",
    "F": "Ғ", "G": "Ɠ", "H": "卄", "I": "I", "J": "Ј",
    "K": "Ҡ", "L": "Ł", "M": "爪", "N": "И", "O": "Ө",
    "P": "尸", "Q": "Q", "R": "尺", "S": "Ѕ", "T": "Ŧ",
    "U": "Ц", "V": "Ѵ", "W": "Ш", "X": "Ж", "Y": "Ұ",
    "Z": "乙",
    "a": "α", "b": "в", "c": "¢", "d": "∂", "e": "є",
    "f": "ƒ", "g": "ɠ", "h": "н", "i": "ι", "j": "נ",
    "k": "к", "l": "ℓ", "m": "м", "n": "η", "o": "σ",
    "p": "ρ", "q": "զ", "r": "я", "s": "ѕ", "t": "т",
    "u": "υ", "v": "ν", "w": "ω", "x": "χ", "y": "у",
    "z": "z",
}


def special(text):
    return apply_map(text, SPECIAL_MAP)


# =========================================================
# UPSIDE DOWN
# =========================================================
UPSIDE_DOWN_MAP = {
    "a": "ɐ", "b": "q", "c": "ɔ", "d": "p", "e": "ǝ",
    "f": "ɟ", "g": "ƃ", "h": "ɥ", "i": "ᴉ", "j": "ɾ",
    "k": "ʞ", "l": "ʃ", "m": "ɯ", "n": "u", "o": "o",
    "p": "d", "q": "b", "r": "ɹ", "s": "s", "t": "ʇ",
    "u": "n", "v": "ʌ", "w": "ʍ", "x": "x", "y": "ʎ",
    "z": "z",
    "A": "∀", "B": "ᗺ", "C": "Ɔ", "D": "◖", "E": "Ǝ",
    "F": "Ⅎ", "G": "Ꭾ", "H": "H", "I": "I", "J": "Ⴑ",
    "K": "⋊", "L": "⅃", "M": "M", "N": "N", "O": "O",
    "P": "Ԁ", "Q": "Q", "R": "Я", "S": "S", "T": "⊥",
    "U": "∩", "V": "Λ", "W": "M", "X": "X", "Y": "⅄",
    "Z": "Z",
    "0": "0", "1": "Ɩ", "2": "ᄅ", "3": "Ɛ", "4": "ㄣ",
    "5": "ϛ", "6": "9", "7": "ㄥ", "8": "8", "9": "6",
}


def upside_down(text):
    return "".join(
        UPSIDE_DOWN_MAP.get(char, char) for char in reversed(text)
    )


# =========================================================
# REVERSE
# =========================================================
def reverse_text(text):
    return text[::-1]


# =========================================================
# MIRROR
# =========================================================
MIRROR_MAP = {
    "A": "A", "B": "ᗺ", "C": "Ɔ", "D": "◖", "E": "Ǝ",
    "F": "ꟻ", "G": "Ꭾ", "H": "H", "I": "I", "J": "Ⴑ",
    "K": "⋊", "L": "⅃", "M": "M", "N": "И", "O": "O",
    "P": "Ԁ", "Q": "Q", "R": "Я", "S": "S", "T": "⊥",
    "U": "∩", "V": "Λ", "W": "M", "X": "X", "Y": "⅄",
    "Z": "Z",
    "a": "ɒ", "b": "d", "c": "ↄ", "d": "b", "e": "ɘ",
    "f": "ʇ", "g": "ᵷ", "h": "ʜ", "i": "i", "j": "ɾ",
    "k": "ʞ", "l": "l", "m": "m", "n": "n", "o": "o",
    "p": "q", "q": "p", "r": "ɿ", "s": "s", "t": "t",
    "u": "u", "v": "v", "w": "w", "x": "x", "y": "y",
    "z": "z",
}


def mirror(text):
    return "".join(MIRROR_MAP.get(char, char) for char in text[::-1])


# =========================================================
# BASIC SCREENSHOT HELPERS
# =========================================================
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


# =========================================================
# CASE MAP
# =========================================================
def case_map(text, mapping, mode):
    if mode == "upper":
        text = text.upper()
    elif mode == "lower":
        text = text.lower()
    return apply_map(text, mapping)


def caps_of(mapping):
    return lambda text: case_map(text, mapping, "upper")


def lower_of(mapping):
    return lambda text: case_map(text, mapping, "lower")


def plain_of(mapping):
    return lambda text: apply_map(text, mapping)


# =========================================================
# ALTERNATING STYLES
# =========================================================
def alternating(text, map_a, map_b):
    result = []
    letter_index = 0
    for char in text:
        if char.isalpha():
            if letter_index % 2 == 0:
                result.append(map_a.get(char, char))
            else:
                result.append(map_b.get(char, char))
            letter_index += 1
        else:
            result.append(char)
    return "".join(result)


def alt_of(map_a, map_b):
    return lambda text: alternating(text, map_a, map_b)


# =========================================================
# TITLE STYLES
# =========================================================
def title_of(mapping):
    return lambda text: apply_map(text.title(), mapping)


# =========================================================
# STYLE REGISTRY
# =========================================================
STYLE_FUNCTIONS = {
    # MAIN STYLES
    "Bold Serif": plain_of(BOLD_SERIF_MAP),
    "Italic Serif": plain_of(ITALIC_SERIF_MAP),
    "Bold Italic": plain_of(BOLD_ITALIC_MAP),
    "Sans Bold": plain_of(SANS_BOLD_MAP),
    "Sans Italic": plain_of(SANS_ITALIC_MAP),
    "Sans Bold Italic": plain_of(SANS_BOLD_ITALIC_MAP),
    "Script": plain_of(SCRIPT_MAP),
    "Bold Script": plain_of(BOLD_SCRIPT_MAP),
    "Gothic": plain_of(FRAKTUR_MAP),
    "Gothic Bold": plain_of(BOLD_FRAKTUR_MAP),
    "Double Struck": plain_of(DOUBLE_STRUCK_MAP),
    "Sans": plain_of(SANS_MAP),
    "Monospace": plain_of(MONOSPACE_MAP),
    "Fullwidth": plain_of(FULLWIDTH_MAP),
    # SCREENSHOT STYLES
    "Typewriter": typewriter,
    "Outline": plain_of(DOUBLE_STRUCK_MAP),
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
    # CLEAN ADDITIONAL STYLES
    "Bold Serif Caps": caps_of(BOLD_SERIF_MAP),
    "Bold Serif Lower": lower_of(BOLD_SERIF_MAP),
    "Italic Serif Caps": caps_of(ITALIC_SERIF_MAP),
    "Italic Serif Lower": lower_of(ITALIC_SERIF_MAP),
    "Bold Italic Caps": caps_of(BOLD_ITALIC_MAP),
    "Bold Italic Lower": lower_of(BOLD_ITALIC_MAP),
    "Sans Caps": caps_of(SANS_MAP),
    "Sans Lower": lower_of(SANS_MAP),
    # Sans Bold Caps REMOVED
    "Sans Bold Lower": lower_of(SANS_BOLD_MAP),
    "Sans Italic Caps": caps_of(SANS_ITALIC_MAP),
    "Sans Italic Lower": lower_of(SANS_ITALIC_MAP),
    "Sans Bold Italic Caps": caps_of(SANS_BOLD_ITALIC_MAP),
    "Sans Bold Italic Lower": lower_of(SANS_BOLD_ITALIC_MAP),
    "Script Caps": caps_of(SCRIPT_MAP),
    "Script Lower": lower_of(SCRIPT_MAP),
    "Bold Script Caps": caps_of(BOLD_SCRIPT_MAP),
    "Bold Script Lower": lower_of(BOLD_SCRIPT_MAP),
    "Gothic Caps": caps_of(FRAKTUR_MAP),
    "Gothic Lower": lower_of(FRAKTUR_MAP),
    "Bold Gothic Caps": caps_of(BOLD_FRAKTUR_MAP),
    "Bold Gothic Lower": lower_of(BOLD_FRAKTUR_MAP),
    "Double Struck Caps": caps_of(DOUBLE_STRUCK_MAP),
    "Double Struck Lower": lower_of(DOUBLE_STRUCK_MAP),
    "Monospace Caps": caps_of(MONOSPACE_MAP),
    "Monospace Lower": lower_of(MONOSPACE_MAP),
    "Fullwidth Caps": caps_of(FULLWIDTH_MAP),
    "Fullwidth Lower": lower_of(FULLWIDTH_MAP),
    "Alternating Bold": alt_of(BOLD_SERIF_MAP, BOLD_ITALIC_MAP),
    "Alternating Sans": alt_of(SANS_MAP, SANS_BOLD_MAP),
    "Alternating Script": alt_of(SCRIPT_MAP, BOLD_SCRIPT_MAP),
    "Alternating Gothic": alt_of(FRAKTUR_MAP, BOLD_FRAKTUR_MAP),
    "Alternating Double": alt_of(DOUBLE_STRUCK_MAP, BOLD_SERIF_MAP),
    "Alternating Monospace": alt_of(MONOSPACE_MAP, SANS_MAP),
    "Alternating Fullwidth": alt_of(FULLWIDTH_MAP, BOLD_SERIF_MAP),
    "Alternating Italic": alt_of(ITALIC_SERIF_MAP, BOLD_ITALIC_MAP),
    "Bold Title": title_of(BOLD_SERIF_MAP),
    "Script Title": title_of(SCRIPT_MAP),
    "Gothic Title": title_of(FRAKTUR_MAP),
    "Sans Title": title_of(SANS_MAP),
    "Double Title": title_of(DOUBLE_STRUCK_MAP),
    "Mono Title": title_of(MONOSPACE_MAP),
}

STYLE_NAMES = list(STYLE_FUNCTIONS.keys())


# =========================================================
# CONVERT TEXT
# =========================================================
def convert_text(text: str, style_name: str) -> str:
    function = STYLE_FUNCTIONS.get(style_name)
    if function is None:
        return text
    try:
        return function(text)
    except Exception as error:
        logger.error("Style conversion error [%s]: %s", style_name, error)
        return text


# =========================================================
# BUTTON TEXT (style name rendered in its own style)
# =========================================================
def style_button_text(style_name: str) -> str:
    preview = convert_text(style_name, style_name)
    if len(preview) > 28:
        preview = preview[:28]
    return preview


# =========================================================
# BUILD KEYBOARD (3 BUTTONS PER ROW)
# =========================================================
def build_style_keyboard(selected_index: int = -1):
    buttons = []
    for i in range(0, len(STYLE_NAMES), 3):
        row = []
        for index in range(i, min(i + 3, len(STYLE_NAMES))):
            button_text = style_button_text(STYLE_NAMES[index])
            if index == selected_index:
                button_text = "✓ " + button_text
            row.append(
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"style:{index}",
                )
            )
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


# =========================================================
# USER TRACKING
# =========================================================
def init_users_db():
    conn = sqlite3.connect(USERS_DB)
    try:
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
    conn = sqlite3.connect(USERS_DB)
    try:
        existing = conn.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user.id,),
        ).fetchone()
        is_new = existing is None

        conn.execute("""
            INSERT INTO users (
                user_id, username, first_name, last_name, first_seen, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_seen = excluded.last_seen
        """, (
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            now,
            now,
        ))
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

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "👤 View Profile",
            url=f"tg://user?id={user.id}",
        )
    ]])

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except Exception as error:
            logger.error("Failed to notify admin %s: %s", admin_id, error)


def get_users():
    conn = sqlite3.connect(USERS_DB)
    try:
        return conn.execute("""
            SELECT user_id, username, first_name, last_name, first_seen, last_seen
            FROM users
            ORDER BY last_seen DESC
        """).fetchall()
    finally:
        conn.close()


def is_admin(user_id):
    return user_id in ADMIN_IDS


def get_user_by_id(user_id):
    conn = sqlite3.connect(USERS_DB)
    try:
        return conn.execute(
            """
            SELECT user_id, username, first_name, last_name, first_seen, last_seen
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    finally:
        conn.close()


def profile_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👤 View Profile",
                url=f"tg://user?id={user_id}",
            )
        ]
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
        f"🕐 یەکەم جار: {first_seen}\n"
        f"🕐 دوا جار: {last_seen}"
    )


async def user_command(update, context):
    if not update.effective_user or not is_admin(update.effective_user.id):
        if update.message:
            await update.message.reply_text("❌ ئەم فرمانە تەنها بۆ ئەدمینە.")
        return

    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "ℹ️ شێوازی بەکارهێنان:\n/user USER_ID\n\nنموونە: /user 123456789"
        )
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
    if not query:
        return

    if not query.from_user or not is_admin(query.from_user.id):
        await query.answer("❌ تەنها ئەدمین دەتوانێت ئەمە ببینێت.", show_alert=True)
        return

    try:
        user_id = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        await query.answer("❌ User ID نادروستە.", show_alert=True)
        return

    user = get_user_by_id(user_id)
    if not user:
        await query.answer("❌ بەکارهێنەر نەدۆزرایەوە.", show_alert=True)
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

    chunk_size = 25
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
                f"🆔 <code>{user_id}</code>\n"
                f"🕐 یەکەم: {first_seen} | دوا: {last_seen}"
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
        member = await bot.get_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id,
        )
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
        "🔒 بۆ بەکارهێنانی بۆتەکە، سەرەتا دەبێت جۆینی "
        "چەناڵەکەمان بکەیت.\n\n"
        "1️⃣ لەسەر «📢 جۆینی چەناڵ» دابگرە\n"
        "2️⃣ پاشان «✅ پشکنینی جۆین» دابگرە"
    )

    if update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=force_join_keyboard(),
        )

    return False


async def check_join(update, context):
    query = update.callback_query
    if not query:
        return

    if await is_subscribed(context.bot, query.from_user.id):
        await query.answer("✅ جۆینەکەت پشتڕاست کرایەوە.", show_alert=True)
        try:
            await query.edit_message_text(
                text=(
                    "✅ جۆینەکەت پشتڕاست کرایەوە.\n\n"
                    "ئێستا دەتوانیت دەقی ئینگلیزی بنێریت بۆ گۆڕینی ستایل."
                )
            )
        except Exception:
            pass
    else:
        await query.answer("❌ هێشتا جۆینی چەناڵەکەت نەکردووە.", show_alert=True)


# =========================================================
# START
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    is_new = track_user(update.effective_user)

    if is_new:
        await notify_admin_new_user(context.bot, update.effective_user)

    if not await require_subscription(update, context):
        return

    await update.message.reply_text(text="Send me an English text.")


# =========================================================
# HANDLE USER TEXT
# The bot message contains ONLY the user's original text.
# =========================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    track_user(update.effective_user)

    if not await require_subscription(update, context):
        return

    if not update.message.text:
        return
    user_text = update.message.text
    if not user_text.strip():
        return

    context.user_data["current_text"] = user_text
    context.user_data["selected_style"] = -1

    keyboard = build_style_keyboard(selected_index=-1)
    safe_text = html.escape(user_text)

    sent_message = await update.message.reply_text(
        text=safe_text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    context.user_data["style_message_id"] = sent_message.message_id


# =========================================================
# BUTTON CLICK
# =========================================================
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    track_user(query.from_user)

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
    if (
        current_message_id
        and query.message
        and query.message.message_id != current_message_id
    ):
        await query.answer(
            "This style menu is no longer active.",
            show_alert=True,
        )
        return

    user_text = context.user_data.get("current_text", "")
    if not user_text:
        try:
            await query.edit_message_text(text="Please send a new text.")
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
            text=safe_styled_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception as error:
        if "Message is not modified" not in str(error):
            logger.error("Message edit failed: %s", error)


# =========================================================
# ERROR HANDLER
# =========================================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception:", exc_info=context.error)


# =========================================================
# MAIN
# =========================================================
def main():
    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN environment variable is missing. "
            "Add it in Render -> Environment."
        )

    init_users_db()

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("user", user_command))
    application.add_handler(
        CallbackQueryHandler(user_profile_callback, pattern=r"^profile:\d+$")
    )
    application.add_handler(
        CallbackQueryHandler(check_join, pattern=r"^check_join$")
    )
    application.add_handler(
        CallbackQueryHandler(button_click, pattern=r"^style:\d+$")
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_error_handler(error_handler)

    logger.info("English Style Font Bot started.")
    logger.info("Total styles: %d", len(STYLE_NAMES))

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
