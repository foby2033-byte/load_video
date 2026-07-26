import asyncio
import logging
import os
import re

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

# =====================
# НАСТРОЙКИ
# =====================

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
# СКАЧИВАНИЕ ЧЕРЕЗ API (Без блокировок YouTube)
# =====================


async def download_via_cobalt(url: str, output_path: str) -> bool:
    """Скачивает видео с YouTube/Instagram/TikTok через обходной API."""
    api_url = "https://co.wuk.sh/api/json"  # Публичный инстанс Cobalt
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "vQuality": "720",  # Качество 720p оптимально для влезания в 50МБ
    }

    async with aiohttp.ClientSession() as session:
        # 1. Запрашиваем прямую ссылку на файл у API
        async with session.post(
            api_url, json=payload, headers=headers
        ) as response:
            if response.status != 200:
                return False
            data = await response.json()
            video_url = data.get("url")

        if not video_url:
            return False

        # 2. Скачиваем сам файл по полученной прямой ссылке
        async with session.get(video_url) as file_response:
            if file_response.status == 200:
                with open(output_path, "wb") as f:
                    while chunk := await file_response.content.read(1024 * 1024):
                        f.write(chunk)
                return True
    return False


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
# ОБРАБОТЧИК ССЫЛОК
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

    # Уникальное имя файла
    file_path = os.path.join(DOWNLOAD_DIR, f"{message.message_id}.mp4")

    try:
        # Пробуем скачать через Cobalt API
        success = await download_via_cobalt(url, file_path)

        if not success or not os.path.exists(file_path):
            await status.edit_text(
                "❌ Не удалось скачать видео (YouTube заблокировал доступ или ссылка недействительна)."
            )
            return

        size = os.path.getsize(file_path)

        if size > MAX_FILE_SIZE:
            await status.edit_text(
                "❌ Видео больше 49 МБ.\nTelegram не позволяет отправлять такие файлы."
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
        logging.error(f"Download Error: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        await status.edit_text(f"❌ Ошибка:\n\n{str(e)[:1000]}")


# =====================
# ЗАПУСК
# =====================


async def main():
    print("BOT ONLINE")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
