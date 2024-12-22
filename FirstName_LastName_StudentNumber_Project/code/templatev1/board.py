# board.py

from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont
from game_logic import GameLogic

class Board(QFrame):
    # Signals for scoreboard
    updateTimerSignal = pyqtSignal(int)   # countdown updates
    clickLocationSignal = pyqtSignal(str) # "[2, 3]"
    infoMessageSignal  = pyqtSignal(str)  # game/log messages

    # Board size & timer
    boardWidth = 7
    boardHeight = 7
    timerSpeed = 1000  # 1 second
    counter = 60       # example countdown

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initBoard()
        self.setMinimumSize(200, 200)

        # Variables to store scoreboard data
        self.currentPlayer = "Black"
        self.blackCaptures = 0
        self.whiteCaptures = 0
        self.blackTerritory = 0
        self.whiteTerritory = 0

    def initBoard(self):
        """Initialize the board logic & timer."""
        self.timer = QBasicTimer()
        self.isStarted = False

        # Initialize game logic
        self.gameLogic = GameLogic(self.boardWidth, self.boardHeight, parent=self)

        # Connect signals
        self.gameLogic.currentPlayerChangedSignal.connect(self.onCurrentPlayerChanged)
        self.gameLogic.capturesUpdatedSignal.connect(self.onCapturesUpdated)
        self.gameLogic.territoryUpdatedSignal.connect(self.onTerritoryUpdated)
        self.gameLogic.gameOverSignal.connect(self.onGameOver)

        self.start()

    def start(self):
        """Start/restart the game."""
        self.isStarted = True
        self.resetGame()
        self.timer.start(self.timerSpeed, self)
        self.infoMessageSignal.emit("Game started.")

    def timerEvent(self, event):
        """Simple countdown timer logic with time-up => forced game over."""
        if event.timerId() == self.timer.timerId():
            if self.counter == 0:
                # Time is up -> Determine a winner quickly

                if self.currentPlayer == "Black":
                    winner = "White"
                else:
                    winner = "Black"

                msg = f"Time's up! {winner} wins on time."
                self.infoMessageSignal.emit(msg)
                
                # Stop the timer and trigger game over
                self.isStarted = False
                self.timer.stop()
                # We can emit the 'gameOverSignal'
                self.gameLogic.gameOverSignal.emit(msg)

            else:
                self.counter -= 1
                self.updateTimerSignal.emit(self.counter)
        else:
            super(Board, self).timerEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        self.drawBackground(painter)
        self.drawBoardSquares(painter)

        self.gameLogic.drawPieces(
            painter,
            self.squareWidth(),
            self.squareHeight(),
            self.width(),
            self.height()
        )

    def drawBackground(self, painter):
        painter.fillRect(self.rect(), QColor(139, 69, 19))  # Brownish background

    def drawBoardSquares(self, painter):
        """
        Draw the 7x7
        """
        painter.setPen(Qt.GlobalColor.black)
        square_size = self.squareWidth()
        offsetX = (self.width() - square_size * self.boardWidth) / 2
        offsetY = (self.height() - square_size * self.boardHeight) / 2

        for row in range(self.boardHeight):
            for col in range(self.boardWidth):
                left = int(offsetX + col * square_size)
                top = int(offsetY + row * square_size)
                painter.drawRect(left, top, int(square_size), int(square_size))

    def mousePressEvent(self, event):
        """
        Handle board clicks
        """
        if not self.isStarted:
            return

        x, y = event.position().x(), event.position().y()
        offsetX = (self.width() - self.squareWidth() * self.boardWidth) / 2
        offsetY = (self.height() - self.squareHeight() * self.boardHeight) / 2

        col = int((x - offsetX) / self.squareWidth())
        row = int((y - offsetY) / self.squareHeight())
        if 0 <= row < self.boardHeight and 0 <= col < self.boardWidth:
            clickLoc = f"[{col}, {row}]"
            self.clickLocationSignal.emit(clickLoc)
            self.infoMessageSignal.emit(f"Clicked on {clickLoc}")
            self.gameLogic.handleMove(row, col)
            self.update()

    def passMove(self):
        """
        When user clicks 'Pass'
        """
        if not self.isStarted:
            return
        self.infoMessageSignal.emit("Player passes.")
        self.gameLogic.passMove()
        self.update()

    def resetGame(self):
        """
        Reset & restart the game
        """
        self.gameLogic.resetGame()
        self.counter = 60
        self.update()
        self.infoMessageSignal.emit("Game reset.")

    # It was removed but Im keeping it just in case
    def printBoardArray(self):
        """
        Debug utility
        """
        print("Board State:")
        for row in self.gameLogic.boardArray:
            print(" ".join(['.' if cell is None else str(cell) for cell in row]))

    def squareWidth(self):
        return min(self.width(), self.height()) / self.boardWidth

    def squareHeight(self):
        return self.squareWidth()

    # -------------------- Game Logic Slots --------------------
    def onCurrentPlayerChanged(self, player):
        self.currentPlayer = player
        self.infoMessageSignal.emit(f"Current player changed to {player}")
        self.update()

    def onCapturesUpdated(self, blackCaptures, whiteCaptures):
        self.blackCaptures = blackCaptures
        self.whiteCaptures = whiteCaptures
        self.infoMessageSignal.emit(
            f"Captures => Black: {blackCaptures}, White: {whiteCaptures}"
        )
        self.update()

    def onTerritoryUpdated(self, blackTerr, whiteTerr):
        self.blackTerritory = blackTerr
        self.whiteTerritory = whiteTerr
        self.infoMessageSignal.emit(
            f"Territory => Black: {blackTerr}, White: {whiteTerr}"
        )
        self.update()

    def onGameOver(self, resultMsg):
        self.isStarted = False
        self.timer.stop()
        self.infoMessageSignal.emit(resultMsg)
        self.update()
