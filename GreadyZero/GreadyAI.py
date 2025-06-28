import random

pieceScore = {"K" : 0, "Q" : 9, "R" : 5, "B" : 3, "N" : 3, "p": 1}
CHECKMATE = 1000
STALEMATE = 0

def findRandomMove(vaildMoves):
    return vaildMoves[random.randint(0,len(vaildMoves)-1)]


# based on points rather than piece amount
def findBestMove(gs, validMoves):
    turnMultipler = 1 if gs.whiteToMove else -1
    maxScore = -CHECKMATE
    bestMove = None

    for playerMove in validMoves:
        gs.makeMove(playerMove)

        if gs.checkmate:
            score = CHECKMATE
        elif gs.stalemate:
            score = STALEMATE
        else:
            score = turnMultipler * scoreMaterial(gs.board)
        if score > maxScore:
            maxScore = score
            bestMove = playerMove

        gs.undoMove()

    return bestMove


def scoreMaterial(board):
    score = 0

    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b' :
                score -= pieceScore[square[1]]

    return score






