# =========================================================
# ENGLISH STYLE FONT BOT (RENDER OPTIMIZED & ENV CHANNEL)
# =========================================================
import logging
import html
import sqlite3
import os
import asyncio
import unicodedata
from collections import OrderedDict
from contextlib import contextmanager
from flask import Flask
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          CallbackQueryHandler, ContextTypes, filters)

app = Flask(__name__)

@app.get('/')
def home():
    return 'English Style Font Bot is running', 200

@app.get('/health')
def health():
    return 'OK', 200

BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
CHANNEL_ID = os.getenv('CHANNEL_ID', '@fontstylem').strip()
CHANNEL_LINK = os.getenv('CHANNEL_LINK', 'https://t.me/fontstylem').strip()
ADMIN_IDS = {int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip().isdigit()}
USERS_DB = os.getenv('USERS_DB', 'users.db')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
LOWER = 'abcdefghijklmnopqrstuvwxyz'
DIGITS = '0123456789'

def make_math_map(upper_start=None, lower_start=None, digit_start=None, exceptions=None):
    mapping = {}
    for alphabet, start in ((UPPER, upper_start), (LOWER, lower_start), (DIGITS, digit_start)):
        if start is not None:
            mapping.update({char: chr(start + i) for i, char in enumerate(alphabet)})
    if exceptions:
        mapping.update(exceptions)
    return mapping

# =========================================================
# UNICODE FONT MAPS
# =========================================================
BOLD_SERIF_MAP = make_math_map(0x1D400, 0x1D41A, 0x1D7CE)
ITALIC_SERIF_MAP = make_math_map(0x1D434, 0x1D44E, exceptions={'h': 'ℎ'})
BOLD_ITALIC_MAP = make_math_map(0x1D468, 0x1D482)
SANS_MAP = make_math_map(0x1D5A0, 0x1D5BA, 0x1D7E2)
SANS_BOLD_MAP = make_math_map(0x1D5D4, 0x1D5EE, 0x1D7EC)
SANS_ITALIC_MAP = make_math_map(0x1D608, 0x1D622)
SANS_BOLD_ITALIC_MAP = make_math_map(0x1D63C, 0x1D656)
MONOSPACE_MAP = make_math_map(0x1D670, 0x1D68A, 0x1D7F6)
DOUBLE_STRUCK_MAP = make_math_map(0x1D538, 0x1D552, 0x1D7D8, exceptions={
    'C': 'ℂ', 'H': 'ℍ', 'N': 'ℕ', 'P': 'ℙ', 'Q': 'ℚ', 'R': 'ℝ', 'Z': 'ℤ'})
FRAKTUR_MAP = make_math_map(0x1D504, 0x1D51E, exceptions={
    'C': 'ℭ', 'H': 'ℌ', 'I': 'ℑ', 'R': 'ℜ', 'Z': 'ℨ'})
BOLD_FRAKTUR_MAP = make_math_map(0x1D56C, 0x1D586)
SCRIPT_MAP = make_math_map(0x1D49C, 0x1D4B6, exceptions={
    'B': 'ℬ', 'E': 'ℰ', 'F': 'ℱ', 'H': 'ℋ', 'I': 'ℐ', 'L': 'ℒ',
    'M': 'ℳ', 'R': 'ℛ', 'e': 'ℯ', 'g': 'ℊ', 'o': 'ℴ', 'l': 'ℓ'})
BOLD_SCRIPT_MAP = make_math_map(0x1D4D0, 0x1D4EA)
FULLWIDTH_MAP = {**make_math_map(0xFF21, 0xFF41, 0xFF10)}

def apply_map(text, mapping):
    return ''.join(mapping.get(char, char) for char in text)

SMALL_CAPS_MAP = dict(zip(LOWER, 'ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'))

def small_caps(text):
    return ''.join(SMALL_CAPS_MAP.get(char, char) for char in text)

CIRCLED_UPPER = 'ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ'
CIRCLED_LOWER = 'ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ'
CIRCLED_DIGITS = '⓪①②③④⑤⑥⑦⑧⑨'
CIRCLED_MAP = dict(zip(UPPER + LOWER + DIGITS, CIRCLED_UPPER + CIRCLED_LOWER + CIRCLED_DIGITS))

