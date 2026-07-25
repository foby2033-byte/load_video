import os
import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp

# Берем токен из скрытых настроек Hugging Face
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 63888386
DOWNLOAD_DIR = "/tmp/downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def download_video(url: str) -> str:
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android'], 'skip': ['webpage']}}
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
    await message.answer("🤖 Бот успешно перенесен на Hugging Face! Отправьте мне ссылку на YouTube, Pinterest или TikTok.")

@dp.message()
async def handle_message(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    if not message.text:
        return

    urls = re.findall(r'(https?://[^\s]+)', message.text)
    if not urls:
        await message.answer("Пожалуйста, отправьте корректную ссылку.")
        return

    url = urls[0]
    status_msg = await message.answer("⏳ Скачиваю видео, пожалуйста, подождите...")

    try:
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url)

        if file_path and os.path.exists(file_path):
            await status_msg.edit_text("🚀 Загружаю видео в Telegram...")
            await message.answer_video(video=types.FSInputFile(file_path), caption="Готово! 😊")
            os.remove(file_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Не удалось скачать.")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)[:100]}")

async def main():
    print("BOT ONLINE")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
