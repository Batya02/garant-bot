from aiogram.dispatcher.filters.state import StatesGroup, State

class Mem(StatesGroup):
    main_user               = State()
    not_main_user           = State()
    set_deal_amount         = State()
    get_amount_balance_func = State()

    #Output money states
    get_output_phone_targ = State()
    get_output_phone_var  = State()

    get_output_amount_targ = State()
    get_output_amount_var  = State()

