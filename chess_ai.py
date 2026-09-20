#!/usr/bin/env python3
import sys

import move_engine as engine

SEARCH_DEPTH = 2
dfs_visited = set()
dfs_stop = False
transposition_table = {}

OPENING_BOOK = {
    0: ('J', (1, 5), (1, 0)),      #white: joey push forward
    1: ('j', (9, 5), (-1, 0)),     #black: joey push forward
    2: ('P', (1, 1), (2, 0)),      #white: pawn two-square advance
    3: ('p', (9, 1), (-2, 0)),     #black: pawn two-square advance
    4: ('N', (0, 9), (2, -1)),     #white: develop right knight
    5: ('n', (10, 1), (-2, 1)),    #black: develop left knight
    6: ('N', (0, 1), (2, 1)),      #white: develop left knight
    7: ('n', (10, 9), (-2, -1)),   #black: develop right knight
}

PIECE_WORTH = {
    'P': 1,   'p': 1, #pawn worth 1 in regular chess
    'N': 3,   'n': 3, #knight worth 3 in regular chess
    'B': 3.5, 'b': 3.5, #bishop worth 3.5 in regular chess (sometimes 3 but because this is a bigger board, it is worth more)
    'R': 5,   'r': 5, #rook worth 5 in regular chess
    'Q': 9,   'q': 9, #queen worth 9 in regular chess
    'K': 200, 'k': 200, #king worth infinite in regular chess
    'W': 200, 'w': 200, #king worth infinite in regular chess
    'S': 4,   's': 4, #serpent worth 4 because she can move more than a pawn (so 2 points; plus poisoning 2 points)
    'E': 12,  'e': 12, #empress worth 12 because she is a queen, knight, and serpent combined
    'O': 3,   'o': 3, #old womnan worth 3 because she can move more than a pawn (so 2 points; plus potential 1 point)
    'G': 2.5, 'g': 2.5, #gorilla worth 2.5 because he can move more than a pawn (so 2 points; plus can't be captured so 0.5 points)
    'C': 3.5, 'c': 3.5, #catapult worth 3.5 because he let's any piece move like a queen (but takes moves to setup)
    'Z': 3,   'z': 3, #beekeeper worth 3 because he can move more than a pawn (so 2 points; plus paralyze so 1 point)
    'X': 2.5, 'x': 2.5, #golf cart worth 2.5 because about as much as a pawn (so 1 point; plus potential 1.5 points)
    'H': 0.5, 'h': 0.5, #time machine worth 0.5 because it can't move
    'J': 0.3, 'j': 0.3, #joey worth 0.3 because he can move more than a pawn (so 2 points; plus potential  to kill friendly pieces so -1.7 points)
}

def get_state_id(board_state):
    
    #convert board state (list of lists) to hashable tuple of tuples
    return tuple(tuple(row) for row in board_state)

def get_legal_moves(board_state):
    board = board_state[1:-3]
    potential_pieces_list = engine.get_pieces_of_current_player(board_state)
    current_pieces_statuses = engine.get_pieces_on_board(potential_pieces_list, board)
    all_moves = engine.get_all_moves(current_pieces_statuses, board)
    within_bounds_moves = engine.get_moves_within_bounds(all_moves, board)
    return engine.get_possible_moves_based_on_rules(within_bounds_moves, board)

def apply_move(board_state, piece_status, move_delta):
    board = board_state[1:-3]
    new_board = engine.perform_move(piece_status, move_delta, board)
    next_turn = [['B']] if board_state[0][0] == 'W' else [['W']]
    return next_turn + new_board + board_state[-3:]

def find_edges_from_state(board_state):
    
    #generate all possible moves's board states from the current board state
    legal_moves = get_legal_moves(board_state)
    edges = []
    for move in legal_moves:
        piece_status, move_delta = move
        child_state = apply_move(board_state, piece_status, move_delta)
        edges.append((move, child_state))
    return edges

def is_leaf_position(board_state, depth):
    
    #if the depth is 0 (meaning we have reached the max depth) or there are no legal moves, it is a leaf position
    return depth <= 0 or not get_legal_moves(board_state)

def is_paralyzed(cell, row_index, col_index, board):
    
    #time machines and golf carts cannot be paralyzed
    if cell in ("H", "h", "X", "x"):
        return False
    
    #a piece is paralyzed if it is adjacent to an opposing beekeeper
    from fixed_a3 import in_bounds, is_opponent
    for row_delta in (-1, 0, 1):
        for col_delta in (-1, 0, 1):
            if row_delta == 0 and col_delta == 0:
                continue
            neighbor_row = row_index + row_delta
            neighbor_col = col_index + col_delta
            if in_bounds(neighbor_row, neighbor_col, board):
                neighbor_piece = board[neighbor_row][neighbor_col]
                if neighbor_piece in ("Z", "z") and is_opponent(neighbor_piece, cell):
                    return True
    return False

