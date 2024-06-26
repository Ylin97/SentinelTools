# 需要挂代理才能加快下载速度，同时需要安装 pysocks 包来解析代理

import os
import time
from collections import OrderedDict
from multiprocessing import Process, Lock, Value
# sentinelsat中导入相关的模块
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from sentinelsat.exceptions import LTATriggered, ServerError, InvalidChecksumError, LTAError


class UserParameter:
    """用户定义的相关参数

    Parameters
    ----------
    user : string
        username for DataHub
    password : string
        password for DataHub
    footprint : string
        Area for querying
    data: tuple(string, string)
        A time interval filter based on the Sensing Start Time of the products.
        Expects a tuple of (start, end), e.g. ("NOW-1DAY", "NOW").
        The timestamps can be either a Python datetime or a string in one of the
        following formats:

            - yyyyMMdd
            - yyyy-MM-ddThh:mm:ss.SSSZ (ISO-8601)
            - yyyy-MM-ddThh:mm:ssZ
            - NOW
            - NOW-<n>DAY(S) (or HOUR(S), MONTH(S), etc.)
            - NOW+<n>DAY(S)
            - yyyy-MM-ddThh:mm:ssZ-<n>DAY(S)
            - NOW/DAY (or HOUR, MONTH etc.) - rounds the value to the given unit

        Alternatively, an already fully formatted string such as "[NOW-1DAY TO NOW]" can be
        used as well.
    platform_name : string
        platform name of sentinel satelite, e.g. 'Sentinel-1'
    product_type : string
        product type, e.g. 'GRD', 'SLC'
    orbit_direction:
        orbit direction of sentinel satelite, 'ASCENDING' or  'DESCENDING'
    url : string, optional
        URL of the DataHub
        defaults to 'https://scihub.copernicus.eu/dhus'
    save_path : string
        save path for downdoaded products

    """
    def __init__(
        self, 
        user: str, 
        password: str, 
        footprint: str, 
        date : tuple,
        platform_name: str='Sentinel-1',
        product_type: str='SLC',
        orbit_direction: str='ASCENDING',
        api_url: str='https://scihub.copernicus.eu/dhus', 
        save_path: str = None
    ) -> None:
        self.user = user
        self.password = password
        self.footprint = footprint
        self.date = date
        self.platform_name = platform_name
        self.product_type = product_type
        self.orbit_direction = orbit_direction
        self.api_url = api_url
        # self.geojson_path = geojson_path
        if not save_path:
            self.save_path = os.path.join('Products', 
                                    time.strftime("%Y%m%dT%H%M%S", time.localtime()))
        else:
            self.save_path = save_path


def download_data(api: SentinelAPI, product: str, save_path: str) -> int:
    """download data of sentinel
    Parameters
    ----------
    `api` : SentinelAPI
    `product` : ID of product that created by SentinelAPI.query()
    `save_path`: save path for downloaded products
    """
    try:
        #通过 OData API 获取单一产品数据的主要元数据信息
        product_info = api.get_product_odata(product)
        print(product_info['title'])
        #下载产品id为product的产品数据
        api.download(product, directory_path=save_path)
    except LTATriggered:
        print(f"Product {product_info['title']} is not online. \
                    Will try to download again after 30 minutes.")
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


def download_LTA(api: SentinelAPI, LTA_list: list, product_ids: list, 
                lock: Lock, total: Value, remain: Value, max_times: int=3) -> None:
    """下载LTA产品
    Parameters
    ----------
    `api` : SentinelAPI
    `LTA_list` : LTA list for current user
    `product_ids` : a list for product IDs
    `total` : total of product queried
    `remain` : remain of produtcts
    `max_times` : maxium attempts
    """
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
                print(f'[{number}/{total.value}]', end=" ")
                if cnt >= max_times:
                    break
                
                res = download_data(api, current_id)
                if res == 0:
                    number += 1
                    lock.acquire()
                    remain.value -= 1
                    lock.release()
                    LTA_list.remove(current_id)
                    product_ids.remove(current_id)
                    break
                elif res == -1:
                    break
                cnt += 1
        remain_dl_times -= 1


