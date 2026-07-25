import os
import asyncio
import random
import requests

from dotenv import load_dotenv
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command


load_dotenv("/home/admin-super/pinterest_bot/.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 63888386

print("TOKEN CHECK:", BOT_TOKEN[:10] if BOT_TOKEN else "EMPTY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def clean_query(text: str) -> str:
    words = [
        "пришли", "мне", "фото", "фотку", "фотографию",
        "картинку", "покажи", "отправь", "найди", "пожалуйста"
    ]
    text = text.lower()
    for w in words:
        text = text.replace(w, "")
    return text.strip()


def get_image(query: str):
    url = "https://www.bing.com/images/search?q=" + requests.utils.quote(query)

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        images = []

        for a in soup.find_all("a"):
            data = a.get("m")
            if not data or "murl" not in data:
                continue

            try:
                img = data.split('"murl":"')[1].split('"')[0]
                img = img.replace("\\/", "/")
                if img.startswith("http"):
                    images.append(img)
            except Exception:
                pass

        if images:
            return random.choice(images)

    except Exception as e:
        print(e)

    return None


@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer(
        "🤖 Бот работает.\n\n"
        "Используйте:\n"
        "@pint коты"
    )


@dp.message()
async def search(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    if not message.text:
        return

    if not message.text.lower().startswith("@pint"):
        return

    query = clean_query(message.text[5:].strip())

    if not query:
        await message.answer("После @pint укажите запрос.")
        return

    image = get_image(query)

    pinterest = (
        "https://www.pinterest.com/search/pins/?q="
        + requests.utils.quote(query)
    )
    if image:
        try:
            img_data = requests.get(
                image,
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
                timeout=10
            ).content

            with open("/tmp/photo.jpg", "wb") as f:
                f.write(img_data)

            await message.answer_photo(
                photo=types.FSInputFile("/tmp/photo.jpg"),
                caption=(
                    f"🔗 Pinterest:\n{pinterest}\n\n"
                    "Я всегда рад вам помочь 😊😊😊"
                )
            )

        except Exception as e:
            print("PHOTO ERROR:", e)

            await message.answer(
                f"🔗 Pinterest:\n{pinterest}\n\n"
                "Я всегда рад вам помочь 😊😊😊"
            )

    else:
        await message.answer(
            f"🔗 Pinterest:\n{pinterest}\n\n"
            "Я всегда рад вам помочь 😊😊😊"
        )
        await message.answer(
            f"🔗 Pinterest:\n{pinterest}\n\n"
            "Я всегда рад вам помочь 😊😊😊"
        )


async def main():
    print("BOT ONLINE")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
