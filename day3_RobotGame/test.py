n = 5

Pint = [[0] * n] * n
Pint[1][1] = 1

Pont = [[0] * n for row in range(n)]
Pont[1][1] = 1
Pont[1][3] = 5

print(Pint)
print(Pont)


class Mogo():
    def __init__(self):
        self.yare = 5
        self.daze = 6

    def hans(self, daze, yare=5):
        self.yare = yare
        self.daze = daze

mugo = Mogo()
mugo.hans(4)