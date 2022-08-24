import os
import numpy as np
import matplotlib.pyplot as plt


class BandFigure:
    """
    Parameters
    ----------
        - band_pixels : numpy.ndarray
        - band_name : such as `Intensity_VV` or `Amplitude_VH` 
    """
    def __init__(self, band_pixels: np.array, band_name: str):
        self.pixels    = band_pixels
        self.band_name = band_name
        self.sigma     = 0
        self.dolog     = False

    def plotall(self, issave: bool=False, save_path: str=None,
                dpi: int=300) -> plt.Figure:
        """
        Parameters
        ------
            - issave : save figure to file
            - save_path : path of saved figure 

        Returns
        ------
            matplotlib.pyplot.Figure
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
        plt.title(f"{self.band_name} 3sigma-log norm")
        plt.axis("off")
        # no log and no sigma
        plt.subplot(3, 2, 5)
        data_nl = self._norm_log(self.pixels)
        plt.imshow(data_nl, cmap=plt.cm.gray)
        plt.title(f"{self.band_name} norm")
        plt.axis("off")
        # with log no sigma
        plt.subplot(3, 2, 6)
        data_nl = self._norm_log(self.pixels, dolog=True)
        plt.imshow(data_nl, cmap=plt.cm.gray)
        plt.title(f"{self.band_name} log norm")
        plt.axis("off")
        plt.suptitle(f"{self.band_name}", fontweight='bold', fontsize=16)
        plt.subplots_adjust(bottom=0.025)
        # plt.margins(0, 0)
        if issave:
            self._save("all", save_path, dpi)
        return fig

    def plotfig(self, sigma: int=None, dolog: bool=False, issave: bool=False, 
                save_path: str =None, dpi: int =300) -> plt.Figure:
        """
        Plot only one Figure

        Parameters:
        -----------
            - sigma : 1, 2, or 3 (three-sigma rule of thum)
            - dolog : precess data by log10()

        Returns
        -------
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
        plt.title(figname, fontweight='bold', fontsize=16)
        plt.axis("off")
        if issave:
            self._save("single", save_path, dpi)
        return fig

    def _norm_log(self, band_data: np.ndarray, sigma: int=None,
                  dolog: bool=False) -> np.ndarray:
        """Normalization and log10"""
        # row, col = dataset.shape
        self.sigma = sigma
        if dolog:
            band_data[band_data == 0] = 1 
            band_data  = np.log10(band_data)
            self.dolog = True
        
        data_mean  = band_data.mean()
        data_std   = band_data.std()
        if not sigma:
            data_max = band_data.max()
            data_nl = band_data / data_max
        elif sigma == 1:
            r_limit = data_mean + data_std
            l_limit = data_mean - data_std
            data_nl = self._norm_sigma(band_data, l_limit, r_limit)       
        elif sigma == 2:
            r_limit = data_mean + data_std * 2
            l_limit = data_mean - data_std * 2
            data_nl = self._norm_sigma(band_data, l_limit, r_limit)
        elif sigma == 3:
            r_limit = data_mean + data_std * 3
            l_limit = data_mean - data_std * 3
            data_nl = self._norm_sigma(band_data, l_limit, r_limit)
        return data_nl

    def _norm_sigma(self, band_data: np.ndarray, l_limit: float,
                    r_limit: float) -> np.ndarray:
        """
        [l_limit, r_limit] -> [0, 1]

        Parameters
        -----------
            - band_data : A band's pixels (numpy.ndarray) 
            - l_limit : left limit point for normalization
            - r_limit : right limit point for normalization
        
        Returns
        -------
        numpy.ndarray
        """
        data = band_data.copy()
        # normalizing
        data[data < l_limit] = l_limit / r_limit
        data[(data >= l_limit) & (data < r_limit)] /= r_limit
        data[data >= r_limit] = 1
        return data

    def _save(self, fig_t: str, save_path: str, dpi=300) -> None:
        """Save figure to file"""
        figname = self.band_name
        if fig_t == "all":
            figname += "_all"
        elif fig_t == "single":
            figname += "_norm" if not self.dolog else "_norm_log"
        if save_path:
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            plt.savefig(os.path.join(save_path, figname + '.png'), dpi=dpi)
        else:
            if not os.path.exists("Figure"):
                os.mkdir("Figure")
            plt.savefig("Figure/{}.png".format(figname), dpi=dpi)


if __name__ == "__main__":
    from bandreader import *

    # data_path = "data/subset_0_of_S1A_IW_GRDH_1SDV_20220131T105217_20220131T105242_041704_04F64F_C18D_Orb_Spk2.data/"
    data_path = "data/subset_0_of_S1A_IW_GRDH_1SDV_20220131T105217_20220131T105242_041704_04F64F_C18D_Orb.data/"
    # band1 = Band()
    # band1.read_hdr("data/subset_0_of_S1A_IW_GRDH_1SDV_20220131T105217_20220131T105242_041704_04F64F_C18D_Orb.data/Amplitude_VV.hdr")
    # print(band1.height)
    band2 = Band(data_path, "Amplitude_VV")
    print(band2.byte_order)
    fig = BandFigure(band2.radar_pixels, "Amplitude_VV")

    # img = fig.plotfig()
    # img = fig.plotfig(sigma=2)
    # img = fig.plotfig(sigma=3, dolog=True)
    # img = fig.plotfig(issave=True)
    # img = fig.plotfig(dolog=True, issave=True)
    # img = fig.plotfig(sigma=2, dolog=True, issave=True, save_path="Figure/single/1")
    img = fig.plotall()
    # img = fig.plotall(issave=True)
    # img = fig.plotall(issave=True, save_path="Figure/all/2")
    plt.show()