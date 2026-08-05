# fibonacci/constraints/vertex.py

# Functions to measure vertex constraints <gs| Q_v | gs> for testing ground-state preparation


from fibonacci.measurements.distributions import get_bit


# Allowed fusions at each vertex
ALLOWED = {"000", "011", "101", "110", "111"}


def Qv_from_probs(probs, v):
    """
    Compute <Q_v> = sum_q[ P(q) delta_v(q) ] for vertex v, where delta_v(q) = 1 if q is an allowed vertex configuration.

    v = [a, b, c] (three qubit indices defining vertex v).
    If an edge is None, edge is treated as fixed to "0" (boundary condition)
    """

    a, b, c = v
    Qv = 0.0

    for bitstring, p in probs.items():
        # Extract the three bits associated to this vertex
        A = "0" if a is None else get_bit(bitstring, a)
        B = "0" if b is None else get_bit(bitstring, b)
        C = "0" if c is None else get_bit(bitstring, c)

        triple = A + B + C

        # delta_v(q) = 1 if triple is allowed, else 0
        if triple in ALLOWED:
            Qv += p

    return Qv

def compute_all_Qv_from_probs(probs, vertices):
    return [Qv_from_probs(probs, v) for v in vertices]
