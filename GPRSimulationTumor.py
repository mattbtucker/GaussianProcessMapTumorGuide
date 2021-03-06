import numpy as np
import cv2
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from sklearn.neighbors import KDTree
import time
from matplotlib import cm
from numpy.linalg import inv
import glob
import os
import shutil

class ErrorSim():

    def __init__(self):

        self.path_type = 12.5
        self.path_index = 1
        self.Npts_ID = 31.0
        self.ratio_p2u = 10
        self.Npts_Interp = self.Npts_ID * self.ratio_p2u
        self.path_save = str(self.path_type) + '_' + str(self.path_index) + '/'

    def ShowMap(self):

        # data_grid = np.load("pts_ID_grid.npy")
        data_org = np.load("data_intensity_tumor_2d.npy")

        img_map = np.zeros((29, 29))
        idx_map_gt = np.linspace(0, len(img_map.ravel()) - 1, len(img_map.ravel()))
        Data_index = np.unravel_index(idx_map_gt.astype(np.int64), img_map.shape)
        Data_use = np.zeros((len(Data_index[0]), 3))
        # print(Data_index[0])
        Data_use[:, 0] = Data_index[0]
        Data_use[:, 1] = Data_index[1]
        Data_use[:, 2] = data_org.ravel()

        np.save("Data_Use.npy", Data_use)

        plt.scatter(Data_use[:, 0], Data_use[:, 1], c = Data_use[:, 2])
        plt.axis('equal')
        plt.show()

        # print(Data_index)
        # print(Data_index)
        # input()
        # print(data_grid)
        # print(data_grid.shape)

    def GridTform(self, Ratio, Npts, delta_x = 5, delta_y = 5):

        x1 = 0 * Ratio
        x2 = np.int(Npts) * Ratio
        y1 = 0 * Ratio
        y2 = np.int(Npts) * Ratio

        rx, ry = np.arange(x1 + delta_x * Ratio, x2 + delta_x *Ratio, Ratio), np.arange(y1 + delta_y * Ratio, y2 + delta_y * Ratio, Ratio)
        gx, gy = np.meshgrid(rx, ry)
        X_2D = np.c_[gx.ravel(), gy.ravel()]

        # Identify the points in the ROI
        idx_use = np.where( (X_2D[:, 0] > x1) & ( X_2D[:, 0] < x2 ) & ( X_2D[:, 1] > y1 ) & ( X_2D[:, 1] < y2 ) )

        X_2D_x = X_2D[:, 0]
        X_2D_y = X_2D[:, 1]
        X_2D_x = X_2D[idx_use[0], 0]
        X_2D_y = X_2D[idx_use[0], 1]

        return X_2D_x, X_2D_y

    def Threshold_Classifier(self):

        # Define the folders
        folder_tumor = '/Users/matttucker/Desktop/GaussianData/Tumor'
        folder_nontumor = '/Users/matttucker/Desktop/GaussianData/NonTumor'

        # The average of the tumor data
        folderinfor_tumor = glob.glob(folder_tumor + "*.csv")
        Nfiles = len(folderinfor_tumor)
        Data_tumor_list = []
        for i in range(20):
            # print("check non tumor", i)
            data_current_spec = np.asarray(np.genfromtxt(folder_tumor + str(i) + '.csv', delimiter=','))
            data_wavelegnth = data_current_spec[:, 0]
            data_current_intenstiy = data_current_spec[:, 1]
            # Find index between 425 and 750
            idx_use = np.where((data_wavelegnth > 425) & (data_wavelegnth < 750))
            data_intensity_use = data_current_intenstiy[idx_use]
            f_vec = np.max(data_intensity_use)
            # print("f_vec = ", f_vec)
            Data_tumor_list.append(f_vec)

        # The average of the non-tumor data
        folderinfor_nontumor = glob.glob(folder_nontumor + "*.csv")
        Nfiles = len(folderinfor_nontumor)
        Data_nontumor_list = []
        for i in range(20):
            # print("check tumor", i)
            data_current_spec = np.asarray(np.genfromtxt(folder_nontumor + str(i) + '_spec.csv', delimiter=','))
            data_wavelegnth = data_current_spec[:, 0]
            data_current_intenstiy = data_current_spec[:, 1]
            # Find index between 425 and 750
            idx_use = np.where((data_wavelegnth > 425) & (data_wavelegnth < 750))
            data_intensity_use = data_current_intenstiy[idx_use]
            f_vec = np.max(data_intensity_use)
            # print("f_vec = ", f_vec)
            Data_nontumor_list.append(f_vec)

        # Define the threshold
        Threshold_use = (np.mean(Data_tumor_list) + np.mean(Data_nontumor_list)) / 2
        # print("The data_tumor list is ", Data_tumor_list)
        # print("The data_nontumor list is ", Data_nontumor_list)
        # print("The mean of tumor is ", np.mean(Data_tumor_list))
        # print("The mean of nontumor is ", np.mean(Data_nontumor_list))
        # print("The Threshold between tumor and nontumor is ", Threshold_use)

        return Threshold_use

    def ReadExpData_ID(self, Npts = 26):

        # Get the grid
        x_mesh_use, y_mesh_use = GetImgGrid(xlist = [0, Npts - 1, 0, Npts - 1], Nptsperline = Npts)
        img_map = np.zeros((Npts, Npts))

        # Define the average threshold based on the tumor and non-tumor data
        path_spec = self.path_main + 'File_Spectrum/'
        folderinfor_spec = glob.glob(self.path_main + r'File_Spectrum\\' + "*.csv")
        Nfiles = len(folderinfor_spec)
        print("Nfiles = ", Nfiles)
        # input("Check the number of files")
        Data_Res = np.zeros((Nfiles, 3))

        for i in range(Nfiles):

            # print(i)
            data_current_spec = np.asarray(np.genfromtxt(path_spec + str(i) + '_spec.csv', delimiter=','))
            data_wavelegnth = data_current_spec[:, 0]
            data_current_intenstiy = data_current_spec[:, 1]

            # Find index between 425 and 750
            idx_use = np.where((data_wavelegnth > 425) & (data_wavelegnth < 750))
            data_intensity_use = data_current_intenstiy[idx_use]
            f_vec = np.max(data_intensity_use)
            img_map[np.int( y_mesh_use[i] ), np.int( x_mesh_use[i] )] = f_vec
            Data_Res[i, 0] = x_mesh_use[i]
            Data_Res[i, 1] = y_mesh_use[i]
            Data_Res[i, 2] = f_vec

        # Save the Map and Data ID
        # np.save("Data_Img_ID.npy", img_map)
        # np.save("Data_ID.npy", Data_Res)

        return Data_Res, img_map

    def Simulate_Error(self):

        '''
        Image Coordiante Problems
        1. In the same coordinate -- they should be similar
        2. problem 1: the intensity is not matching based on the griddata
        3. problem 2: the idea of the problems
        solution:
        1. First, we need to define the global coordinate
        2. Second, align all the models in the
        # Save the files in the folder
        1. Save the dataID and dataImg Files
        2. Save the threshold file and all the intensity value files
        3. Save the interpolated image files
        '''

        # Check the save folder
        # flag_reset = np.int(input("Reset the folder?"))
        flag_reset = 1
        if os.path.isdir(self.path_save) == False:
            os.mkdir(self.path_save)
        elif flag_reset == 1:
            shutil.rmtree(self.path_save)
            os.mkdir(self.path_save)

        # Define the basic parameters
        Npts_interp = self.Npts_Interp              # 300 points for interpolation
        Npts_ID = self.Npts_ID                      # The grid is 26 x 26
        Ratio = Npts_interp / Npts_ID               # The ratio of the mm to pixel coordinates -- 10 pixel / mm
        x_offset = [0, 2]                           # Units in mm
        y_offset = [0, 2]                           # Units in mm

        # Read the spec files from the Dataset
        Data_ID, Img_ID = self.ReadExpData_ID(Npts = np.int(Npts_ID))

        # Save the files
        np.save(self.path_save + "Data_ID.npy", Data_ID)
        np.save(self.path_save + "Data_Img_ID.npy", Img_ID)
        Data_ID = np.load(self.path_save + "Data_ID.npy")
        Img_ID = np.load(self.path_save + "Data_Img_ID.npy")

        # Define the threshold
        thres = self.Threshold_Classifier()
        np.save(self.path_save + "Data_Threshold.npy", thres)

        # Show the image ID -- align them in the same coordinate system
        # plt.subplot(211)
        # plt.imshow(Img_ID)
        # plt.gca().invert_yaxis()
        # plt.subplot(212)
        # plt.scatter(Data_ID[:, 0], Data_ID[:, 1], c = Data_ID[:, 2])
        # plt.axis('equal')
        # plt.show()

        idx_tumor = np.where((Data_ID[:, 2] < thres))
        idx_nontumor = np.where((Data_ID[:, 2] > thres))

        # Show the tumor and nontumor region
        Data_ID_Tumor = Data_ID[idx_tumor, :][0]
        Data_ID_nontumor = Data_ID[idx_nontumor, :][0]

        # Resample the data
        Data_ID_coord = Data_ID[:, 0:2]
        Data_ID_intensity = Data_ID[:, 2]

        # Get the interpolation point sets
        x_min = np.min(Data_ID_coord[:, 0])
        x_max = np.max(Data_ID_coord[:, 0])
        y_min = np.min(Data_ID_coord[:, 1])
        y_max = np.max(Data_ID_coord[:, 1])
        x_list = np.linspace(x_min, x_max, np.int(Npts_interp))
        y_list = np.linspace(y_min, y_max, np.int(Npts_interp))

        print("Npts_interp = ", Npts_interp)

        x_grid, y_grid = np.meshgrid(x_list, y_list)
        # Save the interpolation
        img_map = griddata(Data_ID_coord, Data_ID_intensity, (x_grid, y_grid), method = 'linear')

        np.save(self.path_save + "img_map.npy", img_map)
        # img_map = np.load("img_map.npy")
        idx_map_gt = np.linspace(0, len(img_map.ravel()) - 1, len(img_map.ravel()))

        # Generate an image map from the grid
        xlist = [0, Npts_interp - 1, 0, Npts_interp - 1]
        Nptsperline = Npts_interp
        x_mesh_use, y_mesh_use = GetImgGrid(xlist, Nptsperline)
        Data_index_list = np.zeros((len(x_mesh_use), 2))
        Data_index_list[:, 0] = x_mesh_use
        Data_index_list[:, 1] = y_mesh_use

        # print("The threshold is ", thres)
        # print("Shape of data_imap = ", img_map.shape)
        # print("Shape of Data_ID = ", Data_ID.shape)
        # print("Shape of Data_index_list = ", Data_index_list.shape)
        # input("Check the index")

        # Show the tumor and nontumor region
        # plt.subplot(221)
        # plt.scatter(Data_ID[:, 0], Data_ID[:, 1], c = Data_ID[:, 2])
        # plt.axis('equal')
        # plt.subplot(222)
        # plt.scatter(Data_ID_Tumor[:, 0], Data_ID_Tumor[:, 1], c = Data_ID_Tumor[:, 2])
        # plt.axis('equal')
        # plt.subplot(223)
        # plt.scatter(Data_ID_nontumor[:, 0], Data_ID_nontumor[:, 1], c = Data_ID_nontumor[:, 2])
        # plt.axis('equal')
        # plt.subplot(224)
        # plt.imshow(img_map)
        # plt.gca().invert_yaxis()
        # plt.axis('equal')
        # plt.show()

        # Reset the folder
        # Folder_save_img_spec = 'Data_SimErr/'
        # # flag_reset = np.int(input("Reset the folder?"))
        # flag_reset = 1
        # if os.path.isdir(Folder_save_img_spec) == False:
        #     os.mkdir(Folder_save_img_spec)
        # elif flag_reset == 1:
        #     shutil.rmtree(Folder_save_img_spec)
        #     os.mkdir(Folder_save_img_spec)

        # Test different transformation
        # input("Begin the moving transformation")
        count = 0
        # Define the new sampled data
        Data_ID_Sample = np.zeros((len(Data_ID), 3))

        for i in range(0, 20):
            for j in range(0, 20):

                # print(count)
                delta_x = i / 10.0  # mm
                delta_y = j / 10.0  # mm

                # Find the new coordinate system based on the offset
                Data_ID_Sample[:, 0] = (Data_ID[:, 0] + delta_x) * Ratio
                Data_ID_Sample[:, 1] = (Data_ID[:, 1] + delta_y) * Ratio
                Data_ID_Sample[:, 2] = Data_ID[:, 2]

                # Apply the transformation
                theta =  0.0 # np.pi / 4.0
                Mtform = np.asarray([ [np.cos(theta), np.sin(theta)],
                                     [-np.sin(theta), np.cos(theta)]])
                Data_ID_tform = Data_ID_Sample
                Data_ID_tform[:, 0:2] = np.matmul( Data_ID_Sample[:, 0:2], Mtform )

                # The Data Map for usage
                Data_Use = self.Train_2d_KNN(img_map, Data_index_list, Data_ID_tform, Npts = Npts_interp)

                # Find the intensity greater than the threshold
                threshold = thres
                idx_tumor = np.where((Data_Use[:, 2] < threshold))
                idx_nontumor = np.where((Data_Use[:, 2] > threshold))
                Data_tumor = Data_Use[idx_tumor[0], :]
                Data_nontumor = Data_Use[idx_nontumor[0], :]
                count += 1

                # plt.subplot(131)
                # plt.scatter(Data_Use[:, 0], Data_Use[:, 1], c = Data_Use[:, 2])
                # plt.axis('equal')
                # plt.subplot(132)
                # plt.scatter(Data_ID[:, 0], Data_ID[:, 1], c = Data_ID[:, 2])
                # plt.axis('equal')
                # plt.subplot(133)
                # plt.imshow(img_map)
                # plt.gca().invert_yaxis()
                # plt.axis('equal')
                # plt.show()

                # Save the data
                np.save(self.path_save + "Data_tumor_" + str(count) + ".npy", Data_tumor)
                np.save(self.path_save + "Data_nontumor_" + str(count) + ".npy", Data_nontumor)

    def posterior_predictive(self, X_s, X_train, Y_train, l = 1.0, sigma_f = 1.0, sigma_y = 1e-8):

        '''
        Computes the suffifient statistics of the GP posterior predictive distribution
        from m training data X_train and Y_train and n new inputs X_s.
        Args:
            X_s: New input locations (n x d).
            X_train: Training locations (m x d).
            Y_train: Training targets (m x 1).
            l: Kernel length parameter.
            sigma_f: Kernel vertical variation parameter.
            sigma_y: Noise parameter.
        Returns:
            Posterior mean vector (n x d) and covariance matrix (n x n).
        '''
        K = kernel(X_train, X_train, l, sigma_f) + sigma_y ** 2 * np.eye(len(X_train))
        K_s = kernel(X_train, X_s, l, sigma_f)
        K_ss = kernel(X_s, X_s, l, sigma_f) + 1e-8 * np.eye(len(X_s))
        K_inv = inv(K)

        # Equation (4)
        mu_s = K_s.T.dot(K_inv).dot(Y_train)

        # Equation (5)
        cov_s = K_ss - K_s.T.dot(K_inv).dot(K_s)

        return mu_s, cov_s

    def Train_2d_GP(self):

        # Gaussian Process Regression in 2D Map

        # Define an initial setting
        noise_2D = 0.1

        # Generate the Trainining Data
        Data_Train = np.load("GP_DATA/Data_Test_1.npy")
        X_2D_train = Data_Train[:, 0:2]
        Y_2D_train = Data_Train[:, 2]

        # Get the predictive model
        # The Grid
        rx, ry = np.arange(0, 26, 1), np.arange(0, 26, 1)
        gx, gy = np.meshgrid(rx, rx)
        X_2D = np.c_[gx.ravel(), gy.ravel()]

        # Apply Transformation
        X_2D_x, X_2D_y = self.GridTform()
        X_2D_use = np.zeros((len(X_2D_x), 2))
        X_2D_use[:, 0] = X_2D_x
        X_2D_use[:, 1] = X_2D_y
        print(X_2D_use.shape)

        plt.scatter(X_2D_use[:, 0], X_2D_use[:, 1], c = 'r')
        plt.show()

        # The Model
        t1 = time.time()
        mu_s, cov_s = self.posterior_predictive(X_2D_use, X_2D_train, Y_2D_train, sigma_y = noise_2D)
        t2 = time.time()
        print("The single GP computational time is ", t2 - t1)

        # (gx, gy, mu_s) -- for the image map
        print(mu_s.shape)
        print(cov_s.shape)

        # Show the figure
        plot_gp_2D(gx, gy, mu_s, cov_s, X_2D_train, Y_2D_train, f'Before parameter optimization: l = {1.00} sigma_f = {1.00}', 1)

    def Train_2d_KNN(self, img_map_gt, Data_index_list, Data_Sample, Npts = 300):

        p_index_KDTREE = KDTree(Data_index_list)
        dist_nearest, ind_nearest = p_index_KDTREE.query(Data_Sample[:, 0:2], k = 4)

        for idx, item in enumerate(ind_nearest):
            coordinates = Data_index_list[item, :]
            pts_intensity = []
            for i in range(len(coordinates)):
                pts_intensity.append(img_map_gt[ np.int(coordinates[i][1]), np.int(coordinates[i][0]) ] )
            pts_intensity_mean = np.mean(pts_intensity)
            Data_Sample[idx, 2] = pts_intensity_mean

        Data_use = np.zeros((len(Data_Sample[:, 1]), 3))
        Data_use[:,0] = Data_Sample[:, 0]
        Data_use[:,1] = Data_Sample[:, 1]
        Data_use[:,2] = Data_Sample[:, 2]

        return Data_use

