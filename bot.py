import json
import os
import re
import uuid

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


# ==================================================
# SETTINGS
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 👑 آیدی عددی مالک
ADMIN_ID = 8552447077

CHANNEL_USERNAME = "@MMAD_KING1W"
CHANNEL_URL = "https://t.me/MMAD_KING1W"

OWNER_START_DOGS = 100000
REFERRAL_REWARD = 150

DATA_FILE = "data.json"

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


# ==================================================
# DATABASE
# ==================================================

def empty_user():
    return {
        "DOGS": 0,
        "TON": 0,
        "USDT": 0,
        "NOT": 0,
        "WAT": 0,
        "LTC": 0,
        "referrer": None,
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "users": {},
            "deposits": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            data = {}

        data.setdefault("users", {})
        data.setdefault("deposits", {})

        return data

    except Exception as e:
        print("LOAD ERROR:", e)

        return {
            "users": {},
            "deposits": {}
        }


def save_data(data):
    temp_file = DATA_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(temp_file, DATA_FILE)


# ==================================================
# USER
# ==================================================

def create_user(user_id):
    data = load_data()

    uid = str(user_id)
    changed = False

    if uid not in data["users"]:
        data["users"][uid] = empty_user()
        changed = True

        # فقط بار اول که حساب مالک ساخته می‌شود
        if user_id == ADMIN_ID:
            data["users"][uid]["DOGS"] = OWNER_START_DOGS

    else:
        user = data["users"][uid]

        for currency in CURRENCIES:
            if currency not in user:
                user[currency] = 0
                changed = True

        if "referrer" not in user:
            user["referrer"] = None
            changed = True

    if changed:
        save_data(data)

    return data


def is_owner(user_id):
    return int(user_id) == ADMIN_ID


# ==================================================
# MY ID
# ==================================================

async def myid(update, context):

    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id

    status = (
        "✅ شما مالک هستید."
        if is_owner(user_id)
        else "❌ شما مالک نیستید."
    )

    await update.message.reply_text(
        "🆔 اطلاعات شما\n\n"
        f"🆔 ID شما: {user_id}\n\n"
        f"👑 Owner ID: {ADMIN_ID}\n\n"
        f"{status}"
    )


# ==================================================
# OWNER BALANCE
# ==================================================

async def ownerbalance(update, context):

    if update.effective_chat.type != "private":
        return

    if not is_owner(update.effective_user.id):

        await update.message.reply_text(
            "❌ فقط مالک می‌تواند این دستور را استفاده کند."
        )
        return

    data = create_user(ADMIN_ID)

    user = data["users"][str(ADMIN_ID)]

    await update.message.reply_text(
        "👑 موجودی مالک\n\n"
        f"🐶 DOGS: {user['DOGS']:,}\n"
        f"💎 TON: {user['TON']:,}\n"
        f"💵 USDT: {user['USDT']:,}\n"
        f"🪙 NOT: {user['NOT']:,}\n"
        f"💧 WAT: {user['WAT']:,}\n"
        f"🪙 LTC: {user['LTC']:,}"
    )


# ==================================================
# SET OWNER
# ==================================================

async def setowner(update, context):

    if update.effective_chat.type != "private":
        return

    if not is_owner(update.effective_user.id):

        await update.message.reply_text(
            "❌ فقط مالک می‌تواند این دستور را استفاده کند."
        )
        return

    data = create_user(ADMIN_ID)

    data["users"][str(ADMIN_ID)]["DOGS"] = OWNER_START_DOGS

    save_data(data)

    await update.message.reply_text(
        "✅ موجودی مالک تنظیم شد.\n\n"
        f"🐶 DOGS: {OWNER_START_DOGS:,}"
    )


# ==================================================
# FORCE JOIN
# ==================================================

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


# ==================================================
# MAIN MENU
# ==================================================

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


# ==================================================
# START
# ==================================================

async def start(update, context):

    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id

    if not await is_member(user_id, context):

        await force_join(update, context)
        return

    data = create_user(user_id)

    # ---------- REFERRAL ----------

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
                                f"🎁 پاداش شما: {REFERRAL_REWARD} DOGS"
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


# ==================================================
# WALLET
# ==================================================

async def wallet(update, context):

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    data = create_user(user_id)

    user = data["users"][str(user_id)]

    text = (
        "💰 کیف پول شما\n\n"
        f"🐶 DOGS: {user['DOGS']:,}\n"
        f"💎 TON: {user['TON']:,}\n"
        f"💵 USDT: {user['USDT']:,}\n"
        f"🪙 NOT: {user['NOT']:,}\n"
        f"💧 WAT: {user['WAT']:,}\n"
        f"🪙 لایت‌کوین: {user['LTC']:,}"
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


# ==================================================
# CURRENCIES
# ==================================================

async def currencies(update, context):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "💱 ارزهای لیست شده:\n\n"
        "🐶 DOGS\n"
        "💎 TON\n"
        "💵 USDT\n"
        "🪙 NOT\n"
        "💧 WAT\n"
        "🪙 لایت‌کوین",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="home"
                )
            ]
        ])
    )


