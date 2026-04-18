import pygame
import sys
import time

import connectfour as cf

pygame.init()

# ─── Window & Layout ─────────────────────────────────────────────────────────

CELL_SIZE = 90
COLS = cf.COLS
ROWS = cf.ROWS

BOARD_WIDTH = COLS * CELL_SIZE
BOARD_HEIGHT = ROWS * CELL_SIZE
TOP_BAR = 100
BOTTOM_BAR = 80

WIDTH = BOARD_WIDTH
HEIGHT = TOP_BAR + BOARD_HEIGHT + BOTTOM_BAR

RADIUS = CELL_SIZE // 2 - 8

# ─── Colors ──────────────────────────────────────────────────────────────────

BLUE_DARK   = (20,  50, 120)
BLUE_MED    = (30,  70, 160)
BLACK       = (10,  10,  20)
WHITE       = (255, 255, 255)
RED_PIECE   = (220,  40,  40)
RED_GLOW    = (255, 100, 100)
YELLOW_PIECE= (240, 190,  10)
YELLOW_GLOW = (255, 225,  80)
EMPTY_HOLE  = (15,  35,  90)
GRAY        = (140, 140, 160)
GREEN       = ( 60, 200,  80)

# ─── Fonts ───────────────────────────────────────────────────────────────────

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Connect Four — AI")

font_lg  = pygame.font.Font("OpenSans-Regular.ttf", 32)
font_med = pygame.font.Font("OpenSans-Regular.ttf", 22)
font_sm  = pygame.font.Font("OpenSans-Regular.ttf", 16)

# ─── Game State ──────────────────────────────────────────────────────────────

user   = None          # Which piece the human plays (R or Y)
board  = cf.initial_state()
ai_turn = False
win_cells = []         # Highlighted winning cells


def get_win_cells(board):
    """
    Returns a list of (row, col) tuples for the winning 4 cells.
    """
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for r in range(cf.ROWS):
        for c in range(cf.COLS):
            p = board[r][c]
            if p is None:
                continue
            for dr, dc in directions:
                cells = [(r + i * dr, c + i * dc) for i in range(4)]
                if all(
                    0 <= nr < cf.ROWS and 0 <= nc < cf.COLS and board[nr][nc] == p
                    for nr, nc in cells
                ):
                    return cells
    return []


def draw_board(board, hover_col=None):
    """
    Draws the full game board.
    """
    screen.fill(BLACK)

    # Board background
    board_rect = pygame.Rect(0, TOP_BAR, BOARD_WIDTH, BOARD_HEIGHT)
    pygame.draw.rect(screen, BLUE_DARK, board_rect)
    pygame.draw.rect(screen, BLUE_MED, board_rect, 3)

    # Hover indicator (column highlight)
    if hover_col is not None and not cf.terminal(board):
        hover_rect = pygame.Rect(hover_col * CELL_SIZE, TOP_BAR, CELL_SIZE, BOARD_HEIGHT)
        hover_surf = pygame.Surface((CELL_SIZE, BOARD_HEIGHT), pygame.SRCALPHA)
        hover_surf.fill((255, 255, 255, 20))
        screen.blit(hover_surf, (hover_col * CELL_SIZE, TOP_BAR))

    # Cells
    for r in range(ROWS):
        for c in range(COLS):
            cx = c * CELL_SIZE + CELL_SIZE // 2
            cy = TOP_BAR + r * CELL_SIZE + CELL_SIZE // 2
            cell = board[r][c]
            is_win = (r, c) in win_cells

            if cell == cf.RED:
                color = RED_GLOW if is_win else RED_PIECE
            elif cell == cf.YELLOW:
                color = YELLOW_GLOW if is_win else YELLOW_PIECE
            else:
                color = EMPTY_HOLE

            pygame.draw.circle(screen, color, (cx, cy), RADIUS)

            # Win cell ring
            if is_win:
                pygame.draw.circle(screen, WHITE, (cx, cy), RADIUS, 3)

    # Grid lines
    for c in range(1, COLS):
        pygame.draw.line(screen, BLUE_MED,
                         (c * CELL_SIZE, TOP_BAR),
                         (c * CELL_SIZE, TOP_BAR + BOARD_HEIGHT), 1)
    for r in range(1, ROWS):
        pygame.draw.line(screen, BLUE_MED,
                         (0, TOP_BAR + r * CELL_SIZE),
                         (BOARD_WIDTH, TOP_BAR + r * CELL_SIZE), 1)


def draw_top(text, color=WHITE):
    """
    Draws the status text in the top bar.
    """
    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, TOP_BAR))
    surf = font_lg.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, TOP_BAR // 2))
    screen.blit(surf, rect)


def draw_preview(hover_col, current_player):
    """
    Draws a floating preview piece above the hovered column.
    """
    if hover_col is None:
        return
    cx = hover_col * CELL_SIZE + CELL_SIZE // 2
    cy = TOP_BAR // 2 + 10
    color = RED_PIECE if current_player == cf.RED else YELLOW_PIECE
    pygame.draw.circle(screen, color, (cx, cy), RADIUS - 4)


