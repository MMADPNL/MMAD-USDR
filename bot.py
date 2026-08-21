import json
import os
import re
import uuid
import tempfile
import traceback
import asyncio

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


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 8552447077

CHANNEL_USERNAME = "@MMAD_KING1W"
CHANNEL_URL = "https://t.me/MMAD_KING1W"

DATA_FILE = "data.json"

OWNER_START_DOGS = 100000
REFERRAL_REWARD = 150

DEPOSIT_WALLET = (
    "UQCfIahBY06klJFYNyeAcwOxpNKq78yQOSMMHHe4QDZbziwC"
)

CURRENCIES = {
    "DOGS": "DOGS",
    "TON": "TON",
    "USDT": "USDT",
    "NOT": "NOT",
    "WAT": "WAT",
    "LTC": "لایت‌کوین",
}


# =========================================================
# LOCK
# =========================================================

DATA_LOCK = asyncio.Lock()


# =========================================================
# DATABASE
# =========================================================

def empty_data():
    return {
        "users": {},
        "deposits": {},
        "withdrawals": {},
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        return empty_data()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return empty_data()

        data.setdefault("users", {})
        data.setdefault("deposits", {})
        data.setdefault("withdrawals", {})

        if not isinstance(data["users"], dict):
            data["users"] = {}

        if not isinstance(data["deposits"], dict):
            data["deposits"] = {}

        if not isinstance(data["withdrawals"], dict):
            data["withdrawals"] = {}

        return data

    except Exception as e:
        print("LOAD ERROR:", e)
        return empty_data()


def save_data(data):
    directory = os.path.dirname(os.path.abspath(DATA_FILE))
    temp_path = None

    try:
        fd, temp_path = tempfile.mkstemp(
            prefix="data_",
            suffix=".tmp",
            dir=directory
        )

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, DATA_FILE)

    except Exception as e:
        print("SAVE ERROR:", e)

        if temp_path:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass


# =========================================================
# USER DATABASE
# =========================================================

def default_user():
    return {
        "DOGS": 0,
        "TON": 0,
        "USDT": 0,
        "NOT": 0,
        "WAT": 0,
        "LTC": 0,
        "referrer": None,
        "username": None,
        "first_name": None,
        "last_name": None,
    }


def create_user(user_id, telegram_user=None):

    data = load_data()
    uid = str(user_id)
    changed = False

    if uid not in data["users"]:
        data["users"][uid] = default_user()
        changed = True

    user = data["users"][uid]

    if not isinstance(user, dict):
        user = default_user()
        data["users"][uid] = user
        changed = True

    for currency in CURRENCIES:
        if currency not in user:
            user[currency] = 0
            changed = True

    for key in [
        "referrer",
        "username",
        "first_name",
        "last_name"
    ]:
        if key not in user:
            user[key] = None
            changed = True

    if telegram_user is not None:

        username = telegram_user.username
        first_name = telegram_user.first_name
        last_name = telegram_user.last_name

        if user.get("username") != username:
            user["username"] = username
            changed = True

        if user.get("first_name") != first_name:
            user["first_name"] = first_name
            changed = True

        if user.get("last_name") != last_name:
            user["last_name"] = last_name
            changed = True

    # مالک
    if user_id == ADMIN_ID:
        if user.get("DOGS") is None:
            user["DOGS"] = OWNER_START_DOGS
            changed = True

    if changed:
        save_data(data)

    return data


def is_owner(user_id):
    try:
        return int(user_id) == ADMIN_ID
    except Exception:
        return False


# =========================================================
# FORMAT
# =========================================================

def format_amount(amount):

    try:
        value = float(amount)

        if value.is_integer():
            return f"{int(value):,}"

        return (
            f"{value:,.8f}"
            .rstrip("0")
            .rstrip(".")
        )

    except Exception:
        return str(amount)


# =========================================================
# FIND USER BY USERNAME
# =========================================================

def find_user_by_username(username):

    if not username:
        return None

    username = username.strip()

    if username.startswith("@"):
        username = username[1:]

    username = username.lower()

    if not username:
        return None

    data = load_data()

    for uid, user in data["users"].items():

        if not isinstance(user, dict):
            continue

        saved_username = user.get("username")

        if not saved_username:
            continue

        if str(saved_username).lower() == username:

            try:
                return int(uid)
            except Exception:
                return None

    return None


