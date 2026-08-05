# main.py

# Make a 2x2 figure comparing iMPS and quantum-circuit estimates of
# ⟨S1⟩ and ⟨S_ZY⟩ as functions of g.

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

import cluster_string_order_iMPS as imps
import cluster_string_order_quantum_circuit as qc


def get_iMPS_strings(gs, ell_S1=3, ell_SZY=5):
    S1 = [imps.S1_expectation(g, ell=ell_S1) for g in gs]
    SZY = [imps.SZY_expectation(g, ell=ell_SZY) for g in gs]
    return np.array(S1, float), np.array(SZY, float)


def get_quantum_circuit_direct_strings(gs, L):
    S1 = []
    SZY = []

    pbar = tqdm(list(gs), desc="Direct Measurement", unit="g")
                
    for g in pbar:
        val1, _ = qc.direct_string_order_measurement(L=L, g=g, measure="S1")
        S1.append(val1)
    

        val2, _ = qc.direct_string_order_measurement(L=L, g=g, measure="SZY")
        SZY.append(val2)
        
        # Progress bar
        pbar.set_postfix({"g": f"{g:+.2f}", f"⟨S1⟩": f"{val1:+.2f}", f"⟨SZY⟩": f"{val2:+.2f}"})

    return np.array(S1, float), np.array(SZY, float)


def get_quantum_circuit_indirect_strings(gs, L):
    S1 = []
    SZY = []
    
    pbar = tqdm(list(gs), desc="Indirect Measurement", unit="g")
    
    for g in pbar:
        val1 = qc.indirect_string_order_measurement(L=L, g=g, measure="S1")
        S1.append(val1)

        val2 = qc.indirect_string_order_measurement(L=L, g=g, measure="SZY")
        SZY.append(val2)
        
        # Progress bar
        pbar.set_postfix({"g": f"{g:+.2f}", f"⟨S1⟩": f"{val1:+.2f}", f"⟨SZY⟩": f"{val2:+.2f}"})

    return np.array(S1, float), np.array(SZY, float)


def plot_compare(L=4):
    
    gs_imps = np.linspace(-1.0, 1.0, 401)
    gs_qc   = np.linspace(-1.0, 1.0, 20)

    # iMPS 
    S1_imps,  SZY_imps  = get_iMPS_strings(gs_imps, ell_S1=3, ell_SZY=5)

    # Quantum circuit: direct measurement
    S1_dir,   SZY_dir   = get_quantum_circuit_direct_strings(gs_qc, L=L)

    # Quantum circuit: indirect measurement (Hadamard test)
    S1_ind,   SZY_ind   = get_quantum_circuit_indirect_strings(gs_qc, L=L)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # -------------------------------------------------
    # (0,0): <S1>(g), direct measurement
    ax = axes[0, 0]
    ax.plot(gs_imps, S1_imps, label=r"iMPS $(L|E_X^{\ell}|R)$")
    ax.plot(gs_qc,   S1_dir,  "o", label="QC direct")
    ax.set_xlabel(r"$g$")
    ax.set_ylabel(r"$\langle S_1\rangle$")
    ax.set_title(r"$\langle S_1\rangle$ (direct measurement)")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    # (0,1): <S_ZY>(g), direct measurement
    ax = axes[0, 1]
    ax.plot(gs_imps, SZY_imps, label=r"iMPS $(L|E_ZE_YE_X^{\ell-4}E_YE_Z|R)$")
    ax.plot(gs_qc,   SZY_dir,  "o", label="QC direct")
    ax.set_xlabel(r"$g$")
    ax.set_ylabel(r"$\langle S_{ZY}\rangle$")
    ax.set_title(r"$\langle S_{ZY}\rangle$ (direct measurement)")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    # -------------------------------------------------
    # (1,0): <S1>(g), indirect (Hadamard test)
    ax = axes[1, 0]
    ax.plot(gs_imps, S1_imps, label=r"iMPS $(L|E_X^{\ell}|R)$")
    ax.plot(gs_qc,   S1_ind,  "o", label="QC indirect (Hadamard)")
    ax.set_xlabel(r"$g$")
    ax.set_ylabel(r"$\langle S_1\rangle$")
    ax.set_title(r"$\langle S_1\rangle$ (indirect measurement)")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    # (1,1): <S_ZY>(g), indirect (Hadamard test)
    ax = axes[1, 1]
    ax.plot(gs_imps, SZY_imps, label=r"iMPS $(L|E_ZE_YE_X^{\ell-4}E_YE_Z|R)$")
    ax.plot(gs_qc,   SZY_ind,  "o", label="QC indirect (Hadamard)")
    ax.set_xlabel(r"$g$")
    ax.set_ylabel(r"$\langle S_{ZY}\rangle$")
    ax.set_title(r"$\langle S_{ZY}\rangle$ (indirect measurement)")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    # -------------------------------------------------
    fig.suptitle(
        "String order parameters\n"
        "iMPS vs Direct vs indirect quantum circuit approach",
        fontsize=14
    )
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


if __name__ == "__main__":
    plot_compare(L=4)