# ==================================================
# DEPOSIT MENU
# ==================================================

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


# ==================================================
# DEPOSIT SELECT
# ==================================================

async def deposit_selected(update, context):

    query = update.callback_query
    await query.answer()

    currency = query.data.replace(
        "deposit_",
        ""
    )

    if currency not in CURRENCIES:
        return

    # پاک کردن حالت‌های قبلی
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


# ==================================================
# WITHDRAW MENU
# ==================================================

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


# ==================================================
# WITHDRAW SELECT
# ==================================================

async def withdraw_selected(update, context):

    query = update.callback_query
    await query.answer()

    currency = query.data.replace(
        "withdraw_",
        ""
    )

    if currency not in CURRENCIES:
        return

    user_id = update.effective_user.id

    data = create_user(user_id)

    balance = data["users"][str(user_id)][currency]

    context.user_data.clear()

    context.user_data["withdraw_currency"] = currency
    context.user_data["waiting_withdraw_amount"] = True

    await query.edit_message_text(
        f"📤 برداشت {CURRENCIES[currency]}\n\n"
        f"💰 موجودی شما: {balance:,}\n\n"
        "مقدار برداشت را ارسال کنید:"
    )


# ==================================================
# TEXT HANDLER
# ==================================================

async def receive_text(update, context):

    # فقط متن
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # ==================================================
    # TRANSFER - فقط در گروه/چت Reply
    # ==================================================

    transfer_match = re.match(
        r"^wallet\s+(\d+(?:\.\d+)?)\s+"
        r"(DOGS|TON|USDT|NOT|WAT|LTC)$",
        text,
        re.IGNORECASE
    )

    if transfer_match:

        await wallet_transfer(
            update,
            context
        )

        return

    # ==================================================
    # پیام عادی گروه کاملاً نادیده گرفته شود
    # ==================================================

    if update.effective_chat.type != "private":
        return

    # ==================================================
    # DEPOSIT AMOUNT
    # ==================================================

    if context.user_data.get("waiting_deposit_amount"):

        try:
            amount = float(text)
        except ValueError:

            await update.message.reply_text(
                "❌ مقدار صحیح نیست.\n"
                "لطفاً فقط عدد وارد کنید، مثلاً: 100"
            )

            return

        if amount <= 0:

            await update.message.reply_text(
                "❌ مقدار باید بیشتر از صفر باشد."
            )

            return

        currency = context.user_data.get(
            "deposit_currency"
        )

        if not currency:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ خطا. دوباره وارد بخش واریز شوید."
            )

            return

        context.user_data["deposit_amount"] = amount
        context.user_data["waiting_deposit_amount"] = False
        context.user_data["waiting_deposit_photo"] = True

        await update.message.reply_text(
            f"📥 ارز: {CURRENCIES[currency]}\n"
            f"💰 مقدار: {amount}\n\n"
            "💳 آدرس کیف پول:\n\n"
            f"`{DEPOSIT_WALLET}`\n\n"
            "📸 حالا اسکرین‌شات تراکنش را ارسال کنید.",
            parse_mode="Markdown"
        )

        return

    # ==================================================
    # WITHDRAW AMOUNT
    # ==================================================

    if context.user_data.get("waiting_withdraw_amount"):

        currency = context.user_data.get(
            "withdraw_currency"
        )

        try:
            amount = float(text)
        except ValueError:

            await update.message.reply_text(
                "❌ مقدار صحیح نیست.\n"
                "لطفاً فقط عدد وارد کنید، مثلاً: 100"
            )

            return

        if amount <= 0:

            await update.message.reply_text(
                "❌ مقدار باید بیشتر از صفر باشد."
            )

            return

        data = create_user(
            update.effective_user.id
        )

        balance = data["users"][
            str(update.effective_user.id)
        ][currency]

        if amount > balance:

            await update.message.reply_text(
                "❌ موجودی کافی نیست.\n\n"
                f"💰 موجودی شما: {balance:,} {currency}"
            )

            return

        context.user_data["withdraw_amount"] = amount
        context.user_data["waiting_withdraw_amount"] = False
        context.user_data["waiting_withdraw_address"] = True

        await update.message.reply_text(
            "💳 آدرس کیف پول مقصد را ارسال کنید:"
        )

        return

    # ==================================================
    # WITHDRAW ADDRESS
    # ==================================================

    if context.user_data.get(
        "waiting_withdraw_address"
    ):

        user_id = update.effective_user.id

        currency = context.user_data.get(
            "withdraw_currency"
        )

        amount = context.user_data.get(
            "withdraw_amount"
        )

        address = text

        if not currency or amount is None:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ اطلاعات برداشت پیدا نشد. دوباره تلاش کنید."
            )

            return

        data = create_user(user_id)

        balance = data["users"][
            str(user_id)
        ][currency]

        # دوباره موجودی بررسی می‌شود
        if amount > balance:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ موجودی کافی نیست."
            )

            return

        # کم کردن موجودی
        data["users"][str(user_id)][currency] -= amount

        # ثبت درخواست برداشت
        withdraw_id = uuid.uuid4().hex[:10]

        if "withdrawals" not in data:
            data["withdrawals"] = {}

        data["withdrawals"][withdraw_id] = {
            "user_id": user_id,
            "name": update.effective_user.full_name,
            "currency": currency,
            "amount": amount,
            "address": address,
            "status": "pending"
        }

        save_data(data)

        withdraw_text = (
            "📤 درخواست برداشت جدید\n\n"
            f"🆔 درخواست: {withdraw_id}\n"
            f"👤 نام: {update.effective_user.full_name}\n"
            f"🆔 ID: {user_id}\n"
            f"💱 ارز: {CURRENCIES[currency]}\n"
            f"💰 مقدار: {amount}\n"
            f"💳 آدرس کیف پول:\n{address}"
        )

        # ارسال برای مالک
        try:

            await context.bot.send_message(
                ADMIN_ID,
                withdraw_text
            )

        except Exception as e:

            print("ADMIN WITHDRAW ERROR:", e)

        # ارسال به کانال
        try:

            await context.bot.send_message(
                CHANNEL_USERNAME,
                withdraw_text
            )

        except Exception as e:

            print("CHANNEL WITHDRAW ERROR:", e)

        context.user_data.clear()

        await update.message.reply_text(
            "✅ درخواست برداشت ثبت شد.\n\n"
            "⏳ درخواست برای مالک ارسال شد."
        )

        return

    # پیام عادی خصوصی هیچ جوابی ندهد
    return