# =========================================================
# MY ID
# =========================================================

async def myid(update, context):

    if update.effective_chat.type != "private":
        return

    user = update.effective_user

    create_user(user.id, user)

    status = (
        "✅ شما مالک هستید."
        if is_owner(user.id)
        else
        "❌ شما مالک نیستید."
    )

    username_text = (
        f"@{user.username}"
        if user.username
        else "ندارد"
    )

    await update.message.reply_text(
        "🆔 اطلاعات شما\n\n"
        f"🆔 ID عددی:\n{user.id}\n\n"
        f"👤 Username:\n{username_text}\n\n"
        f"👑 Owner ID:\n{ADMIN_ID}\n\n"
        f"{status}"
    )


# =========================================================
# OWNER BALANCE
# =========================================================

async def ownerbalance(update, context):

    if update.effective_chat.type != "private":
        return

    if not is_owner(update.effective_user.id):
        await update.message.reply_text(
            "❌ فقط مالک می‌تواند این دستور را استفاده کند."
        )
        return

    data = create_user(
        ADMIN_ID,
        update.effective_user
    )

    user = data["users"][str(ADMIN_ID)]

    await update.message.reply_text(
        "👑 موجودی مالک\n\n"
        f"🐶 DOGS: {format_amount(user['DOGS'])}\n"
        f"💎 TON: {format_amount(user['TON'])}\n"
        f"💵 USDT: {format_amount(user['USDT'])}\n"
        f"🪙 NOT: {format_amount(user['NOT'])}\n"
        f"💧 WAT: {format_amount(user['WAT'])}\n"
        f"🪙 LTC: {format_amount(user['LTC'])}"
    )


# =========================================================
# SET OWNER
# =========================================================

async def setowner(update, context):

    if update.effective_chat.type != "private":
        return

    if not is_owner(update.effective_user.id):
        await update.message.reply_text(
            "❌ فقط مالک می‌تواند این دستور را استفاده کند."
        )
        return

    data = create_user(
        ADMIN_ID,
        update.effective_user
    )

    data["users"][str(ADMIN_ID)]["DOGS"] = OWNER_START_DOGS

    save_data(data)

    await update.message.reply_text(
        "✅ موجودی مالک تنظیم شد.\n\n"
        f"🐶 DOGS: {OWNER_START_DOGS:,}"
    )


# =========================================================
# FORCE JOIN
# =========================================================

async def is_member(user_id, context):

    try:

        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception as e:

        print("MEMBER ERROR:", e)
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
        ]
    ]

    text = (
        "🔒 برای استفاده از ربات ابتدا باید "
        "در کانال ما عضو شوید.\n\n"
        "بعد از عضویت روی دکمه "
        "«بررسی عضویت» بزنید."
    )

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif update.message:

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================================================
# MAIN MENU
# =========================================================

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
        ]
    ])


# =========================================================
# START
# =========================================================

async def start(update, context):

    if update.effective_chat.type != "private":
        return

    user = update.effective_user
    user_id = user.id

    if not await is_member(user_id, context):

        await force_join(update, context)
        return

    data = create_user(user_id, user)

    # REFERRAL
    if context.args:

        try:

            referrer_id = int(context.args[0])

            if referrer_id != user_id:

                uid = str(user_id)

                if data["users"][uid]["referrer"] is None:

                    ref_uid = str(referrer_id)

                    if ref_uid in data["users"]:

                        data["users"][uid]["referrer"] = referrer_id

                        data["users"][ref_uid]["DOGS"] += REFERRAL_REWARD

                        save_data(data)

                        try:

                            await context.bot.send_message(
                                referrer_id,
                                "🎉 زیرمجموعه جدید!\n\n"
                                f"🎁 پاداش: "
                                f"{REFERRAL_REWARD} DOGS"
                            )

                        except Exception:
                            pass

        except Exception as e:
            print("REFERRAL ERROR:", e)

    await update.message.reply_text(
        "👑 به ربات خوش آمدید!\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_keyboard()
    )


# =========================================================
# WALLET
# =========================================================

