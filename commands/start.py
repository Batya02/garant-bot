from objects.globals import dp, config
from db_models.User import User

from datetime import datetime as dt

from aiogram.types import (
        Message, ReplyKeyboardMarkup, 
        KeyboardButton
        )

from objects import globals

from keyboards.keyboards import MENU_BUTTONS

@dp.message_handler(commands="start")
async def start(message: Message): 
    globals.state_type = "" #Reset state type

    user_data = await User.objects.filter(user_id=message.from_user.id).all()

    if user_data == []:
        user_id:int = message.from_user.id
        username:str = "None" if message.from_user.username == None else message.from_user.username
        create_time:str = dt.now()
        balance:float = 0.0

        await User.objects.create(
                user_id=user_id, 
                username=username,
                created=create_time, 
                balance=balance) 

    buttons_array = []
    buttons_array.append([KeyboardButton(MENU_BUTTONS[k]) for k in range(len(MENU_BUTTONS)) if k % 2 == 0])
    buttons_array.append([KeyboardButton(MENU_BUTTONS[k]) for k in range(len(MENU_BUTTONS)) if k % 2 != 0])

    if message.from_user.id == int(config["admin_chat_id"]):
        buttons_array.append([KeyboardButton("📊Статистика")])

    buttons = ReplyKeyboardMarkup(
        resize_keyboard=True, 
        keyboard=buttons_array
    ) 
    
    await message.answer(
        text=f"🤖Приветствую! Я бот.", 
        reply_markup=buttons
    )