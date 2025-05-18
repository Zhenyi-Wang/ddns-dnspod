# DDNS 动态域名解析服务 (基于腾讯云 DNSPod)

## 项目简介
这是一个基于腾讯云 DNSPod 的动态域名解析（DDNS）服务。当您的公网 IP 地址发生变化时，本工具可以自动更新 DNSPod 中的域名解析记录，确保您的域名始终指向正确的 IP 地址。

## 功能特点
- 使用腾讯云 DNSPod API 进行域名解析
- 自动从多个备选服务获取公网 IP 地址
- 定期检查 IP 地址变化
- 自动更新 DNSPod 中的域名解析记录
- 自动验证DNS更新是否生效
- 支持配置子域名解析
- 支持SMTP邮件通知（成功更新和错误通知）
- 完善的错误处理和重试机制
- 支持 Docker 部署

## 环境要求
- Python 3.8+
- Docker (可选)

## 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/Zhenyi-Wang/ddns-dnspod.git
cd ddns-dnspod
```

2. 安装依赖（如果不是Docker Compose方式运行）
```bash
pip install -r requirements.txt
```

3. 配置环境变量
复制 `.env.example` 到 `.env` 并填写必要的配置信息

## 运行方式
### 直接运行
```bash
python ddns.py
```

### Docker Compose 运行
```bash
docker compose up -d
```

## 配置说明
1. 复制 `.env.example` 为 `.env`
```bash
cp .env.example .env
```

2. 在 `.env` 文件中配置以下环境变量：

### 必要配置项
- `TENCENT_SECRET_ID`: 腾讯云访问密钥 ID
- `TENCENT_SECRET_KEY`: 腾讯云访问密钥
- `DOMAIN`: 要解析的主域名（例如 example.com）
- `RECORD_TYPE`: 解析记录类型（默认为 A 记录）
- `RECORD_LINE`: 解析线路（默认为 “默认”）
- `SUBDOMAIN`: 子域名前缀，使用 @ 表示根域名
- `RECORD_ID`: 腾讯云解析记录 ID
- `UPDATE_INTERVAL`: DDNS 更新间隔（秒），默认 3600 秒

### 邮件通知配置项（可选）
- `SMTP_HOST`: SMTP 服务器地址
- `SMTP_PORT`: SMTP 服务器端口（默认 587）
- `SMTP_USER`: SMTP 用户名
- `SMTP_PASSWORD`: SMTP 密码
- `SMTP_SENDER_EMAIL`: 发件人邮箱
- `SMTP_SENDER_NAME`: 发件人名称（可选，默认为发件人邮箱）
- `SMTP_RECEIVER_EMAIL`: 接收通知的邮箱
- `SMTP_USE_TLS`: 是否使用TLS（默认为 true）
- `ERROR_EMAIL_INTERVAL`: 错误邮件发送间隔（秒），默认 3600 秒

注意：请妥善保管您的 API 密钥和邮箱密码，不要将其提交到公开仓库

## 工作流程
1. 程序启动后，加载配置文件
2. 定期执行以下操作：
   - 获取当前公网 IP 地址（使用多个备选服务保证可靠性）
   - 从 DNSPod 获取当前 DNS 解析记录
   - 比较当前 DNS 记录值和公网 IP
   - 如果不一致，使用 DNSPod API 更新解析记录
   - 更新后自动验证 DNS 记录是否已经生效
   - 根据配置发送邮件通知结果

## 错误处理机制
本程序实现了全面的错误处理机制：
- IP 获取失败：会尝试多个备选服务
- DNS API 错误：完整记录错误信息并通过邮件通知
- DNS 更新验证：自动验证 DNS 记录是否正确更新
- 配置加载失败：记录错误并尝试重新加载
- 所有错误都会记录到日志并根据配置发送通知邮件（保证不会频繁发送）

## 日志
日志将输出到控制台，格式为：
`时间 - 日志级别: 消息`
日志级别包括 INFO、WARNING、ERROR 和 CRITICAL，可以帮助追踪程序运行状态和问题

### 控制台日志
直接运行程序时，日志将实时输出到控制台

### Docker 日志
使用 Docker Compose 运行时，可以通过以下命令查看日志：
```bash
# 查看最近的日志
docker compose logs ddns

# 持续跟踪日志
docker compose logs -f ddns
```
其中 `ddns` 是 `docker-compose.yml` 中定义的服务名称

## 邮件通知
如果配置了 SMTP 相关参数，程序将在以下情况发送邮件通知：

### 成功通知
- DNS 记录成功更新并验证

### 错误通知
- 无法获取公网 IP
- DNS 记录更新失败
- DNS 更新验证失败
- 配置加载失败
- 程序运行中的其他严重错误

为避免频繁发送，同类型错误通知的发送会有间隔限制

## 许可证
MIT License

## 贡献
欢迎提交 Issues 和 Pull Requests