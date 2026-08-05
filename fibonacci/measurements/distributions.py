# fibonacci/measurements/distributions.py

from qiskit.quantum_info import Statevector


def postselect_distribution(P, qubit_index, value):
    """
    Post-select a probability distribution P on qubit_index = value.

    Args:
        P: Dict[str, float]  (already normalized distribution)
        qubit_index: int     (index in logical bitstring)
        value: int (0 or 1)

    Returns:
        Dict[str, float]: renormalized distribution
    """

    if value not in (0, 1):
        raise ValueError("value must be 0 or 1")

    filtered = {}
    total = 0.0

    for bits, p in P.items():
        if int(bits[qubit_index]) == value:
            filtered[bits] = p
            total += p

    if total == 0:
        raise RuntimeError("No probability mass matched condition")

    # Renormalize
    for bits in filtered:
        filtered[bits] /= total

    return filtered


def get_bit(bitstring: str, q: int) -> str:
    """
    Return measured bit of qubit q from Qiskit bitstring.
    Assumes standard little-endian ordering.
    """
    return bitstring[-1 - q]


def exact_distribution(qc):
    """
        Computes the exact probability distribution of all qubits in qc from the statevector.
    """
    
    psi = Statevector.from_instruction(qc)
    n = qc.num_qubits

    probs = {}

    for i, amp in enumerate(psi.data):
        p = abs(amp)**2
        if p < 1e-14:
            continue

        bitstring = format(i, f"0{n}b")
        probs[bitstring] = p

    return probs
