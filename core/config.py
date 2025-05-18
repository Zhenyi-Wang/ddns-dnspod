import os
import logging
from dotenv import load_dotenv

class ConfigManager:
    """配置管理类，负责加载和验证配置"""

    def __init__(self):
        """初始化配置管理器"""
        self.config = None
    
    def get_full_domain(self):
        """根据配置构建并返回完整域名。"""
        if self.config is None:
            return "[配置未加载]"
        domain = self.config.get('domain', "")
        subdomain = self.config.get('subdomain', "")
        if subdomain and subdomain != '@':
            return f"{subdomain}.{domain}"
        return domain

    def load_temp_smtp_config(self):
        """加载临时SMTP配置，用于在主配置加载失败时发送错误邮件"""
        error_email_interval = int(os.getenv('ERROR_EMAIL_INTERVAL', 3600))
        temp_config = {
            'smtp_host': os.getenv('SMTP_HOST'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'smtp_user': os.getenv('SMTP_USER'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'smtp_sender_email': os.getenv('SMTP_SENDER_EMAIL'),
            'smtp_sender_name': os.getenv('SMTP_SENDER_NAME', os.getenv('SMTP_SENDER_EMAIL')),
            'smtp_receiver_email': os.getenv('SMTP_RECEIVER_EMAIL'),
            'smtp_use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            'error_email_interval': error_email_interval,
            'domain': os.getenv('DOMAIN', '[域名未知]'),
            'subdomain': os.getenv('SUBDOMAIN', '')
        }
        
        # 检查必要的SMTP配置是否存在
        required_smtp_keys = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 
                             'smtp_sender_email', 'smtp_receiver_email']
        if all(temp_config.get(k) for k in required_smtp_keys):
            return temp_config
        return None

    def load_config(self):
        """动态加载配置"""
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
            'record_id': os.getenv('RECORD_ID'),
            'update_interval': int(os.getenv('UPDATE_INTERVAL', 3600)),
            # SMTP配置
            'smtp_host': os.getenv('SMTP_HOST'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'smtp_user': os.getenv('SMTP_USER'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'smtp_sender_email': os.getenv('SMTP_SENDER_EMAIL'),
            # 加载发件人名称。如果未设置，默认为发件人邮箱以便基本显示。
            'smtp_sender_name': os.getenv('SMTP_SENDER_NAME', os.getenv('SMTP_SENDER_EMAIL')),
            'smtp_receiver_email': os.getenv('SMTP_RECEIVER_EMAIL'),
            'smtp_use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            'error_email_interval': int(os.getenv('ERROR_EMAIL_INTERVAL', 3600))
        }
        
        # 检查必要参数并详细列出缺失的环境变量
        required_keys = ['secret_id', 'secret_key', 'domain', 'record_type', 'record_line', 'subdomain', 'record_id']
        # SMTP相关的检查，如果配置了接收邮箱，则其他SMTP参数也应配置
        if config.get('smtp_receiver_email'):
            required_keys.extend(['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'smtp_sender_email'])

        missing_keys = [key for key in required_keys if not config.get(key)]
        
        if missing_keys:
            logging.error(f"缺少以下必要的环境变量: {', '.join(missing_keys)}")
            return None
        
        self.config = config
        return config
    
    def get_config(self):
        """获取当前配置"""
        return self.config
