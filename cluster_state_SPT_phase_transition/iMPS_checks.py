# iMPS_checks.py

import numpy as np
from cluster_string_order_iMPS import B_tensors

def vec(X):
    # vec([[a,b],[c,d]]) = [a, c, b, d].
    return X.reshape((-1, 1), order="F")

# define the transfer map
def T_map(g, X):
    return sum(B @ X @ B.conj().T for B in B_tensors(g))

def Td_map(g, X):
    return sum(B.conj().T @ X @ B for B in B_tensors(g))

# define the transfer superoperator
def T_vec(g):
    return sum(np.kron(B, B.conj()) for B in B_tensors(g))

def Td_vec(g):
    return sum(np.kron(B.T,B.conj().T) for B in B_tensors(g))

def spectral_radius(T):
    vals, vecs = np.linalg.eig(T)
    rad = np.max(np.abs(vals))
    return rad, vals, vecs



g = 1.2
tol = 1e-12  # numerical tolerance for "zero"

print("\n\n--- Canonical form / transfer operator checks ---\n")

# Stack B tensors for convenience
B = B_tensors(g)                    # shape (phys, D, D)          
D = B.shape[1]

# Right fixed point: sum_s B_s B_s^\dagger
R = sum(Bs @ Bs.conj().T for Bs in B)

print("Right-canonical iMPS test:")
print(f"sum_s B_s B_s† =\n {np.real_if_close(R)}\n")

# Isometry W_{(s,b), a} = B^s_{a,b}
W = B.transpose(0, 2, 1).reshape(2 * 2, 2)

print("--- Isometry check on W ---")
WtW = W.conj().T @ W      # I 
WWt = W @ W.conj().T      # projector

print("W† W =\n", np.real_if_close(WtW))
print()
print("W W† =\n", np.real_if_close(WWt))
print()

# Transfer superoperators
T = T_vec(g)
Td = Td_vec(g)

rad, eigvals, eigenvecs = spectral_radius(T)
rad_d, eigvals_d, eigenvecs_d = spectral_radius(Td)

print("--- Transfer matrix spectra ---")
print("Spectral radius of T:   ", rad)
print("Spectral radius of Td:  ", rad_d)


print("\n--- vec(X) check: vec(AXB†) = (A ⊗ B*).vec(X) ---")
X = np.array([[1., 2.],
              [3., 4.]], dtype=complex)

print("X =\n", X)
print("\nvec(X) =\n", vec(X))

T_map_result = T_map(g, X)
print("\n\n vec(∑_s B_s X B_s†) =\n", np.real_if_close(vec(T_map_result)))

Tv_vecX = T @ vec(X)
print("\n(∑_s B_s ⊗ B_s*) @ vec(X) =\n", np.real_if_close(Tv_vecX))