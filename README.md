# DDNS 动态域名解析服务

## 项目简介
这是一个简单的动态域名解析（DDNS）服务，可以自动检测和更新公网IP地址，并将其同步到域名解析记录中。

## 功能特点
- 自动获取公网IP地址
- 定期检查IP地址变化
- 使用环境变量配置DNS服务提供商信息
- 支持Docker部署

## 环境要求
- Python 3.8+
- Docker (可选)

## 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/Zhenyi-Wang/ddns-dnspod.git
cd ddns-dnspod
```

2. 安装依赖
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

### Docker 运行
```bash
docker-compose up -d
```

## 配置说明
1. 复制 `.env.example` 为 `.env`
```bash
cp .env.example .env
```

2. 在 `.env` 文件中配置以下环境变量：
- `TENCENT_SECRET_ID`: 腾讯云访问密钥 ID
- `TENCENT_SECRET_KEY`: 腾讯云访问密钥
- `DOMAIN`: 要解析的主域名（例如 example.com）
- `RECORD_TYPE`: 解析记录类型（默认为 A 记录）
- `RECORD_LINE`: 解析线路（默认为 "默认"）
- `SUBDOMAIN`: 子域名前缀
- `RECORD_ID`: 腾讯云解析记录 ID
- `UPDATE_INTERVAL`: DDNS 更新间隔（秒），默认 60 秒

注意：请妥善保管您的 API 密钥，不要将其提交到公开仓库

## 日志
日志将输出到控制台，格式为：
`时间 - 日志级别: 消息`
日志级别包括 INFO 和 ERROR，可以帮助追踪程序运行状态和问题

### 控制台日志
直接运行程序时，日志将实时输出到控制台

### Docker 日志
使用 Docker Compose 运行时，可以通过以下命令查看日志：
```bash
# 查看最近的日志
docker-compose logs ddns

# 持续跟踪日志
docker-compose logs -f ddns
```
其中 `ddns` 是 `docker-compose.yml` 中定义的服务名称

## 许可证
MIT License

## 贡献
欢迎提交 Issues 和 Pull Requests