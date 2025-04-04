import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from config import MATERIALS_DIR
from modules.listening import ListeningSection, ListeningStates
from modules.reading import ReadingSection, ReadingStates
from modules.writing import WritingSection, WritingStates
from modules.speaking import SpeakingSection, SpeakingStates

load_dotenv()

# Initialize bot and dispatcher with Redis storage
redis_storage = RedisStorage.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=redis_storage)

# Initialize sections
listening_section = ListeningSection()
reading_section = ReadingSection()
writing_section = WritingSection()
speaking_section = SpeakingSection()

# Keyboards
def get_back_keyboard():
    """Create keyboard with only Back to Main Menu button"""
    keyboard = [[KeyboardButton(text="Back to Main Menu")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎧 Listening"), KeyboardButton(text="📖 Reading")],
        [KeyboardButton(text="✍️ Writing"), KeyboardButton(text="🗣 Speaking")],
        [KeyboardButton(text="📊 My Progress"), KeyboardButton(text="👤 Profile")]
    ],
    resize_keyboard=True
)

book_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="IELTS 14")],
        [KeyboardButton(text="IELTS 15")],
        [KeyboardButton(text="🎲 Random Test")],
        [KeyboardButton(text="Back to Main Menu")]
    ],
    resize_keyboard=True
)

test_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Test 1")],
        [KeyboardButton(text="Test 2")],
        [KeyboardButton(text="Test 3")],
        [KeyboardButton(text="Test 4")],
        [KeyboardButton(text="Back to Main Menu")]
    ],
    resize_keyboard=True
)

# Handlers
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply(
        "Welcome to IELTS Training Bot! 🎓\n"
        "I'll help you prepare for the IELTS exam.\n"
        "Select a section to practice:",
        reply_markup=main_keyboard
    )

@dp.message(F.text == "🎧 Listening")
async def listening_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply("Select a book:", reply_markup=book_keyboard)
    await state.set_state(ListeningStates.selecting_book)

