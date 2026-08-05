# fibonacci/gates/categorical_gates.py

import numpy as np

from qiskit.circuit import QuantumCircuit, Gate
from qiskit.circuit.library import UGate, DiagonalGate, UCGate

# NOTE: I have re-implemented some F-moves using UCGate (uniformly controlled/multiplexed gate).
# With UCGate, each |i>_control (multi-qubit control state) gives rise to the action of U_i on single target qubit |q>_target.
# By laying out the action for the full conditional/fusion table, QiSkit transpiles much more efficiently.
# See documentation https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.UCGate

# Gates for creating and manipulating Levin-Wen state such as F-moves

def Uf() -> UGate:
    phi = (1 + np.sqrt(5)) / 2.0
    theta = 2.0 * np.arccos(1.0 / phi)
    return UGate(theta, 0.0, np.pi, label="Uf")

def Us() -> UGate:
    phi = (1 + np.sqrt(5)) / 2.0
    theta = 2.0 * np.arctan(phi)
    return UGate(theta, 0.0, np.pi, label="Us")

def Ur() -> Gate:
    phase0 = np.exp(-4j * np.pi / 5)
    phase1 = np.exp(+3j * np.pi / 5)

    g = DiagonalGate([phase0, phase1])
    g.label = "Ur"
    return g


Id_matrix = np.eye(2, dtype=complex)
X_matrix = np.array([[0, 1], [1, 0]], dtype=complex)
fibonacci_phi = (1 + np.sqrt(5)) / 2.0
Uf_matrix = np.array([ [1.0 / fibonacci_phi, 1.0 / np.sqrt(fibonacci_phi)],
                       [1.0 / np.sqrt(fibonacci_phi), -1.0 / fibonacci_phi], ], dtype=complex,)


def Bp_isolated():
    # First qubit is used as seed edge
    qc = QuantumCircuit(6, name=f"loop")
    
    # put seed in (|0> + φ|1>)/√(1+φ^2)
    qc.append(Us(), [0])
    for q in range(1,6):
        qc.cx(0, q)
    return qc.to_gate()
    

def F1() -> Gate:
    qc = QuantumCircuit(5, name=f"F1")

    # Simple implementation:
    # qc.append(Uf().control(4), [0, 1, 2, 3, 4])
    # qc.cx(3, 1)
    # qc.cx(0, 2)
    # qc.ccx(1, 2, 4)
    # qc.cx(0, 2)
    # qc.cx(3, 1)

    # Optimized implementation using UCGate for better transpilation.
    # Blocks correspond to control states 0000, 0001, ..., 1111.
    blocks = []
    for state in range(16):
        # Binary representation of the control state (4 bits)
        # Example: state = 6 -> 0110 = (q3, q2, q1, q0) = (0, 1, 1, 0)
        q0 = (state >> 0) & 1
        q1 = (state >> 1) & 1
        q2 = (state >> 2) & 1
        q3 = (state >> 3) & 1

        if q0 and q1 and q2 and q3:
            # |q3 q2 q1 q0> = |1111> -> apply Uf
            blocks.append(Uf_matrix)
        elif (q1 ^ q3) and (q2 ^ q0):
            # |q3 q2 q1 q0> = |0011>, |0110>, |1001>, or |1100> -> apply X
            blocks.append(X_matrix)
        else:
            blocks.append(Id_matrix)

    qc.append(
        UCGate(blocks),
        [4, 0, 1, 2, 3],  # UCGate order is target, control0, control1, ...
    )

    return qc.to_gate()

def F2() -> Gate:
    qc = QuantumCircuit(4, name=f"F2")
    
    qc.append(Uf().control(3), [0, 1, 2, 3])
    qc.cx(0,2)
    qc.cx(0,1)
    qc.ccx(1,2,3)
    qc.cx(0,1)
    qc.cx(0,2)
    return qc.to_gate()

def F3() -> Gate:
    qc = QuantumCircuit(4, name=f"F3")

    # Simple implementation:
    # qc.append(Uf().control(3), [0, 1, 2, 3])
    # qc.cx(2, 0)
    # qc.x(1)
    # qc.ccx(0, 1, 3)
    # qc.x(1)
    # qc.cx(2, 0)

    # Optimized implementation using UCGate for better transpilation.
    # Blocks correspond to control states 000, 001, ..., 111.
    blocks = []
    for state in range(8):
        # Binary representation of the control state (3 bits)
        # Example: state = 3 -> 011 = (q2, q1, q0) = (0, 1, 1)
        q0 = (state >> 0) & 1
        q1 = (state >> 1) & 1
        q2 = (state >> 2) & 1
        
        if q0 and q1 and q2:
            # |q2 q1 q0> = |111> -> apply Uf
            blocks.append(Uf_matrix)
        elif (not q1) and (q0 ^ q2):
            # |q2 q1 q0> = |001> or |100> -> apply X
            blocks.append(X_matrix)
        else:
            blocks.append(Id_matrix)

    qc.append(
        UCGate(blocks),
        [3, 0, 1, 2],  # UCGate order is target, control0, control1, ...
    )
    return qc.to_gate()

# F3 but with c = 0
def F3x() -> Gate:
    qc = QuantumCircuit(3, name=f"F3x")
    
    # qc.cx(1,0)
    # qc.cx(0,2)
    # qc.cx(1,0)
    
    # Equivalent but with one less cx gate
    qc.cx(0, 2)
    qc.cx(1, 2)
    return qc.to_gate()


