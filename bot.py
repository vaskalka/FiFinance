import asyncio
import random
import json
from contextlib import suppress

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

import keyboards

# Открываем файл и читаем его содержимое
with open('local.dev.json', 'r') as f:
    auth_data = json.load(f)

# Токен доступа к боту
bot_api_token = auth_data["API_TOKEN"]

# Экземпляры бота и диспетчера
bot = Bot(bot_api_token, parse_mode="HTML")
dp = Dispatcher()

smiles = [
    ["🥑", "Я люблю авокадо!"],
    ["🍓", "Ммм, вкусна!"],
    ["☁️", "Витаю в облаках!"]
]

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


@dp.callback_query(keyboards.Pagination.filter(F.action.in_(["prev", "next"])))
async def pagination_handler(call: CallbackQuery, callback_data: keyboards.Pagination):
    page_num = int(callback_data.page)
    page = page_num - 1 if page_num > 1 else 0

    if callback_data.action == "next":
        page = page_num + 1 if page_num < (len(smiles) - 1) else page_num

    with suppress(TelegramBadRequest):
        await call.message.edit_text(
            f"{smiles[page][0]} <b>{smiles[page][1]}</b>",
            reply_markup=keyboards.paginator(page)
        )
    await call.answer("Смотри на текст! ;)", True)


@dp.message()
async def echo(message: Message):
    msg = message.text.lower()

    if msg == "ссылки":
        await message.answer("Вот ваши ссылки:", reply_markup=keyboards.links_kb)
    elif msg == "спец. кнопки":
        await message.answer("Спец. кнопки", reply_markup=keyboards.spec_kb)
    elif msg == "калькулятор":
        await message.answer("Введите выражение:", reply_markup=keyboards.calc_kb())
    elif msg == "смайлики":
        await message.answer(f"{smiles[0][0]} <b>{smiles[0][1]}</b>", reply_markup=keyboards.paginator())


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
