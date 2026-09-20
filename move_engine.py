#!/usr/bin/env python3
import sys

TRANSPORTER_PADS = {(3, 9), (7, 1), (7, 9), (3, 1)}
JETPACK_SQUARE = (5, 5)
FIXED_SQUARES = {(3, 9): '*', (7, 1): '*', (7, 9): '*', (3, 1): '*', (5, 5): '#'}

def is_piece(char):
    return char.isalpha()

def is_friendly(piece_one, piece_two):
    return (piece_one.isupper() and piece_two.isupper()) or (piece_one.islower() and piece_two.islower())

def is_opponent(piece_one, piece_two):
    return (piece_one.isupper() and piece_two.islower()) or (piece_one.islower() and piece_two.isupper())

def in_bounds(row_index, col_index, board):
    return 0 <= row_index < len(board) and 0 <= col_index < len(board[row_index])

def neightbours(center, board):
    row_index, col_index = center
    board_length = len(board)
    row_length = len(board[row_index])
    for delta_row in range(-1, 2):
        for delta_col in range(-1, 2):
            if delta_row == 0 and delta_col == 0:
                continue
            neighbor_row = row_index + delta_row
            neighbor_col = col_index + delta_col
            if 0 <= neighbor_row < board_length and 0 <= neighbor_col < row_length:
                yield neighbor_row, neighbor_col


def is_fling_move(move):
    return isinstance(move, tuple) and len(move) >= 1 and move[0] == 'fling'


def make_fling_move(from_row, from_col, to_row, to_col):
    return ('fling', from_row, from_col, to_row, to_col)

def reapply_board(board):
    
    #reset the transporter pads and jetpacks if removed 
    for (row, col), square in FIXED_SQUARES.items(): 
        if board[row][col] == '.':
            board[row][col] = square
    return board

def find_gc_positions(board):
    wcol, wrow, bcol, brow = None, None, None, None
    for row in range(len(board)):
        for col in range(len(board[row])):
            if board[row][col] == 'X':
                wcol, wrow = col, row
            elif board[row][col] == 'x':
                bcol, brow = col, row
    return wcol, wrow, bcol, brow

def apply_golf_cart_effect(board, cart_char, col, cart_row):
    if col is None or cart_row is None:
        return
    # Rule: a charged golf cart that is already on the middle row does not move.
    if cart_row == len(board) // 2:
        return
    for row_idx in range(len(board)):
        if (row_idx, col) in TRANSPORTER_PADS or ((row_idx, col) == JETPACK_SQUARE and board[row_idx][col] in ['#', 'w', 'W']):
            continue
        if board[row_idx][col] != cart_char:
            board[row_idx][col] = '.'
    # clear the cart's original position so it doesn't leave a ghost behind
    board[cart_row][col] = '.'
    if cart_row < len(board) // 2:
        board[len(board) - 1][col] = cart_char
    else:
        board[0][col] = cart_char

def apply_poisoning(new_board):
    #After-effect 1: Pieces adjacent to an opposing serpent or empress are poisoned and removed (except Golf Cart, Time Machine).
    
    if not any(
        piece in ["S", "s", "E", "e"]
        for row in new_board
        for piece in row
    ):
        return new_board

    to_remove = set()
    old_woman_to_convert = set()
    enemy_serpents_to_remove = set()

    board_length = len(new_board)
    for row in range(board_length):
        row_length = len(new_board[row])
        for col in range(row_length):
            square = new_board[row][col]
            if not (is_piece(square) and square not in ["H", "h", "X", "x"]):
                continue

            adjacent_opponent_serpent = False
            adjacent_opponent_empress = False
            adjacent_opponent_serpent_positions = []

            for neighbor_row, neighbor_col in neightbours((row, col), new_board):
                target_piece = new_board[neighbor_row][neighbor_col]
                if target_piece in ["S", "s"] and is_opponent(target_piece, square):
                    adjacent_opponent_serpent = True
                    adjacent_opponent_serpent_positions.append((neighbor_row, neighbor_col))
                elif target_piece in ["E", "e"] and is_opponent(target_piece, square):
                    adjacent_opponent_empress = True

            if not (adjacent_opponent_serpent or adjacent_opponent_empress):
                continue

            # Rule: Old Woman adjacent to an opposing Serpent becomes a Grand Empress.
            # The opposing Serpent dies as part of that conversion.
            if square in ["O", "o"] and adjacent_opponent_serpent:
                old_woman_to_convert.add((row, col))
                for neighbor_pos in adjacent_opponent_serpent_positions:
                    enemy_serpents_to_remove.add(neighbor_pos)
                continue

            # Otherwise, any adjacent-to-serpent/empress piece is removed.
            to_remove.add((row, col))

    for row, col in to_remove:
        if (row, col) not in old_woman_to_convert:
            new_board[row][col] = '.'

    for row, col in enemy_serpents_to_remove:
        new_board[row][col] = '.'

    for row, col in old_woman_to_convert:
        new_board[row][col] = "E" if new_board[row][col] == "O" else "e"

    return new_board


