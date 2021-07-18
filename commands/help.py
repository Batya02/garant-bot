from objects.globals import dp

from aiogram.types import (
        Message, InlineKeyboardMarkup, 
        InlineKeyboardButton)

from objects.globals import config

@dp.message_handler(lambda message: message.text == "❓Помощь")
async def help(message: Message):

    admin_url:str = r"https://t.me/%s" % config["admin_username"]

    admin_markup = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text="Спросить админа", url=admin_url)]
        ]
    )

    with open(r"temp/help.txt", mode="r", encoding="utf-8") as load_help_text:
        help_text = load_help_text.read()

    return await message.answer(
        text=help_text, 
        reply_markup=admin_markup
        )