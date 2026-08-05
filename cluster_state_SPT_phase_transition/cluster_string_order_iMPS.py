# cluster_string_order_iMPS.py
# Compute ⟨S1⟩ and ⟨S_ZY⟩ with the iMPS transfer-matrix method

import numpy as np
import matplotlib.pyplot as plt

# Pauli matrices
X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)

# --- Canonical iMPS tensors B^s_{ab} ---
# Physical index s: 0 ≡ "down", 1 ≡ "up"
def B_tensors(g: float):
    a = np.sqrt(abs(g))
    n = np.sqrt(1.0 + abs(g))
    B_down = np.array([[1.0, np.sign(g)*a],
                       [0.0, 0.0]], dtype=complex) / n
    B_up   = np.array([[0.0, 0.0],
                       [a,   1.0]], dtype=complex) / n
    return np.array([B_down, B_up])

# --- Transfer matrices (flattening: rows=(a1,a2), cols=(b1,b2)) ---
def transfer_T(Bs):
    #  T = ∑_s B_s ⊗ B_s*
    #  vec(AXB†) = (A ⊗ B*).vec(X) in our convention
    return sum(np.kron(B, B.conj()) for B in Bs)

def transfer_E(Bs, O):
    # E[O] = ∑_{s,s'} O_{s,s'} B_{s} ⊗ B_{s'}^*
    return sum(
        O[s1, s2] * np.kron(Bs[s1], Bs[s2].conj())
        for s1 in range(2)
        for s2 in range(2)
    )

# --- Fixed points ---
# Right-canonical gauge -> right fixed point is vec(I)
def fixed_points(T):
    R = np.array([1,0,0,1], dtype=complex)   # vec(I)
    w, v = np.linalg.eig(T.T.conj())
    L = v[:, np.argmax(np.abs(w))]           # dominant left eigenvector (≈ eigenvalue 1)
    L /= np.vdot(L, R)                       # normalize so (L|R)=1
    return L, R

# --- Expectation values ---
def S1_expectation(g: float, ell: int = 3) -> float:
    Bs = B_tensors(g)
    T  = transfer_T(Bs)
    EX = transfer_E(Bs, X)
    L, R = fixed_points(T)
    
    # <S1> = (L| E_X^ell |R)
    val = np.vdot(L, np.linalg.matrix_power(EX, ell) @ R)
    return float(np.real_if_close(val))

def SZY_expectation(g: float, ell: int = 5) -> float:
    Bs = B_tensors(g)
    T  = transfer_T(Bs)
    EZ = transfer_E(Bs, Z)
    EY = transfer_E(Bs, Y)
    EX = transfer_E(Bs, X)
    L, R = fixed_points(T)
    
    # <S_ZY> = (L| E_Z E_Y E_X^{ell-4} E_Y E_Z |R)
    val = np.vdot(L, EZ @ EY @ np.linalg.matrix_power(EX, ell-4) @ EY @ EZ @ R)
    return float(np.real_if_close(val))
