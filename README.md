# IELTS Training Bot

A Telegram bot designed to help users prepare for the IELTS exam. The bot provides practice materials, instant feedback, and detailed explanations for all four sections of the IELTS test.

## Features

### 🎧 Listening Section
- Practice with authentic IELTS listening tests
- Multiple choice, matching, and completion tasks
- Immediate feedback on answers
- Audio files with transcripts

### 📖 Reading Section
- Academic and General Training reading passages
- Various question types (matching, T/F/NG, etc.)
- Detailed explanations for answers
- Time management practice

### ✍️ Writing Section
- Task 1 (Academic: graphs/charts, GT: letters)
- Task 2 (essays)
- AI-powered feedback on:
  - Task achievement
  - Coherence and cohesion
  - Lexical resource
  - Grammatical range and accuracy

### 🗣 Speaking Section
- All three parts of the speaking test
- Voice message recording and analysis
- Detailed feedback on:
  - Fluency and coherence
  - Lexical resource
  - Grammatical range and accuracy
  - Pronunciation

### Additional Features
- ❓ Ask about IELTS: Get instant answers to any IELTS-related questions
- 💬 Support: Direct access to the bot administrator
- Random test selection for varied practice
- Detailed explanations and tips

## Technical Requirements

- Python 3.8+
- Redis server
- OpenAI API key
- Telegram Bot Token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yaeooa/ielts_bot
cd ielts_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the bot:
```bash
python bot.py
```

## Project Structure

```
ielts_bot/
├── bot.py              # Main bot file
├── config.py           # Configuration settings
├── database.py         # Database operations
├── requirements.txt    # Python dependencies
├── modules/           # Section-specific modules
│   ├── listening.py
│   ├── reading.py
│   ├── writing.py
│   └── speaking.py
├── utils/             # Utility functions
└── materials/         # IELTS practice materials
    ├── IELTS 14/
    └── IELTS 15/
```

## Environment Variables

- `BOT_TOKEN`: Your Telegram bot token
- `REDIS_URL`: Redis server URL
- `OPENAI_API_KEY`: OpenAI API key
- `MATERIALS_DIR`: Path to IELTS materials

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- IELTS materials from Cambridge IELTS books
- OpenAI for providing the GPT API
- Telegram for the bot platform

## Contact

For support or questions, contact [@romawriteme](https://t.me/romawriteme) on Telegram. 