@dp.message(F.text == "Back to Main Menu")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Handle Back to Main Menu button"""
    await state.clear()
    await message.reply("Select a section:", reply_markup=main_keyboard)

@dp.message(ListeningStates.selecting_book)
async def select_listening_book(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await back_to_main_menu(message, state)
        return

    if message.text == "🎲 Random Test":
        import random
        book = random.choice(["IELTS 14", "IELTS 15"])
        test = random.randint(1, 4)
        await state.update_data(
            selected_book=book,
            selected_test=str(test),
            current_part=1,
            all_user_answers={}
        )
        await message.reply(f"Random test selected: {book} - Test {test}", reply_markup=get_back_keyboard())
        await listening_section.send_part(message, state)
        return

    if message.text not in ["IELTS 14", "IELTS 15"]:
        await message.reply("Please select a book from the options")
        return

    await state.update_data(selected_book=message.text)
    await state.set_state(ListeningStates.selecting_test)
    await message.reply("Select a test:", reply_markup=test_keyboard)

@dp.message(ListeningStates.selecting_test)
async def select_listening_test(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await back_to_main_menu(message, state)
        return

    if not message.text.startswith("Test"):
        await message.reply("Please select a test from the options")
        return

    test_number = message.text.split()[1]
    data = await state.get_data()
    await state.update_data(selected_test=test_number, current_part=1, all_user_answers={})
    await message.reply("Processing...", reply_markup=get_back_keyboard())
    await listening_section.send_part(message, state)

@dp.message(ListeningStates.answering_questions)
async def process_listening_answers(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await state.clear()
        await message.reply("Select a section:", reply_markup=main_keyboard)
        return

    should_return = await listening_section.process_answers(message, state)
    if should_return:
        await message.reply("Select a section:", reply_markup=main_keyboard)

@dp.message(F.text == "📖 Reading")
async def reading_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply("Select a book:", reply_markup=book_keyboard)
    await state.set_state(ReadingStates.selecting_book)

@dp.message(ReadingStates.selecting_book)
async def select_reading_book(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await back_to_main_menu(message, state)
        return

    if message.text == "🎲 Random Test":
        import random
        book = random.choice(["IELTS 14", "IELTS 15"])
        test = random.randint(1, 4)
        await state.update_data(
            selected_book=book,
            selected_test=str(test),
            current_part=1,
            all_user_answers={}
        )
        await message.reply(f"Random test selected: {book} - Test {test}", reply_markup=get_back_keyboard())
        await reading_section.send_part(message, state)
        return

    if message.text not in ["IELTS 14", "IELTS 15"]:
        await message.reply("Please select a book from the options")
        return

    await state.update_data(selected_book=message.text)
    await state.set_state(ReadingStates.selecting_test)
    await message.reply("Select a test:", reply_markup=test_keyboard)

@dp.message(ReadingStates.selecting_test)
async def select_reading_test(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await back_to_main_menu(message, state)
        return

    if not message.text.startswith("Test"):
        await message.reply("Please select a test from the options")
        return

    test_number = message.text.split()[1]
    data = await state.get_data()
    await state.update_data(selected_test=test_number, current_part=1, all_user_answers={})
    await message.reply("Processing...", reply_markup=get_back_keyboard())
    await reading_section.send_part(message, state)

@dp.message(ReadingStates.answering_questions)
async def process_reading_answers(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await state.clear()
        await message.reply("Select a section:", reply_markup=main_keyboard)
        return

    should_return = await reading_section.process_answers(message, state)
    if should_return:   
        await message.reply("Select a section:", reply_markup=main_keyboard)

@dp.message(F.text == "✍️ Writing")
async def writing_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply("Select a book:", reply_markup=book_keyboard)
    await state.set_state(WritingStates.selecting_book)

@dp.message(WritingStates.selecting_book)
async def select_writing_book(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await back_to_main_menu(message, state)
        return

    if message.text == "🎲 Random Test":
        import random
        book = random.choice(["IELTS 14", "IELTS 15"])
        test = random.randint(1, 4)
        task = random.randint(1, 2)
        await state.update_data(
            selected_book=book,
            selected_test=str(test),
            selected_task=task
        )
        await message.reply(f"Random test selected: {book} - Test {test} - Task {task}", reply_markup=get_back_keyboard())
        await writing_section.send_task(message, state)
        return

    if message.text not in ["IELTS 14", "IELTS 15"]:
        await message.reply("Please select a book from the options")
        return

    await state.update_data(selected_book=message.text)
    await state.set_state(WritingStates.selecting_test)
    await message.reply("Select a test:", reply_markup=test_keyboard)

@dp.message(WritingStates.selecting_test)
async def select_writing_test(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await back_to_main_menu(message, state)
        return

    if not message.text.startswith("Test"):
        await message.reply("Please select a test from the options")
        return

    test_number = message.text.split()[1]
    await state.update_data(selected_test=test_number)
    await state.set_state(WritingStates.selecting_task)
    
    task_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Task 1")],
            [KeyboardButton(text="Task 2")],
            [KeyboardButton(text="Back to Main Menu")]
        ],
        resize_keyboard=True
    )
    
    await message.reply("Select a task:", reply_markup=task_keyboard)

@dp.message(WritingStates.selecting_task)
async def select_writing_task(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await state.clear()
        await message.reply("Select a section:", reply_markup=main_keyboard)
        return

    if not message.text.startswith("Task"):
        await message.reply("Please select a task from the options")
        return

    task_number = int(message.text.split()[1])
    await state.update_data(selected_task=task_number)
    await writing_section.send_task(message, state)

@dp.message(WritingStates.waiting_for_response)
async def process_writing_response(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await state.clear()
        await message.reply("Select a section:", reply_markup=main_keyboard)
        return

    should_return = await writing_section.process_response(message, state)
    if should_return:
        await message.reply("Select a section:", reply_markup=main_keyboard)

@dp.message(F.text == "🗣 Speaking")
async def speaking_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply("Select a book:", reply_markup=book_keyboard)
    await state.set_state(SpeakingStates.selecting_book)

@dp.message(SpeakingStates.selecting_book)
async def select_speaking_book(message: types.Message, state: FSMContext):
    should_return = await speaking_section.handle_book_selection(message, state)
    if should_return:
        await message.reply("Select a section:", reply_markup=main_keyboard)

@dp.message(SpeakingStates.selecting_test)
async def select_speaking_test(message: types.Message, state: FSMContext):
    should_return = await speaking_section.handle_test_selection(message, state)
    if should_return:
        await message.reply("Select a section:", reply_markup=main_keyboard)

@dp.message(SpeakingStates.selecting_part)
async def select_speaking_part(message: types.Message, state: FSMContext):
    should_return = await speaking_section.handle_part_selection(message, state)
    if should_return:
        await message.reply("Select a section:", reply_markup=main_keyboard)

@dp.message(SpeakingStates.answering_question)
async def process_speaking_answer(message: types.Message, state: FSMContext):
    should_return = await speaking_section.process_response(message, state)
    if should_return:
        await message.reply("Select a section:", reply_markup=main_keyboard)

@dp.message(SpeakingStates.waiting_for_response)
async def process_speaking_response(message: types.Message, state: FSMContext):
    should_return = await speaking_section.process_response(message, state)
    if should_return:
        await message.reply("Select a section:", reply_markup=main_keyboard)

@dp.message(F.text == "📊 My Progress")
async def progress_handler(message: types.Message):
    await message.reply("🚧 Progress tracking is under development and will be available soon!")

@dp.message(F.text == "👤 Profile")
async def profile_handler(message: types.Message):
    await message.reply("🚧 Profile management is under development and will be available soon!")

async def main():
    print(f"Checking materials path: {MATERIALS_DIR}")
    print(f"Path exists: {os.path.exists(MATERIALS_DIR)}")
    print(f"Directory contents: {os.listdir(MATERIALS_DIR) if os.path.exists(MATERIALS_DIR) else 'directory not found'}")
    
    # Start polling with skip_updates=False to process missed messages
    await dp.start_polling(bot, skip_updates=False)

if __name__ == "__main__":
    asyncio.run(main())