def plot_gp_2D(gx, gy, mu, cov_s, X_train, Y_train, title, i):

    ax_1 = plt.gcf().add_subplot(1, 3, 1, projection = '3d')
    ax_2 = plt.gcf().add_subplot(1, 3, 2, projection = '3d')
    ax_3 = plt.gcf().add_subplot(1, 3, 3, projection = '3d')
    ax_1.plot_surface(gx, gy, mu.reshape(gx.shape), cmap = cm.coolwarm, linewidth = 0, alpha = 0.2, antialiased = False)
    ax_2.scatter(X_train[:, 0], X_train[:, 1], Y_train, c = Y_train, cmap = cm.coolwarm)
    # ax_3.plot_surface(gx, gy, cov_s.reshape(gx.shape), cmap = cm.coolwarm, linewidth = 0, alpha = 0.2, antialiased = False)

    ax_1.set_title("The Predicted Function")
    ax_2.set_title("The Training fcuntion")
    # ax_3.set_title("The Covariance function")
    plt.show()

def kernel(X1, X2, l = 1.0, sigma_f = 1.0):
    '''
    Isotropic squared exponential kernel. Computes
    a covariance matrix from points in X1 and X2.
    Args:
        X1: Array of m points (m x d).
        X2: Array of n points (n x d).
    Returns:
        Covariance matrix (m x n).
    '''
    sqdist = np.sum(X1 ** 2, 1).reshape(-1, 1) + np.sum(X2 ** 2, 1) - 2 * np.dot(X1, X2.T)

    return sigma_f ** 2 * np.exp(-0.5 / l ** 2 * sqdist)