async def wallet(update, context):

    query = update.callback_query

    await query.answer()

    user = update.effective_user

    data = create_user(
        user.id,
        user
    )

    user_data = data["users"][str(user.id)]

    text = (
        "💰 کیف پول شما\n\n"
        f"🐶 DOGS: {format_amount(user_data['DOGS'])}\n"
        f"💎 TON: {format_amount(user_data['TON'])}\n"
        f"💵 USDT: {format_amount(user_data['USDT'])}\n"
        f"🪙 NOT: {format_amount(user_data['NOT'])}\n"
        f"💧 WAT: {format_amount(user_data['WAT'])}\n"
        f"🪙 لایت‌کوین: {format_amount(user_data['LTC'])}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📥 واریز",
                callback_data="deposit"
            ),
            InlineKeyboardButton(
                "📤 برداشت",
                callback_data="withdraw"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="home"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# CURRENCIES
# =========================================================

async def currencies(update, context):

    query = update.callback_query

    await query.answer()

    text = (
        "💱 ارزهای لیست شده:\n\n"
        "🐶 DOGS\n"
        "💎 TON\n"
        "💵 USDT\n"
        "🪙 NOT\n"
        "💧 WAT\n"
        "🪙 لایت‌کوین"
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# DEPOSIT MENU
# =========================================================

async def deposit(update, context):

    query = update.callback_query

    await query.answer()

    keyboard = []

    for code, name in CURRENCIES.items():

        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=f"deposit_{code}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="wallet"
        )
    ])

    await query.edit_message_text(
        "📥 ارز موردنظر برای واریز را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# DEPOSIT SELECT
# =========================================================

async def deposit_selected(update, context):

    query = update.callback_query

    await query.answer()

    currency = query.data.replace(
        "deposit_",
        "",
        1
    ).upper()

    if currency not in CURRENCIES:
        return

    context.user_data.clear()

    context.user_data["deposit_currency"] = currency
    context.user_data["waiting_deposit_amount"] = True

    await query.edit_message_text(
        f"📥 واریز {CURRENCIES[currency]}\n\n"
        "💰 مقدار واریز را ارسال کنید.\n\n"
        "مثال:\n"
        "100\n"
        "1.5"
    )


# =========================================================
# DEPOSIT AMOUNT
# =========================================================

async def handle_deposit_amount(update, context):

    text = update.message.text.strip()

    currency = context.user_data.get(
        "deposit_currency"
    )

    if not currency:
        return False

    try:
        amount = float(
            text.replace(",", "")
        )

    except ValueError:

        await update.message.reply_text(
            "❌ مقدار صحیح نیست.\n\n"
            "مثال: 100"
        )

        return True

    if amount <= 0:

        await update.message.reply_text(
            "❌ مقدار باید بیشتر از صفر باشد."
        )

        return True

    context.user_data["deposit_amount"] = amount
    context.user_data["waiting_deposit_amount"] = False
    context.user_data["waiting_deposit_photo"] = True

    await update.message.reply_text(
        f"📥 ارز: {CURRENCIES[currency]}\n"
        f"💰 مقدار: {format_amount(amount)}\n\n"
        "💳 آدرس کیف پول:\n\n"
        f"`{DEPOSIT_WALLET}`\n\n"
        "📸 حالا اسکرین‌شات تراکنش را ارسال کنید.",
        parse_mode="Markdown"
    )

    return True


# =========================================================
# DEPOSIT PHOTO
# =========================================================

async def receive_photo(update, context):

    if update.effective_chat.type != "private":
        return

    if not context.user_data.get(
        "waiting_deposit_photo"
    ):
        return

    user = update.effective_user

    create_user(user.id, user)

    currency = context.user_data.get(
        "deposit_currency"
    )

    amount = context.user_data.get(
        "deposit_amount"
    )

    if not currency or amount is None:

        context.user_data.clear()

        await update.message.reply_text(
            "❌ اطلاعات واریز پیدا نشد.\n"
            "دوباره شروع کنید."
        )

        return

    deposit_id = uuid.uuid4().hex[:10]

    data = load_data()

    data["deposits"][deposit_id] = {
        "user_id": user.id,
        "username": user.username,
        "name": user.full_name,
        "currency": currency,
        "amount": amount,
        "status": "pending"
    }

    save_data(data)

    username_text = (
        f"@{user.username}"
        if user.username
        else "ندارد"
    )

    caption = (
        "📥 درخواست واریز جدید\n\n"
        f"🆔 درخواست: {deposit_id}\n"
        f"👤 نام: {user.full_name}\n"
        f"🔗 Username: {username_text}\n"
        f"🆔 ID: {user.id}\n"
        f"💱 ارز: {CURRENCIES[currency]}\n"
        f"💰 مقدار: {format_amount(amount)}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ تأیید واریز",
                callback_data=f"approve_deposit_{deposit_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ رد واریز",
                callback_data=f"reject_deposit_{deposit_id}"
            )
        ]
    ])

    try:

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption,
            reply_markup=keyboard
        )

    except Exception as e:

        print("DEPOSIT ADMIN ERROR:", e)

        data = load_data()

        if deposit_id in data["deposits"]:
            del data["deposits"][deposit_id]

        save_data(data)

        await update.message.reply_text(
            "❌ ارسال رسید برای مالک انجام نشد."
        )

        return

    context.user_data.clear()

    await update.message.reply_text(
        "✅ رسید شما دریافت شد.\n\n"
        "⏳ برای مالک ارسال شد.\n"
        "پس از تأیید، موجودی شما اضافه می‌شود."
    )


