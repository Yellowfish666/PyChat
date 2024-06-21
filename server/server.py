import socket
import threading
import os
import json
import time

# 保存所有连接的客户端
clients = {}
# 示例用户数据
user_credentials = {}
data_dir = 'server/data/'

def broadcast_user_list(username=None):
    user_list = {
        "all": list(user_credentials.keys()),
        "online": list(clients.keys())
    }
    message = f"USERLIST:{json.dumps(user_list)}"
    for client_socket in clients.values():
        # 将所有用户头像发送给所有在线客户端
        for username in user_credentials:
            path = os.path.join(data_dir, f"avatar/{username}.png")
            file_size = os.path.getsize(path)
            msg = f"AVATAR:{username}.png:{file_size}"
            client_socket.send(msg.encode('utf-8'))
            time.sleep(0.1)
            with open(path, "rb") as f:
                while chunk := f.read(1024):
                    client_socket.send(chunk)
            time.sleep(0.1)
        client_socket.send(message.encode('utf-8'))
        time.sleep(0.1)

def handle_client(client_socket, addr):
    try:
        # 用户验证或注册
        credentials = client_socket.recv(1024).decode('utf-8')
        if credentials.startswith("REGISTER"):
            username, password = credentials.split(':')[1:]
            if username in user_credentials:
                client_socket.send("REGISTER_FAILED".encode('utf-8'))
                client_socket.send("Username already exists".encode('utf-8'))
                print(f"Registration failed for {addr}: Username already exists")
            else:
                user_credentials[username] = password
                client_socket.send("REGISTER_SUCCESS".encode('utf-8'))
                print(f"Registration successful for {addr}: {username}")
                # 存储用户上传的头像
                avatar_message = client_socket.recv(1024).decode('utf-8')
                if avatar_message.startswith("AVATAR:"):
                    _, filesize = avatar_message.split(':')
                    filesize = int(filesize)
                    with open(os.path.join(data_dir, f"avatar/{username}.png"), "wb") as f:
                        bytes_received = 0
                        while bytes_received < filesize:
                            data = client_socket.recv(1024)
                            if not data:
                                break
                            f.write(data)
                            bytes_received += len(data)
                    print(f"Avatar {username} received.")
                
        else:
            username, password = credentials.split(':')[1:]
            if username in user_credentials and user_credentials[username] == password:
                client_socket.send("LOGIN_SUCCESS".encode('utf-8'))
                clients[username] = client_socket
                broadcast_user_list(username)  # 用户成功登录后广播用户列表
                print(f"Login successful for {addr}: {username}")
                time.sleep(0.1)
                # 检查是否有离线消息
                if os.path.exists(os.path.join(data_dir, f"{username}.txt")):
                    with open(os.path.join(data_dir, f"{username}.txt"), "r", encoding='utf-8') as f:
                        for line in f:
                            line = line.strip('\n')
                            client_socket.send(line.encode('utf-8'))
                    os.remove(os.path.join(data_dir, f"{username}.txt"))
                # 检查是否有离线文件
                if os.path.exists(os.path.join(data_dir, f"{username}_file.txt")):
                    with open(os.path.join(data_dir, f"{username}_file.txt"), "r") as f:
                        for line in f:
                            _, filename, filesize = line.split(':')
                            client_socket.send(line.encode('utf-8'))
                            with open(os.path.join(data_dir, filename), "rb") as f:
                                while chunk := f.read(1024):
                                    clients[username].send(chunk)
                                print(f"File {filename} forwarded to {username}")
                            os.remove(os.path.join(data_dir, filename))
                    os.remove(os.path.join(data_dir, f"{username}_file.txt"))
            else:
                client_socket.send("LOGIN_FAILED".encode('utf-8'))
                print(f"Login failed for {addr}: Invalid credentials")
                client_socket.close()
                return

        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    print(f"Client {username} disconnected")
                    client_socket.close()
                    clients.pop(username, None)
                    broadcast_user_list()  # 用户断开连接后广播用户列表
                    break
                if message.startswith("FILE:"):
                    handle_file_transfer(client_socket, message)
                elif message.startswith("MSG:"):
                    _, target_user, msg = message.split(':', 2)
                    if target_user in clients:
                        forward_message(target_user, f"{username}: {msg}")
                    elif target_user in user_credentials:
                        # 进行离线消息处理
                        with open(os.path.join(data_dir, f"{target_user}.txt"), "a", encoding='utf-8') as f:
                            f.write(f"{username}: {msg}\n")
                    else:
                        clients[username].send(f"User {target_user} not found".encode('utf-8'))
                else:
                    print(f"Received from {username}: {message}")
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                client_socket.close()
                clients.pop(username, None)
                broadcast_user_list()  # 用户断开连接后广播用户列表
                break
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
        client_socket.close()
        clients.pop(username, None)
        broadcast_user_list()  # 用户断开连接后广播用户列表

def forward_message(target_user, message):
    if target_user in clients:
        try:
            clients[target_user].send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error forwarding message to {target_user}: {e}")

def handle_file_transfer(client_socket, message):
    _, target_user, filename, filesize = message.split(':')
    filesize = int(filesize)
    with open(os.path.join(data_dir, f"{filename}"), "wb") as f:
        bytes_received = 0
        while bytes_received < filesize:
            data = client_socket.recv(1024)
            if not data:
                break
            f.write(data)
            bytes_received += len(data)
    if target_user in clients:
        clients[target_user].send(f"FILE:{filename}:{filesize}".encode('utf-8'))
        with open(os.path.join(data_dir, f"{filename}"), "rb") as f:
            while chunk := f.read(1024):
                clients[target_user].send(chunk)
        print(f"File {filename} received from client and forwarded to {target_user}")
        os.remove(os.path.join(data_dir, f"{filename}"))
    elif target_user in user_credentials:
        with open(os.path.join(data_dir, f"{target_user}_file.txt"), "a") as f:
            f.write(f"FILE:{filename}:{filesize}\n")
        print(f"File {filename} received from client and saved for {target_user}")
    else:
        client_socket.send(f"User {target_user} not found".encode('utf-8'))
        print(f"File {filename} received from client but user {target_user} not found")
        os.remove(os.path.join(data_dir, f"{filename}"))

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5555))
    server.listen(5)
    print("Server started...")

    while True:
        client_socket, addr = server.accept()
        print(f"Connection from {addr}")
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()

def delete_files_in_directory(directory):
    for item_name in os.listdir(directory):
        item_path = os.path.join(directory, item_name)
        if os.path.isfile(item_path):
            os.remove(item_path)
            print(f"File {item_path} has been deleted")

if __name__ == "__main__":
    directory_path = data_dir
    delete_files_in_directory(directory_path)
    directory_path = data_dir + "avatar"
    delete_files_in_directory(directory_path)
    start_server()
