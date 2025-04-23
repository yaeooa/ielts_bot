from aiogram.fsm.state import State, StatesGroup

class StatesGroup(StatesGroup):
    selecting_book = State()
    selecting_test = State()
    selecting_part = State()
    answering_questions = State()
    waiting_for_response = State()
    asking_ielts = State()  # Состояние для вопросов об IELTS 