# =========================================================
# DEPOSIT ACTION
# =========================================================

async def deposit_action(update, context):

    query = update.callback_query

    if not is_owner(update.effective_user.id):

        await query.answer(
            "❌ فقط مالک می‌تواند این کار را انجام دهد.",
            show_alert=True
        )

        return

    if query.data.startswith("approve_deposit_"):

        deposit_id = query.data.replace(
            "approve_deposit_",
            "",
            1
        )

        action = "approve"

    elif query.data.startswith("reject_deposit_"):

        deposit_id = query.data.replace(
            "reject_deposit_",
            "",
            1
        )

        action = "reject"

    else:
        return

    data = load_data()

    if deposit_id not in data["deposits"]:

        await query.answer(
            "❌ درخواست پیدا نشد.",
            show_alert=True
        )

        return

    deposit_data = data["deposits"][deposit_id]

    if deposit_data["status"] != "pending":

        await query.answer(
            "⚠️ این درخواست قبلاً بررسی شده.",
            show_alert=True
        )

        return

    user_id = deposit_data["user_id"]
    currency = deposit_data["currency"]
    amount = float(deposit_data["amount"])

    if action == "approve":

        data = create_user(user_id)
        uid = str(user_id)

        data["users"][uid][currency] += amount
        data["deposits"][deposit_id]["status"] = "approved"

        save_data(data)

        try:

            await context.bot.send_message(
                user_id,
                "✅ واریز شما تأیید شد.\n\n"
                f"💱 ارز: {CURRENCIES[currency]}\n"
                f"💰 مقدار: {format_amount(amount)}"
            )

        except Exception:
            pass

        await query.answer(
            "✅ واریز تأیید شد.",
            show_alert=True
        )

        try:

            await query.edit_message_caption(
                caption=(
                    "✅ واریز تأیید شد.\n\n"
                    f"🆔 درخواست: {deposit_id}\n"
                    f"👤 نام: {deposit_data['name']}\n"
                    f"🆔 ID: {user_id}\n"
                    f"💱 ارز: {CURRENCIES[currency]}\n"
                    f"💰 مقدار: {format_amount(amount)}"
                )
            )

        except Exception:
            pass

    else:

        data["deposits"][deposit_id]["status"] = "rejected"

        save_data(data)

        try:

            await context.bot.send_message(
                user_id,
                "❌ واریز شما رد شد.\n\n"
                f"💱 ارز: {CURRENCIES[currency]}\n"
                f"💰 مقدار: {format_amount(amount)}"
            )

        except Exception:
            pass

        await query.answer(
            "❌ واریز رد شد.",
            show_alert=True
        )

        try:

            await query.edit_message_caption(
                caption=(
                    "❌ واریز رد شد.\n\n"
                    f"🆔 درخواست: {deposit_id}\n"
                    f"👤 نام: {deposit_data['name']}\n"
                    f"🆔 ID: {user_id}\n"
                    f"💱 ارز: {CURRENCIES[currency]}\n"
                    f"💰 مقدار: {format_amount(amount)}"
                )
            )

        except Exception:
            pass


# =========================================================
# WITHDRAW MENU
# =========================================================

