import json
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_USERNAME = "@MMAD_KING1W"
CHANNEL_URL = "https://t.me/MMAD_KING1W"

REFERRAL_REWARD = 150

DATA_FILE = "data.json"

CURRENCIES = {
    "DOGS": "DOGS",
    "TON": "TON",
    "USDT": "USDT",
    "NOT": "NOT",
    "WAT": "WAT",
    "LTC": "لایت‌کوین",
}

DEPOSIT_WALLET = "UQCfIahBY06klJFYNyeAcwOxpNKq78yQOSMMHHe4QDZbziwC"


# =========================
# DATABASE
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_user(user_id):
    data = load_data()
    uid = str(user_id)

    if uid not in data["users"]:
        data["users"][uid] = {
            "DOGS": 0,
            "TON": 0,
            "USDT": 0,
            "NOT": 0,
            "WAT": 0,
            "LTC": 0,
            "referrer": None,
        }

        save_data(data)

    return data


# =========================
# FORCE JOIN
# =========================

async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator",
        )

    except Exception:
        return False


async def force_join(update, context):
    keyboard = [
        [
            InlineKeyboardButton(
                "📢 عضویت در کانال",
                url=CHANNEL_URL
            )
        ],
        [
            InlineKeyboardButton(
                "✅ بررسی عضویت",
                callback_data="check_join"
            )
        ],
    ]

    text = (
        "🔒 برای استفاده از ربات ابتدا باید در کانال ما عضو شوید.\n\n"
        "بعد از عضویت روی دکمه «بررسی عضویت» بزنید."
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================
# MAIN MENU
# =========================

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💰 کیف پول",
                callback_data="wallet"
            )
        ],
        [
            InlineKeyboardButton(
                "👥 زیرمجموعه‌گیری",
                callback_data="referral"
            )
        ],
        [
            InlineKeyboardButton(
                "💱 لیست ارزها",
                callback_data="currencies"
            )
        ],
    ])


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    if not await is_member(user_id, context):
        await force_join(update, context)
        return

    data = create_user(user_id)

    # =====================
    # REFERRAL
    # =====================

    if context.args:

        try:
            referrer_id = int(context.args[0])

            if referrer_id != user_id:

                uid = str(user_id)

                if data["users"][uid]["referrer"] is None:

                    referrer_uid = str(referrer_id)

                    if referrer_uid in data["users"]:

                        data["users"][uid]["referrer"] = referrer_id

                        data["users"][referrer_uid]["DOGS"] += REFERRAL_REWARD

                        save_data(data)

                        try:
                            await context.bot.send_message(
                                referrer_id,
                                "🎉 زیرمجموعه جدید!\n\n"
                                f"🎁 پاداش شما: "
                                f"{REFERRAL_REWARD} DOGS"
                            )
                        except Exception:
                            pass

        except Exception:
            pass

    await update.message.reply_text(
        "👑 به ربات خوش آمدید!\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_keyboard()
    )


# =========================
# WALLET
# =========================

async def wallet(update, context):

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    data = create_user(user_id)

    user = data["users"][str(user_id)]

    text = (
        "💰 کیف پول شما\n\n"
        f"🐶 DOGS:
