#!/bin/bash
### 预处理及裁剪数据

# 设置代理
# export ALL_PROXY="socks5://127.0.0.1:20170"

PATH=$PATH":/opt/snap/bin"
product_path="/media/yalin/TOSHIBAyalin/SentinelData/Downloads/Products/chongqing/"
save_path="/media/yalin/TOSHIBAyalin/SentinelData/Subsets/chongqing_sub/chongqing3/subset_snap/"
graph_path="/media/yalin/TOSHIBAyalin/SentinelData/Subsets/chongqing_sub/chongqing3/chongqing3.xml"

total=`ls $product_path*.zip | wc -l`
cnt=1
for product in $(ls $product_path*.zip)
do
    file_name=${product##*/}
    echo "[$cnt/$total] Processing $file_name..."
    file_name=${file_name%%.zip}
#     echo "file name: $file_name"
    input_file="$product"
#     echo $input_file
    output_file="${save_path}Subset_${file_name}.dim"
#    echo $output_file
    gpt $graph_path -Pinput=$input_file -Poutput=$output_file
    echo
    cnt=$[ cnt + 1 ]
done
echo "All products are processed successfully!"
# echo
# echo -e "\033[33mNow to process next task:\033[0m"
# echo
# bash /run/media/yalin/TOSHIBAyalin/SentinelData/SanggendalaiLake/Lake2/dataCropping_snap.sh
