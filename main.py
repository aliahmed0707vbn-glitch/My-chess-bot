import telebot
import requests
import json
import os
from telebot import types

# ==========================================
TOKEN = "8628055657:AAH8@3HemoEmeCUPg8eqV-m_MyWWs6umxlnE"
DB_FILE = "users_database.json"
LI_DB_FILE = "lichess_database.json"
# ==========================================

bot = telebot.TeleBot(TOKEN)

# --- دوال البيانات ---
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_json(filename, data):
    with open(filename, "w") as f: json.dump(data, f)

def get_chess_com_stats(username):
    url = f"https://api.chess.com/pub/player/{username.lower().strip()}/stats"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

def get_lichess_stats(username):
    url = f"https://lichess.org/api/user/{username.lower().strip()}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            p = r.json().get('perfs', {})
            return {
                'rapid': p.get('rapid', {}).get('rating', 0),
                'blitz': p.get('blitz', {}).get('rating', 0),
                'bullet': p.get('bullet', {}).get('rating', 0)
            }
        return None
    except: return None

# --- نظام المتصدرين ---
def get_lb_data(site, mode):
    db = load_json(LI_DB_FILE if site == 'li' else DB_FILE)
    lb = []
    keys = {'rapid': 'chess_rapid', 'blitz': 'chess_blitz', 'bullet': 'chess_bullet'}
    
    for uid, name in db.items():
        st = get_lichess_stats(name) if site == 'li' else get_chess_com_stats(name)
        if st:
            if site == 'li': val = st.get(mode, 0)
            else: val = st.get(keys[mode], {}).get('last', {}).get('rating', 0)
            lb.append({'name': name, 'rating': val})
    
    lb.sort(key=lambda x: x['rating'], reverse=True)
    return lb

def format_lb(lb, title, page=0):
    if not lb: return "⚠️ لا توجد بيانات حالياً."
    start, end = page * 10, (page + 1) * 10
    msg = f"🌟 <b>متصدري {title}:</b>\n━━━━━━━━━━━━━━\n"
    for i, p in enumerate(lb[start:end]):
        r = start + i + 1
        icon, crown = {1:("🥇"," 👑"), 2:("🥈"," 🎖️"), 3:("🥉"," 🏅")}.get(r, (f"<b>{r} -</b>", ""))
        msg += f"{icon} {p['name']}: <code>{p['rating']}</code>{crown}\n"
    return msg + "\n━━━━━━━━━━━━━━"

# --- الأوامر الأساسية ---

@bot.message_handler(commands=['start'])
def start_cmd(m):
    bot.reply_to(m, "👋 أهلاً بك! استخدم /help لرؤية الأوامر.")

@bot.message_handler(commands=['me'])
def profile_command(m):
    uid = str(m.from_user.id)
    db_com = load_json(DB_FILE)
    db_li = load_json(LI_DB_FILE)
    user_com = db_com.get(uid)
    user_li = db_li.get(uid)
    if not user_com and not user_li:
        bot.reply_to(m, "⚠️ أنت غير مرتبط بأي حساب.")
        return
    res = f"👤 <b>ملفك الشطرنجي:</b>\n━━━━━━━━━━━━━━\n"
    if user_com:
        st = get_chess_com_stats(user_com)
        if st:
            def g(k): return st.get(k, {}).get('last', {}).get('rating', 0)
            res += f"🟢 <b>Chess.com:</b> <code>{user_com}</code>\n└ R: {g('chess_rapid')} | B: {g('chess_blitz')} | Bu: {g('chess_bullet')}\n\n"
    if user_li:
        st = get_lichess_stats(user_li)
        if st:
            res += f"🔵 <b>Lichess:</b> <code>{user_li}</code>\n└ R: {st['rapid']} | B: {st['blitz']} | Bu: {st['bullet']}\n"
    bot.reply_to(m, res + "━━━━━━━━━━━━━━", parse_mode='HTML')

# --- الأوامر المحدثة للرد على الرسائل (Reply) ---

@bot.message_handler(commands=['elo'])
def elo_chess(m):
    db = load_json(DB_FILE)
    # إذا كانت الرسالة رداً على شخص، نأخذ الـ ID الخاص بصاحب الرسالة الأصلية، وإلا نأخذ الـ ID الخاص بالمرسل
    target_user = m.reply_to_message.from_user if m.reply_to_message else m.from_user
    uid = str(target_user.id)
    
    user = db.get(uid)
    if not user:
        bot.reply_to(m, f"⚠️ {target_user.first_name} غير مسجل في Chess.com.")
        return
        
    st = get_chess_com_stats(user)
    if st:
        def g(k): return st.get(k, {}).get('last', {}).get('rating', 0)
        msg = (f"👤 <b>{user} (Chess.com):</b>\n━━━━━━━━━━━━━━\n"
               f"🕒 Rapid: <code>{g('chess_rapid')}</code>\n"
               f"⚡ Blitz: <code>{g('chess_blitz')}</code>\n"
               f"🔫 Bullet: <code>{g('chess_bullet')}</code>")
        bot.reply_to(m, msg, parse_mode='HTML')

