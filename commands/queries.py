from typing import Dict
from aiogram.types import (
        CallbackQuery, InlineKeyboardMarkup, 
        Message,       InlineKeyboardButton
        )
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from objects.globals import dp, bot
from db_models.Shops_and_Sales import SAS

from datetime import datetime as dt

class Mem(StatesGroup):
    get_amount_balance_func = State()
    set_deal_amount = State()
    main_user = State()
    not_main_user = State()

@dp.callback_query_handler(lambda query: query.data.startswith(("get-money")))
async def get_money(query: CallbackQuery):
    variants = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text="50", callback_data="value-money_50"), 
             InlineKeyboardButton(text="100", callback_data="value-money_100")], 
            [InlineKeyboardButton(text="150", callback_data="value-money_150"), 
             InlineKeyboardButton(text="200", callback_data="value-money_200")]
        ]
    )

    await bot.send_message(
        query.from_user.id, 
        text="Введите сумму для пополнения или выберите варианты", 
        reply_markup=variants
    )

    await Mem.get_amount_balance_func.set()

@dp.callback_query_handler(lambda query: query.data.startswith(("value-money")))
async def value_money(query: CallbackQuery):
    pass

@dp.callback_query_handler(lambda query: query.data.startswith(("create-deal")))
async def start_deal(query: CallbackQuery, state: FSMContext):

    await bot.send_message(
        query.from_user.id, 
        text="Введите сумму сделки:"
    )

    await state.update_data(main_user=query.from_user.id)
    await state.update_data(not_main_user=query.data.split("_")[1])

    await Mem.set_deal_amount.set()

@dp.callback_query_handler(lambda query: query.data == "active_shops")
async def active_shops(query: CallbackQuery):
    shops = await SAS.objects.filter(main_user=query.from_user.id, ended=0).all()

    if shops == []:
        return await bot.send_message(
            query.from_user.id, 
            text="У вас нет активных покупок!"
        )

    for shop in shops:
        date = dt.strftime(shop.created, "%Y-%m-%d %H:%M:%S")
        type = "Сделка" if shop.type == "deal" else "Unknow"
        globals()[f"{shop.id}"] = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Завершить", callback_data=f"off-deal_{shop.id}")]
                ]
        )

        await bot.send_message(
            query.from_user.id, 
            text=f"ID: <code>{shop.id}</code>\n"
            f"Покупатель: <code>{shop.main_user}</code>\n"
            f"Дата создания: {date}\n"
            f"Сумма: {shop.price}\n"
            f"Продавец: <code>{shop.not_main_user}</code>\n"
            f"Тип: {type}",
            reply_markup=globals()[f"{shop.id}"]
        )

    await bot.send_message(
        query.from_user.id, 
        text=f"У вас активных покупок: {len(shops)}"
    )

@dp.callback_query_handler(lambda query: query.data.startswith(("active_sales")))
async def active_sales(query: CallbackQuery):
    sales = await SAS.objects.filter(not_main_user=query.from_user.id, ended=0).all()

    for sale in sales:
        date = dt.strftime(sale.created, "%Y-%m-%d %H:%M:%S")
        type = "Сделка" if sale.type == "deal" else "Unknow"
        await bot.send_message(
            query.from_user.id, 
            text=f"ID: <code>{sale.id}</code>\n"
            f"Покупатель: <code>{sale.main_user}</code>\n"
            f"Дата создания: {date}\n"
            f"Сумма: {sale.price}\n"
            f"Продавец: <code>{sale.not_main_user}</code>\n"
            f"Тип: {type}"
        )

    if sales == []:
        return await bot.send_message(
            query.from_user.id, 
            text="У вас нет активных продаж!"
        )

    await bot.send_message(
        query.from_user.id, 
        text=f"У вас активных продаж: {len(sales)}"
    )

@dp.message_handler(state=Mem.get_amount_balance_func)
async def get_amount_balance(message: Message, state: FSMContext):
    pass

@dp.message_handler(state=Mem.set_deal_amount)
async def set_deal_amount(message: Message, state: FSMContext):
    data:dict = await state.get_data()
    main_user = data["main_user"]
    not_main_user = data["not_main_user"]
    
    try:
        price = float(message.text)
    except ValueError:
        return await message.answer(
            text="Пример правильного формата суммы: 10; 10.0"
        )
    
    await SAS.objects.create(
            main_user=main_user, 
            created=dt.now(), 
            price=price,
            not_main_user=not_main_user, 
            type="deal", 
            ended="False"
    )

    await message.answer(text="Сделка успешно создана!")

    await state.finish()

@dp.callback_query_handler(lambda query: query.data.startswith(("off-deal")))
async def off_deal(query: CallbackQuery): 
    update_data = await SAS.objects.get(id=int(query.data.split("_")[1]))
    await update_data.update(ended=True)
    
    await bot.edit_message_text(
            chat_id = query.message.chat.id, 
            message_id = query.message.message_id, 
            text = "Сделка завершена!"
            )