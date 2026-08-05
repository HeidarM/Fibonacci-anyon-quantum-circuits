# fibonacci/models/topological_code.py

from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister

from fibonacci.gates.categorical_gates import *
from fibonacci.gates.anyonic_gates import create_taus, annihilate_taus, Sigma
from fibonacci.diagnostics.state_inspection import print_amplitudes



# Trivalent graph consistent of a n-sided polygon plaquette with trivial tails at each vertex for ground-state
# Fibonacci excitations: a pair for each vertex (vertex splits -> one extra ancilla)
# Measurement optimization is an approximation but does not change computational-basis measurements.
def fibonacci_code(num_pairs, topological_gates, measurement_optimized: bool = True) -> QuantumCircuit:

    # For the Fibonacci code ground-state
    n = num_pairs
        
    N = n + num_pairs # Total number of qubits (polygon edges + ancillas for excitations)
    
    # Main polygon qubits
    p = QuantumRegister(n, name="p")
    # Ancillas for excitations
    a = QuantumRegister(num_pairs, name="a")
    # Classical bits for fusion outcomes
    creg = ClassicalRegister(2*num_pairs, "c")
    

    # Circuit
    qc = QuantumCircuit(a, p, creg)

    # ----- Ground state -----
    # GS of Fibonacci code on the n-sided polygon with trivial tails
    qc.append(Us(), [p[0]])  # put seed in (|0> + φ|1>)/√(1+φ^2)
    for q in range(1, n):  # CX fan
        qc.cx(p[0], p[q])
    
    # ----- Create anyon-pairs at each vertex -----
    for q in range(num_pairs):
        create_taus(qc, p[q], a[q])
    
    # ----- Topological gates: braiding anyons -----
    # Allow: s1, s2, ... and si1, si2, ...
    allowed_gates = (
        {f"s{i}"  for i in range(1, 2*num_pairs+1)} |
        {f"si{i}" for i in range(1, 2*num_pairs+1)}
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

        # i even
        if i % 2 == 0:
            q = i // 2
            qc.append(G, [a[(q-1) % num_pairs], p[(q-1) % n], a[q % num_pairs]])
        # i odd
        else:
            q = (i-1) // 2
            qc.append(G, [p[(q-1) % n], a[q % num_pairs], p[q % n]])
    
        
    # ----- Annihilate anyon pairs-----
    for q in range(num_pairs):
        annihilate_taus(qc, p[(q-1) % n], a[q], p[q], measurement_optimized=measurement_optimized)
    
    # # ---- Annihilate anyons to form standard fusion tree basis -----
    # qc.append(F7(), [p[n-1], p[0], a[0]])
    # qc.append(F3(), [a[1], p[n-1], a[0], p[0]])
    
    # for i in range(1, n-1):
    #     qc.append(F3(), [p[i], p[n-1], p[i-1], a[i]])
    #     qc.append(F3(), [a[i+1], p[n-1], a[i], p[i]])
    
    # qc.append(F3tilde(),[p[n-1], p[n-2], a[n-1]])

    # ----- Measure fusion outcomes (logical qubits) -----
    qc.measure(a, creg[:num_pairs])
    qc.measure(p, creg[num_pairs:2*num_pairs])



    return qc
