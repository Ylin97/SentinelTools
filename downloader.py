# 需要挂代理才能加快下载速度，同时需要安装 pysocks 包来解析代理
# 开启代理后需要设置环境变量： $env:all_proxy="socks5://127.0.0.1:port"
# 取消代理命令：$env:all_proxy=""

import os
import time
# sentinelsat中导入相关的模块
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from sentinelsat.exceptions import LTATriggered, ServerError, InvalidChecksumError


# 创建SentinelAPI，请使用哥白尼数据开放获取中心自己的用户名及密码
# api =SentinelAPI('用户名', '密码','https://scihub.copernicus.eu/apihub/')
api = SentinelAPI('kkkli', 'Acs2E%u6_GzHVkE', 'https://scihub.copernicus.eu/dhus')
# api = SentinelAPI('kkkli', 'Acs2E%u6_GzHVkE', 'https://scihub.copernicus.eu/apihub/')

city_name = "changsha"
save_path = f"Products/{city_name}"

if not os.path.exists(save_path):
	os.makedirs(save_path)


# 读入城市的geojson文件并转  换为wkt格式的文件对象，相当于足迹
# 可以到此网址获取 http://geojson.io
footprint =geojson_to_wkt(read_geojson(f'geojson/{city_name}_map.geojson'))

# 设置代理环境变量
os.environ["all_proxy"] = 'socks5://127.0.0.1:7890'

# 通过设置OpenSearch API查询参数筛选符合条件的所有Sentinel-1L2A级数据
products =api.query(footprint,            # Area范围
		date=('20220101','20220201'),     # 搜索的日期范围
		platformname='Sentinel-1',        # 卫星平台名，Sentinel-1                    
		producttype='GRD',                # 产品数据等级，'S2MSI2A'表示S2-L2A级产品
		orbitdirection='Ascending')       # 升降轨选择，Ascending 为升轨, Descending 为降轨        

print("Total: {} products".format(len(products)))

def download_data(product):
	"""download data of sentinel"""
	try:
		#通过OData API获取单一产品数据的主要元数据信息
		product_info = api.get_product_odata(product)
		print(product_info['title'])
		#下载产品id为product的产品数据
		api.download(product, directory_path=save_path)
	except LTATriggered:
		print(f"Product {product_info['title']} is not online. Will try to download again after 30 minutes.")
		time.sleep(3)
		return -1
	except (InvalidChecksumError, ServerError):
		time.sleep(3)
		return -2
	# except Exception:
	# 	time.sleep(5)
	# 	return -2
	else:
		return 0

MAX_TIMES = 3     # 最大尝试下载次数
LTA_list = []     # Long Term Archivel 缓存
remain_list = []  # 由于LTA配额限制导致无法暂时无法请求的产品（通常一小时后可以重新请求）
# 通过for循环遍历并打印、下载出搜索到的产品文件名
cnt = 1
for product in products:
	time_cnt = 0
	print(cnt, end=": ")
	while True:
		if time_cnt >= MAX_TIMES:
			break

		res = download_data(product)
		if res == 0:
			cnt += 1
			break
		elif res == -1:
			LTA_list.append(product)
			break
		time_cnt += 1

# 等待 30 分钟再开始尝试重新下载 LTA 产品
print("*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#")
print("Waiting to download LTA products...")
time.sleep(60 * 30)
print("**********************************************************")
print("Now try to download LTA products...")
for product in LTA_list:
	time_cnt = 0
	print(cnt, end=": ")
	while True:
		if time_cnt >= MAX_TIMES:
			break
		
		res = download_data(product)
		if res == 0:
			cnt += 1
			break
		time_cnt += 1