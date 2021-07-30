from objects.globals import dp, config

from aiogram.types import Message

from db_models.User import User

@dp.message_handler(lambda message: message.text == "📊Статистика")
async def statisctics(message: Message):
    if message.from_user.id == int(config["admin_chat_id"]):
        all_users = await User.objects.all()

        return await message.answer(
            text=f"📊Статистика:\n\n"
            f"Общее количество: {len(all_users)}"
            )