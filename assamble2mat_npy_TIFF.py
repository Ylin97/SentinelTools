import os
import numpy as np
from PIL import Image
from scipy.io import savemat
from bandplot import *

def test():
    im = Image.open('data/s1a-iw-grd-vh-20210106t100617-20210106t100642-036016-043851-002.tif')
    data = np.array(im)

    # plt.imshow(data, cmap='gray', vmin=data.min(), vmax=data.max())
    # plt.show()
    fig = BandFigure(data, "Amplitude_VH")
    fig.plotall()
    fig.show()


def main(file_path: str, zonename: str, size: int, save_path :str = None):
    files = [f for f in os.listdir(file_path) if f.endswith('.tif')]
    # print(files[0][14:22])
    files.sort(key=lambda x: int(x[14:22]))

    # min_dim = 1000000
    # for file in files:
    #     data = np.array(Image.open(os.path.join(file_path, file)))
    #     if data.shape[0] < min_dim:
    #         min_dim = data.shape[0]
    #     elif data.shape[1] < min_dim:
    #         min_dim = data.shape[1]

    imgs_vv = []
    imgs_vh = []
    for file in files:
        data = np.array(Image.open(os.path.join(file_path, file)))
        if data.sum() < 100:  # 图像中没有像素信息时应该丢弃图片
            continue
        if file.endswith('001.tif'):
            # tmp = data[-1400:, :1400]
            # print(tmp.shape)
            imgs_vv.append(data[600:1000, 920:1320])
        else:
            imgs_vh.append(data[600:1000, 920:1320])

    if save_path:
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        spath = os.path.join(save_path, zonename)
    else:
        spath = os.path.join(file_path, 'matrix')
        if not os.path.exist(spath):
            os.mkdir(spath)
        spath = os.path.join(spath, zonename)

    imgs_vv = np.array(imgs_vv, dtype=np.float32)
    print(imgs_vv.shape)
    np.save(spath + f'_vv_{size}x{size}.npy', imgs_vv)
    imgs_vv = imgs_vv.swapaxes(1, 2).swapaxes(0, 2)
    savemat(spath + f'_vv_{size}x{size}.mat', {'data': imgs_vv})

    imgs_vh = np.array(imgs_vh, dtype=np.float32)
    print(imgs_vh.shape)
    np.save(spath + f'_vh_{size}x{size}.npy', imgs_vh)
    imgs_vh = imgs_vh.swapaxes(1, 2).swapaxes(0, 2)
    savemat(spath + f'_vh_{size}x{size}.mat', {'data': imgs_vh})


if __name__ == "__main__":
    # test()
    fpath = "/run/media/yalin/TOSHIBAyalin/SentinelData/SanggendalaiStation_subset/subset_medusa3/"
    save_path = "/run/media/yalin/TOSHIBAyalin/SentinelData/SanggendalaiStation_subset/subset_medusa3/matrix/"
    zonename = "sanggendalaiStation"
    size = 400
    main(fpath, zonename, size, save_path)
