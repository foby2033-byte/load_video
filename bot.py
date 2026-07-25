import os
import re
import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest

import yt_dlp


# =========================
# CONFIG
# =========================

BOT_TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 63888386

DOWNLOAD_DIR = "downloads"

os.makedirs(
    DOWNLOAD_DIR,
    exist_ok=True
)


# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# =========================
# BOT
# =========================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()



# =========================
# WEB SERVER
# =========================

async def home(request):
    return web.Response(
        text="Bot is alive"
    )



# =========================
# DOWNLOAD
# =========================

def download_video(url):

    cookies = os.path.join(
        os.getcwd(),
        "cookies.txt"
    )


    ydl_opts = {

        # для Instagram лучше best
        "format":
        "bestvideo+bestaudio/best",


        "outtmpl":
        f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",


        "merge_output_format":
        "mp4",


        "noplaylist":
        True,


        "quiet":
        False,


        "no_warnings":
        False,


        "retries":
        10,


        "fragment_retries":
        10,


        "socket_timeout":
        60,


        "http_headers": {

            "User-Agent":
            (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "Chrome/120 Safari/537.36"
            )

        },


        "extractor_args": {

            "youtube": {

                "player_client":
                [
                    "android",
                    "web"
                ]

            },

            "instagram": {

                "api_hostname":
                "www.instagram.com"

            }

        }

    }



    # cookies для Instagram / YouTube
    if os.path.exists(cookies):

        logging.info(
            "cookies.txt найден"
        )

        ydl_opts["cookiefile"] = cookies

    else:

        logging.warning(
            "cookies.txt отсутствует"
        )



    with yt_dlp.YoutubeDL(ydl_opts) as ydl:


        info = ydl.extract_info(
            url,
            download=True
        )


        filename = ydl.prepare_filename(
            info
        )


        filename = (
            os.path.splitext(filename)[0]
            +
            ".mp4"
        )


        if not os.path.exists(filename):

            raise Exception(
                "Файл не создан"
            )


        return filename



# =========================
# START
# =========================

@dp.message(
    Command("start")
)
async def start(
    message: types.Message
):

    if message.from_user.id != OWNER_ID:
        return


    await message.answer(
        "🤖 Бот работает\n\n"
        "Отправь ссылку на видео"
    )



# =========================
# MESSAGE
# =========================

@dp.message()
async def handler(
    message: types.Message
):

    if message.from_user.id != OWNER_ID:
        return


    if not message.text:
        return


    links = re.findall(
        r"https?://\S+",
        message.text
    )


    if not links:

        await message.answer(
            "❌ Нет ссылки"
        )

        return



    url = links[0]

    # убрать параметры ?igsh=
    url = url.split("?")[0]


    status = await message.answer(
        "⏳ Скачиваю..."
    )


    file_path = None


    try:


        loop = asyncio.get_running_loop()


        file_path = await loop.run_in_executor(
            None,
            download_video,
            url
        )


        size = os.path.getsize(
            file_path
        )


        # ограничение Telegram
        if size > 50 * 1024 * 1024:

            await status.edit_text(
                "❌ Файл больше 50 МБ"
            )

            return



        await status.edit_text(
            "📤 Отправляю..."
        )


        await message.answer_video(
            video=FSInputFile(
                file_path
            ),
            caption="✅ Готово"
        )


        try:

            await status.delete()

        except TelegramBadRequest:

            pass



    except Exception as e:


        logging.exception(e)


        await status.edit_text(
            "❌ Ошибка:\n"
            +
            str(e)[:500]
        )



    finally:


        if file_path and os.path.exists(file_path):

            os.remove(
                file_path
            )



# =========================
# MAIN
# =========================

async def main():


    app = web.Application()


    app.router.add_get(
        "/",
        home
    )


    runner = web.AppRunner(
        app
    )


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


    logging.info(
        "BOT STARTED"
    )


    await dp.start_polling(
        bot
    )



if __name__ == "__main__":

    asyncio.run(
        main()
    )
