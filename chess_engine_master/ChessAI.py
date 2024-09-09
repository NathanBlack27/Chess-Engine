import random, math

pieceScores = {'k': 0, 'q': 900, 'r': 500, 'b': 310, 'n': 300, 'p': 100}
checkmate = math.inf
maxDepth = 3

def randomMove(legalMoves):
    if len(legalMoves) <= 0:
        pass
    return legalMoves[random.randint(0, len(legalMoves)-1)]

def findBestMove(game_state, legalMoves):
    global bestMove
    bestMove = None
    global count
    count = 0
    # make first recursive call of findMinMax
    evaluation = findMinMax(game_state, legalMoves, maxDepth, -checkmate, checkmate, 1 if game_state.whiteToMove else -1)
    print('Evaluation:', evaluation * (1 if game_state.whiteToMove else -1))
    print('Positions evaluated:', count)
    return bestMove

def findMinMax(game_state, legalMoves, depth, alpha, beta, turn):
    global bestMove
    global count
    if depth == 0:
        count += 1
        return turn * scoreBoard(game_state)
    
    # move ordering here
    # currently only ordering is capturing piece
    orderedMoves = []
    for move in legalMoves:
        if move.pieceCaptured != '-':
            orderedMoves.append(move)
    for move in legalMoves:
        if move.pieceCaptured == '-':
            orderedMoves.append(move)
            

    bestScore = -checkmate
    for move in orderedMoves:
        game_state.makeMove(move)
        '''
        if game_state.checkmate and turn == 1:
            bestMove = move
            return scoreBoard(game_state)
        elif -game_state.checkmate and turn == -1:
            bestMove = move
            return scoreBoard(game_state)
        else:
        '''
        nextMoves = game_state.getLegalMoves()
        score = -findMinMax(game_state, nextMoves, depth - 1, -beta, -alpha, -turn)

        if score > bestScore:
            bestScore = score
            if depth == maxDepth:
                bestMove = move

        game_state.undo()

        if bestScore > alpha:
            alpha = bestScore
        if alpha >= beta:
            break

    return bestScore

def scoreBoard(game_state):
    if game_state.checkmate:
        return -checkmate if game_state.whiteToMove else checkmate
    elif game_state.draw:
        return 0
    
    score = 0

    material = materialScore(game_state.board)
    score = material

    if game_state.inCheck == True: 
        score = score - 50 if game_state.whiteToMove else score + 50

    return score + round(random.uniform(-0.001,0.001), 4) # adding a little randomness for move variety

def materialScore(board):
    material = 0
    for sq in board.keys():
        if board[sq] != '-':
            if board[sq].isupper(): # white pieces
                material += pieceScores[board[sq].lower()]
            else: # black pieces
                material -= pieceScores[board[sq].lower()]

    return material


'''
def moveGenTest(depth):
    if depth == 0:
        return 1
    
    legalMoves = gs.getLegalMoves()
    positions = 0

    for move in legalMoves:
        gs.makeMove(move)
        positions += moveGenTest(depth - 1)
        gs.undo()

    return positions

gs = Engine.GameState()
st = time.time()
print(moveGenTest(3))
et = time.time()
res = et - st
print('Time elapsed:', res)

#if game_state.checkmate:
        #    score = checkmate * -turn
        #elif game_state.draw:
        #    score = 0
        #else:
'''