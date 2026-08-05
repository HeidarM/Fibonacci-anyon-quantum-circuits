import numpy as np

from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import Statevector


        



def overlap_statevector(qc_psi: QuantumCircuit, qc_phi: QuantumCircuit) -> complex:
    """
        qc_psi: circuit for |psi>
        qc_phi: circuit for |phi> = U|psi>
        Returns <psi|phi> = <psi|U|psi>.
    """
    psi = Statevector.from_instruction(qc_psi)
    phi = Statevector.from_instruction(qc_phi)
    return np.vdot(psi.data, phi.data)   # <psi|phi>