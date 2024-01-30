"""
Current state of chess game: current position, move log, possible valid moves, whose turn
Valid move logic
Bot logic

TO WORK ON:
-Fix for undo not working on castling if more than once in a row. Same with FEN position storage
-All FEN cases accounted for?
-UI 
    -Window to set each color as human or AI pregame
    -Window for user choice of pawn promotion

-Start AI
    -Random move algorithm
    -Function for getting all possible positions at certain depth, test compare to broader consensus (checking for legal move bugs)

    -Evaluation function
    -Cache an evaluation/best move for previous positions using FEN notation

"""

class GameState():
    def __init__(self):

        # manually enter FEN here
        self.FEN = ''#rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8'

        # do you want to play from black's perspective?
        self.playAsBlack = False

        self.left_edge = [0,8,16,24,32,40,48,56]
        self.right_edge = [7,15,23,31,39,47,55,63]
        self.directions = {'NW':-9, 'N':-8, 'NE':-7, 'W':-1, 'E':1, 'SW':7, 'S':8, 'SE':9}
        self.moveLog = self.pins = self.checks = [] # pins and checks are lists of tuples of (square of pinned/checking piece, direction outward from king of pin/check)
        self.positionOccurrences = {}
        self.inCheck = self.checkmate = self.draw = False

        if self.FEN == '':
            self.board = {
                0:'r', 1:'n', 2:'b', 3:'q', 4:'k', 5:'b', 6:'n', 7:'r',
                8:'p', 9:'p', 10:'p', 11:'p', 12:'p', 13:'p', 14:'p', 15:'p',
                16:'-', 17:'-', 18:'-', 19:'-', 20:'-', 21:'-', 22:'-', 23:'-',
                24:'-', 25:'-', 26:'-', 27:'-', 28:'-', 29:'-', 30:'-', 31:'-',
                32:'-', 33:'-', 34:'-', 35:'-', 36:'-', 37:'-', 38:'-', 39:'-',
                40:'-', 41:'-', 42:'-', 43:'-', 44:'-', 45:'-', 46:'-', 47:'-',
                48:'P', 49:'P', 50:'P', 51:'P', 52:'P', 53:'P', 54:'P', 55:'P',
                56:'R', 57:'N', 58:'B', 59:'Q', 60:'K', 61:'B', 62:'N', 63:'R',
            }
            self.wKingSq = 60
            self.bKingSq = 4
            self.whiteToMove = True
            self.currCastlingRights = CastlingRights(True, True, True, True) # castling rights for current position
            self.enpassantSq = -1 # 0-63 sq where "phantom" pawn is for en passant
            self.halfMoveClock = 0
            self.fullMoveCounter = 1
            self.positionLog = [self.boardToFEN()]

        else:
            self.readFEN(self.FEN)
            self.positionLog = [self.FEN]

        # list of castling rights for each logged position
        self.castleRightsLog = [CastlingRights(self.currCastlingRights.K, self.currCastlingRights.Q, self.currCastlingRights.k, self.currCastlingRights.q)]

        if self.playAsBlack == True:
            self.board = dict(reversed(self.board.items()))

    def readFEN(self, FEN):
        # Example:
        # rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2
        self.board = {}
        for i in range(64):
            self.board[i] = '-' # empty board position

        spaces = [i for i in range(len(FEN)) if FEN.startswith(' ', i)] # list of indices of spaces
        s = 0
        while s < 64:
            for c in FEN[0 : spaces[0]]:
                if c in ['k','q','r','b','n','p','K','Q','R','B','N','P']:
                    self.board[s] = c
                    if c == 'k':
                        self.bKingSq = s
                    elif c == 'K':
                        self.wKingSq = s
                    s += 1
                elif c.isnumeric():
                    s += int(c)

        self.whiteToMove = True if FEN[spaces[0]+1] == 'w' else False
        self.currCastlingRights = CastlingRights(False, False, False, False) # castling rights for current position
        for r in FEN[spaces[1] : spaces[2]]: # grab castling rights data
            if r == 'K':
                self.currCastlingRights.K = True
            elif r == 'Q':
                self.currCastlingRights.Q = True
            elif r == 'k':
                self.currCastlingRights.k = True
            elif r == 'q':
                self.currCastlingRights.q = True

        self.enpassantSq = self.convertIntNotation(s = (FEN[spaces[2]+1 : spaces[3]])) if FEN[spaces[2]+1] != '-' else -1 # 0-63 sq where "phantom" pawn is for en passant
        self.halfMoveClock = int(FEN[spaces[3]+1 : spaces[4]])
        self.fullMoveCounter = int(FEN[spaces[4]+1 : ])

    def boardToFEN(self):
        # convert game state to FEN string
        FEN = ''

        blankCount = 0
        for sq in self.board:

            if sq in self.left_edge:
                FEN += str(blankCount) if blankCount != 0 else ''
                FEN += '/' if sq != 0 else ''
                blankCount = 0

            if self.board[sq] == '-':
                blankCount += 1
            else:
                FEN += str(blankCount) if blankCount != 0 else ''
                FEN += self.board[sq]
                blankCount = 0

            if blankCount == 8:
                FEN += '8'
                blankCount = 0

        FEN += ' w' if self.whiteToMove else ' b'

        if self.currCastlingRights.K == True or self.currCastlingRights.Q == True or self.currCastlingRights.k == True or self.currCastlingRights.q == True:
            FEN += ' '
        if self.currCastlingRights.K == True:
            FEN += 'K'
        if self.currCastlingRights.Q == True:
            FEN += 'Q'
        if self.currCastlingRights.k == True:
            FEN += 'k'
        if self.currCastlingRights.q == True:
            FEN += 'q'

        intToNotation = {}
        for i in range(8):
            for j in range(8):
                # create dict mapping 0-63 sq to its chess notation sq (eg. 'g3')
                intToNotation[8*i+j] = list(map(chr, range(97, 105)))[j] + str(list(reversed(range(8)))[i]+1)
        FEN = FEN + ' ' + self.convertIntNotation(i = self.enpassantSq) if self.enpassantSq != -1 else FEN + ' -'

        FEN = FEN + ' ' + str(self.halfMoveClock)
        FEN = FEN + ' ' + str(self.fullMoveCounter)

        return FEN

    def makeMove(self, move):
        self.board[move.start] = '-' # make start sqaure empty
        self.board[move.end] = move.pieceMoved # make end square the start piece (overwrite existing piece if applicable)
        self.moveLog.append(move) # log move
        if move.pieceMoved == 'K':
            self.wKingSq = move.end
        elif move.pieceMoved == 'k':
            self.bKingSq = move.end

        # for 50-move draw (if gets to 100, 50-move draw)
        self.halfMoveClock = 0 if (move.pieceMoved.lower() == 'p' or move.pieceCaptured != '-') else self.halfMoveClock +1

        # pawn promotion
        if move.promotion:
            self.board[move.end] = move.promotionChoice if self.whiteToMove == False else move.promotionChoice.upper()

        # capturing en passant
        if move.pieceMoved == 'P' and move.isEnpassant:
            self.board[move.end+8] = '-'
        elif move.pieceMoved == 'p' and move.isEnpassant:
            self.board[move.end-8] = '-'

        # flagging square as en passant-able
        if move.pieceMoved.lower() == 'p' and abs(move.start - move.end) == 16: # only on 2-square advances
            self.enpassantSq = (move.start + move.end) // 2
        else:
            self.enpassantSq = -1
        
        #castling moves
        if move.isCastle:
            if move.end - move.start == 2: # kingside castling
                self.board[move.end-1] = self.board[move.end+1]
                self.board[move.end+1] = '-'
            else: # queenside castling
                self.board[move.end+1] = self.board[move.end-2]
                self.board[move.end-2] = '-'

        # update castling rights
        self.updateCastlingRights(move)
        self.castleRightsLog.append(CastlingRights(self.currCastlingRights.K, self.currCastlingRights.Q, self.currCastlingRights.k, self.currCastlingRights.q))

        if not self.whiteToMove: # if this was a black move, increment move counter ready for next move
            self.fullMoveCounter += 1
        self.whiteToMove = not self.whiteToMove # switch whose turn it is

        # store FEN strings in positionLog and positionOccurances to check for 3-move repetition
        if move.pieceCaptured != '-':
            # for optimization, reset 3-move dict on capture (repetition not possible before vs after capture, so no need to compare)
            # bug created here for undoing FIXME
            self.positionOccurrences = {}
        newPos = self.boardToFEN()
        self.positionLog.append(newPos)
        self.positionOccurrences[newPos[0:newPos.find(' ')]] = self.positionOccurrences.get(newPos[0:newPos.find(' ')], 0) + 1

    def updateCastlingRights(self, move):
        if move.pieceMoved == 'K': # white king moves
            self.currCastlingRights.K = False
            self.currCastlingRights.Q = False
        elif move.pieceMoved == 'k': # black king moves
            self.currCastlingRights.k = False
            self.currCastlingRights.q = False
        elif move.pieceMoved == 'R':
            if move.start == 56: # queenside white rook
                self.currCastlingRights.Q = False
            elif move.start == 63: # kingside white rook
                self.currCastlingRights.K = False
        elif move.pieceMoved == 'r':
            if move.start == 0: # queenside black rook
                self.currCastlingRights.q = False
            elif move.start == 7: # kingside black rook
                self.currCastlingRights.k = False

        if (move.pieceCaptured.lower() == 'r') and (move.end in [0,7,56,63]): # if a rook in corner is captured
            if move.end == 0:
                self.currCastlingRights.q = False
            elif move.end == 7:
                self.currCastlingRights.k = False
            elif move.end == 56:
                self.currCastlingRights.Q = False
            elif move.end == 63:
                self.currCastlingRights.K = False

    def undo(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.start] = move.pieceMoved # set start square to the piece moved (which is stored in the move object class)
            self.board[move.end] = move.pieceCaptured # replace end square with stored captured piece (can be '--', which is fine)
            self.halfMoveClock -= 1
            self.whiteToMove = not self.whiteToMove # switch whose turn it is
            if move.pieceMoved == 'K':
                self.wKingSq = move.start
            elif move.pieceMoved == 'k':
                self.bKingSq = move.start

            if self.whiteToMove == False: # if undoing black move
                self.fullMoveCounter -= 1
            # decrement half move counter
            if self.halfMoveClock != 0:
                self.halfMoveClock -= 1
                
            # undo en passant capture
            if move.isEnpassant:
                if move.pieceMoved == 'P':
                    self.board[move.end+8] = 'p'
                elif move.pieceMoved == 'p':
                    self.board[move.end-8] = 'P'
                self.board[move.end] = '-'
                self.enpassantSq = move.end
            else: # undo any other move
                self.enpassantSq = -1

            # case where undoing multiple moves in a row, reset en passant square based on previous move info
            if move.pieceMoved.lower() == 'p' and abs(move.start - move.end) == 16: # only on 2-square advances
                self.enpassantSq = (move.start + move.end) // 2

            # restore castle rights
            self.castleRightsLog.pop()
            self.currCastlingRights = self.castleRightsLog[-1]

            # undo FEN log and occurrences
            undonePos = self.positionLog.pop()
            self.positionOccurrences[undonePos[0:undonePos.find(' ')]] -= 1

            # undo castling
            if move.isCastle:
                if move.end - move.start == 2: # kingside castling
                    self.board[move.end+1] = self.board[move.end-1]
                    self.board[move.end-1] = '-'
                else: # queenside castling
                    self.board[move.end-2] = self.board[move.end+1]
                    self.board[move.end+1] = '-'

    def getLegalMoves(self):
        moves = []
        kingSq = self.wKingSq if self.whiteToMove else self.bKingSq

        self.inCheck, self.pins, self.checks = self.pinsAndChecks(kingSq)

        if self.inCheck:
            if len(self.checks) == 1: # if only one check (because 2 check is possible)
                moves = self.allPossibleMoves()
                checkSq, checkDirection = self.checks[0]
                pieceChecking = self.board[checkSq]
                canMoveTo = [] # list of legal squares ally pieces can move to, given the king in check
                if pieceChecking.lower() == 'n': # if knight giving check
                    canMoveTo = [checkSq] # no blocking (must capture knight)
                else: # checking piece not knight (can be blocked)
                    for i in range(1,8): # outward from king to create squares ally piece can move to
                        validSq = kingSq + (i * self.directions[checkDirection])
                        canMoveTo.append(validSq)
                        if validSq == checkSq: # append to canMoveTo until capturing checking piece, then stop
                            break
                for i in range(len(moves) -1, -1, -1): # iterate backwards through possible moves, removing moves if don't block check/capture checking piece
                    if moves[i].pieceMoved.lower() != 'k': # moving piece not a king, must block or capture
                        if not moves[i].end in canMoveTo:
                            moves.remove(moves[i])
            else: # len(self.checks) == 2
                self.getKingMoves(kingSq, moves) # king must move. Append to moves only valid king moves
        else: # not in check
            moves = self.allPossibleMoves()

        # checking for game end
        if len(moves) == 0: # no legal moves in current board position
            if self.inCheck:
                self.checkmate = True
                c = 'Black' if self.whiteToMove else 'White'
                print(c + ' wins the game!')
            else:
                self.draw = True
                print('Draw by stalemate.')
        else: # make sure checkmate/stalemate don't act up (because of undo and such)
            self.checkmate = False
            self.draw = False
        if self.halfMoveClock >= 100:
            self.draw = True
            print('Draw by 50-move rule.')

        if 3 in self.positionOccurrences.values():
            self.draw = True
            print('Draw by repetition.')

        return moves

    def allPossibleMoves(self):
        # logic for how each piece moves, disregarding circumstantial rules (such as check)
        moves = []
        for sq in self.board.keys():
            color = self.board[sq].isupper() # True if piece is white, False if piece is black
            if color == self.whiteToMove: # If piece color == whose turn
                if self.board[sq].lower() == 'p':
                    self.getPawnMoves(sq, moves)
                if self.board[sq].lower() == 'n':
                    self.getKnightMoves(sq, moves)
                if self.board[sq].lower() == 'b':
                    self.getBishopMoves(sq, moves)
                if self.board[sq].lower() == 'r':
                    self.getRookMoves(sq, moves)
                if self.board[sq].lower() == 'q':
                    self.getQueenMoves(sq, moves)
                if self.board[sq].lower() == 'k':
                    self.getKingMoves(sq, moves)
        return moves

    def getPawnMoves(self, sq, moves): # get pawn moves at specific 0-63 sq and add to moves list
        pinned = False
        pinDirection = '' 
        for i in range(len(self.pins) -1, -1, -1):
            if self.pins[i][0] == sq: # if pawn is pinned
                pinned = True
                pinDirection = self.pins[i][1]
                self.pins.remove(self.pins[i])

        if self.whiteToMove: # white pawns
            if (self.board[sq-8] == '-'):
                if (not pinned) or (pinDirection == 'N'): # if 1 square above is empty and pins allow movement
                    if (8 <= sq <= 15):
                        self.generatePromotions(sq, sq-8, moves)
                    else:
                        moves.append(Move(sq, sq-8, self.board)) # allow white pawn to move 1 square
                    if (48 <= sq <= 55) and (self.board[sq-16] == '-'): # if 2 squares above is empty AND white pawn on starting square (AND square 1 above empty)
                        moves.append(Move(sq, sq-16, self.board)) # allow white pawn to move 2 squares
            # capturing diagonally
            if ((not pinned) or (pinDirection == 'NW')) and (sq not in self.left_edge):
                if self.board[sq-9].islower():
                    if (8 <= sq <= 15):
                        self.generatePromotions(sq, sq-9, moves)
                    else:
                        moves.append(Move(sq, sq-9, self.board))
                elif sq-9 == self.enpassantSq:
                    moves.append(Move(sq, sq-9, self.board, isEnpassant=True)) 
            if ((not pinned) or (pinDirection == 'NE')) and (sq not in self.right_edge):
                if self.board[sq-7].islower():
                    if (8 <= sq <= 15):
                        self.generatePromotions(sq, sq-7, moves)
                    else:
                        moves.append(Move(sq, sq-7, self.board))
                elif sq-7 == self.enpassantSq:
                    moves.append(Move(sq, sq-7, self.board, isEnpassant=True)) 
                
        else: # black pawns
            if self.board[sq+8] == '-': # if 1 square below is empty
                if (not pinned) or (pinDirection == 'S'):
                    if (48 <= sq <= 55):
                        self.generatePromotions(sq, sq+8, moves)
                    else:
                        moves.append(Move(sq, sq+8, self.board)) # allow black pawn to move 1 square
                    if (8 <= sq <= 15) and (self.board[sq+16] == '-'): # if 2 squares below is empty AND black pawn on starting square (AND square 1 below empty)
                        moves.append(Move(sq, sq+16, self.board)) # allow black pawn to move 2 squares
            # capturing diagonally
            if ((not pinned) or (pinDirection == 'SW')) and (sq not in self.left_edge):
                if self.board[sq+7].isupper():
                    if (48 <= sq <= 55):
                        self.generatePromotions(sq, sq+7, moves)
                    else:
                        moves.append(Move(sq, sq+7, self.board)) 
                elif sq+7 == self.enpassantSq:
                    moves.append(Move(sq, sq+7, self.board, isEnpassant=True)) 
            if ((not pinned) or (pinDirection == 'SE')) and (sq not in self.right_edge):
                if self.board[sq+9].isupper():
                    if (48 <= sq <= 55):
                        self.generatePromotions(sq, sq+9, moves)
                    else:
                        moves.append(Move(sq, sq+9, self.board))
                elif sq+9 == self.enpassantSq:
                    moves.append(Move(sq, sq+9, self.board, isEnpassant=True)) 

    def generatePromotions(self, start, end, moves):
        for p in ['q','r','b','n']:
            moves.append(Move(start, end, self.board, promotionChoice = p))

    def getKnightMoves(self, sq, moves): # get knight moves at specific 0-63 sq and add to moves list
        pinned = False
        for i in range(len(self.pins) -1, -1, -1):
            if self.pins[i][0] == sq: # if knight is pinned
                pinned = True
                self.pins.remove(self.pins[i])

        if pinned: # if a knight is pinned, it cannot move at all
            targets = []
        else:
            targets = [sq-17, sq-15, sq-10, sq-6, sq+6, sq+10, sq+15, sq+17]
        for t in targets:
            if (0 <= t <= 63): # eliminate above and below board
                if (self.board[t].isupper() != self.whiteToMove) or (self.board[t] == '-'): # check if potential move is empty OR enemy piece
                    if (sq%8) == 0: # a file knight
                        if (t == sq-10) or (t == sq+6) or (t == sq-17) or (t == sq+15): # remove -10, +6, -17, and +15
                            continue
                    elif (sq%8) == 1: # b file knight
                        if (t == sq-10) or (t == sq+6): # remove -10 and +6
                            continue
                    elif (sq%8) == 6: # g file knight
                        if (t == sq-6) or (t == sq+10): # remove -6 and +10
                            continue
                    elif (sq%8) == 7: # h file knight
                        if (t == sq-6) or (t == sq+10) or (t == sq-15) or (t == sq+17): # remove -6, +10, -15, and +17
                            continue
                    moves.append(Move(sq, t, self.board))

    def getBishopMoves(self, sq, moves): # get bishop moves at specific 0-63 sq and add to moves list
        pinned = False
        pinDirection = '' 
        for i in range(len(self.pins) -1, -1, -1):
            if self.pins[i][0] == sq: # if bishop is pinned
                pinned = True
                pinDirection = self.pins[i][1]
                if self.board[sq].lower == 'b': # only remove pin from list if not queen
                    self.pins.remove(self.pins[i])

        for d in ['NW', 'SW', 'SE', 'NE']:
            for i in range(1,8): # iterate until edge of board, enemy piece, or friendly piece (max 7)
                target = sq+(i*self.directions[d])
                if (target > 63) or (target < 0): # we hit top or bottom edge of board
                    break
                if ((d == 'NW') or (d == 'SW')) and ((target-7 in self.left_edge) or (target+9 in self.left_edge)): # if iterating NW or SW (left), and previous target was on left edge
                    break
                if ((d == 'SE') or (d == 'NE')) and ((target+7 in self.right_edge) or (target-9 in self.right_edge)): # if iterating NE or SE (right), and previous target was on right edge
                    break

                if (not pinned) or (pinDirection == d) or (self.directions[pinDirection] == -self.directions[d]):
                    if self.board[target] == '-': # if target square is empty
                        moves.append(Move(sq, target, self.board))
                    elif self.board[target].isupper() != self.whiteToMove: # target square is enemy piece
                        moves.append(Move(sq, target, self.board)) # allow enemy capture, 
                        break # but then move on to next direction
                    else: # target square is friendly piece
                        break

    def getRookMoves(self, sq, moves): # get rook moves at specific 0-63 sq and add to moves list
        pinned = False
        pinDirection = '' 
        for i in range(len(self.pins) -1, -1, -1):
            if self.pins[i][0] == sq: # if rook is pinned
                pinned = True
                pinDirection = self.pins[i][1]
                if self.board[sq].lower == 'r': # only remove pin from list if not queen
                    self.pins.remove(self.pins[i])

        for d in ['N', 'S', 'W', 'E']:
            for i in range(1,8): # iterate until edge of board, enemy piece, or friendly piece (max 7)
                target = sq+(i*self.directions[d])
                if (target > 63) or (target < 0): # we hit top or bottom edge of board
                    break
                if d == 'W' and (target+1 in self.left_edge): # if iterating left, and previous target was on left edge
                    break
                elif d == 'E' and (target-1 in self.right_edge): # if iterating right, and previous target was on right edge
                    break

                if (not pinned) or (pinDirection == d) or (self.directions[pinDirection] == -self.directions[d]):
                    if self.board[target] == '-': # if target square is empty
                        moves.append(Move(sq, target, self.board))
                    elif self.board[target].isupper() != self.whiteToMove: # target square is enemy piece
                        moves.append(Move(sq, target, self.board)) # allow enemy capture, 
                        break # but then move on to next direction
                    else: # target square is friendly piece
                        break

    def getQueenMoves(self, sq, moves): # get queen moves at specific 0-63 sq and add to moves list
        self.getBishopMoves(sq, moves)
        self.getRookMoves(sq, moves)

    def getKingMoves(self, sq, moves): # get king moves at specific 0-63 sq and add to moves list
        for d in self.directions:
            target = sq+self.directions[d]
            if (0 <= target <= 63): # eliminate above and below board
                if ((d == 'NW') or (d == 'W') or (d == 'SW')) and (sq in self.left_edge): # if king on left edge, cant go left
                    continue
                if ((d == 'NE') or (d == 'E') or (d == 'SE')) and (sq in self.right_edge): # if king on right edge, cant go right
                    continue
                elif (self.board[target].isupper() != self.whiteToMove) or (self.board[target] == '-'): # check if potential move is empty OR enemy piece
                    tempCheck = self.pinsAndChecks(target)[0]
                    if not tempCheck: # if king on new square does not flag as check, append move
                        moves.append(Move(sq, target, self.board))
        
        # generate castling
        if not self.inCheck and (sq == 4 or sq == 60):
            self.kingsideCastleMoves(sq, moves)
            self.queensideCastleMoves(sq, moves)
    
    def kingsideCastleMoves(self, start, moves):
        if self.board[start+1] == '-' and self.board[start+2] == '-':
            for sq in [start+1, start+2]: # check squares to right
                if self.pinsAndChecks(sq)[0] == True: # if square is attacked
                    return
            if self.whiteToMove and self.currCastlingRights.K:
                moves.append(Move(start, start+2, self.board, isCastle = True))
            if not self.whiteToMove and self.currCastlingRights.k:
                moves.append(Move(start, start+2, self.board, isCastle = True))
                
    def queensideCastleMoves(self, start, moves):    
        if self.board[start-1] == '-' and self.board[start-2] == '-' and self.board[start-3] == '-':
            for sq in [start-1, start-2]: # check squares to left
                if self.pinsAndChecks(sq)[0] == True: # if square is attacked
                    return
            if self.whiteToMove and self.currCastlingRights.Q:
                moves.append(Move(start, start-2, self.board, isCastle = True))
            if not self.whiteToMove and self.currCastlingRights.q:
                moves.append(Move(start, start-2, self.board, isCastle = True))

    def pinsAndChecks(self, start): # also serve as isAttacked function (just pass in any square)
        pins = [] # list of tuples: (sq of piece being pinned to a king, direction it is from king)
        checks = [] # list of tuples: (sq of piece giving check to a king, direction it's coming from) 
        # if checking piece is knight, tuple is (sq of knight, 'n')
        inCheck = False
        for d in self.directions: # iterating over each direction [NW, N, NE, W, E, SW, S, SE]
            possiblePin = () # tuple containing (pinned piece square, direction outward from king)
            possibleEPPin = [] # list of two 0-63 squares that allied pawn could be pinned from en passant
            for i in range(1,8): # iterate outward starting from king
                end = start+(i*+self.directions[d])

                # check if still on board
                if (end > 63) or (end < 0): # we hit top or bottom edge of board
                    break
                elif (d == 'NW' or d == 'W' or d == 'SW') and (end+1 in self.left_edge): # if we're iterating left/west and previous end sq was on left edge
                    break
                elif (d == 'NE' or d == 'E' or d == 'SE') and (end-1 in self.right_edge): # if we're iterating right/east and previous end sq was on right edge
                    break

                endPiece = self.board[end]
                type = endPiece.lower()
                if endPiece == '-':
                    continue

                elif endPiece.isupper() == self.whiteToMove and endPiece.lower() != 'k': # if allied piece                        
                    if possiblePin == (): # have not seen allied piece in this direction yet
                        possiblePin = (end, d) # add (square of pinned piece, direction)
                    else: # if already seen allied piece in this direction
                    # no pin or check is possible in this direction
                        break

                elif endPiece.isupper() == (not self.whiteToMove): # if enemy piece
                    # verifying here if enemy piece can possibly see king
                    # for example, if direction is a diagoonal and piece is a bishop
                    if  ((d == 'NW' or d == 'NE' or d == 'SW' or d == 'SE') and type == 'b') or\
                        ((d == 'N' or d == 'W' or d == 'E' or d == 'S') and type == 'r') or\
                        (type == 'q') or\
                        (type == 'k' and i == 1) or\
                        (i == 1 and type == 'p' and (((start-end == 7 or start-end == 9) and self.whiteToMove) or ((start-end == -7 or start-end == -9) and not self.whiteToMove))):
                        if possiblePin == (): # no allied piece in between means this is a check
                            inCheck = True
                            checks.append((end, d))
                            break
                        else: # allied piece is between king and enemy piece
                            if possiblePin[0] in possibleEPPin:
                                # pin this pawn from en passant-ing, but only vertically
                                pins.append((possiblePin[0] , 'S')) if not self.whiteToMove else pins.append((possiblePin[0] , 'N'))
                            else:
                                pins.append(possiblePin)
                            break
                    else: # enemy piece cannot see king (for example, piece orthogonal and is a bishop)
                        # check for enemy pawn that could be captured en passant
                        if type == 'p' and ((self.whiteToMove and end-8 == self.enpassantSq) or (not self.whiteToMove and end+8 == self.enpassantSq)):
                            possibleEPPin = [end+1, end-1]
                            # no break this direction yet to detect other enemy pieces beyond enemy pawn
                        else: # no need to keep checking this direction
                            break 

        knightMoves = [start-17, start-15, start-10, start-6, start+6, start+10, start+15, start+17]
        for end in knightMoves:
            # dont care if above/below board, ally piece, or not a knight
            if (end < 0) or (end > 63) or (self.board[end].isupper() == self.whiteToMove) or (self.board[end].lower() != 'n'):
                continue
            # pass over knight squares that can't see king
            if (start%8) == 0: # a file king
                if (end == start-10) or (end == start+6) or (end == start-17) or (end == start+15): # remove -10, +6, -17, and +15
                    continue
            elif (start%8) == 1: # b file king
                if (end == start-10) or (end == start+6): # remove -10 and +6
                    continue
            elif (start%8) == 6: # g file king
                if (end == start-6) or (end == start+10): # remove -6 and +10
                    continue
            elif (start%8) == 7: # h file king
                if (end == start-6) or (end == start+10) or (end == start-15) or (end == start+17): # remove -6, +10, -15, and +17
                    continue
            # if code gets here, we know we are looking at an enemy knight that can see the king
            inCheck = True
            checks.append((end, 'n'))

        return inCheck, pins, checks

    def convertIntNotation(self, i = -1, s = ''):
        # pass in 0-63 integer OR board coordinate (such as 'g5') to convert to its other form
        intToNotation = {}
        for a in range(8):
            for b in range(8):
                # create dict mapping 0-63 sq to its chess notation sq (eg. 'g3')
                intToNotation[8*a+b] = list(map(chr, range(97, 105)))[b] + str(list(reversed(range(8)))[a]+1) 
        notationToInt = {val:key for key,val in intToNotation.items()} 

        if i != -1:
            converted = intToNotation[i] 
        elif s != '':
            converted = notationToInt[s]

        return converted

