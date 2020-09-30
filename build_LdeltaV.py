import pymesh
import numpy as np
import os
from scipy import sparse

np.set_printoptions(precision=4, linewidth=250, suppress=True)

# define parameters
mesh_path = 'data/blendshapes_obj'
ref_mesh_name = 'Louise_Neutral'
mesh_list_path = "data/"
mesh_list_name = 'mesh_name_list.npy'
save_path = "data/"
save_name = "LdV_louise"

# load mesh_list
mesh_list = np.load(os.path.join(mesh_list_path, mesh_list_name)).astype(str)
num_blendshapes = len(mesh_list)
print("num_blendshapes", num_blendshapes)


def compute_deltaV(mesh, ref_mesh):
    dv = mesh.vertices - ref_mesh.vertices
    faces = ref_mesh.faces
    return pymesh.form_mesh(dv, faces)


def build_L_deltaV(mesh_list, path, ref_mesh_name):
    ref_mesh = pymesh.load_mesh(os.path.join(path, ref_mesh_name + ".obj"))
    n_vertices = len(ref_mesh.vertices)
    print("n_vertices:", n_vertices)

    LdVs = []
    for mesh_name in mesh_list:
        # compute dV
        if mesh_name != ref_mesh_name:
            mesh = pymesh.load_mesh(os.path.join(path, mesh_name+".obj"))
            dv_mesh = compute_deltaV(mesh, ref_mesh)

            # compute Laplacians
            assembler = pymesh.Assembler(mesh)
            L = assembler.assemble("laplacian").todense()

            # compute LdV
            LdVs.append(np.dot(L, dv_mesh.vertices))

    return np.array(LdVs)


# get LdV
LdV = build_L_deltaV(mesh_list, mesh_path, ref_mesh_name)

if np.shape(LdV)[0] == num_blendshapes:
    print("[Warning] No neutral pose found!")

# reshape and save
LdV = np.reshape(LdV, (np.shape(LdV)[0], -1))
print("shape LdV", np.shape(LdV))
np.save(os.path.join(save_path, save_name), LdV)