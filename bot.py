import asyncio
import json
import logging
import chromadb

import ollama

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = chromadb.Client()
collection = client.create_collection(name="business_info")

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот на связи.")

documents = [
    "Кофейня Coffee Point работает с 9:00 до 21:00, без выходных",
    "Услуги: кофе на вынос, десерты, wi-fi, места для работы",
    "Американо стоит 800 тенге",
    "Капучино стоит 1000 тенге",
    "Латте стоит 1100 тенге",
    "Чизкейк стоит 1500 тенге"
]

def ask_ai(user_message: str) -> str:
    price_words = ["прайс", "цена", "стоимость", "сколько стоит", "меню"]
    hours_words = ["часы", "открыто", "работаете", "закрываетесь"]
    hello_words = ["здравствуйте", "привет", "добрый вечер", "добрый день"]

    if any(word in user_message.lower() for word in price_words + hours_words):
        return load_business_info("business_info.txt")
    if any(word in user_message.lower() for word in hello_words):
        return load_business_info("hello.txt")

    try:
        response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": user_message}])
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Ошибка при обращении к Ollama: {e}")
        return "Извините, сейчас не могу ответить. Попробуйте позже."

def load_business_info(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()  # какой метод читает весь файл целиком?
        return content

collection.add(
    documents = documents,
    ids = ["doc1", "doc2", "doc3", "doc4", "doc5", "doc6"]
)


def search_business_info(query: str) -> str:
    results = collection.query(
        query_texts=[query],
        n_results=1,
        include=["documents", "distances"]
    )

    if results["documents"] and results["documents"][0]:
        distance = results["distances"][0][0]
        print(f"DEBUG: запрос='{query}' | дистанция={distance}")
        if distance < 0.8:
            return results["documents"][0][0]

    return ""

@dp.message()
async def handle_message(message: types.Message):
    reply = ask_ai(message.text)

    logger.info(
        f"Пользователь: {message.from_user.first_name} {message.from_user.last_name} | "
        f"Вопрос: {message.text} | "
        f"Ответ бота: {reply}"
    )

    await message.answer(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())