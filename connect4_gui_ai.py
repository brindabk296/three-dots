import numpy as np
import pygame
import sys
import math

# ----------------------------------
# GAME CONSTANTS
# ----------------------------------

ROW_COUNT = 6
COLUMN_COUNT = 7

PLAYER = 0
AI = 1

PLAYER_PIECE = 1
AI_PIECE = 2

EMPTY = 0

BLUE   = (0, 0, 255)
BLACK  = (0, 0, 0)
RED    = (255, 0, 0)
YELLOW = (255, 255, 0)

# ----------------------------------
# BOARD FUNCTIONS
# ----------------------------------

def create_board():
    return np.zeros((ROW_COUNT, COLUMN_COUNT))

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def is_valid_location(board, col):
    return board[0][col] == 0

def get_next_open_row(board, col):
    for r in range(ROW_COUNT-1, -1, -1):
        if board[r][col] == 0:
            return r

# ----------------------------------
# FIND WINNING POSITIONS
# ----------------------------------

def get_winning_positions(board, piece):
    # Horizontal
    for r in range(ROW_COUNT):
        for c in range(COLUMN_COUNT-3):
            if board[r][c]==piece and board[r][c+1]==piece and board[r][c+2]==piece and board[r][c+3]==piece:
                return [(r,c),(r,c+1),(r,c+2),(r,c+3)]

    # Vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT-3):
            if board[r][c]==piece and board[r+1][c]==piece and board[r+2][c]==piece and board[r+3][c]==piece:
                return [(r,c),(r+1,c),(r+2,c),(r+3,c)]

    # +Diagonal
    for r in range(ROW_COUNT-3):
        for c in range(COLUMN_COUNT-3):
            if board[r][c]==piece and board[r+1][c+1]==piece and board[r+2][c+2]==piece and board[r+3][c+3]==piece:
                return [(r,c),(r+1,c+1),(r+2,c+2),(r+3,c+3)]

    # -Diagonal
    for r in range(3, ROW_COUNT):
        for c in range(COLUMN_COUNT-3):
            if board[r][c]==piece and board[r-1][c+1]==piece and board[r-2][c+2]==piece and board[r-3][c+3]==piece:
                return [(r,c),(r-1,c+1),(r-2,c+2),(r-3,c+3)]

    return None

def winning_move(board, piece):
    return get_winning_positions(board, piece) is not None

# ----------------------------------
# AI MINIMAX
# ----------------------------------

def evaluate_window(window, piece):
    score = 0
    opp = PLAYER_PIECE if piece == AI_PIECE else PLAYER_PIECE

    if window.count(piece) == 4: score += 999
    elif window.count(piece) == 3 and window.count(0) == 1: score += 10
    elif window.count(piece) == 2 and window.count(0) == 2: score += 5

    if window.count(opp) == 3 and window.count(0) == 1: score -= 8
    return score

