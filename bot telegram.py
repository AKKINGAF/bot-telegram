import logging
import random
import time
import asyncio
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

# تنظیم لوگینگ خفن
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("bot_log.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# توکن بات
TOKEN = '7904555787:AAG2_KfWdXKXKYqtIVg4zLg2b87OKIzf9nM'

# سازنده بات
CREATOR = "یه خفن به اسم AKKing این غول +18 رو ساخته!"

# آیدی ادمین (آیدی خودتو بذار)
ADMIN_ID = 6289381027  # آیدی عددی تلگرامت رو بذار

# دیتابیس ساده (ذخیره تو فایل)
DATA_FILE = "bot_data.json"

# لیست کاربرای بن‌شده، میوت‌شده، لقب‌ها، امتیازات و هشدارها
BANNED_USERS = set()
MUTED_USERS = {}
NICKNAMES = {}
SCORES = {}
WARNINGS = {}

# لود کردن دیتا از فایل
def load_data():
    global BANNED_USERS, MUTED_USERS, NICKNAMES, SCORES, WARNINGS
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            BANNED_USERS = set(data.get("banned", []))
            MUTED_USERS = {int(k): v for k, v in data.get("muted", {}).items()}
            NICKNAMES = {int(k): v for k, v in data.get("nicknames", {}).items()}
            SCORES = {int(k): v for k, v in data.get("scores", {}).items()}
            WARNINGS = {int(k): v for k, v in data.get("warnings", {}).items()}
    except FileNotFoundError:
        pass

# ذخیره دیتا تو فایل
def save_data():
    data = {
        "banned": list(BANNED_USERS),
        "muted": {str(k): v for k, v in MUTED_USERS.items()},
        "nicknames": {str(k): v for k, v in NICKNAMES.items()},
        "scores": {str(k): v for k, v in SCORES.items()},
        "warnings": {str(k): v for k, v in WARNINGS.items()}
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# دیکشنری جواب‌های سفارشی با فحشای +18
RESPONSES = {
    "سلام": "سلام کص‌کش! چطوری عشقم؟",
    "hi": "Hey motherfucker! What’s good?",
    "خدافظ": "برو گمشو کونی! دلم برات تنگ می‌شه!",
    "bye": "Fuck off, asshole! Catch ya later!",
    "عشقم": "جانم کیرم؟ بگو چی می‌خوای، برات جونمم می‌دم!",
    "بوس": "ماچ! بیا کصتو بخورم!",
    "sex": "اووو، کیرت راست شده؟ بیا pm حال کنیم!",
    "فحش": "کیرم تو کصت! راضی شدی جنده؟",
    "shit": "گوه نخور کص‌کش! بگو چی می‌خوای!",
    "کیر": "کیرم تو دهنت! چیه؟ چیزی می‌خوای؟",
    "کون": "کونت رو جر بدم؟ بگو چی می‌خوای!"
}

# لیست عکس‌های خفن
PHOTOS = [
    "https://i.imgur.com/8J5z7xM.jpeg",
    "https://i.imgur.com/kJ3mX9P.jpeg",
    "https://i.imgur.com/9pL2mQv.jpeg"
]

# جوک‌های +18 خفن و فحش‌دار
JOKES_18 = [
    "یه روز اومدم به زنم بگم 'بیا سکس کنیم'، گفت 'کیرمو ول کن، دارم سریال می‌بینم!'",
    "چرا کصم همیشه داغه؟ چون هر روز دنبال یه کیر جدیدم!",
    "دختره بهم گفت 'فقط به کون فکر می‌کنی'، گفتم 'آره، چون کون تو مثل ماهه!'",
    "یه روز اومدم خودمو بمالم، کیرم گفت 'دیگه گوه نخور، برو یه کص پیدا کن!'",
    "شوهرم تو رختخواب انقدر گوهه که کیرش فقط خوابشو می‌بینه!",
    "دختره pm داد، رفتم دیدم ساعت ۴ عصر، کص‌خل فکر کرده شب شده!",
    "به رفیقم گفتم 'کیرم گشنشه'، گفت 'برو گوه بخور، سیر می‌شه!'"
]

# فحش‌های رندوم +18
CURSES = [
    "کیرم تو کص مادرت، جنده!",
    "گوه نخور کونی، بگو چی می‌خوای!",
    "کص ننت رو بگام تا صبح!",
    "کیر خر تو کونت، حال کردی؟",
    "جنده‌خونه باز کردی اینجا کص‌کش!",
    "کیرم تو چشات، کور شی گوه!",
    "کص‌کش بیا pm، کیرم آماده‌ست!"
]

# پیام‌های حال‌گیری
ROASTS = [
    "تو انقدر کونی هستی که کیرم ازت خجالت می‌کشه!",
    "کص‌کش، فکر کردی کی هستی؟ برو گوهتو بشور!",
    "با اون کونت فکر کردی می‌تونی منو بترکونی؟",
    "جنده، یه کم کلاس بذار، کیرم خسته شد ازت!"
]

# پیام‌های خوشامدگویی خفن
WELCOME_MESSAGES = [
    "🔥 سلام کیرم! به بات +18 AKKing خوش اومدی! 🔥",
    "💦 هی کص‌کش! پشماتو آماده کن که بریزه! 💦",
    "🍆 سلام جنده! بیا با من حال کن! 🍆"
]

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    load_data()
    if user_id in BANNED_USERS:
        await update.message.reply_text("کص‌کش بن شدی! گمشو!")
        return
    SCORES.setdefault(user_id, 0)
    save_data()
    welcome = random.choice(WELCOME_MESSAGES) + f"\n{user} کونی! بیا حال کنیم!\nبرای لیست دستورات: /help"
    keyboard = [
        [InlineKeyboardButton("جوک +18", callback_data="joke"), InlineKeyboardButton("عکس خفن", callback_data="photo")],
        [InlineKeyboardButton("فحش باحال", callback_data="curse"), InlineKeyboardButton("حال‌گیری", callback_data="roast")],
        [InlineKeyboardButton("سازندم کیه؟", callback_data="creator"), InlineKeyboardButton("تاس بنداز", callback_data="dice")],
        [InlineKeyboardButton("شیر یا خط", callback_data="coin"), InlineKeyboardButton("ساعت", callback_data="time")],
        [InlineKeyboardButton("رندوم عدد", callback_data="roll"), InlineKeyboardButton("امتیازم", callback_data="score")],
        [InlineKeyboardButton("بازی حدس", callback_data="guess"), InlineKeyboardButton("سنگ کاغذ قیچی", callback_data="rps")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome, reply_markup=reply_markup)
    logger.info(f"کونی به اسم {user} بات رو استارت کرد.")

# دستور /help (لیست کامندها)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS:
        await update.message.reply_text("کص‌کش! بن شدی، گمشو!")
        return
    
    help_msg = f"{user} کونی! اینا دستورات منن:\n\n"
    help_msg += "دستورات عمومی:\n"
    help_msg += "/start - استارت بات، کص‌کش!\n"
    help_msg += "/help - همین لیست رو نشون می‌ده\n"
    help_msg += "/joke - یه جوک +18 خفن\n"
    help_msg += "/photo - یه عکس باحال\n"
    help_msg += "/curse - یه فحش +18 رندوم\n"
    help_msg += "/roast - حال‌گیری خفن\n"
    help_msg += "/creator - بگه کی منو ساخته\n"
    help_msg += "/dice - تاس بنداز\n"
    help_msg += "/spam - ۳ تا فحش پشت هم\n"
    help_msg += "/coin - شیر یا خط\n"
    help_msg += "/ping - سرعت بات رو تست کن\n"
    help_msg += "/time - ساعت و تاریخ الان\n"
    help_msg += "/roll <min> <max> - عدد رندوم (پیش‌فرض 1-100)\n"
    help_msg += "/stats - آمار بات\n"
    help_msg += "/score - امتیازت رو ببین\n"
    help_msg += "/guess - بازی حدس عدد (بعدش عدد بفرست)\n"
    help_msg += "/rps - سنگ کاغذ قیچی (بعدش انتخاب کن)\n"
    help_msg += "/rank - رتبه‌ت رو ببین\n"
    help_msg += "/steal <user_id> - از یکی امتیاز بدزد\n"
    help_msg += "/confess - یه اعتراف +18 بشنو\n"
    help_msg += "/spin - چرخ بخت بچرخون\n"
    help_msg += "/love - پیام عاشقانه +18 بگیر\n"
    help_msg += "/coinflip <amount> - با امتیازاتت شرط‌بندی کن\n"
    help_msg += "/roastme - یه رگبار حال‌گیری بگیر\n"
    help_msg += "/c - پاک کردن ۱۰۰ پیام آخر گروه\n\n"
    
    if user_id == ADMIN_ID:
        help_msg += "دستورات ادمین:\n"
        help_msg += "/mute <user_id> <seconds> - کاربر رو میوت کن\n"
        help_msg += "/unmute <user_id> - میوت رو باز کن\n"
        help_msg += "/ban <user_id> - کاربر رو بن کن\n"
        help_msg += "/unban <user_id> - بن رو بردار\n"
        help_msg += "/nickname <user_id> <nick> - لقب بده\n"
        help_msg += "/listusers - لیست کاربرا رو ببین\n"
        help_msg += "/broadcast <message> - پیام همگانی بفرست\n"
        help_msg += "/addscore <user_id> <amount> - امتیاز بده\n"
        help_msg += "/kick <user_id> - کاربر رو از گروه کیک کن\n"
        help_msg += "/warn <user_id> - به کاربر هشدار بده\n"
        help_msg += "/muteall - همه رو تو گروه میوت کن\n"
    
    help_msg += "\nهر چیزی بگی هم جواب می‌دم، کص‌کش!"
    await update.message.reply_text(help_msg)
    logger.info(f"لیست کامندها برای {user} فرستادم.")

# دستور /joke
async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    random_joke = random.choice(JOKES_18)
    await update.message.reply_text(f"بخند کص‌کش {user}:\n{random_joke}")
    SCORES[user_id] = SCORES.get(user_id, 0) + 1
    save_data()
    logger.info(f"جوک +18 برای {user} فرستادم.")

# دستور /photo
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    photo_url = random.choice(PHOTOS)
    await update.message.reply_photo(photo=photo_url, caption=f"برای {user} جنده‌ی خفن!")
    SCORES[user_id] = SCORES.get(user_id, 0) + 1
    save_data()
    logger.info(f"عکس برای {user} فرستادم.")

# دستور /curse
async def curse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    random_curse = random.choice(CURSES)
    await update.message.reply_text(f"بگیر {user} کونی:\n{random_curse}")
    SCORES[user_id] = SCORES.get(user_id, 0) + 1
    save_data()
    logger.info(f"فحش +18 برای {user} فرستادم.")

# دستور /roast
async def roast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    random_roast = random.choice(ROASTS)
    await update.message.reply_text(f"بگیر حال کن {user}:\n{random_roast}")
    SCORES[user_id] = SCORES.get(user_id, 0) + 1
    save_data()
    logger.info(f"حال‌گیری برای {user} فرستادم.")

# دستور /creator
async def creator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS:
        return
    await update.message.reply_text(f"منو {CREATOR} ساخته، {user} کص‌کش! خفن‌تر از این نمی‌شه!")
    logger.info(f"سازنده به {user} نشون داده شد.")

# دستور /dice
async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    await update.message.reply_dice()
    await asyncio.sleep(3)
    await update.message.reply_text(f"{user} کص‌کش! تاس انداختی، حالا بگو چی می‌خوای!")
    SCORES[user_id] = SCORES.get(user_id, 0) + 1
    save_data()
    logger.info(f"تاس برای {user} فرستادم.")

# دستور /spam
async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    await update.message.reply_text(f"آماده باش {user} جنده، اسپم فحش شروع می‌شه!")
    for i in range(3):
        random_curse = random.choice(CURSES)
        await update.message.reply_text(random_curse)
        await asyncio.sleep(1)
    SCORES[user_id] = SCORES.get(user_id, 0) + 3
    save_data()
    logger.info(f"اسپم فحش برای {user} فرستادم.")

# دستور /coin
async def coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    result = random.choice(["شیر", "خط"])
    await update.message.reply_text(f"{user} کونی! نتیجه شیر یا خط: {result}")
    SCORES[user_id] = SCORES.get(user_id, 0) + 1
    save_data()
    logger.info(f"شیر یا خط برای {user} فرستادم: {result}")

# دستور /ping
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    start_time = time.time()
    msg = await update.message.reply_text("پینگ...")
    end_time = time.time()
    latency = round((end_time - start_time) * 1000, 2)
    await msg.edit_text(f"پینگ بات برای {user} کص‌کش: {latency} میلی‌ثانیه!")
    logger.info(f"پینگ برای {user}: {latency}ms")

# دستور /time
async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    current_time = datetime.now().strftime("%H:%M:%S - %Y/%m/%d")
    await update.message.reply_text(f"{user} کونی! ساعت الان: {current_time}")
    logger.info(f"ساعت برای {user} فرستادم.")

# دستور /roll
async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    min_val = int(context.args[0]) if context.args else 1
    max_val = int(context.args[1]) if len(context.args) > 1 else 100
    result = random.randint(min_val, max_val)
    await update.message.reply_text(f"{user} کص‌کش! عدد رندوم بین {min_val} و {max_val}: {result}")
    SCORES[user_id] = SCORES.get(user_id, 0) + 1
    save_data()
    logger.info(f"رندوم عدد برای {user}: {result}")

# دستور /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    stats_msg = (
        f"آمار بات برای {user} کونی:\n"
        f"کاربرای بن‌شده: {len(BANNED_USERS)}\n"
        f"کاربرای میوت‌شده: {len(MUTED_USERS)}\n"
        f"لقب‌های ثبت‌شده: {len(NICKNAMES)}\n"
        f"کاربرای فعال: {len(SCORES)}\n"
        f"هشدارها: {len(WARNINGS)}"
    )
    await update.message.reply_text(stats_msg)
    logger.info(f"آمار برای {user} فرستادم.")

# دستور /score
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    user_score = SCORES.get(user_id, 0)
    await update.message.reply_text(f"{user} کص‌کش! امتیازت: {user_score}")
    logger.info(f"امتیاز برای {user}: {user_score}")

# دستور /guess
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    number = random.randint(1, 10)
    await update.message.reply_text(f"{user} کونی! یه عدد بین 1 تا 10 حدس بزن و بفرست!")
    context.user_data["guess_number"] = number
    logger.info(f"بازی حدس برای {user} شروع شد. عدد: {number}")

# دستور /rps
async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    await update.message.reply_text(f"{user} کص‌کش! انتخاب کن: سنگ، کاغذ یا قیچی؟")
    logger.info(f"بازی سنگ کاغذ قیچی برای {user} شروع شد.")

# دستورات ادمین
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه اینو بزنه!")
        return
    if not context.args:
        await update.message.reply_text("کص‌کش! آیدی کاربر رو بده بعدش مدت زمان (ثانیه)!")
        return
    try:
        target_id = int(context.args[0])
        duration = int(context.args[1]) if len(context.args) > 1 else 60
        MUTED_USERS[target_id] = time.time() + duration
        save_data()
        await update.message.reply_text(f"کاربر {target_id} برای {duration} ثانیه میوت شد! کص‌کش دیگه حرف نمی‌زنه!")
        logger.info(f"ادمین {user_id} کاربر {target_id} رو برای {duration} ثانیه میوت کرد.")
    except ValueError:
        await update.message.reply_text("کص‌کش! آیدی و زمان رو درست بده!")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("جنده! فقط ادمین می‌تونه اینو بزنه!")
        return
    if not context.args:
        await update.message.reply_text("کص‌کش! آیدی کاربر رو بده!")
        return
    try:
        target_id = int(context.args[0])
        if target_id in MUTED_USERS:
            del MUTED_USERS[target_id]
            save_data()
            await update.message.reply_text(f"کاربر {target_id} از میوت دراومد! حالا می‌تونه کص بگه!")
            logger.info(f"ادمین {user_id} کاربر {target_id} رو آن‌میوت کرد.")
        else:
            await update.message.reply_text("کونی! این کاربر میوت نبود!")
    except ValueError:
        await update.message.reply_text("کص‌کش! آیدی رو درست بده!")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه بن کنه!")
        return
    if not context.args:
        await update.message.reply_text("جنده! آیدی کاربر رو بده!")
        return
    try:
        target_id = int(context.args[0])
        BANNED_USERS.add(target_id)
        if target_id in MUTED_USERS:
            del MUTED_USERS[target_id]
        save_data()
        await update.message.reply_text(f"کاربر {target_id} بن شد! گمشو دیگه اینجا نیاد!")
        logger.info(f"ادمین {user_id} کاربر {target_id} رو بن کرد.")
    except ValueError:
        await update.message.reply_text("کص‌کش! آیدی رو درست بده!")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کونی! فقط ادمین می‌تونه اینو بزنه!")
        return
    if not context.args:
        await update.message.reply_text("کص‌کش! آیدی کاربر رو بده!")
        return
    try:
        target_id = int(context.args[0])
        if target_id in BANNED_USERS:
            BANNED_USERS.remove(target_id)
            save_data()
            await update.message.reply_text(f"کاربر {target_id} از بن دراومد! حالا می‌تونه برگرده کص بگه!")
            logger.info(f"ادمین {user_id} کاربر {target_id} رو آن‌بان کرد.")
        else:
            await update.message.reply_text("جنده! این کاربر بن نبود!")
    except ValueError:
        await update.message.reply_text("کص‌کش! آیدی رو درست بده!")

async def nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه لقب بده!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("جنده! آیدی و لقب رو بده! مثل: /nickname 123456789 کونی")
        return
    try:
        target_id = int(context.args[0])
        nick = " ".join(context.args[1:])
        NICKNAMES[target_id] = nick
        save_data()
        await update.message.reply_text(f"کاربر {target_id} حالا لقبش '{nick}' شد! حال کن کص‌کش!")
        logger.info(f"ادمین {user_id} به کاربر {target_id} لقب '{nick}' داد.")
    except ValueError:
        await update.message.reply_text("کص‌کش! آیدی رو درست بده!")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه لیست ببینه!")
        return
    msg = "لیست کاربرا:\n"
    msg += f"بن‌شده‌ها: {', '.join(map(str, BANNED_USERS)) or 'هیچ‌کس'}\n"
    msg += f"میوت‌شده‌ها: {', '.join(f'{k} (تا {datetime.fromtimestamp(v).strftime('%H:%M:%S')})' for k, v in MUTED_USERS.items()) or 'هیچ‌کس'}\n"
    msg += f"لقب‌ها: {', '.join(f'{k}: {v}' for k, v in NICKNAMES.items()) or 'هیچ‌کس'}\n"
    msg += f"امتیازات: {', '.join(f'{k}: {v}' for k, v in SCORES.items()) or 'هیچ‌کس'}\n"
    msg += f"هشدارها: {', '.join(f'{k}: {v}' for k, v in WARNINGS.items()) or 'هیچ‌کس'}"
    await update.message.reply_text(msg)
    logger.info(f"ادمین {user_id} لیست کاربرا رو دید.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه پیام همگانی بفرسته!")
        return
    if not context.args:
        await update.message.reply_text("جنده! متن پیام رو بده!")
        return
    message = " ".join(context.args)
    for uid in set(NICKNAMES.keys()) | BANNED_USERS | set(MUTED_USERS.keys()) | set(SCORES.keys()):
        if uid != ADMIN_ID and uid not in BANNED_USERS:
            try:
                await context.bot.send_message(chat_id=uid, text=f"پیام از AKKing:\n{message}")
                await asyncio.sleep(0.1)
            except TelegramError:
                continue
    await update.message.reply_text("پیام همگانی فرستاده شد، کص‌کشا حال کنن!")
    logger.info(f"ادمین {user_id} پیام همگانی فرستاد: {message}")

async def add_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه امتیاز بده!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("جنده! آیدی و مقدار امتیاز رو بده! مثل: /addscore 123456789 10")
        return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        SCORES[target_id] = SCORES.get(target_id, 0) + amount
        save_data()
        await update.message.reply_text(f"به کاربر {target_id} {amount} امتیاز اضافه شد! حال کن کص‌کش!")
        logger.info(f"ادمین {user_id} به کاربر {target_id} {amount} امتیاز داد.")
    except ValueError:
        await update.message.reply_text("کص‌کش! آیدی و مقدار رو درست بده!")

# دستورات جدید
async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    sorted_scores = sorted(SCORES.items(), key=lambda x: x[1], reverse=True)
    user_rank = next((i + 1 for i, (uid, _) in enumerate(sorted_scores) if uid == user_id), None)
    user_score = SCORES.get(user_id, 0)
    await update.message.reply_text(f"{user} کص‌کش! رتبه‌ت: {user_rank or 'نداری'}\nامتیازت: {user_score}")
    logger.info(f"رتبه {user}: {user_rank}")

async def steal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    if not context.args:
        await update.message.reply_text("کص‌کش! آیدی کسی که می‌خوای ازش بدزدی رو بده!")
        return
    try:
        target_id = int(context.args[0])
        if target_id not in SCORES or target_id == user_id:
            await update.message.reply_text("کونی! یا این کاربر نیست، یا خودتی!")
            return
        if random.random() < 0.1:  # 10% شانس موفقیت
            stolen = min(SCORES[target_id], 10)
            SCORES[target_id] -= stolen
            SCORES[user_id] += stolen
            await update.message.reply_text(f"{user} کص‌کش! {stolen} امتیاز از {NICKNAMES.get(target_id, target_id)} دزدیدی!")
        else:
            await update.message.reply_text(f"{user} جنده! نتونستی بدزدی، کیرت سوخت!")
        save_data()
        logger.info(f"{user} سعی کرد از {target_id} بدزده")
    except ValueError:
        await update.message.reply_text("کص‌کش! آیدی رو درست بده!")

async def confess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    confessions = [
        "یه بار تو حموم کیرم رو انقدر مالیدم که آب قطع شد!",
        "دیشب خواب دیدم کص ننم رو گاییدم، حال داد!",
        "به رفیقم گفتم کونشو بخورم، گفت فقط اگه شامم بدی!"
    ]
    confession = random.choice(confessions)
    await update.message.reply_text(f"{user} کونی اعتراف کرد:\n{confession}")
    SCORES[user_id] = SCORES.get(user_id, 0) + 1
    save_data()
    logger.info(f"اعتراف برای {user} فرستادم.")

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    prizes = [
        ("۱۰ امتیاز", 10), ("یه فحش خفن", 0), ("یه چالش", 0)
    ]
    prize, points = random.choice(prizes)
    if prize == "۱۰ امتیاز":
        SCORES[user_id] = SCORES.get(user_id, 0) + points
        msg = f"{user} کص‌کش! چرخ بخت واست {prize} آورد!"
    elif prize == "یه فحش خفن":
        msg = f"{user} کونی! چرخ بخت واست {prize} آورد:\n{random.choice(CURSES)}"
    else:
        msg = f"{user} جنده! چرخ بخت واست {prize} آورد:\nبه رفیقت pm بده بگو کیرم تو دهنت!"
    await update.message.reply_text(msg)
    save_data()
    logger.info(f"چرخ بخت برای {user}: {prize}")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه کیک کنه!")
        return
    if not context.args:
        await update.message.reply_text("جنده! آیدی کاربر رو بده!")
        return
    if update.message.chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("کونی! این دستور فقط تو گروه کار می‌کنه!")
        return
    try:
        target_id = int(context.args[0])
        await context.bot.ban_chat_member(chat_id, target_id)
        await update.message.reply_text(f"کاربر {target_id} از گروه کیک شد! گمشو کص‌کش!")
        logger.info(f"ادمین {user_id} کاربر {target_id} رو از {chat_id} کیک کرد.")
    except (ValueError, TelegramError):
        await update.message.reply_text("کص‌کش! آیدی رو درست بده یا دسترسی ندارم!")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه هشدار بده!")
        return
    if not context.args:
        await update.message.reply_text("جنده! آیدی کاربر رو بده!")
        return
    try:
        target_id = int(context.args[0])
        WARNINGS[target_id] = WARNINGS.get(target_id, 0) + 1
        save_data()
        await update.message.reply_text(f"کاربر {target_id} هشدار گرفت! تعداد هشدارها: {WARNINGS[target_id]}")
        if WARNINGS[target_id] >= 3:
            BANNED_USERS.add(target_id)
            await update.message.reply_text(f"کاربر {target_id} با ۳ هشدار بن شد! گمشو!")
        logger.info(f"ادمین {user_id} به {target_id} هشدار داد.")
    except ValueError:
        await update.message.reply_text("کص‌کش! آیدی رو درست بده!")

async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    loves = [
        "کیرم تو کصت عاشقتم جنده‌ی من!",
        "کونت مثل قلبمه، هر روز می‌خوام بگامش!",
        "عشقم تویی که کصتو هر شب خواب می‌بینم!"
    ]
    love_msg = random.choice(loves)
    await update.message.reply_text(f"{user} کونی:\n{love_msg}")
    SCORES[user_id] = SCORES.get(user_id, 0) + 1
    save_data()
    logger.info(f"پیام عاشقانه برای {user} فرستادم.")

async def muteall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه همه رو میوت کنه!")
        return
    if update.message.chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("کونی! این دستور فقط تو گروه کار می‌کنه!")
        return
    duration = 60  # ۱ دقیقه
    for uid in SCORES.keys():
        if uid != ADMIN_ID and uid not in BANNED_USERS:
            MUTED_USERS[uid] = time.time() + duration
    save_data()
    await update.message.reply_text(f"همه کص‌کشا برای {duration} ثانیه میوت شدن!")
    logger.info(f"ادمین {user_id} همه رو میوت کرد.")

async def coinflip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    if not context.args:
        await update.message.reply_text("کص‌کش! مقدار امتیاز رو بده! مثل: /coinflip 10")
        return
    try:
        amount = int(context.args[0])
        if amount <= 0 or SCORES.get(user_id, 0) < amount:
            await update.message.reply_text("کونی! یا امتیاز نداری یا گوه خوردی!")
            return
        result = random.choice(["شیر", "خط"])
        if random.random() < 0.5:  # 50% شانس برد
            SCORES[user_id] += amount
            await update.message.reply_text(f"{user} کص‌کش! {result} اومد، {amount} امتیاز بردی!")
        else:
            SCORES[user_id] -= amount
            await update.message.reply_text(f"{user} جنده! {result} اومد، {amount} امتیاز باختی!")
        save_data()
        logger.info(f"{user} شرط‌بندی کرد: {amount} - نتیجه: {result}")
    except ValueError:
        await update.message.reply_text("کص‌کش! یه عدد درست بده!")

async def roastme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return
    await update.message.reply_text(f"{user} کونی! آماده باش که حالتو بگیرم:")
    for i in range(3):
        random_roast = random.choice(ROASTS)
        await update.message.reply_text(random_roast)
        await asyncio.sleep(1)
    SCORES[user_id] = SCORES.get(user_id, 0) + 3
    save_data()
    logger.info(f"رگبار حال‌گیری برای {user} فرستادم.")

# دستور /c برای پاک کردن پیام‌های اخیر
async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # چک کردن اینکه فقط ادمین بتونه استفاده کنه
    if user_id != ADMIN_ID:
        await update.message.reply_text("کص‌کش! فقط ادمین می‌تونه پیاما رو پاک کنه!")
        return
    
    # چک کردن اینکه تو گروه باشه
    if update.message.chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("کونی! این دستور فقط تو گروه کار می‌کنه!")
        return

    # گرفتن آیدی پیام فعلی
    message_id = update.message.message_id
    
    # پاک کردن ۱۰۰ پیام آخر (از پیام فعلی به عقب)
    try:
        for msg_id in range(message_id, message_id - 100, -1):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                await asyncio.sleep(0.05)  # یه تاخیر کوچیک برای جلوگیری از اسپم
            except TelegramError:
                continue  # اگه پیام پاک نشد (مثلاً قدیمی باشه)، ردش کن
        await update.message.reply_text("کص‌کشا! ۱۰۰ تا پیام آخر پاک شد!")
        logger.info(f"ادمین {user_id} تو گروه {chat_id} ۱۰۰ پیام رو پاک کرد.")
    except TelegramError as e:
        await update.message.reply_text(f"کص‌کش! یه جای کار گوه شد: {str(e)}")
        logger.error(f"خطا تو پاک کردن پیام‌ها: {str(e)}")

# مدیریت دکمه‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user.first_name
    user_id = query.from_user.id
    if user_id in BANNED_USERS or user_id in MUTED_USERS:
        return

    if query.data == "joke":
        random_joke = random.choice(JOKES_18)
        await query.edit_message_text(f"بخند {user} کونی:\n{random_joke}")
        SCORES[user_id] = SCORES.get(user_id, 0) + 1
        save_data()
        logger.info(f"جوک +18 از دکمه برای {user} فرستادم.")
    elif query.data == "photo":
        photo_url = random.choice(PHOTOS)
        await query.message.reply_photo(photo=photo_url, caption=f"برای {user} جنده!")
        SCORES[user_id] = SCORES.get(user_id, 0) + 1
        save_data()
        logger.info(f"عکس از دکمه برای {user} فرستادم.")
    elif query.data == "curse":
        random_curse = random.choice(CURSES)
        await query.edit_message_text(f"بگیر {user} کص‌کش:\n{random_curse}")
        SCORES[user_id] = SCORES.get(user_id, 0) + 1
        save_data()
        logger.info(f"فحش از دکمه برای {user} فرستادم.")
    elif query.data == "roast":
        random_roast = random.choice(ROASTS)
        await query.edit_message_text(f"حال کن {user}:\n{random_roast}")
        SCORES[user_id] = SCORES.get(user_id, 0) + 1
        save_data()
        logger.info(f"حال‌گیری از دکمه برای {user} فرستادم.")
    elif query.data == "creator":
        await query.edit_message_text(f"منو {CREATOR} ساخته، {user} کونی!")
        logger.info(f"سازنده از دکمه به {user} نشون داده شد.")
    elif query.data == "dice":
        await query.message.reply_dice()
        await asyncio.sleep(3)
        await query.message.reply_text(f"{user} کص‌کش! تاس انداختی، حالا چی؟")
        SCORES[user_id] = SCORES.get(user_id, 0) + 1
        save_data()
        logger.info(f"تاس از دکمه برای {user} فرستادم.")
    elif query.data == "coin":
        result = random.choice(["شیر", "خط"])
        await query.edit_message_text(f"{user} کونی! نتیجه شیر یا خط: {result}")
        SCORES[user_id] = SCORES.get(user_id, 0) + 1
        save_data()
        logger.info(f"شیر یا خط از دکمه برای {user}: {result}")
    elif query.data == "time":
        current_time = datetime.now().strftime("%H:%M:%S - %Y/%m/%d")
        await query.edit_message_text(f"{user} کونی! ساعت الان: {current_time}")
        logger.info(f"ساعت از دکمه برای {user} فرستادم.")
    elif query.data == "roll":
        result = random.randint(1, 100)
        await query.edit_message_text(f"{user} کص‌کش! عدد رندوم (1-100): {result}")
        SCORES[user_id] = SCORES.get(user_id, 0) + 1
        save_data()
        logger.info(f"رندوم عدد از دکمه برای {user}: {result}")
    elif query.data == "score":
        user_score = SCORES.get(user_id, 0)
        await query.edit_message_text(f"{user} کص‌کش! امتیازت: {user_score}")
        logger.info(f"امتیاز از دکمه برای {user}: {user_score}")
    elif query.data == "guess":
        number = random.randint(1, 10)
        await query.edit_message_text(f"{user} کونی! یه عدد بین 1 تا 10 حدس بزن و بفرست!")
        context.user_data["guess_number"] = number
        logger.info(f"بازی حدس از دکمه برای {user} شروع شد. عدد: {number}")
    elif query.data == "rps":
        await query.edit_message_text(f"{user} کص‌کش! انتخاب کن: سنگ، کاغذ یا قیچی؟")
        logger.info(f"بازی سنگ کاغذ قیچی از دکمه برای {user} شروع شد.")

# تابع پیام تاخیری
async def delayed_message(chat_id, text, delay, context):
    await asyncio.sleep(delay)
    await context.bot.send_message(chat_id=chat_id, text=text)

# مدیریت پیام‌ها (اصلاح‌شده)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()  # متن پیام رو به حروف کوچیک تبدیل می‌کنه
    user = update.message.from_user.first_name
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    load_data()

    # چک کردن بن یا میوت بودن کاربر
    if user_id in BANNED_USERS:
        await update.message.reply_text("کص‌کش! بن شدی، گمشو!")
        return
    if user_id in MUTED_USERS:
        if time.time() > MUTED_USERS[user_id]:
            del MUTED_USERS[user_id]
            save_data()
        else:
            return

    nick = NICKNAMES.get(user_id, user)
    SCORES.setdefault(user_id, 0)

    # جواب دادن فقط به کلمات خاص یا بازی‌ها
    if text in RESPONSES:  # اگه پیام تو دیکشنری RESPONSES باشه
        await update.message.reply_text(RESPONSES[text])
        SCORES[user_id] += 1
        save_data()
        logger.info(f"جواب سفارشی '{text}' برای {nick} فرستادم.")
    elif text in ["عکس", "photo", "pic"]:
        photo_url = random.choice(PHOTOS)
        await update.message.reply_photo(photo=photo_url, caption=f"برای {nick} کص‌کش!")
        SCORES[user_id] += 1
        save_data()
        logger.info(f"عکس برای {nick} فرستادم.")
    elif text in ["جوک", "joke"]:
        random_joke = random.choice(JOKES_18)
        await update.message.reply_text(random_joke)  # فقط جوک رو می‌فرسته
        SCORES[user_id] += 1
        save_data()
        logger.info(f"جوک سریع برای {nick} فرستادم.")
    elif text in ["فحش بده", "curse"]:
        random_curse = random.choice(CURSES)
        await update.message.reply_text(random_curse)  # فقط فحش رو می‌فرسته
        SCORES[user_id] += 1
        save_data()
        logger.info(f"فحش سریع برای {nick} فرستادم.")
    elif text in ["حال‌گیری", "roast"]:
        random_roast = random.choice(ROASTS)
        await update.message.reply_text(random_roast)  # فقط حال‌گیری رو می‌فرسته
        SCORES[user_id] += 1
        save_data()
        logger.info(f"حال‌گیری سریع برای {nick} فرستادم.")
    elif text == "داستان":
        story = f"یه شب {nick} کص‌کش اومد پیشم گفت 'بیا کون بدیم'، گفتم 'کیرم آماده‌ست!' یهو کاندوم پاره شد، گفت 'حالا چی؟' گفتم 'بیا با گوه هم حال کنیم!' تا صبح فقط خندیدیم و کص‌خوری کردیم!"
        await update.message.reply_text(story)
        SCORES[user_id] += 2
        save_data()
        logger.info(f"داستان +18 برای {nick} فرستادم.")
    elif text == "سورپرایز":
        await update.message.reply_text(f"صبر کن {nick} کونی، یه چیز خفن می‌فرستم!")
        await delayed_message(chat_id, random.choice(CURSES), 3, context)
        SCORES[user_id] += 1
        save_data()
        logger.info(f"سورپرایز با تاخیر برای {nick} فرستادم.")
    elif text in ["تاس", "dice"]:
        await update.message.reply_dice()
        SCORES[user_id] += 1
        save_data()
        logger.info(f"تاس سریع برای {nick} فرستادم.")
    elif text in ["شیر یا خط", "coin"]:
        result = random.choice(["شیر", "خط"])
        await update.message.reply_text(result)  # فقط نتیجه رو می‌فرسته
        SCORES[user_id] += 1
        save_data()
        logger.info(f"شیر یا خط سریع برای {nick}: {result}")
    elif text in ["ساعت", "time"]:
        current_time = datetime.now().strftime("%H:%M:%S - %Y/%m/%d")
        await update.message.reply_text(current_time)  # فقط ساعت رو می‌فرسته
        logger.info(f"ساعت سریع برای {nick} فرستادم.")
    elif text in ["رندوم", "roll"]:
        result = random.randint(1, 100)
        await update.message.reply_text(str(result))  # فقط عدد رو می‌فرسته
        SCORES[user_id] += 1
        save_data()
        logger.info(f"رندوم عدد سریع برای {nick}: {result}")
    elif "guess_number" in context.user_data:  # مدیریت بازی حدس
        try:
            guess = int(text)
            number = context.user_data["guess_number"]
            if guess == number:
                await update.message.reply_text(f"آفرین! درست حدس زدی! عدد {number} بود!")
                SCORES[user_id] += 5
                del context.user_data["guess_number"]
            elif guess < number:
                await update.message.reply_text("عدد بزرگ‌تره، دوباره حدس بزن!")
            else:
                await update.message.reply_text("عدد کوچک‌تره، دوباره حدس بزن!")
            save_data()
            logger.info(f"{nick} حدس زد: {guess} (عدد: {number})")
        except ValueError:
            await update.message.reply_text("یه عدد درست بگو!")
    elif text in ["سنگ", "کاغذ", "قیچی"]:  # مدیریت سنگ کاغذ قیچی
        bot_choice = random.choice(["سنگ", "کاغذ", "قیچی"])
        if text == bot_choice:
            result = "مساوی شد!"
        elif (text == "سنگ" and bot_choice == "قیچی") or (text == "کاغذ" and bot_choice == "سنگ") or (text == "قیچی" and bot_choice == "کاغذ"):
            result = "بردی! کیرم تو شانس تو!"
            SCORES[user_id] += 3
        else:
            result = "باختی!"
        await update.message.reply_text(f"من: {bot_choice}\n{result}")
        save_data()
        logger.info(f"بازی rps برای {nick}: کاربر {text}، بات {bot_choice}، نتیجه {result}")
    # اگه هیچ‌کدوم از موارد بالا نبود، بات چیزی نمی‌گه

# مدیریت خطاها
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"خطا: {context.error}")
    await update.message.reply_text("کص‌کش! یه جای کار گوه شده، صبر کن دوباره بگو!")

# تابع اصلی
def main():
    app = Application.builder().token(TOKEN).concurrent_updates(True).read_timeout(10).write_timeout(10).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("joke", joke))
    app.add_handler(CommandHandler("photo", photo))
    app.add_handler(CommandHandler("curse", curse))
    app.add_handler(CommandHandler("roast", roast))
    app.add_handler(CommandHandler("creator", creator))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("coin", coin))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("time", get_time))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("guess", guess))
    app.add_handler(CommandHandler("rps", rps))
    # دستورات ادمین
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("nickname", nickname))
    app.add_handler(CommandHandler("listusers", list_users))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("addscore", add_score))
    # دستورات جدید
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CommandHandler("steal", steal))
    app.add_handler(CommandHandler("confess", confess))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("love", love))
    app.add_handler(CommandHandler("muteall", muteall))
    app.add_handler(CommandHandler("coinflip", coinflip))
    app.add_handler(CommandHandler("roastme", roastme))
    app.add_handler(CommandHandler("c", clear_chat))  # دستور جدید برای پاک کردن پیام‌ها

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    app.add_error_handler(error)

    logger.info("🍆🔥 بات +18 AKKing استارت خورد! پشماتو آماده کن که کص‌کشا رو بترکونم! 🔥🍆")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()