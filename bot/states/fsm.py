from aiogram.fsm.state import State, StatesGroup


class AddSupplementStates(StatesGroup):
    waiting_name = State()
    waiting_dose = State()
    waiting_times = State()
    waiting_stock_count = State()
    waiting_reorder_threshold = State()


class UpdateStockStates(StatesGroup):
    waiting_new_count = State()


class TimezoneStates(StatesGroup):
    waiting_custom_tz = State()


class BroadcastStates(StatesGroup):
    waiting_message = State()