class Move():      
    def __init__(self, start, end, board, isEnpassant = False, isCastle = False, promotionChoice = 'q'):
        self.start = start # 0-63
        self.end = end # 0-63
        self.pieceMoved = board[start] # save piece from start square (to be put on end square)
        self.pieceCaptured = board[end] # save piece from end square

        # promotion flag
        self.promotion = (self.pieceMoved == 'P' and 0 <= self.end <= 7) or (self.pieceMoved == 'p' and 56 <= self.end <= 63)
        self.promotionChoice = promotionChoice

        # en passant flag
        self.isEnpassant = isEnpassant
        if self.isEnpassant:
            self.pieceCaptured = 'p' if self.pieceMoved == 'P' else 'P'

        # castling move flag
        self.isCastle = isCastle
    
    def getChessNotation(self, start, end): # INCOMPLETE. Need to add 'x' for capture, '+' for check, etc
        # start and end should be 0-63 integers

        # to convert from board integer to chess notation: (file, rank) and back
        # for example: [52 , 36] <-> e2e4
        intToNotation = {}
        for i in range(8):
            for j in range(8):
                # create dict mapping 0-63 sq to its chess notation sq (eg. 'g3')
                intToNotation[8*i+j] = list(map(chr, range(97, 105)))[j] + str(list(reversed(range(8)))[i]+1) 
        #notationToInt = {val:key for key,val in intToNotation.items()} 

        return intToNotation[start] + intToNotation[end]
    
    def __eq__(self, other): # something called overriding equals? 
        # This checks if some element (in this case the chess notation) is the same between class objects
        # I'm using this to manually hard code Move objects in moves list in allPossibleMoves function. Since manually inserting a move is different than clicking to generate a move...?
        if isinstance(other, Move):
            return self.getChessNotation(self.start, self.end) == other.getChessNotation(other.start, other.end)
        return False
    

class CastlingRights():
    def __init__(self, K, Q, k, q):
        self.K = K
        self.Q = Q
        self.k = k
        self.q = q
