# Week 7: Give Guns to the Robots

### [<- Back](/index.md) to project overview.

# Task: Implement Textures
## Static Textures
```python
def drawObstacles(self, qp):
    for xpos in range(Board.TileCount):
        for ypos in range(Board.TileCount):
            tileVal = self.obstacleArray[xpos][ypos]
            if tileVal == Hazard.Wall:
                texture = QPixmap("textures/wall.png")
                qp.save()
                source = QRectF(0, 0, 10, 10)
                target = QRectF(xpos * TILE_SIZE, ypos *
                                TILE_SIZE, TILE_SIZE, TILE_SIZE)
                qp.drawPixmap(target, texture, source)
                qp.restore()
...
```

### Texture is a Pixelmap of the Image. Source defines the area which is used of the texture. Target is the Rectangle (including coordinates) which the texture should fill. Then we draw.

## Robot Textures
### Displaying Robot Alpha
```python
qp.translate(robot.x, robot.y)
qp.rotate(robot.alpha)
source = QRectF(0, 0, 567, 566)
target = QRectF(-robot.radius, -robot.radius,
                2 * robot.radius, 2 * robot.radius)
# drawing the robot
qp.setOpacity(robot_op)
qp.drawPixmap(target, texture, source)
```
We set the center around which the Image is rotated to the robots coordinates.
Now we can rotate it by the alpha to display the robot correctly.

### Health and Status display
```python
robot_op = 1
overlay_op = 1
if robot.dead or robot.immune:
    robot_op = 0.7
overlay = QRectF(robot.x - robot.radius, robot.y - robot.radius, 2 * robot.radius, 2 * robot.radius)

if robot.immune:
    R = 0
    G = 0
    B = 255
    A = 100
elif not robot.dead:
    R = 255 * (1 - life_frac)
    G = 255 * life_frac
    B = 0
    A = 255
elif robot.dead:
    R = 10
    G = 10
    B = 10
    A = 255
qp.setBrush(QColor(R, G, B, A))
# drawing overlay
qp.setOpacity(overlay_op)
qp.drawEllipse(overlay)
```

If the robot is alive we over lay it’s texture with a Circle that is has a color to represent the amount of health, creating a fluid transition between green and red. 
If it is dead or immune set the robots opacity below 1 so it becomes slightly transparent. Now we can grey out the whole robot when dead or make it transparent blue while immune.

