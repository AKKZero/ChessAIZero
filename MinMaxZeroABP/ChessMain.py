import pygame as p
import ChessEngine, MinMaxAI

BOARD_WIDTH = BOARD_HEIGHT = 512  #400 if it doesn't work well
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15 #just for animation
IMAGE = {}

#Scorll Content
SCROLL_BAR_WIDTH = 15
SCROLL_BAR_COLOR = "darkgray"
SCROLL_BAR_COLOR2 = "lightgray"
MIN_SCROLL_THUMB_HEIGHT = 20
SCROLL_SPEED = 30


def loadImages():
    pieces = ['wp', 'wR', 'wB', 'wN', 'wK', 'wQ', 'bp', 'bR', 'bB', 'bN', 'bK', 'bQ'] #easier to access anywhere
    for piece in pieces:
        IMAGE[piece] = p.transform.scale(p.image.load("image/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))


def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    moveLogFont = p.font.SysFont('Arial', 28, False, False)
    clock = p.time.Clock()
    screen.fill(p.Color('white'))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False
    animate = False

    # print(gs.board) # OPEN THIS TO HELP WITH DEBUGGING MOVES
    loadImages() # only do this once or FPS goes down

    running = True

    sqSelected = ()
    playerClicks = []

    gameOver = False


    # If both true then PlayerVsPlayer
    player1 = True # Human:White AI:Black
    player2 = True # Human:Black AI:White

    scrollYOffset = 0
    autoScrollBottom = True # This should auto scroll when new moves are made.

    while running:
        isHumanTurn = (gs.whiteToMove and player1) or (not gs.whiteToMove and player2)
        moveLogPanelRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)

        for event in p.event.get():
            if event.type == p.QUIT:
                running = False
            elif event.type == p.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not gameOver and isHumanTurn:
                        location = p.mouse.get_pos()  # x, y location of the mouse
                        col = location[0] // SQ_SIZE
                        row = location[1] // SQ_SIZE

                        if sqSelected == (row, col) or col >= 8: # if user clicked the square already
                            sqSelected = ()
                            playerClicks = []
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected)

                        if len(playerClicks) == 2:
                            move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                            print(f"HUMAN TRY MOVE: {move.getChessNotation(gs)}")
                            for i in range(0, len(validMoves)):
                                if move == validMoves[i]:
                                    gs.makeMove(validMoves[i])
                                    moveMade = True
                                    animate = True
                                    sqSelected = () # reset user's clicks
                                    playerClicks = []
                            if not moveMade:
                                playerClicks = [sqSelected]
                # If the player move the thumb then we should stop auto scroll
                elif event.button == 4:
                    if moveLogPanelRect.collidepoint(p.mouse.get_pos()):
                        scrollYOffset -= 30
                        autoScrollBottom = False
                elif event.button == 5:
                    if moveLogPanelRect.collidepoint(p.mouse.get_pos()):
                        scrollYOffset += 30
                        autoScrollBottom = False
            # This would undo the move when z is pressed.......USE FOR DEBUGGING ONLY
            elif event.type == p.KEYDOWN:
                if event.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    gameOver = False
                #This would restart the game......USE FOR DEBUGGING ONLY
                elif event.key == p.K_r:
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False

        #Here for AI move finding logic
        """print(f"Loop Top: Turn: {'White' if gs.whiteToMove else 'Black'}, gameOver: {gameOver}, Checkmate: {gs.checkmate}, Stalemate: {gs.stalemate}")"""
        if not gameOver and not isHumanTurn:
            AImove = MinMaxAI.findBestMoveMinMax(gs, validMoves)
            if AImove is None:
                print(f"AI returned None. gs.checkmate={gs.checkmate}, gs.stalemate={gs.stalemate}.")
            '''if gs.whiteToMove:
                print("This is the white move made", AImove)  #THIS IS USE FOR DEBUGGING
            else:
                print("This is the black move made", AImove)'''

            if AImove:
                gs.makeMove(AImove)
                moveMade = True
                animate = True
        if moveMade:
            previous_player_was_white = not gs.whiteToMove
            print(f"  Move made by: {'White' if previous_player_was_white else 'Black'}")
            if animate:
                animationMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False

        currentTotalLogHeight = drawGameState(screen, gs, validMoves, sqSelected, moveLogFont, scrollYOffset)

        # --- Clamp scroll_y_offset and handle auto-scroll ---
        if autoScrollBottom:
            if currentTotalLogHeight > MOVE_LOG_PANEL_HEIGHT:
                scrollYOffset = currentTotalLogHeight - MOVE_LOG_PANEL_HEIGHT
            else:
                scrollYOffset = 0
            # auto_scroll_to_bottom = False # Uncomment if you want auto-scroll only for one frame

        # General clamping for scroll_y_offset
        if currentTotalLogHeight <= MOVE_LOG_PANEL_HEIGHT:
            scrollYOffset = 0
        else:
            max_scroll = currentTotalLogHeight - MOVE_LOG_PANEL_HEIGHT
            scrollYOffset = max(0, min(scrollYOffset, max_scroll))


        if gs.checkmate:
            gameOver = True
            if gs.whiteToMove:
                drawText(screen, "Black Win by checkmate")
            else:
                drawText(screen, "White Win by checkmate")
        elif gs.stalemate:
            gameOver = True
            drawText(screen, "Stalemate")



        clock.tick(MAX_FPS)
        p.display.flip()

