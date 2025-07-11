# /hanoi-tower/solve.py
def hanoi_solver(n, source, destination, auxiliary):
    """
    Solves the Tower of Hanoi problem recursively.
    Returns the list of moves.
    """
    moves = []
    if n > 0:
        moves.extend(hanoi_solver(n - 1, source, auxiliary, destination))
        moves.append((source, destination))
        moves.extend(hanoi_solver(n - 1, auxiliary, destination, source))
        return moves
    return []