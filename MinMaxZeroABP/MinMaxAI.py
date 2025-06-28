# MinMaxAI.py (Closer to original structure, with fixes and scoreBoard)

import random

pieceScore = {"K": 0, "Q": 900, "R": 500, "B": 325, "N": 300, "p": 100}
CHECKMATE = 2000
STALEMATE = 0
DEPTH = 4
QDEPTHLIMIT = 6

nextMove = None

# --- Table/Value ---
MOBILITYWEIGHTS = {
    'opening': {'p': 3, 'N': 4, 'B': 4, 'R': 2, 'Q': 3, 'K': 0},
    'middle': {'p': 3, 'N': 2, 'B': 3, 'R': 3, 'Q': 4, 'K': 1},
    'end': {'p': 3, 'N': 2, 'B': 5, 'R': 5, 'Q': 5, 'K': 1},
}

pawnPST = [
    [0 ,  0 ,  0 ,  0 ,  0 ,  0 ,  0 ,  0 ],  # Rank 8 (Promotion line - handled by promotion logic usually, but can give incentive)
    [50, 50 , 50 , 50 , 50 , 50 , 50 , 50 ],  # Rank 7 (Strongly encourage advancing)
    [10, 10 , 20 , 30 , 30 , 20 , 10 , 10 ],  # Rank 6
    [5 ,  5 , 10 , 25 , 25 , 10 , 5  , 5  ],  # Rank 5 (Central pawns get more valuable)
    [0 ,  0 ,  0 , 20 , 20 , 0  , 0  , 0  ],  # Rank 4
    [5 , -5 , -10, 0  ,  0 , -10, -5 , 5  ],  # Rank 3 (Slightly discourage early overextension without support)
    [5 ,  10, 10 , -20, -20, 10 , 10 , 5  ],  # Rank 2 (Initial pawn positions, -20 for d/e if blocked/hard to advance)
    [0 ,  0 ,  0 , 0  , 0  , 0  , 0  , 0  ]   # Rank 1
]

knightPST = [
    [-50, -40, -30, -30, -30, -30, -40, -50], # Row 0 (8th rank)
    [-40, -20,   0,   5,   5,   0, -20, -40], # Row 1 (7th rank)
    [-30,   5,  10,  15,  15,  10,   5, -30], # Row 2 (6th rank)
    [-30,  10,  15,  20,  20,  15,  10, -30], # Row 3 (5th rank)
    [-30,  10,  15,  20,  20,  15,  10, -30], # Row 4 (4th rank)
    [-30,   0,  15,   5,   5,  15,   0, -30], # Row 5 (3rd rank)
    [-40, -20,   0,   5,   5,   0, -20, -40], # Row 6 (2nd rank)
    [-50, -40, -30, -30, -30, -30, -40, -50]  # Row 7 (1st rank)
]

bishopPST = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],  # g2/b2 (row 1, col 1 and 6 for white) get a bonus
    [-10,   0,   0,   5,   5,   0,   0, -10],  # Squares along the diagonal from fianchetto
    [-10,  10,   0,   5,   5,   0,  10, -10],
    [-10,   5,  10,   5,   5,  10,   5, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,  15,   5,   5,   5,   5,  15, -10],  # g7/b7 (mirrored) would also be good for black
    [-20, -10, -10, -10, -10, -10, -10, -20]
]

rookPST = [
    [  0,   0,   0,   0,   0,   0,   0,   0],   # Rank 8
    [  5,  10,  10,  10,  10,  10,  10,   5],   # Rank 7 (Rooks on 7th are great)
    [ -5,   0,   0,   0,   0,   0,   0,  -5],   # Rank 6
    [ -5,   0,   0,   0,   0,   0,   0,  -5],   # Rank 5
    [ -5,   0,   0,   0,   0,   0,   0,  -5],   # Rank 4
    [ -5,   0,   0,   0,   0,   0,   0,  -5],   # Rank 3
    [ -5,   0,   0,   0,   0,   0,   0,  -5],   # Rank 2
    [  0,   0,   0,   5,   5,   0,   0,   0]    # Rank 1 (Slight preference for central files if developing)
]