def highlightSquares(screen, gs, validMove, squaresSelected):
    if squaresSelected != ():
        row, col = squaresSelected
        if gs.board[row][col][0] == ('w' if gs.whiteToMove else 'b'):
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQ_SIZE, row * SQ_SIZE))
            s.fill(p.Color('yellow'))

            for move in validMove:
                if move.startRow == row and move.startCol == col:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))



def drawGameState(screen, gs, validMoves, squaresSelected, moveLogFont, scrollYOffset):
    drawBoard(screen)
    highlightSquares(screen, gs, validMoves, squaresSelected)
    drawPieces(screen, gs.board)
    totalLogHeight = drawMoveLog(screen, gs, moveLogFont, scrollYOffset)
    return totalLogHeight  # Return this for scroll clamping

def drawMoveLog(screen, gs, font, scrollOffset):
    moveLogRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = str(int(i/2 + 1)) + ". " + moveLog[i].getChessNotation(gs) + " "
        if i+1 < len(moveLog):
            moveString += moveLog[i+1].getChessNotation(gs)
        moveTexts.append(moveString)
    padding = 5
    lineSpacing = 2
    current_y_in_log_content = padding

    for i in range(len(moveTexts)):
        text = moveTexts[i]
        textObj = font.render(text, True, p.Color('green'))
        blit_y_on_screen = moveLogRect.top + current_y_in_log_content - scrollOffset
        if blit_y_on_screen + textObj.get_height() > moveLogRect.top and \
                blit_y_on_screen < moveLogRect.bottom:
                    screen.blit(textObj, (moveLogRect.left + padding, blit_y_on_screen))
        current_y_in_log_content += textObj.get_height() + lineSpacing

    totalLogContentHeight = current_y_in_log_content

    #draw Scroll bar
    if totalLogContentHeight > moveLogRect.height:
        scrollbarTrackX = moveLogRect.right - SCROLL_BAR_WIDTH
        ScrollbarTrackRect = p.Rect(scrollbarTrackX, moveLogRect.top, SCROLL_BAR_WIDTH, moveLogRect.height)
        p.draw.rect(screen, p.Color(SCROLL_BAR_COLOR), ScrollbarTrackRect)

        visableRatio = moveLogRect.height / totalLogContentHeight
        thumbHeight = max(MIN_SCROLL_THUMB_HEIGHT, moveLogRect.height * visableRatio)

        scrollableTrackArea = moveLogRect.height - thumbHeight
        scrollableTrackDistance = totalLogContentHeight - moveLogRect.height

        currentRatio = 0.0
        if scrollableTrackDistance > 0:
            clampedScrollY = max(0, min(scrollOffset, scrollableTrackDistance))
            currentRatio = clampedScrollY / scrollableTrackDistance

        calculated_thumb_y = moveLogRect.top + currentRatio * scrollableTrackArea
        scrollbarThumbRect = p.Rect(int(scrollbarTrackX), int(calculated_thumb_y), int(SCROLL_BAR_WIDTH), int(thumbHeight))
        p.draw.rect(screen, p.Color(SCROLL_BAR_COLOR2), scrollbarThumbRect)

    return totalLogContentHeight



def drawBoard(screen):
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for y in range(DIMENSION):
        for x in range(DIMENSION):
            if (x + y) % 2 == 0:
                color = colors[0]
            else:
                color = colors[1]

            p.draw.rect(screen, color, p.Rect(x * SQ_SIZE, y * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawPieces(screen, board):
    for y in range(DIMENSION):
        for x in range(DIMENSION):
            piece = board[y][x]
            if piece != "--":
                screen.blit(IMAGE[piece], p.Rect(x * SQ_SIZE, y * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def animationMove(move, screen, board, clock):
    global colors
    coords = []
    dR, dC = move.endRow - move.startRow, move.endCol - move.startCol
    framesPerSquare = 10
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare

    for frame in range(frameCount + 1):
        aRow, aCol =(move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)

        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)

        if move.pieceCaptured != '--':
            screen.blit(IMAGE[move.pieceCaptured], endSquare)
        screen.blit(IMAGE[move.pieceMoved], p.Rect(aCol*SQ_SIZE, aRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(250)


def drawText(screen, text):
    font = p.font.SysFont("Arial", 32, True, False)
    textObj = font.render(text, 0, p.Color('#686868'))
    textLoc = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - textObj.get_width() / 2, BOARD_HEIGHT / 2 - textObj.get_height() / 2)
    screen.blit(textObj, textLoc)
    textObj = font.render(text, 0, p.Color('#000000'))
    screen.blit(textObj, textLoc.move(2,2))




if __name__ == '__main__':
    main()