# ==================================================
# TRANSFER
# ==================================================

async def wallet_transfer(update, context):

    message = update.message

    # انتقال باید Reply باشد
    if not message.reply_to_message:

        await message.reply_text(
            "❌ برای انتقال باید روی پیام کاربر Reply کنید.\n\n"
            "مثال:\n"
            "wallet 100 dogs"
        )

        return

    sender = update.effective_user

    target = message.reply_to_message.from_user

    if not target:

        await message.reply_text(
            "❌ کاربر مقصد پیدا نشد."
        )

        return

    if sender.id == target.id:

        await message.reply_text(
            "❌ نمی‌توانید به خودتان انتقال دهید."
        )

        return

    match = re.match(
        r"^wallet\s+(\d+(?:\.\d+)?)\s+"
        r"(DOGS|TON|USDT|NOT|WAT|LTC)$",
        message.text.strip(),
        re.IGNORECASE
    )

    if not match:

        await message.reply_text(
            "❌ فرمت اشتباه است.\n\n"
            "مثال:\n"
            "wallet 100 dogs"
        )

        return

    amount = float(match.group(1))

    currency = match.group(2).upper()

    if amount <= 0:

        await message.reply_text(
            "❌ مقدار باید بیشتر از صفر باشد."
        )

        return

    # ساخت حساب فرستنده و گیرنده
    create_user(sender.id)
    create_user(target.id)

    data = load_data()

    sender_uid = str(sender.id)
    target_uid = str(target.id)

    sender_balance = data["users"][
        sender_uid
    ][currency]

    if amount > sender_balance:

        await message.reply_text(
            "❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی شما: {sender_balance:,} {currency}"
        )

        return

    # انتقال
    data["users"][sender_uid][currency] -= amount
    data["users"][target_uid][currency] += amount

    save_data(data)

    if amount.is_integer():
        amount_text = f"{int(amount):,}"
    else:
        amount_text = f"{amount:,}"

    new_balance = data["users"][
        sender_uid
    ][currency]

    await message.reply_text(
        "✅ انتقال با موفقیت انجام شد.\n\n"
        f"👤 فرستنده: {sender.full_name}\n"
        f"👤 گیرنده: {target.full_name}\n"
        f"💰 مقدار: {amount_text} {currency}\n\n"
        f"💳 موجودی شما: {new_balance:,} {currency}"
    )

    # اطلاع به گیرنده
    try:

        await context.bot.send_message(
            target.id,
            "💰 یک انتقال برای شما انجام شد.\n\n"
            f"👤 فرستنده: {sender.full_name}\n"
            f"💰 مقدار: {amount_text} {currency}"
        )

    except Exception:
        pass


