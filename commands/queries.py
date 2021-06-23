from typing import Dict
from asyncio import sleep
from aiogram.types import (
        CallbackQuery, InlineKeyboardMarkup, 
        Message,       InlineKeyboardButton
        )
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from objects.globals import dp, bot, payment_services, config
from db_models.User import User
from db_models.Shops_and_Sales import SAS

from datetime import datetime as dt
from datetime import timedelta

from telegram_bot_pagination import InlineKeyboardPaginator
from formats.dateTime import datetime_format

from payment_services.QIWI import p2p_wallet

class Mem(StatesGroup):
    get_amount_balance_func = State()
    set_deal_amount = State()
    main_user = State()
    not_main_user = State()

@dp.callback_query_handler(lambda query: query.data == "select-payment-service")
async def select_payment_service(query: CallbackQuery):
    payments_services_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button, callback_data=f"service_{button}") for button in payment_services]
        ]
    )

    return await bot.edit_message_text(
        chat_id=query.message.chat.id, 
        message_id = query.message.message_id, 
        text="Выберите платежную систему", 
        reply_markup=payments_services_markup)

@dp.callback_query_handler(lambda query: query.data.startswith(("service")))
async def get_money(query: CallbackQuery):
    """
    variants = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text="50", callback_data="value-money_50"), 
             InlineKeyboardButton(text="100", callback_data="value-money_100")], 
            [InlineKeyboardButton(text="150", callback_data="value-money_150"), 
             InlineKeyboardButton(text="200", callback_data="value-money_200")], 
            [InlineKeyboardButton(text="Другое значение", callback_data="other_value")],
            [InlineKeyboardButton(text="Назад", callback_data="back_menu")]
        ]
    )
    """
    global SERVICE
    SERVICE = query.data.split("_")[1]

    await bot.edit_message_text(
        chat_id=query.message.chat.id, 
        message_id = query.message.message_id, 
        text="Введите сумму для пополнения:"
        )

    await Mem.get_amount_balance_func.set()

@dp.callback_query_handler(lambda query: query.data.startswith(("value-money")))
async def value_money(query: CallbackQuery):pass

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

    return await bot.send_message(
        query.from_user.id, 
        text=f"У вас активных покупок: {len(shops)}"
    )

@dp.callback_query_handler(lambda query: query.data.startswith(("active_sales")))
async def active_sales(query: CallbackQuery):
    sales = await SAS.objects.filter(not_main_user=query.from_user.id, ended=0).all()

    if sales == []:
        return await bot.send_message(
            query.from_user.id, 
            text="У вас нет активных продаж!"
        )

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

    return await bot.send_message(
        query.from_user.id, 
        text=f"У вас активных продаж: {len(sales)}"
    )

@dp.message_handler(state=Mem.get_amount_balance_func)
async def get_amount_balance(message: Message, state: FSMContext):
    await state.finish()
    if not message.text.isdigit():
        return await message.answer(text="Вводимое значение должно быть числом!")

    sum:float = float(message.text)

    if SERVICE == "Qiwi":
        res = p2p_wallet.create_invoice(value=sum, expirationDateTime=datetime_format(dt.now()+timedelta(hours=6)))
        continue_button_payment = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Продолжить", url=res["payUrl"])]
            ]
        )
        await message.answer(
            "Нажмите на кнопку для продолжения оплаты!", 
            reply_markup=continue_button_payment
        )
        billId = res["billId"]
        while True:
            status = p2p_wallet.invoice_status(bill_id=billId)
            if status["status"]["value"] == "WAITING":pass
            elif status["status"]["value"] == "PAID":
                update_balance = await User.objects.get(user_id=message.from_user.id)
                new_balance_value = float(update_balance.balance) + sum
                await update_balance.update(balance=new_balance_value)
                await message.answer(f"Ваш баланс успешно пополнен на {sum}₽")
                break
            await sleep(5)
            
    elif SERVICE == "Yoomoney":pass

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
    await update_data.update(uncreated=dt.now(), ended=True)
    
    await bot.edit_message_text(
            chat_id = query.message.chat.id, 
            message_id = query.message.message_id, 
            text = "Сделка завершена!"
            )

@dp.callback_query_handler(lambda query: query.data == "off#deals")
async def off_deals(query: CallbackQuery):
    all_deals = await SAS.objects.filter(main_user=query.from_user.id, ended=True).all()
    
    if all_deals == []:
        return await bot.send_message(
            query.from_user.id, 
            text="Завершенные сделки отсутствуют!"
        )

    first_deal = all_deals[0]
    created = datetime_format(first_deal.created)
    uncreated = datetime_format(first_deal.uncreated)
    type = "Сделка" if first_deal.type == "deal" else "Unknow"
    
    global COUNT_DEALS
    COUNT_DEALS = len(all_deals)

    paginator = InlineKeyboardPaginator(
        COUNT_DEALS, 
        current_page=1, 
        data_pattern="page_deal#{page}"
    )

    return await bot.send_message(
        query.from_user.id, 
        text=f"Завершенная сделка\n\n"
        f"ID: {first_deal.id}\n"
        f"Покупатель: <code>{first_deal.main_user}</code>\n"
        f"Дата и время создания: {created}\n"
        f"Дата и время завершения: {uncreated}\n"
        f"Сумма: <code>{first_deal.price}</code>\n"
        f"Продавец: <code>{first_deal.not_main_user}</code>\n"
        f"Тип: <i>{type}</i>", 
        reply_markup=paginator.markup
    )

@dp.callback_query_handler(lambda query: query.data.startswith(("page_deal")))
async def page_deal(query: CallbackQuery):
    
    deal_data = await SAS.objects.get(id=int(query.data.split("#")[1]))
    created = datetime_format(deal_data.created)
    uncreated = datetime_format(deal_data.uncreated)
    type = "Сделка" if deal_data.type == "deal" else "Unknow"

    paginator = InlineKeyboardPaginator(
        COUNT_DEALS, 
        current_page=int(query.data.split("#")[1]), 
        data_pattern="page_deal#{page}"
    )

    return await bot.edit_message_text(
        chat_id=query.message.chat.id, 
        message_id = query.message.message_id, 
        text=f"Завершенная сделка\n\n"
        f"ID: {deal_data.id}\n"
        f"Покупатель: <code>{deal_data.main_user}</code>\n"
        f"Дата и время создания: {created}\n"
        f"Дата и время завершения: {uncreated}\n"
        f"Сумма: <code>{deal_data.price}</code>\n"
        f"Продавец: <code>{deal_data.not_main_user}</code>\n"
        f"Тип: <i>{type}</i>",
        reply_markup=paginator.markup
    )

@dp.callback_query_handler(lambda query: query.data == "back_menu")
async def back(query: CallbackQuery):

    payments_services_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button, callback_data=f"service_{button}") for button in payment_services]
        ]
    )

    return await bot.edit_message_text(
        chat_id=query.message.chat.id, 
        message_id = query.message.message_id, 
        text="Выберите платежную систему", 
        reply_markup=payments_services_markup
        )