def apply_promotion(new_board):
    #After-effect 2: Pawn on opposite end → Time Machine; King on Jet Pack → King with Jet Pack.
    
    board_length = len(new_board)
    for row in range(board_length):
        for col in range(len(new_board[row])):
            cell = new_board[row][col]
            if cell == 'P' and row == board_length - 1:
                new_board[row][col] = 'H'
            elif cell == 'p' and row == 0:
                new_board[row][col] = 'h'
            elif cell in ["K", "k"] and (row, col) == JETPACK_SQUARE:
                new_board[row][col] = 'W' if cell == 'K' else 'w'
    return new_board


def apply_golf_cart_rampage(new_board):
    #After-effect 3: Golf cart rampage.
    
    white_pawn_in_row5 = any(new_board[5][col] == 'P' for col in range(len(new_board[5])))
    black_pawn_in_row5 = any(new_board[5][col] == 'p' for col in range(len(new_board[5])))

    white_time_machine_exists = any(
        new_board[row][col] == 'H'
        for row in range(len(new_board))
        for col in range(len(new_board[row]))
    )
    black_time_machine_exists = any(
        new_board[row][col] == 'h'
        for row in range(len(new_board))
        for col in range(len(new_board[row]))
    )

    wcol, wrow, bcol, brow = find_gc_positions(new_board)

    white_cart_charged = (wcol is not None) and (
        black_pawn_in_row5 or white_time_machine_exists
    )
    black_cart_charged = (bcol is not None) and (
        white_pawn_in_row5 or black_time_machine_exists
    )

    if white_cart_charged and black_cart_charged and wcol == bcol:
        for row in range(len(new_board)):
            if (row, wcol) in TRANSPORTER_PADS or (row, wcol) == JETPACK_SQUARE:
                continue
            new_board[row][wcol] = '.'
        return reapply_board(new_board)

    if black_cart_charged:
        apply_golf_cart_effect(new_board, 'x', bcol, brow)
    if white_cart_charged:
        apply_golf_cart_effect(new_board, 'X', wcol, wrow)

    return reapply_board(new_board)


def apply_energize(new_board):
    #After-effect 4: Pieces on transporter pads are moved (3,9)→(3,1), (7,1)→(3,9), (7,9)→(7,1), (3,1)→(7,9).
    
    pad_dest = {(3, 9): (3, 1), (7, 1): (3, 9), (7, 9): (7, 1), (3, 1): (7, 9)}
    
    # Must be simultaneous: compute from a snapshot, then apply in two phases.
    snapshot = {(row, col): new_board[row][col] for (row, col) in TRANSPORTER_PADS}

    # Clear all pads back to '*', regardless of whether they held a piece.
    for (row, col) in TRANSPORTER_PADS:
        new_board[row][col] = '*'

    # Place moved pieces onto their destination pads using the snapshot.
    for (from_pos, piece) in snapshot.items():
        if is_piece(piece):
            to_pos = pad_dest[from_pos]
            new_board[to_pos[0]][to_pos[1]] = piece
    return reapply_board(new_board)


def apply_prince_joey_explodes(new_board):
    
    #After-effect 5: If pieces in Prince Joey's row (including Joey) count is divisible by 5, Joey and all adjacent pieces are removed.
    exploding_joeys = []
    for row in range(len(new_board)):
        for col in range(len(new_board[row])):
            if new_board[row][col] in ["J", "j"]:
                piece_count = sum(1 for square in new_board[row] if is_piece(square))
                if piece_count % 5 == 0:
                    exploding_joeys.append((row, col))

    for (joey_row, joey_col) in exploding_joeys:
        for delta_row in range(-1, 2):
            for delta_col in range(-1, 2):
                target_row = joey_row + delta_row
                target_col = joey_col + delta_col
                if in_bounds(target_row, target_col, new_board):
                    new_board[target_row][target_col] = '.'

    return reapply_board(new_board)


def apply_after_effects(new_board):
    
    #Run all after-effects in order: 1. Poisoning, 2. Promotion, 3. Golf cart rampage, 4. Energize, 5. Prince Joey explodes.
    new_board = apply_poisoning(new_board)
    new_board = apply_promotion(new_board)
    new_board = apply_golf_cart_rampage(new_board)
    new_board = apply_energize(new_board)
    new_board = apply_prince_joey_explodes(new_board)
    return new_board

def get_contents(filename):
    with open(filename, 'r') as file_handle:
        contents = file_handle.read()
    return contents

def get_board_state(contents):
   
    #split contents into lines
    lines = contents.splitlines()
   
    #initialize board as list of lists
    board = []
   
    #go through lines and add to board
    for line in lines:
        board.append(list(line))
       
    return board

