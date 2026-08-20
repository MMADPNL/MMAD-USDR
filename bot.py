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

# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_USERNAME = "@MMAD_KING1W"
CHANNEL_URL = "https://t.me/MMAD_KING1W"

REFERRAL_REWARD = 150
OWNER_START_DOGS = 100000

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
        return {
            "users": {},
            "deposits": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "users" not in data:
            data["users"] = {}

        if "deposits" not in data:
            data["deposits"] = {}

        return data

    except Exception:
        return {
            "users": {},
            "deposits": {}
        }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def create_user(user_id):
    data = load_data()
    uid = str(user_id)
    changed = False

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

        # موجودی اولیه مالک
        if ADMIN_ID != 0 and user_id == ADMIN_ID:
            data["users"][uid]["DOGS"] = OWNER_START_DOGS

        changed = True

    else:
        for currency in CURRENCIES:
            if currency not in data["users"][uid]:
                data["users"][uid][currency] = 0
                changed = True

        if "referrer" not in data["users"][uid]:
            data["users"][uid]["referrer"] = None
            changed = True

        # اگر مالک قبلاً ساخته شده ولی DOGS او صفر است
        if ADMIN_ID != 0 and user_id == ADMIN_ID:
            if data["users"][uid]["DOGS"] == 0:
                data["users"][uid]["DOGS"] = OWNER_START_DOGS
                changed = True

    if changed:
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
            "creator"
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
        ]
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
        f"🐶 DOGS: {user['DOGS']:,}\n"
        f"💎 TON: {user['TON']:,}\n"
        f"💵 USDT: {user['USDT']:,}\n"
        f"🪙 NOT: {user['NOT']:,}\n"
        f"💧 WAT: {user['WAT']:,}\n"
        f"🪙 لایت‌کوین: {user['LTC']:,}\n"
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


# =========================
# CURRENCIES
# =========================

async def currencies(update, context):

    query = update.callback_query
    await query.answer()

    text = (
        "💱 ارزهای لیست شده در ربات:\n\n"
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


# =========================
# DEPOSIT MENU
# =========================

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


# =========================
# DEPOSIT SELECT
# =========================

async def deposit_selected(update, context):

    query = update.callback_query
    await query.answer()

    currency = query.data.replace(
        "deposit_",
        ""
    )

    if currency not in CURRENCIES:
        return

    context.user_data["deposit_currency"] = currency
    context.user_data["waiting_deposit_amount"] = True
    context.user_data["waiting_deposit_photo"] = False

    await query.edit_message_text(
        f"📥 واریز {CURRENCIES[currency]}\n\n"
        "💰 مقدار واریز را ارسال کنید.\n\n"
        "مثال:\n"
        "100\n"
        "1.5"
    )


# =========================
# DEPOSIT AMOUNT
# =========================

async def receive_deposit_amount(update, context):

    text = update.message.text.strip()

    try:
        amount = float(text)
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

    currency = context.user_data.get(
        "deposit_currency"
    )

    if not currency:

        await update.message.reply_text(
            "❌ ارز انتخاب نشده است."
        )

        context.user_data.clear()

        return True

    context.user_data["deposit_amount"] = amount
    context.user_data["waiting_deposit_amount"] = False
    context.user_data["waiting_deposit_photo"] = True

    await update.message.reply_text(
        f"💰 مقدار: {amount}\n"
        f"💱 ارز: {CURRENCIES[currency]}\n\n"
        "💳 آدرس کیف پول:\n\n"
        f"`{DEPOSIT_WALLET}`\n\n"
        "📸 حالا اسکرین‌شات تراکنش را ارسال کنید.\n\n"
        "⏳ بعد از بررسی مالک، موجودی شما اضافه می‌شود.",
        parse_mode="Markdown"
    )

    return True


# =========================
# DEPOSIT PHOTO
# =========================

async def receive_photo(update, context):

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

        await update.message.reply_text(
            "❌ اطلاعات واریز پیدا نشد. دوباره از بخش واریز شروع کنید."
        )

        context.user_data.clear()

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
        "⚠️ برای بررسی یکی از دکمه‌ها را بزنید."
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

    if ADMIN_ID == 0:

        await update.message.reply_text(
            "❌ ADMIN_ID تنظیم نشده است."
        )

        return

    try:

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption,
            reply_markup=keyboard
        )

    except Exception as e:

        print(
            "Deposit admin error:",
            e
        )

        await update.message.reply_text(
            "❌ ارسال رسید به مالک انجام نشد."
        )

        return

    context.user_data.clear()

    await update.message.reply_text(
        "✅ رسید شما دریافت شد.\n\n"
        "⏳ برای مالک ارسال شد.\n"
        "پس از تأیید، موجودی شما اضافه می‌شود."
    )


# =========================
# DEPOSIT APPROVE / REJECT
# =========================