def draw_bottom(board):
    """
    Draws the bottom bar — column numbers.
    """
    y = TOP_BAR + BOARD_HEIGHT
    pygame.draw.rect(screen, BLUE_DARK, (0, y, WIDTH, BOTTOM_BAR))
    for c in range(COLS):
        cx = c * CELL_SIZE + CELL_SIZE // 2
        label = font_sm.render(str(c + 1), True, GRAY)
        screen.blit(label, label.get_rect(center=(cx, y + BOTTOM_BAR // 2)))


def draw_again_button():
    """
    Draws the Play Again button after game over.
    """
    btn = pygame.Rect(WIDTH // 2 - 100, TOP_BAR + BOARD_HEIGHT + 15, 200, 50)
    pygame.draw.rect(screen, BLUE_MED, btn, border_radius=10)
    pygame.draw.rect(screen, WHITE, btn, 2, border_radius=10)
    label = font_med.render("Play Again", True, WHITE)
    screen.blit(label, label.get_rect(center=btn.center))
    return btn


def draw_choose_screen():
    """
    Draws the initial player-selection screen.
    """
    screen.fill(BLACK)

    title = font_lg.render("Connect Four", True, WHITE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 70)))

    sub = font_med.render("Choose your side", True, GRAY)
    screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 115)))

    # Red button
    red_btn = pygame.Rect(WIDTH // 2 - 220, 200, 190, 60)
    pygame.draw.rect(screen, RED_PIECE, red_btn, border_radius=12)
    rl = font_med.render("Play as Red", True, WHITE)
    screen.blit(rl, rl.get_rect(center=red_btn.center))

    # Yellow button
    yel_btn = pygame.Rect(WIDTH // 2 + 30, 200, 190, 60)
    pygame.draw.rect(screen, YELLOW_PIECE, yel_btn, border_radius=12)
    yl = font_med.render("Play as Yellow", True, BLACK)
    screen.blit(yl, yl.get_rect(center=yel_btn.center))

    # Info
    info = font_sm.render("Red always goes first.  AI plays the other side.", True, GRAY)
    screen.blit(info, info.get_rect(center=(WIDTH // 2, 310)))

    # Rules
    rules = [
        "Drop pieces into columns — press 1–7 or click.",
        "First to connect 4 in a row wins!",
        "Horizontal, vertical, or diagonal.",
    ]
    for i, line in enumerate(rules):
        s = font_sm.render(line, True, GRAY)
        screen.blit(s, s.get_rect(center=(WIDTH // 2, 370 + i * 28)))

    pygame.display.flip()
    return red_btn, yel_btn


# ─── Main Loop ───────────────────────────────────────────────────────────────

clock = pygame.time.Clock()
hover_col = None

while True:
    clock.tick(60)

    # ── Choose screen ──────────────────────────────────────────────────────
    if user is None:
        red_btn, yel_btn = draw_choose_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                if red_btn.collidepoint(mouse):
                    time.sleep(0.15)
                    user = cf.RED
                    board = cf.initial_state()
                    win_cells = []
                    ai_turn = False
                elif yel_btn.collidepoint(mouse):
                    time.sleep(0.15)
                    user = cf.YELLOW
                    board = cf.initial_state()
                    win_cells = []
                    ai_turn = True   # AI (RED) goes first

        continue

    # ── Game screen ────────────────────────────────────────────────────────
    game_over = cf.terminal(board)
    current   = cf.player(board)
    w         = cf.winner(board)

    # Status text
    if game_over:
        if w == cf.RED:
            status_text  = "Red wins!" if user == cf.RED else "AI wins!"
            status_color = RED_PIECE
        elif w == cf.YELLOW:
            status_text  = "Yellow wins!" if user == cf.YELLOW else "AI wins!"
            status_color = YELLOW_PIECE
        else:
            status_text  = "It's a draw!"
            status_color = GRAY
    elif user != current:
        status_text  = "AI is thinking..."
        status_color = GRAY
    else:
        name = "Red" if current == cf.RED else "Yellow"
        status_text  = f"Your turn  ({name})"
        status_color = RED_PIECE if current == cf.RED else YELLOW_PIECE

    # Draw everything
    draw_board(board, hover_col if (user == current and not game_over) else None)
    draw_top(status_text, status_color)

    if not game_over and user == current:
        draw_preview(hover_col, current)

    draw_bottom(board)

    again_btn = None
    if game_over:
        again_btn = draw_again_button()

    pygame.display.flip()

    # ── AI move ────────────────────────────────────────────────────────────
    if not game_over and user != current:
        if ai_turn:
            pygame.time.wait(400)
            action = cf.minimax(board)
            if action is not None:
                board = cf.result(board, action)
                if cf.terminal(board):
                    win_cells = get_win_cells(board)
            ai_turn = False
        else:
            ai_turn = True
        continue

    # ── Events ────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

        if event.type == pygame.MOUSEMOTION and not game_over:
            mx, _ = pygame.mouse.get_pos()
            col = mx // CELL_SIZE
            hover_col = col if 0 <= col < COLS else None

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_over and again_btn and again_btn.collidepoint(event.pos):
                user = None
                board = cf.initial_state()
                win_cells = []
                ai_turn = False
                hover_col = None
                break

            if not game_over and user == current:
                mx, my = event.pos
                if TOP_BAR <= my <= TOP_BAR + BOARD_HEIGHT:
                    col = mx // CELL_SIZE
                    if 0 <= col < COLS and col in cf.actions(board):
                        board = cf.result(board, col)
                        if cf.terminal(board):
                            win_cells = get_win_cells(board)

        if event.type == pygame.KEYDOWN and not game_over and user == current:
            key_map = {
                pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                pygame.K_4: 3, pygame.K_5: 4, pygame.K_6: 5, pygame.K_7: 6,
            }
            if event.key in key_map:
                col = key_map[event.key]
                if col in cf.actions(board):
                    board = cf.result(board, col)
                    if cf.terminal(board):
                        win_cells = get_win_cells(board)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            user = None
            board = cf.initial_state()
            win_cells = []
            ai_turn = False
            hover_col = None