def Data_Resample(Data_npy, Npts = 300):

    # The input Data array
    # The number of points

    # Data_npy = np.load("Data_Test_1.npy")
    # Npts = 300

    x_min = np.min(Data_npy[:, 0])
    x_max = np.max(Data_npy[:, 0])

    y_min = np.min(Data_npy[:, 1])
    y_max = np.max(Data_npy[:, 1])

    x_list = np.linspace(x_min, x_max, Npts)
    y_list = np.linspace(y_min, y_max, Npts)

    x_grid, y_grid = np.meshgrid(x_list, y_list)

    img_map = griddata(Data_npy[:, 0:2], Data_npy[:, 2], (x_grid, y_grid), method='linear')

    # np.save("img_map.npy", img_map)

    # print("x_grid = ", x_grid)
    # print("y_grid = ", y_grid)

    # # # Reorder the grid
    # # x1 = xlist[0]
    # # x2 = xlist[1]
    # # y1 = xlist[2]
    # # y2 = xlist[3]
    # # # Nptsperline = 26
    # #
    # # x_list = np.linspace(x1, x2, Nptsperline)
    # # y_list = np.linspace(y1, y2, Nptsperline)
    #
    # [y_mesh, x_mesh] = np.meshgrid(x_list, y_list)
    # x_mesh_path = y_mesh.ravel(order='C')
    # y_mesh_path = x_mesh.ravel(order='C')
    #
    # # print("x_mesh = ", x_mesh)
    # # print("y_mesh = ", y_mesh)
    # # input("")
    # # print("x_mesh_use (before) = ", x_mesh_path.shape)
    # # print("y_mesh_use (before) = ", y_mesh_path.shape)
    # # exit()
    #
    # Nrow = len(x_mesh)
    # # print(Nrow)
    # if (Nrow % 2) != 0:
    #     print("Odd")
    # if (Nrow % 2) == 0:
    #     print("Even")
    #
    # x_mesh_use = []
    # y_mesh_use = []
    # for i in range(Nrow):
    #     if i % 2 != 0:
    #         # print(i)
    #         x_mesh_list = x_mesh[i, :]
    #         y_mesh_list = np.flip(y_mesh[i, :])
    #         # print(x_mesh_list)
    #         # print(y_mesh_list)
    #         # raw_input()
    #     if i % 2 == 0:
    #         # flip
    #         # print(i)
    #         x_mesh_list = np.flip(x_mesh[i, :])
    #         y_mesh_list = y_mesh[i, :]
    #         # print(x_mesh_list)
    #         # print(y_mesh_list)
    #         # raw_input()
    #     x_mesh_use = np.concatenate((x_mesh_use, x_mesh_list), axis = 0)
    #     y_mesh_use = np.concatenate((y_mesh_use, y_mesh_list), axis = 0)
    #
    # print("x_mesh_use = ", x_mesh_use)
    # print("y_mesh_use = ", y_mesh_use)
    # print("x_mesh_use shape = ", x_mesh_use.shape)
    # print("y_mesh_use shape = ", y_mesh_use.shape)
    # exit()



    # print(img_map)
    # plt.imshow(img_map)
    # plt.show()

    a = 1

    return img_map

