class Caller:
    def call1(self):
        return self
    def call2(self):
        return self

obj = Caller()
obj.call1().call2()