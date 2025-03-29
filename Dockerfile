# 使用官方的 Python 镜像作为基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 复制应用程序代码
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 暴露端口
EXPOSE 5000

# 启动应用程序
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app"]