def GetImgGrid(xlist, Nptsperline):

    x1 = xlist[0]
    x2 = xlist[1]
    y1 = xlist[2]
    y2 = xlist[3]
    # Nptsperline = 26

    x_list = np.linspace(x1, x2, Nptsperline)
    y_list = np.linspace(y1, y2, Nptsperline)

    [y_mesh, x_mesh] = np.meshgrid(x_list, y_list)
    x_mesh_path = y_mesh.ravel(order = 'C')
    y_mesh_path = x_mesh.ravel(order = 'C')

    Nrow = len(x_mesh)
    # print(Nrow)
    if (Nrow % 2) != 0:
        print("Odd")
    if (Nrow % 2) == 0:
        print("Even")

    x_mesh_use = []
    y_mesh_use = []
    for i in range(Nrow):
        if i % 2 != 0:
            x_mesh_list = x_mesh[i, :]
            y_mesh_list = np.flip(y_mesh[i, :])
        if i % 2 == 0:
            x_mesh_list = np.flip(x_mesh[i, :])
            y_mesh_list = y_mesh[i, :]
        x_mesh_use = np.concatenate((x_mesh_use, x_mesh_list), axis = 0)
        y_mesh_use = np.concatenate((y_mesh_use, y_mesh_list), axis = 0)

    return x_mesh_use, y_mesh_use

