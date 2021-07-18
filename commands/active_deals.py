from objects.globals import dp
from objects import globals

from db_models.Shops_and_Sales import SAS

from aiogram.types import (
        Message, InlineKeyboardMarkup, 
        InlineKeyboardButton
        )

@dp.message_handler(lambda message: message.text == "📁Активные сделки")
async def activate_deals(message: Message):

    all_shops = await SAS.objects.filter(main_user=message.from_user.id, ended=False).all()
    all_sales = await SAS.objects.filter(not_main_user=message.from_user.id, ended=False).all()

    globals.state_type = "" #Reset state type
    
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Покупки({len(all_shops)})", callback_data="active_shops"), 
             InlineKeyboardButton(text=f"Продажи({len(all_sales)})", callback_data="active_sales")]
        ]
    )

    await message.answer(
        text="Выберите тип сделок", 
        reply_markup=buttons
    )