# go.py
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
from board import Board
from score_board import ScoreBoard

class Go(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def getBoard(self):
        return self.board

    def getScoreBoard(self):
        return self.scoreBoard

    def initUI(self):
        """Initialize the main window
         Adds:
         -> Board at center
         -> ScoreBoard as dock
         """
        self.board = Board(self)
        self.setCentralWidget(self.board)

        # To dock 
        self.scoreBoard = ScoreBoard()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.scoreBoard)
        self.scoreBoard.make_connection(self.board)

        self.resize(800, 800)
        self.center()
        self.setWindowTitle('Go')
        self.show()

    def center(self):
        """Centers the window on the screen."""
        gr = self.frameGeometry()
        screen = self.screen().availableGeometry().center()
        gr.moveCenter(screen)
        self.move(gr.topLeft())
