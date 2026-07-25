import os
import re
import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile

import yt_dlp


# ==============================
# CONFIG
# ==============================

BOT_TOKEN = "8973916830:AAHBRwq2X2XrIyJmQagYBFOZdrziW5rOlKo"
OWNER_ID = 63888386

DOWNLOAD_DIR = "/tmp/downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ==============================
# LOGGING
# ==============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ==============================
# BOT INIT
# ==============================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==============================
# WEB SERVER (FOR RENDER)
# ==============================

async def health(request):
    return web.Response(
        text="Bot is running!"
    )


# ==============================
# DOWNLOAD VIDEO
# ==============================
def download_video(url: str) -> str:
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        # Защита от блокировок YouTube (Имитация клиента Android)
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
                'skip': ['webpage']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Android 14; Mobile; rv:128.0) Gecko/128.0 Firefox/128.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.exists(filename):
            filename = os.path.splitext(filename) + '.mp4'
        return filename



# ==============================
# START COMMAND
# ==============================

@dp.message(Command("start"))
async def start(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return


    await message.answer(
        "🤖 Бот запущен!\n\n"
        "Отправь ссылку на видео."
    )



# ==============================
# MESSAGE HANDLER
# ==============================

@dp.message()
async def message_handler(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return


    if not message.text:
        return


    urls = re.findall(
        r"https?://\S+",
        message.text
    )


    if not urls:

        await message.answer(
            "❌ Отправь ссылку на видео"
        )

        return



    url = urls[0]


    status = await message.answer(
        "⏳ Скачиваю видео..."
    )


    file_path = None


    try:

        loop = asyncio.get_running_loop()


        file_path = await loop.run_in_executor(
            None,
            download_video,
            url
        )


        await status.edit_text(
            "📤 Отправляю видео..."
        )


        await message.answer_video(
            video=FSInputFile(file_path),
            caption="✅ Готово!"
        )


        try:
            await status.delete()

        except TelegramBadRequest:
            pass



    except Exception as e:


        logging.exception(e)


        await status.edit_text(
            "❌ Ошибка:\n"
            f"{str(e)[:300]}"
        )



    finally:


        if file_path and os.path.exists(file_path):

            try:
                os.remove(file_path)

            except Exception:
                pass




# ==============================
# MAIN
# ==============================

async def main():

    logging.info(
        "BOT STARTED"
    )


    app = web.Application()

    app.router.add_get(
        "/",
        health
    )


    runner = web.AppRunner(app)

    await runner.setup()


    port = int(
        os.getenv(
            "PORT",
            10000
        )
    )


    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )


    await site.start()


    await dp.start_polling(
        bot
    )



if __name__ == "__main__":

    asyncio.run(
        main()
    )