def circled(text):
    return apply_map(text, CIRCLED_MAP)

NEGATIVE_CIRCLED_UPPER = '🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩'
SQUARED_UPPER = '🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉'
NEGATIVE_SQUARED_UPPER = '🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉'

def upper_symbols(text, symbols):
    return ''.join(symbols[UPPER.index(c.upper())] if c.upper() in UPPER else c for c in text)

def filled_circled(text): return upper_symbols(text, NEGATIVE_CIRCLED_UPPER)
def squares(text): return upper_symbols(text, SQUARED_UPPER)
def filled_squares(text): return upper_symbols(text, NEGATIVE_SQUARED_UPPER)

PARENTHESIZED_MAP = dict(zip(LOWER, '⒜⒝⒞⒟⒠⒡⒢⒣⒤⒥⒦⒧⒨⒩⒪⒫⒬⒭⒮⒯⒰⒱⒲⒳⒴⒵'))

def parenthesized(text):
    return ''.join(PARENTHESIZED_MAP.get(char, char) for char in text)

TINY_MAP = dict(zip(LOWER, ['ᵃ','ᵇ','ᶜ','ᵈ','ᵉ','ᶠ','ᵍ','ʰ','ⁱ','ʲ','ᵏ','ˡ','ᵐ','ⁿ','ᵒ','ᵖ','q','ʳ','ˢ','ᵗ','ᵘ','ᵛ','ʷ','ˣ','ʸ','ᶻ']))
TINY_MAP.update(dict(zip(UPPER, ['ᴬ','ᴮ','ᶜ','ᴰ','ᴱ','ᶠ','ᴳ','ᴴ','ᴵ','ᴶ','ᴷ','ᴸ','ᴹ','ᴺ','ᴼ','ᴾ','Q','ᴿ','ˢ','ᵀ','ᵁ','ⱽ','ᵂ','ˣ','ʸ','ᶻ'])))
TINY_MAP.update(dict(zip(DIGITS, '⁰¹²³⁴⁵⁶⁷⁸⁹')))

def tiny(text): return apply_map(text, TINY_MAP)

COMIC_MAP = dict(zip(UPPER + LOWER,
    ['Ⱥ','Ɓ','Ƈ','Đ','Ɛ','Ƒ','Ɠ','Ħ','Ɨ','Ɉ','Ƙ','Ł','Ɯ','Ɲ','Ø','Ƥ','Ɋ','Ʀ','Ş','Ŧ','Ʉ','Ʋ','Ŵ','Ӿ','Ƴ','Ƶ'] +
    ['ɑ','ɓ','ƈ','ɗ','ɛ','ƒ','ɠ','ɦ','ɨ','ʝ','ƙ','ł','ɱ','ɲ','ø','ƥ','ɋ','ɍ','ʂ','ŧ','ʉ','ʋ','ŵ','ӿ','ɏ','ƶ']))
QUNI_MAP = dict(zip(UPPER + LOWER,
    ['Ⱥ','Ɓ','Ƈ','Đ','Ɇ','Ƒ','Ǥ','Ħ','Ɨ','Ɉ','Ƙ','Ł','M','Ŋ','Ø','Ƥ','Ɋ','Ɍ','Ş','Ŧ','Ʉ','Ʋ','Ŵ','Ӿ','Ɏ','Ƶ'] +
    ['Ⱥ','ƀ','ƈ','đ','ɇ','ƒ','ǥ','ħ','ɨ','ɉ','ƙ','ł','ɱ','ŋ','ø','ƥ','ɋ','ɍ','ş','ŧ','ʉ','ʋ','ŵ','ӿ','ɏ','ƶ']))
SPECIAL_MAP = dict(zip(UPPER + LOWER,
    ['Λ','β','C','ᗪ','Σ','Ғ','Ɠ','卄','I','Ј','Ҡ','Ł','爪','И','Ө','尸','Q','尺','Ѕ','Ŧ','Ц','Ѵ','Ш','Ж','Ұ','乙'] +
    ['α','в','¢','∂','є','ƒ','ɠ','н','ι','נ','к','ℓ','м','η','σ','ρ','զ','я','ѕ','т','υ','ν','ω','χ','у','z']))

