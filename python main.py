import telebot
from telebot import types
import random

TOKEN = os.getenv("8284563854:AAE1paum5oJrUm1l6cpyWeGva_aZr68XZFA")
bot = telebot.TeleBot(TOKEN)

# ===============================
# GLOBAL O‘ZGARUVCHILAR
# ===============================
players = {}        # {uid: {"name": ..., "role": ..., "alive": True}}
game_started = False
night_phase = False
vote_phase = False
votes = {}          # kimga ovoz -> ovozlar soni

# TUN TANLOVLARI
mafia_target = None
don_check = None
doctor_save = None
commissar_check = None
maniac_kill = None
witch_kill = None
witch_save_used = False
witch_poison_used = False

# Rollar to‘plami
roles = [
    "Mafia", "Mafia", 
    "Don",
    "Komissar", 
    "Shifokor",
    "Jodugar",
    "Maniak",
    "Tinch aholi", "Tinch aholi", "Tinch aholi"
]


# ===============================
# START
# ===============================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     "😈 *Mafia PRO o‘yiniga xush kelibsiz!*\n"
                     "👉 /join — o‘yinga qo‘shilish\n"
                     "👉 /startgame — o‘yinni boshlash\n"
                     "👉 Admin: /endgame — o‘yinni tugatish",
                     parse_mode="Markdown")


# ===============================
# O‘YINCHI QO‘SHISH
# ===============================
@bot.message_handler(commands=['join'])
def join(message):
    global players, game_started

    if game_started:
        bot.reply_to(message, "⛔ O‘yin allaqachon boshlangan.")
        return

    uid = message.from_user.id

    if uid in players:
        bot.reply_to(message, "✔ Siz allaqachon ro‘yxatda bor ekansiz.")
        return

    players[uid] = {"name": message.from_user.first_name, 
                    "role": None, 
                    "alive": True}

    bot.send_message(message.chat.id,
                     f"👤 {message.from_user.first_name} o‘yinga qo‘shildi!\n"
                     f"Jami o‘yinchilar: {len(players)}")


# ===============================
# O‘YINNI BOSHLASH
# ===============================
@bot.message_handler(commands=['startgame'])
def startgame(message):
    global game_started
    if game_started:
        bot.reply_to(message, "⛔ O‘yin avval boshlangandi.")
        return

    if len(players) < 6:
        bot.reply_to(message, "⚠ Kamida 6 ta o‘yinchi kerak.")
        return

    game_started = True
    bot.send_message(message.chat.id, "🎮 O‘yin boshlandi!")

    assign_roles()
    night()


# ===============================
# ROLLARNI TAQSIMLASH
# ===============================
def assign_roles():
    temp_roles = roles.copy()
    random.shuffle(temp_roles)

    for uid in players:
        role = temp_roles.pop()
        players[uid]["role"] = role

        try:
            bot.send_message(uid, f"🎭 Sizning rolingiz: *{role}*", parse_mode="Markdown")
        except:
            pass


# ===============================
# TUN BOSQICHI
# ===============================
def night():
    global night_phase
    night_phase = True

    bot.send_message(list(players.keys())[0], "🌙 *Tun boshlandi!*", parse_mode="Markdown")

    mafia_menu()
    don_menu()
    doctor_menu()
    commissar_menu()
    maniac_menu()
    witch_menu()


# --- MAFIA TANLOVI ---
def mafia_menu():
    markup = types.InlineKeyboardMarkup()
    for uid, p in players.items():
        if p["alive"]:
            markup.add(types.InlineKeyboardButton(p["name"], callback_data=f"maf_{uid}"))
    for uid, p in players.items():
        if p["role"] in ["Mafia"]:
            bot.send_message(uid, "🔪 MAFIA: kimni o‘ldirasiz?", reply_markup=markup)


# --- DON TEKSHIRISH ---
def don_menu():
    for uid, p in players.items():
        if p["role"] == "Don" and p["alive"]:
            markup = types.InlineKeyboardMarkup()
            for pid, pl in players.items():
                markup.add(types.InlineKeyboardButton(pl["name"], callback_data=f"don_{pid}"))
            bot.send_message(uid, "🕶 Don: komissarni toping", reply_markup=markup)


