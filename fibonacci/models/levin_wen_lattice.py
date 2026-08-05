# fibonacci/models/levin_wen_lattice.py

# Function overview:

# (1) fibonacci_ground_state: create ground-state of Levin-Wen model on with Quantum Circuit with
# C = Fibonaci category
# Z(C) = C x C^* = doubled Fibonacci modular tensor category

# (2) fibonacci_closedLoops: Create anyons from vacuum, move along various loops and annihilate
# <gs| W_loop |gs>

# (3) fibonacci_code_Three_Plaq: Braiding (topological computation) with four anyons in Levin-Wen model

from qiskit.circuit import QuantumCircuit

from fibonacci.gates.categorical_gates import *
from fibonacci.gates.anyonic_gates import create_taus, annihilate_taus, Sigma
from fibonacci.diagnostics.state_inspection import print_amplitudes
from fibonacci.gates.anyonic_gates import move_tail_along_path
from fibonacci.measurements.statevector_tools import overlap_statevector

from fibonacci.geometry.three_plaquette import *


# Three plaquettes           
def fibonacci_ground_state_original(number_of_anyon_pairs = 2) -> QuantumCircuit:

    # For GS construction + first 3 anyon pairs
    ancillas = 3

    # For extra anyon pairs
    if number_of_anyon_pairs > 3:
        ancillas += number_of_anyon_pairs - 3
        
    # Three plaquettes with qubits on edges (15 qubits)
    # Plus 3 ancilla qubits cA cB, cC (for 3 plaquettes)
    # Plus extra ancillas so there is room to create excitations
    qc = QuantumCircuit(15 + ancillas)


    # Prepare the ground state of the Fibonacci code
    
    # Prepare plaquette B
    qc.append(Us(), [cB])
    for e in plaqB:
        qc.cx(cB, e) # CX fan
    qc.cx(BCedge, cB)
    
    # print("\nAfter plaquette B:")
    # print_amplitudes(qc)
    
    # Prepare plaquette C
    qc.cx(BCedge, cB)
    qc.append(Us(), [cC])
    qc.cx(cB,BCedge)
    for e in plaqC:
        if e != BCedge:
            qc.cx(cC, e) # CX fan
    qc.append(Fx(), [cB, BCedge, cC])
    qc.cx(0, cC)
    qc.cx(14, cB)
    # print("\nAfter plaquette C:")
    # print_amplitudes(qc)
    
    # Prepare plaquette A
    qc.append(Us(), [cA])
    qc.cx(12,ABedge)
    qc.cx(ACedge, ABedge)
    qc.cx(1,ACedge)
    qc.cx(0, cC)
    for e in plaqA:
        if e not in (ABedge, ACedge):
            qc.cx(cA, e)  # CX fan
    qc.append(Fx(), [cA, ACedge, cC])
    qc.append(F1(), [11, 12, BCedge, ACedge, ABedge])
    qc.cx(0, cC)
    qc.cx(3, cA)
    # print("\nAfter plaquette A:")
    # print_amplitudes(qc)


    return qc


# optimized version
def fibonacci_ground_state(number_of_anyon_pairs = 2) -> QuantumCircuit:

    # For GS construction + first 3 anyon pairs
    ancillas = 3

    # For extra anyon pairs
    if number_of_anyon_pairs > 3:
        ancillas += number_of_anyon_pairs - 3

    # Three plaquettes with qubits on edges (15 qubits)
    # Plus 3 unused center/anyon ancilla qubits cA, cB, cC
    # Plus extra ancillas so there is room to create excitations
    qc = QuantumCircuit(15 + ancillas)

    # State-preparation equivalent to fibonacci_ground_state on |0...0>.
    # The plaquette center qubits are replaced by edge qubits that carry the
    # same copied value in the original circuit:
    #
    #   cB -> edge 14, a plaquette-B edge
    #   cC -> edge 0,  a plaquette-C edge
    #   cA -> edge 3,  a plaquette-A edge
    #
    # The physical qubits cA=15, cB=16, cC=17 remain allocated and stay in |0>,
    # so the circuit keeps the same qubit numbering expected by the rest of
    # the code.
    seed_B = 14
    seed_C = 0
    seed_A = 3

    # Prepare plaquette B using edge 14 instead of center cB.
    qc.append(Us(), [seed_B])
    for e in plaqB:
        if e not in (seed_B, BCedge):
            qc.cx(seed_B, e)

    # Prepare plaquette C using edge 0 instead of center cC.
    qc.append(Us(), [seed_C])
    for e in plaqC:
        if e not in (seed_C, BCedge):
            qc.cx(seed_C, e)
    qc.append(Fx(), [seed_B, BCedge, seed_C])

    # Prepare plaquette A using edge 3 instead of center cA.
    qc.append(Us(), [seed_A])
    qc.cx(12, ABedge)
    qc.cx(ACedge, ABedge)
    qc.cx(1, ACedge)
    for e in plaqA:
        if e not in (seed_A, ABedge, ACedge):
            qc.cx(seed_A, e)
    qc.append(Fx(), [seed_A, ACedge, seed_C])
    qc.append(F1(), [11, 12, BCedge, ACedge, ABedge])

    return qc




