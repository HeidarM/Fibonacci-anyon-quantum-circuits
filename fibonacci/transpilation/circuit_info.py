from dataclasses import dataclass


@dataclass(frozen=True)
class TranspileStats:
    """Gate counts and depth for one transpiled circuit."""

    seed: int
    two_qubit_gates: int
    depth: int
    one_qubit_gates: int

    @property
    def score(self):
        # Prefer fewer 2-qubit gates, then lower depth, then fewer 1-qubit gates.
        return (self.two_qubit_gates, self.depth, self.one_qubit_gates)


@dataclass(frozen=True)
class TranspiledCircuit:
    """A transpiled circuit with its qubit mapping and stats."""

    circuit: object
    mapping: list
    stats: TranspileStats


@dataclass(frozen=True)
class TranspileResult:
    """Best and worst circuits found by trying many seeds."""

    best: TranspiledCircuit
    worst: TranspiledCircuit
    seeds_tried: int


def logical_to_physical_mapping(qc, tqc):
    """Get the initial logical-to-physical qubit mapping."""

    initial_layout = tqc.layout.initial_layout
    virtual_to_physical = initial_layout.get_virtual_bits()

    mapping = []
    for logical, qubit in enumerate(qc.qubits):
        if qubit in virtual_to_physical:
            mapping.append((logical, virtual_to_physical[qubit]))

    return mapping


def final_logical_to_physical_mapping(qc, tqc):
    """Get the final logical-to-physical mapping when available."""

    try:
        final_layout = tqc.layout.final_index_layout(filter_ancillas=True)
    except Exception:
        return logical_to_physical_mapping(qc, tqc)

    return [
        (logical, final_layout[logical])
        for logical in range(min(qc.num_qubits, len(final_layout)))
    ]


def two_qubit_gate_count(qc):
    total = 0
    for item in qc.data:
        operation = item.operation if hasattr(item, "operation") else item[0]
        if operation.num_qubits == 2:
            total += 1
    return total


def one_qubit_gate_count(qc):
    total = 0
    for item in qc.data:
        operation = item.operation if hasattr(item, "operation") else item[0]
        if operation.num_qubits == 1:
            total += 1
    return total


def circuit_stats(qc, seed):
    """Get the stats used to compare one seed against another."""

    return TranspileStats(
        seed=seed,
        two_qubit_gates=two_qubit_gate_count(qc),
        depth=qc.depth(),
        one_qubit_gates=one_qubit_gate_count(qc),
    )