def score_position(board, piece):
    score = 0

    # Center column preference
    center = [int(i) for i in list(board[:, COLUMN_COUNT//2])]
    score += center.count(piece) * 6

    # Horizontal
    for r in range(ROW_COUNT):
        row = [int(i) for i in list(board[r])]
        for c in range(COLUMN_COUNT-3):
            score += evaluate_window(row[c:c+4], piece)

    # Vertical
    for c in range(COLUMN_COUNT):
        col = [int(i) for i in list(board[:, c])]
        for r in range(ROW_COUNT-3):
            score += evaluate_window(col[r:r+4], piece)

    # Diagonals
    for r in range(ROW_COUNT-3):
        for c in range(COLUMN_COUNT-3):
            score += evaluate_window([board[r+i][c+i] for i in range(4)], piece)

    for r in range(3, ROW_COUNT):
        for c in range(COLUMN_COUNT-3):
            score += evaluate_window([board[r-i][c+i] for i in range(4)], piece)

    return score

def get_valid_locations(board):
    return [c for c in range(COLUMN_COUNT) if is_valid_location(board, c)]

def minimax(board, depth, alpha, beta, maximizing):
    valid = get_valid_locations(board)

    if depth == 0 or winning_move(board, AI_PIECE) or winning_move(board, PLAYER_PIECE):
        if winning_move(board, AI_PIECE): return None, 1e10
        if winning_move(board, PLAYER_PIECE): return None, -1e10
        return None, score_position(board, AI_PIECE)

    if maximizing:
        value = -math.inf
        best_col = np.random.choice(valid)
        for col in valid:
            row = get_next_open_row(board, col)
            temp = board.copy()
            drop_piece(temp, row, col, AI_PIECE)
            _, score = minimax(temp, depth-1, alpha, beta, False)
            if score > value:
                value, best_col = score, col
            alpha = max(alpha, value)
            if alpha >= beta: break
        return best_col, value

    else:
        value = math.inf
        best_col = np.random.choice(valid)
        for col in valid:
            row = get_next_open_row(board, col)
            temp = board.copy()
            drop_piece(temp, row, col, PLAYER_PIECE)
            _, score = minimax(temp, depth-1, alpha, beta, True)
            if score < value:
                value, best_col = score, col
            beta = min(beta, value)
            if alpha >= beta: break
        return best_col, value

# ----------------------------------
# DRAW BOARD
# ----------------------------------

def draw_board(board):
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            pygame.draw.rect(screen, BLUE, (c*SQUARE, r*SQUARE+SQUARE, SQUARE, SQUARE))
            pygame.draw.circle(screen, BLACK, (c*SQUARE+SQUARE//2, r*SQUARE+SQUARE+SQUARE//2), RADIUS)

    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            piece = board[r][c]
            if piece == PLAYER_PIECE:
                color = RED
            elif piece == AI_PIECE:
                color = YELLOW
            else:
                continue

            pygame.draw.circle(
                screen, color,
                (c*SQUARE+SQUARE//2, height-(r*SQUARE+SQUARE//2)),
                RADIUS
            )
    pygame.display.update()

# ----------------------------------
# ONE-TIME ZOOM EFFECT (NO FLICKER)
# ----------------------------------

def pulse_winning_pieces(board, positions, color, duration=200):

    start = pygame.time.get_ticks()
    end = start + duration

    while True:
        now = pygame.time.get_ticks()
        if now >= end:
            break

        t = (now - start) / duration  # 0 → 1
        pulse = math.sin(t * math.pi)  # 0 → 1 → 0 ONE TIME

        zoom_r = int(RADIUS + pulse * 22)

        draw_board(board)

        for (r, c) in positions:
            pygame.draw.circle(
                screen, color,
                (c*SQUARE+SQUARE//2, height-(r*SQUARE+SQUARE//2)),
                zoom_r
            )

        pygame.display.update()
        pygame.time.wait(2)

# ----------------------------------
# MAIN GAME LOOP
# ----------------------------------

pygame.init()

SQUARE = 100
RADIUS = SQUARE//2 - 5
width = COLUMN_COUNT * SQUARE
height = (ROW_COUNT + 1) * SQUARE

screen = pygame.display.set_mode((width, height))
font = pygame.font.SysFont("monospace", 50)
font_small = pygame.font.SysFont("monospace", 25)

while True:

    board = create_board()
    turn = PLAYER
    game_over = False

    draw_board(board)

    while not game_over:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                sys.exit()

            # Preview circle
            if event.type == pygame.MOUSEMOTION and turn == PLAYER and not game_over:
                pygame.draw.rect(screen, BLACK, (0,0,width,SQUARE))
                x = event.pos[0]
                pygame.draw.circle(screen, RED, (x, SQUARE//2), RADIUS)
                pygame.display.update()

            # Player click
            if event.type == pygame.MOUSEBUTTONDOWN and turn == PLAYER:
                col = event.pos[0] // SQUARE

                if is_valid_location(board, col):
                    row = get_next_open_row(board, col)
                    drop_piece(board, row, col, PLAYER_PIECE)

                    if winning_move(board, PLAYER_PIECE):
                        win = get_winning_positions(board, PLAYER_PIECE)
                        pulse_winning_pieces(board, win, RED)

                        pygame.draw.rect(screen, BLACK, (0,0,width,SQUARE))
                        draw_board(board)

                        screen.blit(font.render("Player Wins!", True, RED), (10,10))
                        screen.blit(font_small.render("SPACE = Restart   X = Exit", True, RED), (10,70))
                        pygame.display.update()
                        game_over = True

                    else:
                        turn = AI

                draw_board(board)

        # AI MOVE
        if turn == AI and not game_over:
            col, _ = minimax(board, 5, -math.inf, math.inf, True)

            if is_valid_location(board, col):
                row = get_next_open_row(board, col)
                drop_piece(board, row, col, AI_PIECE)

                if winning_move(board, AI_PIECE):
                    win = get_winning_positions(board, AI_PIECE)
                    pulse_winning_pieces(board, win, YELLOW)

                    pygame.draw.rect(screen, BLACK, (0,0,width,SQUARE))
                    draw_board(board)

                    screen.blit(font.render("AI Wins!", True, YELLOW), (10,10))
                    screen.blit(font_small.render("SPACE = Restart   X = Exit", True, YELLOW), (10,70))
                    pygame.display.update()
                    game_over = True

                else:
                    turn = PLAYER

                draw_board(board)

        # GAME OVER LOOP — FIXED SPACE RESTART
        # GAME OVER LOOP — CLEAN AND CORRECT
    while game_over:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:
                # Restart the FULL game (outer while True loop)
                    board = create_board()
                    turn = PLAYER
                    game_over = False
                    draw_board(board)
                    break   # exit inner for-loop

                if event.key == pygame.K_x:
                    sys.exit()

        if not game_over:
            break  # exit the while game_over loop and restart gameplay