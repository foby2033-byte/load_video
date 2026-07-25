import os
import asyncio
import re
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp

# Конфигурация бота
BOT_TOKEN = "8973916830:AAGuCnzVJTibJwMoF_-srCAeh2BZfRG_DGo"
OWNER_ID = 63888386
DOWNLOAD_DIR = "/tmp/downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def handle(request):
    return web.Response(text="Bot is running active!")

def download_video(url: str) -> str:
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.exists(filename):
            filename = os.path.splitext(filename) + '.mp4'
        return filename

@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer("🤖 Бот запущен на сервере! Отправьте мне ссылку на видео, и я скачаю его.")

@dp.message()
async def handle_message(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    if not message.text:
        return

    urls = re.findall(r'(https?://[^\s]+)', message.text)
    if not urls:
        await message.answer("Пожалуйста, отправьте корректную ссылку на видео.")
        return

    url = urls[0]  # Исправлено: берем первую ссылку из списка
    status_msg = await message.answer("⏳ Скачиваю видео, подождите...")

    try:
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url)

        if file_path and os.path.exists(file_path):
            await status_msg.edit_text("🚀 Загружаю видео в Telegram...")
            await message.answer_video(
                video=types.FSInputFile(file_path),
                caption="Держи свое видео! 😊"
            )
            os.remove(file_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Не удалось скачать видео.")
    except Exception as e:
        print(f"DOWNLOAD ERROR: {e}")
        await status_msg.edit_text("❌ Ошибка скачивания. Сервер соцсети заблокировал запрос.")

async def main():
    print("BOT ONLINE")
    app = web.Application()
    app.router.add_get('/', handle)
    asyncio.create_task(dp.start_polling(bot))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
