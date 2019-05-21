# Week 3: Create a Playing Field and a Robot

### [<- Back](/index.md) to project overview.

Let's define some constant values first:
```python
FIELD_SIZE = 1000
TILE_SIZE = 10
```

## Task 1
### Create a Class that represents the board and set up a 100x100 array to represent potential obstacles:
```python
class Board(QWidget):

    def __init__(self):
        super().__init__()

        self.obstacleArray = Board.setupArray(100)
        self.initUI()

    @staticmethod
    def setupArray(arraysize):
        obstacleArray = [[0 for col in range(arraysize)] for row in range(arraysize)]

        #setting the sidewalls by setting all the first and last Elements of each row and column to 1
        for x in range(arraysize):
            obstacleArray[x][0] = 1
            obstacleArray[x][arraysize - 1] = 1
            obstacleArray[0][x] = 1
            obstacleArray[arraysize - 1][x] = 1

        #individual Wall tiles:
        obstacleArray[28][34] = 1
        obstacleArray[54][43] = 1
        obstacleArray[0][49] = 0

        return obstacleArray
```

## Problem?
### Where to put the setup of the window?
```python
class Board(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
    #setting up Window
    self.setGeometry(0, 0, FIELD_SIZE, FIELD_SIZE)
    self.setWindowTitle('Game')
    self.show()
```

## Solution!
### Separate functions of the window from functions of the board!
```python
class Game(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.board = Board(self)

        self.setCentralWidget(self.board)
        self.setGeometry(300, 40, FIELD_SIZE, FIELD_SIZE)
        self.setWindowTitle('RobotGame')
        self.show()


class Board(QWidget):

    TileCount = int(FIELD_SIZE / TILE_SIZE)

    def __init__(self, parent):
        super().__init__(parent)

        self.obstacleArray = Board.setupArray(Board.TileCount)
``` 

## Task 2
### Draw the board!
We reimplement the `paintEvent` and seperate a `drawGrid` function and a `drawObstacles` function:
```python
def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawGrid(qp)
        self.drawObstacles(qp)
        qp.end()

def drawGrid(self, qp):

    # painting a grid to showcase the tiles
    # using the constants TILE_SIZE and FIELD_SIZE to determine the size
    pen = QPen(Qt.black, .1, Qt.SolidLine)
    qp.setPen(pen)
    # horizontal lines
    for horizontal in range(0, FIELD_SIZE, TILE_SIZE):
        qp.drawLine(0, horizontal, FIELD_SIZE, horizontal)

    # vertical lines
    for vertical in range(0, FIELD_SIZE, TILE_SIZE):
        qp.drawLine(vertical, 0, vertical, FIELD_SIZE)

def drawObstacles(self, qp):
        
    #setting Wallcolor
    qp.setBrush(Qt.black)

    for xpos in range(Board.TileCount):
        for ypos in range(Board.TileCount):
            if self.obstacleArray[xpos][ypos] == 1:
                qp.drawRect(xpos*TILE_SIZE, ypos*TILE_SIZE, TILE_SIZE, TILE_SIZE)
```

## Task 3
### Set up a class for the robot to store its position (x,y), radius and direction as class attributes.
```python
class BaseRobot():

    def __init__(self, x, y, radius, alpha):

        self.x = x
        self.y = y
        self.radius = radius
        self.alpha = alpha

    # with this we can create an example robot for further use
    @staticmethod
    def createExampleRobot(boardSize: int, tileSize: int):

        return BaseRobot(1, 1, tileSize/2, 45)
```

## Problem?
### How to draw the robot on the battlefield?
We create an additional function `drawRobot`. But where to put the robot?
```python
    ROBOT = '???'

    def drawRobot(self, qp):

        # setting circle color and transparency
        qp.setBrush(QColor(133, 242, 252, 100))
        # calculating center point of the circle
        center = QPoint(ROBOT.x * TILE_SIZE + 0.5 * TILE_SIZE,
                        ROBOT.y * TILE_SIZE + 0.5 * TILE_SIZE)
        # drawing the circle with the position and radius of the Robot
        qp.drawEllipse(center, ROBOT.radius, ROBOT.radius)

        # calculating the point to draw the line that indicates alpha
        radian = ((ROBOT.alpha - 90) / 180 * math.pi)
        direction = QPoint(math.cos(radian) * ROBOT.radius + QPoint.x(center),
                           math.sin(radian) * ROBOT.radius + QPoint.y(center))
        # setting color of directional line
        qp.setPen(Qt.red)
        qp.drawLine(QPoint.x(center), QPoint.y(center),
                    QPoint.x(direction), QPoint.y(direction))

        # marking center point
        # setting center color
        qp.setBrush(Qt.white)
        # drawing small circle
        qp.drawEllipse(center, 2, 2)
```

