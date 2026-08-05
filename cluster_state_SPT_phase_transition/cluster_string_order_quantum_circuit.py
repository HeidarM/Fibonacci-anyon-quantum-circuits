# cluster_string_order_quantum_circuit.py
# Compute ⟨S1⟩ and ⟨S_ZY⟩ using quantum circuits

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from gates import U_gate, U1_gate, CY

# -------- Create State --------
# Creating |psi(g)> using iMPS-based circuit
def iMPS_state_circuit(L, g):
    U = U_gate(g)
    U1 = U1_gate(g)

    # q[0,1] = bond ancillas, q[2..L+1] = physical sites
    qc = QuantumCircuit(L+2)  # +2 for ancilla qubits
    
    # |phi>
    qc.append(U1, [0,1])
    for i in range(1, L+1):
        qc.append(U, [i, i+1]) # Moves ancilla from i to i+1 as well
        
    # Ancilla's are now at q0 and q_{L+1}
    # Physical sites: q1 ... q_L
    
    return qc


# -------- Direct Measurement of String Order Parameters --------
# Create circuit that prepares |psi(g)> and performs direct measurement of S1 or S_ZY
def create_direct_measurement_circuit(L, g, measure: str = "S1"):

    # Ancilla's are at q0 and q_{L+1}
    # Physical sites: q1 ... q_L
    qc = iMPS_state_circuit(L, g) # |psi>
    
    # Add L classical bits for the L measured sites
    creg = ClassicalRegister(L, "c_phys")
    qc.add_register(creg)
 
    if measure == "S1":
        # change basis X -> Z
        # |psi'> = H^{\otimes L} |psi>
        for i in range(1, L+1):
            qc.h(i)
            qc.measure(i, creg[i-1])   # Measure in Z basis (except ancilla), put into classical register i-2
            
    elif measure == "SZY":
        # change basis Z Y X...X Y Z -> Z^{\otimes L}
        qc.z(1)    # first Z
        qc.sdg(2); qc.h(2)  # first Y -> Z
        
        # middle X...X -> Z...Z
        for i in range(3, L-1):
            qc.h(i)
            
        qc.sdg(L-1); qc.h(L-1)  # last Y -> Z
        qc.z(L)  # last Z
        
        # measure all in Z basis
        for i in range(1, L+1):
            qc.measure(i, creg[i-1])

    return qc


def compute_S_from_counts(counts: dict, measure: str = "S1") -> float:
    # Compute <psi'| Z...Z |psi'> from measurement counts in Z basis.
    # Both S1 = <X...X> and S_ZY = <Z Y X...X Y Z> have been mapped to this form (for different |psi'>).
    shots = sum(counts.values())
    
    expectation_value = 0.0
    for bitstr, c in counts.items():
        ones = bitstr.count('1')
        
        # prod_i x_i = ±1
        x = 1.0 if (ones % 2 == 0) else -1.0
        
        expectation_value += x * (c / shots)
        
    error = ( (1.0 - expectation_value**2) / shots )**0.5
    # print(f"⟨{measure}⟩ ≈", expectation_value, "±", error)
    return expectation_value, error

def direct_string_order_measurement(L, g, measure: str = "S1"):
    
    # Create circuit
    qc = create_direct_measurement_circuit(L=L, g=g, measure=measure)
    
    # Simulate
    sim = AerSimulator(seed_simulator=1234)
    tqc = transpile(qc, sim, optimization_level=3)
    res = sim.run(tqc, shots=20_000).result()
    
    # Compute <S> = <psi'| Z...Z |psi'> from Z-measurement counts
    counts = res.get_counts()
    expectation_value, error = compute_S_from_counts(counts, measure=measure)
    return expectation_value, error


# -------- Hadamard Test for String Order Parameter ⟨S_ZY⟩ --------
def hadamard_test_string_order(qc_state: QuantumCircuit, L: int, measure = "S1", imag=False):
    """
    Hadamard test that measures P = <Z_i Y...Y Z_j> on the state prepared by qc_state.
    
    If imag = fale: Measurement of Re<P>
                    |0>   -- H --.--- H -- Measurement-
                                 |
                    |psi> ------ P --------------------
    
    if imag = true: Measurement of Im<P>
                    |0>   -- H--S+---.--- H -- Measurement-
                                     |
                    |psi> ---------- P --------------------
                    
    NOTE: This version is fine for simulator, but too non-local for real hardware.
    For real hardware: we must use swap gates to move the ancilla.
    """
    # |psi>
    qc = qc_state.copy()
    
    # Add ancilla qubit and classical bit
    qa = QuantumRegister(1, "ancilla")
    ca = ClassicalRegister(1, "classical bit")
    
    qc.add_register(qa)
    qc.add_register(ca)
    ancilla = qa[0]

    qc.h(ancilla)
    if imag:
        qc.sdg(ancilla)
        
    # Apply control-P (controlled string order operator)
    apply_controlled_cluster_string_order(qc, ancilla, L, measure)
    
    qc.h(ancilla)
    qc.measure(ancilla, ca[0])
    return qc

def apply_controlled_cluster_string_order(qc: QuantumCircuit, ancilla, L: int, measure = "S1"):
    # Apply controlled-(X...X) with control 'ancilla'.
    if measure == "S1":
        for i in range(1, L+1):
            qc.cx(ancilla, i)
        
    # Apply controlled-(ZY X...X YZ) with control 'ancilla'.
    elif measure == "SZY":
        qc.cz(ancilla, 1)
        CY(qc, ancilla, 2)
        for i in range(3, L-1):
            qc.cx(ancilla, i)
        CY(qc, ancilla, L-1)
        qc.cz(ancilla, L)
        
        
def ancilla_expectation(counts: dict) -> float:
    """Return <Z_a> = (p0 - p1) from ancilla counts."""
    n0 = counts.get('0', 0)
    n1 = counts.get('1', 0)
    return (n0 - n1) / (n0 + n1)

def indirect_string_order_measurement(L, g, measure: str = "S1"):
    # Create circuit
    qc_state = iMPS_state_circuit(L=L, g=g)
    qc = hadamard_test_string_order(qc_state, L, measure=measure)
    
    # Simulate
    sim = AerSimulator(seed_simulator=1234)
    tqc = transpile(qc, sim, optimization_level=3)
    res = sim.run(tqc, shots=20_000).result()
    
    # Compute <S> = <psi'| Z...Z |psi'> from Z-measurement counts
    counts = res.get_counts()
    expectation_value = ancilla_expectation(counts)
    
    # print(f"⟨{measure}⟩ ≈", expectation_value)
    return expectation_value