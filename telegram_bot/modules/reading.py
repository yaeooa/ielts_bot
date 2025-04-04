import os
from aiogram import types
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from config import MATERIALS_DIR
from utils.material_loader import MaterialLoader

class ReadingStates(StatesGroup):
    selecting_book = State()
    selecting_test = State()
    answering_questions = State()

class ReadingSection:
    def __init__(self):
        self.material_loader = MaterialLoader()
        self.question_ranges = {
            1: (1, 13),
            2: (14, 26),
            3: (27, 40)
        }

    async def start_section(self, message: types.Message, state: FSMContext):
        """Start Reading section"""
        await state.clear()  # Clear state at start
        await state.set_state(ReadingStates.selecting_book)

    async def handle_test_selection(self, message: types.Message, state: FSMContext):
        """Handle test selection"""
        if message.text == "Back to Main Menu":
            await state.clear()
            return True

        if not message.text.startswith("Test"):
            await message.reply("Please select a test from the options")
            return False

        test_number = message.text.split()[1]
        await state.update_data(selected_test=test_number, current_part=1, all_user_answers={})
        await self.send_part(message, state)
        return False

    async def send_part(self, message: types.Message, state: FSMContext):
        """Send test part"""
        data = await state.get_data()
        book = data['selected_book'].strip()
        test_number = data['selected_test'].strip()
        part_number = data['current_part']
        test_dir = os.path.join(MATERIALS_DIR, book.strip(), f"{test_number.strip()} test".strip(), "Reading").strip()
        
        try:
            # Collect all images for this passage
            image_files = []
            for image_file in sorted(os.listdir(test_dir)):
                if image_file.startswith(f"reading-test{test_number}-passage{part_number}-") and image_file.endswith(".png"):
                    image_path = os.path.join(test_dir, image_file).strip()
                    image_files.append(image_path)

            if not image_files:
                raise FileNotFoundError(f"No images found for passage {part_number}")

            # Send first image with reply
            await message.reply_photo(types.FSInputFile(image_files[0]))

            # Send remaining images without reply
            for image_path in image_files[1:]:
                await message.answer_photo(types.FSInputFile(image_path))

            start_q, end_q = self.question_ranges[part_number]

            await message.reply(
                f"Answer questions {start_q}-{end_q}\n"
                "Send your answers in the format:\n"
                f"{start_q}. answer\n{start_q+1}. answer\n...\n{end_q}. answer"
            )

            # Create and send answer template
            numbers = "\n".join([f"{i}." for i in range(start_q, end_q + 1)])
            template = f"`{numbers}`"
            await message.reply(template, parse_mode="MarkdownV2")

            await state.update_data(
                start_question=start_q,
                end_question=end_q
            )
            await state.set_state(ReadingStates.answering_questions)

        except FileNotFoundError as e:
            print(f"File not found: {e}")
            await message.reply("Sorry, some materials for this test are not available yet.")
            await state.clear()
        except Exception as e:
            print(f"Error sending materials: {e}")
            await message.reply("An error occurred while loading materials. Please try another test.")
            await state.clear()

    async def process_answers(self, message: types.Message, state: FSMContext):
        """Process user answers"""
        if message.text == "Back to Main Menu":
            await state.clear()
            return True

        try:
            data = await state.get_data()
            
            # Проверяем наличие необходимых данных в состоянии
            if 'selected_test' not in data:
                print("Debug - Missing selected_test in state data")
                await message.reply("Please select a test first.")
                await state.set_state(ReadingStates.selecting_test)
                return False
            
            test_number = data['selected_test']
            part_number = data.get('current_part', 1)
            start_q = data.get('start_question', 1)
            end_q = data.get('end_question', 13)
            
            # Get previous user answers and convert all keys to integers
            all_user_answers = {int(k): v for k, v in data.get('all_user_answers', {}).items()}

            # Parse new answers
            new_answers = self._parse_answers(message.text)
            all_user_answers.update(new_answers)

            # Save all answers to state
            await state.update_data(all_user_answers=all_user_answers)

            # Confirm saving
            await message.reply(
                f"✅ Answers for passage {part_number} saved!\n"
                f"Questions {start_q}-{end_q} processed."
            )

            # Check if this is the last part
            if part_number == 3:  # Reading has 3 parts
                await self._check_all_answers(message, state, test_number, all_user_answers)
                await state.clear()  # Clear state after completion
                return True
            else:
                await state.update_data(current_part=part_number + 1)
                await self.send_part(message, state)
                return False
            
        except Exception as e:
            print(f"Error in process_answers: {e}")
            await message.reply("Sorry, an error occurred while processing your answers. Please try again.")
            await state.clear()
            return True

    def _parse_answers(self, text):
        """Parse user answers"""
        answers = {}
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if '.' in line:
                try:
                    parts = line.split('.', 1)
                    num = int(parts[0].strip())
                    ans = parts[1].strip() if len(parts) > 1 else ""
                    if ans:
                        answers[num] = ans
                except:
                    continue
            else:  # Handle answers without dot
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        num = int(parts[0])
                        ans = ' '.join(parts[1:])
                        if ans:
                            answers[num] = ans
                except:
                    continue
        return answers

    async def _check_all_answers(self, message: types.Message, state: FSMContext, test_number: str, all_user_answers: dict):
        """Check all answers and send results"""
        try:
            data = await state.get_data()
            book = data['selected_book'].strip()
            test_number = test_number.strip()
            
            answers_file = os.path.join(
                MATERIALS_DIR,
                book.strip(),
                f"{test_number.strip()} test".strip(),
                "Reading",
                f"answers-reading-test{test_number}.txt"
            ).strip()

            with open(answers_file, 'r', encoding='utf-8') as f:
                correct_answers = {}
                for line in f:
                    if '.' in line:
                        try:
                            num, ans = line.split('.', 1)
                            correct_answers[int(num.strip())] = ans.strip()
                        except:
                            continue

            total_score = 0
            feedback = []
            for q_num in range(1, 41):
                user_ans = all_user_answers.get(q_num, "").lower().strip()
                correct_ans = correct_answers.get(q_num, "").lower().strip()
                
                # Check alternative answers
                correct_alternatives = [ans.strip() for ans in correct_ans.split('/')]
                
                if user_ans and (user_ans in correct_alternatives):
                    total_score += 1
                    feedback.append(f"{q_num}. ✅ Correct")
                elif user_ans:
                    feedback.append(f"{q_num}. ❌ Incorrect (your answer: {user_ans}, correct: {correct_ans})")
                else:
                    feedback.append(f"{q_num}. ❌ No answer (correct: {correct_ans})")

            # Form results message
            result_message = (
                f"🎯 Final Reading test results:\n"
                f"Correct answers: {total_score} out of 40\n"
                f"Your IELTS score: {self.calculate_score(total_score)}\n\n"
                "Detailed feedback:\n" + "\n".join(feedback)
            )

            # Send results
            if len(result_message) > 4000:
                parts = [result_message[i:i+4000] for i in range(0, len(result_message), 4000)]
                for part in parts:
                    await message.reply(part)
            else:
                await message.reply(result_message)

        except Exception as e:
            print(f"Error checking answers: {e}")
            await message.reply("An error occurred while checking answers. Please try again.")

    def calculate_score(self, correct_answers: int) -> float:
        """Calculate IELTS Reading score according to official scale"""
        if correct_answers >= 39: return 9.0
        elif correct_answers >= 37: return 8.5
        elif correct_answers >= 35: return 8.0
        elif correct_answers >= 33: return 7.5
        elif correct_answers >= 30: return 7.0
        elif correct_answers >= 27: return 6.5
        elif correct_answers >= 23: return 6.0
        elif correct_answers >= 19: return 5.5
        elif correct_answers >= 15: return 5.0
        elif correct_answers >= 13: return 4.5
        elif correct_answers >= 10: return 4.0
        else: return 3.5

reading_section = ReadingSection() 