## Solution!
### Add a robot as attribute to the board!
```python
class Board(QWidget):

    TileCount = int(FIELD_SIZE / TILE_SIZE)

    def __init__(self, parent):
        super().__init__(parent)

        self.obstacleArray = Board.setupArray(Board.TileCount)
        self.robot = BaseRobot.createExampleRobot(Board.TileCount, TILE_SIZE)

    def drawRobot(self, qp):

        rb = self.robot
        # [...]
```

## Task 4
### Set up a timer to move the robot around the battlefield.
Our robot now needs to _move_. We choose to implement a function, that will move the robot by one tile in the given direction:
```python
class BaseRobot():

    def moveStep(self, direction: str):

        # don't forget to turn the robot!
        if direction == 'north':
            self.y = self.y - 1
            self.alpha = 0

        elif direction == 'south':
            self.y = self.y + 1
            self.alpha = 180

        elif direction == 'east':
            self.x = self.x + 1
            self.alpha = 90

        elif direction == 'west':
            self.x = self.x - 1
            self.alpha = 270
```

## Problem?
### How to use a timer to move the robot?
We use a `QBasicTimer` and need to reimplement the `timerEvent`:
```python
class Board(QWidget):

    RefreshSpeed = 200

    def __init__(self, parent):
        super().__init__(parent)

        self.timer = QBasicTimer()
        self.timer.start(Board.RefreshSpeed, self)
        # [...]
    
    def timerEvent(self, event):
        # TODO
        pass
```


## Solution 1!
### Static movement.
```python
def timerEvent(self, event):

        # simple movement command
        # TODO should be re-implemented to avoid working
        # directly with the robots coordinates
        if not self.robot.x >= 98:
            self.robot.moveStep('east')
        elif not self.robot.y >= 98:
            self.robot.moveStep('south')

        # update visuals
        self.update()
```
## Subproblem: `moveStep`
### Let's take a closer look at `moveStep` again. This function can be improved in many ways!
```python
class BaseRobot():

    def moveStep(self, direction: str):

        # don't forget to turn the robot!
        if direction == 'north':
            self.y = self.y - 1
            self.alpha = 0

        elif direction == 'south':
            self.y = self.y + 1
            self.alpha = 180

        elif direction == 'east':
            self.x = self.x + 1
            self.alpha = 90

        elif direction == 'west':
            self.x = self.x - 1
            self.alpha = 270
```
First, it would be possible for our robot to 'walk off' the board!<br/>
Looking towards a proper implementation of obstacles, we need to add  a function `checkStep` to the board:
```python
    def checkStep(self, direction: str):
        # we get parameters from the robot
        rbx = self.robot.x
        rby = self.robot.y

        # only move, if the field in the desired direction is available!
        if direction == 'north':
            if rby - 1 > 0:
                self.robot.place(rbx, rby - 1, 'north')
            else:
                self.robot.place(rbx, rby, 'north')

        elif direction == 'south':
            if rby + 1 < Board.TileCount - 1:
                self.robot.place(rbx, rby + 1, 'south')
            else:
                self.robot.place(rbx, rby, 'south')

        elif direction == 'east':
            if rbx + 1 < Board.TileCount - 1:
                self.robot.place(rbx + 1, rby, 'east')
            else:
                self.robot.place(rbx, rby, 'east')

        elif direction == 'west':
            if rbx - 1 > 0:
                self.robot.place(rbx - 1, rby, 'west')
            else:
                self.robot.place(rbx, rby, 'west')
```
## But now a lot of code is a duplicate!

