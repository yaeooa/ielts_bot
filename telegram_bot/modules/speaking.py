import os
import asyncio
from aiogram import types
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import MATERIALS_DIR
import openai
from utils.material_loader import MaterialLoader

class SpeakingStates(StatesGroup):
    selecting_book = State()
    selecting_test = State()
    selecting_part = State()
    answering_question = State()
    waiting_for_response = State()

class SpeakingSection:
    def __init__(self):
        self.material_loader = MaterialLoader()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = "openai/gpt-4o-mini"
        
        # Конфигурация для разных частей
        self.part_config = {
            1: {
                "emoji": "🎤",
                "timing": "⏱ Part 1: 4-5 minutes total (~20-30 seconds per question)",
                "advice": "💡 Keep your answers brief and to the point",
                "duration": 25
            },
            2: {
                "emoji": "📝",
                "timing": "⏱ Part 2: 1 minute preparation + 2 minutes speaking",
                "advice": "💡 You have 1 minute to prepare and 2 minutes to speak",
                "duration": 120
            },
            3: {
                "emoji": "💬",
                "timing": "⏱ Part 3: 4-5 minutes total (~40-60 seconds per question)",
                "advice": "💡 Provide detailed answers with explanations and examples",
                "duration": 50
            }
        }

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
            import random
            book = random.choice(["IELTS 14", "IELTS 15"])
            test_number = str(random.randint(1, 4))
            part_number = random.randint(1, 3)
            
            await state.update_data(
                selected_book=book,
                selected_test=test_number,
                selected_part=part_number
            )
            
            await message.reply(
                f"🎲 Random test selected:\n"
                f"📚 Book: {book}\n"
                f"📝 Test: {test_number}\n"
                f"🗣 Part: {part_number}\n\n"
                f"{self.part_config[part_number]['timing']}\n"
                f"{self.part_config[part_number]['advice']}"
            )
            
            return await self._load_and_send_questions(message, state)

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
        await state.update_data(selected_part=part_number)
        
        # Send timing information
        config = self.part_config[part_number]
        await message.reply(f"{config['timing']}\n{config['advice']}")
        
        return await self._load_and_send_questions(message, state)

    async def _load_and_send_questions(self, message: types.Message, state: FSMContext):
        """Load questions and send appropriate content based on part"""
        try:
            data = await state.get_data()
            book = data['selected_book']
            test_number = data['selected_test']
            part_number = data['selected_part']
            config = self.part_config[part_number]

            print(f"Debug - Loading questions for: Book={book}, Test={test_number}, Part={part_number}")

            # Load questions
            questions_path = os.path.join(
                MATERIALS_DIR,
                book,
                f"{test_number} test",
                "Speaking",
                f"speaking-test{test_number}-part{part_number}.txt"
            )
            
            print(f"Debug - Questions path: {questions_path}")
            print(f"Debug - Path exists: {os.path.exists(questions_path)}")
            
            if not os.path.exists(questions_path):
                await message.reply("Sorry, the questions for this part are not available.")
                return False

            with open(questions_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Debug - File content:\n{content}")

            # Parse content
            questions_list = []
            discussion_topics = []
            current_topic = None
            
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if line.startswith("**Discussion topic:"):
                    topic = line.replace("**Discussion topic:", "").strip()
                    topic = topic.rstrip('*')
                    discussion_topics.append(topic)
                    current_topic = topic
                    print(f"Debug - Found topic: {topic}")
                elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    question = line.split('.', 1)[1].strip()
                    questions_list.append({
                        'question': question,
                        'topic': current_topic
                    })
                    print(f"Debug - Found question: {question} (topic: {current_topic})")

            print(f"Debug - Found {len(questions_list)} questions and {len(discussion_topics)} topics")

            if part_number == 2:
                # Handle Part 2
                image_path = os.path.join(
                    MATERIALS_DIR,
                    book,
                    f"{test_number} test",
                    "Speaking",
                    f"speaking-test{test_number}-part2.png"
                )
                
                print(f"Debug - Image path: {image_path}")
                print(f"Debug - Image exists: {os.path.exists(image_path)}")
                
                if not os.path.exists(image_path):
                    await message.reply("Sorry, the image for this part is not available.")
                    return False

                # Create single question for Part 2
                questions_list = [{
                    'question': "Describe the topic shown in the image.",
                    'topic': None
                }]
                
                await state.update_data(
                    questions=questions_list,
                    all_responses=[]
                )
                
                await message.reply_photo(
                    types.FSInputFile(image_path),
                    caption=f"{config['emoji']} Part {part_number}\n\n"
                           f"{config['advice']}\n"
                           f"⏱ Expected speaking duration: {config['duration']} seconds\n\n"
                           f"Please record your answer and send it as a voice message."
                )
                await state.set_state(SpeakingStates.waiting_for_response)
                
            else:
                # Handle Parts 1 and 3
                if not questions_list:
                    print("Debug - No questions found in the file")
                    await message.reply("Error: No questions found in the file.")
                    return False

                if part_number == 3 and discussion_topics:
                    print("Debug - Showing discussion topics for Part 3")
                    print(f"Debug - Discussion topics: {discussion_topics}")
                    # Show discussion topics for Part 3
                    topics_text = []
                    for topic in discussion_topics:
                        print(f"Debug - Processing topic: {topic}")
                        escaped_topic = self._escape_markdown(topic)
                        print(f"Debug - Escaped topic: {escaped_topic}")
                        topics_text.append(f"*{escaped_topic}*")
                    
                    final_text = (
                        f"{config['emoji']} Discussion topics:\n\n"
                        f"{chr(10).join(topics_text)}\n\n"
                        f"💡 You will be asked several questions about these topics\."
                    )
                    print(f"Debug - Final message text: {final_text}")
                    
                    await message.reply(
                        final_text,
                        parse_mode="MarkdownV2"
                    )

                print(f"Debug - Updating state with {len(questions_list)} questions")
                await state.update_data(
                    questions=questions_list,
                    current_question_index=0,
                    all_responses=[]
                )
                await state.set_state(SpeakingStates.answering_question)
                await self._send_next_question(message, state)

            return False

        except Exception as e:
            print(f"Debug - Error in _load_and_send_questions: {str(e)}")
            await message.reply("Sorry, an error occurred while loading questions. Please try again.")
            return False

    def _escape_markdown(self, text: str) -> str:
        """Escape special characters for MarkdownV2"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    async def _send_next_question(self, message: types.Message, state: FSMContext):
        """Send next question to the user"""
        try:
            data = await state.get_data()
            
            print(f"Debug - _send_next_question: Current state data: {data}")
            
            # Проверяем наличие необходимых данных
            if 'questions' not in data or 'current_question_index' not in data or 'selected_part' not in data:
                print("Debug - Missing required data in state")
                await message.reply("Error: Missing required data. Please try selecting the part again.")
                return

            questions = data['questions']
            current_index = data['current_question_index']
            part_number = data['selected_part']
            config = self.part_config[part_number]

            print(f"Debug - Current question index: {current_index}, Total questions: {len(questions)}")

            if current_index >= len(questions):
                print("Debug - All questions answered, evaluating responses")
                await self._evaluate_all_responses(message, state)
                return

            question_data = questions[current_index]
            question = question_data['question']
            topic = question_data.get('topic', '')
            
            print(f"Debug - Sending question {current_index + 1}: {question}")
            print(f"Debug - Topic: {topic}")
            
            # Собираем сообщение по частям
            message_parts = []
            
            # Добавляем заголовок
            message_parts.append(f"{config['emoji']} Question {current_index + 1}/{len(questions)}:")
            
            # Добавляем тему, если есть
            if topic and part_number == 3:
                escaped_topic = self._escape_markdown(topic)
                message_parts.append(f"*{escaped_topic}*")
            
            # Добавляем вопрос
            escaped_question = self._escape_markdown(question)
            message_parts.append(escaped_question)
            
            # Добавляем совет
            escaped_advice = self._escape_markdown(config['advice'])
            message_parts.append(f"💡 {escaped_advice}")
            
            # Добавляем время
            message_parts.append(f"⏱ Expected duration: up to {config['duration']} seconds")
            
            # Добавляем инструкцию
            message_parts.append(self._escape_markdown("Please record your answer and send it as a voice message."))
            
            # Собираем финальное сообщение
            message_text = "\n\n".join(message_parts)
            
            print(f"Debug - Message text: {message_text}")
            
            await message.reply(
                message_text,
                parse_mode="MarkdownV2"
            )

        except Exception as e:
            print(f"Debug - Error in _send_next_question: {str(e)}")
            await message.reply(
                "Sorry, an error occurred while sending the next question.\n"
                "Please try selecting the part again."
            )

    async def process_response(self, message: types.Message, state: FSMContext):
        """Process user's voice response"""
        if message.text == "Back to Main Menu":
            await state.clear()
            return True

        if not message.voice:
            await message.reply("Please send a voice message.")
            return False

        try:
            await message.reply("🎤 Got your voice message! Processing it now...")

            data = await state.get_data()
            part_number = data['selected_part']
            config = self.part_config[part_number]
            questions = data['questions']
            all_responses = data.get('all_responses', [])
            current_index = data.get('current_question_index', 0)

            # Get voice message duration
            duration = message.voice.duration
            if duration < 3:
                await message.reply("Your voice message is too short. Please record a longer message.")
                return False

            # Download voice message
            voice_file = await message.bot.get_file(message.voice.file_id)
            voice_path = f"temp_voice_{message.from_user.id}.ogg"
            await message.bot.download_file(voice_file.file_path, voice_path)

            try:
                # Create OpenAI client
                client = openai.AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )

                # Transcribe using Whisper
                with open(voice_path, "rb") as audio_file:
                    transcription = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",  # Получаем расширенный JSON с информацией о языке
                        temperature=0.2
                    )
                
                # Получаем текст и язык
                text = transcription.text
                detected_language = transcription.language if hasattr(transcription, 'language') else 'unknown'
                
                if not text.strip():
                    await message.reply(
                        "⚠️ Could not transcribe any words from your voice message.\n"
                        "Please try speaking more clearly and try again."
                    )
                    return False
                
                # Проверяем язык
                if detected_language.lower() not in ['en', 'english']:
                    await message.reply(
                        f"⚠️ Your response was in {detected_language.upper()}. "
                        "Please answer in English as this is an IELTS speaking test."
                    )
                    return False
                    
            except Exception as e:
                print(f"Debug - Error in transcription: {str(e)}")
                await message.reply(
                    "⚠️ Could not transcribe the voice message.\n"
                    "Please try again with better audio quality."
                )
                text = '[Transcription not available]'
                detected_language = 'unknown'

            # Clean up temporary file
            os.remove(voice_path)

            # Store response
            response_data = {
                'text': text,
                'duration': duration,
                'language': detected_language
            }
            all_responses.append(response_data)
            
            # Получаем текущий вопрос для логирования
            current_question = questions[current_index]['question'] if current_index < len(questions) else "Unknown question"
            
            # Логируем ответ
            print(f"\nDebug - Response {current_index + 1}:")
            print(f"Question: {current_question}")
            print(f"Answer: {text}")
            print(f"Duration: {duration} seconds")
            print(f"Language: {detected_language}")
            print(f"All responses so far: {all_responses}\n")

            # Update state
            await state.update_data(
                all_responses=all_responses,
                current_question_index=current_index + 1
            )

            if part_number == 2:
                await self._evaluate_all_responses(message, state)
            else:
                if current_index + 1 < len(questions):
                    await message.reply(
                        f"✅ Answer {current_index + 1} received!\n"
                        f"⏱ Duration: {duration} seconds\n\n"
                        f"Moving to the next question..."
                    )
                    await self._send_next_question(message, state)
                else:
                    await message.reply(
                        f"✅ All answers received!\n"
                        f"⏱ Processing your responses..."
                    )
                    await self._evaluate_all_responses(message, state)

            return False

        except Exception as e:
            print(f"Debug - Error in process_response: {str(e)}")
            await message.reply("Sorry, an error occurred while processing your response. Please try again.")
            return False

    async def _evaluate_all_responses(self, message: types.Message, state: FSMContext):
        """Evaluate all responses for the part"""
        try:
            data = await state.get_data()
            part_number = data['selected_part']
            book = data['selected_book']
            test_number = data['selected_test']
            all_responses = data['all_responses']
            questions = data['questions']

            if not all_responses:
                await message.reply("No responses to evaluate. Please try again.")
                return

            # Check for transcriptions
            has_transcriptions = all(r['text'] != '[Transcription not available]' for r in all_responses)
            if not has_transcriptions:
                await message.reply(
                    "⚠️ Could not evaluate your responses because voice messages could not be transcribed.\n"
                    "Please try speaking more clearly and try again."
                )
                return

            # Combine responses
            combined_response = "\n\n".join([
                f"Question {i+1}: {q['question']}\nAnswer: {r['text']}\nDuration: {r['duration']} seconds"
                for i, (q, r) in enumerate(zip(questions, all_responses))
            ])

            # Load evaluation prompt
            prompt_path = os.path.join(MATERIALS_DIR, "prompts", "speaking", "evaluation.txt")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()

            # Replace placeholders
            prompt = prompt.replace("[PART NUMBER (1, 2 or 3)]", str(part_number))
            prompt = prompt.replace("[TRANSCRIBED TEXT OF STUDENT RESPONSE]", combined_response)
            prompt = prompt.replace("[TEXT OF QUESTIONS FROM .txt FILE FOR THAT PART]", "\n".join([q['question'] for q in questions]))
            prompt = prompt.replace("[DURATION INFO]", "Multiple responses - see individual durations above")

            # Create OpenRouter client
            client = openai.AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/yourusername/ielts_bot",
                    "X-Title": "IELTS Speaking Bot"
                }
            )

            # Get evaluation
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an IELTS speaking examiner."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            # Format and send evaluation
            raw_evaluation = response.choices[0].message.content
            formatted_evaluation = self._format_evaluation(raw_evaluation)
            
            # Add summary
            summary = "📝 Summary of your responses:\n\n"
            for i, (q, r) in enumerate(zip(questions, all_responses)):
                summary += f"Question {i+1}: {r['duration']} seconds\n"
            
            await message.reply(f"{summary}\n\n{formatted_evaluation}")
            await state.set_state(SpeakingStates.selecting_part)
            await message.reply("Select a part:", reply_markup=self.get_part_keyboard())

        except Exception as e:
            await message.reply("Sorry, an error occurred while evaluating your responses. Please try again.")

    def _format_evaluation(self, evaluation: str) -> str:
        """Format evaluation for user display"""
        try:
            parts = evaluation.split('\n')
            formatted_parts = []
            
            criteria_emojis = {
                "fluency_and_coherence": "💬",
                "lexical_resource": "📚",
                "grammatical_range_and_accuracy": "✍️",
                "pronunciation": "🎤"
            }
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                if "_score:" in part:
                    criterion = part.split("_score:")[0].strip()
                    score = part.split("_score:")[1].strip()
                    emoji = criteria_emojis.get(criterion, "📝")
                    formatted_parts.append(f"\n{emoji} {criterion.replace('_', ' ').title()}: {score}/9")
                
                elif "_comment:" in part:
                    criterion = part.split("_comment:")[0].strip()
                    comment = part.split("_comment:")[1].strip()
                    formatted_parts.append(f"💬 {comment}\n")
                
                elif "overall_band_score:" in part:
                    score = part.split("overall_band_score:")[1].strip()
                    formatted_parts.append(f"\n\n🏆 Overall Score: {score}/9")
                
                elif "overall_comment:" in part:
                    comment = part.split("overall_comment:")[1].strip()
                    formatted_parts.append(f"\n📝 Overall Comment:\n{comment}")
            
            return "\n".join(formatted_parts)
            
        except Exception as e:
            return "Sorry, an error occurred while formatting the evaluation." 