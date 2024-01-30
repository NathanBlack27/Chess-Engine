"""
Driver File. Responsible for user input (right click to make move, left click to undo), 
drawing board/pieces from current position, other graphics
"""

import pygame as p
import Engine, ChessAI

width = height = 400
dimension = 8
sq_size = height // dimension
fps = 15
images = {} # image dict for later ease of use

def setup():
    global screen, clock
    p.init()
    screen = p.display.set_mode((width, height)) # create window
    p.display.set_caption('Chess') # change window name
    clock = p.time.Clock()
    loadImages() # only do this once, before game running in while loop

def loadImages():
    pieces = {'wP':'P', 'wN':'N', 'wB':'B', 'wR':'R', 'wQ':'Q', 'wK':'K',
              'bP':'p', 'bN':'n', 'bB':'b', 'bR':'r', 'bQ':'q', 'bK':'k'}
    for piece in pieces:
        # add each piece image to dict with index 'piece' ('P', 'N', ...)
        images[pieces[piece]] = p.transform.scale(p.image.load('chess_piece_images/' + piece + '.png'), (sq_size, sq_size))
        # access a piece image for drawing with image[piece]. Used in drawPieces function

def main():
    setup()
    game_state = Engine.GameState() # initialize game state from engine file
    legalMoves = game_state.getLegalMoves() # call this to generate possible moves for current position
    # do NOT call this every frame. It is 'spensive
    moveMade = False

    currSq = -1 # 0-63 int describing square currently selected (-1 is none selected)
    moveCandidate = [] # list of up to two integers describing a move user intends
                       # for example: [52, 36] -> Piece e2 to e4
    global choice
    choice = ''
    gameOver = False
    whitePlayer = True # true if human playing white
    blackPlayer = True # true if human playing black

    done = False
    while not done:
        humanTurn = (game_state.whiteToMove and whitePlayer) or (not game_state.whiteToMove and blackPlayer)
        # the following is done once per frame
        for e in p.event.get():
            if e.type == p.QUIT: # if mouse press red X,
                done = True # quit program

            elif e.type == p.MOUSEBUTTONDOWN: # what to do with user clicks
                if (p.mouse.get_pressed()[0] == True) and (gameOver == False) and (humanTurn): # if left clicked and game hasn't finished
                    location = p.mouse.get_pos() # location[0,1] is (x,y) pixel clicked on
                    col = location[0] // sq_size
                    row = (location[1] // sq_size) * 8
                    if currSq == (row + col): # check for user clicking same square twice
                        currSq = -1 # deselect the square
                        moveCandidate = [] # reset move 
                    else:
                        currSq = row + col if game_state.playAsBlack == False else 63 - (row + col) # 0-63
                        moveCandidate.append(currSq) # add selected square to moveCandidate 

                elif p.mouse.get_pressed()[2] == True: # if right clicked
                    game_state.undo() # undo previous move
                    moveMade = True # flag to re-generate legal moves from new position

            elif e.type == p.KEYDOWN: # what to do with key presses
                if e.key == p.K_z: # the Z key is pressed
                    # reset game to initial position
                    game_state = Engine.GameState()
                    legalMoves = game_state.getLegalMoves()
                    currSq = -1
                    moveCandidate = []
                    moveMade = False 

        if len(moveCandidate) == 2: # once we have start and end clicks
            move = Engine.Move(start = moveCandidate[0], end = moveCandidate[1], board = game_state.board) # make a move object with user clicks
            if move.promotion:
                print("Use Q, R, B, or N on your keyboard to select promoted piece.")
                choice = waitForKeypress() # proceed when user presses Q, R, B, or N only
                move = Engine.Move(start = moveCandidate[0], end = moveCandidate[1], board = game_state.board, promotionChoice = choice)
            #print(move.getChessNotation(moveCandidate[0], moveCandidate[1])) # print this for debugging purposes (can delete later)
            for m in range(len(legalMoves)):
                if move.getChessNotation(move.start, move.end) == legalMoves[m].getChessNotation(legalMoves[m].start, legalMoves[m].end) and (move.promotionChoice == legalMoves[m].promotionChoice): # compare user generated move with each element in list of legal moves
                    game_state.makeMove(legalMoves[m]) # actually making the move (more precisely, the engine-generated legal move that matches user-inputted move)
                    moveMade = True # flag as a move made so we can re-generate all possible legal moves this frame
                    currSq = -1 # resetting the user input clicks
                    moveCandidate = []
            if moveMade == False: # if user inputted move != one of the legal moves
                moveCandidate = [currSq]

        # AI make move
        if not gameOver and not humanTurn: 
            AImove = ChessAI.randomMove(legalMoves)
            game_state.makeMove(AImove)
            moveMade = True

        if moveMade == True: # if a move (or undo) was made this frame, re-generate legal moves for new position
            legalMoves = game_state.getLegalMoves()
            moveMade = False
            gameOver = True if game_state.checkmate or game_state.draw else False

        # finish this frame by drawing board and ticking clock
        drawGameState(screen, game_state, currSq, legalMoves)
        p.display.flip()
        clock.tick(fps) 

def drawGameState(screen, game_state, currSq, legalMoves):
    drawSquares(screen, currSq, legalMoves, game_state) # squares are drawn over previously drawn images
    drawPieces(screen, game_state) # draw current board state pieces over squares

def drawSquares(screen, sq, moves, game_state):
    # drawing light/dark squares, highlighting noteworthy squares
    color = [(116,148,172), (218,228,232), (250, 236, 132), (233,132,119), (175,175,175)] # dark, light, selected sq, king in check, legal moves circle
    for horz in range(4):
        for vert in range(4):
            #create top-left 2x2 corner, repeat 4 times horz and 4 times vert
            wsq1 = p.Rect(2*horz*sq_size, 2*vert*sq_size, sq_size, sq_size) # x,y position on screen; width,height
            wsq2 = p.Rect(sq_size + 2*horz*sq_size, sq_size + 2*vert*sq_size, sq_size, sq_size)
            dsq1 = p.Rect(sq_size + 2*horz*sq_size, 2*vert*sq_size, sq_size, sq_size) 
            dsq2 = p.Rect(2*horz*sq_size, sq_size + 2*vert*sq_size, sq_size, sq_size)
            p.draw.rect(screen, color[1], wsq1)
            p.draw.rect(screen, color[0], dsq1)
            p.draw.rect(screen, color[1], wsq2)
            p.draw.rect(screen, color[0], dsq2)

    if 0 <= sq <= 63: # sq = -1 if nothing selected, so no highlight
        # highlight for currSq selected
        highlight = p.Rect((flip(sq) % 8)*sq_size, (flip(sq) // 8)*sq_size, sq_size, sq_size) if game_state.playAsBlack else p.Rect((sq % 8)*sq_size, (sq // 8)*sq_size, sq_size, sq_size)
        p.draw.rect(screen, color[2], highlight)

        # highlight legal moves for selected piece
        for m in moves: # iterating over current legal moves
            if m.start == sq: # legal move possibility == selected sq
                circleCenter = ((flip(m.end) % 8)*sq_size + (sq_size/2), (flip(m.end) // 8)*sq_size + (sq_size/2)) if game_state.playAsBlack else ((m.end % 8)*sq_size + (sq_size/2), (m.end // 8)*sq_size + (sq_size/2))
                if m.pieceCaptured == '-': # normal circle on blank squares
                    p.draw.circle(screen, color[4], circleCenter, round(sq_size/6))
                else: # larger hollow circle on captures
                    p.draw.circle(screen, color[4], circleCenter, round(sq_size/2), round(sq_size/10))

    if game_state.inCheck:
        # highlight king if in check
        kingSq = game_state.wKingSq if game_state.whiteToMove else game_state.bKingSq
        highlight = p.Rect((flip(kingSq) % 8)*sq_size, (flip(kingSq) // 8)*sq_size, sq_size, sq_size) if game_state.playAsBlack else p.Rect((kingSq % 8)*sq_size, (kingSq // 8)*sq_size, sq_size, sq_size)
        p.draw.rect(screen, color[3], highlight)

def drawPieces(screen, game_state):
    if game_state.playAsBlack == False: # draw pieces from white's perspective
        for i in game_state.board.keys():
            if game_state.board[i] != '-':
                screen.blit(images[game_state.board[i]], p.Rect((i % 8)*sq_size-1 if game_state.board[i].lower()=='p' else (i % 8)*sq_size, (i // 8)*sq_size , sq_size, sq_size)) # grab dict index and draw associated image on board[i]
    else: # black's perspective
        for i in game_state.board.keys():
            if game_state.board[i] != '-':
                screen.blit(images[game_state.board[i]], p.Rect((flip(i) % 8)*sq_size-1 if game_state.board[i].lower()=='p' else (flip(i) % 8)*sq_size, (flip(i) // 8)*sq_size , sq_size, sq_size)) # grab dict index and draw associated image on board[i]

def waitForKeypress():
    while True:
        for e in p.event.get():
            if e.type == p.KEYDOWN:
                if e.key == p.K_q:
                    return 'q'
                elif e.key == p.K_r:
                    return 'r'
                elif e.key == p.K_b:
                    return 'b'
                elif e.key == p.K_n:
                    return'n' 

def flip(sq):
    return 63 - sq
                    
main()
