import os
import numpy as np
import matplotlib.pyplot as plt


class BandFigure:
    def __init__(self, band_pixels:np.array, band_name:str):
        """
        Params:
            band_pixels: a numpy.ndarray
            band_name: such as 'Intensity_VV' or 'Amplitude_VH'
        Return:
            No return 
        """
        self.pixels    = band_pixels
        self.band_name = band_name

    def plotall(self, issave=False, save_path=None, dpi=300)->plt.Figure:
        """
        Params:
            issave: save figure to file
            save_path: path of saved figure 
        Returns:
            No return
        """
        fig = plt.figure(clear=True)
        # with sigma
        for i in range(1, 4):
            data_nl = self._norm_log(self.pixels, i)
            plt.subplot(3, 2, i)
            plt.imshow(data_nl, cmap=plt.cm.gray)
            plt.title(f"{self.band_name} {i}sigma norm")
            plt.axis("off")
        # with sigma and log
        plt.subplot(3, 2, 4)
        data_nl = self._norm_log(self.pixels, 3, dolog=True)
        plt.imshow(data_nl, cmap=plt.cm.gray)
        plt.title(f"{self.band_name} 3sigma log-norm")
        plt.axis("off")
        # no log and no sigma
        plt.subplot(3, 2, 5)
        data_nl = self._norm_log(self.pixels)
        plt.imshow(data_nl, plt.cm.gray)
        plt.title(f"{self.band_name} norm")
        plt.axis("off")
        # with log no sigma
        plt.subplot(3, 2, 6)
        data_nl = self._norm_log(self.pixels, dolog=True)
        plt.imshow(data_nl, cmap=plt.cm.gray)
        plt.title(f"{self.band_name} log-norm")
        plt.axis("off")
        plt.suptitle(f"{self.band_name}", fontweight='bold', fontsize=16)
        plt.subplots_adjust(bottom=0.025)
        # plt.margins(0, 0)
        if issave:
            if save_path:
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                plt.savefig(os.path.join(save_path, f"{self.band_name}.png"), dpi=dpi)
            else:
                if not os.path.exists("Figure"):
                    os.mkdir("Figure")
                plt.savefig("Figure/{}.png".format(self.band_name), dpi=dpi)
        return fig

    def plotfig(self, sigma=None, dolog=False, issave=False, 
                save_path=None, dpi=300)->plt.Figure:
        """
        Plot only one Figure
        Params:
            sigma: 1, 2, or 3 (three-sigma rule of thum)
            dolog: precess data by log10()
        Returns:
            matplotlib.pyplot.Figure
        """
        fig = plt.figure(clear=True)
        data_nl = self._norm_log(self.pixels, sigma, dolog)
        figname = self.band_name
        if sigma:
            figname += f"_{sigma}sigma"
        if dolog:
            figname += "_log"
        plt.imshow(data_nl, cmap=plt.cm.gray)
        plt.title(figname)
        plt.axis("off")
        if issave:
            if save_path:
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                plt.savefig(os.path.join(save_path, figname + '.png'), dpi=dpi)
            else:
                if not os.path.exists("Figure"):
                    os.mkdir("Figure")
                plt.savefig("Figure/{}.png".format(figname), dpi=dpi)
        return fig

    def _norm_log(self, band_data: np.ndarray, sigma=None, dolog=False) -> np.ndarray:
        """Normalization and log10"""
        # row, col = dataset.shape
        if dolog:
            band_data = np.log10(band_data)
        
        data_mean  = band_data.mean()
        data_std   = band_data.std()
        if not sigma:
            data_max = band_data.max()
            data_min = band_data.min()
            data_nl = band_data / (data_max - data_min)
        elif sigma == 1:
            r_limit = data_mean + data_std
            l_limit = data_mean - data_std
            data_nl = self._normalization(band_data, l_limit, r_limit)       
        elif sigma == 2:
            r_limit = data_mean + data_std * 2
            l_limit = data_mean - data_std * 2
            data_nl = self._normalization(band_data, l_limit, r_limit)
        elif sigma == 3:
            r_limit = data_mean + data_std * 3
            l_limit = data_mean - data_std * 3
            data_nl = self._normalization(band_data, l_limit, r_limit)
        return data_nl

    def _normalization(self, band_data:np.ndarray, l_limit:float, r_limit:float):
        """
        [l_limit, r_limit] -> [0, 1]
        Params:
            band_data: A band's pixels (numpy.ndarray) 
            l_limit: left limit point for normalization
            r_limit: right limit point for normalization
        """
        data = band_data.copy()
        distance = r_limit - l_limit
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                if data[i, j] < l_limit:
                    data[i, j] = l_limit / distance
                elif data[i, j] < r_limit:
                    data[i, j] /= distance
                else:
                    data[i, j] = r_limit / distance
        return data


if __name__ == "__main__":
    from bandreader import *

    data_path = "data/subset_0_of_S1A_IW_GRDH_1SDV_20220131T105217_20220131T105242_041704_04F64F_C18D_Orb.data/"
    # data_path = "data/S1A_IW_GRDH_1SDV_20220131T105217_20220131T105242_041704_04F64F_C18D_Orb.data/"
    # band1 = Band()
    # band1.read_hdr("data/subset_0_of_S1A_IW_GRDH_1SDV_20220131T105217_20220131T105242_041704_04F64F_C18D_Orb.data/Amplitude_VV.hdr")
    # print(band1.height)
    band2 = Band(data_path, "Amplitude_VV")
    print(band2.byte_order)
    fig = BandFigure(band2.radar_pixels, "Amplitude_VV")
    # img = fig.plotfig(sigma=3, dolog=True)
    # img = fig.plotall(issave=True)
    img = fig.plotall(issave=True, save_path="Figure/all/1")
    plt.show()