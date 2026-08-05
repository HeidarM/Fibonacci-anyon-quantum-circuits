# fibonacci/gates/anyonic_gates.py
from qiskit.circuit import QuantumCircuit, Gate
from fibonacci.gates.categorical_gates import *

from fibonacci.geometry.three_plaquette import e1, e2, plaqA, plaqB, plaqC, vertices
from fibonacci.geometry.three_plaquette import PlaqA_vertices, PlaqB_vertices, PlaqC_vertices
from fibonacci.geometry.three_plaquette import Ribbon_path_PlaqA, Ribbon_path_PlaqB, Ribbon_path_PlaqC



# ------ Higher-level gates for Fibonacci code ------
# Only correct if creating anyon on the edge
def create_taus(qc, edgeA, new_edge) -> QuantumCircuit:
    # Bond - edge configuration
    # A - B ---> A - (tau) new_edge (tau) - B
    qc.append(F9(), [edgeA, new_edge])

def annihilate_taus(qc, a, b, c, measurement_optimized: bool = False) -> QuantumCircuit:
    # Measurement optimization changes phases but preserves computational-basis probabilities.
    # Only use right before measurement, and not in the middle of a circuit as it's an approximation.
    qc.append(F7(measurement_optimized=measurement_optimized), [a, c, b])
    
# ------ Gates for moving anyons alongs paths -----
def move_tail(qc, v, x, y, tail, ribbon_twist=0, verbose=False):
    """
    Move the tail across vertex v from edge x -> edge y.
    
    tail: qubit index of the tail edge to be moved.
    
    ribbon_twist:
      0  : no twist
      +1 : apply R2()
      -1 : apply R2().inverse()
    """

    if x not in (0, 1, 2) or y not in (0, 1, 2):
        raise ValueError("x and y must be 0,1,2.")
    if x == y:
        raise ValueError("x and y must be different.")
    

    edges = vertices[v]
    src = edges[x]
    dst = edges[y]
    z = ({0, 1, 2} - {x, y}).pop()  # Third edge index
    third = edges[z]                # Third edge

    if src is None or dst is None:
        raise ValueError(f"Cannot move tail to or from boundary at vertex {v}.")

    # Printing path info
    if verbose:
        print(f"Moving tail from edge {src+1} to edge {dst+1} at vertex {v+1} with twist {ribbon_twist}.")

    if ribbon_twist == 1:
        qc.append(R2(), [tail, src])
        if verbose:
            print(f"qc.append(R2(), [tail, {src}])")
    elif ribbon_twist == -1:
        qc.append(R2().inverse(), [tail, src])
        if verbose:
            print(f"qc.append(R2().inverse(), [tail, {src}])")
    elif ribbon_twist != 0:
        raise ValueError("ribbon_twist must be -1, 0, or +1.")

    # Recouple - F-move
    if third is None:
        if verbose:
            print(f"F3x({src}, {dst}, tail)")
        qc.append(F3x(), [src, dst, tail])
    else:
        if verbose:
            print(f"F3({src}, {third}, {dst}, tail)")
        qc.append(F3(), [src, third, dst, tail])

    # print()
    
    # keep canonical convention: tail becomes the moved-to edge wire
    qc.swap(tail, dst)
    if verbose:
        print(f"qc.swap(tail, {dst})")
    
    
    # Undo ribbon twist
    if ribbon_twist == 1:
        qc.append(R2().inverse(), [tail, dst])
        if verbose:
            print(f"qc.append(R2().inverse(), [tail, {dst}])")
    elif ribbon_twist == -1:
        qc.append(R2(), [tail, dst])
        if verbose:
            print(f"qc.append(R2(), [tail, {dst}])")
    if verbose:
        print()
  

def move_tail_along_path(qc, ribbon_path, tail, verbose=False):
    for v, x, y, *rest in ribbon_path:
        ribbon_twist = rest[0] if rest else 0
        move_tail(qc, v, x, y, tail, ribbon_twist, verbose=verbose)
        
# ----- Bp operators -----
def Bp_tau_gate(plaquette="A") -> Gate:
    """
    Return the (unitary) tau-loop operator B_p^tau as a gate.
    """
    if plaquette == "A":
        Ribbon_path = Ribbon_path_PlaqA
        edges = plaqA
        vertices = PlaqA_vertices
    elif plaquette == "B":
        Ribbon_path = Ribbon_path_PlaqB
        edges = plaqB
        vertices = PlaqB_vertices
    elif plaquette == "C":
        Ribbon_path = Ribbon_path_PlaqC
        edges = plaqC
        vertices = PlaqC_vertices
    else:
        raise ValueError(f"Invalid plaquette: {plaquette}")

    qc = QuantumCircuit(18, name=f"Bp_tau_{plaquette}")

    # Copying the edge configurations to new edge degrees of freedom
    qc.cx(edges[0], e1)

    # Fuse anyon to the lattice with F-move
    qc.append(F9(), [e1, e2])

    # First step: Move left anyon one step clockwise around the plaquette
    if plaquette == "C":
        qc.append(F3(), [e2, 9, edges[1], e1])
    else:
        qc.append(F3x(), [e2, edges[1], e1])
    qc.swap(e1, edges[1])

    move_tail_along_path(qc, ribbon_path=Ribbon_path, tail=e1, verbose=False)

    qc.swap(e1, e2)

    # Fuse anyon away with F-move
    qc.append(F9().inverse(), [e1, e2])
    qc.cx(edges[0], e1)

    return qc.to_gate()


# -------- Topological gates --------
# Sigma gate for braiding tau-anyons
def Sigma() -> Gate:
    qc = QuantumCircuit(3, name="sig")

    qc.append(R2(), [0, 1])
    qc.append(F8(), [0, 2, 1])
    qc.append(R2().inverse(), [1, 2])

    return qc.to_gate()
