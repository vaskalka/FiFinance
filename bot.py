import asyncio
import random
import json
import aiohttp
from contextlib import suppress
import html
import aiofiles
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

import keyboards

# Открываем файл и читаем его содержимое
with open('local.dev.json', 'r') as f:
    auth_data = json.load(f)

# Токен доступа к боту
bot_api_token = auth_data["API_TOKEN"]
# Токен доступа к api парсинга чеков
check_api_token = auth_data["API_CHECK_TOKEN"]

# Экземпляры бота и диспетчера с использованием MemoryStorage
storage = MemoryStorage()
bot = Bot(bot_api_token, parse_mode="HTML")
dp = Dispatcher(storage=storage)

smiles = [
    ["🥑", "Я люблю авокадо!"],
    ["🍓", "Ммм, вкусна!"],
    ["☁️", "Витаю в облаках!"]
]


# Создание состояний для FSM
class PhotoStates(StatesGroup):
    waiting_for_photo = State()


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


@dp.message(Command("калории"))
async def handle_calories(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте фото для обработки.")
    await state.set_state(PhotoStates.waiting_for_photo)


@dp.message(PhotoStates.waiting_for_photo)
async def handle_photo(message: Message, state: FSMContext):
    if message.content_type == ContentType.PHOTO:
        photo = message.photo[-1]
        photo_file_id = photo.file_id

        # Получение файла фотографии
        file = await bot.get_file(photo_file_id)
        file_path = file.file_path
        file_url = f"https://api.telegram.org/file/bot{bot_api_token}/{file_path}"

        # Загрузка фотографии через Telegram API
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                photo_data = await response.read()

            # Отправка фото на указанный API с токеном
            form_data = aiohttp.FormData()
            form_data.add_field('qrfile', photo_data, filename='photo.jpg')
            form_data.add_field('token', check_api_token)

            async with session.post("https://proverkacheka.com/api/v1/check/get", data=form_data) as api_response:
                if api_response.status == 200:
                    api_result = await api_response.text()  # Здесь мы получаем текстовый ответ
                    escaped_result = html.escape(api_result)

                    # Сохраняем ответ API в файл
                    async with aiofiles.open('api_response.txt', 'w') as file:
                        await file.write(api_result)

                    await message.answer(
                        f"Фото получено и обработано: {photo_file_id}\n"
                        f"Ответ API сохранен в файл: api_response.txt"
                    )
                else:
                    error_text = await api_response.text()
                    escaped_error = html.escape(error_text)

                    # Сохраняем ошибку API в файл
                    async with aiofiles.open('api_error.txt', 'w') as file:
                        await file.write(error_text)

                    await message.answer(
                        f"Произошла ошибка при обработке фото. Статус: {api_response.status}\n"
                        f"Ответ API сохранен в файл: api_error.txt"
                    )
        await state.clear()
    else:
        await message.answer("Пожалуйста, отправьте именно фото.")


@dp.message()
async def echo(message: Message, state: FSMContext):
    msg = message.text.lower()

    match msg:
        case "калории":
            await handle_calories(message, state)  # Передаем оба аргумента
        case "ссылки":
            await message.answer("Вот ваши ссылки:", reply_markup=keyboards.links_kb)
        case "спец. кнопки":
            await message.answer("Спец. кнопки", reply_markup=keyboards.spec_kb)
        case "калькулятор":
            await message.answer("Введите выражение:", reply_markup=keyboards.calc_kb())
        case "смайлики":
            await message.answer(f"{smiles[0][0]} <b>{smiles[0][1]}</b>", reply_markup=keyboards.paginator())
        case "назад":
            await message.answer("Вы вернулись назад.", reply_markup=keyboards.main_kb)  # Основная клавиатура
        case _:
            pass  # Другие случаи, которые вы можете обработать по вашему усмотрению


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