@bot.message_handler(commands=['elol'])
def elo_li(m):
    db = load_json(LI_DB_FILE)
    target_user = m.reply_to_message.from_user if m.reply_to_message else m.from_user
    uid = str(target_user.id)
    
    user = db.get(uid)
    if not user:
        bot.reply_to(m, f"⚠️ {target_user.first_name} غير مسجل في Lichess.")
        return
        
    st = get_lichess_stats(user)
    if st:
        msg = (f"👤 <b>{user} (Lichess):</b>\n━━━━━━━━━━━━━━\n"
               f"🕒 Rapid: <code>{st['rapid']}</code>\n"
               f"⚡ Blitz: <code>{st['blitz']}</code>\n"
               f"🔫 Bullet: <code>{st['bullet']}</code>")
        bot.reply_to(m, msg, parse_mode='HTML')

@bot.message_handler(commands=['user'])
def user_chess(m):
    db = load_json(DB_FILE)
    target_user = m.reply_to_message.from_user if m.reply_to_message else m.from_user
    uid = str(target_user.id)
    user = db.get(uid)
    if user:
        bot.reply_to(m, f"👤 يوزر Chess.com لـ {target_user.first_name}: <code>{user}</code>", parse_mode='HTML')
    else:
        bot.reply_to(m, "⚠️ غير مسجل في Chess.com.")

@bot.message_handler(commands=['userl'])
def user_lichess(m):
    db = load_json(LI_DB_FILE)
    target_user = m.reply_to_message.from_user if m.reply_to_message else m.from_user
    uid = str(target_user.id)
    user = db.get(uid)
    if user:
        bot.reply_to(m, f"👤 يوزر Lichess لـ {target_user.first_name}: <code>{user}</code>", parse_mode='HTML')
    else:
        bot.reply_to(m, "⚠️ غير مسجل في Lichess.")

# --- أوامر التوب ---

@bot.message_handler(commands=['topelo', 'topelob', 'topelobu'])
def top_com(m):
    mode = 'bullet' if 'bu' in m.text else ('blitz' if 'elob' in m.text and 'bu' not in m.text else 'rapid')
    lb = get_lb_data('com', mode)
    markup = types.InlineKeyboardMarkup()
    if len(lb) > 10: markup.add(types.InlineKeyboardButton("المزيد ➡️", callback_data=f"p_com_{mode}_1"))
    bot.reply_to(m, format_lb(lb, f"Chess.com {mode.upper()}", 0), reply_markup=markup, parse_mode='HTML')

@bot.message_handler(commands=['topelol', 'topelobl', 'topelobul'])
def top_li(m):
    cmd = m.text.lower()
    if 'bul' in cmd: mode = 'bullet'
    elif 'bl' in cmd: mode = 'blitz'
    else: mode = 'rapid'
    lb = get_lb_data('li', mode)
    markup = types.InlineKeyboardMarkup()
    if len(lb) > 10: markup.add(types.InlineKeyboardButton("المزيد ➡️", callback_data=f"p_li_{mode}_1"))
    bot.reply_to(m, format_lb(lb, f"Lichess {mode.upper()}", 0), reply_markup=markup, parse_mode='HTML')

# --- تسجيل الدخول والخروج ---
@bot.message_handler(commands=['sign', 'signl', 'signout', 'signoutl'])
def signs_handler(m):
    cmd = m.text.lower()
    site = 'li' if 'l' in cmd else 'com'
    file = LI_DB_FILE if site == 'li' else DB_FILE
    db = load_json(file)
    if 'out' in cmd:
        uid = str(m.from_user.id)
        if uid in db: del db[uid]; save_json(file, db); bot.reply_to(m, "✅ تم إلغاء الربط.")
        else: bot.reply_to(m, "⚠️ الحساب غير مرتبط.")
    else:
        args = m.text.split()
        if len(args) > 1:
            db[str(m.from_user.id)] = args[1].strip()
            save_json(file, db); bot.reply_to(m, f"✅ تم الربط بنجاح في {'Lichess' if site == 'li' else 'Chess.com'}!")
        else:
            bot.reply_to(m, "⚠️ أرسل اليوزر مع الأمر.")

@bot.message_handler(commands=['help'])
def help_cmd(m):
    text = (
        "📖 <b>أوامر البوت:</b>\n\n"
        "👤 <b>معلومات (تعمل بالرد):</b> /elo, /elol, /user, /userl, /me\n"
        "🟢 <b>متصدري Chess.com:</b> /topelo, /topelob, /topelobu\n"
        "🔵 <b>متصدري Lichess:</b> /topelol, /topelobl, /topelobul\n"
        "🧩 <b>لغز اليوم:</b> /puzzle"
    )
    bot.reply_to(m, text, parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data.startswith('p_'))
def pages_handler(c):
    _, site, mode, p = c.data.split('_'); p = int(p)
    lb = get_lb_data(site, mode)
    markup = types.InlineKeyboardMarkup()
    btns = []
    if p > 0: btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"p_{site}_{mode}_{p-1}"))
    if (p+1)*10 < len(lb): btns.append(types.InlineKeyboardButton("➡️", callback_data=f"p_{site}_{mode}_{p+1}"))
    if btns: markup.row(*btns)
    bot.edit_message_text(format_lb(lb, f"{site.upper()} {mode.upper()}", p), c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(commands=['puzzle'])
def puzzle(m):
    try:
        r = requests.get("https://api.chess.com/pub/puzzle", headers={'User-Agent': 'Mozilla/5.0'}).json()
        bot.send_photo(m.chat.id, r['image'], caption=f"🧩 {r['title']}\n<a href='{r['url']}'>اضغط للحل</a>", parse_mode='HTML')
    except: bot.reply_to(m, "⚠️ فشل جلب اللغز.")

if __name__ == '__main__':
    print("البوت يعمل الآن...")
    bot.infinity_polling()