queenPST = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20], # Rank 8
    [-10,   0,   0,   0,   0,   0,   0, -10], # Rank 7
    [-10,   0,   5,   5,   5,   5,   0, -10], # Rank 6
    [ -5,   0,   5,   5,   5,   5,   0,  -5], # Rank 5 (Central and active)
    [  0,   0,   5,   5,   5,   5,   0,  -5], # Rank 4
    [-10,   5,   5,   5,   5,   5,   0, -10], # Rank 3
    [-10,   0,   5,   0,   0,   0,   0, -10], # Rank 2
    [-20, -10, -10,  -5,  -5, -10, -10, -20]  # Rank 1 (Discourage bringing out too early)
]

kingPSTMiddlegame = [
    [-30, -40, -40, -50, -50, -40, -40, -30], # Rank 8
    [-30, -40, -40, -50, -50, -40, -40, -30], # Rank 7
    [-30, -40, -40, -50, -50, -40, -40, -30], # Rank 6 (Generally unsafe)
    [-30, -40, -40, -50, -50, -40, -40, -30], # Rank 5
    [-20, -30, -30, -40, -40, -30, -30, -20], # Rank 4
    [-10, -20, -20, -20, -20, -20, -20, -10], # Rank 3
    [ 20,  20,   0,   0,   0,   0,  20,  20], # Rank 2 (Squares after castling short are safer)
    [ 20,  30,  10,   0,   0,  10,  30,  20]  # Rank 1 (g1/h1/c1/b1 after castling)
]

kingPSTEndgame = [
    [-50, -40, -30, -20, -20, -30, -40, -50], # Rank 8
    [-30, -20, -10,   0,   0, -10, -20, -30], # Rank 7
    [-30, -10,  20,  30,  30,  20, -10, -30], # Rank 6 (King becomes an attacker)
    [-30, -10,  30,  40,  40,  30, -10, -30], # Rank 5 (Centralize the king)
    [-30, -10,  30,  40,  40,  30, -10, -30], # Rank 4
    [-30, -10,  20,  30,  30,  20, -10, -30], # Rank 3
    [-30, -30,   0,   0,   0,   0, -30, -30], # Rank 2
    [-50, -30, -30, -30, -30, -30, -30, -50]  # Rank 1
]

# --- End Table/Value ---
def findRandomMove(validMoves):  # Corrected parameter name
    if not validMoves:
        return None
    return validMoves[random.randint(0, len(validMoves) - 1)]


# --- Material ---
def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b':
                score -= pieceScore[square[1]]
    return score

# --- Mobility ---
def mobilityEvaluation(gs, forWhitePlayer, currentPhaseWeights):
    playerMobilityScore = 0

    for r in range(8):
        for c in range(8):
            pieceStr = gs.board[r][c]
            if pieceStr != '--':
                pieceColor = pieceStr[0]
                pieceType = pieceStr[1]

                if (forWhitePlayer and pieceColor == 'w') or \
                        (not forWhitePlayer and pieceColor == 'b'):

                    numMovesForPiece = 0
                    if pieceType == 'p':
                        numMovesForPiece = countPseudoLegalPawnMoves(gs, r, c, forWhitePlayer)
                    elif pieceType == 'N':
                        numMovesForPiece = countPseudoLegalKnightMoves(gs, r, c, forWhitePlayer)
                    elif pieceType == 'B':
                        numMovesForPiece = countPseudoLegalBishopMoves(gs, r, c, forWhitePlayer)
                    elif pieceType == 'R':
                        numMovesForPiece = countPseudoLegalRookMoves(gs, r, c, forWhitePlayer)
                    elif pieceType == 'Q':
                        numMovesForPiece = countPseudoLegalQueenMoves(gs, r, c, forWhitePlayer)
                    elif pieceType == 'K':
                        numMovesForPiece = countPseudoLegalKingMoves(gs, r, c, forWhitePlayer)

                    playerMobilityScore += numMovesForPiece * currentPhaseWeights.get(pieceType, 0)

    return playerMobilityScore

