from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt
import sys


class Chessboard(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Chessboard')
        self.resize(1000, 1000)
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawBoard(qp)
        qp.end()

    def drawSquare(self, qp, x, y):

        # paints a black rectangle at a given coordinate
        # this coordinate represents the to left corner
        qp.setPen(Qt.black)
        square_width = self.width() / 8.
        qp.fillRect(x, y, square_width, square_width, Qt.black)


    def drawBoard(self, qp):

        # paints the 2,4,6,8th row
        # outer loop: resets x coordinate to 0 , recalculates y for the next row
        # inner loop: draws square, adjusts x coordinate for the next Square
        x = 0
        square_width = self.width() / 8.
        y = square_width
        for Row in range(4):
            for Col in range(4):
                self.drawSquare(qp, x, y)
                x = x + (2 * square_width)
            x = 0
            y = y + (2 * square_width)

        # paints the 1,3,5,7th row
        # resets x and y  coordinates
        # outer loop: resets x coordinate to 0 , recalculates y for the next row
        # inner loop: draws square with offset coordinates for the chess board pattern
        # adjusts x coordinate for the next Square
        x = 0
        y = square_width
        for Row in range(4):
            for Col in range(4):
                self.drawSquare(qp, x + square_width, y - square_width)
                x = x + (2 * square_width)
            x = 0
            y = y + (2 * square_width)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    cb = Chessboard()
    sys.exit(app.exec_())