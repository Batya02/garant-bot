from objects.globals import dp
from db_models.User import User

from datetime import datetime as dt

from aiogram.types import (
        Message, ReplyKeyboardMarkup,
        KeyboardButton
        )

from objects import globals

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

    buttons = ReplyKeyboardMarkup(
        resize_keyboard=True, 
        keyboard=[
            [
                KeyboardButton(text="👤Мой профиль"), 
                KeyboardButton(text="🔍Найти пользователя"), 
                KeyboardButton(text="📁Активные сделки")
                ]
        ]
    ) 
    
    await message.answer(
        text=f"🤖Приветствую! Я бот.", 
        reply_markup=buttons
    )