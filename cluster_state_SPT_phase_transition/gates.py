# gates.py

import numpy as np
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import U3Gate
from qiskit_aer import AerSimulator

def U_gate(g):
    s = np.sign(g) if g != 0 else 1.0
    a = np.sqrt(abs(g))
    norm = np.sqrt(1+abs(g))

    theta_v = np.arcsin(a/norm)
    theta_w = np.arccos(s*a/norm)
    
    qc = QuantumCircuit(2)
    
    qc.x(0)

    # control- W
    Wtilde = U3Gate(theta_w, 0.0, 0.0)
    qc.append(Wtilde, [1])
    qc.cx(0, 1)
    qc.append(Wtilde.inverse(), [1])
    
    qc.x(0)

    # control-V
    Vt = U3Gate(theta_v, 0.0, 0.0)
    qc.append(Vt, [1])
    qc.cx(0, 1)
    qc.append(Vt.inverse(), [1])
    
    qc.x(0)

    return qc.to_gate(label=f"U({g:.2f})")


def U1_gate(g):

    theta_r = 2.0 * np.arcsin(1 / np.sqrt(1+abs(g)))
    
    qc = QuantumCircuit(2)
    
    qc.h(0)
    qc.cx(0, 1)
    
    R = U3Gate(theta_r, 0.0, np.pi)
    qc.append(R, [1])

    if g>0:
        qc.cz(0,1)

    return qc.to_gate(label=f"U1({g:.2f})")


def CY(qc: QuantumCircuit, control_qubit, target_qubit):
    # Creating CY from CX with a basis change on target qubit
    qc.s(target_qubit)
    qc.cx(control_qubit, target_qubit)
    qc.sdg(target_qubit)