def king_safety_penalty(board):
    
    penalty = 0.0
    from fixed_a3 import in_bounds, is_opponent
    for row_index, row in enumerate(board):
        for col_index, cell in enumerate(row):
            if cell in ("K", "k", "W", "w"):
                for row_delta in (-1, 0, 1):
                    for col_delta in (-1, 0, 1):
                        if row_delta == 0 and col_delta == 0:
                            continue
                        neighbor_row = row_index + row_delta
                        neighbor_col = col_index + col_delta
                        if in_bounds(neighbor_row, neighbor_col, board):
                            neighbor_piece = board[neighbor_row][neighbor_col]
                            if neighbor_piece in ("S", "s", "E", "e") and is_opponent(neighbor_piece, cell):
                                
                                if cell.isupper():
                                    penalty -= 5.0
                                else:
                                    penalty += 5.0
    return penalty

def effective_piece_worth(cell, row_index, col_index, board, white_has_serpent_or_empress, black_has_serpent_or_empress):
    
    #get the base worth of the piece
    base = PIECE_WORTH.get(cell, 0)
    if base == 0:
        return 0

    worth = base

    # if a side has no serpent/empress, its old woman can never be promoted so is worth less
    if cell == "O" and not white_has_serpent_or_empress:
        worth = 1.0
    elif cell == "o" and not black_has_serpent_or_empress:
        worth = 1.0

    # if a golf cart is not in the top or bottom row it can't move left/right, it is worth less
    if cell in ("X", "x"):
        if row_index not in (0, len(board) - 1):
            worth = 0.5

    #paralyzed important pieces are less valuable (but never discount kings/jetpack kings)
    if worth > 0 and cell not in ("K", "k", "W", "w") and is_paralyzed(cell, row_index, col_index, board):
        worth *= 0.3

    return worth


def evaluate_board(board_state):
    
    #evaluate the board state
    board = board_state[1:-3]
    current_is_white = board_state[0][0] == 'W'
    total = 0

    # check if each side still has a serpent or empress (for old woman value)
    white_has_serpent_or_empress = any(cell in ["S", "E"] for row in board for cell in row)
    black_has_serpent_or_empress = any(cell in ["s", "e"] for row in board for cell in row)

    #count total pieces on the board to detect endgame (fewer than 12 pieces left)
    total_piece_count = sum(1 for row in board for cell in row if cell.isalpha())
    is_endgame = total_piece_count < 12

    for row_index, row in enumerate(board):
        for col_index, cell in enumerate(row):
            worth = effective_piece_worth(
                cell,
                row_index,
                col_index,
                board,
                white_has_serpent_or_empress,
                black_has_serpent_or_empress,
            )
            if worth == 0:
                continue

            #endgame adjustments
            if is_endgame:
                if cell in ("P", "p"):
                    worth *= 1.5
                if cell in ("K", "k", "W", "w"):
                    distance_to_center = abs(row_index - 5) + abs(col_index - 5)
                    worth += (10 - distance_to_center) * 0.3

            # add the worth of the piece if it is mine, otherwise subtract it
            is_mine = (current_is_white and cell.isupper()) or (not current_is_white and cell.islower())
            total += worth if is_mine else -worth

    #king safety term
    king_safety_score = king_safety_penalty(board)
    total += king_safety_score

    return total


def dfs_with_alpha_beta(board_state, depth, alpha, beta):
    
    #if the depth is 0 or there are no legal moves, return the evaluated board state
    if depth <= 0 or is_leaf_position(board_state, depth):
        return evaluate_board(board_state)

    #transposition table
    #a cached result from a deeper search is more accurate
    state_id = get_state_id(board_state)
    if state_id in transposition_table:
        cached_depth, cached_score = transposition_table[state_id]
        if cached_depth >= depth:
            return cached_score

    best_score = None

    #examine captures first 
    moves_with_scores = []
    board = board_state[1:-3]
    for (piece_status, move_delta), destination_state in find_edges_from_state(board_state):
        from_row, from_col = piece_status[1]

        #estimate capture value for ordering (best-effort; fling moves are trickier)
        capture_value = 0.0
        if isinstance(move_delta, tuple) and (len(move_delta) == 2 or move_delta[0] != 'fling'):
            target_row = from_row + move_delta[0]
            target_col = from_col + move_delta[1]
            if 0 <= target_row < len(board) and 0 <= target_col < len(board[target_row]):
                target_piece = board[target_row][target_col]
                if target_piece.isalpha():
                    capture_value = PIECE_WORTH.get(target_piece, 0)
        moves_with_scores.append((capture_value, destination_state))

    moves_with_scores.sort(key=lambda item: item[0], reverse=True)

    for _capture_val, destination_state in moves_with_scores:
        
        child_alpha = None if beta is None else -beta
        child_beta = None if alpha is None else -alpha
        child_score = dfs_with_alpha_beta(destination_state, depth - 1, child_alpha, child_beta)
        if child_score is None:
            continue
        score = -child_score

        if best_score is None or score > best_score:
            best_score = score

        if alpha is None or score > alpha:
            alpha = score

        if beta is not None and alpha is not None and alpha >= beta:
            break

    #if we didn't find any children, evaluate this position
    if best_score is None:
        return evaluate_board(board_state)

    #store the result in the transposition table for future lookups
    transposition_table[state_id] = (depth, best_score)
    return best_score

