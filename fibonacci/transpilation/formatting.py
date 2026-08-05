def format_stats(stats):
    return (
        f"seed {stats.seed}: "
        f"2q={stats.two_qubit_gates}, "
        f"depth={stats.depth}, "
        f"1q={stats.one_qubit_gates}"
    )


def format_spread(best, worst):
    return (
        f"2q={worst.two_qubit_gates - best.two_qubit_gates}, "
        f"depth={worst.depth - best.depth}, "
        f"1q={worst.one_qubit_gates - best.one_qubit_gates}"
    )


def format_layout(mapping, indent="      "):
    layout = [physical for _, physical in sorted(mapping)]
    lines = [f"{indent}["]

    for i in range(0, len(layout), 6):
        values = ", ".join(str(q) for q in layout[i:i + 6])
        lines.append(f"{indent}    {values},")

    lines.append(f"{indent}]")
    return "\n".join(lines)