# ==================================================
# PHOTO / DEPOSIT RECEIPT
# ==================================================

async def receive_photo(update, context):

    if update.effective_chat.type != "private":
        return

    if not context.user_data.get(
        "waiting_deposit_photo"
    ):
        return

    user = update.effective_user

    currency = context.user_data.get(
        "deposit_currency"
    )

    amount = context.user_data.get(
        "deposit_amount"
    )

    if not currency or amount is None:

        context.user_data.clear()

        await update.message.reply_text(
            "❌ اطلاعات واریز پیدا نشد. دوباره شروع کنید."
        )

        return

    deposit_id = uuid.uuid4().hex[:10]

    data = load_data()

    data["deposits"][deposit_id] = {
        "user_id": user.id,
        "name": user.full_name,
        "currency": currency,
        "amount": amount,
        "status": "pending"
    }

    save_data(data)

    caption = (
        "📥 درخواست واریز جدید\n\n"
        f"🆔 درخواست: {deposit_id}\n"
        f"👤 نام: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"💱 ارز: {CURRENCIES[currency]}\n"
        f"💰 مقدار: {amount}\n\n"
        "⚠️ وضعیت: در انتظار بررسی"
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

        print("ADMIN PHOTO ERROR:", e)

        await update.message.reply_text(
            "❌ ارسال رسید برای مالک انجام نشد."
        )

        return

    context.user_data.clear()

    await update.message.reply_text(
        "✅ رسید واریز دریافت شد.\n\n"
        "⏳ برای مالک ارسال شد.\n"
        "بعد از تأیید، موجودی شما اضافه می‌شود."
    )


# ==================================================
# DEPOSIT APPROVE / REJECT
# ==================================================

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
            ""
        )

        action = "approve"

    elif query.data.startswith("reject_deposit_"):

        deposit_id = query.data.replace(
            "reject_deposit_",
            ""
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

    # ==========================
    # APPROVE
    # ==========================

    if action == "approve":

        user_data = create_user(user_id)

        user_data["users"][str(user_id)][currency] += amount

        user_data["deposits"][deposit_id]["status"] = "approved"

        save_data(user_data)

        try:

            await context.bot.send_message(
                user_id,
                "✅ واریز شما تأیید شد.\n\n"
                f"💱 ارز: {CURRENCIES[currency]}\n"
                f"💰 مقدار: {amount}"
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
                    f"💰 مقدار: {amount}"
                )
            )

        except Exception:
            pass

    # ==========================
    # REJECT
    # ==========================

    else:

        data["deposits"][deposit_id]["status"] = "rejected"

        save_data(data)

        try:

            await context.bot.send_message(
                user_id,
                "❌ واریز شما رد شد.\n\n"
                f"💱 ارز: {CURRENCIES[currency]}\n"
                f"💰 مقدار: {amount}"
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
                    f"💰 مقدار: {amount}"
                )
            )

        except Exception:
            pass