# Experimenting by creating various closed loops of tau-anyons - should not change ground-state
def fibonacci_closedLoops():
    qc = fibonacci_ground_state()
    
    # print("\nGS:")
    # print_amplitudes(qc)
    
    print("Checking varous closed loops of tau-anyons on the ground-state of the Fibonacci Levin-Wen model starting from bottom of plaquette C and moving clockwise around...")

    
    Ribbon_paths = [Ribbon_path_PlaqB, Ribbon_path_PlaqBA, Ribbon_path_PlaqBC, Ribbon_path_PlaqABC]
    Path_names = ["PlaqB", "PlaqBA", "PlaqBC", "PlaqABC"]
    qcs = []
    
    for Ribbon_path in Ribbon_paths:
        qc_path = qc.copy()
        # --- Create anyon pair and move around plaquette then annihilate: should stabilize the ground-state ---
        # Copying the edge configurations to new edge degrees of freedom
        qc_path.cx(14, e1)
        # Fuse anyon to the lattice with F-move
        qc_path.append(F9(), [e1, e2])
        
        # First step: Move left anyon from 14 -> 12
        qc_path.append(F3x(), [e2, 12, e1])
        qc_path.swap(e1, 12)
        
        move_tail_along_path(qc_path, ribbon_path = Ribbon_path, tail = e1, verbose=False)
        
        qc_path.swap(e1, e2)
        
        # Fuse anyon away with F-move
        qc_path.append(F7(), [e1, 14, e2])
        qc_path.cx(14, e1)
        
        qcs.append(qc_path)

    for path, qc_path in zip(Path_names, qcs):
        print("\nFor path around", path, ":")
        # print_amplitudes(qc_path)
        # Compute overlap with ground-state
        amp = overlap_statevector(qc, qc_path)
        print("⟨ψ|U|ψ⟩ =", np.real_if_close(amp))
        print("fidelity |⟨ψ|U|ψ⟩|^2 =", abs(amp)**2)




def fibonacci_code_on_three_plaquettes(edges, ancillas, topological_gates):
    
    number_of_anyon_pairs = len(edges)
    
    qc = fibonacci_ground_state(number_of_anyon_pairs=number_of_anyon_pairs)
    
    # Create anyon pairs on the edges and fuse them to the lattice
    for (a, e) in zip(edges, ancillas):
        create_taus(qc, a, e)
    
    # Order of bonds for applying topological gates:
    # bonds = (a1, e1, a2, e1, ...)
    bonds = [x for pair in zip(edges, ancillas) for x in pair] + [edges[-1]]

    max_n = len(bonds) - 2
    # Allow: s1, s2, ... and si1, si2, ...
    allowed_gates = (
        {f"s{i}"  for i in range(1, max_n + 1)} |
        {f"si{i}" for i in range(1, max_n + 1)}
    )

    for gate in topological_gates:
        if gate not in allowed_gates:
            raise ValueError(f"Invalid topological gate: {gate}")

        # Extract index
        if gate.startswith("si"):
            i = int(gate[2:])   # after "si"
            G = Sigma().inverse()
        else:
            i = int(gate[1:])   # after "s"
            G = Sigma()

        qc.append(G, [bonds[i-1], bonds[i], bonds[i+1]])

    
    # Annihilate anyons on the edges
    for i in range(0, len(bonds) - 2, 2):
        a  = bonds[i]
        e = bonds[i + 1]
        b = bonds[i + 2]
        annihilate_taus(qc, a, e, b)
    
    return qc
