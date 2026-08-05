# fibonacci/measurements/sampling.py

from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import Sampler


def sample_circuit(qc, backend, shots=10000, seed=None):

    # ---- Simulation ----
    if isinstance(backend, AerSimulator):
        job_id = None
        run_kwargs = {"shots": shots}
        if seed is not None:
            run_kwargs["seed_simulator"] = seed

        job = backend.run(qc, **run_kwargs)
        result = job.result()
        counts = result.get_counts()

    # ---- IBM hardware ----
    else:
        sampler = Sampler(backend)
        job = sampler.run([qc], shots=shots)
        job_id = job.job_id()
        result = job.result()

        creg_name = qc.cregs[0].name

        counts = getattr(result[0].data, creg_name).get_counts()

    # ---- Convert counts -> probs ----
    total = sum(counts.values())
    if total == 0:
        raise RuntimeError("No counts returned.")

    P = {}
    for bits, c in counts.items():
        bits = bits.replace(" ", "")
        bits = bits[::-1]  # Qiskit little-endian -> logical order
        P[bits] = c / total

    return P, job_id
