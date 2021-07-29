from typing import Dict
from asyncio import sleep

from aiogram.types import (
        CallbackQuery, InlineKeyboardMarkup, 
        Message,       InlineKeyboardButton
        )
from aiogram.dispatcher.storage import FSMContext

from objects.globals import dp, bot, payment_services, config

from db_models.User import User
from db_models.Shops_and_Sales import SAS
from db_models.OutputApplications import OutputApplication

from datetime import datetime as dt
from datetime import timedelta

from telegram_bot_pagination import InlineKeyboardPaginator

from formats.dateTime import datetime_format
from formats.phone import phone_format

from payment_services.QIWI import p2p_wallet

from states.MEM import Mem

from keyboards.keyboards import MENU_BUTTONS

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
    
    global SERVICE
    SERVICE = query.data.split("_")[1]

    if SERVICE == "Yoomoney":
        return await query.answer(text="Временно недоступен!")

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

    if len(shops) == 0:
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

    if len(sales) == 0:
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
    
    try:
        price = float(message.text)
    except ValueError:
        return await message.answer(
            text="Пример правильного формата суммы: 10; 10.0"
        )

    user_info = await User.objects.get(user_id=message.from_user.id)

    if float(user_info.balance) < float(message.text):
        await state.finish()
        return await message.answer(text="Недостаточно средств на балансе!")

    data:dict = await state.get_data()
    main_user = data["main_user"]
    not_main_user = data["not_main_user"]
    
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
    update_data_deal = await SAS.objects.get(id=int(query.data.split("_")[1]))

    update_data_not_main_user = await User.objects.get(user_id=int(update_data_deal.not_main_user))
    
    reset_deal_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Завершить", callback_data=f"reset-deal_{update_data_deal.id}"
                )
            ]
        ]
    ) 

    await bot.send_message(
        chat_id=update_data_not_main_user.user_id, 
        text=f"ID сделки: <code>{update_data_deal.id}</code>\n"
        f"Получена заявка на завершение сделки.\n"
        f"Завершить сделку?", 
        reply_markup=reset_deal_markup
    )

    await bot.edit_message_text(
            chat_id = query.from_user.id, 
            message_id = query.message.message_id, 
            text = "Отправлена заявка на завершение сделки."
            )
    

@dp.callback_query_handler(lambda query: query.data == "off#deals")
async def off_deals(query: CallbackQuery):

    all_shops = await SAS.objects.filter(main_user=query.from_user.id, ended=True).all()
    all_sales = await SAS.objects.filter(not_main_user=query.from_user.id, ended=True).all()

    type_deal_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Покупки({len(all_shops)})", callback_data="off_shops")], 
            [InlineKeyboardButton(text=f"Продажи({len(all_sales)})", callback_data="off_sales")]
        ]
    )

    return await bot.edit_message_text(
        chat_id=query.from_user.id, 
        message_id=query.message.message_id, 
        text="Выберите тип", 
        reply_markup=type_deal_buttons
    )

@dp.callback_query_handler(lambda query: query.data == "off_shops")
async def all_off_shops(query: CallbackQuery):
    all_shops = await SAS.objects.filter(main_user=query.from_user.id, ended=True).all()

    if len(all_shops) == 0:
        return await bot.edit_message_text(
            chat_id=query.from_user.id, 
            message_id=query.message.message_id, 
            text="У вас отсутствуют завершенные покупки!"
        )

    first_shop = all_shops[0]
    created = datetime_format(first_shop.created)
    uncreated = datetime_format(first_shop.uncreated)
    type = "Сделка" if first_shop.type == "deal" else "Unknow"
    
    global ALL_DEALS
    ALL_DEALS = [id.id for id in all_shops]

    paginator = InlineKeyboardPaginator(
        len(ALL_DEALS), 
        current_page=1, 
        data_pattern="page_deal#{page}"
    )

    return await bot.send_message(
        query.from_user.id, 
        text=f"✅Завершенная сделка\n\n"
        f"📍ID: {first_shop.id}\n"
        f"→Покупатель: <code>{first_shop.main_user}</code>\n"
        f"⏱Создано: <b>{created}</b>\n"
        f"📅Завершено: <b>{uncreated}</b>\n"
        f"💰Сумма: <code>{first_shop.price}</code>\n"
        f"←Продавец: <code>{first_shop.not_main_user}</code>\n"
        f"🗞Тип: <i>{type}</i>", 
        reply_markup=paginator.markup
    )

