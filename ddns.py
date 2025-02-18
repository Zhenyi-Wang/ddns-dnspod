import os
from dotenv import load_dotenv
import json
import time
import logging
import requests
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dnspod.v20210323 import dnspod_client, models

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_config():
    """动态加载配置"""
    # 使用相对路径加载 .env 文件
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)
    
    config = {
        'secret_id': os.getenv('TENCENT_SECRET_ID'),
        'secret_key': os.getenv('TENCENT_SECRET_KEY'),
        'domain': os.getenv('DOMAIN'),
        'record_type': os.getenv('RECORD_TYPE'),
        'record_line': os.getenv('RECORD_LINE'),
        'subdomain': os.getenv('SUBDOMAIN'),
        'record_id': os.getenv('RECORD_ID'),
        'update_interval': int(os.getenv('UPDATE_INTERVAL', 3600))
    }
    
    # 检查必要参数并详细列出缺失的环境变量
    required_keys = ['secret_id', 'secret_key', 'domain', 'record_type', 'record_line', 'subdomain', 'record_id']
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        logging.error(f"缺少以下必要的环境变量: {', '.join(missing_keys)}")
        return None
    
    return config

def get_public_ip():
    """获取公网IP地址"""
    try:
        response = requests.get('http://ip-api.com/json', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return data['query']
        logging.error("获取公网IP失败：无效的响应")
        return None
    except requests.RequestException as e:
        logging.error(f"获取公网IP失败: {e}")
        return None

def update_dns_record(config, last_ip=None):
    """更新DNS解析记录"""
    try:
        # 获取公网IP
        ip = get_public_ip()
        if not ip:
            logging.error("无法获取公网IP")
            return last_ip, False

        # 如果IP没有变化，跳过更新
        if ip == last_ip:
            logging.info(f"公网IP未变化：{ip}，跳过更新")
            return ip, False

        # 实例化认证对象
        cred = credential.Credential(config['secret_id'], config['secret_key'])
        
        # 配置HTTP选项
        httpProfile = HttpProfile()
        httpProfile.endpoint = "dnspod.tencentcloudapi.com"

        # 配置客户端
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = dnspod_client.DnspodClient(cred, "", clientProfile)

        # 修改记录
        req = models.ModifyRecordRequest()
        params = {
            "Domain": config['domain'],
            "RecordType": config['record_type'],
            "RecordLine": config['record_line'],
            "Value": ip,
            "RecordId": int(config['record_id']),
            "SubDomain": config['subdomain']
        }
        req.from_json_string(json.dumps(params))
        logging.info(f"准备更新DNS记录：{config['subdomain']}.{config['domain']} -> {ip}")

        # 发送请求
        resp = client.ModifyRecord(req)
        logging.info(f"DNS记录更新成功：{config['subdomain']}.{config['domain']} -> {ip}")
        return ip, True

    except TencentCloudSDKException as err:
        logging.error(f"腾讯云SDK异常：{err}")
        return last_ip, False
    except Exception as e:
        logging.error(f"更新DNS记录时发生错误：{e}")
        return last_ip, False

def main():
    """主循环"""
    last_ip = None
    while True:
        config = None
        try:
            logging.info("开始执行DDNS更新")
            
            # 每次循环都重新加载配置
            config = load_config()
            if not config:
                logging.error("配置加载失败，将在下一个周期重试")
                continue

            last_ip, success = update_dns_record(config, last_ip)
            
            logging.info("DDNS更新执行结束")
        
        except Exception as e:
            logging.error(f"主循环发生未知错误：{e}")
        
        finally:
            # 使用配置的更新间隔，如果配置不可用则使用默认间隔
            wait_time = config.get('update_interval', 60)
            logging.info(f"等待 {wait_time} 秒后下次更新")
            time.sleep(wait_time)

if __name__ == "__main__":
    main()
