import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QBrush


class Chess(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        # we need a window of size 1000 x 1000 for this task
        # since most screens nowadays have 1920x1080 resolution,
        # we choose the y-offset to be 40
        self.setGeometry(300, 40, 1000, 1000)
        self.setWindowTitle('Chess')
        self.show()

    # The paintEvent will call the drawBoard() method,
    # that draws the board using a QPainter() instance.
    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawBoard(qp)
        qp.end()

    def drawBoard(self, qp):

        # define size and offset of the chess board. should be multiple of 8.
        # this could be done at a previous step but since for this task the
        # values are fix, we choose to define the parameters at this point.
        size = 968
        offset = 16
        tileSize = size/8

        # we vectors of x and y positions for the topleft corner of the
        # black squares of the board.
        # there are two different vectors needed: one with additional
        # offset of one tile size and one without.
        vec1 = [offset + 2 * tileSize * a for a in range(4)]
        vec2 = [tileSize + a for a in vec1]

        # we now need all possible combinations of those two vectors.
        # since we will manually invert the order of the tuples later,
        # we need each combination only one time
        vecZip = [(a, b) for a in vec1 for b in vec2]

        # we get us a white brush and paint the white background of the board
        # nothing to see here
        qp.setBrush(QColor(255, 255, 255))
        qp.drawRect(offset, offset, size, size)

        # since we don't want the black tiles to have additional borders,
        # we need to disable the pen
        qp.setPen(Qt.NoPen)
        qp.setBrush(QColor(0, 0, 0))

        # now we draw the black tiles using the coordinate vector
        # we set up above
        # to get all possible combinations, we need to paint two tiles
        # each time: one with the reversed coordinates for x and y
        for a, b in vecZip:
            qp.drawRect(a, b, tileSize, tileSize)
            qp.drawRect(b, a, tileSize, tileSize)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    ch = Chess()
    sys.exit(app.exec_())
