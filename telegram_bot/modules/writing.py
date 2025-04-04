import os
from aiogram import types
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import MATERIALS_DIR
import httpx
from dotenv import load_dotenv
import openai

load_dotenv()

class WritingStates(StatesGroup):
    selecting_book = State()
    selecting_test = State()
    selecting_task = State()
    waiting_for_response = State()

class WritingSection:
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = "openai/gpt-4o-mini"
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.tasks = {
            1: "Task 1",
            2: "Task 2"
        }

    async def start_section(self, message: types.Message, state: FSMContext):
        """Start Writing section"""
        await state.clear()  # Clear state at start
        await state.set_state(WritingStates.selecting_book)

    def _find_correct_path(self, base_path: str, filename: str) -> str:
        """Находит правильный путь к файлу, учитывая возможные пробелы в директориях"""
        # Разбиваем базовый путь на части
        parts = base_path.split(os.sep)
        
        # Создаем все возможные варианты пути
        possible_paths = []
        
        # Вариант 1: оригинальный путь
        possible_paths.append(os.path.join(base_path, filename))
        
        # Вариант 2: добавляем пробел после каждой части пути
        for i in range(len(parts)):
            temp_parts = parts.copy()
            temp_parts[i] = temp_parts[i] + " "
            possible_paths.append(os.path.join(*temp_parts, filename))
        
        # Вариант 3: добавляем пробел после Writing
        if "Writing" in parts:
            writing_index = parts.index("Writing")
            temp_parts = parts.copy()
            temp_parts[writing_index] = "Writing "
            possible_paths.append(os.path.join(*temp_parts, filename))
        
        # Вариант 4: добавляем пробел после test
        if "test" in parts:
            test_index = parts.index("test")
            temp_parts = parts.copy()
            temp_parts[test_index] = "test "
            possible_paths.append(os.path.join(*temp_parts, filename))
        
        # Вариант 5: добавляем пробел после номера теста
        for i, part in enumerate(parts):
            if part.isdigit() and i + 1 < len(parts) and parts[i + 1] == "test":
                temp_parts = parts.copy()
                temp_parts[i] = part + " "
                possible_paths.append(os.path.join(*temp_parts, filename))
        
        # Вариант 6: добавляем пробел после "test" и номера
        for i, part in enumerate(parts):
            if part == "test" and i > 0 and parts[i - 1].isdigit():
                temp_parts = parts.copy()
                temp_parts[i] = "test "
                possible_paths.append(os.path.join(*temp_parts, filename))
        
        # Вариант 7: добавляем пробел в конце каждой директории
        for i in range(len(parts)):
            temp_parts = parts.copy()
            temp_parts[i] = temp_parts[i].rstrip() + " "
            possible_paths.append(os.path.join(*temp_parts, filename))
        
        # Вариант 8: добавляем пробел в конце Writing
        if "Writing" in parts:
            writing_index = parts.index("Writing")
            temp_parts = parts.copy()
            temp_parts[writing_index] = "Writing "
            possible_paths.append(os.path.join(*temp_parts, filename))
        
        # Вариант 9: специальный случай для "test "
        for i, part in enumerate(parts):
            if part == "test":
                temp_parts = parts.copy()
                temp_parts[i] = "test "
                possible_paths.append(os.path.join(*temp_parts, filename))
        
        # Проверяем каждый вариант
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found correct path: {path}")
                return path
        
        # Если ни один путь не найден, выводим все проверенные пути
        print("Debug - All checked paths:")
        for path in possible_paths:
            print(f"- {path}")
        
        # Возвращаем первый вариант
        return possible_paths[0]

    async def send_task(self, message: types.Message, state: FSMContext):
        """Send writing task"""
        data = await state.get_data()
        book = data['selected_book'].strip()
        test_number = data['selected_test'].strip()
        task_number = data['selected_task']
        
        # Создаем базовый путь
        base_path = os.path.join(MATERIALS_DIR, book, f"{test_number} test", "Writing")
        
        try:
            # Находим правильный путь к изображению
            image_filename = f"writing-test{test_number}-task{task_number}-1.png"
            image_path = self._find_correct_path(base_path, image_filename)
            
            print(f"Debug - image_path: {image_path}")
            print(f"Debug - Image file exists: {os.path.exists(image_path)}")
            
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Находим правильный путь к текстовому файлу
            task_filename = f"writing-test{test_number}-task{task_number}.txt"
            task_path = self._find_correct_path(base_path, task_filename)
            
            if not os.path.exists(task_path):
                raise FileNotFoundError(f"Task file not found: {task_path}")

            with open(task_path, 'r', encoding='utf-8') as f:
                task_text = f.read()

            # Send image with caption
            time_advice = "20 minutes" if task_number == 1 else "40 minutes"
            await message.reply_photo(
                types.FSInputFile(image_path),
                caption=f"📝 Writing Task {task_number}\n\n"
                       f"Time recommendation: {time_advice}\n"
                       f"Total time for both tasks: 60 minutes\n\n"
                       f"Please write your response in the next message."
            )

            # Save task information for prompt
            await state.update_data(
                task_text=task_text
            )
            await state.set_state(WritingStates.waiting_for_response)

        except FileNotFoundError as e:
            print(f"File not found: {e}")
            await message.reply("Sorry, materials for this task are not available yet.")
            await state.clear()
        except Exception as e:
            print(f"Error sending materials: {e}")
            await message.reply("An error occurred while loading materials. Please try another task.")
            await state.clear()

    def get_test_keyboard(self):
        """Create test selection keyboard"""
        keyboard = [
            [KeyboardButton(text="Test 1")],
            [KeyboardButton(text="Test 2")],
            [KeyboardButton(text="Test 3")],
            [KeyboardButton(text="Test 4")],
            [KeyboardButton(text="Back to Main Menu")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    def get_task_keyboard(self):
        """Create task selection keyboard"""
        keyboard = [
            [KeyboardButton(text="Task 1")],
            [KeyboardButton(text="Task 2")],
            [KeyboardButton(text="Back to Main Menu")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    async def handle_test_selection(self, message: types.Message, state: FSMContext):
        """Handle test selection"""
        if message.text == "Back to Main Menu":
            await state.clear()
            return True

        if not message.text.startswith("Test"):
            await message.reply("Please select a test from the options")
            return False

        test_number = message.text.split()[1]
        await state.update_data(selected_test=test_number)
        await state.set_state(WritingStates.selecting_task)
        await message.reply("Select a task:", reply_markup=self.get_task_keyboard())
        return False

    async def handle_task_selection(self, message: types.Message, state: FSMContext):
        """Handle task selection"""
        if message.text == "Back to Main Menu":
            await state.clear()
            return True

        if not message.text.startswith("Task"):
            await message.reply("Please select a task from the options")
            return False

        task_number = int(message.text.split()[1])
        data = await state.get_data()
        test_number = data['selected_test']
        
        # Send task image
        image_path = os.path.join(
            MATERIALS_DIR,
            f"{test_number} test",
            "Writing",
            f"writing-test{test_number}-task{task_number}-1.png"
        )
        
        if not os.path.exists(image_path):
            await message.reply("Sorry, materials for this task are not available yet.")
            return False

        await message.reply_photo(
            types.FSInputFile(image_path),
            caption=f"📝 Writing Task {task_number}\n\n"
                   f"Please write your response in the next message.\n"
                   f"Minimum word count:\n"
                   f"Task 1: 150 words\n"
                   f"Task 2: 250 words"
        )

        # Save task information
        await state.update_data(
            selected_task=task_number,
            task_text=self._load_task_text(test_number, task_number)
        )
        await state.set_state(WritingStates.waiting_for_response)
        return False

    def _load_task_text(self, test_number: str, task_number: int) -> str:
        """Загрузка текста задания из файла"""
        file_path = os.path.join(
            MATERIALS_DIR,
            f"{test_number} test",
            "Writing",
            f"writing-test{test_number}-task{task_number}.txt"
        )
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Ошибка при загрузке текста задания: {e}")
            return ""

    async def process_response(self, message: types.Message, state: FSMContext):
        """Process user response"""
        if message.text == "Back to Main Menu":
            await state.clear()
            return True

        data = await state.get_data()
        task_text = data['task_text']
        student_response = message.text

        # Send checking message
        await message.reply("⏳ Checking your response...")

        try:
            # Get GPT evaluation
            evaluation = await self._get_gpt_evaluation(task_text, student_response)
            
            # Format and send result
            if evaluation:
                await message.reply(evaluation)
            else:
                await message.reply("Sorry, couldn't generate an evaluation. Please try again.")
            
            # Return to task selection
            await state.set_state(WritingStates.selecting_task)
            await message.reply("Select a task:", reply_markup=self.get_task_keyboard())
            return False
            
        except Exception as e:
            print(f"Error in process_response: {e}")
            await message.reply("Sorry, an error occurred while processing your response. Please try again.")
            return False

    async def _get_gpt_evaluation(self, task_text: str, student_response: str) -> str:
        """Get evaluation from GPT via OpenRouter"""
        try:
            # Load prompt from file
            prompt_path = os.path.join(MATERIALS_DIR, "prompts", "writing", "evaluation.txt")
            if not os.path.exists(prompt_path):
                raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            
            # Replace placeholders in prompt
            prompt = prompt.replace("[TASK TEXT HERE]", task_text)
            prompt = prompt.replace("[STUDENT RESPONSE HERE]", student_response)
            
            print(f"Debug - Using model: {self.model}")
            print(f"Debug - API Key: {self.openrouter_api_key[:5]}...")
            
            # Create OpenRouter client
            client = openai.AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/yourusername/ielts_bot",
                    "X-Title": "IELTS Writing Bot"
                }
            )
            
            # Send request
            print("Debug - Sending request to OpenRouter...")
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an IELTS writing examiner."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            print(f"Debug - Response received: {response}")
            
            # Extract evaluation from response
            evaluation = response.choices[0].message.content
            
            print(f"Debug - Raw evaluation: {evaluation}")
            
            # Format evaluation
            formatted_evaluation = self._format_evaluation(evaluation)
            
            if not formatted_evaluation.strip():
                print("Debug - Empty formatted evaluation")
                raise ValueError("Empty evaluation after formatting")
            
            return formatted_evaluation
            
        except FileNotFoundError as e:
            print(f"Error loading prompt: {e}")
            return "Sorry, an error occurred while loading the evaluation template."
        except Exception as e:
            print(f"Error getting GPT evaluation: {e}")
            return f"Sorry, an error occurred while getting the evaluation: {str(e)}"

    def _format_evaluation(self, evaluation: str) -> str:
        """Format evaluation for user display"""
        try:
            # Split evaluation into parts
            parts = evaluation.split('\n')
            formatted_parts = []
            
            # Dictionary for emojis and formatting
            criteria_emojis = {
                "task_achievement": "🎯",
                "coherence_and_cohesion": "🔗",
                "lexical_resource": "📚",
                "grammatical_range_and_accuracy": "✍️"
            }
            
            # Process each part
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Process scores
                if "_score:" in part:
                    criterion = part.split("_score:")[0].strip()
                    score = part.split("_score:")[1].strip()
                    emoji = criteria_emojis.get(criterion, "📝")
                    formatted_parts.append(f"\n{emoji} {criterion.replace('_', ' ').title()}: {score}/9")
                
                # Process comments
                elif "_comment:" in part:
                    criterion = part.split("_comment:")[0].strip()
                    comment = part.split("_comment:")[1].strip()
                    formatted_parts.append(f"💬 {comment}\n")
                
                # Process overall score
                elif "overall_band_score:" in part:
                    score = part.split("overall_band_score:")[1].strip()
                    formatted_parts.append(f"\n\n🏆 Overall Score: {score}/9")
                
                # Process overall comment
                elif "overall_comment:" in part:
                    comment = part.split("overall_comment:")[1].strip()
                    formatted_parts.append(f"\n📝 Overall Comment:\n{comment}")
            
            # Combine all parts
            result = "\n".join(formatted_parts)
            print(f"Debug - Formatted evaluation: {result}")
            return result
            
        except Exception as e:
            print(f"Error formatting evaluation: {e}")
            return "Sorry, an error occurred while formatting the evaluation."

# Не создаем экземпляр здесь
# writing_section = WritingSection() 