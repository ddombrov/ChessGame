# Chess-Variant AI

An AI player for a custom chess variant (extra piece types: serpent, empress, old woman,
gorilla, catapult, beekeeper, golf cart, time machine, joey) on a larger board.

`chess_ai.py` implements move selection: minimax search with alpha-beta pruning, a
transposition table for memoized positions, capture-first move ordering, a hardcoded
opening book, and a time-adaptive search depth that shrinks as the clock runs low.

`move_engine.py` provides board parsing and legal move generation for the variant.

Ranked 9th of 85 in a class-wide tournament.