def comic(text): return apply_map(text, COMIC_MAP)
def quni(text): return apply_map(text, QUNI_MAP)
def special(text): return apply_map(text, SPECIAL_MAP)

UPSIDE_DOWN_MAP = dict(zip(LOWER + UPPER + DIGITS,
    ['ɐ','q','ɔ','p','ǝ','ɟ','ƃ','ɥ','ᴉ','ɾ','ʞ','ʃ','ɯ','u','o','d','b','ɹ','s','ʇ','n','ʌ','ʍ','x','ʎ','z'] +
    ['∀','ᗺ','Ɔ','◖','Ǝ','Ⅎ','Ꭾ','H','I','Ⴑ','⋊','⅃','M','N','O','Ԁ','Q','Я','S','⊥','∩','Λ','M','X','⅄','Z'] +
    ['0','Ɩ','ᄅ','Ɛ','ㄣ','ϛ','9','ㄥ','8','6']))
MIRROR_MAP = dict(zip(UPPER + LOWER,
    ['A','ᗺ','Ɔ','◖','Ǝ','Ⅎ','Ꭾ','H','I','Ⴑ','⋊','⅃','M','И','O','Ԁ','Q','Я','S','⊥','∩','Λ','M','X','⅄','Z'] +
    ['ɒ','d','ↄ','b','ɘ','ɟ','ᵷ','ʜ','i','ɾ','ʞ','l','m','n','o','q','p','ɿ','s','t','u','v','w','x','y','z']))

def upside_down(text): return apply_map(text[::-1], UPSIDE_DOWN_MAP)
def reverse_text(text): return text[::-1]
def mirror(text): return apply_map(text[::-1], MIRROR_MAP)
def serif(text): return text

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
# ADDITIONAL CUSTOM STYLES ADDED HERE
# =========================================================
MAP_STYLE_1 = dict(zip(UPPER, ['ɑ','ϐ','ᝯ','ժ','ꫀ','⨍','ᧁ','h','ꪱ','յ','ƙ','ᥣ','ꩇ','ꪀ','ᨵ','℘','q','ꭈ','꯱','t','υ','᥎','ᨰ','᥊','ᨮ','z']))
MAP_STYLE_2 = dict(zip(UPPER, ['卂','乃','匚','ᗪ','乇','千','Ꮆ','卄','丨','ﾌ','Ҝ','ㄥ','爪','几','ㄖ','卩','Ɋ','尺','丂','ㄒ','ㄩ','ᐯ','山','乂','ㄚ','乙']))
MAP_STYLE_3 = dict(zip(UPPER, ['ﾑ','乃','ᄃ','り','乇','ｷ','G','ん','ﾉ','ﾌ','ズ','ﾚ','ﾶ','刀','の','ｱ','ゐ','尺','丂','ｲ','ひ','√','W','ﾒ','ﾘ','乙']))
MAP_STYLE_4 = dict(zip(UPPER, ['ꪖ','᥇','ꪰ','ᦔ','ꫀ','ᠻ','ᧁ','ꫝ','꠸','꠹','ᛕ','ꪶ','ꪑ','ꪀ','ꪮ','ρ','ꪇ','᥅','ᦓ','ꪻ','ꪊ','ꪜ','᭙','᥊','ꪗ','ƺ']))
for mapping in (MAP_STYLE_1, MAP_STYLE_2, MAP_STYLE_3, MAP_STYLE_4):
    mapping.update({lower: mapping[upper] for upper, lower in zip(UPPER, LOWER)})
MAP_STYLE_3['g'] = 'g'
MAP_STYLE_4.update(dict(zip('123456789', ['᧒','ᒿ','ᗱ','ᔰ','Ƽ','ᦆ','ᒣ','Ზ','ၦ'])))

