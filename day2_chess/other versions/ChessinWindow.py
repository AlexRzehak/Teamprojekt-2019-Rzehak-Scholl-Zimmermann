from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QBrush
import sys



class Chess(QWidget):


    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(200, 0, sidelen, sidelen)
        self.setWindowTitle('Colours')
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawBoard(qp)
        qp.end()

    def drawBoard(self, qp):
        col = QColor(0, 0, 0)
        qp.setPen(col)
        qp.setBrush(QColor(0, 0, 0))

        for row in range(8):
            for col in range(4):
                if row % 2 == 0:
                    qp.drawRect(row * (sidelen/8),
                                (col * (sidelen/4)) + (sidelen/8),
                                (sidelen/8), (sidelen/8))
                else:
                    qp.drawRect(row * (sidelen/8),
                                (col * (sidelen/4)),
                                (sidelen/8), (sidelen/8))


if __name__ == '__main__':
    sidelen = int(input("Please type a desired sidelength for your Chessboard:"))
    app = QApplication(sys.argv)
    ex = Chess()
    sys.exit(app.exec_())