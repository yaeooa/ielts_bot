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
from states import StatesGroup as BotStates
import openai

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
        [KeyboardButton(text="❓ Ask about IELTS"), KeyboardButton(text="💬 Support")]
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

@dp.message(F.text == "💬 Support")
async def support_handler(message: types.Message):
    await message.reply(
        "For support, please contact me directly:\n"
        "👉 @romawriteme\n\n"
        "I'll get back to you as soon as possible!"
    )

@dp.message(F.text == "❓ Ask about IELTS")
async def ask_ielts_handler(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.asking_ielts)
    await message.reply(
        "Ask any question about IELTS format, exam structure, "
        "preparation, or requirements. I'll try to give you a detailed answer!\n\n"
        "You can ask your question in any language - I'll respond in the same language.",
        reply_markup=get_back_keyboard()
    )

@dp.message(BotStates.asking_ielts)
async def process_ielts_question(message: types.Message, state: FSMContext):
    if message.text == "Back to Main Menu":
        await state.clear()
        await message.reply("Select a section:", reply_markup=main_keyboard)
        return

    try:
        # Отправляем уведомление о начале обработки
        processing_msg = await message.reply("⌛️ Processing your question...")

        # Читаем промпт
        prompt_path = os.path.join(MATERIALS_DIR, "prompts", "IELTS_Reference_Prompt.txt")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            reference_prompt = f.read()

        # Создаем клиент OpenAI
        client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Формируем сообщения (без контекста)
        messages = [
            {"role": "system", "content": reference_prompt},
            {"role": "user", "content": message.text}
        ]

        # Отправляем запрос
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )

        # Получаем ответ
        answer = response.choices[0].message.content
        
        # Парсим ответ
        try:
            # Проверяем наличие всех необходимых маркеров
            if "---ANSWER START---" not in answer or "---ANSWER END---" not in answer:
                # Если маркеры не найдены, отправляем ответ как есть с предупреждением
                formatted_response = (
                    "⚠️ Note: The response format was not as expected, but here's the answer:\n\n"
                    f"{answer}"
                )
            else:
                # Извлекаем части ответа
                parts = answer.split("---")
                answer_text = ""
                sources = ""
                language = ""
                
                # Ищем нужные секции
                for i in range(len(parts)):
                    if "ANSWER START" in parts[i]:
                        answer_text = parts[i+1].strip()
                    elif "SOURCES START" in parts[i]:
                        sources = parts[i+1].strip()
                    elif "LANGUAGE START" in parts[i]:
                        language = parts[i+1].strip()
                
                if not answer_text:
                    raise ValueError("No answer text found")
                
                # Форматируем ответ для Telegram
                formatted_response = answer_text.replace("**", "<b>").replace("**", "</b>")  # Заменяем Markdown на HTML
                formatted_response = formatted_response.replace("*", "<i>").replace("*", "</i>")  # Курсив
                
                # Заменяем маркеры списков на эмодзи
                formatted_response = formatted_response.replace("•", "•")
                
                # Добавляем источники, если есть
                if sources:
                    formatted_response += f"\n\n📚 Sources:\n{sources}"
            
            # Создаем инлайн-клавиатуру с кнопкой возврата в главное меню
            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
                ]
            )
            
            # Отправляем ответ пользователю
            await message.reply(
                formatted_response,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
        except Exception as e:
            print(f"Error formatting response: {str(e)}")
            print(f"Raw response: {answer}")
            # Если произошла ошибка, отправляем ответ как есть с предупреждением
            await message.reply(
                f"⚠️ Note: There was an error processing the response format, but here's the answer:\n\n{answer}",
                reply_markup=get_back_keyboard()
            )

        # Удаляем сообщение о обработке
        await processing_msg.delete()

    except Exception as e:
        print(f"Error in process_ielts_question: {str(e)}")
        await message.reply(
            "Sorry, an error occurred while processing your question. "
            "Please try rephrasing your question or ask it later.",
            reply_markup=get_back_keyboard()
        )

@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle main menu callback"""
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)  # Убираем инлайн-клавиатуру
    await callback.message.reply(
        "Welcome to IELTS Training Bot! 🎓\n"
        "I'll help you prepare for the IELTS exam.\n"
        "Select a section to practice:",
        reply_markup=main_keyboard
    )
    await callback.answer()

async def main():
    print(f"Checking materials path: {MATERIALS_DIR}")
    print(f"Path exists: {os.path.exists(MATERIALS_DIR)}")
    print(f"Directory contents: {os.listdir(MATERIALS_DIR) if os.path.exists(MATERIALS_DIR) else 'directory not found'}")
    
    # Start polling with skip_updates=False to process missed messages
    await dp.start_polling(bot, skip_updates=False)

if __name__ == "__main__":
    asyncio.run(main())
