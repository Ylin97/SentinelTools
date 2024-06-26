import os
import numpy as np
from scipy.io import savemat
from bandreader import *

# RAND_TYPE = ("Amplitude_VV", "Amplitude_VH")

def run(fpath: str, spath: str, zname: str, ztime: int, size: int):
    """将SAR数据转换为MATLAB矩阵"""

    dirs = [x for x in os.listdir(fpath) if x.endswith('.data')]
    # tmp = dirs[0][24:32]
    dirs.sort(key=lambda x: int(x[24:32]))
    mat_vv, mat_vh = [], []
    for d in dirs:
        data_vv = Band(os.path.join(fpath, d), "Intensity_VV").radar_pixels
        # print(data_vv.shape)
        data_vh = Band(os.path.join(fpath, d), "Intensity_VH").radar_pixels
        # print(data_vh.shape)      
        data_slice_vv = data_vv[0:size, 0:size]
        data_slice_vh = data_vh[0:size, 0:size]

        if data_slice_vv.shape != (size, size) or data_slice_vh.shape != (size, size):
            print("WARN: the size of '{}' is not pair to ({}, {})".format(d.removesuffix(".data"), size, size))
            continue;

        mat_vv.append(data_slice_vv)
        mat_vh.append(data_slice_vh)

    if not os.path.exists(spath):
        os.makedirs(save_path)
    ndarr_vv = np.array(mat_vv, dtype=np.float32)
    print(ndarr_vv.shape)
    np.save(os.path.join(spath, f"{zname}_vv_{size}x{size}_t{ztime}.npy"), ndarr_vv)
    ndarr_vv = ndarr_vv.swapaxes(1, 2).swapaxes(0, 2)
    print(ndarr_vv.shape)
    savemat(os.path.join(spath, f"{zname}_vv_{size}x{size}_t{ztime}.mat"), {'data' : ndarr_vv})

    ndarr_vh = np.array(mat_vh, dtype=np.float32)
    print(ndarr_vh.shape)
    np.save(os.path.join(spath, f"{zname}_vh_{size}x{size}_t{ztime}.npy"), ndarr_vh)
    ndarr_vh = ndarr_vh.swapaxes(1, 2).swapaxes(0, 2)
    print(ndarr_vh.shape)
    savemat(os.path.join(spath, f"{zname}_vh_{size}x{size}_t{ztime}.mat"), {'data' : ndarr_vh})

if __name__ == "__main__":
    file_path = "SanggendalaiLake/Lake1/subset_snap/t1006"
    save_path = "SanggendalaiLake/Lake1/subset_snap/t1006_subset"
    zone_name = "sanggendalailake1"
    size = 500
    zone_time = 1006
    run(file_path, save_path, zone_name, zone_time, size)        
    