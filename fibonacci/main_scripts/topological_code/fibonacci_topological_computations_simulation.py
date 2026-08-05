# fibonacci/main_scripts/topological_code/fibonacci_topological_computations_simulation.py

# Run from root folder as:
# python -m fibonacci.main_scripts.topological_code.fibonacci_topological_computations_simulation

from fibonacci.models.topological_code import fibonacci_code
from fibonacci.measurements.sampling import sample_circuit
from fibonacci.measurements.distributions import postselect_distribution
from fibonacci.diagnostics.state_inspection import print_fusion_stats_bits
from fibonacci.transpilation.circuit_info import one_qubit_gate_count, two_qubit_gate_count
from fibonacci.transpilation.optimization import transpile_for_backend


from qiskit_ibm_runtime import QiskitRuntimeService

from qiskit_aer import Aer

# --- Gates from Fibbonacci braidings ---

# Approximation to Hadamard gate
hadamard = [
    's1','s1','s1','s1',
    'si2','si2',
    's1','s1',
    'si2','si2',
    's1','s1',
    's2','s2',
    'si1','si1',
    's2','s2','s2','s2',
    's1','s1',
    'si2','si2',
    'si1','si1',
    's2','s2',
    's1','s1'
]

Z_gate = ['s1'] * 5
X_gate = hadamard + Z_gate + hadamard


if __name__ == "__main__":

    # topological_gates_collection = [[], ['s2'], ['s2', 's1'], ['s2', 's1', 's2'], ['s2', 's2'], ['s2', 's2', 's2']]
    # topological_gates_collection = [hadamard, X_gate, Z_gate, X_gate + Z_gate, X_gate + X_gate]
    # topological_gates_collection = [['s2']]
    
    braid_experiments = [
        ("I", []),
        ("s1", ["s1"]),
        ("s2", ["s2"]),
        ("s3", ["s3"]),
        ("s2 s1", ["s2", "s1"]),
        ("s2 s1 s2", ["s2", "s1", "s2"]),
        ("s2^2", ["s2", "s2"]),
        ("s2^3", ["s2", "s2", "s2"]),
        ("Z = s1^5", Z_gate),
        ("H approximation", hadamard),
        ("X = H Z H approximation", X_gate),
    ]

    
    anyon_pairs = 2
    
    backend = Aer.get_backend("aer_simulator")
        
    print("Chosen backend:", backend.name)

    for label, topological_gates in braid_experiments: 

        qc = fibonacci_code(num_pairs=anyon_pairs, topological_gates=topological_gates)

        tqc = transpile_for_backend(qc, backend, optimization_level=3)
        # print("Depth:", tqc.depth())
        # print("2Q gates:", two_qubit_gate_count(tqc))
        # print("1Q gates:", one_qubit_gate_count(tqc))
        P, job_id = sample_circuit(tqc, backend, shots=4000)
        P = postselect_distribution(P, qubit_index=-1, value = 0) # Keep only outcomes where total fusion is trivial (last qubit = 0)
    
        heading = f"Topological gates: {label}"
        print("-" * len(heading))
        print(heading)
        print("-" * len(heading))
        print("Fusion statistics (total fusion -> vacuum):")
        print_fusion_stats_bits(P, numbered=True)
        
        
        print()
        
        
        
