# game_logic.py

from copy import deepcopy
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush
from PyQt6.QtCore import Qt

class GameLogic(QObject):
    """
    A simplified Go game logic with:
      - Alternating Black/White stone placement
      - Capturing of opponent stones (no liberties)
      - Suicide rule (can't place a stone that dies unless it captures)
      - **SUPERKO rule** (no returning to ANY previously seen board state)
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

        # For superko
        self.allBoardSignatures = set()
        self.resetGame()

    def resetGame(self):
        """
        Reset everything for a new game.
        """
        self.boardArray = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.currentPlayer = "B"
        self.blackCaptures = 0
        self.whiteCaptures = 0
        self.blackTerritory = 0
        self.whiteTerritory = 0
        self.consecutivePasses = 0
        self.gameOver = False

        self.allBoardSignatures.clear()
        # Record the initial empty board
        initialSig = self._getBoardSignature(self.boardArray)
        self.allBoardSignatures.add(initialSig)

        self._emitInitialSignals()

    def handleMove(self, row, col):
        """
        Handle stone placement at (row, col). If the move is valid:
         -> Place stone
         -> Capture enemy stones if they have no liberties
         -> Check for suicide (remove own stones if no liberties & no capture)
         -> Check for superko (illegal if new state is ANY past state)
         -> Switch player
         -> Reset consecutivePasses
        """
        if self.gameOver:
            return

        # Bounds check
        if not (0 <= row < self.height and 0 <= col < self.width):
            return

        # Must be empty
        if self.boardArray[row][col] is not None:
            return

        # Keep old board + captures in case we revert
        oldBoard = deepcopy(self.boardArray)
        oldBlackCaptures = self.blackCaptures
        oldWhiteCaptures = self.whiteCaptures

        # Place stone
        self.boardArray[row][col] = self.currentPlayer
        self.consecutivePasses = 0

        # Capture
        capturedStones = self._captureOpponents()

        # Check suicide
        group, liberties = self._get_group_and_liberties(row, col, self.currentPlayer)
        if liberties == 0 and capturedStones == 0:
            # revert
            self.boardArray[row][col] = None
            return

        # If captures occurred, update scoreboard
        if capturedStones > 0:
            self.capturesUpdatedSignal.emit(self.blackCaptures, self.whiteCaptures)

        # Now compute the new board signature
        newSig = self._getBoardSignature(self.boardArray)
        # **SUPERKO** 
        if newSig in self.allBoardSignatures:
            # revert
            self.boardArray = oldBoard
            self.blackCaptures = oldBlackCaptures
            self.whiteCaptures = oldWhiteCaptures
            return

        # If valid, record newSig in the history
        self.allBoardSignatures.add(newSig)

        # Switch player
        self._switchPlayer()

    def passMove(self):
        """
        2 consecutive passes => game ends => territory counted
        """
        if self.gameOver:
            return

        self.consecutivePasses += 1
        if self.consecutivePasses >= 2:
            self.gameOver = True
            self._computeTerritory()
            self._emitFinalResult()
            return
        
        # Add the current position to history 
        # to a previously seen position
        newSig = self._getBoardSignature(self.boardArray)
        self.allBoardSignatures.add(newSig)

        self._switchPlayer()

    def drawPieces(self, painter, squareWidth, squareHeight, boardPixelWidth, boardPixelHeight):
        """
        Draw black and white stones onto the board.
        """
        offsetX = (boardPixelWidth - (squareWidth * self.width)) / 2
        offsetY = (boardPixelHeight - (squareHeight * self.height)) / 2
        radius = int(min(squareWidth, squareHeight)//2) - 2

        for row in range(self.height):
            for col in range(self.width):
                stone = self.boardArray[row][col]
                if stone in ("B", "W"):
                    centerX = offsetX + col*squareWidth + squareWidth/2
                    centerY = offsetY + row*squareHeight + squareHeight/2
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

    # -----------------------------------------------------------------
    # Superko Helpers
    # -----------------------------------------------------------------
    def _getBoardSignature(self, board):
        """
        Return a string uniquely identifying 'board' layout.
        We ignore captures or current player in the signature,
        focusing purely on stone placements. (This is typical for superko.)
        """
        rows = []
        for r in range(self.height):
            row_str = "".join('.' if board[r][c] is None else board[r][c]
                              for c in range(self.width))
            rows.append(row_str)
        return "\n".join(rows)

    # -----------------------------------------
    # Internal Helpers
    # -----------------------------------------
    def _emitInitialSignals(self):
        self.currentPlayerChangedSignal.emit("Black")
        self.capturesUpdatedSignal.emit(self.blackCaptures, self.whiteCaptures)
        self.territoryUpdatedSignal.emit(self.blackTerritory, self.whiteTerritory)

    def _switchPlayer(self):
        if self.currentPlayer == "B":
            self.currentPlayer = "W"
            self.currentPlayerChangedSignal.emit("White")
        else:
            self.currentPlayer = "B"
            self.currentPlayerChangedSignal.emit("Black")

    def _captureOpponents(self):
        opponent = "W" if self.currentPlayer == "B" else "B"
        captured_stones = 0
        visited = set()

        for r in range(self.height):
            for c in range(self.width):
                if self.boardArray[r][c] == opponent and (r, c) not in visited:
                    group, liberties = self._get_group_and_liberties(r, c, opponent)
                    visited.update(group)
                    if liberties == 0:
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
        stack = [(start_row, start_col)]
        visited = {(start_row, start_col)}
        group = []
        liberties = 0

        while stack:
            r, c = stack.pop()
            group.append((r, c))
            for nr, nc in [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]:
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if self.boardArray[nr][nc] is None:
                        liberties += 1
                    elif self.boardArray[nr][nc] == color and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))
        return group, liberties

    def _computeTerritory(self):
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
        self.territoryUpdatedSignal.emit(self.blackTerritory, self.whiteTerritory)

    def _explore_empty_region(self, start_row, start_col, visited):
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
        black_score = self.blackTerritory + self.blackCaptures
        white_score = self.whiteTerritory + self.whiteCaptures

        if black_score > white_score:
            msg = f"Game Over! Black wins ({black_score} vs {white_score})"
        elif white_score > black_score:
            msg = f"Game Over! White wins ({white_score} vs {black_score})"
        else:
            msg = f"Game Over! It's a tie ({black_score} - {white_score})"

        self.gameOverSignal.emit(msg)
