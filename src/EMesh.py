import numpy as np

from src.mesh import triangulate_vertices
from src.mesh import build_Laplacian


class EMesh:
    """
    Construct a class to compute E_Mesh as in formula 11 using a function to pass directly the personalized blendshapes
    in delta space delta_p (dp)

    k:= num_of_blendshapes
    f:= num_frames
    m:= num_markers
    n:= num_features

    """
    def __init__(self, delta_gk):
        self.delta_gk = delta_gk
        self.K = np.shape(self.delta_gk)[0]
        self.M = np.shape(self.delta_gk)[1]

        self.L = []
        for k in range(self.K):
            mesh = triangulate_vertices(delta_gk[k])
            self.L.append(build_Laplacian(mesh, self.M))
        self.L = np.array(self.L)

    def _emesh(self, dp):
        """
        Compute E_Mesh as in formula 11

        :param dp: delta p (k, n)
        :return: e_mesh
        """
        # reshape dp in case it comes as a 1D array
        if len(np.shape(dp)) < 2:
            dp = np.reshape(dp, (self.K, self.M * 3))

        e_list = []
        for k in range(self.K):
            e = np.linalg.norm(self.L[k].dot(np.reshape(dp[k], (-1, 3)) - self.delta_gk[k]), axis=1)**2
            e_list.append(e)

        return np.sum(e_list) / self.M

    def get_eMesh(self):
        """
        return the function emesh
        :return:
        """
        return self._emesh

    def get_dEmesh(self):
        """
        Compute the derivative of E_Mesh (formula 11) at delta_p as to minimize delta_p -> E_mesh' = 0
        equation: (2/M) * sum_i(L^{m, i}_k) * delta_p^m_k - (2/M) * sum_i(L^{m, i}_k) * delta_g^m_k]
        with L^i the Laplacian coefficients

        It splits the equation in a diagonal matrix A and a vector b as to solve the equation Ax = b, with x = delta_p
        Since the equation are separable in xyz, the function splits the data and returns a system of equation for each
        dimension, resulting in 3*(kMxknM) instead of one (3kMx3kM) -> section 4.6 of the paper

        M:= num_markers = self.N / 3
        A*:= (kM x kM) diag matrix with coef = (2/M) * s sum_i(L^{m, i}_k)
        b*:= (kM,) vector with value = (2/M) * sum_i(L^{m, i}_k) * delta_g^m_k

        :return: AX, AY, AZ, bX, bY, bZ
        :return:
        """

        # test if delta_gk is separable into 3
        if len(np.shape(self.delta_gk)) < 3:
            if np.shape(self.delta_gk)[1] % 3 != 0:
                raise ValueError("Number of features delta_gk ({}) is not a multiple of 3 (xyz)".format(np.shape(self.delta_gk)))
            else:
                self.delta_gk = self.delta_gk.reshape(self.K, self.M, 3)
                print("[EMesh] Warning! self.delta_gk has been reshaped to: {}".format(np.shape(self.delta_gk)))

        # split delta_gk
        dgkX = self.delta_gk[:, :, 0]
        dgkY = self.delta_gk[:, :, 1]
        dgkZ = self.delta_gk[:, :, 2]

        # declare variables
        A = np.zeros((self.K, self.M))  # get reshaped afterward into (kMxkM)
        bX = np.zeros((self.K, self.M))  # get reshaped afterward into (kM,)
        bY = np.zeros((self.K, self.M))  # get reshaped afterward into (kM,)
        bZ = np.zeros((self.K, self.M))  # get reshaped afterward into (kM,)

        # build A (kM x kM) diagonal matrix and b(kM) vector
        for k in range(self.K):
            # build coef.: sum_m'(L^{m, m'}_k)
            sum_lapl = np.sum(np.power(self.L[k].todense(), 2), axis=0)

            # build A coef. as sum_m'(L^{m, m'}_k)
            A[k] = sum_lapl

            # build b coef. as sum_m'(L^{m, m'}_k) * g^m_k
            bX[k] = np.multiply(sum_lapl, np.expand_dims(dgkX[k], axis=1).T)
            bY[k] = np.multiply(sum_lapl, np.expand_dims(dgkY[k], axis=1).T)
            bZ[k] = np.multiply(sum_lapl, np.expand_dims(dgkZ[k], axis=1).T)

        # reshape matrix A into diagonal of (kMxkM) and b into vector of (kM,)
        A = (2/self.M) * np.diag(A.flatten())
        bX = (2/self.M) * bX.flatten()
        bY = (2/self.M) * bY.flatten()
        bZ = (2/self.M) * bZ.flatten()

        # A = Ax = Ay = Az
        return A, A, A, bX, bY, bZ


if __name__ == '__main__':
    """
    test e_mesh functions
    
    1st part build a random array
    2nd part triangulate a set of markers from Vicon recording into a mesh
    
    run: python -m src.EMesh
    """

    np.random.seed(1)
    np.set_printoptions(precision=4, linewidth=250, suppress=True)
    print("--------- test toy example ----------")
    # declare variables
    n_k = 1  # num_blendshapes
    n_m = 5  # num markers
    n_n = n_m * 3  # num_features (num_markers * 3)
    dgk = np.random.rand(n_k, n_m, 3)
    dp = np.random.rand(n_k, n_n)
    print("dgk")
    print(dgk)
    print("dp")
    print(dp)

    # create EMesh object
    e_mesh = EMesh(dgk)

    # control compute e_mesh
    print("compute control e_mesh")
    emesh_list = []
    for k in range(n_k):
        mesh = triangulate_vertices(dgk[k])
        L = build_Laplacian(mesh, n_m)
        dv = np.reshape(dp[k], (-1, 3)) - dgk[k]
        l_op = L.dot(dv)
        norm = np.linalg.norm(l_op, axis=1)**2
        emesh_list.append(norm)

    emesh_ctrl = np.sum(emesh_list) / n_m
    print("emesh_ctrl =", emesh_ctrl)

    # compute e_mesh
    print("compute e_mesh")
    e_mesh_fn = e_mesh.get_eMesh()
    emesh = e_mesh_fn(dp)
    print("emesh =", emesh)

    assert emesh == emesh_ctrl
    print("emesh values are equal")
    print()

    print("----- Minimization ------")
    import time as time
    print("try optimizer")
    from scipy import optimize
    start = time.time()
    opt = optimize.minimize(e_mesh_fn, np.reshape(dgk, (n_k, n_n)), method="BFGS")  # todo: confirm that delta_p_k = delta_g_k when solving only for EMesh
    # print(opt)
    print("solved in:", time.time() - start)
    print("shape opt.x", np.shape(opt.x))
    print(opt.x)

    from scipy.linalg import solve
    print("try solver")
    AX, AY, AZ, bX, bY, bZ = e_mesh.get_dEmesh()
    start = time.time()
    solX = solve(AX, bX)
    solY = solve(AY, bY)
    solZ = solve(AZ, bZ)
    sol = np.vstack((solX, solY, solZ)).reshape(-1, order='F')
    print("solved in:", time.time() - start)
    print("shape sol", np.shape(sol))
    print(sol)
    print("dgk")
    print(np.reshape(dgk, (n_k, n_n)))

    # test if values matches
    np.testing.assert_array_equal(np.around(opt.x, 5), np.round(sol, 5))
    print("Reached same value!")
