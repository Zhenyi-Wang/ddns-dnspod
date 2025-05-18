import re
import logging
import requests

class IPFetcher:
    """IP 地址获取工具类，负责从多个服务获取公网 IP"""

    def __init__(self):
        """初始化 IP 获取器"""
        # 用于 HTTP 请求的通用头信息
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 可用于获取公网 IP 的服务列表
        self.ip_services = [
            # 国内服务
            {'url': 'https://myip.ipip.net/json', 'parser': lambda r: r.json()['data']['ip']},
            {'url': 'http://members.3322.org/dyndns/getip', 'parser': lambda r: r.text.strip()},
            # 稳定可用的国外服务（已测试可用）
            {'url': 'http://ip-api.com/json', 'parser': lambda r: r.json()['query'] if r.json()['status'] == 'success' else None},
            {'url': 'https://ifconfig.me/ip', 'parser': lambda r: r.text.strip()},
        ]

    def is_valid_ip(self, ip):
        """验证 IP 地址格式"""
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return bool(re.match(pattern, str(ip)))

    def get_public_ip(self):
        """获取公网 IP 地址，使用可靠的多个备选服务"""
        for service in self.ip_services:
            try:
                response = requests.get(service['url'], timeout=5, headers=self.headers)
                if response.status_code == 200:
                    ip = service['parser'](response)
                    if ip and self.is_valid_ip(ip):
                        logging.info(f"成功从 {service['url']} 获取到IP: {ip}")
                        return ip
            except Exception as e:
                logging.warning(f"从 {service['url']} 获取IP失败: {e}")
                continue

        logging.error("所有IP获取服务均失败")
        return None