def get_pieces_of_current_player(board_state):
   
    #read whose turn it is from board
    turn = board_state[0][0]
   
    #set pieces to check for based on whose turn it is
    if turn == "W":
        pieces=["P", "R", "N", "B", "Q", "K", "S", "O", "E", "J", "C", "G", "X", "H", "Z", "W"]
    else:
        pieces=["p", "r", "n", "b", "q", "k", "s", "o", "e", "j", "c", "g", "x", "h", "z", "w"]
       
    return pieces

def get_pieces_on_board(potential_pieces_list, board):
   
    pieces_statuses = []
   
    #go through rows of board
    for row in range(len(board)):
       
        #go through columns of board
        for col in range(len(board[row])):
           
            square=board[row][col]
           
            #if a potential piece is on the board, add piece and location to list of pieces
            if square in potential_pieces_list:
               
                #get location of piece and add to list of pieces
                location = (row, col)
                pieces_statuses.append((square, location))
                   
    return pieces_statuses

def get_all_moves(current_pieces_statuses, board):
   
    all_moves = []
    board_length = len(board)
     
    #go through pieces
    for piece_type, location in current_pieces_statuses:
       
        #get all moves for piece and add to list of all moves
        piece_status = (piece_type, location)
        potential_moves_for_this_piece = get_potential_moves_of_a_piece(piece_type, board)
     
        for move in potential_moves_for_this_piece:
            all_moves.append((piece_status, move))

        #catapult fling: fling each adjacent friendly piece in the direction from that piece toward the catapult
        if piece_type in ["C", "c"]:
            catapult_row, catapult_col = location
            
            for row_delta in [-1, 0, 1]: 
                for col_delta in [-1, 0, 1]:
                    
                    if row_delta == 0 and col_delta == 0:
                        continue
                    
                    adjacent_row = catapult_row + row_delta
                    adjacent_col = catapult_col + col_delta
                    
                    if not in_bounds(adjacent_row, adjacent_col, board):
                        continue
                    
                    adjacent_piece = board[adjacent_row][adjacent_col]
                    
                    if not is_piece(adjacent_piece):
                        continue
                    
                    if not is_friendly(adjacent_piece, piece_type):
                        continue
                    
                    #cannot fling a time machine
                    if adjacent_piece in ["H", "h"]:
                        continue
                    
                    #fling direction
                    fling_dir_row, fling_dir_col = -row_delta, -col_delta
                    step = 2
                    
                    while True:
                        destination_row = adjacent_row + fling_dir_row * step
                        destination_col = adjacent_col + fling_dir_col * step
                        
                        if not (0 <= destination_row < board_length and 0 <= destination_col < board_length):
                            break
                        
                        dest_piece = board[destination_row][destination_col]
                        
                        #cannot fling onto a king or gorilla (but can pass over)
                        if dest_piece in ["K", "k", "G", "g"]:
                            step += 1
                            continue
                        if is_piece(dest_piece):
                            #cannot land on friendly pieces with a fling (but can pass over)
                            if is_friendly(dest_piece, adjacent_piece):
                                step += 1
                                continue

                            #serpent cannot be flung onto an enemy piece
                            if adjacent_piece in ["S", "s"] and is_opponent(dest_piece, adjacent_piece):
                                step += 1
                                continue

                            #enemy piece: can land/capture, but can also fly over and keep scanning
                            all_moves.append((piece_status, make_fling_move(adjacent_row, adjacent_col, destination_row, destination_col)))
                            step += 1
                            continue

                        #empty square: can land and keep scanning further squares
                        all_moves.append((piece_status, make_fling_move(adjacent_row, adjacent_col, destination_row, destination_col)))
                        step += 1
               
    return all_moves

