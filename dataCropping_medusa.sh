#!/bin/bash
### 预处理及裁剪数据
### 本程序需要 gdal 工具支持，请确保 /usr/bin/gdalwarp 存在！如果不存在，请根据您所使用的发行版
### 的包管理工具安装 gdal 以及它的依赖
### 对于 ArchLinux 可以执行如下命令安装 gdal 及其依赖：
###     sudo pacman -S gdal arrow hdf5 mariadb-libs postgresql-libs netcdf


# 设置代理
# export ALL_PROXY="socks5://127.0.0.1:20170"

# PATH=$PATH":/home/yalin/snap/bin/"
product_path="/run/media/yalin/TOSHIBAyalin/SentinelData/Downloads/Products/sanggendalai/20190101-20201231/"
save_path="/run/media/yalin/TOSHIBAyalin/SentinelData/SanggendalaiStation_subset/subset_medusa3/"
geojson_file="/run/media/yalin/TOSHIBAyalin/SentinelData/SanggendalaiStation_subset/sanggendalaiStation3.geojson"
for product in $(ls $product_path*T1006*.zip)
do
    file_name=${product##*/}
    echo "Processing $file_name..."
    file_name=${file_name%%.zip}
#     echo "file name: $file_name"
    input_file="$product"
#     echo $input_file
    output_file="${save_path}Subset_${file_name}.dim"
#   echo $output_file
#     gpt $graph_path -Pinput=$input_file -Poutput=$output_file
    python sentinel_crop.py --sentinel 1 --archive $input_file --geojson $geojson_file --dest $save_path
    echo
done
echo "All products are processed successfully!"
