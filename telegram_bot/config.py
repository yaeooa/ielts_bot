import os
from dotenv import load_dotenv

load_dotenv()

# Абсолютный путь к материалам IELTS
MATERIALS_DIR = "/Users/macbook/Downloads/ielts_materials"

# Проверка существования директории при запуске
if not os.path.exists(MATERIALS_DIR):
    raise FileNotFoundError(f"Директория с материалами не найдена: {MATERIALS_DIR}") 