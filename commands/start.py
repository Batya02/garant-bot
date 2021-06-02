from objects.globals import dp
from aiogram.types import Message
from db_models.User import User

from datetime import datetime as dt

@dp.message_handler(commands="start")
async def start(message: Message):  
    user_data = await User.objects.filter(user_id=message.from_user.id).all()
    if user_data == []:
        user_id:int = message.from_user.id
        username:str = "None" if message.from_user.username == None else message.from_user.username
        create_time:str = dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")
        balance:float = 0.0

        await User.objects.create(
                user_id=user_id, 
                username=username,
                created=create_time, 
                balance=balance)
    else:
        user_data = user_data[0]
        await message.answer(
                f"🗝Ваш ID: {user_data.user_id}\n"
                f"💰Ваш баланс: {user_data.balance}\n\n"
                f"▪️▪️▪️▪️▪️▪️▪️▪\n"
                f"▪️▪️▪️▪️▪️▪️▪️▪️"
        )