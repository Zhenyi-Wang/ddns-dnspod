import os
import json
import logging
from dotenv import load_dotenv
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
    """加载配置文件"""
    # 使用相对路径加载 .env 文件
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    logging.debug(f"尝试加载配置文件: {env_path}")
    load_dotenv(env_path, override=True)
    
    config = {
        'secret_id': os.getenv('TENCENT_SECRET_ID'),
        'secret_key': os.getenv('TENCENT_SECRET_KEY'),
        'domain': os.getenv('DOMAIN'),
        'record_type': os.getenv('RECORD_TYPE'),
        'record_line': os.getenv('RECORD_LINE'),
        'subdomain': os.getenv('SUBDOMAIN'),
        'record_id': os.getenv('RECORD_ID')
    }
    
    # 检查必要参数并详细列出缺失的环境变量
    required_keys = ['secret_id', 'secret_key', 'domain', 'record_type', 'record_line', 'subdomain', 'record_id']
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        logging.error(f"缺少以下必要的环境变量: {', '.join(missing_keys)}")
        return None
    
    return config

def get_dns_record(config):
    """获取域名的解析记录
    
    Args:
        config (dict): 包含配置信息的字典
        
    Returns:
        dict: 包含解析记录信息的字典，如果获取失败则返回None
    """
    try:
        # 实例化认证对象
        cred = credential.Credential(config['secret_id'], config['secret_key'])
        
        # 配置HTTP选项
        httpProfile = HttpProfile()
        httpProfile.endpoint = "dnspod.tencentcloudapi.com"

        # 配置客户端
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = dnspod_client.DnspodClient(cred, "", clientProfile)

        # 准备请求参数
        req = models.DescribeRecordListRequest()
        params = {
            "Domain": config['domain'],
            "Subdomain": config['subdomain'],
            "RecordType": config['record_type']
        }
        req.from_json_string(json.dumps(params))
        
        # 发送请求
        resp = client.DescribeRecordList(req)
        # 打印API响应详情
        logging.info(f"DescribeRecordList API Response: {resp.to_json_string()}")
        
        
        # 解析响应
        if hasattr(resp, 'RecordList') and resp.RecordList:
            for record in resp.RecordList:
                if record.Name == config['subdomain'] and record.Type == config['record_type']:
                    return {
                        'value': record.Value,
                        'record_id': record.RecordId,
                        'type': record.Type,
                        'line': record.Line,
                        'ttl': record.TTL,
                        'status': '已启用' if record.Status == 'ENABLE' else '已禁用'
                    }
        return None
        
    except TencentCloudSDKException as err:
        logging.error(f"腾讯云SDK异常：{err}")
        return None
    except Exception as e:
        logging.error(f"获取DNS记录时发生错误：{e}")
        return None

def update_dns_record(config, ip):
    """更新DNS解析记录
    
    Args:
        config (dict): 包含配置信息的字典
        ip (str): 要更新的IP地址
        
    Returns:
        bool: 更新是否成功
    """
    try:
        # 实例化认证对象
        cred = credential.Credential(config['secret_id'], config['secret_key'])
        
        # 配置HTTP选项
        httpProfile = HttpProfile()
        httpProfile.endpoint = "dnspod.tencentcloudapi.com"

        # 配置客户端
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = dnspod_client.DnspodClient(cred, "", clientProfile)

        # 准备请求参数
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
        logging.info(f"ModifyRecord API Response: {resp.to_json_string()}")
        logging.info(f"DNS记录更新成功：{config['subdomain']}.{config['domain']} -> {ip}")
        return True

    except TencentCloudSDKException as err:
        logging.error(f"腾讯云SDK异常：{err}")
        return False
    except Exception as e:
        logging.error(f"更新DNS记录时发生错误：{e}")
        return False

def print_record_info(record):
    """打印DNS记录信息
    
    Args:
        record (dict): DNS记录信息
    """
    if not record:
        print("未找到对应的DNS记录")
        return
        
    print("\n当前DNS记录信息：")
    print(f"记录值(IP): {record['value']}")
    print(f"记录类型: {record['type']}")
    print(f"线路: {record['line']}")
    print(f"TTL: {record['ttl']}")
    print(f"状态: {record['status']}")

def main():
    """主函数，用于测试DNS更新"""
    # 加载配置
    config = load_config()
    if not config:
        return
    
    # 获取当前DNS记录
    print(f"正在获取 {config['subdomain']}.{config['domain']} 的DNS记录...")
    record = get_dns_record(config)
    print_record_info(record)
    
    # 这里可以手动指定要更新的IP，或者从输入获取
    ip = "127.0.0.2"
    if not ip:
        print("IP地址不能为空")
        return
    
    # 更新DNS记录
    print(f"\n正在更新DNS记录到: {ip}")
    success = update_dns_record(config, ip)
    if success:
        print(f"\n✅ DNS记录更新成功: {config['subdomain']}.{config['domain']} -> {ip}")
        
        # 更新后再次获取记录
        print("\n正在验证更新后的DNS记录...")
        updated_record = get_dns_record(config)
        print_record_info(updated_record)
    else:
        print("\n❌ DNS记录更新失败，请查看日志了解详情")

if __name__ == "__main__":
    main()
