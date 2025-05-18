import json
import time
import logging
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dnspod.v20210323 import dnspod_client, models

class DNSUpdater:
    """DNS 更新管理类，负责处理腾讯云 DNS 相关操作"""

    def __init__(self, config_manager):
        """
        初始化 DNS 更新器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
    
    def get_current_dns_record(self):
        """从腾讯云API获取当前DNS记录值"""
        config = self.config_manager.get_config()
        if not config:
            return None
            
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
            
            # 解析响应
            if hasattr(resp, 'RecordList') and resp.RecordList:
                for record in resp.RecordList:
                    if str(record.RecordId) == str(config['record_id']):
                        return {
                            'value': record.Value,
                            'record_id': record.RecordId,
                            'type': record.Type,
                            'line': record.Line,
                            'ttl': record.TTL,
                            'status': 'ENABLE' if record.Status == 'ENABLE' else 'DISABLE'
                        }
            domain_name = self.config_manager.get_full_domain()
            logging.warning(f"未找到匹配的DNS记录: {domain_name} (ID: {config['record_id']})")
            return None
            
        except TencentCloudSDKException as err:
            logging.error(f"腾讯云SDK异常：{err}")
            return None
        except Exception as e:
            logging.error(f"获取DNS记录时发生错误：{e}")
            return None

    def update_dns_record(self, ip):
        """
        更新DNS解析记录
        
        Args:
            ip: 新的 IP 地址
            
        Returns:
            bool: 是否更新成功
        """
        config = self.config_manager.get_config()
        if not config:
            return False
            
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
            domain_name = self.config_manager.get_full_domain()
            logging.info(f"准备更新DNS记录：{domain_name} -> {ip}")

            # 发送请求
            resp = client.ModifyRecord(req)
            # 日志在DDNS主类中统一处理，这里不再重复输出
            return True

        except TencentCloudSDKException as err:
            logging.error(f"腾讯云SDK异常：{err}")
            return False
        except Exception as e:
            logging.error(f"更新DNS记录时发生错误：{e}")
            return False

    def verify_dns_update(self, expected_ip, max_attempts=3, wait_time=10):
        """
        验证DNS更新是否已经生效，直接通过API查询记录值
        
        Args:
            expected_ip: 期望的 IP 地址
            max_attempts: 最大尝试次数
            wait_time: 每次尝试之间的等待时间(秒)
            
        Returns:
            bool: 是否验证成功
        """
        domain_name = self.config_manager.get_full_domain()
        
        for attempt in range(max_attempts):
            try:
                # 直接从API获取当前记录值
                current_record = self.get_current_dns_record()
                
                if not current_record:
                    logging.warning(f"无法获取当前DNS记录值 (尝试 {attempt+1}/{max_attempts})")
                else:
                    current_ip = current_record.get('value')
                    logging.info(f"API记录验证 (尝试 {attempt+1}/{max_attempts}): {domain_name} -> {current_ip}")
                    
                    # 检查记录值是否与预期一致
                    if current_ip == expected_ip:
                        # 成功日志在主类中输出，这里不再重复
                        return True
                    else:
                        logging.warning(f"DNS记录验证不匹配: 期望 {expected_ip}, 实际 {current_ip}")
                
                if attempt < max_attempts - 1:
                    # 删除过多的日志，只在调试级别记录
                    logging.debug(f"等待 {wait_time} 秒后重新验证...") 
                    time.sleep(wait_time)
                    
            except Exception as e:
                logging.error(f"DNS记录验证过程发生错误: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(wait_time)
        
        logging.error(f"DNS记录验证失败: 最大尝试次数 {max_attempts} 已用尽")
        return False
