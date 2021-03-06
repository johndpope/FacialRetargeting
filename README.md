This repository reproduce the paper "Facial Retargeting with Automaticc Range of Motion Alignment" (2017) done by Roger Blanco, Eduard Zell et. al

It supposes that you already have a character mesh with blendshapes and a set of Vicon motion capture (in a .c3d file). 

Pre steps:
1) The first step is to triangulate all your mesh. If your mesh is not triangulate, you can run the script: 01_triangulate_mesh by copy pasting it (within "maya_script" folder) in the script editor of Maya. It will take care of triangulate the mesh and all its blendshapes provided you modify the name of the base mesh and the repository of the blendshape meshes.
2) If not already done, you now need to attached all the blendshape. We recommend to delete your node and apply the provided script "02_create_blendshapes_nodes" which will save a mesh_name_list that will be used to ensure the correct indexation of your blendshapes and the final facial retargeting weights.
3) You now need to built the dictionary of vertices that semantically represent the positions of your markers on the character. You will be require to change the "vtx_list" within the script "03_extract_blendshape_pos_and_obj", which will save the positions of all the sparse markers for each blendshape as well as saving the blendshapes into an .obj file which we be use to compute the Laplacian over the full meshes. 

Facial retargeting:
1) First, compute the actor specific blendshape (delta_p). Run: python build_actor_blendshapes.py
2) Secondly, pre-compute the LdV matrix. Note: this script uses PyMesh which is not yet available for Win10. 
3) run python retarget.py to get your retargeting weights for your sequence
4) run ... to apply the weights to your mesh witin Maya