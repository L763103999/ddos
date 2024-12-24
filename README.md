# DDOS 测量墙机器人配置

## 项目简介
该项目用于将DDOS测量墙机器人与TG机器人进行对接，支持实时数据监控与通知。

## 安装步骤

### 1. 安装必备工具：`iftop`
首先需要安装必备的 `iftop`，使用以下命令安装：

apt install iftop

2. 接着，安装 python3 和 pip3：

apt install python3-pip

3. 安装 Telegram Bot 模块
使用 pip3 安装 Telegram 的 Python 模块

pip3 install python-telegram-bot

4. 安装 Screen
安装 screen 以便在后台运行脚本：
apt install screen
后端对接机器人

步骤 1: 修改 API Token
下载 py 脚本。
修改脚本中的机器人 API Token。
步骤 2: 新建 Screen 窗口
在后台运行脚本时，使用 screen 新建一个窗口：
screen -m

步骤 3: 运行脚本
在新窗口中，使用以下命令运行脚本：
python3 xxx.py
其中 xxx.py 为您的脚本名称。

交流飞机群 https://t.me/ydmfq