@dp.callback_query_handler(lambda query: query.data == "off_sales")
async def all_off_sales(query: CallbackQuery):

    all_sales = await SAS.objects.filter(not_main_user=query.from_user.id, ended=True).all()

    if len(all_sales) == 0:
        return await bot.edit_message_text(
            chat_id=query.from_user.id, 
            message_id=query.message.message_id, 
            text="У вас отсутствуют завершенные продажи!"
        )


    first_sale = all_sales[0]
    created = datetime_format(first_sale.created)
    uncreated = datetime_format(first_sale.uncreated)
    type = "Сделка" if first_sale.type == "deal" else "Unknow"
    
    global ALL_DEALS
    ALL_DEALS = [id.id for id in all_sales]

    paginator = InlineKeyboardPaginator(
        len(ALL_DEALS), 
        current_page=1, 
        data_pattern="page_deal#{page}"
    )

    return await bot.send_message(
        query.from_user.id, 
        text=f"✅Завершенная сделка\n\n"
        f"📍ID: {first_sale.id}\n"
        f"→Покупатель: <code>{first_sale.main_user}</code>\n"
        f"⏱Создано: <b>{created}</b>\n"
        f"📅Завершено: <b>{uncreated}</b>\n"
        f"💰Сумма: <code>{first_sale.price}</code>\n"
        f"←Продавец: <code>{first_sale.not_main_user}</code>\n"
        f"🗞Тип: <i>{type}</i>", 
        reply_markup=paginator.markup
    )

