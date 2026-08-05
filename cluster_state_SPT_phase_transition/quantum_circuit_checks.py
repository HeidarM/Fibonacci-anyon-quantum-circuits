# quantum_circuit_checks.py

import numpy as np
from qiskit.quantum_info import Operator

from cluster_string_order_quantum_circuit import iMPS_state_circuit
from gates import U_gate, U1_gate



g = 0.8
U = U_gate(g)
U1 = U1_gate(g)

U_matrix = np.real_if_close( Operator(U).data )
U1_matrix = np.real_if_close( Operator(U1).data )

# Change basis from |q1 q0> to |q0 q1> for comparison
P = np.array([[1,0,0,0],
              [0,0,1,0],
              [0,1,0,0],
              [0,0,0,1]], dtype=complex)

print("U = ")
print( P @ U_matrix @ P.T.conj() )
print()
print("U1 = ")
print( P @ U1_matrix @ P.T.conj() )


qc = iMPS_state_circuit(L=4, g=g)
print(qc)
