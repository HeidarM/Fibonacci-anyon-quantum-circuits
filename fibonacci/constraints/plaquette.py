# fibonacci/constraints/plaquette.py

# Functions to measure plaquette loops <gs| B_p |gs> for testing ground-state preparation

import numpy as np

from qiskit_aer import Aer

from fibonacci.measurements.statevector_tools import overlap_statevector
from fibonacci.measurements.sampling import sample_circuit
from fibonacci.transpilation.optimization import transpile_for_backend
from fibonacci.gates.anyonic_gates import Bp_tau_gate

from circuits.hadamard_test import hadamard_test



def measure_Bp_Exact(qc, plaquette="C"):
    """
        Measure <gs| B_p |gs> and <gs| B^tau_p |gs> for plaquette p using the exact statevector of qc.
    """
    
    Bp_tau = Bp_tau_gate(plaquette=plaquette)

    qcB = qc.copy()
    # |gs> -> B^tau_p |gs>
    qcB.append(Bp_tau, qcB.qubits)
    
    # Compute overlap
    amp = overlap_statevector(qc, qcB)
    
    phi = (1 + np.sqrt(5)) / 2
    B_tau = phi * np.real_if_close(amp) # multiply with phi (quantum dimension) since B_p^tau is unitary version of the projector using ancillas 
    Bp = (1 + phi * B_tau) / (1 + phi**2)
    
    return Bp, B_tau


def measure_Bp_sampling(qc, backend, plaquette="C", shots=10000, seed=None,
                         optimization_level=1):
    """
        Estimate <B_p> and <B_p^tau> using Hadamard-test
    """

    Bp_tau = Bp_tau_gate(plaquette=plaquette)
    qc_test = hadamard_test(qc, Bp_tau, imag=False)
    tqc_test = transpile_for_backend(
        qc_test,
        backend,
        optimization_level=optimization_level,
    )

    probabilities, job_id = sample_circuit(
        tqc_test,
        backend,
        shots=shots,
        seed=seed,
    )
    
    loop_expectation = probabilities.get("0", 0.0) - probabilities.get("1", 0.0)

    phi = (1 + np.sqrt(5)) / 2
    B_tau = phi * loop_expectation
    Bp = (1 + phi * B_tau) / (1 + phi**2)

    return Bp, B_tau
