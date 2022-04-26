# nginx-gunicorn-flask

FROM ubuntu:latest
MAINTAINER Hiller Liao <hillerliao@163.com>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-virtualenv nginx supervisor

# Setup flask application
RUN mkdir -p /app
COPY . /app
RUN pip install -r /app/requirements.txt -i https://mirrors.aliyun.com/pypi/simple
RUN pip install gunicorn
# RUN pip install git+https://github.com/getsyncr/notion-sdk.git

# Setup nginx 
RUN rm /etc/nginx/sites-enabled/default
COPY flask.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/flask.conf /etc/nginx/sites-enabled/flask.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# Setup supervisord
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY gunicorn.conf /etc/supervisor/conf.d/gunicorn.conf

# Start processes
CMD ["/usr/bin/supervisord"]
