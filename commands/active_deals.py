from objects.globals import dp
from objects import globals

from aiogram.types import (
        Message, InlineKeyboardMarkup, 
        InlineKeyboardButton
        )

@dp.message_handler(lambda message: message.text == "📁Активные сделки")
async def activate_deals(message: Message):
    globals.state_type = "" #Reset state type
    
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Покупки", callback_data="active_shops"), 
             InlineKeyboardButton(text="Продажи", callback_data="active_sales")]
        ]
    )

    await message.answer(
        text="Выберите тип сделок", 
        reply_markup=buttons
    )