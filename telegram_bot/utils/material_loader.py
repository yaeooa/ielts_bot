import os
import json
from typing import List, Dict
from config import MATERIALS_DIR

class MaterialLoader:
    def __init__(self):
        self.base_path = MATERIALS_DIR
        
    async def get_available_tests(self) -> List[str]:
        """Получение списка доступных тестов"""
        try:
            tests = []
            for item in os.listdir(self.base_path):
                if item.endswith('test') and os.path.isdir(os.path.join(self.base_path, item)):
                    tests.append(item)
            return sorted(tests)
        except FileNotFoundError:
            print(f"Ошибка: Директория {self.base_path} не найдена")
            return []

    async def get_reading_material(self, test_number: int) -> Dict:
        """Загрузка материалов для reading"""
        path = os.path.join(self.base_path, f"{test_number} test", "reading")
        # TODO: Реализовать загрузку конкретного материала
        return {"text": "текст", "questions": []}

    async def get_listening_material(self, test_number: int) -> Dict:
        """Загрузка материалов для listening"""
        path = os.path.join(self.base_path, f"{test_number} test", "listening")
        # TODO: Реализовать загрузку конкретного материала
        return {"audio_path": "", "questions": []} 