async def withdraw(update, context):

    query = update.callback_query

    await query.answer()

    keyboard = []

    for code, name in CURRENCIES.items():

        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=f"withdraw_{code}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="wallet"
        )
    ])

    await query.edit_message_text(
        "📤 ارز موردنظر برای برداشت را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# WITHDRAW SELECT
# =========================================================

async def withdraw_selected(update, context):

    query = update.callback_query

    await query.answer()

    currency = query.data.replace(
        "withdraw_",
        "",
        1
    ).upper()

    if currency not in CURRENCIES:
        return

    user = update.effective_user

    data = create_user(user.id, user)

    balance = data["users"][str(user.id)][currency]

    context.user_data.clear()

    context.user_data["withdraw_currency"] = currency
    context.user_data["waiting_withdraw_amount"] = True

    await query.edit_message_text(
        f"📤 برداشت {CURRENCIES[currency]}\n\n"
        f"💰 موجودی شما: {format_amount(balance)}\n\n"
        "مقدار برداشت را ارسال کنید:"
    )


# =========================================================
# WITHDRAW TEXT
# =========================================================

async def handle_withdraw_text(update, context):

    text = update.message.text.strip()

    currency = context.user_data.get(
        "withdraw_currency"
    )

    if not currency:
        return False

    if context.user_data.get(
        "waiting_withdraw_amount"
    ):

        try:

            amount = float(
                text.replace(",", "")
            )

        except ValueError:

            await update.message.reply_text(
                "❌ مقدار صحیح نیست.\n\n"
                "مثال: 100"
            )

            return True

        if amount <= 0:

            await update.message.reply_text(
                "❌ مقدار باید بیشتر از صفر باشد."
            )

            return True

        data = create_user(
            update.effective_user.id,
            update.effective_user
        )

        uid = str(update.effective_user.id)

        balance = data["users"][uid][currency]

        if amount > balance:

            await update.message.reply_text(
                "❌ موجودی کافی نیست.\n\n"
                f"💰 موجودی: {format_amount(balance)}"
            )

            return True

        context.user_data["withdraw_amount"] = amount
        context.user_data["waiting_withdraw_amount"] = False
        context.user_data["waiting_withdraw_address"] = True

        await update.message.reply_text(
            "💳 آدرس کیف پول مقصد را ارسال کنید:"
        )

        return True

    if context.user_data.get(
        "waiting_withdraw_address"
    ):

        address = text

        amount = context.user_data.get(
            "withdraw_amount"
        )

        user_id = update.effective_user.id

        if amount is None:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ درخواست منقضی شد.\n"
                "دوباره برداشت را شروع کنید."
            )

            return True

        data = load_data()
        uid = str(user_id)

        if uid not in data["users"]:
            data["users"][uid] = default_user()

        balance = float(
            data["users"][uid].get(
                currency,
                0
            )
        )

        if amount > balance:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ موجودی کافی نیست."
            )

            return True

        withdraw_id = uuid.uuid4().hex[:10]

        data["withdrawals"][withdraw_id] = {
            "user_id": user_id,
            "username": update.effective_user.username,
            "name": update.effective_user.full_name,
            "currency": currency,
            "amount": amount,
            "address": address,
            "status": "pending"
        }

        save_data(data)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ تأیید برداشت",
                    callback_data=f"approve_withdraw_{withdraw_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ رد برداشت",
                    callback_data=f"reject_withdraw_{withdraw_id}"
                )
            ]
        ])

        username = update.effective_user.username

        username_text = (
            f"@{username}"
            if username
            else "ندارد"
        )

        withdraw_text = (
            "📤 درخواست برداشت جدید\n\n"
            f"🆔 درخواست: {withdraw_id}\n"
            f"👤 نام: {update.effective_user.full_name}\n"
            f"🔗 Username: {username_text}\n"
            f"🆔 ID: {user_id}\n"
            f"💱 ارز: {CURRENCIES[currency]}\n"
            f"💰 مقدار: {format_amount(amount)}\n"
            f"💳 آدرس:\n{address}"
        )

        try:

            await context.bot.send_message(
                ADMIN_ID,
                withdraw_text,
                reply_markup=keyboard
            )

        except Exception as e:

            print("ADMIN WITHDRAW ERROR:", e)

            data = load_data()

            if withdraw_id in data["withdrawals"]:
                del data["withdrawals"][withdraw_id]

            save_data(data)

            await update.message.reply_text(
                "❌ ارسال درخواست برای مالک انجام نشد."
            )

            return True

        context.user_data.clear()

        await update.message.reply_text(
            "✅ درخواست برداشت ثبت شد.\n\n"
            "⏳ منتظر تأیید مالک باشید."
        )

        return True

    return False


