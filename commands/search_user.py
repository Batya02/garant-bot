from objects.globals import dp
from objects import globals

from aiogram.types import (
        Message, InlineKeyboardMarkup, 
        InlineKeyboardButton
        )

from db_models.User import User
from db_models.Shops_and_Sales import SAS

@dp.message_handler(lambda message: message.text == "🔍Найти пользователя")
async def search_user(message: Message):
    await message.answer(
        text="Введите ID пользователя:"
    )
    globals.state_type = "get_user" #Set state type (get_user)

@dp.message_handler()
async def search_user(message: Message):
    if globals.state_type == "get_user":
        if not message.text.isdigit():
            return await message.answer("ID должен содержать только цифры!")

        get_user = await User.objects.filter(user_id=int(message.text)).all()

        if message.from_user.id == int(message.text):
            return await message.answer(text="Это ваш ID!")
            
        if get_user == []:
            return await message.answer("Пользователь с таким ID не найден!")

        get_user = get_user[0]

        get_user_sales = await SAS.objects.filter(not_main_user=get_user.user_id).all()
        get_user_shops = await SAS.objects.filter(main_user=get_user.user_id).all()

        buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Начать сделку", callback_data=f"create-deal_{get_user.user_id}")]
            ]
        )

        await message.answer(
            text=f"Пользователь (ID): <code>{get_user.user_id}</code>\n\n"
            f"▪️▪️▪️▪️▪️▪️▪️▪\n"
            f"🛒Продажи: {len(get_user_sales)} шт\n"
            f"🛒Покупки: {len(get_user_shops)} шт\n"
            f"▪️▪️▪️▪️▪️▪️▪️▪", 
            reply_markup=buttons
        )

        globals.state_type = ""