# MinMaxAI.py (Closer to original structure, with fixes and scoreBoard)

import random

pieceScore = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1}
CHECKMATE = 1000
STALEMATE = 0
DEPTH = 3

nextMove = None

def findRandomMove(vaildMoves):
    if not vaildMoves:
        return None
    return vaildMoves[random.randint(0, len(vaildMoves) - 1)]

# --- ScoreBoard and scoreMaterial functions ---
def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b':
                score -= pieceScore[square[1]]
    return score


def scoreBoard(gs):
    if gs.checkmate:
        if gs.whiteToMove:  # White is to move, but is checkmated (by black's last move)
            return -CHECKMATE
        else:  # Black is to move, but is checkmated (by white's last move)
            return CHECKMATE
    elif gs.stalemate:
        return STALEMATE
    return scoreMaterial(gs.board)
# --- End of scoreBoard and scoreMaterial ---


def findMoveMinMax(gs, validMoves, depth, whiteToMove):
    global nextMove  # We are using the global nextMove

    if depth == 0:
        return scoreBoard(gs)  # Use scoreBoard for evaluation at max depth

    current_player_valid_moves = list(validMoves)
    random.shuffle(current_player_valid_moves)

    if whiteToMove:
        maxScore = -CHECKMATE - 1  # Initialize slightly below worst score

        if depth == DEPTH and not nextMove and current_player_valid_moves:
            nextMove = current_player_valid_moves[0]

        for move in current_player_valid_moves:
            gs.makeMove(move)

            if gs.checkmate:  # Opponent (Black) is checkmated by this move
                score = CHECKMATE
            elif gs.stalemate:  # Stalemate
                score = STALEMATE
            else:
                # Get opponent's valid moves. This call updates gs.checkmate/gs.stalemate.
                opponent_valid_moves = gs.getValidMoves()
                if not opponent_valid_moves:
                    # If opponent has no moves, use scoreBoard to evaluate the terminal state
                    score = scoreBoard(gs)
                else:
                    score = findMoveMinMax(gs, opponent_valid_moves, depth - 1, False)

            gs.undoMove()

            if score > maxScore:
                maxScore = score
                if depth == DEPTH:  # Only set global 'nextMove' at the top level of the search
                    nextMove = move
        return maxScore

    else:  # Black to move (minimizing player)
        minScore = CHECKMATE + 1  # Initialize slightly above best score

        if depth == DEPTH and not nextMove and current_player_valid_moves:
            nextMove = current_player_valid_moves[0]

        for move in current_player_valid_moves:
            gs.makeMove(move)

            if gs.checkmate:  # Opponent (White) is checkmated by this move
                score = -CHECKMATE
            elif gs.stalemate:
                score = STALEMATE
            else:
                opponent_valid_moves = gs.getValidMoves()
                if not opponent_valid_moves:
                    score = scoreBoard(gs)
                else:
                    score = findMoveMinMax(gs, opponent_valid_moves, depth - 1, True)

            gs.undoMove()

            if score < minScore:
                minScore = score
                if depth == DEPTH:
                    nextMove = move
        return minScore


#
def findBestMoveMinMax(gs, vaildMoves):
    global nextMove
    nextMove = None

    if not vaildMoves:
        return None  # No move if no valid moves

    # The recursive call will set the global 'nextMove' if a better move is found at DEPTH
    findMoveMinMax(gs, vaildMoves, DEPTH, gs.whiteToMove)
    if nextMove is None and vaildMoves:
        nextMove = findRandomMove(vaildMoves)  # Use your findRandomMove

    return nextMove