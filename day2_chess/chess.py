import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QBrush, QIcon

WSIZE = int(input("Please type your desired size of the Window: "))
OFFSET = int(input("How wide do you want the border?  "))


class Chess(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        # here the initially set size if the window gets used
        # since the default window size for this task is 1000 x 1000
        # and most screens nowadays have 1920x1080 resolution,
        # we choose the y-offset to be 40
        self.setGeometry(300, 40, WSIZE, WSIZE)
        self.setWindowTitle('Chess')
        self.setWindowIcon(QIcon('web.png'))
        self.show()

    # The paintEvent will call the drawBoard() method,
    # that draws the board using a QPainter() instance.
    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawBoard(qp)
        qp.end()

    def drawBoard(self, qp):

        # compute the size of the actual Chessboard
        chessSize = WSIZE - 2 * OFFSET
        tileSize = chessSize/8

        # we vectors of x and y positions for the topleft corner of the
        # black squares of the board.
        # there are two different vectors needed: one with additional
        # offset of one tile size and one without.
        vec1 = [OFFSET + 2 * tileSize * a for a in range(4)]
        vec2 = [tileSize + a for a in vec1]

        # we now need all possible combinations of those two vectors.
        # since we will manually invert the order of the tuples later,
        # we need each combination only one time
        vecZip = [(a, b) for a in vec1 for b in vec2]

        # we get us a white brush and paint the white background of the board
        # nothing to see here
        qp.setBrush(QColor(255, 255, 255))
        qp.drawRect(OFFSET, OFFSET, chessSize, chessSize)

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