def countPseudoLegalPawnMoves(gs, r, c, isWhitePlayer):
    count = 0
    if isWhitePlayer:
        if r > 0 and gs.board[r - 1][c] == "--":
            count += 1
            if r == 6 and gs.board[r - 2][c] == "--":
                count += 1
        if r > 0 and c > 0 and gs.board[r - 1][c - 1][0] == 'b': count += 1
        if r > 0 and c < 7 and gs.board[r - 1][c + 1][0] == 'b': count += 1
        if gs.enpassantPossible:  # Check if enpassantPossible is not None or empty tuple
            if (r - 1, c - 1) == gs.enpassantPossible and c > 0: count += 1
            if (r - 1, c + 1) == gs.enpassantPossible and c < 7: count += 1
    else:
        if r < 7 and gs.board[r + 1][c] == "--":
            count += 1
            if r == 1 and gs.board[r + 2][c] == "--":
                count += 1
        if r < 7 and c > 0 and gs.board[r + 1][c - 1][0] == 'w': count += 1
        if r < 7 and c < 7 and gs.board[r + 1][c + 1][0] == 'w': count += 1
        if gs.enpassantPossible:  # Check if enpassantPossible is not None or empty tuple
            if (r + 1, c - 1) == gs.enpassantPossible and c > 0: count += 1
            if (r + 1, c + 1) == gs.enpassantPossible and c < 7: count += 1
    return count
def countPseudoLegalKnightMoves(gs, r, c, isWhitePlayer):
    count = 0
    allyColor = 'w' if isWhitePlayer else 'b'
    knightMoves = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, 2), (1, 2), (-1, -2), (1, -2)]
    for dr, dc in knightMoves:
        endRow, endCol = r + dr, c + dc
        if 0 <= endRow < 8 and 0 <= endCol < 8:
            if gs.board[endRow][endCol][0] != allyColor:
                count += 1
    return count


def _countSlidingPieceMoves(gs, r, c, isWhitePlayer, directions):  # Helper remains "private-like"
    count = 0
    allyColor = 'w' if isWhitePlayer else 'b'
    enemyColor = 'b' if isWhitePlayer else 'w'
    for dr, dc in directions:
        for i in range(1, 8):
            endRow, endCol = r + dr * i, c + dc * i
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = gs.board[endRow][endCol]
                if endPiece == "--":
                    count += 1
                elif endPiece[0] == enemyColor:
                    count += 1
                    break
                elif endPiece[0] == allyColor:
                    break
            else:
                break
    return count


def countPseudoLegalBishopMoves(gs, r, c, isWhitePlayer):
    directions = [(-1, -1), (1, 1), (-1, 1), (1, -1)]
    return _countSlidingPieceMoves(gs, r, c, isWhitePlayer, directions)


def countPseudoLegalRookMoves(gs, r, c, isWhitePlayer):
    directions = [(-1, 0), (0, 1), (0, -1), (1, 0)]
    return _countSlidingPieceMoves(gs, r, c, isWhitePlayer, directions)


def countPseudoLegalQueenMoves(gs, r, c, isWhitePlayer):
    directions = [(-1, -1), (1, 1), (-1, 1), (1, -1), (-1, 0), (0, 1), (0, -1), (1, 0)]
    return _countSlidingPieceMoves(gs, r, c, isWhitePlayer, directions)


def countPseudoLegalKingMoves(gs, row, col, isWhitePlayer):
    count = 0
    allyColor = 'w' if isWhitePlayer else 'b'
    kingMoves = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dr, dc in kingMoves:
        endRow, endCol = row + dr, col + dc
        if 0 <= endRow < 8 and 0 <= endCol < 8:
            if gs.board[endRow][endCol][0] != allyColor:
                count += 1
    return count

