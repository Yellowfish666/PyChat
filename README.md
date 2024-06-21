# PyChat 聊天软件

## 目录结构

```
pychat/
├── client/
│   ├── client.py
│   ├── data/
│   │       ├── avatar/  # 包含用户头像图片
│   │       ├── ...      # 数据传输相关文件和目录
│   └── ...              # 其他客户端相关文件和目录
├── server/
│   ├── server.py
│   ├── data/
│   │       ├── avatar/  # 包含用户头像图片
│   │       ├── ...      # 数据传输保留在服务器端的部分文件和目录
│   └── ...              # 其他服务器相关文件和目录

```

## 使用方式

1. 克隆项目到本地：

```bash
git clone https://github.com/Yellowfish666/PyChat.git
```

2. 进入项目目录：

```bash
cd PyChat
```

3. 启动服务器：

```bash
python server/server.py
```

4. 启动客户端：

```bash
python client/client.py
```

5. 在客户端进行注册和登录，正确设置服务器的IP地址和端口号，然后开始聊天。
