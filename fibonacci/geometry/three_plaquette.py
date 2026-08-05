# fibonacci/geometry/three_plaquette.py


# Define qubit indices for plaquettes and edges
# # Plaquette edges - OLD VERSION
# plaqA = [3, 5, 9, 11, 8, 4]
# plaqB = [7, 10, 13, 14, 12, 9]
# plaqC = [0, 2, 6, 7, 5, 1]

# Plaquette edges starting with bottom edge and going clockwise
plaqA = [11, 8 , 4, 3, 5 ,  9]
plaqC = [7 , 5 , 1, 0, 2 ,  6]
plaqB = [14, 12, 9, 7, 10, 13]

# Plaquette vertices starting with left vertex and going clockwise
PlaqA_vertices = [5, 2, 3, 6, 9, 8]
PlaqC_vertices = [3, 0, 1, 4, 7, 6]
PlaqB_vertices = [9, 6, 7, 10, 12, 11]

# Edges between plaquettes
ABedge = 9
ACedge = 5
BCedge = 7
# Ancilla qubits - center of each plaquette
cA = 15
cB = 16
cC = 17

# Ancillas for excitations
e1 = 15
e2 = 16

# Ancillas for excitations
e3 = 17
e4 = 18

# Ancillas for excitations
e5 = 19
e6 = 20

vertices = [
    # v=0
    [None, 1, 0],
    # v=1
    [0, 2, None],
    # v=2
    [None, 4, 3],
    # v=3
    [3, 5, 1],
    # v=4
    [2, 6, None],
    # v=5
    [None, 8, 4],
    # v=6
    [5, 9, 7],
    # v=7
    [7, 10, 6],
    # v=8
    [8, None, 11],
    # v=9
    [11, 12, 9],
    # v=10
    [10, 13, None],
    # v=11
    [12, None, 14],
    # v=12
    [14, None, 13],
]



# Ribbon paths
# [v = vertex, x = src_edge, y = dst_edge, ribbon_twist]
Ribbon_path_PlaqA = [[5, 1, 2], [2, 1, 2], [3, 0, 1], [6,  0, 1], [9,  2, 0]]
Ribbon_path_PlaqC = [[3, 1, 2], [0, 1, 2], [1, 0, 1], [4,  0, 1], [7,  2, 0]]
Ribbon_path_PlaqB = [[9, 1, 2], [6, 1, 2], [7, 0, 1], [10, 0, 1], [12, 2, 0]]

Ribbon_path_PlaqBA= [[9, 1, 0, 1], [8, 2, 0], [5, 1, 2], [2, 1, 2], [3, 0, 1], [6, 0, 2, 1], [7, 0, 1], [10, 0, 1], [12, 2, 0]]
Ribbon_path_PlaqBC = [[9, 1, 2], [6, 1, 0, 1], [3, 1, 2], [0, 1, 2], [1, 0, 1], [4, 0, 1], [7, 2, 1, 1], [10, 0, 1], [12, 2, 0]]
Ribbon_path_PlaqABC = [[9, 1, 0, 1], [8, 2, 0], [5, 1, 2], [2, 1, 2], [3, 0, 2, 1], [0, 1, 2], [1, 0, 1], [4, 0, 1], [7, 2, 1, 1], [10, 0, 1], [12, 2, 0]]