def getGamePhase(gs):
    materialCountNoPawnsKings = 0
    numQueensWhite = 0
    numQueensBlack = 0

    whiteMinorPieces = 0
    blackMinorPieces = 0
    whiteMajorPieces = 0  # Rooks, Queens
    blackMajorPieces = 0

    for row in range(8):
        for col in range(8):
            pieceStr = gs.board[row][col]
            if pieceStr != '--':
                color = pieceStr[0]
                pieceType = pieceStr[1]
                if pieceType == 'Q':
                    if color == 'w':
                        numQueensWhite += 1
                    else:
                        numQueensBlack += 1
                if pieceType in ['N', 'B']:
                    if color == 'w':
                        whiteMinorPieces += 1
                    else:
                        blackMinorPieces += 1
                if pieceType in ['R', 'Q']:
                    if color == 'w':
                        whiteMajorPieces += 1
                    else:
                        blackMajorPieces += 1

                if pieceType not in ['p', 'K']:
                    materialCountNoPawnsKings += 1
    isEndgame = False
    if numQueensWhite == 0 and numQueensBlack == 0:
        isEndgame = True
    elif numQueensWhite > 0 and whiteMajorPieces + whiteMinorPieces <= 2:
        if numQueensBlack == 0 or (numQueensBlack > 0 and blackMajorPieces + blackMinorPieces <= 2):
            isEndgame = True
    elif numQueensBlack > 0 and blackMajorPieces + blackMinorPieces <= 2:
        if numQueensWhite == 0 or (numQueensWhite > 0 and whiteMajorPieces + whiteMinorPieces <= 2):
            isEndgame = True
    if isEndgame:
        return 'end'
    if len(gs.moveLog) < 20 and materialCountNoPawnsKings > 8:
        return 'opening'
    return 'middle'

# --- End Mobility ---

# --- Structure/Positioning ---
def evaluatePiecePositions(gs):
    score = 0
    game_phase = getGamePhase(gs)  # You already have this

    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece != '--':
                p_color, p_type = piece[0], piece[1]

                current_pst_value = 0
                if p_type == 'p':
                    current_pst_value = pawnPST[r][c] if p_color == 'w' else pawnPST[7 - r][c]
                elif p_type == 'N':
                    current_pst_value = knightPST[r][c] if p_color == 'w' else knightPST[7 - r][c]
                elif p_type == 'B':
                    current_pst_value = bishopPST[r][c] if p_color == 'w' else bishopPST[7 - r][c]
                elif p_type == 'R':
                    current_pst_value = rookPST[r][c] if p_color == 'w' else rookPST[7 - r][c]
                elif p_type == 'Q':
                    current_pst_value = queenPST[r][c] if p_color == 'w' else queenPST[7 - r][c]
                elif p_type == 'K':
                    if game_phase == 'end':
                        current_pst_value = kingPSTEndgame[r][c] if p_color == 'w' else \
                        kingPSTEndgame[7 - r][c]
                    else:  # opening/middlegame
                        current_pst_value = kingPSTMiddlegame[r][c] if p_color == 'w' else \
                        kingPSTMiddlegame[7 - r][c]

                if p_color == 'w':
                    score += current_pst_value
                else:  # black piece
                    score -= current_pst_value  # Subtract black's positional advantage (from white's perspective)
    return score

# --- End of Position/Structure ---



# --- ScoreBoard ---
def scoreBoard(gs):
    if gs.checkmate:
        # gs.whiteToMove is True if it's White's turn but they are checkmated (Black won)
        # gs.whiteToMove is False if it's Black's turn but they are checkmated (White won)
        if gs.whiteToMove:
            return -CHECKMATE  # Black wins
        else:
            return CHECKMATE  # White wins
    elif gs.stalemate:
        return STALEMATE
    currentScore = scoreMaterial(gs.board)

    # 2. Mobility Score
    currentPhase = getGamePhase(gs)
    phaseSpecificWeights = MOBILITYWEIGHTS[currentPhase]

    whiteMobilityScore = mobilityEvaluation(gs, True, phaseSpecificWeights)
    blackMobilityScore = mobilityEvaluation(gs, False, phaseSpecificWeights)

    mobilityBonus = whiteMobilityScore - blackMobilityScore
    currentScore += mobilityBonus

    positionScore = evaluatePiecePositions(gs)
    currentScore += positionScore

    return currentScore
