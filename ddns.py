import time
import logging

# 导入自定义模块
from core.config import ConfigManager
from core.ip_utils import IPFetcher
from core.dns_api import DNSUpdater
from core.notification import NotificationManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class DDNS:
    """DDNS主类，用于协调各个组件完成DDNS更新工作"""

    def __init__(self):
        """初始化DDNS更新器"""
        self.config_manager = ConfigManager()
        self.ip_fetcher = IPFetcher()
        self.notification_manager = None  # 初始化为None，等配置加载后再创建
        self.dns_updater = None  # 初始化为None，等配置加载后再创建
        
        # 配置初始状态变量
        self.update_verified = False  # 跟踪上次成功更新是否已验证
        self.verification_interval = 3600  # 默认验证间隔（1小时）
        self.last_verification_time = 0

    def initialize_components(self):
        """初始化依赖组件"""
        # 加载配置
        config = self.config_manager.load_config()
        if config:
            # 配置加载成功，创建其他组件
            self.notification_manager = NotificationManager(self.config_manager)
            self.dns_updater = DNSUpdater(self.config_manager)
            return True
        return False

    def handle_config_load_failure(self, current_time):
        """处理配置加载失败情况"""
        if self.notification_manager:
            return self.notification_manager.handle_config_load_failure(current_time)
        else:
            # 配置加载失败且通知管理器未初始化，先创建临时通知管理器
            temp_config = self.config_manager.load_temp_smtp_config()
            if temp_config:
                original_config = self.config_manager.config
                self.config_manager.config = temp_config
                
                # 临时创建通知管理器
                temp_notification_manager = NotificationManager(self.config_manager)
                temp_notification_manager.send_error_notification(
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

    def run(self):
        """运行DDNS服务的主循环"""
        config = None  # 在循环外初始化config，以便finally块中可用

        while True:
            try:
                logging.info("开始执行DDNS更新")
                
                # 初始化/重新初始化组件
                if not self.initialize_components():
                    wait_time = self.handle_config_load_failure(time.time())
                    time.sleep(wait_time)
                    continue
                
                config = self.config_manager.get_config()
                current_time = time.time()
                current_public_ip = self.ip_fetcher.get_public_ip()

                if not current_public_ip:
                    logging.error("无法获取当前公网IP，跳过本次更新")
                    domain_name = self.config_manager.get_full_domain()
                    self.notification_manager.send_error_notification(
                        f"DDNS IP获取失败: {domain_name}",
                        f"DDNS服务在为域名 {domain_name} 获取公网IP时失败。请检查网络连接和IP查询服务。",
                        current_time,
                        error_type='ip_fetch'
                    )
                    time.sleep(config.get('update_interval', 60))
                    continue

                domain_name = self.config_manager.get_full_domain()
                record_updated_in_this_cycle = False
                
                # 获取当前DNS记录值
                current_dns_record = self.dns_updater.get_current_dns_record()
                current_dns_ip = current_dns_record.get('value') if current_dns_record else None
                
                if not current_dns_record:
                    logging.warning(f"无法获取当前DNS记录值，将尝试更新到当前公网IP: {current_public_ip}")
                    update_needed = True
                else:
                    logging.info(f"当前DNS记录值: {domain_name} -> {current_dns_ip}")
                    update_needed = current_public_ip != current_dns_ip
                    
                if update_needed:
                    logging.info(f"需要更新DNS记录: {domain_name} 从 {current_dns_ip or '未知'} 到 {current_public_ip}")
                    update_success = self.dns_updater.update_dns_record(current_public_ip)
                    
                    if update_success:
                        logging.info(f"腾讯云API报告DNS记录更新请求成功: {domain_name} -> {current_public_ip}")
                        record_updated_in_this_cycle = True
                        
                        # 直接通过API验证更新是否成功
                        self.update_verified = self.dns_updater.verify_dns_update(current_public_ip, max_attempts=3, wait_time=10)

                        if self.update_verified:
                            logging.info(f"验证成功: {domain_name} 已指向 {current_public_ip}")
                            
                            if config.get('smtp_receiver_email'):
                                self.notification_manager.send_notification_email(
                                    f"DDNS更新成功: {domain_name}", 
                                    f"域名 {domain_name} 已成功更新并验证指向 {current_public_ip}。"
                                )
                            self.last_verification_time = current_time
                        else:
                            logging.warning(f"验证失败: {domain_name} 未能解析到 {current_public_ip} (在API成功后)")
                            self.notification_manager.send_error_notification(
                                f"DDNS验证失败: {domain_name}", 
                                f"域名 {domain_name} 更新后未能验证指向 {current_public_ip}。请检查DNS状态。", 
                                current_time,
                                error_type='dns_verify'
                            )
                    else:
                        logging.error(f"腾讯云API报告DNS记录更新请求失败: {domain_name} -> {current_public_ip}")
                        self.notification_manager.send_error_notification(
                            f"DDNS API更新请求失败: {domain_name}", 
                            f"更新域名 {domain_name} 到 {current_public_ip} 的API请求失败。请检查腾讯云后台和脚本日志。", 
                            current_time,
                            error_type='dns_update'
                        )
                else:
                    logging.info(f"当前DNS记录值与公网IP一致 ({current_public_ip}) for {domain_name}，跳过DNS更新")

                logging.info("DDNS更新执行结束")
            
            except Exception as e:
                logging.error(f"主循环发生未知错误：{e}", exc_info=True)  # 添加exc_info=True获取更详细的traceback
                current_time = time.time()

                error_subject = "DDNS服务发生严重错误"
                error_body = f"DDNS服务在主循环中遇到严重错误: {str(e)}。请检查日志获取详细的Traceback。"
                
                # 确定用于发送错误邮件的配置
                if self.notification_manager:
                    self.notification_manager.send_error_notification(
                        error_subject, error_body, current_time, error_type='general'
                    )
                else:
                    # 尝试使用临时配置发送错误通知
                    self.handle_config_load_failure(current_time)

            finally:
                config = self.config_manager.get_config()
                wait_time = config.get('update_interval', 60) if config else 60  # 如果config加载失败，默认等待60s
                logging.info(f"等待 {wait_time} 秒后下次更新")
                time.sleep(wait_time)


def main():
    """主程序入口"""
    try:
        ddns = DDNS()
        ddns.run()
    except Exception as e:
        logging.critical(f"程序启动失败: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    main()