# F3 but with d = 0
def F3y() -> Gate:
    qc = QuantumCircuit(3, name=f"F3y")
    
    qc.x(1)
    qc.ccx(0,1,2)
    qc.x(1)
    return qc.to_gate()

# F3 but with b = c
def F3tilde() -> Gate:
    qc = QuantumCircuit(3, name=f"F3tilde")

    # Simple implementation:
    # qc.append(Uf().control(2), [0, 1, 2])
    # qc.cx(1, 0)
    # qc.cx(0, 2)
    # qc.cx(1, 0)

    # Optimized implementation using UCGate for better transpilation.
    # Blocks correspond to control states 00, 01, 10, 11.
    qc.append(
        UCGate(
            [
                Id_matrix,
                X_matrix,
                X_matrix,
                Uf_matrix,
            ]
        ),
        [2, 0, 1],  # UCGate order is target, control0, control1.
    )
    return qc.to_gate()



def F4() -> Gate:
    qc = QuantumCircuit(4, name=f"F4")
    
    qc.cx(2,0)
    qc.ccx(0,1,3)
    qc.cx(2,0)
    return qc.to_gate()

def F5() -> Gate:
    qc = QuantumCircuit(3, name=f"F5")

    # Simple implementation:
    # qc.append(Uf().control(2), [0, 1, 2])
    # qc.cx(1, 0)
    # qc.cx(0, 2)
    # qc.cx(1, 0)

    # Optimized implementation using UCGate for better transpilation.
    # Blocks correspond to control states 00, 01, 10, 11.
    qc.append(
        UCGate(
            [
                Id_matrix,
                X_matrix,
                X_matrix,
                Uf_matrix,
            ]
        ),
        [2, 0, 1],  # UCGate order is target, control0, control1.
    )
    return qc.to_gate()

def F6() -> Gate:
    qc = QuantumCircuit(3, name=f"F6")

    # Simple implementation:
    # qc.append(Uf().control(2), [0, 1, 2])
    # qc.x(0)
    # qc.x(1)
    # qc.ccx(0, 1, 2)
    # qc.x(0)
    # qc.x(1)

    # Optimized implementation using UCGate for better transpilation.
    # Blocks correspond to control states 00, 01, 10, 11.
    qc.append(
        UCGate(
            [
                X_matrix,
                Id_matrix,
                Id_matrix,
                Uf_matrix,
            ]
        ),
        [2, 0, 1],  # UCGate order is target, control0, control1.
    )
    return qc.to_gate()

# measurement_optimized is not the exact unitary: it omits a final diagonal correction, preserving only computational-basis measurement probabilities.
# Gives better transpilation results.
# Only use right before measurement, and not in the middle of a circuit.
def F7(measurement_optimized: bool = False) -> Gate:
    name = "F7_measurement" if measurement_optimized else "F7"
    qc = QuantumCircuit(3, name=name)

    # Simple implementation:
    # qc.append(Uf().control(2), [0, 1, 2])
    # qc.x(0)
    # qc.x(1)
    # qc.ccx(0, 1, 2)
    # qc.x(0)
    # qc.x(1)

    # Optimized implementation using UCGate for better transpilation.
    # Blocks correspond to control states 00, 01, 10, 11.
    qc.append(
        UCGate(
            [
                X_matrix,
                Id_matrix,
                Id_matrix,
                Uf_matrix,
            ],
            up_to_diagonal=measurement_optimized,
        ),
        [2, 0, 1],  # UCGate order is target, control0, control1.
    )
    return qc.to_gate()


def F8() -> Gate:
    qc = QuantumCircuit(3, name=f"F8")

    # Simple implementation:
    # qc.append(Uf().control(2), [0, 1, 2])

    # Optimized implementation.
    # Since Uf = Ry(beta) Z Ry(-beta) ---> CC(Uf) = Ry(beta) CCZ Ry(-beta)
    beta = np.arccos(1.0 / fibonacci_phi)
    qc.ry(-beta, 2)
    qc.ccz(0, 1, 2)
    qc.ry(beta, 2)
    
    
    # This commented out part is from the paper, but wrong.
    # qc.x(0)
    # qc.x(1)
    # qc.ccx(0, 1, 2)
    # qc.x(0)
    # qc.x(1)

    return qc.to_gate()

def F9() -> Gate:
    qc = QuantumCircuit(2, name=f"F9")
    
    qc.append(Uf().control(1), [0, 1])
    qc.x(0)
    qc.cx(0,1)
    qc.x(0)
    return qc.to_gate()

def Fx() -> Gate:
    qc = QuantumCircuit(3, name=f"Fx")

    # Simple implementation:
    # qc.append(Uf().control(2), [0, 2, 1])
    # qc.cx(0, 2)
    # qc.cx(2, 1)
    # qc.cx(0, 2)

    # Optimized implementation using UCGate for better transpilation.
    # Blocks correspond to control states 00, 01, 10, 11.
    qc.append(
        UCGate(
            [
                Id_matrix,
                X_matrix,
                X_matrix,
                Uf_matrix,
            ]
        ),
        [1, 0, 2],  # UCGate order is target, control0, control1.
    )
    return qc.to_gate()


def R1() -> Gate:
    qc = QuantumCircuit(3, name=f"R1")

    qc.append(Ur().control(2), [0, 1, 2])
    return qc.to_gate()

def R2() -> Gate:
    qc = QuantumCircuit(2, name=f"R2")
    
    qc.append(Ur().control(1), [0, 1])
    return qc.to_gate()






    
