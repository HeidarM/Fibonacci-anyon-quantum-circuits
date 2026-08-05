# toric_code/toric_code_modular_matrix_circuits.py
# run as python -m toric_code.toric_code_modular_matrix_circuits

# Prepares a three-plaquette toric-code ground state and uses Wilson-string circuits to exchange and braid e and m anyons.
# Hadamard tests measure their self and mutual statistics, giving the modular T and S matrices.

import numpy as np

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator
from qiskit.circuit import Gate

from circuits.hadamard_test import hadamard_test


def B_circ(qc, p):
    # Act with B_p operator on circuit qc on edges in plaquette p
    # B_p = prod_{i\in p} X_i - creating a closed string
    
    q0 = p[0] # control qubit
    qc.h(q0)
    
    # CX fan to: |0> -> 1/sqrt(2) (|0> + |1>) for full plaquette
    for q in p[1::]:
        qc.cx(q0, q)
 
def W_e(qc, curve, qe=1):
        # Act with W_e[l] = prod_{i\in l} X_i Wilson line for electric charge
        if qe == 1:
            for q in curve:
                qc.x(q)

def W_m(qc, curve, qm=1):
        # Act with W_m[ld] = prod_{i\in ld} Z_i Wilson line for magnetic charge (curve on dual lattice)
        if qm == 1:
            for q in curve:
                qc.z(q)
    
    
def toric_code_state_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(15) # Honeycomb lattice with qubits on edges with 3 faces/plaquettes
    
    # Plaquettes
    p1 = [0, 1, 2, 3, 4, 5]
    p2 = [6, 4, 7, 8, 9, 10]
    p3 = [11, 12, 13, 2, 14, 6]

    # Create state using plaquettes: As|psi> = |psi> already satisfied
    B_circ(qc,p1)
    B_circ(qc,p2)
    B_circ(qc,p3)
    
    return qc


def make_anyon_exchange_gate(charge=(1,1)) -> Gate:
    qc = QuantumCircuit(15)

    qe, qm = charge

    # ---- Create anyons: pull out of boundary ----
    # Create first dyon d = em
    W_e(qc, [4, 2], qe)
    W_m(qc, [5], qm)
    # Create second dyon d = em
    W_e(qc, [7, 9], qe)
    W_m(qc, [10], qm)

    # ---- Move step 1 ----
    W_e(qc, [14, 13], qe)
    W_m(qc, [6], qm)

    # ---- Move step 2 ----
    W_e(qc, [2, 6], qe)
    W_m(qc, [4], qm)

    # ---- Move step 3 ----
    W_e(qc, [11, 12], qe)
    W_m(qc, [2], qm)

    # ---- Annihilate anyons: push into boundary ----
    W_e(qc, [7, 9], qe)
    W_m(qc, [10], qm)
    W_e(qc, [4, 2], qe)
    W_m(qc, [5], qm)

    return qc.to_gate(label="W_em")


def make_anyon_double_exchange_gate(charge1=(1,0), charge2=(0,1)) -> Gate:
    qc = QuantumCircuit(15)

    q1e, q1m = charge1
    q2e, q2m = charge2

    # ---- Create anyons: pull out of boundary ----
    # Create first dyon d1 = e1m1
    W_e(qc, [4, 2], q1e)
    W_m(qc, [5], q1m)
    # Create second dyon d2 = e2m2
    W_e(qc, [7, 9], q2e)
    W_m(qc, [10], q2m)

    # ---- First exchange ----
    W_e(qc, [14, 13], q2e)
    W_m(qc, [6], q2m)

    W_e(qc, [2, 6], q1e)
    W_m(qc, [4], q1m)

    W_e(qc, [11, 12], q2e)
    W_m(qc, [2], q2m)
    
    # ---- Second exchange ----
    W_e(qc, [14, 13], q1e)
    W_m(qc, [6], q1m)
    
    W_e(qc, [2, 6], q2e)
    W_m(qc, [4], q2m)

    W_e(qc, [11, 12], q1e)
    W_m(qc, [2], q1m)

    # ---- Annihilate anyons: push into boundary ----
    W_e(qc, [7, 9], q2e)
    W_m(qc, [10], q2m)
    W_e(qc, [4, 2], q1e)
    W_m(qc, [5], q1m)

    return qc.to_gate(label="W_em")


def ancilla_expectation(counts: dict) -> float:
    # Return <Z_a> = (p0 - p1) from ancilla counts.
    n0 = counts.get('0', 0)
    n1 = counts.get('1', 0)
    return (n0 - n1) / (n0 + n1)


def measure_circuit(qc):
    # Simulate
    sim = AerSimulator(seed_simulator=1234)
    tqc = transpile(qc, sim, optimization_level=3)
    res = sim.run(tqc, shots=20_000).result()
    
    # Compute <W...W> = <psi'| W...W |psi'> from Z-measurement counts
    counts = res.get_counts()
    expectation_value = ancilla_expectation(counts)
    
    # print(f"⟨W...W⟩ ≈", expectation_value)
    return expectation_value

def T_matrix():
    T_diag = np.array([])   # self-statitics
    
    for [qe, qm] in [[0,0], [0,1], [1,0], [1,1]]:
        # Create circuit
        qc_state = toric_code_state_circuit()
        P = make_anyon_exchange_gate(charge=[qe, qm])
        qc = hadamard_test(qc_state, P, imag=False)
        
        self_statistics = measure_circuit(qc)
        T_diag = np.append(T_diag, self_statistics)
    
    T_matrix = np.diag(T_diag)
        
    return T_matrix

def S_matrix():
    S = np.zeros((4,4))
    
    charges = [[0,0], [0,1], [1,0], [1,1]]
    
    for d1 in charges:
        for d2 in charges:
            # Create circuit
            qc_state = toric_code_state_circuit()
            P = make_anyon_double_exchange_gate(charge1=d1, charge2=d2)
            qc = hadamard_test(qc_state, P, imag=False)
            
            mutual_statistics = measure_circuit(qc)
            print(f"({d1[0]},{d1[1]}) -> {charges.index(d1)}")
            S[charges.index(d1), charges.index(d2)] = mutual_statistics

    return S




T = np.real_if_close(T_matrix())
print(f"T = \n{T}")


print()
S = np.real_if_close(S_matrix())
print(f"S = \n{S}")
