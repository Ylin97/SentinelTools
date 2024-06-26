# 需要挂代理才能加快下载速度，同时需要安装 pysocks 包来解析代理

import os
import time
from multiprocessing import Process, Value
# sentinelsat中导入相关的模块
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from sentinelsat.exceptions import LTATriggered, ServerError, InvalidChecksumError, LTAError


def download_data(api: SentinelAPI, product):
	"""download data of sentinel
	Parameters:
		api          : SentinelAPI
		product      : Sentinel product that created by SentinelAPI.query()
	"""
	try:
		#通过 OData API 获取单一产品数据的主要元数据信息
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
	except LTAError:
		time.sleep(3)
		return -3
	# except Exception:
	# 	time.sleep(5)
	# 	return -2
	else:
		return 0


def action(api: SentinelAPI, footprint: str, remain: Value):
	"""下载主程序
	Parameters:
		api          : SentinelAPI
		footprintf   : Well-Known Text string representation of the geometry 
					   that created by sentinelsat.geojson_to_wkt()
		remain       : Remain of products
	"""
	# 通过设置 OpenSearch API 查询参数筛选符合条件的所有 Sentinel-1L2A 级数据
	products = api.query(footprint,             # Area 范围
				date=('20210101','20220831'),   # 搜索的日期范围
				platformname='Sentinel-1',      # 卫星平台名，Sentinel-1                    
				producttype='GRD',              # 产品数据等级，'S2MSI2A'表示 S2-L2A 级产品
				orbitdirection='Ascending')     # 升降轨选择，Ascending 为升轨, Descending 为降轨        

	# global remain
	remain.value = len(products)
	print(f'remain in action: {remain.value}')
	print("Total: {} products".format(len(products)))

	if products:
		product_ids = list(products.keys())
	else:
		return

	MAX_TIMES = 3      # 最大尝试下载次数
	LTA_list  = []     # Long Term Archivel 缓存
	# 通过for循环遍历并打印、下载出搜索到的产品文件名
	is_LTA_limit = False
	number = 1
	while product_ids:
		for current_id in product_ids:
			cnt = 0
			while True:
				print(number, end=": ")
				if cnt >= MAX_TIMES:
					break

				res = download_data(api, current_id)
				if res == 0:
					number += 1
					remain.value -= 1;
					product_ids.remove(current_id)
					break
				elif res == -1:
					LTA_list.append(current_id)
					break
				elif res == -3:
					is_LTA_limit = True
					break
				cnt += 1
			if (len(LTA_list) >= 20 or is_LTA_limit):  # LTA 单用户的产品配额为20, 需要隔一段时间才会重新分配
				break;

		remain_dl_times = 3   # 对于 LAT 产品的最大尝试下载次数
		while LTA_list  and remain_dl_times > 0:
			# 等待 30 分钟再开始尝试重新下载 LTA 产品
			print("\n*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#")
			print("\033[34mWaiting to download LTA products... ({})\033[0m".format(
								time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
			time.sleep(60 * 30)
			print("\n**********************************************************")
			print("\033[34mNow try to download LTA products... ({})\033[0m".format(
								time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
			tmp_list = LTA_list.copy()
			for current_id in tmp_list:
				cnt = 0
				while True:
					print(number, end=": ")
					if cnt >= MAX_TIMES:
						break
					
					res = download_data(api, current_id)
					if res == 0:
						number += 1
						remain.value -= 1
						LTA_list.remove(current_id)
						product_ids.remove(current_id)
						break
					elif res == -1:
						break;
					cnt += 1
			remain_dl_times -= 1


def check(api, footprint: str, remain):
	""" 检查下载子进程是否存活
	Parameters:
		api          : SentinelAPI
		footprintf   : Well-Known Text string representation of the geometry 
					   that created by sentinelsat.geojson_to_wkt()
		remain       : Remain of products
	"""
	# '下载'子进程
	download_process = Process(target=action, args=(api, footprint, remain))
	download_process.start()
	while remain.value > 0:
		if not download_process.is_alive():
			print("\n\033[1;33mWARN: Creating a new subprocessing now!\033[0m")
			download_process.close()
			download_process = Process(target=action, args=(api, footprint, remain))
			download_process.start()
		# print(f'remain in check: {remain.value}')
		time.sleep(60 * 2)   # 每2分钟检查一次下载进程是否存活
	print("\nAll products downloaded successfully.\n\n--Bye.")
	download_process.close()


if __name__ == '__main__':

	# 创建SentinelAPI, 请使用哥白尼数据开放获取中心自己的用户名及密码
	# api = SentinelAPI('用户名', '密码', 'https://scihub.copernicus.eu/apihub/')
	api = SentinelAPI('用户名', '密码', 'https://scihub.copernicus.eu/dhus')

	# 城市名和文件保存路径设置
	city_name = "changsha"
	save_path = f"Products/{city_name}"

	if not os.path.exists(save_path):
		os.makedirs(save_path)

	# 读入城市的 geojson 文件并转  换为 wkt 格式的文件对象，相当于足迹
	# 可以到此网址获取 https://geojson.io
	footprint = geojson_to_wkt(read_geojson(f'geojson/{city_name}_map.geojson'))

	# 设置代理环境变量
	# os.environ["all_proxy"] = 'socks5://127.0.0.1:20170'

	# 剩余的产品数量 (初始化为1，使之进入 check() 函数的 while 循环)
	remain = Value('i', 1)

	# '检查'子进程
	check_process = Process(target=check, args=(api, footprint, remain))
	check_process.start()
	

