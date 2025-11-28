# bird.py - Классы для птиц

from .base import Animal, Flyable, calculate_age_in_days

class Bird(Animal, Flyable):
    """Класс птицы, наследующий от Animal и Flyable."""
    
    def __init__(self, name: str, species: str):
        super().__init__(name)
        self.species = species
    
    def speak(self) -> str:
        """Птица чирикает."""
        return "Chirp!"
    
    def get_species(self) -> str:
        """Возвращает вид птицы."""
        return self.species
    
    def fly_and_speak(self) -> str:
        """Комбинирует полет и звук."""
        return f"{self.fly()} while {self.speak()}"

class Parrot(Bird):
    """Класс попугая, наследующий от Bird."""
    
    def __init__(self, name: str, species: str, vocabulary: list):
        super().__init__(name, species)
        self.vocabulary = vocabulary
    
    def speak(self) -> str:
        """Попугай повторяет слова из словаря."""
        if self.vocabulary:
            return f"Polly says: {self.vocabulary[0]}"
        return "Chirp!"
    
    def learn_word(self, word: str) -> None:
        """Попугай изучает новое слово."""
        if word not in self.vocabulary:
            self.vocabulary.append(word)

def create_bird(name: str, species: str) -> Bird:
    """Создает новую птицу."""
    return Bird(name, species)

def create_parrot(name: str, species: str, vocabulary: list = None) -> Parrot:
    """Создает нового попугая."""
    if vocabulary is None:
        vocabulary = []
    return Parrot(name, species, vocabulary)

def calculate_bird_age_in_days(bird: Bird, age_years: int) -> int:
    """Вычисляет возраст птицы в днях."""
    return calculate_age_in_days(age_years)