# --- End of Score ---

def findMoveMinMaxABPruning(gs, validMoves, depth, alpha, beta,
                            turnWhite):
    global nextMove

    if depth == 0:
        return quiecenceSearch(gs, alpha, beta, turnWhite, QDEPTHLIMIT)

    current_player_valid_moves = list(validMoves)

    if depth == DEPTH and not nextMove and current_player_valid_moves:
        nextMove = current_player_valid_moves[0]

    if turnWhite:  # Maximizing player (White)
        maxScore = -CHECKMATE - 1  # Initialize slightly below worst score for White
        for move in current_player_valid_moves:
            gs.makeMove(move)
            opponent_valid_moves = gs.getValidMoves()

            if gs.checkmate:  # Black is checkmated by White's move
                score = CHECKMATE
            elif gs.stalemate:  # Stalemate after White's move
                score = STALEMATE
            else:  # Black has moves, recurse for Black's turn
                score = findMoveMinMaxABPruning(gs, opponent_valid_moves, depth - 1, alpha, beta, False)

            gs.undoMove()

            if score > maxScore:
                maxScore = score
                if depth == DEPTH:
                    nextMove = move

            alpha = max(alpha, maxScore)  # White (maximizer) updates alpha
            if alpha >= beta:  # Pruning condition
                break
        return maxScore

    else:  # Minimizing player
        minScore = CHECKMATE + 1  # Initialize slightly above best score for White
        for move in current_player_valid_moves:
            gs.makeMove(move)
            opponent_valid_moves = gs.getValidMoves()

            if gs.checkmate:  # White is checkmated by Black's move
                score = -CHECKMATE
            elif gs.stalemate:  # Stalemate after Black's move
                score = STALEMATE
            else:  # White has moves, recurse for White's turn
                score = findMoveMinMaxABPruning(gs, opponent_valid_moves, depth - 1, alpha, beta, True)

            gs.undoMove()

            if score < minScore:
                minScore = score
                if depth == DEPTH:
                    nextMove = move

            beta = min(beta, minScore)  # Black (minimizer) updates beta
            if beta <= alpha:  # Pruning condition
                break
        return minScore


def findBestMoveMinMax(gs, validMoves):  # Corrected parameter name
    global nextMove
    nextMove = None

    if not validMoves:
        return None

    findMoveMinMaxABPruning(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE, gs.whiteToMove)
    if nextMove is None and validMoves:
        # print("MinMaxAI: nextMove was None after search, choosing random move.")
        nextMove = findRandomMove(validMoves)

    return nextMove

def quiecenceSearch(gs, alpha, beta, turnWhite, qDepthRemain):
    # If there is no more capture/tactic
    standPatScore = scoreBoard(gs)

    if turnWhite:
        if standPatScore >= beta:
            return beta
        alpha = max(alpha, standPatScore)
    else:
        if standPatScore <= alpha:
            return alpha
        beta = min(beta, standPatScore)

    if qDepthRemain == 0:
        return standPatScore

    allLegalMoves = gs.getValidMoves()
    captureMoves = []

    for move in allLegalMoves:
        if move.pieceCaptured != '--':
            captureMoves.append(move)

    if not captureMoves and not gs.inCheck:
        return standPatScore

    if turnWhite:
        maxEval = standPatScore
        for move in captureMoves:
            gs.makeMove(move)
            score = quiecenceSearch(gs, alpha, beta, False, qDepthRemain - 1)
            gs.undoMove()
            maxEval = max(maxEval, score)
            alpha = max(alpha, maxEval)

            if alpha >= beta:
                break

        return maxEval
    else:
        minEval = standPatScore
        for move in captureMoves:
            gs.makeMove(move)
            score = quiecenceSearch(gs, alpha, beta, True, qDepthRemain - 1)
            gs.undoMove()
            minEval = min(minEval, score)
            beta = min(beta, minEval)
            if alpha >= beta:
                break

        return minEval




