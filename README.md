# Chess-Engine

# This is a chess engine I have created from scratch in Python to better my programming skills.
# The code is quite bloated and likely hard to read, but my goal here is to see if I can do it! And to show off to recruiters I did.

# Main.py file is the driver file which calls Engine.py and ChessAI.py. Responsible for user input, drawing board/pieces, etc.
# Engine.py is where legal move logic is done, as well as reading in FEN notation and updating game state.
# ChessAI.py is where the bot's code for finding the best move is. Current state of the bot is primitive and barely optimized with Alpha-Beta pruning.

# Idea by Eddie Sharick, but I'm adding features and using a fundamentally different method for creating/accessing the squares. I use 0-63 integers to interact with the board, while he does a row/col format.
# https://youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_&si=oJfMp-LRDtapxpN7
