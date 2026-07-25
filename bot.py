import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

import yt_dlp


# ВСТАВЬТЕ НОВЫЙ ТОКЕН ОТ @BotFather
TOKEN = "ВАШ_ТОКЕН"


DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "✅ Бот работает!\n\n"
        "Отправьте ссылку YouTube или Instagram."
    )


@dp.message()
async def download_video(message: Message):

    url = message.text

    if not url or not url.startswith("http"):
        await message.answer(
            "❌ Отправьте ссылку на видео"
        )
        return


    await message.answer(
        "⏳ Скачиваю видео..."
    )


    try:

        options = {
            "format": "best",
            "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
            "noplaylist": True,

            # Для Instagram нужен cookies.txt
            "cookiefile": "cookies.txt",
        }


        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(info)


        if os.path.exists(filename):

            await message.answer(
                "📤 Отправляю видео..."
            )


            await message.answer_video(
                FSInputFile(filename),
                caption="✅ Готово"
            )


            os.remove(filename)


        else:

            await message.answer(
                "❌ Видео не найдено"
            )


    except Exception as e:

        print("ERROR:", e)

        await message.answer(
            "❌ Ошибка:\n\n" + str(e)[:1000]
        )


async def main():

    print("BOT ONLINE")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
