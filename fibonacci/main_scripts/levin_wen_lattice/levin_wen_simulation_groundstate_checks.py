# fibonacci/main_scripts/levin_wen_lattice/levin_wen_simulation_groundstate_checks.py

# Run from root folder as:
# python -m fibonacci.main_scripts.levin_wen_lattice.levin_wen_simulation_groundstate_checks


import numpy as np

from qiskit_aer import AerSimulator

from fibonacci.geometry.three_plaquette import e1, e2, e3, e4, vertices
from fibonacci.diagnostics.state_inspection import print_amplitudes
from fibonacci.models.levin_wen_lattice import fibonacci_ground_state, fibonacci_closedLoops, fibonacci_code_on_three_plaquettes

from fibonacci.constraints.plaquette import measure_Bp_Exact, measure_Bp_sampling
from fibonacci.measurements.distributions import exact_distribution
from fibonacci.constraints.vertex import Qv_from_probs, compute_all_Qv_from_probs
from fibonacci.visualization.constraint_plot import plot_three_plaquette_constraints
    
    
if __name__ == "__main__":
    
    print("\n"*3)
    print("-"*60)
    print("Testing closed loop operators on Fibonacci ground state...")
    print("-"*60)
    # Test action of particle creation - annihilation around closed loops on ground-state
    fibonacci_closedLoops()
    
    
    
    
    # Circuit for the ground state of the Fibonacci Levin-Wen model on three plaquettes
    qc = fibonacci_ground_state()
    
    # print_amplitudes(qc) # For debugging
    
    # Measure the probability distribution of all qubits in qc
    P = exact_distribution(qc) # from statevector
    
    # Compute expectation values <Q_v>
    Qv = compute_all_Qv_from_probs(P, vertices)
    
    
    title = "Checking ground-state constraints"
    print("\n"*3 + title)
    print("="*len(title))

    title = "1. Vertex constraints Q_v:"
    print("\n" + title)
    print("-"*len(title))
    for v, val in enumerate(Qv):
        print(f"<Q_{v}> \t= {val:.4f}")
    print("-"*len(title))

    
    title = "2. Plaquette constraints B_p:"
    print("\n" + title)
    print("-"*len(title))
    # B_A, B_tau_A = measure_Bp_Exact(qc, plaquette="A")
    # B_B, B_tau_B = measure_Bp_Exact(qc, plaquette="B")
    # B_C, B_tau_C = measure_Bp_Exact(qc, plaquette="C")
    
    backend = AerSimulator()
    B_A, B_tau_A = measure_Bp_sampling(qc, backend, plaquette="A", shots=20_000)
    B_B, B_tau_B = measure_Bp_sampling(qc, backend, plaquette="B", shots=20_000)
    B_C, B_tau_C = measure_Bp_sampling(qc, backend, plaquette="C", shots=20_000)
    
    Bp_values = [B_A, B_B, B_C]
    Bp_tau_values = [B_tau_A, B_tau_B, B_tau_C]
    
    
    for (p, Bp, B_tau_p) in zip(["A", "B", "C"], Bp_values, Bp_tau_values):
        print(f"⟨ψ|B_{p}|ψ⟩ = {Bp:.4f}")
        print(f"⟨ψ|B^tau_{p}|ψ⟩ = {B_tau_p:.4f}")
        print()
    print("-"*len(title))
    
    print(qc.num_qubits)


    # Qv = np.random.rand(len(vertices))
    # Bp_values = np.random.rand(3)
    
    # Bp_values = [-1, -1, B]  # Plaquette order: A, B, C
    plot_three_plaquette_constraints(
        Qv,
        Bp_values,
        title="Levin-Wen Fibonacci Ground-State Check",
        show_edge_labels=True,
    )