if __name__ == "__main__":

    test = ErrorSim()
    # test.ShowMap()
    # test.Simulate_Error()

    # The whole function
    list_type = [12.5, 10, 7.5]
    list_NptsID = [31.0, 29.0, 27.0]
    list_index = [1, 2, 3]

    count = 0
    for i in range(3):
        for j in range(3):
            print("i = ", i)
            print("j = ", j)
            print("The current case is ", count)
            test.path_type = list_type[i]
            test.Npts_ID = list_NptsID[i]
            test.path_index = list_index[j]
            test.Npts_Interp = test.Npts_ID * test.ratio_p2u
            test.path_main = 'E:/Data TumorIDCNC/Data_Phantom_050120/Test4_a' + str(test.path_index) + '_' + str(test.path_type) + 'mm/'
            test.path_save = str(test.path_type) + '_' + str(test.path_index) + '/'
            test.ratio_p2u = 10
            test.Simulate_Error()
            count += 1

    # Get the image grid for the image map
    # xlist = [0, 299, 0, 299]
    # Nptsperline = 300
    # x_mesh_use, y_mesh_use = GetImgGrid(xlist, Nptsperline)
    # print("x_mesh_use = ", x_mesh_use[0:350])
    # print("y_mesh_use = ", y_mesh_use[0:350])
    # exit()

    # Generate the ID scanning grid
    # xlist = [0, 2.6, 0, 2.6]
    # Nptsperline = 27
    # x_mesh_use, y_mesh_use = GetImgGrid(xlist, Nptsperline)
    # pts_grid_ID = np.zeros((len(x_mesh_use), 2))
    # pts_grid_ID[:, 0] = x_mesh_use
    # pts_grid_ID[:, 1] = y_mesh_use
    # np.save("pts_grid_ID_27.npy", pts_grid_ID)

    # print("x_mesh_use = ", x_mesh_use)
    # print("y_mesh_use = ", y_mesh_use)
