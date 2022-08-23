import re
import os
import struct
import numpy as np


DATA_TYPES = {
    "1": [1, "int8"],
    "2": [2, "int16"],
    "3": [4, "int32"],
    "4": [4, "float32"],
    "5": [8, "float64"],
    "6": [8, "complex64"],
    "9": [16, "complex128"],
    "12": [2, "uint16"],
    "13": [4, "uint32"],
    "14": [8, "uint64"],
    "15": [8, "uint64"]
 }

class Band:
    """Sentine Product band"""
    def __init__(self, data_path=None, band_name=None) -> None:
        """
        Params:
            data_path: *.data folder's path;
            band_name: name of a band
        """
        self.name         = band_name
        self.radar_pixels = None
        self.width        = None
        self.height       = None
        self.map_info     = None
        self.byte_order   = None
        self.data_t       = None
        if data_path:
            self._init(data_path)

    def _init(self, data_path: str) -> None:
        self.read_hdr(os.path.join(data_path, f"{self.name}.hdr"))
        self.radar_pixels = self.read_img(os.path.join(data_path, f"{self.name}.img"))

    def read_hdr(self, path: str) -> None:
        """read *.hdr file """
        w_s, h_s, mi_s, dt_s, bo_s = True, True, True, True, True
        with open(path, 'r') as fr:
            img_info = fr.readlines()
            for line in img_info:
                # if nm_s:
                #     m = re.match(r"band names = {\s*(.*?)\s*}", line)
                #     self.name = m.group(1) if m else ""; nm_s = False
                if w_s:
                    m = re.match(r"samples = (\d+)", line)
                    if m:
                        self.width = int(m.group(1).strip()); w_s = False
                if h_s:
                    m = re.match(r"lines = (\d+)\n", line)
                    if m:
                        self.height = int(m.group(1).strip()); h_s = False
                if mi_s:
                    m = re.match(r"map info = {\s*(.*?)\s*}", line)
                    if m:
                        self.map_info = m.group(1); mi_s = False
                if bo_s:
                    m = re.match(r"byte order = (\d)", line)
                    if m:
                        self.byte_order = "big" if m.group(1) == '1' else "little"; bo_s = False
                    else:
                        self.byte_order = "big"
                if dt_s:
                    m = re.match(r"data type = (\d{1,2})", line)
                    if m and m.group(1) in DATA_TYPES.keys():
                        self.data_t = DATA_TYPES[m.group(1)]; dt_s = False

    def read_img(self, path: str) -> np.ndarray:
        """read *.img file"""
        with open(path, 'rb') as fr:
            radar_data = []
            dt = np.dtype(self.data_t[1])
            if self.byte_order == "big":
                dt = dt.newbyteorder('>')
            else:
                dt = dt.newbyteorder('<')
            for i in range(self.height):
                buf = fr.read(self.width * self.data_t[0])
                line_data = np.frombuffer(buf, dtype=dt)
                radar_data.append(line_data)
        radar_data = np.array(radar_data, dtype=np.float64)
        # print(radar_data.shape)
        return radar_data


if __name__ == "__main__":
    data_path = "data/subset_0_of_S1A_IW_GRDH_1SDV_20220131T105217_20220131T105242_041704_04F64F_C18D_Orb.data/"
    # data_path = "data/S1A_IW_GRDH_1SDV_20220131T105217_20220131T105242_041704_04F64F_C18D_Orb.data/"
    band1 = Band()
    band1.read_hdr("data/subset_0_of_S1A_IW_GRDH_1SDV_20220131T105217_20220131T105242_041704_04F64F_C18D_Orb.data/Amplitude_VV.hdr")
    print(band1.height)
    band2 = Band(data_path, "Amplitude_VV")
    print(band2.byte_order)