def download(api: SentinelAPI, products: OrderedDict, lock: Lock, 
             total: Value, remain: Value, save_path, max_times: int=3) -> None:
    """下载所有产品
    Parameters
    ----------
    `api` : SentinelAPI
    `products` : Sentinel product that obtained by SentinelAPI.query()
    `total` : total of product queried
    `remain` : remain of produtcts
    `save_path`: save path for downloaded products
    `max_times` : maxium attempts
    """
    lock.acquire()
    total.value = len(products)
    remain.value = len(products)
    lock.release()
    print(f'remain in action: {remain.value}')
    print("Total: {} products".format(len(products)))

    if products:
        product_ids = list(products.keys())
    else:
        return

    LTA_list  = []     # Long Term Archivel 缓存
    # 通过for循环遍历并打印、下载出搜索到的产品文件名
    is_LTA_limit = False
    number = 1
    while product_ids:
        for current_id in product_ids:
            cnt = 0
            while True:
                print(f'[{number}/{total.value}]', end=" ")
                if cnt >= max_times:
                    break

                res = download_data(api, current_id, save_path)
                if res == 0:
                    number += 1
                    lock.acquire()
                    remain.value -= 1
                    lock.release()
                    product_ids.remove(current_id)
                    break
                elif res == -1:
                    LTA_list.append(current_id)
                    break
                elif res == -3:
                    is_LTA_limit = True
                    break
                cnt += 1
            # LTA 单用户的产品配额为20, 需要隔一段时间才会重新分配
            if (len(LTA_list) >= 20 or is_LTA_limit): 
                break
    download_LTA(api, LTA_list, product_ids, lock, total, remain, max_times)


def action(lock: Lock, params: UserParameter, total: Value, remain: Value) -> None:
    """下载主程序

    Parameters
    ----------
    `lock` : multiprocessing.Lock
    `params`  : user parameters
    `total` : total of product queried
    `remain` : remain of products
    """
    if not os.path.exists(params.save_path):
        os.makedirs(params.save_path)
    # 创建SentinelAPI, 请使用哥白尼数据开放获取中心自己的用户名及密码
    api = SentinelAPI(params.user, params.password, params.api_url)
    # 通过设置 OpenSearch API 查询参数筛选符合条件的所有 Sentinel-1L2A 级数据
    products = api.query(
                params.footprint,                      # Area 范围
                date=params.date,  # 搜索的日期范围
                platformname=params.platform_name,     # 卫星平台名，Sentinel-1                    
                producttype=params.product_type,       # 产品数据等级，'S2MSI2A'表示 S2-L2A 级产品
                orbitdirection=params.orbit_direction  # 升降轨选择，A 为升轨, Descending 为降轨 
            )            
    # 下载所有产品
    download(api, products, lock, total, remain, params.save_path, 3)


def check(lock: Lock, params: UserParameter):
    """ 检查下载子进程是否存活

    Parameters
    ----------
    `lock` : multiprocessing.Lock
    `params`  : user parameters
    """
    # 剩余的产品数量 (初始化为-1，使之进入 check() 函数的 while 循环)
    remain = Value('i', -1)
    # 总产品数
    total = Value('i', 0)
    # '下载'子进程
    download_process = Process(target=action, args=(lock, params, total, remain))
    download_process.start()
    while remain.value == -1 or remain.value > 0:
        if not download_process.is_alive():
            print("\n\033[1;33mWARN: Creating a new subprocessing now!\033[0m")
            download_process.close()
            download_process = Process(target=action, args=(lock, params, total, remain))
            download_process.start()
        # print(f'remain in check: {remain.value}')
        time.sleep(60 * 2)   # 每2分钟检查一次下载进程是否存活
    print("\nAll products downloaded successfully.\n\n--Bye.")
    download_process.close()


if __name__ == '__main__':
    # 相关参数设置
    area_name      = "shanghai"   # 区域名称
    save_path      = os.path.join("Products", area_name)   # 数据保存路径
    user_name      = "your_username"  # https://scihub.copernicus.eu/dhus 网站注册的账户名
    password       = "your_password"  # 账户密码 
    api_url        = "https://scihub.copernicus.eu/dhus"
    geojson_path   = "geojson/shanghai_map.geojson"  # 目标区域对应的geojson文件
    # 读入城市的 geojson 文件并转  换为 wkt 格式的文件对象，相当于足迹
    # 可以到此网址获取 https://geojson.io
    footprint      = geojson_to_wkt(read_geojson(geojson_path))
    date           = ('20220901','20230331')   # 搜索的日期范围
    platformname   = 'Sentinel-1'              # 卫星平台名，Sentinel-1                    
    producttype    = 'SLC'                     # 产品数据等级，'S2MSI2A'表示 S2-L2A 级产品
    orbitdirection = 'Ascending'               # 升降轨选择，A 为升轨, Descending 为降轨 

    parameters = UserParameter(
                        user_name, 
                        password, 
                        footprint,
                        date,
                        platformname,
                        producttype,
                        orbitdirection,
                        api_url, 
                        save_path
                    )
 
    # 设置代理环境变量
    os.environ["all_proxy"] = 'socks5://127.0.0.1:20170'

    # # 剩余的产品数量 (初始化为1，使之进入 check() 函数的 while 循环)
    # remain = Value('i', 1)

    # '检查'子进程
    lock = Lock()
    check_process = Process(target=check, args=(lock, parameters))
    check_process.start()
