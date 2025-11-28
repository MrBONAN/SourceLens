# dog.py - Специализированные классы для собак

from .base import Animal, calculate_age_in_days, format_animal_info

class Dog(Animal):
    """Класс собаки, наследующий от Animal."""
    
    def __init__(self, name: str, breed: str):
        super().__init__(name)
        self.breed = breed
    
    def speak(self) -> str:
        """Собака лает."""
        return "Woof!"
    
    def get_breed(self) -> str:
        """Возвращает породу собаки."""
        return self.breed

class Puppy(Dog):
    """Класс щенка, наследующий от Dog."""
    
    def __init__(self, name: str, breed: str, age_months: int):
        super().__init__(name, breed)
        self.age_months = age_months
    
    def speak(self) -> str:
        """Щенок издает более тихий звук."""
        return "Yip!"
    
    def get_age_in_days(self) -> int:
        """Возвращает возраст щенка в днях."""
        age_years = self.age_months / 12
        return calculate_age_in_days(int(age_years))

def create_dog(name: str, breed: str) -> Dog:
    """Создает новую собаку."""
    return Dog(name, breed)

def create_puppy(name: str, breed: str, age_months: int) -> Puppy:
    """Создает нового щенка."""
    return Puppy(name, breed, age_months)

def describe_dog(dog: Dog) -> str:
    """Описывает собаку."""
    base_info = format_animal_info(dog)
    return f"{base_info}, Breed: {dog.get_breed()}"