# --- SHIFOKOR ---
def doctor_menu():
    for uid, p in players.items():
        if p["role"] == "Shifokor" and p["alive"]:
            markup = types.InlineKeyboardMarkup()
            for pid, pl in players.items():
                markup.add(types.InlineKeyboardButton(pl["name"], callback_data=f"doc_{pid}"))
            bot.send_message(uid, "💉 Shifokor: kimni saqlaysiz?", reply_markup=markup)


# --- KOMISSAR ---
def commissar_menu():
    for uid, p in players.items():
        if p["role"] == "Komissar" and p["alive"]:
            markup = types.InlineKeyboardMarkup()
            for pid, pl in players.items():
                markup.add(types.InlineKeyboardButton(pl["name"], callback_data=f"com_{pid}"))
            bot.send_message(uid, "🔍 Komissar: kimni tekshirasiz?", reply_markup=markup)


# --- MANIAK ---
def maniac_menu():
    for uid, p in players.items():
        if p["role"] == "Maniak" and p["alive"]:
            markup = types.InlineKeyboardMarkup()
            for pid, pl in players.items():
                if pl["alive"]:
                    markup.add(types.InlineKeyboardButton(pl["name"], callback_data=f"man_{pid}"))
            bot.send_message(uid, "🔪 Maniak: kimni o‘ldirasiz?", reply_markup=markup)


# --- JODUGAR ---
def witch_menu():
    for uid, p in players.items():
        if p["role"] == "Jodugar" and p["alive"]:
            markup = types.InlineKeyboardMarkup()

            # saqlash eliksiri (bitta marta)
            if not witch_save_used:
                markup.add(types.InlineKeyboardButton("Saqlash eliksiri", callback_data="wit_save"))

            # zahar eliksiri (bitta marta)
            if not witch_poison_used:
                for pid, pl in players.items():
                    if pl["alive"]:
                        markup.add(types.InlineKeyboardButton(f"ZAHAR: {pl['name']}",
                                                              callback_data=f"wit_kill_{pid}"))

            bot.send_message(uid, "🧪 Jodugar harakati:", reply_markup=markup)


# ===============================
# CALLBACK TANLOVLAR
# ===============================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global mafia_target, don_check, doctor_save, commissar_check
    global maniac_kill, witch_kill, witch_save_used, witch_poison_used

    data = call.data

    ### Mafia
    if data.startswith("maf_"):
        mafia_target = int(data.split("_")[1])
        bot.answer_callback_query(call.id, "Mafia tanladi.")

    ### Don
    if data.startswith("don_"):
        pid = int(data.split("_")[1])
        don_check = pid
        if players[pid]["role"] == "Komissar":
            bot.send_message(call.from_user.id, "🕶 Bu komissar!")
        else:
            bot.send_message(call.from_user.id, "🕶 Bu komissar EMAS.")
        bot.answer_callback_query(call.id)

    ### Shifokor
    if data.startswith("doc_"):
        doctor_save = int(data.split("_")[1])
        bot.answer_callback_query(call.id, "Saqlash qabul qilindi.")

    ### Komissar
    if data.startswith("com_"):
        pid = int(data.split("_")[1])
        role = players[pid]["role"]
        bot.send_message(call.from_user.id, f"🔍 Natija: {players[pid]['name']} — *{role}*",
                         parse_mode="Markdown")
        commissar_check = pid
        bot.answer_callback_query(call.id)

    ### Maniak
    if data.startswith("man_"):
        maniac_kill = int(data.split("_")[1])
        bot.answer_callback_query(call.id, "Maniak tanladi.")

    ### Jodugar — saqlash
    if data == "wit_save":
        witch_save_used = True
        witch_kill = None
        doctor_save = mafia_target
        bot.answer_callback_query(call.id, "Jodugar saqladi.")

    ### Jodugar — zaharlash
    if data.startswith("wit_kill_"):
        witch_poison_used = True
        witch_kill = int(data.split("_")[2])
        bot.answer_callback_query(call.id, "Zahar berildi.")

    # Agar tun tugagan bo‘lsa → kun
    if mafia_target is not None:
        day()