async def deposit_action(update, context):

    query = update.callback_query

    if update.effective_user.id != ADMIN_ID:

        await query.answer(
            "❌ فقط مالک ربات می‌تواند این کار را انجام دهد.",
            show_alert=True
        )

        return

    if query.data.startswith(
        "approve_deposit_"
    ):

        deposit_id = query.data.replace(
            "approve_deposit_",
            ""
        )

        action = "approve"

    elif query.data.startswith(
        "reject_deposit_"
    ):

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

    deposit = data["deposits"][deposit_id]

    if deposit["status"] != "pending":

        await query.answer(
            "⚠️ این درخواست قبلاً بررسی شده.",
            show_alert=True
        )

        return

    user_id = deposit["user_id"]
    currency = deposit["currency"]
    amount = deposit["amount"]

    if action == "approve":

        data = create_user(user_id)

        data["users"][str(user_id)][currency] += amount

        data["deposits"][deposit_id]["status"] = "approved"

        save_data(data)

        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ واریز شما تأیید شد.\n\n"
                    f"💱 ارز: {CURRENCIES[currency]}\n"
                    f"💰 مقدار: {amount}\n\n"
                    "💳 موجودی شما افزایش یافت."
                )
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
                    f"👤 نام: {deposit['name']}\n"
                    f"🆔 ID: {user_id}\n"
                    f"💱 ارز: {CURRENCIES[currency]}\n"
                    f"💰 مقدار: {amount}"
                )
            )

        except Exception:
            pass

    else:

        data["deposits"][deposit_id]["status"] = "rejected"

        save_data(data)

        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ واریز شما رد شد.\n\n"
                    f"💱 ارز: {CURRENCIES[currency]}\n"
                    f"💰 مقدار: {amount}"
                )
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
                    f"👤 نام: {deposit['name']}\n"
                    f"🆔 ID: {user_id}\n"
                    f"💱 ارز: {CURRENCIES[currency]}\n"
                    f"💰 مقدار: {amount}"
                )
            )

        except Exception:
            pass


# =========================
# WITHDRAW
# =========================

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


# =========================
# WITHDRAW SELECTED
# =========================

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

    context.user_data["withdraw_currency"] = currency
    context.user_data["waiting_withdraw_amount"] = True

    await query.edit_message_text(
        f"📤 برداشت {CURRENCIES[currency]}\n\n"
        f"💰 موجودی شما: {balance:,}\n\n"
        "لطفاً مقدار برداشت را ارسال کنید:"
    )


# =========================
# WALLET TRANSFER
# =========================

async def wallet_transfer(update, context):

    message = update.message

    if not message.reply_to_message:

        await message.reply_text(
            "❌ برای انتقال باید روی پیام کاربر Reply کنید.\n\n"
            "مثال:\n"
            "wallet 200 dogs\n"
            "wallet 1 ton\n"
            "wallet 100 wat\n"
            "wallet 1 usdt\n"
            "wallet 10 not\n"
            "wallet 5 ltc"
        )

        return

    target_user = message.reply_to_message.from_user
    sender = update.effective_user

    if not target_user:

        await message.reply_text(
            "❌ کاربر مقصد پیدا نشد."
        )

        return

    if sender.id == target_user.id:

        await message.reply_text(
            "❌ نمی‌توانید به خودتان انتقال دهید."
        )

        return

    parts = message.text.strip().split()

    if len(parts) != 3:

        await message.reply_text(
            "❌ فرمت اشتباه است.\n\n"
            "مثال:\n"
            "wallet 200 dogs"
        )

        return

    try:
        amount = float(parts[1])
    except ValueError:

        await message.reply_text(
            "❌ مقدار صحیح نیست."
        )

        return

    if amount <= 0:

        await message.reply_text(
            "❌ مقدار باید بیشتر از صفر باشد."
        )

        return

    currency = parts[2].upper()

    if currency not in CURRENCIES:

        await message.reply_text(
            "❌ ارز نامعتبر است.\n\n"
            "DOGS\n"
            "TON\n"
            "USDT\n"
            "NOT\n"
            "WAT\n"
            "LTC"
        )

        return

    data = create_user(sender.id)
    data = create_user(target_user.id)

    sender_uid = str(sender.id)
    target_uid = str(target_user.id)

    sender_balance = data["users"][sender_uid][currency]

    if amount > sender_balance:

        await message.reply_text(
            "❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی شما: {sender_balance:,} {currency}"
        )

        return

    data["users"][sender_uid][currency] -= amount
    data["users"][target_uid][currency] += amount

    save_data(data)

    sender_new = data["users"][sender_uid][currency]
    target_new = data["users"][target_uid][currency]

    if amount.is_integer():
        amount_text = f"{int(amount):,}"
    else:
        amount_text = f"{amount:,}"

    await message.reply_text(
        "✅ انتقال با موفقیت انجام شد.\n\n"
        f"👤 فرستنده: {sender.full_name}\n"
        f"👤 گیرنده: {target_user.full_name}\n"
        f"💰 مقدار: {amount_text} {currency}\n\n"
        f"💳 موجودی شما: {sender_new:,} {currency}\n"
        f"💳 موجودی گیرنده: {target_new:,} {currency}"
    )


