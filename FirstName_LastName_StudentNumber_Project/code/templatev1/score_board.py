# score_board.py

from PyQt6.QtWidgets import (
    QDockWidget, QVBoxLayout, QWidget, QLabel,
    QGroupBox, QHBoxLayout, QPushButton, QMessageBox
)
from PyQt6.QtCore import pyqtSlot, Qt

class ScoreBoard(QDockWidget):
    """
    A QDockWidget that displays:
      - Current click location
      - Time remaining
      - Current player
      - Black captures, White captures
      - Black territory, White territory
      - Pass / Reset buttons
      - Game over message
    """

    def __init__(self):
        super().__init__()
        self.board = None
        self.initUI()

    def initUI(self):
        """Set up the dock widget's layout and widgets."""
        self.resize(220, 300)
        self.setWindowTitle("ScoreBoard")
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)

        self.mainWidget = QWidget()
        self.setWidget(self.mainWidget)
        self.mainLayout = QVBoxLayout(self.mainWidget)

        # Style (QSS)
        self.setStyleSheet("""
            QDockWidget {
                background-color: #FAF0E6; /* Linen */
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                color: #333333;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #8B4513; /* SaddleBrown */
                border-radius: 5px;
                margin-top: 10px;
            }
            QPushButton {
                background-color: #F5DEB3; /* Wheat */
                border: 1px solid #8B4513;
                border-radius: 4px;
                padding: 3px 8px;
            }
            QPushButton:hover {
                background-color: #DEB887; /* BurlyWood */
            }
        """)

        # ------------------ Game Info: Click & Timer ------------------
        infoGroup = QGroupBox("Game Info")
        infoLayout = QVBoxLayout()

        self.label_clickLocation = QLabel("Click Location: N/A")
        self.label_timeRemaining = QLabel("Time Remaining: 60s")

        infoLayout.addWidget(self.label_clickLocation)
        infoLayout.addWidget(self.label_timeRemaining)
        infoGroup.setLayout(infoLayout)
        self.mainLayout.addWidget(infoGroup)

        # ------------------ Scores: Player, Captures, Territory ------------------
        scoreGroup = QGroupBox("Scores")
        scoreLayout = QVBoxLayout()

        self.label_currentPlayer = QLabel("Current Player: Black")
        scoreLayout.addWidget(self.label_currentPlayer)

        capturesLayout = QHBoxLayout()
        self.label_blackCaptures = QLabel("Black Captures: 0")
        self.label_whiteCaptures = QLabel("White Captures: 0")
        capturesLayout.addWidget(self.label_blackCaptures)
        capturesLayout.addWidget(self.label_whiteCaptures)
        scoreLayout.addLayout(capturesLayout)

        territoryLayout = QHBoxLayout()
        self.label_blackTerritory = QLabel("Black Territory: 0")
        self.label_whiteTerritory = QLabel("White Territory: 0")
        territoryLayout.addWidget(self.label_blackTerritory)
        territoryLayout.addWidget(self.label_whiteTerritory)
        scoreLayout.addLayout(territoryLayout)

        scoreGroup.setLayout(scoreLayout)
        self.mainLayout.addWidget(scoreGroup)

        # ------------------ Controls: Pass, Reset ------------------
        controlsGroup = QGroupBox("Controls")
        controlsLayout = QHBoxLayout()

        self.passButton = QPushButton("Pass")
        self.passButton.clicked.connect(self.onPassClicked)
        controlsLayout.addWidget(self.passButton)

        self.resetButton = QPushButton("Reset")
        self.resetButton.clicked.connect(self.onResetClicked)
        controlsLayout.addWidget(self.resetButton)

        controlsGroup.setLayout(controlsLayout)
        self.mainLayout.addWidget(controlsGroup)

        self.mainWidget.setLayout(self.mainLayout)
        self.show()

    def make_connection(self, board):
        """
        Connect signals from Board and its GameLogic to update the ScoreBoard.
        Also keep a reference to board for pass/reset.
        """
        self.board = board

        # Board signals
        board.clickLocationSignal.connect(self.setClickLocation)
        board.updateTimerSignal.connect(self.setTimeRemaining)

        # GameLogic signals
        gameLogic = board.gameLogic
        gameLogic.currentPlayerChangedSignal.connect(self.updateCurrentPlayer)
        gameLogic.capturesUpdatedSignal.connect(self.updateCaptures)
        gameLogic.territoryUpdatedSignal.connect(self.updateTerritory)
        gameLogic.gameOverSignal.connect(self.onGameOver)

    # -------------------------------------------------------------------------
    # Slots responding to Board signals
    # -------------------------------------------------------------------------
    @pyqtSlot(str)
    def setClickLocation(self, clickLoc):
        """Update the label for the clicked location on the board."""
        self.label_clickLocation.setText(f"Click Location: {clickLoc}")

    @pyqtSlot(int)
    def setTimeRemaining(self, timeRemaining):
        """Update the label for time remaining."""
        self.label_timeRemaining.setText(f"Time Remaining: {timeRemaining}s")

    # -------------------------------------------------------------------------
    # Slots responding to GameLogic signals
    # -------------------------------------------------------------------------
    @pyqtSlot(str)
    def updateCurrentPlayer(self, playerColor):
        """Update which player's turn it is."""
        # Could be "Black" or "White"
        self.label_currentPlayer.setText(f"Current Player: {playerColor}")

    @pyqtSlot(int, int)
    def updateCaptures(self, blackCaptured, whiteCaptured):
        """Update capture counts for Black and White."""
        self.label_blackCaptures.setText(f"Black Captures: {blackCaptured}")
        self.label_whiteCaptures.setText(f"White Captures: {whiteCaptured}")

    @pyqtSlot(int, int)
    def updateTerritory(self, blackTerr, whiteTerr):
        """Update territory counts for Black and White."""
        self.label_blackTerritory.setText(f"Black Territory: {blackTerr}")
        self.label_whiteTerritory.setText(f"White Territory: {whiteTerr}")

    @pyqtSlot(str)
    def onGameOver(self, resultMsg):
        """
        Called when the game is over (2 passes).
        Display final results; you could also disable moves or show a pop-up.
        """
        # Disable pass button so no more moves
        self.passButton.setEnabled(False)

        # Option 1: Just display in the timeRemaining label
        self.label_timeRemaining.setText(resultMsg)

        # Option 2: Show a pop-up message
        # msg_box = QMessageBox(self)
        # msg_box.setWindowTitle("Game Over")
        # msg_box.setText(resultMsg)
        # msg_box.exec()

    # -------------------------------------------------------------------------
    # Pass & Reset button handlers
    # -------------------------------------------------------------------------
    def onPassClicked(self):
        """When user clicks 'Pass', call board.passMove()."""
        if self.board:
            self.board.passMove()

    def onResetClicked(self):
        """When user clicks 'Reset', reset the board (new game)."""
        if self.board:
            self.board.resetGame()
            # Re-enable pass button if it was disabled
            self.passButton.setEnabled(True)

    def center(self):
        """No-op for a dock widget in this example."""
        pass
