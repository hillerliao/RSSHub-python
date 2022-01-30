# 使用基础镜像库
FROM alpine:3.8
RUN echo -e http://mirrors.ustc.edu.cn/alpine/v3.7/main/ > /etc/apk/repositories

RUN apk add --no-cache vim nginx python3 uwsgi uwsgi-python3
RUN apk add --update --upgrade
RUN apk add --no-cache nginx python3 uwsgi uwsgi-python3
RUN pip3 install --no-cache-dir --upgrade pip
RUN ln -s /usr/bin/python3 /usr/bin/python


 
# 创建工作路径
RUN mkdir /app
 
# 指定容器启动时执行的命令都在app目录下执行
WORKDIR /app
 
# 替换nginx的配置
COPY nginx.conf /etc/nginx/nginx.conf
 
# 将本地目录下的内容拷贝到容器的app目录下
COPY . /app/

RUN apk update
RUN apk add --no-cache gcc musl-dev libxml2 libxslt-dev
# pip读取requirements.txt内容安装所需的库
RUN pip install -r /app/requirements.txt -i  https://pypi.tuna.tsinghua.edu.cn/simple some-package --no-cache-dir
 
# 启动nginx和uwsgi
ENTRYPOINT nginx -g "daemon on;" && uwsgi --ini /app/uwsgi.ini