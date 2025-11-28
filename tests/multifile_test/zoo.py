# zoo.py - Главный модуль зоопарка

from .dog import Dog, Puppy, create_dog, create_puppy, describe_dog
from .bird import Bird, Parrot, create_bird, create_parrot, calculate_bird_age_in_days
from .base import Animal, format_animal_info

class Zoo:
    """Класс зоопарка для управления животными."""
    
    def __init__(self, name: str):
        self.name = name
        self.animals = []
    
    def add_animal(self, animal: Animal) -> None:
        """Добавляет животное в зоопарк."""
        self.animals.append(animal)
    
    def get_animal_count(self) -> int:
        """Возвращает количество животных в зоопарке."""
        return len(self.animals)
    
    def make_all_animals_speak(self) -> list:
        """Заставляет всех животных говорить."""
        sounds = []
        for animal in self.animals:
            sound = animal.speak()
            sounds.append(f"{animal.get_name()}: {sound}")
        return sounds
    
    def get_animal_info(self) -> list:
        """Возвращает информацию о всех животных."""
        info = []
        for animal in self.animals:
            info.append(format_animal_info(animal))
        return info

def create_sample_zoo() -> Zoo:
    """Создает зоопарк с примерами животных."""
    zoo = Zoo("Sample Zoo")
    
    # Создаем собак
    dog1 = create_dog("Buddy", "Golden Retriever")
    puppy1 = create_puppy("Max", "Labrador", 6)
    
    # Создаем птиц
    bird1 = create_bird("Tweety", "Canary")
    parrot1 = create_parrot("Polly", "African Grey", ["Hello", "Goodbye"])
    
    # Добавляем в зоопарк
    zoo.add_animal(dog1)
    zoo.add_animal(puppy1)
    zoo.add_animal(bird1)
    zoo.add_animal(parrot1)
    
    return zoo

def demonstrate_inheritance():
    """Демонстрирует наследование и полиморфизм."""
    zoo = create_sample_zoo()
    
    print(f"Zoo: {zoo.name}")
    print(f"Animal count: {zoo.get_animal_count()}")
    print("\nAnimal sounds:")
    for sound in zoo.make_all_animals_speak():
        print(f"  {sound}")
    
    print("\nAnimal info:")
    for info in zoo.get_animal_info():
        print(f"  {info}")
    
    # Демонстрируем специальные методы
    print("\nSpecial methods:")
    for animal in zoo.animals:
        if isinstance(animal, Dog):
            print(f"  {describe_dog(animal)}")
        elif isinstance(animal, Bird):
            print(f"  {animal.get_species()}: {animal.fly_and_speak()}")

if __name__ == "__main__":
    demonstrate_inheritance()
