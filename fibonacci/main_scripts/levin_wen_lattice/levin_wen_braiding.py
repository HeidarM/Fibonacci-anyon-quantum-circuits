# fibonacci/main_scripts/levin_wen_lattice/levin_wen_braiding.py

# Run from root folder as:
# python -m fibonacci.main_scripts.levin_wen_lattice.levin_wen_braiding

import numpy as np

from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import Statevector, partial_trace
from qiskit_aer import Aer

from fibonacci.geometry.three_plaquette import e1, e2, e3, e4
from fibonacci.models.levin_wen_lattice import fibonacci_ground_state, fibonacci_closedLoops, fibonacci_code_on_three_plaquettes


from fibonacci.diagnostics.state_inspection import print_fusion_stats_bits, print_fusion_stats



def fusion_probs(qc, f_qubit):
    psi = Statevector.from_instruction(qc)
    n = qc.num_qubits
    p0 = p1 = 0.0

    for i, amp in enumerate(psi.data):
        pr = abs(amp)**2
        if pr < 1e-14:
            continue
        bits = format(i, f"0{n}b")
        b = bits[-1 - f_qubit]   # qiskit little-endian
        if b == "0":
            p0 += pr
        else:
            p1 += pr

    # interpret: 0->f=1, 1->f=tau
    return {"f=1 (|0>)": p0, "f=tau (|1>)": p1}


def measure_fusion_2qubits(qc, qA, qB, tol=1e-14):
    """
    Measure fusion outcomes |00>,|01>,|10>,|11>
    for two fusion-output qubits qA, qB.

    0 -> vacuum (1)
    1 -> tau (τ)
    """

    psi = Statevector.from_instruction(qc)
    n = qc.num_qubits

    P = { 
        "00": 0.0,
        "01": 0.0,
        "10": 0.0,
        "11": 0.0
    }

    for i, amp in enumerate(psi.data):

        pr = abs(amp)**2
        if pr < tol:
            continue

        bits = format(i, f"0{n}b")

        # Qiskit little-endian
        bA = bits[-1 - qA]
        bB = bits[-1 - qB]

        P[bA + bB] += pr

    return P


    
    

def fusion_state_2q(qc, q1, q2):
    # Get reduced density matrix for two fusion-output qubits q1, q2
    psi = Statevector.from_instruction(qc)

    keep = [q1, q2]
    traced = partial_trace(
        psi,
        [i for i in range(qc.num_qubits) if i not in keep]
    )

    return traced.data   # 4x4 density matrix







if __name__ == "__main__":
    

    # Create three pairs of anyons on a section of the three-plaquette honeycomb lattice
    edges = [12, 14, 13, 11]
    ancillas = [e1, e2, e3]
    
    # Approximation to Hadamard gate
    hadamard = [
        's1','s1','s1','s1',
        'si2','si2',
        's1','s1',
        'si2','si2',
        's1','s1',
        's2','s2',
        'si1','si1',
        's2','s2','s2','s2',
        's1','s1',
        'si2','si2',
        'si1','si1',
        's2','s2',
        's1','s1'
    ]
    
    Z_gate = ['s1'] * 5
    X_gate = hadamard + Z_gate + hadamard



    
    braid_experiments = [
        ("I", []),
        ("s1", ["s1"]),
        ("s2", ["s2"]),
        ("s3", ["s3"]),
        ("s2 s1", ["s2", "s1"]),
        ("s2 s1 s2", ["s2", "s1", "s2"]),
        ("s2^2", ["s2", "s2"]),
        ("s2^3", ["s2", "s2", "s2"]),
        ("Z = s1^5", Z_gate),
        ("H approximation", hadamard),
        ("X = H Z H approximation", X_gate),
    ]
    show_reduced_density_matrix = False

    # Braiding fibonacci anyons on three-plaquette honeycomb lattice
    for label, topological_gates in braid_experiments:
        qc = fibonacci_code_on_three_plaquettes( edges=edges,
                                        ancillas=ancillas,
                                        topological_gates=topological_gates)
        
        heading = f"Topological gates: {label}"
        print("-" * len(heading))
        print(heading)
        print("-" * len(heading))
        
        P = measure_fusion_2qubits(qc, e1, e2)

        print("Post-braiding fusion statistics:")
        print_fusion_stats(P)

        if show_reduced_density_matrix:
            rho = fusion_state_2q(qc, e1, e2)
            print()
            print("Reduced fusion-channel density matrix:")
            print(np.round(rho, 4))
        
        print()


    
    # Qv_exact = exact_all_Qv(qc, vertices)
    
    # Qv = measure_all_Qv(qc, vertices, shots=10000)

    # print("From measurement:")
    # for v, val in enumerate(Qv):
    #     print(f"Q_{v} = {val:.4f}")
    
    # print("\nFrom wave function: ")
    # for v, val in enumerate(Qv_exact):
    #     print(f"Q_{v} = {val:.6f}")
        
    # Bp, B_tau_p = measure_Bp_Exact(qc)
    # print("\n⟨ψ|B_p|ψ⟩ =", Bp)
    # print("⟨ψ|B^tau_p|ψ⟩ =", B_tau_p)
    
    # print()
    
    # p0, p1 = prob_qubit(qc, e2)

    # print("\nP(0) =", p0)
    # print("P(1) =", p1)
    
    # print()
    
    # print(fusion_probs(qc, e4))
    # print(fusion_probs(qc, e2))
    
    # print()
    
    # P = measure_fusion_2qubits(qc, e2, e3)

    # print("Fusion statistics:")
    # print_fusion_stats(P)


    
    # rho = get_logical_qubit(qc, e3)
    # print(rho)
    
    # print()
    
    # vec, purity = logical_qubit_state(qc, e3)

    # print("Purity:", purity)
    # print("State:", vec)
    
