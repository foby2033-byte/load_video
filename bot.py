import asyncio
import logging
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
import yt_dlp

# =====================
# НАСТРОЙКИ
# =====================

# Бот берет токен из Environment Variables на Render
BOT_TOKEN = os.getenv(
    "BOT_TOKEN", "8973916830:AAHBRwq2X2XrIyJmQagYBFOZdrziW5rOlKo"
)

OWNER_ID = 63888386
DOWNLOAD_DIR = "downloads"
MAX_FILE_SIZE = 49 * 1024 * 1024  # 49 MB

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =====================
# СКАЧИВАНИЕ
# =====================


def download_video(url):
    options = {
        "format": "bestvideo[height<=1080]+bestaudio/best",
        # ИСПРАВЛЕНО: Сохраняем по ID видео, чтобы избежать ошибок со спецсимволами
        "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # ИСПРАВЛЕНО: Использование файла куки для обхода блокировок YouTube/Instagram
        "cookiefile": "cookies.txt",
        # ИСПРАВЛЕНО: Отключаем файлы .part, чтобы избежать [Errno 2] No such file
        "nopart": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        },
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            mp4 = os.path.splitext(filename)[0] + ".mp4"
            if os.path.exists(mp4):
                filename = mp4

        return filename


# =====================
# START
# =====================


@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer(
        "🤖 Бот работает!\n\nОтправьте ссылку на видео:"
    )


# =====================
# ССЫЛКИ
# =====================


@dp.message()
async def download_handler(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    if not message.text:
        return

    links = re.findall(r"https?://\S+", message.text)

    if not links:
        await message.answer("❌ Отправьте ссылку")
        return

    url = links[0]
    status = await message.answer("⏳ Скачиваю видео...")

    try:
        loop = asyncio.get_running_loop()

        file_path = await loop.run_in_executor(None, download_video, url)

        if not os.path.exists(file_path):
            await status.edit_text("❌ Файл не найден")
            return

        size = os.path.getsize(file_path)

        if size > MAX_FILE_SIZE:
            await status.edit_text(
                "❌ Видео больше 49 МБ.\nTelegram не позволяет отправить его."
            )
            os.remove(file_path)
            return

        await status.edit_text("📤 Отправляю видео...")

        await message.answer_video(
            video=FSInputFile(file_path),
            caption="✅ Готово",
            supports_streaming=True,
        )

        os.remove(file_path)
        await status.delete()

    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        await status.edit_text("❌ Ошибка:\n\n" + str(e)[:1000])


# =====================
# ЗАПУСК
# =====================


async def main():
    print("BOT ONLINE")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