# =========================================================
# WITHDRAW ACTION
# =========================================================

async def withdraw_action(update, context):

    query = update.callback_query

    if not is_owner(update.effective_user.id):

        await query.answer(
            "❌ فقط مالک می‌تواند این کار را انجام دهد.",
            show_alert=True
        )

        return

    if query.data.startswith("approve_withdraw_"):

        withdraw_id = query.data.replace(
            "approve_withdraw_",
            "",
            1
        )

        action = "approve"

    elif query.data.startswith("reject_withdraw_"):

        withdraw_id = query.data.replace(
            "reject_withdraw_",
            "",
            1
        )

        action = "reject"

    else:
        return

    data = load_data()

    if withdraw_id not in data["withdrawals"]:

        await query.answer(
            "❌ درخواست پیدا نشد.",
            show_alert=True
        )

        return

    request = data["withdrawals"][withdraw_id]

    if request["status"] != "pending":

        await query.answer(
            "⚠️ این درخواست قبلاً بررسی شده.",
            show_alert=True
        )

        return

    user_id = request["user_id"]
    currency = request["currency"]
    amount = float(request["amount"])
    uid = str(user_id)

    if action == "approve":

        if uid not in data["users"]:
            data["users"][uid] = default_user()

        current_balance = float(
            data["users"][uid].get(
                currency,
                0
            )
        )

        if amount > current_balance:

            data["withdrawals"][withdraw_id]["status"] = "failed"

            save_data(data)

            await query.answer(
                "❌ موجودی کاربر دیگر کافی نیست.",
                show_alert=True
            )

            return

        data["users"][uid][currency] -= amount

        data["withdrawals"][withdraw_id]["status"] = "approved"

        save_data(data)

        try:

            await context.bot.send_message(
                user_id,
                "✅ برداشت شما تأیید شد.\n\n"
                f"💱 ارز: {CURRENCIES[currency]}\n"
                f"💰 مقدار: {format_amount(amount)}\n"
                f"💳 آدرس:\n{request['address']}"
            )

        except Exception:
            pass

        await query.answer(
            "✅ برداشت تأیید شد.",
            show_alert=True
        )

        try:

            await query.edit_message_text(
                "✅ برداشت تأیید شد.\n\n"
                f"🆔 درخواست: {withdraw_id}\n"
                f"👤 نام: {request['name']}\n"
                f"🆔 ID: {user_id}\n"
                f"💱 ارز: {CURRENCIES[currency]}\n"
                f"💰 مقدار: {format_amount(amount)}\n"
                f"💳 آدرس:\n{request['address']}"
            )

        except Exception:
            pass

    else:

        data["withdrawals"][withdraw_id]["status"] = "rejected"

        save_data(data)

        try:

            await context.bot.send_message(
                user_id,
                "❌ برداشت شما رد شد.\n\n"
                f"💱 ارز: {CURRENCIES[currency]}\n"
                f"💰 مقدار: {format_amount(amount)}"
            )

        except Exception:
            pass

        await query.answer(
            "❌ برداشت رد شد.",
            show_alert=True
        )

        try:

            await query.edit_message_text(
                "❌ برداشت رد شد.\n\n"
                f"🆔 درخواست: {withdraw_id}\n"
                f"👤 نام: {request['name']}\n"
                f"🆔 ID: {user_id}\n"
                f"💱 ارز: {CURRENCIES[currency]}\n"
                f"💰 مقدار: {format_amount(amount)}"
            )

        except Exception:
            pass


# =========================================================
# TRANSFER BY USERNAME
#
# قبول می‌کند:
#
# wallet 200 DOGS @MMAD_KING
# wallet 200 DOGS MMAD_KING
# wallet 200 DOGS @MMAD123
# wallet 200 DOGS MMAD123
# wallet 200 DOGS user123
#
# Username تلگرام می‌تواند حروف، عدد و _ داشته باشد.
# =========================================================

