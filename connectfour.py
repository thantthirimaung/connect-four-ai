"""
Connect Four Player
"""

import math
import copy

RED = "R"
YELLOW = "Y"
EMPTY = None

ROWS = 6
COLS = 7


def initial_state():
    """
    Returns starting state of the board.
    Board is a 6x7 grid, all cells empty.
    """
    return [[EMPTY] * COLS for _ in range(ROWS)]


def player(board):
    """
    Returns player who has the next turn on a board.

    Logic:
    - RED always goes first.
    - Count R and Y on the board:
        * If counts are equal → RED's turn
        * If RED has one more → YELLOW's turn
    """
    r_count = sum(row.count(RED) for row in board)
    y_count = sum(row.count(YELLOW) for row in board)

    return RED if r_count == y_count else YELLOW


def actions(board):
    """
    Returns set of all possible actions (columns) available on the board.

    Logic:
    - A column is a valid action if its top cell is EMPTY.
    - Returns a set of column indices (0–6).
    """
    return {col for col in range(COLS) if board[0][col] == EMPTY}


def result(board, action):
    """
    Returns the board that results from dropping a piece into `action` (column).

    Logic:
    - Validate action (must be in actions(board))
    - Deep copy the board
    - Drop the current player's piece into the lowest available row
    - Return new board

    Raises:
        Exception if action is invalid
    """
    if action not in actions(board):
        raise Exception(f"Invalid action: column {action} is full or out of range.")

    new_board = copy.deepcopy(board)
    current = player(board)

    # Drop piece to the lowest empty row in the chosen column
    for row in range(ROWS - 1, -1, -1):
        if new_board[row][action] == EMPTY:
            new_board[row][action] = current
            break

    return new_board


def winner(board):
    """
    Returns the winner of the game, if there is one.

    Logic:
    - Check all horizontal, vertical, and diagonal windows of 4
    - If any window has 4 of the same non-EMPTY symbol → winner found
    - Otherwise return None
    """
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            w = _check_window(window)
            if w:
                return w

    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            window = [board[r + i][c] for i in range(4)]
            w = _check_window(window)
            if w:
                return w

    # Diagonal (bottom-left to top-right)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            w = _check_window(window)
            if w:
                return w

    # Diagonal (bottom-right to top-left)
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            window = [board[r + i][c - i] for i in range(4)]
            w = _check_window(window)
            if w:
                return w

    return None


def _check_window(window):
    """
    Helper: Returns the winner if a window of 4 is all the same player.
    """
    if window[0] is not None and all(cell == window[0] for cell in window):
        return window[0]
    return None


def terminal(board):
    """
    Returns True if game is over, False otherwise.

    Logic:
    - Game is over if:
        * There is a winner
        * OR no valid actions remain (draw)
    """
    if winner(board) is not None:
        return True

    if not actions(board):
        return True

    return False


def utility(board):
    """
    Returns utility of a terminal board.

    Logic:
    - RED wins  → +1
    - YELLOW wins → -1
    - Draw → 0

    Assumption:
    - Called only when terminal(board) is True
    """
    win = winner(board)

    if win == RED:
        return 1
    elif win == YELLOW:
        return -1
    else:
        return 0


# ─── Heuristic scoring for non-terminal states ───────────────────────────────

def _score_window(window, piece):
    """
    Scores a window of 4 cells for the given piece.

    Heuristic values:
    - 4 in a row       → +100
    - 3 + 1 empty      → +5
    - 2 + 2 empty      → +2
    - opponent 3 + 1 empty → -4  (block threat)
    """
    opp = YELLOW if piece == RED else RED
    p_count = window.count(piece)
    e_count = window.count(EMPTY)
    o_count = window.count(opp)

    if p_count == 4:
        return 100
    elif p_count == 3 and e_count == 1:
        return 5
    elif p_count == 2 and e_count == 2:
        return 2
    elif o_count == 3 and e_count == 1:
        return -4

    return 0


def _heuristic(board, piece):
    """
    Evaluates the board state heuristically for `piece`.

    Considers:
    - Center column preference (+3 per piece in center)
    - Horizontal, vertical, diagonal windows of 4
    """
    score = 0

    # Center column bonus
    center_col = [board[r][COLS // 2] for r in range(ROWS)]
    score += center_col.count(piece) * 3

    # Horizontal windows
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            score += _score_window(window, piece)

    # Vertical windows
    for r in range(ROWS - 3):
        for c in range(COLS):
            window = [board[r + i][c] for i in range(4)]
            score += _score_window(window, piece)

    # Diagonal (↘)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += _score_window(window, piece)

    # Diagonal (↙)
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            window = [board[r + i][c - i] for i in range(4)]
            score += _score_window(window, piece)

    return score


# ─── Minimax with Alpha-Beta Pruning ─────────────────────────────────────────

DEPTH = 5  # Search depth (increase for stronger AI, slower response)

# Column order: prefer center columns first for better pruning
COL_ORDER = [3, 2, 4, 1, 5, 0, 6]


def minimax(board):
    """
    Returns the optimal action (column) for the current player on the board.

    Logic:
    - If board is terminal → return None
    - If current player is RED  → maximize score
    - If current player is YELLOW → minimize score
    - Uses Alpha-Beta Pruning for efficiency
    """
    if terminal(board):
        return None

    current = player(board)

    if current == RED:
        best_value = -math.inf
        best_action = None

        for action in _ordered_actions(board):
            value = _min_value(result(board, action), DEPTH - 1, -math.inf, math.inf)
            if value > best_value:
                best_value = value
                best_action = action

        return best_action

    else:
        best_value = math.inf
        best_action = None

        for action in _ordered_actions(board):
            value = _max_value(result(board, action), DEPTH - 1, -math.inf, math.inf)
            if value < best_value:
                best_value = value
                best_action = action

        return best_action


def _ordered_actions(board):
    """
    Returns valid actions sorted by center preference for better pruning.
    """
    valid = actions(board)
    return [c for c in COL_ORDER if c in valid]


def _max_value(board, depth, alpha, beta):
    """
    Minimax MAX node (RED's turn).
    Returns the highest achievable score.
    """
    if terminal(board):
        return utility(board) * 1000000

    if depth == 0:
        return _heuristic(board, RED) - _heuristic(board, YELLOW)

    v = -math.inf

    for action in _ordered_actions(board):
        v = max(v, _min_value(result(board, action), depth - 1, alpha, beta))
        alpha = max(alpha, v)
        if alpha >= beta:
            break  # Beta cut-off

    return v


def _min_value(board, depth, alpha, beta):
    """
    Minimax MIN node (YELLOW's turn).
    Returns the lowest achievable score.
    """
    if terminal(board):
        return utility(board) * 1000000

    if depth == 0:
        return _heuristic(board, RED) - _heuristic(board, YELLOW)

    v = math.inf

    for action in _ordered_actions(board):
        v = min(v, _max_value(result(board, action), depth - 1, alpha, beta))
        beta = min(beta, v)
        if alpha >= beta:
            break  # Alpha cut-off

    return v