# ===============================
# KUN BOSQICHI
# ===============================
def day():
    global night_phase, votes, vote_phase
    night_phase = False

    result = "🌞 *Kun boshlandi!*\n\n"

    killed = []

    # Mafia
    if mafia_target != doctor_save:
        players[mafia_target]["alive"] = False
        killed.append(players[mafia_target]["name"])

    # Maniak
    if maniac_kill and maniac_kill != doctor_save:
        players[maniac_kill]["alive"] = False
        killed.append(players[maniac_kill]["name"])

    # Jodugar zahri
    if witch_kill:
        players[witch_kill]["alive"] = False
        killed.append(players[witch_kill]["name"])

    if killed:
        result += "💀 O‘lganlar:\n" + "\n".join(killed)
    else:
        result += "😇 Hech kim o‘lmagan!"

    bot.send_message(list(players.keys())[0], result, parse_mode="Markdown")

    votes = {}
    start_voting()


# ===============================
# OVOZ BERISH BOSQICHI
# ===============================
def start_voting():
    global vote_phase
    vote_phase = True

    markup = types.InlineKeyboardMarkup()

    for uid, p in players.items():
        if p["alive"]:
            markup.add(types.InlineKeyboardButton(p["name"], callback_data=f"vote_{uid}"))

    for uid in players:
        if players[uid]["alive"]:
            bot.send_message(uid, "🗳 Kimni osamiz? Ovoz bering:", reply_markup=markup)


# ===============================
# OVOZ QABUL QILISH
# ===============================
@bot.callback_query_handler(func=lambda c: c.data.startswith("vote_"))
def vote_handler(call):
    uid = call.from_user.id
    target = int(call.data.split("_")[1])

    votes[uid] = target
    bot.answer_callback_query(call.id, "Ovozingiz qabul qilindi.")

    # hamma tirik o‘yinchilar ovoz berganda ->
    alive = [u for u in players if players[u]["alive"]]

    if len(votes) == len(alive):
        finish_voting()


# ===============================
# OVOZ YAKUNI
# ===============================
def finish_voting():
    vote_count = {}

    for voter, target in votes.items():
        vote_count[target] = vote_count.get(target, 0) + 1

    target = max(vote_count, key=vote_count.get)
    players[target]["alive"] = False

    bot.send_message(list(players.keys())[0],
                     f"🪓 Ovoz natijasi:\n"
                     f"{players[target]['name']} — osildi!")

    check_win()


# ===============================
# G‘OLIBNI ANIQLASH
# ===============================
def check_win():
    mafia_alive = any(p["role"] in ["Mafia", "Don"] and p["alive"] for p in players.values())
    aholi_alive = any(p["role"] not in ["Mafia", "Don"] and p["alive"] for p in players.values())

    if not mafia_alive:
        end_game("🎉 Aholi g‘olib bo‘ldi!")
    elif not aholi_alive:
        end_game("😈 Mafia g‘olib bo‘ldi!")
    else:
        night()


# ===============================
# O‘YINNI TUGATISH
# ===============================
@bot.message_handler(commands=['endgame'])
def cmd_end(message):
    end_game("🛑 O‘yin admin tomonidan tugatildi.")


def end_game(text):
    global players, game_started, night_phase, vote_phase
    players = {}
    game_started = False
    night_phase = False
    vote_phase = False

    bot.send_message(list(players.keys())[0] if players else None, text)


# ===============================
# BOT NI ISHLATISH
# ===============================

# --------- WEBHOOK SETTINGS ---------
WEBHOOK_HOST = "https://baxromjon0840.github.io/mafia-bot"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    print("Webhook o‘rnatildi:", WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()
    print("Webhook o‘chirildi.")
    if name == "main":
    from aiogram import executor
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=8000
    )
