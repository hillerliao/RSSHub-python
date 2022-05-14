#! /bin/bash
echo "重启Docker容器名称为： rsshub">>/home/lxf/log/restartdocker.log
docker restart rsshub
echo "重启命令的执行状态："$?>>/home/lxf/log/restartdocker.log
if [ $? -eq 0 ]; then
    echo "执行成功！">> /home/lxf/log/restartdocker.log
else
    echo "执行失败！">> //home/lxf/log/restartdocker.log
    exit
fi
echo "重启Docker容器： rsshub 完毕！输出日志在/home/lxf/log/restartdocker.log中">> /home/lxf/log/restartdocker.log