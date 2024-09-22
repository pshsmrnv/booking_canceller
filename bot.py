import logging
import asyncio
import pandas as pd
import joblib

from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware

HELP_COMMAND = '''
/start - начать работу
/help - список команд
'''

from config import API_TOKEN

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
button_start = KeyboardButton("/start")
button_help = KeyboardButton("/help")
current_index = 0 # Индекс текущей строки в данных

# Создаем reply-кнопки

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard= True)
    button1 = KeyboardButton("Профиль отеля")
    button2 = KeyboardButton("Статистика по отелю")
    keyboard.add(button1, button2)
    return keyboard

def get_reply_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard= True)
    button1 = KeyboardButton("Подтвердить бронирование")
    button2 = KeyboardButton("Посмотреть дополнительную информацию")
    button3 = KeyboardButton("Отменить бронирование")
    keyboard.add(button1, button2, button3)
    return keyboard

def get_reply_keyboard_without_dopinfo():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard= True)
    button1 = KeyboardButton("Подтвердить бронирование")
    button3 = KeyboardButton("Отменить бронирование")
    keyboard.add(button1,  button3)
    return keyboard

def get_second_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard= True)
    button_call_client = KeyboardButton("Позвонить клиенту")
    button_main_menu = KeyboardButton("В главное меню")
    keyboard.add(button_call_client, button_main_menu)
    return keyboard
def get_third_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard= True)
    button_main_menu = KeyboardButton("В главное меню")
    keyboard.add(button_main_menu)
    return keyboard

def get_full_stat():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard= True)
    button_main_menu = KeyboardButton("В главное меню")
    button_graph = KeyboardButton("Графики")
    button_dop1 = KeyboardButton("доп1")
    button_dop2 = KeyboardButton("доп2")

    keyboard.add(button_main_menu, button_graph, button_dop1, button_dop2)
    return keyboard




@dp.message_handler(lambda message: message.text == "Профиль отеля")
async def process_profile(message: types.Message):
    await message.reply("Гостиница: Космос, тут холод и тьма, в костинице космос сходят сума",reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "Статистика по отелю")
async def process_statistics(message: types.Message):
    await message.reply("Статистика по отелю: 75% бронирований, 20% отменено, 5% не подтверждено", reply_markup=get_full_stat())

@dp.message_handler(lambda message: message.text == "Графики")
async def process_statistics(message: types.Message):
    await message.reply("Подробная информация в графиках:", reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "доп1")
async def process_statistics(message: types.Message):
    await message.reply("Дополнительная информация 1", reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "доп2")
async def process_statistics(message: types.Message):
    await message.reply("Дополнительная информация 2", reply_markup=get_main_menu())


@dp.message_handler(lambda message: message.text == "Подтвердить бронирование")
async def process_booking_confirm(message: types.Message):
    await message.reply("Бронирование для пользователя подтверждено", reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "Посмотреть дополнительную информацию")
async def process_view_info(message: types.Message):
    await message.reply("Здесь выводится информация об бронировании, номер телефона, сколько было у пользователя броней и т.д.", reply_markup=get_reply_keyboard_without_dopinfo())

@dp.message_handler(lambda message: message.text == "Отменить бронирование")
async def process_booking_cancel(message: types.Message):
    await message.reply("Бронирование для пользователя отменено", reply_markup=get_second_menu())

@dp.message_handler(lambda message: message.text == "Позвонить клиенту")
async def process_call_client(message: types.Message):
    await message.reply("Пожалуйста, свяжитесь с клиентом по телефону.", reply_markup=get_third_menu())

@dp.message_handler(lambda message: message.text == "В главное меню")
async def process_main_menu(message: types.Message):
    await message.reply("Вы вернулись в главное меню.", reply_markup=get_reply_keyboard())

def get_next_row():
    data = pd.read_csv('data.csv')
    global current_index
    if current_index < len(data):
        row = data.iloc[current_index].values.reshape(1, -1)
        current_index += 1
        return row
    else:
        return None  # или другое значение, если строки закончились

async def model_predict(row):
    loaded_model = joblib.load('random_forest_model.pkl')
    prediction = loaded_model.predict_proba(row)[:, 1][0].round(2)
    return f"Предсказание об отмене брони: {prediction}"

async def new_booking(user_id):
    while True:
        try:
            row = get_next_row()
            if row is not None:
                prediction = await model_predict(row)
                await bot.send_message(user_id, f"Поступила новая бронь: {prediction}", reply_markup=get_reply_keyboard())
            else:
                logging.info("Строки закончились.")
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения: {e}")
        await asyncio.sleep(30)  # Задержка в 3 минуты (180 секунд)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await bot.send_message(chat_id = message.from_user.id ,text = "Бот отслеживания бронирования запущен. Вы будете получать сообщения о бронировании.", reply_markup=get_main_menu(), parse_mode='HTML')
    asyncio.create_task(new_booking(message.from_user.id))

# Обработчик команды /help
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.reply(text=HELP_COMMAND)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