# ==================================================
# REFERRAL
# ==================================================

async def referral(update, context):

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    bot = await context.bot.get_me()

    link = (
        f"https://t.me/{bot.username}"
        f"?start={user_id}"
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


# ==================================================
# CALLBACKS
# ==================================================

async def callbacks(update, context):

    query = update.callback_query
    data = query.data

    # deposit approve / reject
    if (
        data.startswith("approve_deposit_")
        or data.startswith("reject_deposit_")
    ):

        await deposit_action(
            update,
            context
        )

        return

    if data == "check_join":

        if await is_member(
            update.effective_user.id,
            context
        ):

            await query.answer(
                "✅ عضویت تأیید شد!"
            )

            await query.edit_message_text(
                "👑 خوش آمدید!\n\n"
                "یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=main_keyboard()
            )

        else:

            await query.answer(
                "❌ هنوز عضو کانال نشده‌اید.",
                show_alert=True
            )

        return

    if data == "home":

        await query.answer()

        await query.edit_message_text(
            "👑 منوی اصلی\n\n"
            "یکی از گزینه‌ها را انتخاب کنید:",
            reply_markup=main_keyboard()
        )

        return

    if data == "wallet":

        await wallet(update, context)
        return

    if data == "currencies":

        await currencies(update, context)
        return

    if data == "referral":

        await referral(update, context)
        return

    if data == "deposit":

        await deposit(update, context)
        return

    if data.startswith("deposit_"):

        await deposit_selected(
            update,
            context
        )

        return

    if data == "withdraw":

        await withdraw(update, context)
        return

    if data.startswith("withdraw_"):

        await withdraw_selected(
            update,
            context
        )

        return


# ==================================================
# ERROR
# ==================================================

async def error_handler(update, context):

    print(
        "BOT ERROR:",
        context.error
    )


# ==================================================
# MAIN
# ==================================================

def main():

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN تنظیم نشده است."
        )

        return

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(60)
        .read_timeout(60)
        .write_timeout(60)
        .pool_timeout(60)
        .build()
    )

    # Commands
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

    # Callbacks
    application.add_handler(
        CallbackQueryHandler(
            callbacks
        )
    )

    # Photos فقط خصوصی
    application.add_handler(
        MessageHandler(
            filters.PHOTO & filters.ChatType.PRIVATE,
            receive_photo
        )
    )

    # Text
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("==============================")
    print("✅ BOT IS RUNNING")
    print(f"👑 OWNER ID: {ADMIN_ID}")
    print("==============================")

    application.run_polling()


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    main()