def choose_best_move(board_state):
    
    #initialize the visited and stop flags
    global dfs_visited, dfs_stop, transposition_table
    dfs_visited.clear()
    dfs_stop = False
    transposition_table = {}

    #get the legal moves
    legal_moves = get_legal_moves(board_state)
    if not legal_moves:
        return None

    #immediate win detection
    current_is_white = board_state[0][0] == 'W'
    my_king_chars = ('K', 'W') if current_is_white else ('k', 'w')
    opponent_king_chars = ('k', 'w') if current_is_white else ('K', 'W')
    board = board_state[1:-3]

    for piece_status, move_delta in legal_moves:
        simulated_board = engine.perform_move(piece_status, move_delta, board)
        next_turn = [['B']] if current_is_white else [['W']]
        simulated_state = next_turn + simulated_board + board_state[-3:]

        opponent_still_has_king = any(
            cell in opponent_king_chars for row in simulated_board for cell in row
        )
        if not opponent_still_has_king:
            return piece_status, move_delta

    #immediate loss avoidance
    safe_moves = []
    losing_in_one = set()
    for piece_status, move_delta in legal_moves:
        simulated_board = engine.perform_move(piece_status, move_delta, board)
        next_turn = [['B']] if current_is_white else [['W']]
        simulated_state = next_turn + simulated_board + board_state[-3:]

        #if our king is already gone, horrible move
        my_king_alive = any(
            cell in my_king_chars for row in simulated_board for cell in row
        )
        if not my_king_alive:
            losing_in_one.add((piece_status, move_delta))
            continue

        opponent_replies = get_legal_moves(simulated_state)
        king_can_be_captured = False
        reply_board = simulated_state[1:-3]
        for reply_status, reply_delta in opponent_replies:
            reply_result = engine.perform_move(reply_status, reply_delta, reply_board)
            my_king_still_alive = any(
                cell in my_king_chars for row in reply_result for cell in row
            )
            if not my_king_still_alive:
                king_can_be_captured = True
                break

        if king_can_be_captured:
            losing_in_one.add((piece_status, move_delta))
        else:
            safe_moves.append((piece_status, move_delta))

    #if there is at least one safe move, ignore moves that lose 
    candidate_moves = safe_moves if safe_moves else legal_moves

    #sort root moves so captures are searched first (high value captures before low)
    #this sets a strong best_score early so alpha-beta prunes later moves faster
    root_scored = []
    for piece_status, move_delta in candidate_moves:
        capture_value = 0.0
        from_row, from_col = piece_status[1]
        if isinstance(move_delta, tuple) and (len(move_delta) == 2 or move_delta[0] != 'fling'):
            target_row = from_row + move_delta[0]
            target_col = from_col + move_delta[1]
            if 0 <= target_row < len(board) and 0 <= target_col < len(board[target_row]):
                target_piece = board[target_row][target_col]
                if target_piece.isalpha():
                    capture_value = PIECE_WORTH.get(target_piece, 0)
        root_scored.append((capture_value, piece_status, move_delta))
    root_scored.sort(key=lambda item: item[0], reverse=True)
    candidate_moves = [(ps, md) for _, ps, md in root_scored]

    #find the best move using alpha-beta pruning 
    best_move = None
    best_score = None
    for piece_status, move_delta in candidate_moves:
        destination_state = apply_move(board_state, piece_status, move_delta)
        
        #evaluate_board is defined relative, so dfs_with_alpha_beta returns the value from the opponent's perspective (since destination_state flips the turn)
        #pass our running best score so the child can prune branches that cant beat it
        child_beta = None if best_score is None else -best_score
        score = -dfs_with_alpha_beta(destination_state, SEARCH_DEPTH - 1, None, child_beta)
        if score is not None:
            if best_score is None or score > best_score:
                best_score = score
                best_move = (piece_status, move_delta)

    return best_move


