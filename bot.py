import asyncio
import random
import json

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.types import Message

import keyboards

# Открываем файл и читаем его содержимое
with open('local.dev.json', 'r') as f:
    auth_data = json.load(f)

# Токен доступа к боту
bot_api_token = auth_data["API_TOKEN"]

# Экземпляры бота и диспетчера
bot = Bot(bot_api_token, parse_mode="HTML")
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(f"Hello, <b>{message.from_user.first_name}!</b>", reply_markup=keyboards.main_kb)


@dp.message(Command(commands=["rn", "random-number"]))  # /rn 1-100
async def get_random_number(message: Message, command: CommandObject):
    try:
        a, b = [int(n) for n in command.args.split("-")]  # [1, 100]
        rnum = random.randint(a, b)
        # TODO: Расписать Exceptions
        await message.reply(f"Random number: {rnum}")

    except Exception as e:
        await message.reply(f"Ошибка: {e}")


@dp.message(Command("play"))
async def play_games(message: Message):
    await message.answer_dice(DiceEmoji.DICE)


@dp.message()
async def echo(message: Message):
    msg = message.text.lower()

    if msg == "ссылки":
        await message.answer("Вот ваши ссылки:", reply_markup=keyboards.links_kb)
    elif msg == "спец. кнопки":
        await message.answer("Спец. кнопки", reply_markup=keyboards.spec_kb)
    elif msg == "калькулятор":
        await message.answer("Введите выражение:", reply_markup=keyboards.calc_kb())


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
