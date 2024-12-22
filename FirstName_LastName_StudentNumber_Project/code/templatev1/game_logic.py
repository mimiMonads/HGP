# game_logic.py
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush
from PyQt6.QtCore import Qt

class GameLogic(QObject):
    """
    A simplified Go game logic with:
      - Alternating Black/White stone placement
      - Capturing of opponent stones (no liberties)
      - Suicide rule (can't place a stone that dies unless it captures)
      - KO rule
      - Pass logic (2 consecutive passes => game over)
      - Simplified territory counting at game end
      - Signals to update the scoreboard
    """

    # Signals for ScoreBoard

    currentPlayerChangedSignal = pyqtSignal(str)    
    capturesUpdatedSignal      = pyqtSignal(int, int)  
    territoryUpdatedSignal     = pyqtSignal(int, int)
    gameOverSignal             = pyqtSignal(str)

    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        # For Ko rule, store the previous board position
        self.previousBoardState = None  
        self.resetGame()

    def resetGame(self):
        self.boardArray = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.currentPlayer = "B"
        self.blackCaptures = 0
        self.whiteCaptures = 0
        self.blackTerritory = 0
        self.whiteTerritory = 0
        self.consecutivePasses = 0
        self.gameOver = False
        self.previousBoardState = None

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

        # Save board state before move (KO)
        oldState = self._getBoardSignature()

        # Place stone
        self.boardArray[row][col] = self.currentPlayer
        self.consecutivePasses = 0

        # Capture opponents
        capturedStones = self._captureOpponents()

        # Check for suicide
        group, liberties = self._get_group_and_liberties(row, col, self.currentPlayer)
        if liberties == 0 and capturedStones == 0:
            # revert the stone
            for (r, c) in group:
                self.boardArray[r][c] = None
            return

        # If captures occurred, update scoreboard
        if capturedStones > 0:
            self.capturesUpdatedSignal.emit(self.blackCaptures, self.whiteCaptures)

        # Ko check: if the new board state == old board state, it’s a Ko
        newState = self._getBoardSignature()
        if newState == oldState:
            # Revert the move
            self.boardArray[row][col] = None
            # If we removed stones, restore them if needed. 
            # But in a typical single step KO scenario, 
            # the only reason it s identical is that we captured some stones 
            # and ended up with the same position as before.
            self._restoreBoardFromSignature(oldState)
            return

        # If everything is valid, store new state as previous
        self.previousBoardState = newState
        self._switchPlayer()

    def passMove(self):
        """
        Current player chooses to pass. 
        If we get 2 consecutive passes => game over => compute territory.
        """
        if self.gameOver:
            return

        self.consecutivePasses += 1
        if self.consecutivePasses >= 2:
            self.gameOver = True
            self._computeTerritory()
            self._emitFinalResult()
            return
        
        # KO
        self.previousBoardState = self._getBoardSignature()
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
                    painter.setPen(Qt.GlobalColor.black)
                    if stone == "B":
                        painter.setBrush(QBrush(Qt.GlobalColor.black))
                    else:
                        painter.setBrush(QBrush(Qt.GlobalColor.white))
                    painter.drawEllipse(
                        int(centerX - radius),
                        int(centerY - radius),
                        2*radius, 2*radius
                    )

    # -------------- Ko Helper: Board Signature --------------
    def _getBoardSignature(self):
        """
        Return a simple string representing the entire board.
        'B' for black, 'W' for white
        """
        rows = []
        for r in range(self.height):
            row_str = "".join(
                '.' if self.boardArray[r][c] is None else self.boardArray[r][c]
                for c in range(self.width)
            )
            rows.append(row_str)
        return "\n".join(rows)

    def _restoreBoardFromSignature(self, signature):
        """
        Restore self.boardArray from a previously saved signature.
        """
        lines = signature.split("\n")
        for r, line in enumerate(lines):
            for c, char in enumerate(line):
                if char == '.':
                    self.boardArray[r][c] = None
                else:
                    self.boardArray[r][c] = char

    # ------------------------------------------
    # Internal Helpers
    # ------------------------------------------
    def _emitInitialSignals(self):
        self.currentPlayerChangedSignal.emit("Black")
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
                    for pos in group:
                        visited.add(pos)
                    if liberties == 0:
                        # remove group
                        for (gr, gc) in group:
                            self.boardArray[gr][gc] = None
                        captured_stones += len(group)

        if captured_stones > 0:
            if self.currentPlayer == "B":
                self.blackCaptures += captured_stones
            else:
                self.whiteCaptures += captured_stones

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

            # neighbors
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