## Solution `moveStep`:
### We map the directions to changes of (x, y)-coordinates!
We can combine both functions!
```python
    def moveStep(self, direction: str):

        directions = dict(north=(0, -1, 0),
                          south=(0, 1, 180),
                          east=(1, 0, 90),
                          west=(-1, 0, 270))

        x_add, y_add, new_alpha = directions[direction]
        new_x = self.robot.x + x_add
        new_y = self.robot.y + y_add

        # don't forget to turn the robot
        self.robot.alpha = new_alpha

        if (Board.field_is_valid(new_x, new_y)):
            self.robot.x = new_x
            self.robot.y = new_y

    @staticmethod
    def field_is_valid(xpos, ypos):
        # [...]
```
# Additional Features

## Solution 2!
### Mouse control.
The robot should notice a click on the board an move to the cursor. We need a `mousePressEvent`:
```python
class Board(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        # We need to enable input via devices for the widget.
        self.setFocusPolicy(Qt.StrongFocus)

        # [...]
    
    def mousePressEvent(self, event):
        # calculate the position of the click
        mouseX = int((event.x()) / TILE_SIZE)
        mouseY = int((event.y()) / TILE_SIZE)
        dx = self.robot.x - mouseX
        dy = self.robot.y - mouseY

        # TODO
        self.do_the_thing(dx, dy)
```
## Subproblem: Routing
### The robot now needs the ability to determine a way to the clicked position. Then, it should move along that way step by step (given by the timer).
```python
    def timerEvent(self, event):

        # TODO
        self.do_the_next_robot_step()

        # update visuals
        self.update()
```

## Solution: Routing
### Since we don't want to use complex routing algorithms yet, we simply chose to move the robot in the direction of the cursor.
If we click diagonal, the robot will move on the axis with the further distance!
### The cobot will store the information of the click as a _command_.
This command consists of the clicked direction and a count of steps the robot needs to perform to reach its destination.
```python
class BaseRobot():

    def __init__(self, x, y, radius, alpha):

        # the current command executed by the robot
        self.command = ('stay', 0)

        # [...]


class Board(QWidget):

    def mousePressEvent(self, event):
        mouseX = int((event.x()) / TILE_SIZE)
        mouseY = int((event.y()) / TILE_SIZE)
        dx = self.robot.x - mouseX
        dy = self.robot.y - mouseY

        # determine the direction
        if abs(dx) > abs(dy):
            if dx > 0:
                self.robot.command = ('west', abs(dx))
            else:
                self.robot.command = ('east', abs(dx))
        else:
            if dy > 0:
                self.robot.command = ('north', abs(dy))
            else:
                self.robot.command = ('south', abs(dy))

    def followCommand(self):
        direction, distance = self.robot.command

        if distance:
            self.moveStep(direction)
            # make sure to count down the number of steps to perform
            self.robot.command = (direction, distance - 1)

    
    def timerEvent(self, event):
        
        # now call the followCommand function to perform one step
        self.robot.followCommand(self.obstacleArray)

        # update visuals
        self.update()
```

## Obstacles
### We want to distinguish more different kinds of board hazards!
Since Walls are represented by a number 1 in the `obstacleArray`, the other hazards could be the next bigger integers.
```python
@staticmethod
    def createExampleArray(size: int):

        array = [[0] * size for row in range(size)]

        # setting the sidewalls by setting all the first and last Elements
        # of each row and column to 1
        for x in range(size):
            array[x][0] = 2
            array[x][size - 1] = 2
            array[0][x] = 2
            array[size - 1][x] = 2

        # individual Wall tiles:
        array[28][34] = 1
        array[54][43] = 1
        array[5][49] = 3
        array[0][30] = 0
        array[99][30] = 0

return array
```

## Subproblem: Identification of board hazards.
### We might want to handle the hazards at more than one point in the program.
The implementation should consider extensibility!
```python
# 0 = Empty Tile
# 1 = Wall
# 2 = Border
# 3 = Hole
```

## Solution: Identification of board hazards.
### We use a namespace class.
That way, we might add basic functionalities to the class later! We can now use at any point of the code the identifier `Hazard.Wall`, if we mean a wall.
```python
class Hazard():
    Empty = 0
    Wall = 1
    Border = 2
    Hole = 3
```

