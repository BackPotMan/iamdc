# iamdc
运维自动化平台(iamdc)
http://www.huangdc.com


一、环境
系统: CentOS 6
python 版本: Python 2.7.10

二、Python 虚拟环境
1、安装
  pip install virtualenv

2、为一个工程创建一个虚拟环境
  mkdir /opt/project
  cd /opt/project && virtualenv venv

3、激活虚拟环境
  source venv/bin/activate

4、git clone 下载iamdc
  git clone https://github.com/huangdongcong/iamdc.git

5、安装所需环境
  cd iamdc && pip install -r requirements.txt

6、初始数据库模型
  migrate使用方法:
  第一次使用  python manager.py db init

  后面每次有表修改执行下面两句进行修改
  python manager.py db migrate
  python manager.py db upgrade

7、运行启动
python run.py