def choose_first_legal_move(board_state):

    legal_moves = get_legal_moves(board_state)
    if not legal_moves:
        return None
    return legal_moves[0]


def choose_best_move_under_100ms(board_state):

    legal_moves = get_legal_moves(board_state)
    if not legal_moves:
        return None

    current_is_white = board_state[0][0] == 'W'
    my_king_chars = ('K', 'W') if current_is_white else ('k', 'w')
    opponent_king_chars = ('k', 'w') if current_is_white else ('K', 'W')
    board = board_state[1:-3]

    # immediate win detection (must simulate, but we only do it for this move list)
    for piece_status, move_delta in legal_moves:
        simulated_board = engine.perform_move(piece_status, move_delta, board)
        next_turn = [['B']] if current_is_white else [['W']]
        simulated_state = next_turn + simulated_board + board_state[-3:]

        opponent_still_has_king = any(
            cell in opponent_king_chars for row in simulated_board for cell in row
        )
        if not opponent_still_has_king:
            return piece_status, move_delta

    # immediate loss avoidance
    safe_moves = []
    for piece_status, move_delta in legal_moves:
        simulated_board = engine.perform_move(piece_status, move_delta, board)
        next_turn = [['B']] if current_is_white else [['W']]
        simulated_state = next_turn + simulated_board + board_state[-3:]

        my_king_alive = any(
            cell in my_king_chars for row in simulated_board for cell in row
        )
        if not my_king_alive:
            continue

        opponent_replies = get_legal_moves(simulated_state)
        king_can_be_captured = False
        reply_board = simulated_state[1:-3]
        for reply_status, reply_delta in opponent_replies:
            reply_result = engine.perform_move(reply_status, reply_delta, reply_board)
            my_king_still_alive = any(
                cell in my_king_chars for row in reply_result for cell in row
            )
            if not my_king_still_alive:
                king_can_be_captured = True
                break

        if not king_can_be_captured:
            safe_moves.append((piece_status, move_delta))

    candidate_moves = safe_moves if safe_moves else legal_moves
    return candidate_moves[0]


def get_piece_worth(piece_type):
    return PIECE_WORTH.get(piece_type, 0)

def choose_opening_move(board_state):
    
    #check if we have a hardcoded opening move for this move number
    #uses move_no as index so it plays the right move each turn (not always move 0)
    move_no = _parse_int_line(board_state[-1]) if len(board_state) >= 1 else 0

    if move_no not in OPENING_BOOK:
        return None

    target_piece, target_pos, target_delta = OPENING_BOOK[move_no]
    legal_moves = get_legal_moves(board_state)

    for piece_status, move_delta in legal_moves:
        piece_type, pos = piece_status
        if piece_type == target_piece and pos == target_pos and move_delta == target_delta:
            return piece_status, move_delta

    return None


def _parse_int_line(line):
    
    if line is None:
        return 0
    if isinstance(line, list):
        line_text = ''.join(line)
    else:
        line_text = str(line)
    line_text = line_text.strip()
    return int(line_text) if line_text else 0


def choose_move(board_state):

    #time-based SEARCH_DEPTH adjustment
    #small opening move
    #fallback
    used_time_ms = _parse_int_line(board_state[-3]) if len(board_state) >= 3 else 0
    total_time_ms = _parse_int_line(board_state[-2]) if len(board_state) >= 2 else 60000
    move_no = _parse_int_line(board_state[-1]) if len(board_state) >= 1 else 0

    #reduce search depth when remaining time is low.
    remaining_ms = max(0, total_time_ms - used_time_ms)

    # opening moves
    opening = choose_opening_move(board_state)
    if opening is not None:
        return opening

    # ultra-low time
    if remaining_ms < 50:
        return choose_first_legal_move(board_state)

    # low time
    if remaining_ms < 100:
        return choose_best_move_under_100ms(board_state)

    # normal time
    global SEARCH_DEPTH
    if remaining_ms < 500:
        SEARCH_DEPTH = 1
    else:
        SEARCH_DEPTH = 2

    return choose_best_move(board_state)

def main():
    
    #read the input from stdin
    contents = sys.stdin.read()
    if not contents.strip():
        return

    #get the board state from the input
    board_state = engine.get_board_state(contents)
    move = choose_move(board_state)
    board = board_state[1:-3]

    if move is None:
        new_board_status = board_state
    
    #if there is a move, apply it to the board
    else:
        piece_status, move_delta = move
        new_board = engine.perform_move(piece_status, move_delta, board)
        next_turn = [['B']] if board_state[0][0] == 'W' else [['W']]
        new_board_status = next_turn + new_board + board_state[-3:]

    for row in new_board_status:
        sys.stdout.write(''.join(row) + '\n')


if __name__ == "__main__":
    main()
