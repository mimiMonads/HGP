# board.py
from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor
from game_logic import GameLogic

class Board(QFrame):
    updateTimerSignal = pyqtSignal(int)  # Signal sent when the timer is updated
    clickLocationSignal = pyqtSignal(str)  # Signal sent on new click location

    boardWidth = 7  # Adjust for a 7x7 board
    boardHeight = 7
    timerSpeed = 1000  # Timer updates every 1000 milliseconds (1 second)
    counter = 60  # Example counter for game timing

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initBoard()
        self.setMinimumSize(200, 200)  # Ensure the board is at least 200x200 pixels

    def initBoard(self):
        """Initialize the board."""
        self.timer = QBasicTimer()
        self.isStarted = False
        self.gameLogic = GameLogic(self.boardWidth, self.boardHeight)
        self.start()

    def printBoardArray(self):
        """Print the boardArray in an attractive way."""
        print("Board State:")
        for row in self.gameLogic.boardArray:
            print(" ".join(['.' if cell is None else str(cell) for cell in row]))

    def squareWidth(self):
        """Return the width of one square in the board."""
        return min(self.width(), self.height()) / self.boardWidth

    def squareHeight(self):
        """Return the height of one square on the board."""
        return self.squareWidth()  # Ensure squares remain square

    def start(self):
        """Start the game."""
        self.isStarted = True
        self.resetGame()
        self.timer.start(self.timerSpeed, self)
        print("Game started.")

    def timerEvent(self, event):
        """Handle timer events."""
        if event.timerId() == self.timer.timerId():
            if self.counter == 0:
                print("Game over")
                self.timer.stop()
            else:
                self.counter -= 1
                print(f"Timer Event: {self.counter}")
                self.updateTimerSignal.emit(self.counter)
        else:
            super(Board, self).timerEvent(event)

    def paintEvent(self, event):
        """Paint the board and pieces."""
        painter = QPainter(self)
        self.drawBackground(painter)
        self.drawBoardSquares(painter)
        self.gameLogic.drawPieces(painter, self.squareWidth(), self.squareHeight(), self.width(), self.height())

    def drawBackground(self, painter):
        """Draw the background color of the board area."""
        painter.fillRect(self.rect(), QColor(139, 69, 19))  # Brown background

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        x, y = event.position().x(), event.position().y()
        offsetX = (self.width() - self.squareWidth() * self.boardWidth) / 2
        offsetY = (self.height() - self.squareHeight() * self.boardHeight) / 2

        col = int((x - offsetX) / self.squareWidth())
        row = int((y - offsetY) / self.squareHeight())
        clickLoc = f"Click location: [{col}, {row}]"
        print(clickLoc)
        self.clickLocationSignal.emit(clickLoc)

        self.gameLogic.handleMove(row, col)
        self.update()

    def resetGame(self):
        """Reset the game state."""
        self.gameLogic.resetGame()
        self.counter = 60
        print("Game reset.")

    def drawBoardSquares(self, painter):
        """Draw the squares of the board."""
        painter.setPen(Qt.GlobalColor.black)
        square_size = self.squareWidth()  # Ensure square size is uniform
        offsetX = (self.width() - self.squareWidth() * self.boardWidth) / 2
        offsetY = (self.height() - self.squareHeight() * self.boardHeight) / 2

        for row in range(self.boardHeight):
            for col in range(self.boardWidth):
                left = int(offsetX + col * square_size)
                top = int(offsetY + row * square_size)
                painter.drawRect(left, top, int(square_size), int(square_size))
