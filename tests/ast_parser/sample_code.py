from math import sqrt, pow, pi


class Shape:
    def __init__(self, color):
        self.color = color

    def get_color(self):
        return self.color


class Circle(Shape):
    def __init__(self, radius, color):
        super().__init__(color)
        self.radius = radius

    def area(self):
        result = pi * pow(self.radius, 2)
        print(f"Circle color: {self.get_color()}")
        return result


if __name__ == "__main__":
    my_circle = Circle(10, "red")
    circle_area = my_circle.area()
    calculate_hypotenuse = lambda a, b: sqrt(a ** 2 + b ** 2)
    hypot = calculate_hypotenuse(3, 4)
    print(f"Area: {circle_area}, Hypotenuse: {hypot}")
