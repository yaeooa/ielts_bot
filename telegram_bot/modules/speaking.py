import os
import asyncio
from aiogram import types
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import MATERIALS_DIR
import openai
import httpx
from utils.material_loader import MaterialLoader
import random

class SpeakingStates(StatesGroup):
    selecting_book = State()
    selecting_test = State()
    selecting_part = State()
    answering_question = State()
    waiting_for_response = State()

class SpeakingSection:
    def __init__(self):
        self.material_loader = MaterialLoader()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.AsyncOpenAI(api_key=self.openai_api_key)
        
        # Timing information
        self.part_timings = {
            1: "⏱ Part 1: 4-5 minutes total (~20-30 seconds per question)\n"
               "💡 Keep your answers brief and to the point",
            2: "⏱ Part 2: 1 minute preparation + 2 minutes speaking",
            3: "⏱ Part 3: 4-5 minutes total (~40-60 seconds per question)\n"
               "💡 Provide detailed answers with explanations and examples"
        }
        
        # Expected durations in seconds
        self.expected_durations = {
            1: 25,  # per question (20-30 seconds)
            2: 120,  # total speaking time (2 minutes)
            3: 50   # per question (40-60 seconds)
        }
        
        # Emojis for different parts
        self.part_emojis = {
            1: "🎤",
            2: "📝",
            3: "💬"
        }

    async def start_section(self, message: types.Message, state: FSMContext):
        """Start Speaking section"""
        await state.clear()
        await state.set_state(SpeakingStates.selecting_book)
        await message.reply("Select a book:", reply_markup=self.get_book_keyboard())

    def get_book_keyboard(self):
        """Create keyboard for book selection"""
        keyboard = [
            [KeyboardButton(text="IELTS 14")],
            [KeyboardButton(text="IELTS 15")],
            [KeyboardButton(text="🎲 Random Test")],
            [KeyboardButton(text="Back to Main Menu")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    def get_test_keyboard(self):
        """Create keyboard for test selection"""
        keyboard = [
            [KeyboardButton(text="Test 1")],
            [KeyboardButton(text="Test 2")],
            [KeyboardButton(text="Test 3")],
            [KeyboardButton(text="Test 4")],
            [KeyboardButton(text="Back to Main Menu")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    def get_part_keyboard(self):
        """Create keyboard for part selection"""
        keyboard = [
            [KeyboardButton(text="Part 1")],
            [KeyboardButton(text="Part 2")],
            [KeyboardButton(text="Part 3")],
            [KeyboardButton(text="Back to Main Menu")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    async def handle_book_selection(self, message: types.Message, state: FSMContext):
        """Handle book selection"""
        if message.text == "Back to Main Menu":
            await state.clear()
            return True

        if message.text == "🎲 Random Test":
            # Выбираем случайную книгу и тест
            book = random.choice(["IELTS 14", "IELTS 15"])
            test_number = str(random.randint(1, 4))
            part_number = random.randint(1, 3)
            
            await state.update_data(
                selected_book=book,
                selected_test=test_number,
                selected_part=part_number
            )
            
            # Загружаем вопросы для выбранной части
            questions_path = os.path.join(
                MATERIALS_DIR,
                book,
                f"{test_number} test",
                "Speaking",
                f"speaking-test{test_number}-part{part_number}.txt"
            )
            
            if not os.path.exists(questions_path):
                await message.reply("Sorry, the questions for this part are not available. Please try again.")
                return False

            with open(questions_path, 'r', encoding='utf-8') as f:
                questions = f.read()

            # Parse questions and discussion topics
            questions_list = []
            discussion_topics = []
            current_topic = None
            
            for line in questions.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith("**Discussion topic:"):
                        topic = line.replace("**Discussion topic:", "").strip()
                        discussion_topics.append(topic)
                        current_topic = topic
                    elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                        question = line.split('.', 1)[1].strip()
                        questions_list.append({
                            'question': question,
                            'topic': current_topic
                        })

            # Отправляем информацию о выбранной части
            await message.reply(
                f"🎲 Random test selected:\n"
                f"📚 Book: {book}\n"
                f"📝 Test: {test_number}\n"
                f"🗣 Part: {part_number}\n\n"
                f"{self.part_timings[part_number]}"
            )

            if part_number == 2:
                # For Part 2, send the image
                image_path = os.path.join(
                    MATERIALS_DIR,
                    book,
                    f"{test_number} test",
                    "Speaking",
                    f"speaking-test{test_number}-part2.png"
                )
                
                if os.path.exists(image_path):
                    await message.reply_photo(
                        types.FSInputFile(image_path),
                        caption=f"{self.part_emojis[part_number]} Part {part_number}\n\n"
                               f"💡 You have 1 minute to prepare and 2 minutes to speak.\n"
                               f"⏱ Expected speaking duration: 2 minutes\n\n"
                               f"Please record your answer and send it as a voice message."
                    )
                    await state.update_data(
                        questions=questions_list,
                        all_responses=[]
                    )
                    await state.set_state(SpeakingStates.waiting_for_response)
                else:
                    await message.reply("Sorry, the image for this part is not available.")
                    return False
            else:
                # For Parts 1 and 3
                if part_number == 3 and discussion_topics:
                    topics_text = []
                    for topic in discussion_topics:
                        escaped_topic = topic.replace('.', '\.').replace('-', '\-').replace('_', '\_')
                        topics_text.append(f"*{escaped_topic}*")
                    
                    await message.reply(
                        f"{self.part_emojis[part_number]} Discussion topics:\n\n"
                        f"{chr(10).join(topics_text)}\n\n"
                        f"💡 You will be asked several questions about these topics\.",
                        parse_mode="MarkdownV2"
                    )

                await state.update_data(
                    questions=questions_list,
                    current_question_index=0,
                    all_responses=[]
                )
                await state.set_state(SpeakingStates.answering_question)
                await self._send_next_question(message, state)
            return False

        if message.text not in ["IELTS 14", "IELTS 15"]:
            await message.reply("Please select a book from the options")
            return False

        await state.update_data(selected_book=message.text)
        await state.set_state(SpeakingStates.selecting_test)
        await message.reply("Select a test:", reply_markup=self.get_test_keyboard())
        return False

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
        await state.set_state(SpeakingStates.selecting_part)
        await message.reply("Select a part:", reply_markup=self.get_part_keyboard())
        return False

    async def handle_part_selection(self, message: types.Message, state: FSMContext):
        """Handle part selection"""
        if message.text == "Back to Main Menu":
            await state.clear()
            return True

        if not message.text.startswith("Part"):
            await message.reply("Please select a part from the options")
            return False

        part_number = int(message.text.split()[1])
        data = await state.get_data()
        book = data['selected_book']
        test_number = data['selected_test']

        # Send timing information
        await message.reply(self.part_timings[part_number])

        # Load questions
        questions_path = os.path.join(
            MATERIALS_DIR,
            book,
            f"{test_number} test",
            "Speaking",
            f"speaking-test{test_number}-part{part_number}.txt"
        )
        
        if not os.path.exists(questions_path):
            await message.reply("Sorry, the questions for this part are not available.")
            return False

        with open(questions_path, 'r', encoding='utf-8') as f:
            questions = f.read()

        # Parse questions and discussion topics
        questions_list = []
        discussion_topics = []
        current_topic = None
        
        for line in questions.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith("**Discussion topic:"):
                    topic = line.replace("**Discussion topic:", "").strip()
                    discussion_topics.append(topic)
                    current_topic = topic
                elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    question = line.split('.', 1)[1].strip()
                    questions_list.append({
                        'question': question,
                        'topic': current_topic
                    })

        if part_number == 2:
            # For Part 2, send the image and prepare for response
            image_path = os.path.join(
                MATERIALS_DIR,
                book,
                f"{test_number} test",
                "Speaking",
                f"speaking-test{test_number}-part2.png"
            )
            
            if os.path.exists(image_path):
                # Для Part 2 создаем один вопрос с описанием задания
                question_text = f"Describe the topic shown in the image. You have 1 minute to prepare and 2 minutes to speak."
                questions_list = [{
                    'question': question_text,
                    'topic': None
                }]
                
                # Сохраняем вопросы в состоянии
                await state.update_data(
                    selected_part=part_number,
                    questions=questions_list,
                    all_responses=[]
                )
                
                await message.reply_photo(
                    types.FSInputFile(image_path),
                    caption=f"{self.part_emojis[part_number]} Part {part_number}\n\n"
                           f"💡 You have 1 minute to prepare and 2 minutes to speak.\n"
                           f"⏱ Expected speaking duration: 2 minutes\n\n"
                           f"Please record your answer and send it as a voice message."
                )
                await state.set_state(SpeakingStates.waiting_for_response)
            else:
                await message.reply("Sorry, the image for this part is not available.")
                return False
        else:
            # For Parts 1 and 3, send first question
            if part_number == 3:
                # For Part 3, show all discussion topics first
                if discussion_topics:
                    topics_text = []
                    for topic in discussion_topics:
                        escaped_topic = topic.replace('.', '\.').replace('-', '\-').replace('_', '\_')
                        topics_text.append(f"*{escaped_topic}*")
                    
                    await message.reply(
                        f"{self.part_emojis[part_number]} Discussion topics:\n\n"
                        f"{chr(10).join(topics_text)}\n\n"
                        f"💡 You will be asked several questions about these topics\.",
                        parse_mode="MarkdownV2"
                    )

            await state.update_data(
                selected_part=part_number,
                questions=questions_list,
                current_question_index=0,
                all_responses=[]
            )
            await state.set_state(SpeakingStates.answering_question)
            await self._send_next_question(message, state)
            return False

    async def _send_next_question(self, message: types.Message, state: FSMContext):
        """Send next question to the user"""
        print("=== Starting _send_next_question ===")
        try:
            data = await state.get_data()
            print(f"Current state data: {data}")
            
            questions = data['questions']
            current_index = data['current_question_index']
            part_number = data['selected_part']

            print(f"Current index: {current_index}, Total questions: {len(questions)}")

            if current_index >= len(questions):
                print("All questions answered, evaluating responses...")
                await self._evaluate_all_responses(message, state)
                return

            question_data = questions[current_index]
            question = question_data['question']
            topic = question_data.get('topic', '')
            
            timing_advice = "Keep your answer brief and to the point" if part_number == 1 else "Provide detailed answers with explanations"
            print(f"Sending question {current_index + 1}: {question}")
            
            message_text = f"{self.part_emojis[part_number]} Question {current_index + 1}/{len(questions)}:\n\n"
            
            if topic and part_number == 3:
                # Экранируем специальные символы для MarkdownV2
                escaped_topic = topic.replace('.', '\.').replace('-', '\-').replace('_', '\_')
                message_text += f"*{escaped_topic}*\n\n"
            
            message_text += f"{question}\n\n"
            message_text += f"💡 {timing_advice}\n"
            message_text += f"⏱ Expected duration: up to {self.expected_durations[part_number]} seconds\n\n"
            message_text += "Please record your answer and send it as a voice message."
            
            await message.reply(
                message_text,
                parse_mode="MarkdownV2" if topic and part_number == 3 else None
            )
            print("=== _send_next_question completed successfully ===")
        except Exception as e:
            print(f"Error in _send_next_question: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            await message.reply("Sorry, an error occurred while sending the next question. Please try again.")

    async def _evaluate_all_responses(self, message: types.Message, state: FSMContext):
        """Evaluate all responses for the part"""
        print("=== Starting _evaluate_all_responses ===")
        try:
            data = await state.get_data()
            print(f"Current state data: {data}")
            
            part_number = data['selected_part']
            book = data['selected_book']
            test_number = data['selected_test']
            all_responses = data['all_responses']
            questions = data['questions']

            print(f"Evaluating {len(all_responses)} responses for Part {part_number}")
            print(f"Number of questions: {len(questions)}")

            if not all_responses:
                await message.reply("No responses to evaluate. Please try again.")
                return

            # Combine all responses and questions
            combined_response = "\n\n".join([
                f"Question {i+1}: {q['question']}\nAnswer: {r['text']}\nDuration: {r['duration']} seconds"
                for i, (q, r) in enumerate(zip(questions, all_responses))
            ])
            print("Responses combined for evaluation")

            # Load evaluation prompt
            prompt_path = os.path.join(MATERIALS_DIR, "prompts", "speaking", "evaluation.txt")
            print(f"Loading prompt from: {prompt_path}")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()

            # Replace placeholders in prompt
            prompt = prompt.replace("[PART NUMBER (1, 2 or 3)]", str(part_number))
            prompt = prompt.replace("[TRANSCRIBED TEXT OF STUDENT RESPONSE]", combined_response)
            prompt = prompt.replace("[TEXT OF QUESTIONS FROM .txt FILE FOR THAT PART]", "\n".join([q['question'] for q in questions]))
            prompt = prompt.replace("[DURATION INFO]", "Multiple responses - see individual durations above")
            print("Prompt prepared")

            # Get evaluation from GPT
            print("Sending request to GPT...")
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an IELTS speaking examiner."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            print("GPT response received")

            # Format and send evaluation
            evaluation = response.choices[0].message.content
            formatted_evaluation = self._format_evaluation(evaluation)
            
            # Add summary of all responses
            summary = "📝 Summary of your responses:\n\n"
            for i, (q, r) in enumerate(zip(questions, all_responses)):
                summary += f"Question {i+1}: {r['duration']} seconds\n"
            
            print("Sending evaluation to user...")
            await message.reply(f"{summary}\n\n{formatted_evaluation}")
            await state.set_state(SpeakingStates.selecting_part)
            await message.reply("Select a part:", reply_markup=self.get_part_keyboard())
            print("=== _evaluate_all_responses completed successfully ===")

        except Exception as e:
            print(f"Error in _evaluate_all_responses: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            await message.reply("Sorry, an error occurred while evaluating your responses. Please try again.")

    async def process_response(self, message: types.Message, state: FSMContext):
        """Process user's voice response"""
        print("=== Starting process_response ===")
        if message.text == "Back to Main Menu":
            print("Back to Main Menu selected")
            await state.clear()
            return True

        if not message.voice:
            print("No voice message received")
            await message.reply("Please send a voice message.")
            return False

        try:
            print("Sending acknowledgment message")
            await message.reply("🎤 Got your voice message! Processing it now...")

            data = await state.get_data()
            print(f"Current state data: {data}")
            
            part_number = data['selected_part']
            book = data['selected_book']
            test_number = data['selected_test']
            questions = data['questions']
            all_responses = data.get('all_responses', [])
            current_index = data.get('current_question_index', 0)
            
            print(f"Processing response for Part {part_number}, Question {current_index + 1}/{len(questions)}")

            # Get voice message duration
            duration = message.voice.duration
            expected_duration = self.expected_durations[part_number]
            print(f"Voice duration: {duration} seconds (Expected: {expected_duration})")

            # Проверяем длительность голосового сообщения
            if duration < 3:  # Минимальная длительность 3 секунды
                await message.reply("Your voice message is too short. Please record a longer message.")
                return False

            # Download voice message
            print("Downloading voice message...")
            voice_file = await message.bot.get_file(message.voice.file_id)
            voice_path = f"temp_voice_{message.from_user.id}.ogg"
            await message.bot.download_file(voice_file.file_path, voice_path)

            try:
                # Transcribe using Whisper
                print("Transcribing voice message...")
                with open(voice_path, "rb") as audio_file:
                    transcription = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                print(f"Transcription completed: {transcription.text[:100]}...")
            except Exception as e:
                print(f"Error in transcription: {str(e)}")
                # Если не удалось транскрибировать, используем placeholder
                transcription = type('obj', (object,), {'text': '[Transcription not available]'})
                await message.reply("⚠️ Could not transcribe the voice message. The evaluation will be based on duration only.")

            # Clean up temporary file
            os.remove(voice_path)
            print("Temporary file removed")

            # Store response
            all_responses.append({
                'text': transcription.text,
                'duration': duration
            })
            print(f"Response stored. Total responses: {len(all_responses)}")

            # Update state with new response
            print("Updating state...")
            await state.update_data(
                all_responses=all_responses,
                current_question_index=current_index + 1
            )
            print(f"State updated. New current_index: {current_index + 1}")

            if part_number == 2:
                print("Processing Part 2 response")
                await self._evaluate_all_responses(message, state)
            else:
                print(f"Processing Part {part_number} response")
                if current_index + 1 < len(questions):
                    print("Sending next question...")
                    await message.reply(
                        f"✅ Answer {current_index + 1} received!\n"
                        f"⏱ Duration: {duration} seconds\n\n"
                        f"Moving to the next question..."
                    )
                    await self._send_next_question(message, state)
                else:
                    print("All questions answered, evaluating responses...")
                    await message.reply(
                        f"✅ All answers received!\n"
                        f"⏱ Processing your responses..."
                    )
                    await self._evaluate_all_responses(message, state)

            print("=== process_response completed successfully ===")
            return False

        except Exception as e:
            print(f"Error in process_response: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            await message.reply("Sorry, an error occurred while processing your response. Please try again.")
            return False

    def _format_evaluation(self, evaluation: str) -> str:
        """Format evaluation for user display"""
        try:
            # Split evaluation into parts
            parts = evaluation.split('\n')
            formatted_parts = []
            
            # Dictionary for emojis and formatting
            criteria_emojis = {
                "fluency_and_coherence": "💬",
                "lexical_resource": "📚",
                "grammatical_range_and_accuracy": "✍️",
                "pronunciation": "🎤"
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
            return result
            
        except Exception as e:
            print(f"Error formatting evaluation: {e}")
            return "Sorry, an error occurred while formatting the evaluation." 