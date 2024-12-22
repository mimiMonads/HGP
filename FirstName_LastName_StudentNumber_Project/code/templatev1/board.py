# board.py
from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont
from game_logic import GameLogic

class Board(QFrame):
    # Existing signals
    updateTimerSignal = pyqtSignal(int)   # Signal for countdown
    clickLocationSignal = pyqtSignal(str) # Signal for click location

    # Board size & timer
    boardWidth = 7
    boardHeight = 7
    timerSpeed = 1000  # 1 second
    counter = 60       # example countdown

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initBoard()
        self.setMinimumSize(200, 200)
        
        # Store the scoreboard info locally for drawing on the board
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
        # Connect game logic signals to local handlers
        self.gameLogic.currentPlayerChangedSignal.connect(self.onCurrentPlayerChanged)
        self.gameLogic.capturesUpdatedSignal.connect(self.onCapturesUpdated)
        self.gameLogic.territoryUpdatedSignal.connect(self.onTerritoryUpdated)
        self.gameLogic.gameOverSignal.connect(self.onGameOver)

        self.start()

    def start(self):
        """Start the game: reset state, start timer, etc."""
        self.isStarted = True
        self.resetGame()
        self.timer.start(self.timerSpeed, self)
        print("Game started.")

    def timerEvent(self, event):
        """Timer countdown logic."""
        if event.timerId() == self.timer.timerId():
            if self.counter == 0:
                print("Time's up! (Example behavior - game over or switch player, etc.)")
                self.timer.stop()
            else:
                self.counter -= 1
                self.updateTimerSignal.emit(self.counter)
        else:
            super(Board, self).timerEvent(event)

    def paintEvent(self, event):
        """Draw the board and all stones, plus overlay scoreboard text."""
        painter = QPainter(self)

        # 1) Board background and grid
        self.drawBackground(painter)
        self.drawBoardSquares(painter)

        # 2) Stones
        self.gameLogic.drawPieces(
            painter,
            self.squareWidth(),
            self.squareHeight(),
            self.width(),
            self.height()
        )

        # 3) Overlay text for current player, captures, and territory
        self.drawScoreOverlay(painter)

    def drawBackground(self, painter):
        painter.fillRect(self.rect(), QColor(139, 69, 19))  # Brown

    def drawBoardSquares(self, painter):
        """Draw grid lines for the board."""
        painter.setPen(Qt.GlobalColor.black)
        square_size = self.squareWidth()
        offsetX = (self.width() - square_size * self.boardWidth) / 2
        offsetY = (self.height() - square_size * self.boardHeight) / 2

        for row in range(self.boardHeight):
            for col in range(self.boardWidth):
                left = int(offsetX + col * square_size)
                top = int(offsetY + row * square_size)
                painter.drawRect(left, top, int(square_size), int(square_size))

    def drawScoreOverlay(self, painter):
        """
        Draw current player, captures, and territory in one corner of the board.
        Adjust position/color/font to your preference.
        """
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        # Build a multi-line string for convenience
        scoreboard_text = (
            f"Current: {self.currentPlayer}\n"
            f"B caps: {self.blackCaptures}, W caps: {self.whiteCaptures}\n"
            f"B terr: {self.blackTerritory}, W terr: {self.whiteTerritory}"
        )

        # Draw near the top-left corner with some padding
        x_pos = 10
        y_pos = 20
        line_height = 18  # approx spacing between lines

        for i, line in enumerate(scoreboard_text.split("\n")):
            painter.drawText(x_pos, y_pos + i * line_height, line)

    def mousePressEvent(self, event):
        """Handle a click on the board."""
        if not self.isStarted:
            return

        x, y = event.position().x(), event.position().y()
        offsetX = (self.width() - self.squareWidth() * self.boardWidth) / 2
        offsetY = (self.height() - self.squareHeight() * self.boardHeight) / 2

        col = int((x - offsetX) / self.squareWidth())
        row = int((y - offsetY) / self.squareHeight())

        if 0 <= row < self.boardHeight and 0 <= col < self.boardWidth:
            clickLoc = f"[{col}, {row}]"
            self.clickLocationSignal.emit(clickLoc)  # e.g. "Click location: [col, row]"
            print(f"Clicked on {clickLoc}")
            # Pass move to game logic
            self.gameLogic.handleMove(row, col)
            self.update()

    def passMove(self):
        """Handle a pass move from the scoreboard."""
        if not self.isStarted:
            return
        self.gameLogic.passMove()
        self.update()

    def resetGame(self):
        """Reset the game state and restart the timer."""
        self.gameLogic.resetGame()
        self.counter = 60
        self.update()

    def printBoardArray(self):
        """Utility to print the board in the console."""
        print("Board State:")
        for row in self.gameLogic.boardArray:
            print(" ".join(['.' if cell is None else str(cell) for cell in row]))

    def squareWidth(self):
        return min(self.width(), self.height()) / self.boardWidth

    def squareHeight(self):
        return self.squareWidth()  # Keep squares symmetric

    # ---------------------------------------------------------------------
    # Slots from GameLogic signals
    # ---------------------------------------------------------------------
    def onCurrentPlayerChanged(self, player):
        """
        e.g. "Black" or "White".
        Update local variable and print to console.
        """
        self.currentPlayer = player
        print(f"Current player changed: {player}")
        self.update()

    def onCapturesUpdated(self, blackCaptures, whiteCaptures):
        """Store and print updated captures."""
        self.blackCaptures = blackCaptures
        self.whiteCaptures = whiteCaptures
        print(f"Captures updated -> Black: {blackCaptures}, White: {whiteCaptures}")
        self.update()

    def onTerritoryUpdated(self, blackTerr, whiteTerr):
        """Store and print updated territory."""
        self.blackTerritory = blackTerr
        self.whiteTerritory = whiteTerr
        print(f"Territory updated -> Black: {blackTerr}, White: {whiteTerr}")
        self.update()

    def onGameOver(self, resultMsg):
        """Handle the game over signal."""
        print(resultMsg)
        self.isStarted = False
        self.timer.stop()
        self.update()  # final update so overlay is current

