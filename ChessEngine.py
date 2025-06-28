class GameState():
    def __init__(self):
        # 8x8 board, 2d list with 2 letter element in it representing color and type
        # "--" represent no piece, should all be in string to make it easier to add together
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.moveFunction = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                             'Q': self.getQueenMoves, 'K': self.getKingMoves, 'B': self.getBishopMoves}

        self.whiteToMove = True
        self.moveLog = []

        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)

        self.inCheck = False
        self.pins = []
        self.checks = []

        self.enpassantPossible = ()

        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [
            CastleRights(self.currentCastlingRight.whiteKingSide, self.currentCastlingRight.blackKingSide,
                         self.currentCastlingRight.whiteQueenSide, self.currentCastlingRight.blackQueenSide)]

        self.checkmate = False

        self.stalemate = False
        self.halfmoveClock = 0
        self.halfmoveClockLog = [0]
        self.positionHistory = {}
        self.updatePositionHistory()

    def getPositionHash(self):
        return (
            tuple(map(tuple, self.board)),  # Make board hashable
            self.whiteToMove,
            self.currentCastlingRight.astuple(),
            self.enpassantPossible
        )

    def updatePositionHistory(self):
        pos_hash = self.getPositionHash()
        self.positionHistory[pos_hash] = self.positionHistory.get(pos_hash, 0) + 1

    def unUpdatePositionHistory(self):
        pos_hash = self.getPositionHash()
        if pos_hash in self.positionHistory:
            self.positionHistory[pos_hash] -= 1
            if self.positionHistory[pos_hash] == 0:
                del self.positionHistory[pos_hash]

    def is_insufficient_material(self):
        """Checks if the material on board is insufficient for a checkmate."""
        # Count pieces
        pieceCounts = {'w': {'Q': 0, 'R': 0, 'B': 0, 'N': 0, 'p': 0},
                       'b': {'Q': 0, 'R': 0, 'B': 0, 'N': 0, 'p': 0}}
        b_bishop_colors = []  # Stores (row+col)%2 for black bishops
        w_bishop_colors = []  # Stores (row+col)%2 for white bishops

        for r in range(8):
            for c in range(8):
                piece_str = self.board[r][c]
                if piece_str != '--':
                    color = piece_str[0]
                    piece_type = piece_str[1]
                    if piece_type != 'K':  # Kings are assumed
                        pieceCounts[color][piece_type] += 1
                    if piece_type == 'B':
                        if color == 'w':
                            w_bishop_colors.append((r + c) % 2)
                        else:
                            b_bishop_colors.append((r + c) % 2)

        # No pawns, rooks, or queens means only K, N, B can be on board
        if pieceCounts['w']['p'] > 0 or pieceCounts['b']['p'] > 0: return False
        if pieceCounts['w']['Q'] > 0 or pieceCounts['b']['Q'] > 0: return False
        if pieceCounts['w']['R'] > 0 or pieceCounts['b']['R'] > 0: return False

        # K vs K
        if pieceCounts['w']['N'] == 0 and pieceCounts['w']['B'] == 0 and \
                pieceCounts['b']['N'] == 0 and pieceCounts['b']['B'] == 0:
            return True

        # K vs KN or K vs KB
        if (pieceCounts['w']['N'] <= 1 and pieceCounts['w']['B'] == 0 and \
            pieceCounts['b']['N'] == 0 and pieceCounts['b']['B'] == 0) or \
                (pieceCounts['w']['N'] == 0 and pieceCounts['w']['B'] <= 1 and \
                 pieceCounts['b']['N'] == 0 and pieceCounts['b']['B'] == 0):
            return True
        if (pieceCounts['b']['N'] <= 1 and pieceCounts['b']['B'] == 0 and \
            pieceCounts['w']['N'] == 0 and pieceCounts['w']['B'] == 0) or \
                (pieceCounts['b']['N'] == 0 and pieceCounts['b']['B'] <= 1 and \
                 pieceCounts['w']['N'] == 0 and pieceCounts['w']['B'] == 0):
            return True

        # KB vs KB (bishops on same color)
        if pieceCounts['w']['N'] == 0 and pieceCounts['w']['B'] == 1 and \
                pieceCounts['b']['N'] == 0 and pieceCounts['b']['B'] == 1:
            if len(w_bishop_colors) > 0 and len(b_bishop_colors) > 0 and w_bishop_colors[0] == b_bishop_colors[0]:
                return True

        # KN vs KN (This is a draw, but not typically auto-declared by engines without claim.
        # For simplicity here, we might not include it or always declare it a draw if it's the only material)
        # if piece_counts['w']['B'] == 0 and piece_counts['w']['N'] == 1 and \
        #    piece_counts['b']['B'] == 0 and piece_counts['b']['N'] == 1:
        #     return True

        return False  # Otherwise, material might be sufficient

    def is_threefold_repetition(self):
        """Checks if the current position has been repeated three times."""
        currentHash = self.getPositionHash()
        return self.positionHistory.get(currentHash, 0) >= 3

    def is_fifty_move_rule(self):
        """Checks if 50 moves (100 half-moves) have passed without pawn move or capture."""
        return self.halfmoveClock >= 100

    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved

        self.moveLog.append(move)  # History of the game
        self.whiteToMove = not self.whiteToMove  # this should exchange turns

        # update king's location
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        # Pawn promo
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + 'Q'

        # enpassent
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = '--'

        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
        else:  # rest if the players made any other moves besides the enpassant move
            self.enpassantPossible = ()

        # Castle
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # king side
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1]
                self.board[move.endRow][move.endCol + 1] = '--'
            else:
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]
                self.board[move.endRow][move.endCol - 2] = '--'

        self.updateCastleRight(move)
        self.castleRightsLog.append(
            CastleRights(self.currentCastlingRight.whiteKingSide, self.currentCastlingRight.blackKingSide,
                         self.currentCastlingRight.whiteQueenSide, self.currentCastlingRight.blackQueenSide))

        # 50-move rule counter
        if move.pieceMoved[1] == 'p' or move.pieceCaptured != '--':
            self.halfmoveClock = 0
        else:
            self.halfmoveClock += 1
        self.halfmoveClockLog.append(self.halfmoveClock)

        # Update repetition history for the new state
        self.updatePositionHistory()

        # Reset checkmate/stalemate flags, they will be re-evaluated
        self.checkmate = False
        self.stalemate = False
        self.draw = False

    def undoMove(self):
        if len(self.moveLog) != 0:
            # IF YOU HAVE THIS LINE FROM YOUR ORIGINAL CODE, IT'S A BUG for threefold repetition:
            # self.updatePositionHistory()
            # IT SHOULD BE (as in my previous full example):
            self.unUpdatePositionHistory()

            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured

            self.whiteToMove = not self.whiteToMove

            # update king's location
            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)

            # Restore enpassant state (this needs its own log like castleRightsLog for full correctness)
            # My previous example added self.enpassantPossibleLog. For now, focus on halfmove.
            # Simplified enpassant undo from your original (might still have subtle bugs if not logged):
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = '--'
                self.board[move.startRow][move.endCol] = move.pieceCaptured
                self.enpassantPossible = (move.endRow, move.endCol)  # Restores if THIS move created an EP square
                # but doesn't restore previous EP square if this move was not EP related.

            if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:  # This was a double pawn push
                self.enpassantPossible = ()  # No EP square if this specific type of move is undone.
                # This should be: restore self.enpassantPossible from a log.

            # Restore Castling Rights
            self.castleRightsLog.pop()
            # self.currentCastlingRight = self.castleRightsLog[-1] # This is correct
            # To be absolutely safe ensuring it's a new object or mutable fields are copied:
            prev_rights = self.castleRightsLog[-1]
            self.currentCastlingRight = CastleRights(prev_rights.whiteKingSide, prev_rights.blackKingSide,
                                                     prev_rights.whiteQueenSide, prev_rights.blackQueenSide)

            if move.isCastleMove:
                if move.endCol - move.startCol == 2:  # king side
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = '--'
                else:  # queen side
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = '--'

            # THIS BLOCK MUST BE UNINDENTED TO APPLY TO ALL UNDONE MOVES
            self.halfmoveClockLog.pop()
            self.halfmoveClock = self.halfmoveClockLog[-1]

            self.checkmate = False
            self.stalemate = False


    def updateCastleRight(self, move):
        # King Move
        if move.pieceMoved == 'wK':
            self.currentCastlingRight.whiteKingSide = False
            self.currentCastlingRight.whiteQueenSide = False
        elif move.pieceMoved == 'bK':
            self.currentCastlingRight.blackKingSide = False
            self.currentCastlingRight.blackQueenSide = False

        # Rook Move
        if move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startCol == 0:
                    self.currentCastlingRight.whiteQueenSide = False
                elif move.startCol == 7:
                    self.currentCastlingRight.whiteKingSide = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startCol == 0:
                    self.currentCastlingRight.blackQueenSide = False
                elif move.startCol == 7:
                    self.currentCastlingRight.blackKingSide = False

        # Rook Taken
        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRight.whiteQueenSide = False
                elif move.endCol == 7:
                    self.currentCastlingRight.whiteKingSide = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRight.blackQueenSide = False
                elif move.endCol == 7:
                    self.currentCastlingRight.blackKingSide = False

    # moves considering checks
    def getValidMoves(self):
        tempEnpassantPossible = self.enpassantPossible
        # Save the original castling rights state to restore at the end,
        # making getValidMoves have fewer side effects on these specific attributes.
        tempCastleRightsState = CastleRights(self.currentCastlingRight.whiteKingSide,
                                             self.currentCastlingRight.blackKingSide,
                                             self.currentCastlingRight.whiteQueenSide,
                                             self.currentCastlingRight.blackQueenSide)

        # 1. Determine the current check, pins, and checks status.
        # This status will be used by move generation functions.
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()

        # Store a copy of the pins list because piece move generation functions might modify it (by removing pins they handle).
        original_pins_list = list(self.pins)

        current_valid_moves = []  # Initialize an empty list to store all valid moves.

        if self.whiteToMove:
            kingRow, kingCol = self.whiteKingLocation
        else:
            kingRow, kingCol = self.blackKingLocation

        if self.inCheck:  # If the king is currently in check
            if len(self.checks) == 1:  # Single check
                # Need to find moves that block the check or capture the checking piece.
                self.pins = list(original_pins_list)  # Restore pins for getAllPossibleMoves
                possible_moves = self.getAllPossibleMoves()  # Generates non-king moves

                check = self.checks[0]  # Information about the single check
                checkRow, checkCol = check[0], check[1]
                checking_piece_type = self.board[checkRow][checkCol][1]

                # Determine squares that a piece can move to, to either block the check or capture the checking piece.
                squares_to_interfere = []
                if checking_piece_type == 'N':  # Knight check: must capture the knight or move the king.
                    squares_to_interfere.append((checkRow, checkCol))
                else:  # Sliding piece (Rook, Bishop, Queen) or Pawn check: can block or capture.
                    for i in range(1, 8):
                        # Iterate along the line of attack from the king towards the checker.
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i)
                        squares_to_interfere.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:  # Reached the checker's square
                            break

                for move in possible_moves:
                    if move.pieceMoved[1] != 'K':  # King moves are handled separately.
                        if (move.endRow, move.endCol) in squares_to_interfere:
                            current_valid_moves.append(move)

                # Add king moves (getKingMoves itself ensures the king doesn't move into another check).
                self.pins = list(original_pins_list)  # Restore pins for getKingMoves
                self.getKingMoves(kingRow, kingCol, current_valid_moves)  # Appends valid king moves.

            else:  # Double check (or more, though practically only double check is possible).
                # Only king moves are valid.
                self.pins = list(original_pins_list)  # Restore pins for getKingMoves
                self.getKingMoves(kingRow, kingCol, current_valid_moves)

            # No castling is allowed if the king is in check.

        else:  # King is NOT in check.
            # Generate all standard piece moves (non-king, non-castle).
            # These functions use self.pins to respect pins.
            self.pins = list(original_pins_list)  # Restore pins for getAllPossibleMoves
            current_valid_moves = self.getAllPossibleMoves()

            # Add king moves.
            self.pins = list(original_pins_list)  # Restore pins for getKingMoves
            self.getKingMoves(kingRow, kingCol, current_valid_moves)  # Appends valid king moves.

            # Add castle moves if conditions are met.
            # self.inCheck is False here, so the check in getCastleMove's beginning passes.
            # getCastleMove will also check if squares king passes through are attacked.
            if self.whiteToMove:
                self.getCastleMove(self.whiteKingLocation[0], self.whiteKingLocation[1], current_valid_moves)
            else:
                self.getCastleMove(self.blackKingLocation[0], self.blackKingLocation[1], current_valid_moves)

        if len(current_valid_moves) == 0:
            if self.inCheck:
                self.checkmate = True
                self.stalemate = False  # Not stalemate if checkmate
            else:
                print("No Move stalemate")
                self.stalemate = True  # Stalemate by no legal moves
                self.checkmate = False
        else:  # Moves are possible, reset checkmate/stalemate and check other draws
            self.checkmate = False
            self.stalemate = False
            # Check other draw conditions only if not already checkmate/stalemate by no moves
            if self.is_fifty_move_rule() or self.is_threefold_repetition():
                print("50 move stalemate")
                self.stalemate = True
            elif self.is_insufficient_material():
                # Important: Insufficient material can occur even if moves are possible.
                # e.g., K vs K, K can still move but it's a draw.
                print("Insufficient material stalemate")
                self.stalemate = True
            else:
                self.stalemate = False
        # Restore game state attributes that might have been conceptually altered or for safety.
        # self.pins, self.checks, self.inCheck are updated by this function to reflect the board.
        # Enpassant and CastlingRights are restored to their pre-call state, meaning this function
        # itself doesn't change them permanently on the GameState object passed to it.
        self.enpassantPossible = tempEnpassantPossible
        self.currentCastlingRight = tempCastleRightsState

        return current_valid_moves

    def getAllPossibleMoves(self):
        moves = []

        for rows in range(len(self.board)):  # rows
            for cols in range(len(self.board[rows])):  # cols
                turn = self.board[rows][cols][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[rows][cols][1]
                    self.moveFunction[piece](rows, cols, moves)
        return moves

    def getPawnMoves(self, rows, cols, moves):
        # white pawn move
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == rows and self.pins[i][1] == cols:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove:
            if self.board[rows - 1][cols] == "--":
                if not piecePinned or pinDirection == (-1, 0):
                    moves.append(Move((rows, cols), (rows - 1, cols), self.board))
                    if rows == 6 and self.board[rows - 2][cols] == "--":
                        moves.append(Move((rows, cols), (rows - 2, cols), self.board))

            # making capture for white pawn
            if cols - 1 >= 0:  # left capture for white
                if self.board[rows - 1][cols - 1][0] == 'b':
                    if not piecePinned or pinDirection == (-1, -1):
                        moves.append(Move((rows, cols), (rows - 1, cols - 1), self.board))
                elif (rows - 1, cols - 1) == self.enpassantPossible:
                    if not piecePinned or pinDirection == (-1, -1):
                        moves.append(Move((rows, cols), (rows - 1, cols - 1), self.board, isEnpassantMove=True))
            if cols + 1 <= 7:  # right capture for white
                if self.board[rows - 1][cols + 1][0] == 'b':
                    if not piecePinned or pinDirection == (-1, 1):
                        moves.append(Move((rows, cols), (rows - 1, cols + 1), self.board))
                elif (rows - 1, cols + 1) == self.enpassantPossible:
                    if not piecePinned or pinDirection == (-1, 1):
                        moves.append(Move((rows, cols), (rows - 1, cols + 1), self.board, isEnpassantMove=True))

        # black pawn move
        else:
            if self.board[rows + 1][cols] == "--":
                if not piecePinned or pinDirection == (1, 0):
                    moves.append(Move((rows, cols), (rows + 1, cols), self.board))
                    if rows == 1 and self.board[rows + 2][cols] == "--":
                        moves.append(Move((rows, cols), (rows + 2, cols), self.board))
            # making capture for black pawn
            if cols - 1 >= 0:  # right capture for black
                if self.board[rows + 1][cols - 1][0] == 'w':
                    if not piecePinned or pinDirection == (1, -1):
                        moves.append(Move((rows, cols), (rows + 1, cols - 1), self.board))
                elif (rows + 1, cols - 1) == self.enpassantPossible:
                    if not piecePinned or pinDirection == (1, -1):
                        moves.append(Move((rows, cols), (rows + 1, cols - 1), self.board, isEnpassantMove=True))

            if cols + 1 <= 7:  # left capture for black
                if self.board[rows + 1][cols + 1][0] == 'w':
                    if not piecePinned or pinDirection == (1, 1):
                        moves.append(Move((rows, cols), (rows + 1, cols + 1), self.board))
                elif (rows + 1, cols + 1) == self.enpassantPossible:
                    if not piecePinned or pinDirection == (1, 1):
                        moves.append(Move((rows, cols), (rows + 1, cols + 1), self.board, isEnpassantMove=True))

    def getRookMoves(self, rows, cols, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == rows and self.pins[i][1] == cols:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[rows][cols][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break

        direction = [(-1, 0), (0, 1), (0, -1), (1, 0)]

        enemyColor = 'b' if self.whiteToMove else 'w'

        for direct in direction:
            for i in range(1, 8):
                endRow = rows + direct[0] * i
                endCol = cols + direct[1] * i

                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == direct or pinDirection == ((-direct[0], -direct[1])):
                        endPiece = self.board[endRow][endCol]

                        if endPiece == "--":
                            moves.append(Move((rows, cols), (endRow, endCol), self.board))

                        elif endPiece[0] == enemyColor:
                            moves.append(Move((rows, cols), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:
                    break

    def getBishopMoves(self, rows, cols, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == rows and self.pins[i][1] == cols:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        direction = [(-1, -1), (1, 1), (-1, 1), (1, -1)]
        enemyColor = 'b' if self.whiteToMove else 'w'

        for d in direction:
            for i in range(1, 8):
                endRow = rows + d[0] * i
                endCol = cols + d[1] * i

                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((rows, cols), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((rows, cols), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:
                    break

    def getKnightMoves(self, rows, cols, moves):
        piecePinned = False

        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == rows and self.pins[i][1] == cols:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        direction = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, 2), (1, 2), (-1, -2), (1, -2)]
        allyColor = 'w' if self.whiteToMove else 'b'

        for move in direction:
            endRow = rows + move[0]
            endCol = cols + move[1]

            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor:
                        moves.append(Move((rows, cols), (endRow, endCol), self.board))

    def getQueenMoves(self, rows, cols, moves):
        self.getRookMoves(rows, cols, moves)
        self.getBishopMoves(rows, cols, moves)

    def getKingMoves(self, rows, cols, moves):
        # Define all eight directions the king can move
        directions = [
            (-1, 0),  # up
            (1, 0),  # down
            (0, -1),  # left
            (0, 1),  # right
            (-1, -1),  # up-left
            (-1, 1),  # up-right
            (1, -1),  # down-left
            (1, 1)  # down-right
        ]

        # Get ally color and enemy color
        allyColor = 'w' if self.whiteToMove else 'b'

        for directionRows, directionColumns in directions:
            endRow = rows + directionRows
            endCol = cols + directionColumns

            # Check if the position is on the board
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]

                if endPiece[0] != allyColor:

                    if allyColor == 'w':
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()

                    if not inCheck:
                        moves.append(Move((rows, cols), (endRow, endCol), self.board))

                    if allyColor == 'w':
                        self.whiteKingLocation = (rows, cols)
                    else:
                        self.blackKingLocation = (rows, cols)
        # Note: Castle moves would be added here in a more complete implementation
        # self.getCastleMove(rows, cols, moves)

    def getCastleMove(self, row, col, moves):
        if self.inCheck:
            return

        if (self.whiteToMove and self.currentCastlingRight.whiteKingSide) or (
                not self.whiteToMove and self.currentCastlingRight.blackKingSide):
            self.getKingSideMove(row, col, moves)

        if (self.whiteToMove and self.currentCastlingRight.whiteQueenSide) or (
                not self.whiteToMove and self.currentCastlingRight.blackQueenSide):
            self.getQueenSideMove(row, col, moves)

    def getKingSideMove(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squaresUnderAttack(row, col + 1) and not self.squaresUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, isCastleMove=True))

    def getQueenSideMove(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squaresUnderAttack(row, col - 1) and not self.squaresUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, isCastleMove=True))

    def inCheck(self):
        if self.whiteToMove:
            return self.squaresUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squaresUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    def squaresUnderAttack(self, row, col):
        self.whiteToMove = not self.whiteToMove
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove

        for move in oppMoves:
            if (move.endRow == row and move.endCol == col):
                return True
        return False

    def checkForPinsAndChecks(self):
        pins = []
        checks = []
        inCheck = False

        if self.whiteToMove:
            enemyColor = 'b'
            allyColor = 'w'
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = 'w'
            allyColor = 'b'
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]

        # Directions from King's perspective to the potential attacking piece
        # direction[j]:
        # j=0: (0,1)   Right
        # j=1: (0,-1)  Left
        # j=2: (1,0)   Down
        # j=3: (-1,0)  Up
        # j=4: (1,1)   Down-Right
        # j=5: (1,-1)  Down-Left
        # j=6: (-1,1)  Up-Right
        # j=7: (-1,-1) Up-Left
        direction = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

        for j in range(len(direction)):
            d = direction[j]
            possiblePin = ()
            for i in range(1, 8):  # distance from king
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':  # Cannot be 'K' for a pin
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:  # Second allied piece, no pin from this direction
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        # Check if this enemy piece is causing a check or a pin
                        # For Rooks (j=0,1,2,3) and Bishops (j=4,5,6,7) along their lines
                        # For Pawns (i=1, specific diagonals j=4,5,6,7)
                        # For Queens (any j)
                        # For Kings (i=1, any j)
                        if (0 <= j <= 3 and type == 'R') or \
                                (4 <= j <= 7 and type == 'B') or \
                                (i == 1 and type == 'p' and (
                                        # Corrected pawn check logic:
                                        (enemyColor == 'w' and (
                                                j == 4 or j == 5)) or  # White pawn attacking Black king (WP is at BK_pos + d, d=(1,1) or (1,-1))
                                        (enemyColor == 'b' and (j == 6 or j == 7))
                                        # Black pawn attacking White king (BP is at WK_pos + d, d=(-1,1) or (-1,-1))
                                )) or \
                                (type == 'Q') or \
                                (i == 1 and type == 'K'):  # King attacking king
                            if possiblePin == ():  # No allied piece blocking -> direct check
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break  # out of this direction's scan
                            else:  # Allied piece is pinned
                                pins.append(possiblePin)
                                break  # out of this direction's scan
                        else:  # Enemy piece, but not one that can check along this line/distance
                            break  # out of this direction's scan
                else:  # Off board
                    break  # out of this direction's scan

        # Knight checks (Knights don't pin in this context)
        Knightmove = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, 2), (1, 2), (-1, -2), (1, -2)]
        for move in Knightmove:
            endRow = startRow + move[0]
            endCol = startCol + move[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if (endPiece[0] == enemyColor) and endPiece[1] == 'N':  # Enemy knight
                    inCheck = True
                    # For knight checks, d[0] and d[1] are the move itself
                    checks.append((endRow, endCol, move[0], move[1]))
        return inCheck, pins, checks


class CastleRights():
    def __init__(self, whtieKingSide, blackKingSide, whiteQueenSide, blackQueenSide):
        self.whiteKingSide = whtieKingSide
        self.blackKingSide = blackKingSide
        self.whiteQueenSide = whiteQueenSide
        self.blackQueenSide = blackQueenSide

    def astuple(self):
        return (self.whiteKingSide, self.blackKingSide, self.whiteQueenSide, self.blackQueenSide)

    def __eq__(self, other):  # Optional, but good practice
        if isinstance(other, CastleRights):
            return self.astuple() == other.astuple()
        return False

    def __hash__(self):  # Optional, but good practice
        return hash(self.astuple())


class Move():
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}

    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnpassantMove=False, isCastleMove=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]

        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]

        self.isPawnPromotion = (self.pieceMoved == 'wp' and self.endRow == 0) or (
                    self.pieceMoved == 'bp' and self.endRow == 7)
        self.isEnpassantMove = isEnpassantMove

        if self.isEnpassantMove:
            self.pieceCaptured = 'wp' if self.pieceMoved == 'bp' else 'bp'

        self.isCastleMove = isCastleMove

        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def astuple(self):
        return (self.whiteKingSide, self.blackKingSide, self.whiteQueenSide, self.blackQueenSide)

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        # !!!!!!!!!!!!!!!! Need to add more chess notation !!!!!!!!!!!!!!!!!!!
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, row, col):
        return self.colsToFiles[col] + self.rowsToRanks[row]