@dp.callback_query_handler(lambda query: query.data.startswith(("page_deal")))
async def page_deal(query: CallbackQuery):
    
    deal_data = await SAS.objects.get(id=ALL_DEALS[int(query.data.split("#")[1])-1])
    created = datetime_format(deal_data.created)
    uncreated = datetime_format(deal_data.uncreated)
    type = "Сделка" if deal_data.type == "deal" else "Unknow"

    paginator = InlineKeyboardPaginator(
        len(ALL_DEALS), 
        current_page=int(query.data.split("#")[1]), 
        data_pattern="page_deal#{page}"
    )

    return await bot.edit_message_text(
        chat_id=query.message.chat.id, 
        message_id = query.message.message_id, 
        text=f"✅Завершенная сделка\n\n"
        f"📍ID: {deal_data.id}\n"
        f"→Покупатель: <code>{deal_data.main_user}</code>\n"
        f"⏱Создано: <b>{created}</b>\n"
        f"📅Завершено: <b>{uncreated}</b>\n"
        f"💰Сумма: <code>{deal_data.price}</code>\n"
        f"←Продавец: <code>{deal_data.not_main_user}</code>\n"
        f"🗞Тип: <i>{type}</i>",
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

@dp.callback_query_handler(lambda query: query.data.startswith(("reset-deal")))
async def reset_deal(query: CallbackQuery, state:FSMContext):
    deal_info = await SAS.objects.get(id=int(query.data.split("_")[1]))
    
    update_data_not_main_user = await User.objects.get(user_id=deal_info.main_user)

    new_balance_not_main_user:float = float(update_data_not_main_user.balance) - float(deal_info.price)

    if int(new_balance_not_main_user) < 0:
        return await bot.send_message(
            chat_id=query.from_user.id, 
            text="Недостаточно средств для завершения сделки, нужно пополнить счёт!"
        )

    await update_data_not_main_user.update(balance=new_balance_not_main_user)
    await deal_info.update(uncreated=dt.now(), ended=True)

    update_data_not_main_user = await User.objects.get(user_id=int(deal_info.not_main_user))
    
    new_balance_not_main_user:float = float(update_data_not_main_user.balance) + float(deal_info.price)
    await update_data_not_main_user.update(balance=new_balance_not_main_user)

    user_ids = []
    user_ids.extend((query.from_user.id, deal_info.main_user))

    for i in user_ids:
        await bot.send_message(
            chat_id=i, 
            text="✅Сделка успешно завершена!"
        )

    await state.finish()

@dp.callback_query_handler(lambda query: query.data == "output-money")
async def output_money(query: CallbackQuery):
    await bot.edit_message_text(
        chat_id=query.from_user.id,
        message_id=query.message.message_id, 
        text=f"Отменить -> /reset\n"
        f"❗️Важно: проверьте правильность ввода\n"
        f"Введите номер телефона или номер карты(Qiwi):"
    )

    await Mem.get_output_phone_targ.set()

@dp.message_handler(
    lambda message: message.text not in MENU_BUTTONS,
    state=Mem.get_output_phone_targ
    )
async def output_amount_targ(message: Message, state:FSMContext):
    if message.text == "/reset":
        await state.finish()
        return await message.answer(text="Отмена")

    await state.update_data(get_output_phone_var=phone_format(message.text))

    await message.answer(text=f"Отменить -> /reset\n" f"Введите сумму для вывода:")
    await Mem.get_output_amount_targ.set()

@dp.message_handler(
    lambda message: message.text not in MENU_BUTTONS,
    state=Mem.get_output_amount_targ
    )
async def output_amount_targ(message: Message, state:FSMContext):
    if message.text == "/reset":
        await state.finish()
        return await message.answer(text="Отмена")

    if message.text.replace(".", "").isdigit() or message.text.isdigit():
        await state.update_data(get_output_amount_var=message.text)
      
    user_data = await User.objects.get(user_id=message.from_user.id)

    get_state_data = await state.get_data()

    amount:str = get_state_data["get_output_amount_var"]

    percent:float = float(amount) * config["percent"] / 100

    if int(float(user_data.balance) - (float(amount)+percent)) < 0:
        return await message.answer(
            text=f"🔴Недостаточно средств на балансе!\n"
            f"⚠️Попробуйте ввести другое значение или же отмените операцию с помощью команды /reset")
    
    phone:str  = get_state_data["get_output_phone_var"]
    created:str = dt.strftime(dt.now(), "%Y:%m:%d %H:%M:%S")

    confirm_operation_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm-operation_{message.from_user.id}_{float(amount)+percent}")]
        ]
    )

    await bot.send_message(
        chat_id=config["admin_chat_id"], 
        text=f"🔔Заявка на вывод➡️\n"
        f"Номер телефона: {phone}\n"
        f"Сумма на вывод: {amount}\n"
        f"Дата создания заявки: {created}", 
        reply_markup=confirm_operation_markup
    )

    await message.answer(text="🟢Заявка на вывод успешно создана!")

    await state.finish()

@dp.callback_query_handler(lambda query: query.data.startswith(("confirm-operation")))
async def confirm_operation(query: CallbackQuery):
    get_confirm_data = query.data.split("_")
    get_user_data = await User.objects.get(user_id=get_confirm_data[1])
    
    new_balance = float(get_user_data.balance) - float(get_confirm_data[2])

    await get_user_data.update(balance=new_balance)

    await OutputApplication.objects.create(
        user_id=get_confirm_data[1], 
        amount=float(get_confirm_data[2])
    )

    return await bot.edit_message_text(
        chat_id=query.from_user.id, 
        message_id=query.message.message_id, 
        text="Заявка успешно подтверждена!"
    )