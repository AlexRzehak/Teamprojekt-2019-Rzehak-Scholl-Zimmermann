# Week 3: Create a Playing Field and a Robot

### [<- Back](/index.md) to project overview.

1. Create a Class that represents the Playing field and set up a 100x100 array to represent potential Obstacles:
```
class PlayingField:

    def setupArray(self, arraysize):
        obstacleArray = [[0 for col in range(arraysize)] for row in range(arraysize)]

        # setting the sidewalls by setting all the first and last Elements of each row and column to 1
        for x in range(arraysize):
            obstacleArray[x][0] = 1
            obstacleArray[x][arraysize - 1] = 1
            obstacleArray[0][x] = 1
            obstacleArray[arraysize - 1][x] = 1

        # individual Wall tiles:
        obstacleArray[28][34] = 1
        obstacleArray[54][43] = 1
        obstacleArray[0][49] = 0

        return obstacleArray
```

2. Draw the actual Playing Field:
  2.1 1000x1000 Window:
```
FIELD_SIZE = 1000
TILE_SIZE = 10

class drawFinishedBoard(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # setting up Window
        self.setGeometry(0, 0, FIELD_SIZE, FIELD_SIZE)
        self.setWindowTitle('Game')
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawGrid(qp)
        self.drawObstacles(qp)
        self.drawRobot(Robot.TestRobot, qp)
        qp.end()
```
  2.2 Draw BlackSquares for Wall pieces:
  
```
    def drawObstacles(self, qp):

        # setting Wallcolor
        qp.setBrush(Qt.black)

        # creating the array
        # its size depends on FIELD_SIZE and TILE_SIZE
        arraysize = int(FIELD_SIZE / TILE_SIZE)
        obstacleArray = PlayingField.setupArray(PlayingField, arraysize)

        # painting a wallpiece when there is a 1 in the array
        for row in range(arraysize):
            for col in range(arraysize):
                if obstacleArray[row][col] == 1:
                    qp.drawRect(row * TILE_SIZE, col * TILE_SIZE, TILE_SIZE, TILE_SIZE)
```
3. Setting up a class for the Robot to store his Position, Size and direction
  
```
class Robot:

    def __init__(self, x, y, radius, alpha):
        self.x = x
        self.y = y
        self.radius = radius
        self.alpha = alpha
        self.position = [x, y]


TestRobot = Robot(10, 20, 10, 765)
```

4. drawing the Robot (in class drawFinishedBoard):
  4.1 drawing circle at the right Position
```
    def drawRobot(self, Robot, qp):
        
        # setting circle color and transparency
        qp.setBrush(QColor(133, 242, 252, 100))
        # calculating center point of the circle
        center = QPoint(Robot.x * TILE_SIZE, Robot.y * TILE_SIZE)
        # drawing the circle with the position and radius of the Robot
        qp.drawEllipse(center, Robot.radius, Robot.radius)
```
  4.2 marking the center of the Robot
```
        # setting center color
        qp.setBrush(Qt.white)
        # drawing small circle
        qp.drawEllipse(center, 2, 2)
```
  4.3 drawing the Line that indicates the direction
```
        # calculating the point to draw the line that indicates alpha
        radian = ((Robot.alpha - 90) / 180 * math.pi)
        direction = QPoint(math.cos(radian) * Robot.radius + QPoint.x(center), math.sin(radian) * Robot.radius + QPoint.y(center))
        # setting color of directional line
        qp.setPen(QPen(Qt.red, .8))
        qp.drawLine(QPoint.x(center), QPoint.y(center), QPoint.x(direction), QPoint.y(direction))
```
