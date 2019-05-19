n = 5

Pint = [[0] * n] * n
Pint[1][1] = 1

Pont = [[0] * n for row in range(n)]
Pont[1][1] = 1
Pont[1][3] = 5

print(Pint)
print(Pont)