def custom_style_extra_1(text): return apply_map(text, MAP_STYLE_1)
def custom_style_extra_2(text): return apply_map(text, MAP_STYLE_2)
def custom_style_extra_3(text): return apply_map(text, MAP_STYLE_3)
def custom_style_extra_4(text): return apply_map(text, MAP_STYLE_4)
def glitch_all_style(text): return ''.join(char + '\u0489' for char in text)

def alternating(text, map_a, map_b):
    result, letter_index = [], 0
    for char in text:
        if char.isalpha():
            result.append((map_a if letter_index % 2 == 0 else map_b).get(char, char))
            letter_index += 1
        else:
            result.append(char)
    return ''.join(result)

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

STYLE_FUNCTIONS = OrderedDict([
    ('Bold Serif', bold_serif), ('Italic Serif', italic_serif),
    ('Bold Italic', bold_italic), ('Sans Bold', sans_bold),
    ('Sans Italic', sans_italic), ('Sans Bold Italic', sans_bold_italic),
    ('Script', script), ('Bold Script', bold_script),
    ('Gothic', gothic), ('Gothic Bold', bold_gothic),
    ('Double Struck', double_struck), ('Sans', sans),
    ('Monospace', monospace), ('Fullwidth', fullwidth),
    ('Serif', serif), ('Small Caps', small_caps), ('Tiny', tiny),
    ('Comic', comic), ('Circled', circled), ('Filled Circled', filled_circled),
    ('Squares', squares), ('Filled Squares', filled_squares),
    ('Upside Down', upside_down), ('Mirror', mirror), ('Reverse', reverse_text),
    ('QUNI', quni), ('Special', special), ('Parenthesized', parenthesized),
    ('Alternating Bold', alternating_bold), ('Alternating Sans', alternating_sans),
    ('Alternating Script', alternating_script), ('Alternating Gothic', alternating_gothic),
    ('Alternating Double', alternating_double), ('Alternating Monospace', alternating_mono),
    ('Alternating Fullwidth', alternating_fullwidth), ('Alternating Italic', alternating_italic),
    ('Bold Title', bold_title), ('Script Title', script_title),
    ('Gothic Title', gothic_title), ('Sans Title', sans_title),
    ('Double Title', double_title), ('Mono Title', mono_title),
    ('Decorated Cursive', custom_style_extra_1), ('Wide Outline', custom_style_extra_2),
    ('Cyrillic Mix Pro', custom_style_extra_3), ('Advanced Bubble', custom_style_extra_4),
    ('Glitch All', glitch_all_style),
])
STYLE_NAMES = list(STYLE_FUNCTIONS)

def convert_text(text: str, style_name: str) -> str:
    function = STYLE_FUNCTIONS.get(style_name)
    if function is None:
        return text
    try:
        return function(text)
    except Exception:
        logger.exception('Style conversion error [%s]', style_name)
        return text

def style_button_text(style_name: str) -> str:
    preview = convert_text(style_name, style_name)
    # Avoid splitting a base character from combining marks.
    if len(preview) > 28:
        cutoff = 28
        while cutoff < len(preview) and unicodedata.combining(preview[cutoff]):
            cutoff += 1
        preview = preview[:cutoff]
    return preview

def build_style_keyboard(selected_index: int = -1, page: int = 0):
    ITEMS_PER_PAGE = 15
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
                button_text = '✓ ' + button_text
            row.append(InlineKeyboardButton(text=button_text, callback_data=f'style:{index}:{page}'))
        buttons.append(row)
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text='⬅️ پاشوو', callback_data=f'page:{page - 1}:{selected_index}'))
    nav_row.append(InlineKeyboardButton(text=f'📄 {page + 1} / {total_pages}', callback_data='noop'))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text='دواتر ➡️', callback_data=f'page:{page + 1}:{selected_index}'))
    buttons.append(nav_row)
    return InlineKeyboardMarkup(buttons)

