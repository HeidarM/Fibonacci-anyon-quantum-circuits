# circuits/hadamard_test.py

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Gate

def hadamard_test(qc_state: QuantumCircuit, P_gate: Gate, imag: bool = False) -> QuantumCircuit:
    """
    Hadamard test that measures P on the state prepared by qc_state.
    
    If imag = fale: Measurement of Re<P>
                    |0>   -- H --.--- H -- Measurement-
                                 |
                    |psi> ------ P --------------------
    
    if imag = true: Measurement of Im<P>
                    |0>   -- H--S+---.--- H -- Measurement-
                                     |
                    |psi> ---------- P --------------------
    """
    
    # Copy state-prep and remember its original qubits (targets for P)
    qc = qc_state.copy()
    orig_qubits = list(qc.qubits)

    # Add ancilla + classical bit
    qa = QuantumRegister(1, "ancilla")
    ca = ClassicalRegister(1, "c_anc")
    qc.add_register(qa)
    qc.add_register(ca)
    anc = qa[0]

    # H-test
    qc.h(anc)
    if imag:
        qc.sdg(anc)

    # Controlled-P on the original system qubits
    # Assumes P_gate.num_qubits == len(orig_qubits)
    cP = P_gate.control(1)
    qc.append(cP, [anc, *orig_qubits])

    qc.h(anc)
    qc.measure(anc, ca[0])
    return qc
