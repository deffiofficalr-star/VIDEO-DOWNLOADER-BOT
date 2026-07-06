import os
import re
import shutil
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import yt_dlp

BOT_TOKEN = "ВАШ_ТОКЕН_ТУТА"

ADMIN_IDS = [
    5413018519,
]

REQUIRED_CHANNELS = [
    "@bytefps",
]

DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def escape_markdown(text):
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for ch in chars:
        text = text.replace(ch, f'\\{ch}')
    return text

async def check_subscription(user_id, context):
    if not REQUIRED_CHANNELS:
        return True
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

async def get_subscription_keyboard():
    keyboard = []
    for channel in REQUIRED_CHANNELS:
        keyboard.append([InlineKeyboardButton(f"📢 Подписаться на {channel}", url=f"https://t.me/{channel[1:]}")])
    keyboard.append([InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")])
    return InlineKeyboardMarkup(keyboard)

async def main_menu(user_id=None):
    keyboard = [
        [InlineKeyboardButton("📥 Скачать видео", callback_data="download")],
        [InlineKeyboardButton("📖 Помощь", callback_data="help")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("⭐ Поддержать", callback_data="donate")],
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🛠 Админ-панель", callback_data="admin")])
    return InlineKeyboardMarkup(keyboard)

async def admin_menu():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Добавить канал", callback_data="admin_add_channel")],
        [InlineKeyboardButton("🗑️ Удалить канал", callback_data="admin_remove_channel")],
        [InlineKeyboardButton("📋 Список каналов", callback_data="admin_list_channels")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")],
    ])
    return keyboard

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Гость"
    username = escape_markdown(username)

    if not await check_subscription(user_id, context):
        text = (
            f"🌟 Добро пожаловать, {username}! 🌟\n\n"
            "🎬 Я — Video Downloader Bot\n"
            "Я умею скачивать видео с YouTube, TikTok, Instagram, Twitter/X и многих других сайтов.\n\n"
            "⚠️ Для использования бота подпишись на наши каналы ниже:\n"
            "После подписки нажми кнопку «Проверить подписку»."
        )
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=await get_subscription_keyboard()
        )
        return

    text = (
        f"🌟 Привет, {username}! 🌟\n\n"
        "🎬 Я — Video Downloader Bot\n\n"
        "📥 Как я работаю:\n"
        "• Просто отправь мне ссылку на видео\n"
        "• Я скачаю его в максимальном качестве\n"
        "• И пришлю тебе готовое видео\n\n"
        "🌐 Поддерживаемые платформы:\n"
        "YouTube • TikTok • Instagram • Twitter/X • Vimeo • Facebook • Twitch • Reddit и ещё 1000+ сайтов\n\n"
        "👇 Выбери действие в меню ниже:"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=await main_menu(user_id)
    )

async def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data != "check_sub" and not await check_subscription(user_id, context):
        await query.edit_message_text(
            text="⚠️ Требуется подписка!\n\nПодпишись на каналы ниже и нажми «Проверить подписку»:",
            parse_mode="Markdown",
            reply_markup=await get_subscription_keyboard()
        )
        return

    if query.data == "check_sub":
        if await check_subscription(user_id, context):
            await query.edit_message_text(
                text="✅ Спасибо за подписку!\n\nТеперь ты можешь пользоваться ботом.\n\n👇 Выбери действие:",
                parse_mode="Markdown",
                reply_markup=await main_menu(user_id)
            )
        else:
            await query.answer("❌ Ты ещё не подписан на все каналы!", show_alert=True)

    elif query.data == "back_to_menu":
        text = (
            "👇 Главное меню\n\n"
            "Выбери действие:"
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=await main_menu(user_id)
        )

    elif query.data == "download":
        text = (
            "📥 Отправь мне ссылку на видео!\n\n"
            "🔗 Поддерживаются:\n"
            "• YouTube\n"
            "• TikTok\n"
            "• Instagram\n"
            "• Twitter / X\n"
            "• Vimeo\n"
            "• Facebook\n"
            "• Twitch\n"
            "• Reddit\n"
            "• И 1000+ других сайтов\n\n"
            "💡 Просто вставь ссылку в чат и отправь."
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")]])
        )

    elif query.data == "help":
        text = (
            "📖 Как пользоваться ботом:\n\n"
            "1️⃣ Скопируй ссылку на видео с YouTube, TikTok, Instagram или другого сайта.\n"
            "2️⃣ Отправь ссылку в этот чат.\n"
            "3️⃣ Дождись скачивания — я покажу информацию о видео.\n"
            "4️⃣ Получи видео — я пришлю его тебе в отличном качестве.\n\n"
            "⚡ Совет: Для YouTube можно отправлять ссылки на плейлисты — я скачаю все видео!\n\n"
            "🔗 Поддерживаемые сайты:\n"
            "YouTube, TikTok, Instagram, Twitter/X, Vimeo, Facebook, Twitch, Reddit, VK, Rutube и ещё 1000+.\n\n"
            "❓ Есть вопросы? Пиши @bytefps"
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")]])
        )

    elif query.data == "profile":
        user = await context.bot.get_chat(user_id)
        name = escape_markdown(user.first_name or "—")
        username = escape_markdown(user.username or "—")
        text = (
            f"👤 Твой профиль\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"📛 Имя: {name}\n"
            f"🔹 Юзернейм: @{username}\n\n"
            f"📥 Скачано видео: {context.user_data.get('downloads', 0)}\n"
            f"📊 Всего скачиваний ботом: {context.bot_data.get('total_downloads', 0)}\n\n"
            f"💬 Статус: Активен ✅"
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")]])
        )

    elif query.data == "donate":
        text = (
            "⭐ Поддержать проект ⭐\n\n"
            "Если тебе нравится мой бот и ты хочешь помочь его развитию,\n"
            "ты можешь поддержать меня финансово.\n\n"
            "💳 BTC: `bc1q...`\n"
            "💳 USDT (TRC20): `T...`\n"
            "💳 ETH: `0x...`\n\n"
            "🙏 Спасибо за поддержку! ❤️"
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")]])
        )

    elif query.data == "admin":
        if user_id not in ADMIN_IDS:
            await query.answer("⛔ У тебя нет доступа к админ-панели!", show_alert=True)
            return
        text = (
            "🛠 Админ-панель\n\n"
            "Здесь ты можешь управлять настройками бота.\n\n"
            "👇 Выбери действие:"
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=await admin_menu()
        )

    elif query.data == "admin_add_channel":
        if user_id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён!", show_alert=True)
            return
        text = (
            "📢 Добавить обязательный канал\n\n"
            "Отправь мне название канала в формате:\n"
            "`@channel_name`\n\n"
            "❗ Важно: Бот должен быть администратором канала."
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в админ-панель", callback_data="back_to_admin")]])
        )
        context.user_data['admin_action'] = 'add_channel'

    elif query.data == "admin_remove_channel":
        if user_id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён!", show_alert=True)
            return
        if not REQUIRED_CHANNELS:
            await query.answer("📭 Список каналов пуст!", show_alert=True)
            return
        keyboard = []
        for ch in REQUIRED_CHANNELS:
            keyboard.append([InlineKeyboardButton(f"🗑️ {ch}", callback_data=f"remove_ch_{ch}")])
        keyboard.append([InlineKeyboardButton("◀️ Назад в админ-панель", callback_data="back_to_admin")])
        text = (
            "🗑️ Удалить канал\n\n"
            "Выбери канал, который нужно удалить из обязательных:"
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("remove_ch_"):
        if user_id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён!", show_alert=True)
            return
        channel = query.data.replace("remove_ch_", "")
        if channel in REQUIRED_CHANNELS:
            REQUIRED_CHANNELS.remove(channel)
            await query.answer(f"✅ Канал {channel} удалён!", show_alert=True)
            text = (
                f"🗑️ Канал {channel} удалён!\n\n"
                "Теперь подписка на этот канал не обязательна."
            )
            await query.edit_message_text(
                text=text,
                parse_mode="Markdown",
                reply_markup=await admin_menu()
            )

    elif query.data == "admin_list_channels":
        if user_id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён!", show_alert=True)
            return
        if not REQUIRED_CHANNELS:
            text = "📭 Список обязательных каналов пуст"
        else:
            text = "📋 Обязательные каналы:\n\n" + "\n".join([f"• {ch}" for ch in REQUIRED_CHANNELS])
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в админ-панель", callback_data="back_to_admin")]])
        )

    elif query.data == "admin_stats":
        if user_id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён!", show_alert=True)
            return
        text = (
            f"📊 Статистика бота\n\n"
            f"📢 Обязательных каналов: {len(REQUIRED_CHANNELS)}\n"
            f"👥 Админов: {len(ADMIN_IDS)}\n"
            f"📥 Всего скачиваний: {context.bot_data.get('total_downloads', 0)}\n"
            f"🕐 Время работы: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"✅ Бот работает стабильно"
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в админ-панель", callback_data="back_to_admin")]])
        )

    elif query.data == "back_to_admin":
        text = (
            "🛠 Админ-панель\n\n"
            "Выбери действие:"
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=await admin_menu()
        )

async def handle_url(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    url = update.message.text.strip()

    if context.user_data.get('admin_action') == 'add_channel':
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("⛔ У тебя нет доступа!")
            return

        channel = url.strip()
        if not channel.startswith('@'):
            await update.message.reply_text(
                "❌ Неверный формат!\n\n"
                "Канал должен начинаться с @\n"
                "Пример: @bytefps",
                parse_mode="Markdown"
            )
            return

        if channel in REQUIRED_CHANNELS:
            await update.message.reply_text(
                f"ℹ️ Канал {channel} уже есть в списке!",
                parse_mode="Markdown"
            )
            return

        REQUIRED_CHANNELS.append(channel)
        context.user_data['admin_action'] = None
        await update.message.reply_text(
            f"✅ Канал {channel} добавлен!\n\n"
            "Теперь подписка на этот канал обязательна.",
            parse_mode="Markdown",
            reply_markup=await admin_menu()
        )
        return

    if not await check_subscription(user_id, context):
        text = (
            "⚠️ Требуется подписка!\n\n"
            "Чтобы пользоваться ботом, подпишись на каналы ниже\n"
            "и нажми «Проверить подписку»:"
        )
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=await get_subscription_keyboard()
        )
        return

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ Пожалуйста, отправь ссылку на видео.", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text(
        "⏳ Получаю информацию о видео...\n\n"
        "🔍 Пожалуйста, подожди немного...",
        parse_mode="Markdown"
    )

    try:
        info = get_video_info(url)
        if info:
            duration_str = f"{info['duration'] // 60}:{info['duration'] % 60:02d}" if info['duration'] else "—"
            title = escape_markdown(info['title'])
            uploader = escape_markdown(info['uploader'])
            text = (
                f"🎬 {title}\n\n"
                f"👤 Автор: {uploader}\n"
                f"⏱ Длительность: {duration_str}\n"
                f"👁 Просмотры: {info['views']:,}\n"
                f"👍 Лайки: {info['likes']:,}\n\n"
                f"⬇️ Начинаю скачивание...\n"
                f"⏳ Это может занять несколько секунд."
            )
            await status_msg.edit_text(text, parse_mode="Markdown")
        else:
            await status_msg.edit_text(
                "⏳ Скачиваю видео...\n\n"
                "⏳ Пожалуйста, подожди...",
                parse_mode="Markdown"
            )

        file_path, title = download_video(url)

        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            log(f"Скачано: {title} ({file_size:.1f} MB)")

            try:
                with open(file_path, "rb") as f:
                    await update.message.reply_video(
                        video=f,
                        caption=f"✅ {title[:50]}\n📦 Размер: {file_size:.1f} MB\n\n🎬 Видео готово! Наслаждайся просмотром! ❤️",
                        parse_mode="Markdown",
                        supports_streaming=True,
                        write_timeout=120,
                        connect_timeout=120,
                        read_timeout=120
                    )
                await status_msg.delete()
                context.user_data['downloads'] = context.user_data.get('downloads', 0) + 1
                context.bot_data['total_downloads'] = context.bot_data.get('total_downloads', 0) + 1

                await update.message.reply_text(
                    text="📋 Что дальше?\n\n"
                         "Ты можешь:\n"
                         "• Отправить ещё одну ссылку\n"
                         "• Вернуться в главное меню\n\n"
                         "👇 Нажми кнопку ниже, чтобы вернуться:",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Вернуться в меню", callback_data="back_to_menu")]])
                )
            except Exception as e:
                await status_msg.edit_text(f"❌ Ошибка отправки: {e}", parse_mode="Markdown")
            finally:
                try:
                    os.remove(file_path)
                except:
                    pass
        else:
            await status_msg.edit_text(
                text="❌ Не удалось скачать видео.\n\n"
                     "🔍 Возможные причины:\n"
                     "• Видео защищено (Private / Age-restricted)\n"
                     "• Ссылка недействительна\n"
                     "• Сайт не поддерживается\n"
                     "• Видео слишком большое\n\n"
                     "💡 Попробуй другую ссылку или напиши @bytefps",
                parse_mode="Markdown"
            )
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}", parse_mode="Markdown")

def get_video_info(url):
    options = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "socket_timeout": 30
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Неизвестно"),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", "Неизвестно"),
                "views": info.get("view_count", 0),
                "likes": info.get("like_count", 0)
            }
    except:
        return None

def download_video(url):
    options = {
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
        "format": "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "socket_timeout": 30,
        "retries": 5,
        "fragment_retries": 5,
        "skip_download": False,
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }],
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if not os.path.exists(filename):
                base = os.path.splitext(filename)[0]
                for ext in [".mp4", ".webm", ".mkv", ".avi", ".mov"]:
                    test_path = base + ext
                    if os.path.exists(test_path):
                        filename = test_path
                        break
            
            if not os.path.exists(filename):
                files = [os.path.join(DOWNLOAD_FOLDER, f) for f in os.listdir(DOWNLOAD_FOLDER)
                        if f.endswith((".mp4", ".webm", ".mkv", ".avi", ".mov"))]
                if files:
                    filename = max(files, key=os.path.getctime)
            
            if os.path.exists(filename):
                return filename, info.get("title", "video")
            return None, None
    except Exception as e:
        log(f"Ошибка скачивания: {e}")
        return None, None

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    log("🚀 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
