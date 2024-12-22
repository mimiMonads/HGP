# game_logic.py
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import Qt

class GameLogic(QObject):
    """
    A simplified Go game logic with:
      - Alternating Black/White stone placement
      - Capturing of opponent stones (no liberties)
      - Suicide rule (can't place a stone that dies unless it captures)
      - Pass logic (2 consecutive passes => game over)
      - Simplified territory counting at game end
      - Signals to update the scoreboard
    """

    # Signals for ScoreBoard
    currentPlayerChangedSignal = pyqtSignal(str)         # "Black" or "White"
    capturesUpdatedSignal     = pyqtSignal(int, int)     # blackCaptures, whiteCaptures
    territoryUpdatedSignal    = pyqtSignal(int, int)     # blackTerritory, whiteTerritory
    gameOverSignal            = pyqtSignal(str)          # final result message

    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.resetGame()
    # ------------------------------------------
    # Public Interface
    # ------------------------------------------

    def resetGame(self):
        """
        Reset everything for a new game:
          -> Empty board
          -> Black moves first
          -> Clear captures & territory
          -> Clear pass count
          -> Not game over
          -> Clear previous board states for KO rule
        """
        self.boardArray = [[None] * self.width for _ in range(self.height)]
        self.currentPlayer = "B"  # Starting with black
        self.blackCaptures = 0
        self.whiteCaptures = 0
        self.blackTerritory = 0  # Initialize black territory
        self.whiteTerritory = 0  # Initialize white territory
        self.gameOver = False
        self.previousBoardStates = []  # List to store board states for KO rule

        # Emit initial signals if needed
        self._emitInitialSignals()

    def handleMove(self, row, col):
        """
        Handle stone placement at (row, col). If the move is valid:
         -> Place stone
         -> Capture enemy stones if they have no liberties
         -> Check for suicide (remove own stones if no liberties & no capture)
         -> Check for KO (illegal move if it recreates the previous board state)
         -> Switch player
         -> Reset consecutivePasses
        """
        if self.gameOver:
            return

        # Ensure the move is within bounds
        if not (0 <= row < self.height and 0 <= col < self.width):
            return

        # Ensure the cell is empty
        if self.boardArray[row][col] is not None:
            return

        # Save current board state before making a move for KO check
        self.previousBoardStates.append(self._copyBoard())

        # Place the stone
        self.boardArray[row][col] = self.currentPlayer

        # Capture any opponent stones with no liberties
        capturedStones = self._captureOpponents()

        # Check for suicide: if the move leads to no liberties for the stone
        group, liberties = self._get_group_and_liberties(row, col, self.currentPlayer)
        if liberties == 0 and capturedStones == 0:
            # Undo the move if it's a suicide
            for (r, c) in group:
                self.boardArray[r][c] = None
            return

        # Check for KO: If the move recreates the previous board state, it's a KO
        if self._isKO():
            # Undo the move to prevent KO
            self.boardArray[row][col] = None
            self.previousBoardStates.pop()  # Remove the saved board state
            return

        # Update captures and switch players
        if capturedStones > 0:
            if self.currentPlayer == "B":
                self.blackCaptures += capturedStones
            else:
                self.whiteCaptures += capturedStones
            self.capturesUpdatedSignal.emit(self.blackCaptures, self.whiteCaptures)

        # Update territory (you would calculate and update this as needed)
        self._updateTerritory()

        # Switch player
        self._switchPlayer()

    def _updateTerritory(self):
        self.blackTerritory = 0  # Replace with actual logic
        self.whiteTerritory = 0  # Replace with actual logic

        # Emit the updated territories
        self.territoryUpdatedSignal.emit(self.blackTerritory, self.whiteTerritory)


    def _isKO(self):
        """
        Check if the current board state results in a KO situation.
        This compares the current board with the most recent previous state.
        """
        if len(self.previousBoardStates) < 1:
            return False  # No previous state to compare with

        lastBoardState = self.previousBoardStates[-1]

        # Compare the board state to see if it matches the previous one
        for r in range(self.height):
            for c in range(self.width):
                if self.boardArray[r][c] != lastBoardState[r][c]:
                    return False
        return True

    def _copyBoard(self):
        """Helper method to create a deep copy of the board for comparison."""
        return [row[:] for row in self.boardArray]
    

    def passMove(self):
        """
        Current player chooses to pass. 
        If we get 2 consecutive passes => game over => compute territory.
        """
        if self.gameOver:
            return

        self.consecutivePasses += 1
        if self.consecutivePasses >= 2:
            # End of game: compute territory, announce final result
            self.gameOver = True
            self._computeTerritory()
            self._emitFinalResult()
            return

        # Switch to the other player
        self._switchPlayer()

    def drawPieces(self, painter, squareWidth, squareHeight, boardPixelWidth, boardPixelHeight):
        """
        Draw black and white stones onto the board.
        Called by board's paintEvent().
        """
        # Calculate offset so the board is centered
        offsetX = (boardPixelWidth - (squareWidth * self.width)) / 2
        offsetY = (boardPixelHeight - (squareHeight * self.height)) / 2

        # Stone radius
        radius = int(min(squareWidth, squareHeight)//2) - 2

        for row in range(self.height):
            for col in range(self.width):
                stone = self.boardArray[row][col]
                if stone in ("B", "W"):
                    centerX = offsetX + col*squareWidth + (squareWidth/2)
                    centerY = offsetY + row*squareHeight + (squareHeight/2)

                    if stone == "B":
                        painter.setBrush(QBrush(Qt.GlobalColor.black))
                    else:
                        painter.setBrush(QBrush(Qt.GlobalColor.white))

                    painter.setPen(Qt.GlobalColor.black)
                    painter.drawEllipse(int(centerX - radius),
                                        int(centerY - radius),
                                        2*radius, 2*radius)

    # ------------------------------------------
    # Internal Helpers
    # ------------------------------------------

    def _emitInitialSignals(self):
        """
        Emit initial scoreboard signals
        """
        self.currentPlayerChangedSignal.emit("Black")  # Start with black
        self.capturesUpdatedSignal.emit(self.blackCaptures, self.whiteCaptures)
        self.territoryUpdatedSignal.emit(self.blackTerritory, self.whiteTerritory)

    def _switchPlayer(self):
        """
        Switch from B to W or W to B, emit signal for scoreboard
        """
        if self.currentPlayer == "B":
            self.currentPlayer = "W"
            self.currentPlayerChangedSignal.emit("White")
        else:
            self.currentPlayer = "B"
            self.currentPlayerChangedSignal.emit("Black")

    def _captureOpponents(self):
        """
        Find and remove any groups of the *opponent* color that have no liberties.
        Return total number of stones captured (to update scoreboard).
        """
        opponent = "W" if self.currentPlayer == "B" else "B"
        captured_stones = 0
        visited = set()

        for r in range(self.height):
            for c in range(self.width):
                if self.boardArray[r][c] == opponent and (r, c) not in visited:
                    group, liberties = self._get_group_and_liberties(r, c, opponent)
                    # Mark them visited so we don't re-check
                    for pos in group:
                        visited.add(pos)
                    if liberties == 0:
                        # Capture entire group
                        for (gr, gc) in group:
                            self.boardArray[gr][gc] = None
                        captured_stones += len(group)

        # Update capture count for the *current* player
        if captured_stones > 0:
            if self.currentPlayer == "B":
                self.blackCaptures += captured_stones
            else:
                self.whiteCaptures += captured_stones
            self.capturesUpdatedSignal.emit(self.blackCaptures, self.whiteCaptures)

        return captured_stones

    def _get_group_and_liberties(self, start_row, start_col, color):
        """
        BFS or DFS to get:
         - 'group': list of connected stones of 'color'
         - 'liberties': count of empty adjacent intersections
        """
        stack = [(start_row, start_col)]
        visited = set()
        visited.add((start_row, start_col))
        group = []
        liberties = 0

        while stack:
            r, c = stack.pop()
            group.append((r, c))

            # Check neighbors
            for nr, nc in [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]:
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if self.boardArray[nr][nc] is None:
                        liberties += 1
                    elif self.boardArray[nr][nc] == color and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))

        return group, liberties

    def _computeTerritory(self):
        """
        A simplified territory computation:
         - For each empty region, see which color(s) border it.
         - If exactly one color borders that region, that color gets territory = region size.
        """
        visited = set()
        self.blackTerritory = 0
        self.whiteTerritory = 0

        for r in range(self.height):
            for c in range(self.width):
                if self.boardArray[r][c] is None and (r, c) not in visited:
                    region, bordering_colors = self._explore_empty_region(r, c, visited)
                    if len(bordering_colors) == 1:
                        color = bordering_colors.pop()
                        if color == "B":
                            self.blackTerritory += len(region)
                        elif color == "W":
                            self.whiteTerritory += len(region)

        # Emit updated territory
        self.territoryUpdatedSignal.emit(self.blackTerritory, self.whiteTerritory)

    def _explore_empty_region(self, start_row, start_col, visited):
        """
        BFS to find all connected empty cells and which colors border it.
        Returns (list_of_positions, set_of_border_colors).
        """
        queue = [(start_row, start_col)]
        region_positions = []
        bordering_colors = set()
        visited.add((start_row, start_col))

        while queue:
            r, c = queue.pop(0)
            region_positions.append((r, c))

            for nr, nc in [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]:
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if (nr, nc) not in visited:
                        if self.boardArray[nr][nc] is None:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                        else:
                            bordering_colors.add(self.boardArray[nr][nc])

        return region_positions, bordering_colors

    def _emitFinalResult(self):
        """
        Compare final scores:
            blackScore = blackTerritory + blackCaptures
            whiteScore = whiteTerritory + whiteCaptures
        Then emit a message via gameOverSignal
        """
        black_score = self.blackTerritory + self.blackCaptures
        white_score = self.whiteTerritory + self.whiteCaptures

        if black_score > white_score:
            msg = f"Game Over! Black wins ({black_score} vs {white_score})"
        elif white_score > black_score:
            msg = f"Game Over! White wins ({white_score} vs {black_score})"
        else:
            msg = f"Game Over! It's a tie ({black_score} - {white_score})"

        self.gameOverSignal.emit(msg)
