FROM python:3.11-alpine AS build

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .
RUN pip install gunicorn

FROM python:3.11-alpine AS runtime

WORKDIR /app

# 复制并安装gunicorn
COPY --from=build /app/requirements.txt .
RUN pip install -r requirements.txt
RUN pip install Flask-Caching

# 复制应用代码
COPY --from=build /app .

# 设置用户和端口    
USER 1000:1000
EXPOSE 5000

ENTRYPOINT ["gunicorn", "-w", "4", "-b", ":5000", "main:app"]
