from objects.globals import dp
from objects import globals

from aiogram.types import (
        Message, InlineKeyboardMarkup, 
        InlineKeyboardButton
        )

from db_models.User import User
from db_models.Shops_and_Sales import SAS

@dp.message_handler(lambda message: message.text == "👤Мой профиль")
async def my_profile(message: Message):
    globals.state_type = "" #Reset state type
    
    get_and_send_money = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Пополнить", callback_data=f"get-money")]
            ]
    )

    user_data = await User.objects.filter(user_id=message.from_user.id).all()
    user_data = user_data[0]

    sales = await SAS.objects.filter(seller_id=user_data.user_id).all()
    shops = await SAS.objects.filter(buyer_id=user_data.user_id).all()

    await message.answer(
            f"🗝Ваш ID: <code>{user_data.user_id}</code>\n"
            f"💰Ваш баланс: {user_data.balance}\n\n"
            f"▪️▪️▪️▪️▪️▪️▪️▪\n"
            f"🛒Продажи: {len(sales)} шт\n"
            f"🛒Покупки: {len(shops)} шт\n"
            f"▪️▪️▪️▪️▪️▪️▪️▪️", 
            reply_markup=get_and_send_money
            )