def get_potential_moves_of_a_piece(piece_type, board):
   
    #define potential moves for each piece type
    board_length = len(board)
   
    #pawn
    if piece_type == "P":
        return [(1, 0), (2, 0), (1, 1), (1, -1)]
    elif piece_type == "p":
        return [(-1, 0), (-2, 0), (-1, 1), (-1, -1)]
   
    #rook
    elif piece_type in ["R", "r"]:
        return [(offset, 0) for offset in range(-board_length, board_length) if offset != 0] + [(0, offset) for offset in range(-board_length, board_length) if offset != 0]
   
    #knight
    elif piece_type in ["N", "n"]:
        return [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
   
    #bishop, king with jetpack
    elif piece_type in ["B", "b", "W", "w"]:
        return [(offset, offset) for offset in range(-board_length, board_length) if offset != 0] + [(offset, -offset) for offset in range(-board_length, board_length) if offset != 0]
   
    #queen
    elif piece_type in ["Q", "q"]:
        return [(offset, 0) for offset in range(-board_length, board_length) if offset != 0] + [(0, offset) for offset in range(-board_length, board_length) if offset != 0] + [(offset, offset) for offset in range(-board_length, board_length) if offset != 0] + [(offset, -offset) for offset in range(-board_length, board_length) if offset != 0]
   
    #king, serpent, joey, catapult, gorilla, beekeeper, old woman
    elif piece_type in ["K", "k", "S", "s", "J", "j", "C", "c", "G", "g", "Z", "z", "O", "o"]:
        return [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
   
    #empress (E: moves like queen and knight)
    elif piece_type in ["E", "e"]:
        return [(offset, 0) for offset in range(-board_length, board_length) if offset != 0] + [(0, offset) for offset in range(-board_length, board_length) if offset != 0] + [(offset, offset) for offset in range(-board_length, board_length) if offset != 0] + [(offset, -offset) for offset in range(-board_length, board_length) if offset != 0] + [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
   
    #golf cart (X: moves left/right 1 space)
    elif piece_type in ["X", "x"]:
        return [(0, 1), (0, -1)]
   
    #time machine (H: doesn't move)
    elif piece_type in ["H", "h"]:
        return []

def get_moves_within_bounds(moves, board):
   
    within_bounds_moves = []
    for piece_status, move_delta in moves:
        
        #already bound-checked 
        if is_fling_move(move_delta):
            within_bounds_moves.append((piece_status, move_delta))
            continue
        
        piece_location = piece_status[1]
        new_location = (piece_location[0] + move_delta[0], piece_location[1] + move_delta[1])
        
        if in_bounds(new_location[0], new_location[1], board):
            within_bounds_moves.append((piece_status, move_delta))
            
    return within_bounds_moves

def get_possible_moves_based_on_rules(valid_moves_of_a_piece, board):
   
    possible_moves_based_on_rules=[]
   
    #go through valid moves of piece
    for piece_status, move in valid_moves_of_a_piece:

        #fling: only check that the catapult itself is not paralyzed
        if is_fling_move(move):
            paralyzed = False
            
            for delta_row in range(-1, 2):
                
                for delta_col in range(-1, 2):
                    target_location = (piece_status[1][0] + delta_row, piece_status[1][1] + delta_col)
                    
                    if in_bounds(target_location[0], target_location[1], board):
                        target_piece = board[target_location[0]][target_location[1]]
                        is_beekeeper = target_piece in ["Z", "z"]
                        is_opponent_piece = is_opponent(target_piece, piece_status[0])
                        
                        if is_beekeeper and is_opponent_piece:
                            paralyzed = True
            
            if not paralyzed:
                possible_moves_based_on_rules.append((piece_status, move))
            continue

        #check if move is allowed based on new rules (ex. serpent cannot capture another piece)
        if is_move_allowed_based_on_rules(piece_status, move, board):
            possible_moves_based_on_rules.append((piece_status, move))
           
    return possible_moves_based_on_rules

def is_move_allowed_based_on_rules(piece_status, move, board):
       
    board_length=len(board)
   
    if move == (0, 0):
        return False
   
    #beekeeper interaction
    #paralyzed pieces can't move (excluding time machines and golf carts which are unaffected by paralysis); paralyzed if touching a beekeeper (including diagonals)
    for delta_row in range(-1, 2):
        for delta_col in range(-1, 2):
            target_location = (piece_status[1][0] + delta_row, piece_status[1][1] + delta_col)
            if in_bounds(target_location[0], target_location[1], board):
                target_piece = board[target_location[0]][target_location[1]]
                is_beekeeper = target_piece in ["Z", "z"]
                if is_beekeeper and is_opponent(target_piece, piece_status[0]) and piece_status[0] not in ["H", "h", "X", "x"]:
                    return False
   
    #gorilla interaction (excluding catapult where a flung piece can hit a gorilla which is handled in the catapult interaction)
    destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
    destination_piece = board[destination[0]][destination[1]]
    
    if destination_piece in ["G", "g"]:
        return False
   
    #pawn
    if piece_status[0] in ["P", "p"]:
       
        #can move up 1 if no other piece is in front of it
        if move in [(1, 0), (-1, 0)]:
            target_square = board[piece_status[1][0] + move[0]][piece_status[1][1]]
            if not is_piece(target_square):
                return True
       
        #can move up 2 if in starting row and both squares in front are empty
        elif move in [(2, 0), (-2, 0)]:
            direction = 1 if piece_status[0] == "P" else -1
            in_starting_row = (piece_status[0] == "P" and piece_status[1][0] == 1) or (piece_status[0] == "p" and piece_status[1][0] == board_length - 2)
            square_one_away = board[piece_status[1][0] + direction][piece_status[1][1]]
            square_two_away = board[piece_status[1][0] + 2 * direction][piece_status[1][1]]
            if in_starting_row and not square_one_away.isalpha() and not square_two_away.isalpha():
                return True
       
        #can capture diagonally if there is an opponent's piece in that location
        elif move in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            new_location = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
            target_piece = board[new_location[0]][new_location[1]]
            if is_piece(target_piece) and is_opponent(target_piece, piece_status[0]):
                return True
           
    #rook
    elif piece_status[0] in ["R", "r"]:
       
        #vertical movement
        vertical_move = 0 if move[0] == 0 else (1 if move[0] > 0 else -1)
       
        #horizontal movement
        horizontal_move = 0 if move[1] == 0 else (1 if move[1] > 0 else -1)
       
        current_location = piece_status[1]
        destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
       
        while True:
           
            #move one step towards destination
            current_location = (current_location[0] + vertical_move, current_location[1] + horizontal_move)
           
            #if we have reached the destination, check if move is valid
            if current_location == destination:
               
                destination_piece = board[destination[0]][destination[1]]
               
                #if destination is empty, move is valid
                if not is_piece(destination_piece):
                    return True
               
                #if destination has opponent's piece, move is valid
                return is_opponent(destination_piece, piece_status[0])
           
            #don't let rook jump over pieces
            target_square = board[current_location[0]][current_location[1]]
            if target_square.isalpha():
                return False
           
    #knight
    elif piece_status[0] in ["N", "n"]:
       
        destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
        destination_piece = board[destination[0]][destination[1]]
       
        #knight can jump over pieces, just need to check if destination square is empty or has opponent's piece
        if not is_piece(destination_piece) or is_opponent(destination_piece, piece_status[0]):
            return True
   
    #bishop, king with jetpack
    elif piece_status[0] in ["B", "b", "W", "w"]:
       
        vertical_move = 1 if move[0] > 0 else -1
        horizontal_move = 1 if move[1] > 0 else -1
       
        current_location = piece_status[1]
        destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
       
        while True:
           
            #move one step towards destination
            current_location = (current_location[0] + vertical_move, current_location[1] + horizontal_move)
           
            #if we have reached the destination, check if move is valid
            if current_location == destination:
               
                destination_piece = board[destination[0]][destination[1]]
               
                #if destination is empty, move is valid
                if not is_piece(destination_piece):
                    return True
               
                #if destination has opponent's piece, move is valid
                return is_opponent(destination_piece, piece_status[0])
           
            #don't let bishop jump over pieces
            target_square = board[current_location[0]][current_location[1]]
            if target_square.isalpha():
                return False
   
    #queen
    elif piece_status[0] in ["Q", "q"]:
       
        vertical_move = 0 if move[0] == 0 else (1 if move[0] > 0 else -1)
        horizontal_move = 0 if move[1] == 0 else (1 if move[1] > 0 else -1)
       
        current_location = piece_status[1]
        destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
       
        while True:
           
            #move one step towards destination
            current_location = (current_location[0] + vertical_move, current_location[1] + horizontal_move)
           
            #if we have reached the destination, check if move is valid
            if current_location == destination:
               
                destination_piece = board[destination[0]][destination[1]]
               
                #if destination is empty, move is valid
                if not is_piece(destination_piece):
                    return True
               
                #if destination has opponent's piece, move is valid
                return is_opponent(destination_piece, piece_status[0])
           
            #don't let queen jump over pieces
            target_square = board[current_location[0]][current_location[1]]
            if target_square.isalpha():
                return False
   
    #king, joey, beekeeper, old woman
    elif piece_status[0] in ["K", "k", "J", "j", "Z", "z", "O", "o"]:

        destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
        destination_piece = board[destination[0]][destination[1]]
       
        #alr found which moves possible and within bounds, just need to check if destination square is empty or has opponent's piece
        if not is_piece(destination_piece) or is_opponent(destination_piece, piece_status[0]):
            return True
   
    #serpent, catapult (cannot capture)
    elif piece_status[0] in ["S", "s", "C", "c"]:
        destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
        destination_piece = board[destination[0]][destination[1]]
        if not is_piece(destination_piece):
            return True
       
    #gorilla (moves like king; can move to empty or push a piece)
    #Gorilla cannot push off the board; cannot push another gorilla.
    elif piece_status[0] in ["G", "g"]:
        destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
        destination_piece = board[destination[0]][destination[1]]
        if not is_piece(destination_piece):
            return True
        #push: destination has a piece; check destination_of_destination is in bounds
        destination_of_destination = (destination[0] + move[0], destination[1] + move[1])
       
        #move the destination_piece to take over the destination_of_destination piece
        if 0 <= destination_of_destination[0] < board_length and 0 <= destination_of_destination[1] < board_length:
            destination_of_destination_piece = board[destination_of_destination[0]][destination_of_destination[1]]
           
            #if there is a piece in the destination of destination, it gets killed; if it's a gorilla pushing a gorilla, or if the pushed piece would land on a gorilla, move is not allowed;
            #if there is no piece in the destination of destination, move is allowed
            if destination_of_destination_piece.isalpha():
                if destination_piece in ["G", "g"] or destination_of_destination_piece in ["G", "g"]:
                    return False
                else:
                    return True
            else:
                return True
    
    #time machine
    elif piece_status[0] in ["H", "h"]:
        return False
   
    #golf cart (can only move/capture left and right on the top and bottom rows)
    elif piece_status[0] in ["X", "x"]:
        piece_row = piece_status[1][0]
        if piece_row != 0 and piece_row != board_length - 1:
            return False
        destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
        destination_piece = board[destination[0]][destination[1]]
        if move in [(0, 1), (0, -1)]:
            return not destination_piece.isalpha() or ((destination_piece.isupper() and piece_status[0].islower()) or (destination_piece.islower() and piece_status[0].isupper()))
   
    #empress
    elif piece_status[0] in ["E", "e"]:
        delta_row, delta_col = move
       
        #knight-like component: handle as a jump (no path blocking)
        if (abs(delta_row), abs(delta_col)) in [(1, 2), (2, 1)]:
            destination = (piece_status[1][0] + delta_row, piece_status[1][1] + delta_col)
            destination_piece = board[destination[0]][destination[1]]
            return (not is_piece(destination_piece) or
                    is_opponent(destination_piece, piece_status[0]))
        #sliding queen-like component
        vertical_move = 0 if delta_row == 0 else (1 if delta_row > 0 else -1)
        horizontal_move = 0 if delta_col == 0 else (1 if delta_col > 0 else -1)
       
        current_location = piece_status[1]
        destination = (piece_status[1][0] + delta_row, piece_status[1][1] + delta_col)
       
        while True:
           
            #move one step towards destination
            current_location = (current_location[0] + vertical_move, current_location[1] + horizontal_move)
           
            #if we ever step off the board, the move is invalid
            if not (0 <= current_location[0] < board_length and 0 <= current_location[1] < board_length):
                return False
           
            #if we have reached the destination, check if move is valid
            if current_location == destination:
                destination_piece = board[destination[0]][destination[1]]
               
                #if destination is empty, move is valid
                if not is_piece(destination_piece):
                    return True
               
                #if destination has opponent's piece, move is valid
                return is_opponent(destination_piece, piece_status[0])
           
            #don't let empress jump over pieces on the slide
            target_square = board[current_location[0]][current_location[1]]
            if target_square.isalpha():
                return False
   
    return False

def perform_move(piece_status, move, board):
   
    #create a copy of the board to modify
    new_board = [row.copy() for row in board]
    board_length = len(board)
   
    #get piece type and location
    piece_type = piece_status[0]
    piece_location = piece_status[1]

    #handle fling: catapult stays, flung piece moves to destination
    if is_fling_move(move):
        
        _, fling_row, fling_col, destination_row, destination_col = move
        flung_piece = new_board[fling_row][fling_col]
        new_board[fling_row][fling_col] = '.'
        new_board[destination_row][destination_col] = flung_piece

        #pawn promotion on fling landing
        if flung_piece == "P" and destination_row == board_length - 1:

            new_board[destination_row][destination_col] = "H"
        elif flung_piece == "p" and destination_row == 0:

            new_board[destination_row][destination_col] = "h"

        #serpent poisoning at fling destination
        if flung_piece in ["S", "s"]:
            flung_loc = (destination_row, destination_col)
            serpent_poisoned_by_adjacent_opponent = False
            for delta_row in range(-1, 2):
                for delta_col in range(-1, 2):
                    if delta_row == 0 and delta_col == 0:
                        continue
                    neighbor_row = flung_loc[0] + delta_row
                    neighbor_col = flung_loc[1] + delta_col
                    if not in_bounds(neighbor_row, neighbor_col, new_board):
                        continue
                    neighbor_piece = new_board[neighbor_row][neighbor_col]
                    opponent_check = (neighbor_piece.isupper() and flung_piece.islower()) or (
                        neighbor_piece.islower() and flung_piece.isupper()
                    )
                    if neighbor_piece in ["S", "s", "E", "e"] and opponent_check:
                        serpent_poisoned_by_adjacent_opponent = True

            conversion_old_woman_location = None

            for delta_row in range(-1, 2):

                for delta_col in range(-1, 2):
                    target_location = (flung_loc[0] + delta_row, flung_loc[1] + delta_col)

                    if not (0 <= target_location[0] < board_length and 0 <= target_location[1] < len(new_board[target_location[0]])):
                        continue

                    target_piece = new_board[target_location[0]][target_location[1]]
                    is_opp = (target_piece.isupper() and flung_piece.islower()) or (target_piece.islower() and flung_piece.isupper())

                    # poison biological pieces (not time machines / golf carts)
                    if target_piece.isalpha() and is_opp and target_piece not in ["H", "h", "X", "x"]:
                        # conversion triggers when poisoning a non-old-woman piece that is adjacent to an opposing old woman
                        if target_piece not in ["O", "o"]:
                            for ow_delta_row in range(-1, 2):
                                for ow_delta_col in range(-1, 2):
                                    ow_row, ow_col = target_location[0] + ow_delta_row, target_location[1] + ow_delta_col
                                    if 0 <= ow_row < board_length and 0 <= ow_col < len(new_board[ow_row]):
                                        maybe_old_woman = new_board[ow_row][ow_col]
                                        if maybe_old_woman in ["O", "o"] and ((maybe_old_woman.isupper() and flung_piece.islower()) or (maybe_old_woman.islower() and flung_piece.isupper())):
                                            conversion_old_woman_location = (ow_row, ow_col)

                        new_board[target_location[0]][target_location[1]] = '.'

            if conversion_old_woman_location is not None:
                new_board[flung_loc[0]][flung_loc[1]] = '.'
                new_board[conversion_old_woman_location[0]][conversion_old_woman_location[1]] = "E" if flung_piece.islower() else "e"

            # If an opposing serpent/empress was adjacent to this serpent, it should die too.
            if serpent_poisoned_by_adjacent_opponent:
                new_board[flung_loc[0]][flung_loc[1]] = '.'

        #empress poisoning at fling destination
        if flung_piece in ["E", "e"]:
            flung_loc = (destination_row, destination_col)

            for delta_row in range(-1, 2):
                for delta_col in range(-1, 2):
                    target_location = (flung_loc[0] + delta_row, flung_loc[1] + delta_col)
                    if not (0 <= target_location[0] < board_length and 0 <= target_location[1] < len(new_board[target_location[0]])):
                        continue

                    target_piece = new_board[target_location[0]][target_location[1]]
                    is_opp = (target_piece.isupper() and flung_piece.islower()) or (target_piece.islower() and flung_piece.isupper())
                    if target_piece.isalpha() and is_opp and target_piece not in ["H", "h", "X", "x"]:
                        new_board[target_location[0]][target_location[1]] = '.'

        new_board = apply_after_effects(new_board)
        return new_board

    #calculate new location of piece after move
    new_location = (piece_location[0] + move[0], piece_location[1] + move[1])
   
    #move piece on new board (normal move); promotion (pawn→Time Machine, King→Jet Pack) is done in apply_promotion
    new_board[new_location[0]][new_location[1]] = piece_type
    new_board[piece_location[0]][piece_location[1]] = '.'
   
    #serpent will poison all adjacent enemy biological pieces (unless time machine or golf cart).
    #If it poisons any piece that is adjacent to an opposing old woman, the serpent dies and the old woman becomes a Grand Empress.
    if piece_type in ["S", "s"]:
       
        serpent_poisoned_by_adjacent_opponent = False
        for delta_row in range(-1, 2):
            for delta_col in range(-1, 2):
                if delta_row == 0 and delta_col == 0:
                    continue
                neighbor_row = new_location[0] + delta_row
                neighbor_col = new_location[1] + delta_col
                if not in_bounds(neighbor_row, neighbor_col, new_board):
                    continue
                neighbor_piece = new_board[neighbor_row][neighbor_col]
                opponent_check = (neighbor_piece.isupper() and piece_type.islower()) or (
                    neighbor_piece.islower() and piece_type.isupper()
                )
                if neighbor_piece in ["S", "s", "E", "e"] and opponent_check:
                    serpent_poisoned_by_adjacent_opponent = True

        conversion_old_woman_location = None
        old_woman_location = None
        for delta_row in range(-1, 2):
            for delta_col in range(-1, 2):
                target_location = (new_location[0] + delta_row, new_location[1] + delta_col)
                if not (0 <= target_location[0] < board_length and 0 <= target_location[1] < len(new_board[target_location[0]])):
                    continue
                target_piece = new_board[target_location[0]][target_location[1]]
                is_opponent = (target_piece.isupper() and piece_type.islower()) or (target_piece.islower() and piece_type.isupper())
               
                if target_piece.isalpha() and is_opponent and target_piece in ["O", "o"]:
                    old_woman_location = target_location
                   
                #don't let serpent kill time machines or golf carts
                if target_piece.isalpha() and is_opponent and target_piece not in ["H", "h", "X", "x"]:
                    if target_piece not in ["O", "o"]:
                        # conversion triggers when poisoning a non-old-woman piece adjacent to an opposing old woman
                        for ow_delta_row in range(-1, 2):
                            for ow_delta_col in range(-1, 2):
                                ow_row, ow_col = target_location[0] + ow_delta_row, target_location[1] + ow_delta_col
                                if 0 <= ow_row < board_length and 0 <= ow_col < len(new_board[ow_row]):
                                    maybe_old_woman = new_board[ow_row][ow_col]
                                    if maybe_old_woman in ["O", "o"] and ((maybe_old_woman.isupper() and piece_type.islower()) or (maybe_old_woman.islower() and piece_type.isupper())):
                                        conversion_old_woman_location = (ow_row, ow_col)
                    new_board[target_location[0]][target_location[1]] = '.'
                   
        #conversion rule
        if conversion_old_woman_location is not None:
            #serpent dies
            new_board[new_location[0]][new_location[1]] = '.'
            #old woman becomes an empress
            new_board[conversion_old_woman_location[0]][conversion_old_woman_location[1]] = "E" if piece_type.islower() else "e"

        # If an opposing serpent/empress was adjacent to this serpent, it should die too.
        if serpent_poisoned_by_adjacent_opponent:
            new_board[new_location[0]][new_location[1]] = '.'
           
    #empress will kill all enemy pieces in the 8 surrounding squares when it moves (unless that piece is a time machine or a golf cart which are unaffected)
    if piece_type in ["E", "e"]:
        for delta_row in range(-1, 2):
            for delta_col in range(-1, 2):
                target_row = new_location[0] + delta_row
                target_col = new_location[1] + delta_col
                if not (0 <= target_row < board_length and 0 <= target_col < len(new_board[target_row])):
                    continue
                target_piece = new_board[target_row][target_col]
                is_opponent_piece = (target_piece.isupper() and piece_type.islower()) or (
                    target_piece.islower() and piece_type.isupper()
                )

                # don't let empress kill time machines or golf carts
                if target_piece.isalpha() and is_opponent_piece and target_piece not in ["H", "h", "X", "x"]:
                    new_board[target_row][target_col] = '.'

    #gorilla: moves into adjacent square, pushing the piece there one step in same direction (capturing what's in that spot)
    if piece_type in ["G", "g"]:
        destination = (piece_status[1][0] + move[0], piece_status[1][1] + move[1])
        destination_piece = board[destination[0]][destination[1]]
        destination_of_destination = (destination[0] + move[0], destination[1] + move[1])
        if destination_piece.isalpha() and destination_piece not in ["G", "g"] and 0 <= destination_of_destination[0] < board_length and 0 <= destination_of_destination[1] < board_length:
            pushed_piece = destination_piece
            new_board[destination_of_destination[0]][destination_of_destination[1]] = pushed_piece
            new_board[destination[0]][destination[1]] = piece_type

    #if a non-catapult, non-time machine piece moves in a straight line or diagonal past an adjacent friendly catapult,
    #treat it as being flung to its landing square (capturing what was there)
    if piece_type not in ["C", "c", "H", "h"]:
        delta_row, delta_col = move
        if not (delta_row == 0 and delta_col == 0):
            if delta_row == 0 or delta_col == 0 or abs(delta_row) == abs(delta_col):
                distance = max(abs(delta_row), abs(delta_col))
                if distance >= 2:
                    step_row = 0 if delta_row == 0 else (1 if delta_row > 0 else -1)
                    step_col = 0 if delta_col == 0 else (1 if delta_col > 0 else -1)
                    adjacent_row = piece_location[0] + step_row
                    adjacent_col = piece_location[1] + step_col
                    if 0 <= adjacent_row < len(board) and 0 <= adjacent_col < len(board[adjacent_row]):
                        adjacent_piece = board[adjacent_row][adjacent_col]
                        if adjacent_piece in ["C", "c"]:
                            same_colour = (piece_type.isupper() and adjacent_piece.isupper()) or (piece_type.islower() and adjacent_piece.islower())
                            if same_colour:
                                fling_destination = new_location
                                if 0 <= fling_destination[0] < len(board) and 0 <= fling_destination[1] < len(board[fling_destination[0]]):
                                    fling_destination_piece = board[fling_destination[0]][fling_destination[1]]
                                    if fling_destination_piece.isalpha():
                                        new_board[fling_destination[0]][fling_destination[1]] = '.'
                                new_board[new_location[0]][new_location[1]] = '.'
                                new_board[fling_destination[0]][fling_destination[1]] = piece_type
           
    new_board = apply_after_effects(new_board)
    return new_board

def output_boards(board_status, valid_moves):
   
    board=board_status[1:-3]
   
    #output as board.000, board.001, etc.
    for move_index in range(len(valid_moves)):
        move = valid_moves[move_index]
        name = f"board.{move_index:03d}"
        piece_status=move[0]
        location_move=move[1]
        new_board = perform_move(piece_status, location_move, board)
       
        #switch turn
        next_turn = [['B']] if board_status[0][0] == 'W' else [['W']]
        new_board_status = next_turn + new_board + board_status[-3:]
        output_board(name, new_board_status)

    return

def output_board(name, board_status):
   
    filename = name
   
    with open(filename, 'w') as file_handle:
        for row in board_status:
            file_handle.write(''.join(row) + '\n')

if __name__ == "__main__":
   
    #read filename from standard input
    contents = sys.stdin.read()
   
    #get a 2D list representing the board's state
    board_state = get_board_state(contents)

    #get the board from the board state
    board = board_state[1:-3]
   
    #determine which pieces could move based on whose turn it is
    potential_pieces_list = get_pieces_of_current_player(board_state)
   
    #determine which of those pieces are actually on the board
    current_pieces_statuses = get_pieces_on_board(potential_pieces_list, board)
   
    #get all potential moves for pieces on the board
    all_moves = get_all_moves(current_pieces_statuses, board)
   
    #filter moves to only include those that are within bounds of the board
    within_bounds_moves=get_moves_within_bounds(all_moves, board)
   
    #filter moves to only include those that are valid based on new rules (ex. serpent cannot capture another piece)
    valid_moves_based_on_rules=get_possible_moves_based_on_rules(within_bounds_moves, board)
   
    #output all possible boards resulting from valid moves
    output_boards(board_state, valid_moves_based_on_rules)