async def wallet_transfer(update, context):

    message = update.message
    sender = update.effective_user

    parts = message.text.strip().split()

    if len(parts) != 4:

        await message.reply_text(
            "❌ فرمت انتقال اشتباه است.\n\n"
            "فرمت صحیح:\n"
            "wallet مقدار ارز آیدی\n\n"
            "مثال:\n"
            "wallet 200 DOGS @MMAD_KING\n"
            "wallet 500 TON @username123\n"
            "wallet 10 NOT MMAD123"
        )

        return

    command = parts[0].lower()

    if command != "wallet":
        return

    # =====================================================
    # AMOUNT
    # =====================================================

    amount_text = parts[1].replace(",", "")

    try:

        amount = float(amount_text)

    except ValueError:

        await message.reply_text(
            "❌ مقدار صحیح نیست.\n\n"
            "مثال:\n"
            "wallet 200 DOGS @MMAD_KING"
        )

        return

    if amount <= 0:

        await message.reply_text(
            "❌ مقدار باید بیشتر از صفر باشد."
        )

        return

    # =====================================================
    # CURRENCY
    # =====================================================

    currency = parts[2].upper()

    if currency not in CURRENCIES:

        await message.reply_text(
            "❌ ارز نامعتبر است.\n\n"
            "ارزهای قابل انتقال:\n\n"
            "🐶 DOGS\n"
            "💎 TON\n"
            "💵 USDT\n"
            "🪙 NOT\n"
            "💧 WAT\n"
            "🪙 LTC"
        )

        return

    # =====================================================
    # USERNAME
    # =====================================================

    target_username = parts[3].strip()

    # @ اختیاری است
    if target_username.startswith("@"):
        target_username_clean = target_username[1:]
    else:
        target_username_clean = target_username

    target_username_clean = target_username_clean.strip()

    # =====================================================
    # مهم:
    # حروف انگلیسی + عدد + _
    #
    # مثال:
    # MMAD123
    # user123
    # MMAD_KING1
    # =====================================================

    if not re.fullmatch(
        r"[A-Za-z0-9_]{3,32}",
        target_username_clean
    ):

        await message.reply_text(
            "❌ آیدی کاربر صحیح نیست.\n\n"
            "آیدی باید شامل حروف انگلیسی، عدد یا _ باشد.\n\n"
            "مثال:\n"
            "@MMAD123\n"
            "@MMAD_KING1\n"
            "user123"
        )

        return

    # =====================================================
    # CREATE SENDER
    # =====================================================

    create_user(
        sender.id,
        sender
    )

    # =====================================================
    # SELF CHECK
    # =====================================================

    if (
        sender.username
        and
        sender.username.lower()
        == target_username_clean.lower()
    ):

        await message.reply_text(
            "❌ نمی‌توانید به خودتان انتقال دهید."
        )

        return

    # =====================================================
    # FIND TARGET
    # =====================================================

    target_user_id = find_user_by_username(
        target_username_clean
    )

    if target_user_id is None:

        await message.reply_text(
            "❌ این کاربر در ربات پیدا نشد.\n\n"
            f"👤 آیدی مقصد: @{target_username_clean}\n\n"
            "⚠️ کاربر مقصد باید حداقل یک‌بار "
            "ربات را /start کرده باشد و Username "
            "تلگرام داشته باشد."
        )

        return

    # =====================================================
    # SELF CHECK BY ID
    # =====================================================

    if sender.id == target_user_id:

        await message.reply_text(
            "❌ نمی‌توانید به خودتان انتقال دهید."
        )

        return

    # =====================================================
    # CREATE TARGET
    # =====================================================

    create_user(target_user_id)

    data = load_data()

    sender_uid = str(sender.id)
    target_uid = str(target_user_id)

    # =====================================================
    # BALANCE
    # =====================================================

    sender_balance = float(
        data["users"][sender_uid].get(
            currency,
            0
        )
    )

    if amount > sender_balance:

        await message.reply_text(
            "❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی شما: "
            f"{format_amount(sender_balance)} {currency}\n"
            f"💸 مبلغ انتقال: "
            f"{format_amount(amount)} {currency}"
        )

        return

    # =====================================================
    # TRANSFER
    # =====================================================

    data["users"][sender_uid][currency] -= amount

    data["users"][target_uid][currency] += amount

    save_data(data)

    new_balance = data[
        "users"
    ][sender_uid][currency]

    target_data = data["users"][target_uid]

    receiver_username = (
        target_data.get("username")
        or target_username_clean
    )

    # =====================================================
    # SENDER MESSAGE
    # =====================================================

    await message.reply_text(
        "✅ انتقال با موفقیت انجام شد.\n\n"
        f"👤 گیرنده: @{receiver_username}\n"
        f"💰 مقدار: "
        f"{format_amount(amount)} {currency}\n\n"
        f"💳 موجودی شما:\n"
        f"{format_amount(new_balance)} {currency}"
    )

    # =====================================================
    # RECEIVER MESSAGE
    # =====================================================

    try:

        await context.bot.send_message(
            target_user_id,
            "💰 یک انتقال برای شما انجام شد.\n\n"
            f"👤 فرستنده: {sender.full_name}\n"
            f"💰 مقدار: "
            f"{format_amount(amount)} {currency}"
        )

    except Exception as e:

        print(
            "RECEIVER MESSAGE ERROR:",
            e
        )


