# score_board.py

from PyQt6.QtWidgets import (
    QDockWidget, QVBoxLayout, QWidget, QLabel,
    QGroupBox, QHBoxLayout, QPushButton, QMessageBox, QPlainTextEdit
)
from PyQt6.QtCore import pyqtSlot, Qt

class ScoreBoard(QDockWidget):
    """
    A QDockWidget that displays:
      -> Timer
      -> Current player
      -> Black/White captures, territory
      -> Stack-like log (newest on top)
      -> Pass/Reset buttons
      -> A popup on game over
    """

    def __init__(self):
        super().__init__()
        self.board = None
        # We'll keep a list of messages, with the newest at index 0
        self.logMessages = []
        self.initUI()

    def initUI(self):
        self.resize(250, 450)
        self.setWindowTitle("ScoreBoard")
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)

        self.mainWidget = QWidget()
        self.setWidget(self.mainWidget)
        self.mainLayout = QVBoxLayout(self.mainWidget)

        # STYLE UWU
        self.setStyleSheet("""
            QDockWidget {
                background-color: #2D2D2D;
                color: #EEEEEE;
                font-family: Arial;
                font-size: 14px;
            }
            QGroupBox {
                margin-top: 10px;
                border: 2px solid #888888;
                border-radius: 5px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QLabel {
                color: #DDDDDD;
            }
            QPushButton {
                background-color: #444444;
                color: #FFFFFF;
                border: 1px solid #AAAAAA;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #DDDDDD;
                border: 1px solid #555555;
            }
        """)

        # ------------------ Timer + Controls  ------------------
        topGroup = QGroupBox("Game Controls")
        topLayout = QVBoxLayout()

        self.label_timeRemaining = QLabel("Time: 60s")
        topLayout.addWidget(self.label_timeRemaining)

        # Buttons layout
        btnLayout = QHBoxLayout()
        self.passButton = QPushButton("Pass")
        btnLayout.addWidget(self.passButton)
        self.resetButton = QPushButton("Reset")
        btnLayout.addWidget(self.resetButton)
        topLayout.addLayout(btnLayout)

        topGroup.setLayout(topLayout)
        self.mainLayout.addWidget(topGroup)

        # Connect buttons
        self.passButton.clicked.connect(self.onPassClicked)
        self.resetButton.clicked.connect(self.onResetClicked)

        # ------------------ Scores (Current Player, Captures, Territory) ------------------
        scoreGroup = QGroupBox("Scores")
        scoreLayout = QVBoxLayout()

        self.label_currentPlayer = QLabel("Current Player: Black")
        scoreLayout.addWidget(self.label_currentPlayer)

        capturesLayout = QHBoxLayout()
        self.label_blackCaptures = QLabel("Black Caps: 0")
        self.label_whiteCaptures = QLabel("White Caps: 0")
        capturesLayout.addWidget(self.label_blackCaptures)
        capturesLayout.addWidget(self.label_whiteCaptures)
        scoreLayout.addLayout(capturesLayout)

        territoryLayout = QHBoxLayout()
        self.label_blackTerritory = QLabel("Black Terr: 0")
        self.label_whiteTerritory = QLabel("White Terr: 0")
        territoryLayout.addWidget(self.label_blackTerritory)
        territoryLayout.addWidget(self.label_whiteTerritory)
        scoreLayout.addLayout(territoryLayout)

        scoreGroup.setLayout(scoreLayout)
        self.mainLayout.addWidget(scoreGroup)

        # ------------------ Game Log (Stack-like) ------------------
        logGroup = QGroupBox("Game Log")
        logLayout = QVBoxLayout()
        self.gameLogText = QPlainTextEdit()
        self.gameLogText.setReadOnly(True)
        logLayout.addWidget(self.gameLogText)
        logGroup.setLayout(logLayout)
        self.mainLayout.addWidget(logGroup)

        self.mainWidget.setLayout(self.mainLayout)
        self.show()

    def make_connection(self, board):
        """
        Connect signals from the Board
        """
        self.board = board

        # Board signals
        board.clickLocationSignal.connect(self.onClickLocation)
        board.updateTimerSignal.connect(self.onTimeUpdate)
        board.infoMessageSignal.connect(self.onInfoMessage)

        # GameLogic signals
        gameLogic = board.gameLogic
        gameLogic.currentPlayerChangedSignal.connect(self.onCurrentPlayerChanged)
        gameLogic.capturesUpdatedSignal.connect(self.onCapturesUpdated)
        gameLogic.territoryUpdatedSignal.connect(self.onTerritoryUpdated)
        gameLogic.gameOverSignal.connect(self.onGameOver)

    # ------------------------------ Board Slots ------------------------------
    @pyqtSlot(str)
    def onClickLocation(self, clickLoc):
        # Optionally do nothing, or just log it
        # Never used it 
        pass

    @pyqtSlot(int)
    def onTimeUpdate(self, timeRemaining):
        """
        Update the scoreboard with the countdown
        """
        self.label_timeRemaining.setText(f"Time: {timeRemaining}s")

    @pyqtSlot(str)
    def onInfoMessage(self, message):
        """
        We want the newest message on top => Insert at index 0 in self
        """
        self.logMessages.insert(0, message)
        # We could rejoin them with \n
        self.gameLogText.setPlainText("\n".join(self.logMessages))

    # ------------------------------ GameLogic Slots ------------------------------
    @pyqtSlot(str)
    def onCurrentPlayerChanged(self, playerColor):
        """
        Update label for the current player
        """
        self.label_currentPlayer.setText(f"Current Player: {playerColor}")

    @pyqtSlot(int, int)
    def onCapturesUpdated(self, blackCaps, whiteCaps):
        """
        Update captures for Black/White
        """
        self.label_blackCaptures.setText(f"Black Caps: {blackCaps}")
        self.label_whiteCaptures.setText(f"White Caps: {whiteCaps}")

    @pyqtSlot(int, int)
    def onTerritoryUpdated(self, blackTerr, whiteTerr):
        """
        Update territory counts
        """
        self.label_blackTerritory.setText(f"Black Terr: {blackTerr}")
        self.label_whiteTerritory.setText(f"White Terr: {whiteTerr}")

    @pyqtSlot(str)
    def onGameOver(self, resultMsg):
        """
        Show final results in a popup, disable 'Pass', log the message
        at the top of the stack
        """
        self.passButton.setEnabled(False)

        # Insert the game over message at
        self.onInfoMessage(resultMsg)

        box = QMessageBox(self)
        box.setWindowTitle("Game Over!")
        box.setText(resultMsg)
        box.exec()

    # ------------------------------ Button Handlers ------------------------------
    def onPassClicked(self):
        """
        User clicks 'Pass'
        """
        if self.board:
            self.board.passMove()

    def onResetClicked(self):
        """
        User clicks 'Reset'
        """
        if self.board:
            self.board.resetGame()
            self.passButton.setEnabled(True)
            # Clear the old log? how knows
            self.logMessages.clear()
            self.gameLogText.setPlainText("")
