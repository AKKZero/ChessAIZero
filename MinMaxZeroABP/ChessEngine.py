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

        self.inCheck = False  # Is the current player in check? Set by getValidMoves.
        self.pins = []  # List of pinned pieces for the current player.
        self.checks = []  # List of checks against the current player's king.

        self.enpassantPossible = ()
        self.enpassantPossibleLog = [()]  # Log to correctly undo enpassant states

        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [
            CastleRights(self.currentCastlingRight.whiteKingSide, self.currentCastlingRight.blackKingSide,
                         self.currentCastlingRight.whiteQueenSide, self.currentCastlingRight.blackQueenSide)]

        self.checkmate = False
        self.stalemate = False  # This flag will be used for stalemate and other draw conditions
        self.halfmoveClock = 0
        self.halfmoveClockLog = [0]
        self.positionHistory = {}
        self.updatePositionHistory()

    def getPositionHash(self):
        return (
            tuple(map(tuple, self.board)),
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
        pieceCounts = {'w': {'Q': 0, 'R': 0, 'B': 0, 'N': 0, 'p': 0},
                       'b': {'Q': 0, 'R': 0, 'B': 0, 'N': 0, 'p': 0}}
        b_bishop_colors = []
        w_bishop_colors = []
        for r in range(8):
            for c in range(8):
                piece_str = self.board[r][c]
                if piece_str != '--':
                    color, piece_type = piece_str[0], piece_str[1]
                    if piece_type != 'K': pieceCounts[color][piece_type] += 1
                    if piece_type == 'B':
                        if color == 'w':
                            w_bishop_colors.append((r + c) % 2)
                        else:
                            b_bishop_colors.append((r + c) % 2)
        if any(pieceCounts[color]['p'] > 0 for color in 'wb') or \
                any(pieceCounts[color]['Q'] > 0 for color in 'wb') or \
                any(pieceCounts[color]['R'] > 0 for color in 'wb'): return False
        if pieceCounts['w']['N'] == 0 and pieceCounts['w']['B'] == 0 and \
                pieceCounts['b']['N'] == 0 and pieceCounts['b']['B'] == 0: return True
        if (pieceCounts['w']['N'] <= 1 and pieceCounts['w']['B'] == 0 and pieceCounts['b']['N'] == 0 and
            pieceCounts['b']['B'] == 0) or \
                (pieceCounts['w']['N'] == 0 and pieceCounts['w']['B'] <= 1 and pieceCounts['b']['N'] == 0 and
                 pieceCounts['b']['B'] == 0): return True
        if (pieceCounts['b']['N'] <= 1 and pieceCounts['b']['B'] == 0 and pieceCounts['w']['N'] == 0 and
            pieceCounts['w']['B'] == 0) or \
                (pieceCounts['b']['N'] == 0 and pieceCounts['b']['B'] <= 1 and pieceCounts['w']['N'] == 0 and
                 pieceCounts['w']['B'] == 0): return True
        if pieceCounts['w']['N'] == 0 and pieceCounts['w']['B'] == 1 and \
                pieceCounts['b']['N'] == 0 and pieceCounts['b']['B'] == 1:
            if w_bishop_colors and b_bishop_colors and w_bishop_colors[0] == b_bishop_colors[0]: return True
        return False

    def is_threefold_repetition(self):
        currentHash = self.getPositionHash()
        return self.positionHistory.get(currentHash, 0) >= 3

    def is_fifty_move_rule(self):
        return self.halfmoveClock >= 100

    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove

        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        if move.isPawnPromotion: self.board[move.endRow][move.endCol] = move.pieceMoved[0] + 'Q'
        if move.isEnpassantMove: self.board[move.startRow][move.endCol] = '--'

        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
        else:
            self.enpassantPossible = ()
        self.enpassantPossibleLog.append(self.enpassantPossible)

        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # king side
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1]
                self.board[move.endRow][move.endCol + 1] = '--'
            else:  # queen side
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]
                self.board[move.endRow][move.endCol - 2] = '--'

        self.updateCastleRight(move)
        self.castleRightsLog.append(
            CastleRights(self.currentCastlingRight.whiteKingSide, self.currentCastlingRight.blackKingSide,
                         self.currentCastlingRight.whiteQueenSide, self.currentCastlingRight.blackQueenSide))

        if move.pieceMoved[1] == 'p' or move.pieceCaptured != '--':
            self.halfmoveClock = 0
        else:
            self.halfmoveClock += 1
        self.halfmoveClockLog.append(self.halfmoveClock)
        self.updatePositionHistory()
        self.checkmate = False
        self.stalemate = False
        # Removed self.draw as it was in your original but not defined/used consistently

    def undoMove(self):
        if len(self.moveLog) != 0:
            self.unUpdatePositionHistory()  # Corrected: must un-update for current state before popping move
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove

            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)

            self.enpassantPossibleLog.pop()  # Remove current EP state from log
            self.enpassantPossible = self.enpassantPossibleLog[-1]  # Restore previous EP state

            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = '--'  # Captured pawn was on endRow, endCol conceptually
                self.board[move.startRow][move.endCol] = move.pieceCaptured  # Restore the captured pawn
                # The self.enpassantPossible is already restored from the log to state *before* this EP move.

            self.castleRightsLog.pop()
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

            self.halfmoveClockLog.pop()
            self.halfmoveClock = self.halfmoveClockLog[-1]
            self.checkmate = False
            self.stalemate = False

    def updateCastleRight(self, move):
        if move.pieceMoved == 'wK':
            self.currentCastlingRight.whiteKingSide = False
            self.currentCastlingRight.whiteQueenSide = False
        elif move.pieceMoved == 'bK':
            self.currentCastlingRight.blackKingSide = False
            self.currentCastlingRight.blackQueenSide = False

        if move.pieceMoved == 'wR':
            if move.startRow == 7 and move.startCol == 0:
                self.currentCastlingRight.whiteQueenSide = False
            elif move.startRow == 7 and move.startCol == 7:
                self.currentCastlingRight.whiteKingSide = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0 and move.startCol == 0:
                self.currentCastlingRight.blackQueenSide = False
            elif move.startRow == 0 and move.startCol == 7:
                self.currentCastlingRight.blackKingSide = False
        #Missing Rooks
        if move.pieceCaptured == 'wR':
            if move.endRow == 7 and move.endCol == 0:
                self.currentCastlingRight.whiteQueenSide = False
            elif move.endRow == 7 and move.endCol == 7:
                self.currentCastlingRight.whiteKingSide = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0 and move.endCol == 0:
                self.currentCastlingRight.blackQueenSide = False
            elif move.endRow == 0 and move.endCol == 7:
                self.currentCastlingRight.blackKingSide = False

    def getValidMoves(self):
        tempEnpassantPossible = self.enpassantPossible
        tempCastleRightsState = CastleRights(self.currentCastlingRight.whiteKingSide,
                                             self.currentCastlingRight.blackKingSide,
                                             self.currentCastlingRight.whiteQueenSide,
                                             self.currentCastlingRight.blackQueenSide)

        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        original_pins_for_this_turn = list(self.pins)  # Make a copy specific to this call
        current_valid_moves = []

        if self.whiteToMove:
            kingRow, kingCol = self.whiteKingLocation
        else:
            kingRow, kingCol = self.blackKingLocation

        if self.inCheck:
            if len(self.checks) == 1:  # Single check
                self.pins = list(original_pins_for_this_turn)  # Restore pins for this specific path
                possible_non_king_moves = self.getAllPossibleMoves()  # Non-king moves

                check = self.checks[0]
                checkRow, checkCol = check[0], check[1]
                checking_piece_type = self.board[checkRow][checkCol][1]
                squares_to_interfere = []
                if checking_piece_type == 'N':
                    squares_to_interfere.append((checkRow, checkCol))
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i)
                        squares_to_interfere.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol: break

                for m in possible_non_king_moves:
                    if (m.endRow, m.endCol) in squares_to_interfere:
                        current_valid_moves.append(m)

                self.pins = list(original_pins_for_this_turn)  # Restore pins for getKingMoves
                self.getKingMoves(kingRow, kingCol, current_valid_moves)
            else:  # Double check, only king moves are valid
                self.pins = list(original_pins_for_this_turn)  # Restore pins for getKingMoves
                self.getKingMoves(kingRow, kingCol, current_valid_moves)
            # No castling if in check (handled by getCastleMove's self.inCheck check)
        else:  # Not in check
            self.pins = list(original_pins_for_this_turn)  # Use fresh copy of pins for getAllPossibleMoves
            current_valid_moves = self.getAllPossibleMoves()  # Generates non-king moves

            self.pins = list(original_pins_for_this_turn)  # Use fresh copy of pins for getKingMoves
            self.getKingMoves(kingRow, kingCol, current_valid_moves)

            # Add castle moves (getCastleMove will check rights, king position, and attacked squares)
            # self.inCheck is False here.
            if self.whiteToMove:
                self.getCastleMove(self.whiteKingLocation[0], self.whiteKingLocation[1], current_valid_moves)
            else:
                self.getCastleMove(self.blackKingLocation[0], self.blackKingLocation[1], current_valid_moves)

        if len(current_valid_moves) == 0:
            if self.inCheck:
                self.checkmate = True; self.stalemate = False
            else:
                self.stalemate = True; self.checkmate = False; print("No Move stalemate")
        else:
            self.checkmate = False;
            self.stalemate = False
            if self.is_fifty_move_rule():
                self.stalemate = True; print("50 move stalemate")
            elif self.is_threefold_repetition():
                self.stalemate = True; print("Three fold repetition stalemate")
            elif self.is_insufficient_material():
                self.stalemate = True; print("Insufficient material stalemate")

        self.enpassantPossible = tempEnpassantPossible
        self.currentCastlingRight = tempCastleRightsState
        return current_valid_moves

    def getAllPossibleMoves(self):
        moves = []
        for row in range(len(self.board)):  # Renamed r to r_idx
            for colum in range(len(self.board[row])):  # Renamed c to c_idx
                turn = self.board[row][colum][0]
                if (turn == "w" and self.whiteToMove) or \
                        (turn == "b" and not self.whiteToMove):
                    piece_type = self.board[row][colum][1]
                    if piece_type != 'K':  # FIX 1: Exclude king moves from here
                        self.moveFunction[piece_type](row, colum, moves)
        return moves

    def getPawnMoves(self, rows, cols, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):  # Iterate backwards for safe removal
            if self.pins[i][0] == rows and self.pins[i][1] == cols:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])  # This modifies the current self.pins list
                break
        # ... rest of pawn logic (from your original file, seems mostly okay)
        if self.whiteToMove:
            if rows - 1 >= 0 and self.board[rows - 1][cols] == "--":  # Check boundary for rows-1
                if not piecePinned or pinDirection == (-1, 0):
                    moves.append(Move((rows, cols), (rows - 1, cols), self.board))
                    if rows == 6 and rows - 2 >= 0 and self.board[rows - 2][cols] == "--":  # Check boundary for rows-2
                        moves.append(Move((rows, cols), (rows - 2, cols), self.board))
            if cols - 1 >= 0 and rows - 1 >= 0:  # Check boundary for rows-1
                if self.board[rows - 1][cols - 1][0] == 'b':
                    if not piecePinned or pinDirection == (-1, -1):
                        moves.append(Move((rows, cols), (rows - 1, cols - 1), self.board))
                elif (rows - 1, cols - 1) == self.enpassantPossible:
                    if not piecePinned or pinDirection == (-1, -1):
                        moves.append(Move((rows, cols), (rows - 1, cols - 1), self.board, isEnpassantMove=True))
            if cols + 1 <= 7 and rows - 1 >= 0:  # Check boundary for rows-1
                if self.board[rows - 1][cols + 1][0] == 'b':
                    if not piecePinned or pinDirection == (-1, 1):
                        moves.append(Move((rows, cols), (rows - 1, cols + 1), self.board))
                elif (rows - 1, cols + 1) == self.enpassantPossible:
                    if not piecePinned or pinDirection == (-1, 1):
                        moves.append(Move((rows, cols), (rows - 1, cols + 1), self.board, isEnpassantMove=True))
        else:  # Black pawn move
            if rows + 1 <= 7 and self.board[rows + 1][cols] == "--":  # Check boundary for rows+1
                if not piecePinned or pinDirection == (1, 0):
                    moves.append(Move((rows, cols), (rows + 1, cols), self.board))
                    if rows == 1 and rows + 2 <= 7 and self.board[rows + 2][cols] == "--":  # Check boundary for rows+2
                        moves.append(Move((rows, cols), (rows + 2, cols), self.board))
            if cols - 1 >= 0 and rows + 1 <= 7:  # Check boundary for rows+1
                if self.board[rows + 1][cols - 1][0] == 'w':
                    if not piecePinned or pinDirection == (1, -1):
                        moves.append(Move((rows, cols), (rows + 1, cols - 1), self.board))
                elif (rows + 1, cols - 1) == self.enpassantPossible:
                    if not piecePinned or pinDirection == (1, -1):
                        moves.append(Move((rows, cols), (rows + 1, cols - 1), self.board, isEnpassantMove=True))
            if cols + 1 <= 7 and rows + 1 <= 7:  # Check boundary for rows+1
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
                if self.board[rows][cols][1] != 'Q':  # Queen uses rook moves but isn't removed from pin list here
                    self.pins.remove(self.pins[i])
                break
        # ... (rest of logic unchanged)
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
                            moves.append(Move((rows, cols), (endRow, endCol), self.board)); break
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
                if self.board[rows][cols][1] == 'B':  # Only remove if actually a Bishop
                    self.pins.remove(self.pins[i])
                break
        # ... (rest of logic unchanged)
        direction = [(-1, -1), (1, 1), (-1, 1), (1, -1)]
        enemyColor = 'b' if self.whiteToMove else 'w'
        for d_dir in direction:  # Renamed d to d_dir
            for i in range(1, 8):
                endRow = rows + d_dir[0] * i
                endCol = cols + d_dir[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d_dir or pinDirection == (-d_dir[0], -d_dir[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((rows, cols), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((rows, cols), (endRow, endCol), self.board)); break
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
        # ... (rest of logic unchanged)
        direction = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, 2), (1, 2), (-1, -2), (1, -2)]
        allyColor = 'w' if self.whiteToMove else 'b'
        for move_dir in direction:  # Renamed 'move' to 'move_dir'
            endRow = rows + move_dir[0]
            endCol = cols + move_dir[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor: moves.append(Move((rows, cols), (endRow, endCol), self.board))

    def getQueenMoves(self, rows, cols, moves):
        self.getRookMoves(rows, cols, moves)
        self.getBishopMoves(rows, cols, moves)

    def getKingMoves(self, rows, cols, moves):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        allyColor = 'w' if self.whiteToMove else 'b'

        # Store original king locations before simulation within this function
        original_wK_loc = self.whiteKingLocation
        original_bK_loc = self.blackKingLocation

        for dr, dc in directions:
            endRow, endCol = rows + dr, cols + dc
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    # Temporarily update the correct king's location for check evaluation
                    if allyColor == 'w':
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    king_would_be_in_check, _, _ = self.checkForPinsAndChecks()

                    if not king_would_be_in_check:
                        moves.append(Move((rows, cols), (endRow, endCol), self.board))

                    self.whiteKingLocation = original_wK_loc
                    self.blackKingLocation = original_bK_loc
        # Castle moves handled by getCastleMove

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
        # Assumes king is on its starting square (e.g., (row,4)) due to checks in getCastleMove
        # Squares (row, col+1) and (row, col+2) must be empty and not attacked
        if 0 <= col + 2 < 8:  # Defensive: ensure col+1 and col+2 are on board
            if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
                if not self.squaresUnderAttack(row, col + 1) and \
                        not self.squaresUnderAttack(row, col + 2):
                    moves.append(Move((row, col), (row, col + 2), self.board, isCastleMove=True))
        # else: print(f"DEBUG: K-side castling squares for col {col} would be off board.")

    def getQueenSideMove(self, row, col, moves):
        if 0 <= col - 3 < 8:  # Defensive: ensure col-1, col-2, col-3 are on board
            # FIX 3: Check all three intervening squares for emptiness
            if self.board[row][col - 1] == '--' and \
                    self.board[row][col - 2] == '--' and \
                    self.board[row][col - 3] == '--':
                if not self.squaresUnderAttack(row, col - 1) and \
                        not self.squaresUnderAttack(row, col - 2):
                    moves.append(Move((row, col), (row, col - 2), self.board, isCastleMove=True))
        # else: print(f"DEBUG: Q-side castling squares for col {col} would be off board.")


    def squaresUnderAttack(self, r_target, c_target):
        player_being_checked_turn = self.whiteToMove  # Player whose square safety is being checked

        # Temporarily switch to opponent's perspective
        self.whiteToMove = not player_being_checked_turn
        _, opponent_pins, _ = self.checkForPinsAndChecks()  # We only need opponent's pins for their move generation

        # Store and set pins for the opponent's move generation
        pins_before_opp_move_gen = list(
            self.pins)  # This would be pins on player_being_checked from opponent perspective
        self.pins = opponent_pins  # Pins on opponent pieces by player_being_checked (relevant for opponent's moves)

        # Opponent is by definition not "inCheck" by the player_being_checked when generating attacking moves
        inCheck_before_opp_move_gen = self.inCheck
        self.inCheck = False

        attack_found = False
        try:
            # Get all non-king moves for the opponent
            opponent_non_king_moves = self.getAllPossibleMoves()
            for move in opponent_non_king_moves:
                if move.endRow == r_target and move.endCol == c_target:
                    attack_found = True
                    break

            if not attack_found:
                # Get opponent's king moves separately
                opp_king_row, opp_king_col = self.blackKingLocation if self.whiteToMove else self.whiteKingLocation  # Current self.whiteToMove is opponent
                # For squaresUnderAttack, king moves are simpler: just direct attacks
                king_directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                for dr, dc in king_directions:
                    if opp_king_row + dr == r_target and opp_king_col + dc == c_target:
                        attack_found = True
                        break
        finally:
            # Restore state for the player_being_checked_turn
            self.whiteToMove = player_being_checked_turn
            self.pins = pins_before_opp_move_gen  # Restore pins that were relevant for player_being_checked_turn's context
            self.inCheck = inCheck_before_opp_move_gen  # Restore inCheck state
            # self.checks doesn't need complex restoration here as it's recalculated in getValidMoves

        return attack_found

    def checkForPinsAndChecks(self):  # This is for the current self.whiteToMove player
        pins = []
        checks = []
        inCheck = False
        if self.whiteToMove:
            enemyColor = 'b'
            allyColor = 'w'
            startRow, startCol = self.whiteKingLocation
        else:
            enemyColor = 'w'
            allyColor = 'b'
            startRow, startCol = self.blackKingLocation

        direction = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for j in range(len(direction)):
            d = direction[j]
            possiblePin = ()
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:
                            break
                    elif endPiece[0] == enemyColor:
                        piece_type = endPiece[1]  # Renamed 'type' to 'piece_type'
                        # FIX 5: Corrected pawn check logic j-indices
                        if (0 <= j <= 3 and piece_type == 'R') or \
                                (4 <= j <= 7 and piece_type == 'B') or \
                                (i == 1 and piece_type == 'p' and (
                                        (enemyColor == 'w' and (j == 4 or j == 5)) or
                                        (enemyColor == 'b' and (j == 6 or j == 7))
                                )) or \
                                (piece_type == 'Q') or \
                                (i == 1 and piece_type == 'K'):
                            if possiblePin == ():
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:
                                pins.append(possiblePin)
                                break
                        else:
                            break
                else:
                    break

        knightMoves = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, 2), (1, 2), (-1, -2), (1, -2)]
        for move_dir in knightMoves:  # Renamed 'move' to 'move_dir'
            endRow = startRow + move_dir[0]
            endCol = startCol + move_dir[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N':
                    inCheck = True
                    checks.append((endRow, endCol, move_dir[0], move_dir[1]))
        return inCheck, pins, checks


class CastleRights():
    def __init__(self, whtieKingSide, blackKingSide, whiteQueenSide, blackQueenSide):
        self.whiteKingSide = whtieKingSide
        self.blackKingSide = blackKingSide
        self.whiteQueenSide = whiteQueenSide
        self.blackQueenSide = blackQueenSide

    def astuple(self): return (self.whiteKingSide, self.blackKingSide, self.whiteQueenSide, self.blackQueenSide)

    def __eq__(self, other): return isinstance(other, CastleRights) and self.astuple() == other.astuple()

    def __hash__(self): return hash(self.astuple())


class Move():
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnpassantMove=False, isCastleMove=False):
        self.startRow, self.startCol = startSq[0], startSq[1]
        self.endRow, self.endCol = endSq[0], endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.isPawnPromotion = (self.pieceMoved == 'wp' and self.endRow == 0) or \
                               (self.pieceMoved == 'bp' and self.endRow == 7)
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove: self.pieceCaptured = 'wp' if self.pieceMoved == 'bp' else 'bp'
        self.isCastleMove = isCastleMove
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def __eq__(self, other):
        return isinstance(other, Move) and self.moveID == other.moveID

    def getChessNotation(self, gs):  # gs is the GameState for context
        notation = ""
        # Pawn moves
        if self.pieceMoved[1] == 'p':
            if self.pieceCaptured != "--" or self.isEnpassantMove:  # Pawn captures
                notation += self.colsToFiles[self.startCol] + "x"
            notation += self.getRankFile(self.endRow, self.endCol)  # Target square
            if self.isPawnPromotion: notation += "=Q"
        # Castle moves
        elif self.isCastleMove:
            if self.endCol - self.startCol == 2:
                notation = "O-O"  # Kingside
            else:
                notation = "O-O-O"  # Queenside
        # Other piece moves
        else:
            notation += self.pieceMoved[1]  # Piece initial (N, B, R, Q, K)
            # Disambiguation (e.g. Rae1 vs Rfe1) is not handled here for simplicity
            if self.pieceCaptured != "--": notation += "x"  # Capture
            notation += self.getRankFile(self.endRow, self.endCol)  # Target square
        if gs.checkmate:  # If the state gs (passed for context) indicates checkmate
            # Check if the player whose turn it *was* (who made this move) delivered checkmate
            if gs.whiteToMove != (self.pieceMoved[0] == 'w'):  # If current turn is opponent of mover
                notation += "#"
        elif gs.inCheck:  # If the state gs indicates the *next* player is in check
            if gs.whiteToMove != (self.pieceMoved[0] == 'w'):  # If current turn is opponent of mover
                if not (self.isCastleMove and gs.checkmate):  # Avoid O-O+ if it's O-O#
                    notation += "+"
        return notation

    def getRankFile(self, row, col):
        return self.colsToFiles[col] + self.rowsToRanks[row]