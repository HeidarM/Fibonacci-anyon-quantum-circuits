# fibonacci/diagnostics/state_inspection.py

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import Statevector

def print_amplitudes(qc: QuantumCircuit, threshold=1e-12, tol=1e-10):
    psi = Statevector.from_instruction(qc)
    n = qc.num_qubits

    for i, amp in enumerate(psi.data):
        if abs(amp) > threshold:
            amp_clean = np.real_if_close(amp, tol=tol)
            print(f"{amp_clean:+.6g} |{i:0{n}b}>")
            
            

def print_fusion_stats_bits(P, numbered=False):
    for i, k in enumerate(sorted(P)):
        n = len(k)
        mid = n // 2

        # Split the bitstring in half
        left = k[:mid]
        right = k[mid:]
        formatted = f"{left};{right}"

        if numbered:
            print(f"{i+1}:\t |{formatted}>: {P[k]}")
        else:
            print(f"|{formatted}>: {P[k]}")


def print_fusion_stats(P):
    print("|00>:", P["00"])
    print("|01>:", P["01"])
    print("|10>:", P["10"])
    print("|11>:", P["11"])
