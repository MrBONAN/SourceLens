# base.py - Базовые классы и функции

class Animal:
    """Базовый класс для всех животных."""
    
    def __init__(self, name: str):
        self.name = name
    
    def speak(self) -> str:
        """Возвращает звук, который издает животное."""
        return "Some generic animal sound"
    
    def get_name(self) -> str:
        """Возвращает имя животного."""
        return self.name

class Flyable:
    """Миксин для летающих объектов."""
    
    def fly(self) -> str:
        """Возвращает сообщение о полете."""
        return "Flying through the air"

def calculate_age_in_days(age_years: int) -> int:
    """Вычисляет возраст в днях."""
    return age_years * 365

def format_animal_info(animal: Animal) -> str:
    """Форматирует информацию о животном."""
    return f"Animal: {animal.get_name()}, Sound: {animal.speak()}"