# =========================
# TEXT
# =========================

async def receive_text(update, context):

    text = update.message.text.strip()

    user_id = update.effective_user.id

    # wallet transfer
    if re.match(
        r"^wallet\s+[-+]?\d+(?:\.\d+)?\s+[a-zA-Z]+$",
        text,
        re.IGNORECASE
    ):

        await wallet_transfer(
            update,
            context
        )

        return

    # deposit amount
    if context.user_data.get(
        "waiting_deposit_amount"
    ):

        await receive_deposit_amount(
            update,
            context
        )

        return

    # withdraw amount
    if context.user_data.get(
        "waiting_withdraw_amount"
    ):

        currency = context.user_data.get(
            "withdraw_currency"
        )

        try:
            amount = float(text)

        except ValueError:

            await update.message.reply_text(
                "❌ مقدار وارد شده صحیح نیست."
            )

            return

        data = create_user(user_id)

        balance = data["users"][str(user_id)][currency]

        if amount <= 0:

            await update.message.reply_text(
                "❌ مقدار باید بیشتر از صفر باشد."
            )

            return

        if amount > balance:

            await update.message.reply_text(
                "❌ موجودی کافی نیست."
            )

            return

        context.user_data["withdraw_amount"] = amount
        context.user_data["waiting_withdraw_amount"] = False
        context.user_data["waiting_withdraw_address"] = True

        await update.message.reply_text(
            "💳 آدرس کیف پول مقصد را ارسال کنید:"
        )

        return

    # withdraw address
    if context.user_data.get(
        "waiting_withdraw_address"
    ):

        address = text

        currency = context.user_data.get(
            "withdraw_currency"
        )

        amount = context.user_data.get(
            "withdraw_amount"
        )

        data = create_user(user_id)

        data["users"][str(user_id)][currency] -= amount

        save_data(data)

        context.user_data.clear()

        withdraw_text = (
            "📤 درخواست برداشت جدید\n\n"
            f"👤 نام: {update.effective_user.full_name}\n"
            f"🆔 ID: {user_id}\n"
            f"💱 ارز: {CURRENCIES[currency]}\n"
            f"💰 مقدار: {amount}\n"
            f"💳 آدرس کیف پول:\n{address}"
        )

        if ADMIN_ID != 0:

            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=withdraw_text
                )
            except Exception as e:
                print(
                    "Admin withdraw error:",
                    e
                )

        try:

            await context.bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=withdraw_text
            )

        except Exception as e:

            print(
                "Channel send error:",
                e
            )

        await update.message.reply_text(
            "✅ درخواست برداشت شما ثبت شد.\n\n"
            "⏳ پس از بررسی مدیریت انجام می‌شود."
        )

        return


# =========================
# REFERRAL
# =========================

async def referral(update, context):

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    bot = await context.bot.get_me()

    link = (
        f"https://t.me/{bot.username}"
        f"?start={user_id}"
    )

    text = (
        "👥 زیرمجموعه‌گیری\n\n"
        "🔗 لینک اختصاصی شما:\n\n"
        f"{link}\n\n"
        "🎁 به ازای هر زیرمجموعه موفق:\n"
        f"💰 {REFERRAL_REWARD} DOGS\n\n"
        "پاداش به صورت خودکار به کیف پول شما اضافه می‌شود."
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


# =========================
# CALLBACKS
# =========================

async def callbacks(update, context):

    query = update.callback_query
    data = query.data

    # deposit approve / reject
    if (
        data.startswith("approve_deposit_")
        or
        data.startswith("reject_deposit_")
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

    elif data == "home":

        await query.answer()

        await query.edit_message_text(
            "👑 منوی اصلی\n\n"
            "یکی از گزینه‌ها را انتخاب کنید:",
            reply_markup=main_keyboard()
        )

    elif data == "wallet":

        await wallet(update, context)

    elif data == "currencies":

        await currencies(update, context)

    elif data == "referral":

        await referral(update, context)

    elif data == "deposit":

        await deposit(update, context)

    elif data.startswith("deposit_"):

        await deposit_selected(
            update,
            context
        )

    elif data == "withdraw":

        await withdraw(update, context)

    elif data.startswith("withdraw_"):

        await withdraw_selected(
            update,
            context
        )


# =========================
# ERROR
# =========================

async def error_handler(update, context):

    print(
        "ERROR:",
        context.error
    )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN تنظیم نشده است."
        )

        return

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(60)
        .read_timeout(60)
        .write_timeout(60)
        .pool_timeout(60)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            callbacks
        )
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            receive_photo
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "✅ ربات در حال اجراست..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
