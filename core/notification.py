import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

class NotificationManager:
    """通知管理类，负责处理邮件通知和错误通知"""

    def __init__(self, config_manager):
        """
        初始化通知管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        
        # 错误邮件发送的时间戳记录
        self.last_error_times = {
            'ip_fetch': 0,      # 获取IP失败
            'dns_update': 0,    # DNS更新失败
            'dns_verify': 0,    # DNS验证失败
            'config': 0,        # 配置加载失败
            'general': 0        # 其他一般错误
        }

    def send_notification_email(self, subject, body):
        """
        发送邮件通知
        
        Args:
            subject: 邮件主题
            body: 邮件正文
            
        Returns:
            bool: 是否发送成功
        """
        config = self.config_manager.get_config()
        if not config or not config.get('smtp_receiver_email'):
            logging.info("未配置接收邮件地址，跳过邮件发送")
            return False

        msg = MIMEText(body)
        msg['Subject'] = subject
        # 使用formataddr设置发件人显示名称和邮箱地址
        msg['From'] = formataddr(
            (config.get('smtp_sender_name', config.get('smtp_sender_email')), 
             config.get('smtp_sender_email'))
        )
        msg['To'] = config['smtp_receiver_email']

        # 端口号决定使用哪种连接方式
        port = int(config.get('smtp_port', 587))
        use_ssl = port == 465  # 端口465通常使用SSL
        use_tls = config.get('smtp_use_tls', True) and not use_ssl  # 如果不是SSL，则根据配置决定是否使用TLS
        
        logging.debug(f"邮件连接方式: SSL={use_ssl}, TLS={use_tls}, Port={port}")
        
        try:
            # 建立连接，根据端口选择使用SSL还是普通SMTP
            if use_ssl:
                # 对于端口465，使用SSL直接加密连接
                logging.debug(f"使用SSL连接SMTP服务器: {config['smtp_host']}:{port}")
                server = smtplib.SMTP_SSL(config['smtp_host'], port, timeout=30)
            else:
                # 对于端口587等，先使用普通连接，然后如果需要则升级到TLS
                logging.debug(f"使用普通连接SMTP服务器: {config['smtp_host']}:{port}")
                server = smtplib.SMTP(config['smtp_host'], port, timeout=30)
            
            # 增加调试级别
            # server.set_debuglevel(1)  # 如需详细调试可启用此行
            
            # 设置连接超时
            if hasattr(server, 'sock') and server.sock:
                server.sock.settimeout(30)
            
            # 如果使用TLS但不是SSL，则升级连接
            if use_tls:
                server.starttls()
                logging.debug("已升级连接到TLS")
            
            # 登录验证
            server.login(config['smtp_user'], config['smtp_password'])
            logging.debug("登录成功")
            
            # 发送邮件
            server.sendmail(
                config['smtp_sender_email'], 
                [config['smtp_receiver_email']], 
                msg.as_string()
            )
            
            # 关闭连接
            server.quit()
            logging.info(f"邮件发送成功: {subject}")
            return True
        except smtplib.SMTPConnectError as e:
            logging.error(f"邮件发送失败 - 连接错误: {e}")
            return False
        except smtplib.SMTPAuthenticationError as e:
            logging.error(f"邮件发送失败 - 认证错误: {e}")
            return False
        except smtplib.SMTPException as e:
            logging.error(f"邮件发送失败 - SMTP错误: {e}")
            return False
        except (ConnectionRefusedError, TimeoutError) as e:
            logging.error(f"邮件发送失败 - 连接被拒绝或超时: {e}")
            return False
        except Exception as e:
            logging.error(f"邮件发送失败: {e}")
            return False

    def send_error_notification(self, subject, body, current_time, error_type='general'):
        """
        发送错误通知邮件，并遵循频率限制
        
        Args:
            subject: 邮件主题
            body: 邮件正文
            current_time: 当前时间戳
            error_type: 错误类型，可选值为 'ip_fetch', 'dns_update', 'dns_verify', 'config', 'general'
            
        Returns:
            bool: 是否成功发送邮件
        """
        config = self.config_manager.get_config()
        if not config or not config.get('smtp_receiver_email'):
            return False
        
        # 获取上次错误通知时间
        last_error_time = self.last_error_times.get(error_type, 0)
        
        error_interval = config.get('error_email_interval', 3600)
        if (current_time - last_error_time) <= error_interval:
            logging.info(f"{error_type} 类型的错误邮件已在 {error_interval} 秒内发送过，本次跳过")
            return False
        
        if self.send_notification_email(subject, body):
            # 更新错误通知时间
            self.last_error_times[error_type] = current_time
            return True
        return False
    
    def handle_config_load_failure(self, current_time):
        """
        处理配置加载失败的情况
        
        Args:
            current_time: 当前时间戳
            
        Returns:
            int: 重试等待时间(秒)
        """
        logging.error("配置加载失败，将在下一个周期重试")
        temp_config = self.config_manager.load_temp_smtp_config()
        if temp_config:
            # 临时设置配置用于发送失败通知
            original_config = self.config_manager.config
            self.config_manager.config = temp_config
            
            self.send_error_notification(
                "DDNS配置加载失败通知", 
                "DDNS服务无法加载配置文件，请检查.env文件和日志。", 
                current_time,
                error_type='config'
            )
            
            # 恢复原配置
            self.config_manager.config = original_config
        else:
            logging.warning("SMTP配置不完整，无法发送配置加载失败的邮件通知。")
        return 60  # 返回等待时间