# =========================================================
# REFERRAL
# =========================================================

async def referral(update, context):

    query = update.callback_query

    await query.answer()

    user = update.effective_user

    create_user(
        user.id,
        user
    )

    bot = await context.bot.get_me()

    link = (
        f"https://t.me/"
        f"{bot.username}"
        f"?start={user.id}"
    )

    await query.edit_message_text(
        "👥 زیرمجموعه‌گیری\n\n"
        "🔗 لینک اختصاصی شما:\n\n"
        f"{link}\n\n"
        f"🎁 پاداش هر زیرمجموعه: "
        f"{REFERRAL_REWARD} DOGS",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="home"
                )
            ]
        ])
    )


# =========================================================
# HOME
# =========================================================

async def home(update, context):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "👑 منوی اصلی\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_keyboard()
    )


# =========================================================
# CHECK JOIN
# =========================================================

async def check_join(update, context):

    query = update.callback_query

    user_id = update.effective_user.id

    if await is_member(user_id, context):

        await query.answer(
            "✅ عضویت شما تأیید شد.",
            show_alert=True
        )

        try:

            await query.edit_message_text(
                "👑 به ربات خوش آمدید!\n\n"
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=main_keyboard()
            )

        except Exception:
            pass

    else:

        await query.answer(
            "❌ هنوز در کانال عضو نشده‌اید.",
            show_alert=True
        )


# =========================================================
# TEXT HANDLER
# =========================================================

async def receive_text(update, context):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    # =====================================================
    # TRANSFER
    # =====================================================

    if re.match(
        r"^wallet\s+",
        text,
        re.IGNORECASE
    ):

        await wallet_transfer(
            update,
            context
        )

        return

    # =====================================================
    # DEPOSIT AMOUNT
    # =====================================================

    if context.user_data.get(
        "waiting_deposit_amount"
    ):

        await handle_deposit_amount(
            update,
            context
        )

        return

    # =====================================================
    # WITHDRAW
    # =====================================================

    if (
        context.user_data.get(
            "waiting_withdraw_amount"
        )
        or
        context.user_data.get(
            "waiting_withdraw_address"
        )
    ):

        await handle_withdraw_text(
            update,
            context
        )

        return


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):

    print("BOT ERROR:")

    traceback.print_exception(
        type(context.error),
        context.error,
        context.error.__traceback__
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN پیدا نشد."
        )

        return

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # COMMANDS

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "myid",
            myid
        )
    )

    application.add_handler(
        CommandHandler(
            "ownerbalance",
            ownerbalance
        )
    )

    application.add_handler(
        CommandHandler(
            "setowner",
            setowner
        )
    )

    # CALLBACKS

    application.add_handler(
        CallbackQueryHandler(
            check_join,
            pattern=r"^check_join$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            wallet,
            pattern=r"^wallet$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            referral,
            pattern=r"^referral$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            currencies,
            pattern=r"^currencies$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            deposit,
            pattern=r"^deposit$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            deposit_selected,
            pattern=r"^deposit_(DOGS|TON|USDT|NOT|WAT|LTC)$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            deposit_action,
            pattern=r"^(approve|reject)_deposit_[A-Za-z0-9]+$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            withdraw,
            pattern=r"^withdraw$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            withdraw_selected,
            pattern=r"^withdraw_(DOGS|TON|USDT|NOT|WAT|LTC)$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            withdraw_action,
            pattern=r"^(approve|reject)_withdraw_[A-Za-z0-9]+$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            home,
            pattern=r"^home$"
        )
    )

    # PHOTO

    application.add_handler(
        MessageHandler(
            filters.PHOTO & filters.ChatType.PRIVATE,
            receive_photo
        )
    )

    # TEXT

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("================================