### Let's update the drawObstacles function to paint the different hazard types:
```python
def drawObstacles(self, qp):
        for xpos in range(Board.TileCount):
            for ypos in range(Board.TileCount):

                tileVal = self.obstacleArray[xpos][ypos]

                # still no need to redraw an empty tile!

                # we use a bit prettier visuals
                if tileVal == Hazard.Wall:
                    brush = QBrush(Qt.Dense2Pattern)
                    brush.setColor(Qt.red)
                    qp.setBrush(brush)
                    qp.drawRect(xpos * TILE_SIZE,
                                ypos * TILE_SIZE,
                                TILE_SIZE, TILE_SIZE)

                elif tileVal == Hazard.Border:
                    brush = QBrush(Qt.Dense2Pattern)
                    brush.setColor(Qt.blue)
                    qp.setBrush(brush)
                    qp.drawRect(xpos * TILE_SIZE,
                                ypos * TILE_SIZE,
                                TILE_SIZE, TILE_SIZE)

                elif tileVal == Hazard.Hole:
                    qp.setBrush(Qt.black)
                    center = QPoint(xpos * TILE_SIZE + 0.5 * TILE_SIZE,
                                    ypos * TILE_SIZE + 0.5 * TILE_SIZE)
                    qp.drawEllipse(center, 0.5 * TILE_SIZE, 0.25 * TILE_SIZE)
```

## Subproblem: Interact with the hazards.
### If we want to interact with our hazards, we need to check the next field before entering it. Else we would walk into a wall.
We have a spot for this kind of functionality in our `moveStep` function:
```python
class Board(QWidget):

    def moveStep(self, direction: str):

        directions = dict(north=(0, -1, 0),
                          south=(0, 1, 180),
                          east=(1, 0, 90),
                          west=(-1, 0, 270))

        # We work directly with attributes of the robot!
        x_add, y_add, new_alpha = directions[direction]
        new_x = self.robot.x + x_add
        new_y = self.robot.y + y_add

        # don't forget to turn the robot
        self.robot.alpha = new_alpha

        self.handle_next_tile(new_x, new_y)

    # This should not be placed here!
    def handle_next_tile(self, xpos, ypos):
        # we need the obstacleArray!
        tileType = self.obstacleArray[xpos][ypos]

        # TODO

```
On one hand, we logically work directly with features and traits of the robot (like its coordinates). On the other hand, we need the information of the `obstacleArray` to resolve the interactions with the hazards correctly.

## Solution: Interact with hazards
### We move the stepping functionality to the `BaseRobot` class. To resolve interactions correctly, we pass the `obstacleArray` as an additional argument.
```python
class BaseRobot():

    def __init__(self, x, y, radius, alpha):

        self.x = x
        self.y = y
        self.radius = radius
        self.alpha = alpha
        self.command = ('stay', 0)

    # We get the obstacleArray as additional argument!
    def moveStep(self, direction: str, obstacleArray):

        directions = dict(north=(0, -1, 0),
                          south=(0, 1, 180),
                          east=(1, 0, 90),
                          west=(-1, 0, 270))

        x_add, y_add, new_alpha = directions[direction]
        new_x, new_y = self.x + x_add, self.y + y_add

        # now that we have borders, what happens if borders are missing?
        new_x, new_y = new_x % Board.TileCount, new_y % Board.TileCount

        tileVal = obstacleArray[new_x][new_y]

        if tileVal == Hazard.Empty:
            self.x = new_x
            self.y = new_y

        # explicit to show the different hazard types.
        elif tileVal == Hazard.Wall:
            pass

        elif tileVal == Hazard.Border:
            pass

        # this hole will respawn you at the topleft position.
        elif tileVal == Hazard.Hole:
            self.x = 1
            self.y = 1

        self.alpha = new_alpha
```

We now need to adapt all occurences of `moveStep` to match the improved definition.
```python
class Board():

        def timerEvent(self, event):

        self.robot.followCommand(self.obstacleArray)

        # update visuals
        self.update()

class BaseRobot():

    def followCommand(self, obstacleArray):
        direction, distance = self.command

        if distance:
            self.moveStep(direction, obstacleArray)
            self.command = (direction, distance - 1)
```
This distribution makes way more sense!

# Let's go and bully some robot around!