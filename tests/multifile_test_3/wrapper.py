from .first import First, Second

class Wrapper:
    def __init__(self, obj):
        self.obj = obj
        pass

    def do_something(self):
        self.obj.something()