# =========================================================
# DATABASE OPERATIONS
# =========================================================
@contextmanager
def db_connect():
    conn = sqlite3.connect(USERS_DB, timeout=30)
    try:
        conn.execute('PRAGMA busy_timeout = 30000')
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_users_db():
    with db_connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            last_name TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL)''')

def track_user(user):
    if not user:
        return False
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_connect() as conn:
        existing = conn.execute('SELECT user_id FROM users WHERE user_id = ?', (user.id,)).fetchone()
        conn.execute('''INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username, first_name=excluded.first_name,
                last_name=excluded.last_name, last_seen=excluded.last_seen''',
            (user.id, user.username, user.first_name, user.last_name, now, now))
        return existing is None

async def notify_admin_new_user(bot, user):
    if not user:
        return
    username = f'@{user.username}' if user.username else 'بێ Username'
    name = user.full_name or 'بێ ناو'
    text = ('🆕 <b>بەکارهێنەری نوێ!</b>\n\n'
            f'👤 ناو: {html.escape(name)}\n'
            f'📛 Username: {html.escape(username)}\n'
            f'🆔 User ID: <code>{user.id}</code>')
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('👤 View Profile', url=f'tg://user?id={user.id}')]])
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=text, parse_mode='HTML', reply_markup=keyboard)
        except Exception as error:
            logger.error('Failed to notify admin %s: %s', admin_id, error)

def get_users():
    with db_connect() as conn:
        return conn.execute('SELECT user_id, username, first_name, last_name, first_seen, last_seen FROM users ORDER BY last_seen DESC').fetchall()

def is_admin(user_id): return user_id in ADMIN_IDS

def get_user_by_id(user_id):
    with db_connect() as conn:
        return conn.execute('SELECT user_id, username, first_name, last_name, first_seen, last_seen FROM users WHERE user_id = ?', (user_id,)).fetchone()

def profile_keyboard(user_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('👤 View Profile', url=f'tg://user?id={user_id}')]])

def format_user_profile(user):
    user_id, username, first_name, last_name, first_seen, last_seen = user
    name = ' '.join(x for x in (first_name, last_name) if x) or 'بێ ناو'
    uname = f'@{username}' if username else 'بێ username'
    return ('👤 زانیاری بەکارهێنەر\n\n'
            f'📛 ناو: {html.escape(name)}\n'
            f'🔗 Username: {html.escape(uname)}\n'
            f'🆔 User ID: <code>{user_id}</code>\n'
            f'🕐 یەکەم جار: {html.escape(first_seen)}\n'
            f'🕐 دوا جار: {html.escape(last_seen)}')

async def user_command(update, context):
    if not update.effective_user or not is_admin(update.effective_user.id):
        if update.message:
            await update.message.reply_text('❌ ئەم فرمانە تەنها بۆ ئەدمینە.')
        return
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text('ℹ️ شێوازی بەکارهێنان:\n/user USER_ID')
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text('❌ User ID دەبێت ژمارە بێت.')
        return
    user = get_user_by_id(user_id)
    if not user:
        await update.message.reply_text('❌ ئەم User ID ـیە لە دیتابەیسەکەدا نییە.')
        return
    await update.message.reply_text(format_user_profile(user), parse_mode='HTML', reply_markup=profile_keyboard(user_id))

async def user_profile_callback(update, context):
    query = update.callback_query
    if not query:
        return
    if not query.from_user or not is_admin(query.from_user.id):
        await query.answer('❌ تەنها ئەدمین دەتوانێت ئەمە ببینێت.', show_alert=True)
        return
    try:
        user_id = int((query.data or '').split(':', 1)[1])
    except (ValueError, IndexError):
        await query.answer()
        return
    user = get_user_by_id(user_id)
    await query.answer()
    if not user or not query.message:
        return
    await query.message.reply_text(format_user_profile(user), parse_mode='HTML', reply_markup=profile_keyboard(user_id))

async def users_command(update, context):
    if not update.effective_user or not is_admin(update.effective_user.id):
        if update.message:
            await update.message.reply_text('❌ ئەم فرمانە تەنها بۆ ئەدمینە.')
        return
    if not update.message:
        return
    users = get_users()
    if not users:
        await update.message.reply_text('📭 هیچ بەکارهێنەرێک تۆمار نەکراوە.')
        return
    for start_index in range(0, len(users), 10):
        chunk = users[start_index:start_index + 10]
        lines = [f'👥 کۆی گشتی بەکارهێنەران: {len(users)}',
                 f'📄 بەکارهێنەرەکان {start_index + 1} - {start_index + len(chunk)}', '']
        keyboard = []
        for i, (user_id, username, first_name, last_name, first_seen, last_seen) in enumerate(chunk, start_index + 1):
            name = ' '.join(x for x in (first_name, last_name) if x) or 'بێ ناو'
            uname = f'@{username}' if username else 'بێ username'
            lines.append(f'{i}. {html.escape(name)} | {html.escape(uname)}\n'
                         f'🆔 <code>{user_id}</code>\n🕐 یەکەم: {first_seen} | دوا: {last_seen}')
            keyboard.append([InlineKeyboardButton(f'👤 View Profile — {name[:35]}', callback_data=f'profile:{user_id}')])
        await update.message.reply_text('\n\n'.join(lines), parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

# =========================================================
# FORCE JOIN HELPERS
# =========================================================
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return (member.status in ('member', 'administrator', 'creator') or
                (member.status == 'restricted' and getattr(member, 'is_member', False)))
    except Exception as error:
        logger.error('Subscription check failed: %s', error)
        return False

def force_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📢 جۆینی چەناڵ', url=CHANNEL_LINK)],
        [InlineKeyboardButton('✅ پشکنینی جۆین', callback_data='check_join')]])

async def require_subscription(update, context):
    user = update.effective_user
    if not user:
        return False
    if await is_subscribed(context.bot, user.id):
        return True
    text = ('🔒 بۆ بەکارهێنانی بۆتەکە، سەرەتا دەبێت جۆینی چەناڵەکەمان بکەیت.\n\n'
            '1️⃣ لەسەر «📢 جۆینی چەناڵ» دابگرە\n'
            '2️⃣ پاشان «✅ پشکنینی جۆین» دابگرە')
    if update.message:
        await update.message.reply_text(text=text, reply_markup=force_join_keyboard())
    return False

async def check_join(update, context):
    query = update.callback_query
    if not query:
        return
    if await is_subscribed(context.bot, query.from_user.id):
        await query.answer('✅ جۆینەکەت پشتڕاست کرایەوە.', show_alert=True)
        try:
            await query.edit_message_text('✅ جۆینەکەت پشتڕاست کرایەوە.\n\nئێستا دەقێکی ئینگلیزی بنێرە بۆ گۆڕینی ستایل.')
        except BadRequest as error:
            if 'not modified' not in str(error).lower():
                logger.error('Join message edit failed: %s', error)
    else:
        await query.answer('❌ هێشتا جۆینی چەناڵەکەت نەکردووە.', show_alert=True)

# =========================================================
# BOT HANDLERS
# =========================================================
async def register_user(update, context):
    is_new = track_user(update.effective_user)
    if is_new:
        await notify_admin_new_user(context.bot, update.effective_user)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await register_user(update, context)
    if not await require_subscription(update, context):
        return
    await update.message.reply_text('ئێستا دەقێکی ئینگلیزی بنێرە بۆ گۆڕینی ستایل.')

# Each message has its own text, so older keyboards still work.
# In-memory state has the same persistence behavior as the original user_data.
def get_message_text(context, message_id):
    texts = context.user_data.get('message_texts', {})
    return texts.get(message_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await register_user(update, context)
    if not await require_subscription(update, context):
        return
    user_text = update.message.text
    if not user_text or not user_text.strip():
        return
    if len(user_text) > 4000:
        await update.message.reply_text('⚠️ تکایە دەقەکەت کورتتر بکەوە؛ زۆرترین قەبارەی پشتیوانیکراو ٤٠٠٠ پیتە.')
        return
    keyboard = build_style_keyboard(selected_index=-1, page=0)
    sent = await update.message.reply_text(text=html.escape(user_text), reply_markup=keyboard, parse_mode='HTML')
    context.user_data.setdefault('message_texts', {})[sent.message_id] = user_text
    context.user_data['current_text'] = user_text
    context.user_data['selected_style'] = -1

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await register_user(update, context)
    if not await is_subscribed(context.bot, query.from_user.id):
        await query.answer('❌ بۆ بەکارهێنانی بۆتەکە دەبێت سەرەتا جۆینی چەناڵ بکەیت.', show_alert=True)
        if query.message:
            try:
                await query.message.reply_text('🔒 سەرەتا جۆینی چەناڵەکە بکە، پاشان بگەڕێوە بۆ بۆتەکە.', reply_markup=force_join_keyboard())
            except Exception as error:
                logger.error('Force join prompt failed: %s', error)
        return
    data = query.data or ''
    if data.startswith('page:'):
        try:
            _, target_page, selected_index = data.split(':')
            target_page, selected_index = int(target_page), int(selected_index)
        except (ValueError, IndexError):
            await query.answer()
            return
        await query.answer()
        keyboard = build_style_keyboard(selected_index=selected_index, page=target_page)
        try:
            await query.edit_message_reply_markup(reply_markup=keyboard)
        except BadRequest as error:
            if 'not modified' not in str(error).lower():
                logger.error('Pagination markup edit failed: %s', error)
        return
    if data == 'noop':
        await query.answer()
        return
    if not data.startswith('style:'):
        await query.answer()
        return
    try:
        parts = data.split(':')
        style_index = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        await query.answer()
        return
    if not 0 <= style_index < len(STYLE_NAMES):
        await query.answer()
        return
    message_id = query.message.message_id if query.message else None
    user_text = get_message_text(context, message_id)
    if user_text is None:
        await query.answer()
        try:
            await query.edit_message_text('تکایە دەقێکی نوێ بنێرە.')
        except BadRequest as error:
            if 'not modified' not in str(error).lower():
                logger.error('Missing text message edit failed: %s', error)
        return
    await query.answer()
    style_name = STYLE_NAMES[style_index]
    styled_text = convert_text(user_text, style_name)
    if len(styled_text.encode('utf-16-le')) // 2 > 4096:
        # Telegram's text limit is checked after entity parsing.
        await query.message.reply_text('⚠️ تکایە دەقەکەت کورتتر بکەوە؛ زۆرترین قەبارەی پشتیوانیکراو ٤٠٠٠ پیتە.')
        return
    context.user_data['selected_style'] = style_index
    keyboard = build_style_keyboard(selected_index=style_index, page=page)
    try:
        await query.edit_message_text(text=html.escape(styled_text), reply_markup=keyboard, parse_mode='HTML')
    except BadRequest as error:
        if 'not modified' not in str(error).lower():
            logger.error('Message edit failed: %s', error)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error('Unhandled exception:', exc_info=context.error)

# =========================================================
# MAIN ASYNC ENGINE (FULLY NON-BLOCKING FOR RENDER)
# =========================================================
async def main():
    if not BOT_TOKEN:
        raise ValueError('Missing BOT_TOKEN environment variable in Render > Environment')
    init_users_db()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('users', users_command))
    application.add_handler(CommandHandler('user', user_command))
    application.add_handler(CallbackQueryHandler(user_profile_callback, pattern=r'^profile:\d+$'))
    application.add_handler(CallbackQueryHandler(check_join, pattern=r'^check_join$'))
    application.add_handler(CallbackQueryHandler(button_click, pattern=r'^(style:\d+:\d+|style:\d+|page:\d+:\d+|noop)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    port = int(os.environ.get('PORT', 10000))
    from werkzeug.serving import run_simple
    loop = asyncio.get_running_loop()
    server_future = loop.run_in_executor(None, lambda: run_simple('0.0.0.0', port, app, use_reloader=False, threaded=True))
    logger.info('Flask server starting on port %d', port)
    logger.info('Bot starting Telegram Polling...')
    async with application:
        await application.start()
        try:
            await application.updater.start_polling(drop_pending_updates=True)
            await asyncio.Event().wait()
        finally:
            if application.updater.running:
                await application.updater.stop()
            if application.running:
                await application.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
