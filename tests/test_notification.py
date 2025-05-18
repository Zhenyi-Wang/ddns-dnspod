#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试通知模块的邮件发送功能
"""

import os
import time
import logging
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import ConfigManager
from core.notification import NotificationManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def test_email_sending():
    """测试邮件发送功能"""
    print("开始测试邮件发送功能...")
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if not config:
        print("❌ 配置加载失败，请检查.env文件")
        return False
    
    # 检查SMTP配置
    smtp_keys = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 
                'smtp_sender_email', 'smtp_receiver_email']
    
    print("\n当前SMTP配置:")
    for key in smtp_keys:
        value = config.get(key, "未配置")
        # 对密码做特殊处理，不显示明文
        if key == "smtp_password" and value != "未配置":
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}")
    
    # 检查配置完整性
    missing_keys = [key for key in smtp_keys if not config.get(key)]
    if missing_keys:
        print(f"\n❌ SMTP配置不完整，缺少: {', '.join(missing_keys)}")
        return False
    
    # 初始化通知管理器
    notification_manager = NotificationManager(config_manager)
    
    # 发送测试邮件
    print("\n发送测试邮件...")
    domain_name = config_manager.get_full_domain()
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    subject = f"DDNS测试邮件: {domain_name}"
    body = f"""这是一封从DDNS服务发送的测试邮件。

时间: {current_time}
域名: {domain_name}

如果您收到此邮件，说明DDNS的邮件通知功能工作正常。
"""
    
    # 使用两种方式测试
    print("1. 测试普通通知邮件发送...")
    result1 = notification_manager.send_notification_email(subject, body)
    
    print("2. 测试错误通知邮件发送...")
    current_timestamp = time.time()
    result2 = notification_manager.send_error_notification(
        f"DDNS错误测试: {domain_name}",
        f"这是一封测试错误通知邮件，时间: {current_time}",
        current_timestamp,
        error_type='general'
    )
    
    if result1 and result2:
        print("\n✅ 邮件发送测试通过！请检查您的邮箱。")
        return True
    elif result1:
        print("\n⚠️ 普通邮件发送成功，但错误通知邮件发送失败。")
        return False
    elif result2:
        print("\n⚠️ 错误通知邮件发送成功，但普通邮件发送失败。")
        return False
    else:
        print("\n❌ 两种邮件发送均失败，请检查SMTP配置和日志。")
        return False

if __name__ == "__main__":
    test_email_sending()
