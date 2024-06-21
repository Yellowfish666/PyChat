import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel,
                             QFileDialog, QListWidget, QStackedWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QScrollArea, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QPropertyAnimation
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont
import socket
import os
import json
import time

data_dir = 'client/data/'
ipv4 = '192.168.3.47'

#modified
language = 'english'
translations = {
    'english': {
        'switch_language': '切换语言',
        'login': 'Login',
        'register': 'Register',
        'username': 'Username:',
        'password': 'Password:',
        'register_success': 'Registration successful!',
        'login_failed': 'Login failed. Please try again.',
        'Welcome_to_PyChat': 'Welcome to PyChat!',
        'registration_successful': 'Registration successful. Please login.',
        'file_received': 'File received',
        'send_file': 'Send File',
        'send': 'Send',
        'Join PyChat today!': 'Join PyChat today!',
        'Passwords do not match': 'Passwords do not match',
        'confirm_password': 'Confirm Password:',
        'You': 'You',
        'Select Avatar': 'Select Avatar',
        'Avatar Selected': 'Avatar Selected'
    },
    'chinese': {
        'switch_language': 'Switch Language',
        'login': '登录',
        'register': '注册',
        'username': '用户名：',
        'password': '密码：',
        'register_success': '注册成功！',
        'login_failed': '登录失败，请重试。',
        'Welcome_to_PyChat': '欢迎使用PyChat！',
        'registration_successful': '注册成功，请登录。',
        'file_received': '文件已接收',
        'send_file': '发送文件',
        'send': '发送',
        'Join PyChat today!': '加入PyChat吧！',
        'Passwords do not match': '密码不匹配',
        'confirm_password': '确认密码：',
        'You': '你',
        'Select Avatar': '选择头像',
        'Avatar Selected': '头像已选择'
    },
}
#modified
def translate(text):
    return translations[language].get(text, text)

class ClientThread(QThread):
    received_signal = pyqtSignal(str)
    file_signal = pyqtSignal(bytes, str, bool)
    userlist_signal = pyqtSignal(dict)

    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket

    def run(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                # if data.startswith(b"AVATAR:"):
                #     header = data.decode('utf-8')
                #     _, username = header.split(':')
                #     with open(os.path.join(data_dir, f"avatar/{username}.jpg"), "wb") as f:
                #         while chunk := self.client_socket.recv(1024):
                #             if chunk == "AVATAR_END".encode('utf-8'):
                #                 break
                #             f.write(chunk)
                #     print(f"Avatar uploaded for {username}")
                elif data.startswith(b"USERLIST:"):
                    user_list = json.loads(data[len("USERLIST:"):].decode('utf-8'))
                    self.userlist_signal.emit(user_list)  # 发送用户列表信号
                elif data.startswith(b"FILE:") or data.startswith(b"AVATAR:"):
                    header = data.decode('utf-8')
                    _, filename, filesize = header.split(':')
                    filesize = int(filesize)
                    bytes_received = 0
                    self.file_signal.emit(b'', filename, True)  # Start of file signal
                    while bytes_received < filesize:
                        chunk = self.client_socket.recv(1024)
                        if not chunk:
                            break
                        self.file_signal.emit(chunk, filename, False)
                        bytes_received += len(chunk)
                    self.file_signal.emit(b'', filename, False)  # End of file signal
                else:
                    self.received_signal.emit(data.decode('utf-8'))
            except ConnectionAbortedError:
                break
            except Exception as e:
                print(f"Error: {e}")
                break

#modified
class LoginWindow(QWidget):
    login_signal = pyqtSignal()
    register_signal = pyqtSignal()
    authenticated = pyqtSignal(str, str)  # Emits username and token after successful login
    userlist = pyqtSignal(socket.socket ,str, str)  # Emits username and token after successful login

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Login")
        self.setGeometry(100, 100,800,1200)
        self.setStyleSheet("""
            QWidget {
                background-color: #2E3440;
                color: #D8DEE9;
            }
            QLineEdit, QLabel {
                background-color: #3B4252;
                color: #D8DEE9;
                border: 1px solid #4C566A;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: 1px solid #5E81AC;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add logo and slogan
        # modified
        self.language_button = QPushButton(translate('switch_language'), self)
        self.language_button.setStyleSheet("font-family: 'Segoe UI', sans-serif")
        self.language_button.setFixedSize(150, 35)
        self.language_button.clicked.connect(self.switch_language)

        # Add logo and slogan
        #有修改
        self.logo = QLabel(self)
        pixmap = QPixmap(os.path.join(data_dir, 'avatar/UI.png'))
        pixmap = pixmap.scaled(self.logo.width(), self.logo.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo.setPixmap(pixmap)
        self.logo.setScaledContents(True)
        layout.addWidget(self.logo, alignment=Qt.AlignCenter)

        self.slogan = QLabel("Welcome to PyChat!", self)
        self.slogan.setStyleSheet("font-family: 'Segoe UI', sans-serif")
        layout.addWidget(self.slogan, alignment=Qt.AlignCenter)

        self.username_label = QLabel("Username:", self)
        self.username_label.setStyleSheet("font-family: 'Segoe UI', sans-serif")
        layout.addWidget(self.username_label)
        self.username = QLineEdit(self)

        layout.addWidget(self.username)

        self.password_label = QLabel("Password:", self)
        self.password_label.setStyleSheet("font-family: 'Segoe UI', sans-serif")
        layout.addWidget(self.password_label)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)
        self.password.returnPressed.connect(self.login)
        self.username.returnPressed.connect(self.password.setFocus)

        self.login_button = QPushButton("Login", self)
        self.login_button.setStyleSheet("font-family: 'Segoe UI', sans-serif")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.register_button = QPushButton("Register", self)
        self.register_button.setStyleSheet("font-family: 'Segoe UI', sans-serif")
        self.register_button.clicked.connect(self.register)
        layout.addWidget(self.register_button)

        self.resizeEvent(None)

    #修改：动态适应界面大小
    def resizeEvent(self, event):
        # Update logo size
        pixmap = QPixmap(os.path.join(data_dir, 'avatar/UI.png'))  # Replace with your logo path
        pixmap = pixmap.scaled(int(self.width() * 0.2), int(self.height() * 0.2), Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Adjust these values to suit your needs
        self.logo.setPixmap(pixmap)

        # Update username label, password label font size
        for widget in [self.username_label, self.password_label]:
            font = widget.font()
            font.setPointSize(14)  # Fixed font size
            widget.setFont(font)

        # Update username and password input text font size and height
        for widget in [self.username, self.password]:
            font = widget.font()
            font.setPointSize(12)  # Fixed font size
            widget.setFont(font)
            widget.setFixedHeight(30)  # Fixed height

        # Update login button, register button font size
        for widget in [self.login_button, self.register_button]:
            font = widget.font()
            font_size = self.height() * 0.03  # Adjust this value to suit your needs
            font.setPointSize(round(font_size))  # Round to nearest integer
            widget.setFont(font)

        # Update slogan style
        font_size = round(self.height() * 0.03)  # Adjust this value to suit your needs
        font = QFont()
        font.setPointSize(font_size)
        self.slogan.setFont(font)

        super().resizeEvent(event)
    
    def switch_language(self):
        global language
        language = 'chinese' if language == 'english' else 'english'
        self.language_button.setText(translate('switch_language'))
        self.login_button.setText(translate('login'))
        self.register_button.setText(translate('register'))
        self.username_label.setText(translate('username'))
        self.password_label.setText(translate('password'))
        self.slogan.setText(translate('Welcome_to_PyChat'))

    def login(self):
        username = self.username.text()
        password = self.password.text()

        # Connect to server and send login credentials
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((ipv4, 5555))
        self.client_socket.send(f"LOGIN:{username}:{password}".encode('utf-8'))
        response = self.client_socket.recv(1024).decode('utf-8')
        print(response)
        # label, message = response.split("\n")
        if response == "LOGIN_SUCCESS":
            token = "some_auth_token"  # For demonstration, replace with actual token generation
            # 转到聊天窗口
            # response1 = self.client_socket.recv(1024).decode('utf-8')
            # print(response1)
            self.userlist.emit(self.client_socket,username, token)
            # pass
        else:
            self.slogan.setText(translate('login_failed'))

    def register(self):
        # 转到注册窗口
        self.register_window = RegisterWindow()
        self.register_window.show()
        self.register_window.register_signal.connect(self.register_success)

    def register_success(self):
        self.slogan.setText(translate('registration_successful'))#modified
        self.register_window.close()

#modified   
class RegisterWindow(QWidget):
    register_signal = pyqtSignal()  # Emits username and password after successful registration

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Register")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #2E3440;
                color: #D8DEE9;
            }
            QLineEdit, QLabel {
                background-color: #3B4252;
                color: #D8DEE9;
                border: 1px solid #4C566A;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: 1px solid #5E81AC;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add logo and slogan
        self.logo = QLabel(self)
        pixmap = QPixmap(os.path.join(data_dir, 'avatar/UI.png'))  # Replace with your logo path
        self.logo.setPixmap(pixmap)
        layout.addWidget(self.logo, alignment=Qt.AlignCenter)

        self.slogan = QLabel("Join PyChat today!", self)
        self.slogan.setStyleSheet("font-family:'Segoe UI', sans-serif")
        layout.addWidget(self.slogan, alignment=Qt.AlignCenter)

        self.username_label = QLabel("Username:", self)
        self.username_label.setStyleSheet("font-family:'Segoe UI', sans-serif")
        layout.addWidget(self.username_label)
        self.username = QLineEdit(self)
        layout.addWidget(self.username)

        self.password_label = QLabel("Password:", self)
        self.password_label.setStyleSheet("font-family:'Segoe UI', sans-serif")
        layout.addWidget(self.password_label)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)

        self.confirm_password_label = QLabel("Confirm Password:", self)
        self.confirm_password_label.setStyleSheet("font-family:'Segoe UI', sans-seriff")
        layout.addWidget(self.confirm_password_label)
        self.confirm_password = QLineEdit(self)
        self.confirm_password.returnPressed.connect(self.register)
        self.username.returnPressed.connect(self.password.setFocus)
        self.password.returnPressed.connect(self.confirm_password.setFocus)
        self.confirm_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_password)

        # 设置选择头像按钮
        self.avatar_path = None
        self.avatar_button = QPushButton("Select Avatar", self)
        self.avatar_button.clicked.connect(self.select_avatar)
        self.avatar_button.setStyleSheet("font-family: 'Segoe UI', sans-serif")
        layout.addWidget(self.avatar_button)

        self.register_button = QPushButton("Register", self)
        self.register_button.setStyleSheet("font-family:'Segoe UI', sans-serif")
        self.register_button.clicked.connect(self.register)
        layout.addWidget(self.register_button)

        self.set_language()
        self.resizeEvent(None)

    def resizeEvent(self, event):
        # Update logo size
        pixmap = QPixmap(os.path.join(data_dir, 'avatar/UI.png'))  # Replace with your logo path
        pixmap = pixmap.scaled(int(self.width() * 0.2), int(self.height() * 0.2), Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Adjust these values to suit your needs
        self.logo.setPixmap(pixmap)

        # Update username label, password label, username and password input text, login button, register button font size
        for widget in [self.username_label, self.password_label, self.confirm_password_label, self.register_button, self.slogan, self.avatar_button]:
            font = widget.font()
            font_size = self.height() * 0.02  # Adjust this value to suit your needs
            font.setPointSize(round(font_size))  # Round to nearest integer
            widget.setFont(font)

        super().resizeEvent(event)

    def set_language(self):
        global language
        self.register_button.setText(translate('register'))
        self.username_label.setText(translate('username'))
        self.password_label.setText(translate('password'))
        self.slogan.setText(translate('Join PyChat today!'))
        self.confirm_password_label.setText(translate('confirm_password'))
        self.avatar_button.setText(translate('Select Avatar'))
    
    def register(self):
        username = self.username.text()
        password = self.password.text()
        confirm_password = self.confirm_password.text()

        if password == confirm_password:
            # Connect to server and send registration credentials
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ipv4, 5555))
            self.client_socket.send(f"REGISTER:{username}:{password}".encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(response)

            if response == "REGISTER_SUCCESS":
                # 将头像上传到服务器
                if self.avatar_path == None:
                    self.avatar_path = os.path.join(data_dir, 'avatar/BloodyWolf.png')
                file_size = os.path.getsize(self.avatar_path)
                self.client_socket.send(f"AVATAR:{file_size}".encode('utf-8'))
                with open(self.avatar_path, "rb") as f:
                    while chunk := f.read(1024):
                        self.client_socket.send(chunk)
                self.register_signal.emit()
            else:
                # self.slogan.setText("Registration failed. Please try again.")
                response = self.client_socket.recv(1024).decode('utf-8')
                print(response)
                self.slogan.setText(response)
        else:
            self.slogan.setText(self.translate('Passwords do not match'))

    def select_avatar(self):
        # 选择头像
        avatar_path, _ = QFileDialog.getOpenFileName(self, "Select Avatar", "", "Image Files (*.png *.jpg *.bmp)")
        if avatar_path:
            self.avatar_path = avatar_path
            self.avatar_button.setText(translate("Avatar Selected"))
            

class EmojiWidget(QWidget):
    emoji_signal = pyqtSignal()

    def __init__(self, user_input):
        super().__init__()
        self.initUI()
        self.text_edit = user_input

    def initUI(self):
        self.setWindowTitle("Emoji Example")
        self.setGeometry(200, 200, 420, 360)
        self.setStyleSheet("""
            QWidget {
                background-color: #2E3440;
                color: #D8DEE9;
            }
            QTableWidget {
                background-color: #3B4252;
                color: #D8DEE9;
                border: 1px solid #4C566A;
                padding: 5px;
                border-radius: 10px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #4C566A;
            }
        """)
        # 创建一个表格，并按需求设定大小和行列数
        self.table = QTableWidget(5, 6, self)
        self.table.setGeometry(0, 0, 440, 380)

        # 设置表格行高和列宽
        for i in range(self.table.columnCount()):
            self.table.setColumnWidth(i, 70)
        for i in range(self.table.rowCount()):
            self.table.setRowHeight(i, 70)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()

        # 填充emoji
        emojis = ["😀", "😃", "😄", "😁", "😆", "😅", "😊", "😌", "😍",
                "😘", "😗", "😙", "😚", "😋", "😜", "😝", "😛",
                "😎", "😏", "😒", "😞", "😔", "😟", "😠", "😡", "😢"]
        # 将emoji添加到表格中
        for index, emoji in enumerate(emojis):
            row = int(index / 6)
            col = int(index % 6)
            self.table.setItem(row, col, QTableWidgetItem(emoji))
        
        # 为表格单元格点击事件绑定处理函数
        self.table.cellClicked.connect(self.insert_emoji_into_text_edit)

    def insert_emoji_into_text_edit(self, row, col):
        emoji = self.table.item(row, col).text()
        self.text_edit.insert(emoji)
        self.close()

#modified
class ChatDialog(QWidget):
    def __init__(self, you, target_user, client_socket):
        super().__init__()
        self.your_username = you
        self.target_user = target_user
        self.client_socket = client_socket
        self.file_buffer = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Chat with {self.target_user}")
        self.setGeometry(100, 100, 800, 1200)
        self.setStyleSheet("""
            QWidget {
                background-color: #2E3440;
                color: #D8DEE9;
            }
            QLineEdit, QTextEdit, QLabel {
                background-color: #3B4252;
                color: #D8DEE9;
                border: 1px solid #4C566A;
                padding: 5px;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: 1px solid #5E81AC;
                padding: 5px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.chat_output = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_content.setLayout(self.chat_output)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        input_layout = QHBoxLayout()
        layout.addLayout(input_layout)

        self.user_input = QLineEdit(self)
        self.user_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.user_input)

        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("font-family: 'Segoe UI', sans-serif")
        input_layout.addWidget(self.send_button)

        self.emoji_button = QPushButton("😊", self)
        self.emoji_button.clicked.connect(self.emoji_selection)
        input_layout.addWidget(self.emoji_button)

        self.send_file_button = QPushButton("Send File", self)
        self.send_file_button.clicked.connect(self.send_file)
        self.send_file_button.setStyleSheet("font-family: 'Segoe UI', sans-serif")
        input_layout.addWidget(self.send_file_button)
        self.set_language()

    def create_message_bubble(self, sender, message, is_sender=True):
        bubble = QFrame()
        bubble.setStyleSheet("""
            QFrame {
                border-radius: 15px;
                background-color: #5E81AC;
                color: #ECEFF4;
                
                max-width: 70%;  # 动态调整气泡宽度
                word-wrap: break-word;
            }
        """ if is_sender else """
            QFrame {
                border-radius: 15px;
                background-color: #A3BE8C;
                color: #2E3440;
               
                max-width: 70%;  # 动态调整气泡宽度
                word-wrap: break-word;
            }
        """)

        layout = QVBoxLayout()
        bubble.setLayout(layout)

        avatar_layout = QHBoxLayout()
        layout.addLayout(avatar_layout)

        avatar = QLabel()
        if is_sender == True:
            pixmap = QPixmap(os.path.join(data_dir, f'avatar/{self.your_username}.png'))
        else:
            pixmap = QPixmap(os.path.join(data_dir, f'avatar/{sender}.png'))
        pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        avatar.setPixmap(pixmap)

        username_label = QLabel(sender)
        username_label.setStyleSheet("QLabel { margin: 1px; }")

        text_label = QLabel(message)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("QLabel { margin: 1px; }")

        if is_sender:
            message_layout = QHBoxLayout()
            message_layout.addWidget(text_label, alignment=Qt.AlignLeft)
            message_layout.addWidget(username_label, alignment=Qt.AlignCenter)
            message_layout.addWidget(avatar, alignment=Qt.AlignRight)
            avatar_layout.addLayout(message_layout)
            layout.addLayout(avatar_layout)
            layout.setAlignment(avatar_layout, Qt.AlignRight)
        else:
            avatar_layout.addWidget(avatar)
            avatar_layout.addWidget(username_label)
            avatar_layout.addWidget(text_label)
            layout.addLayout(avatar_layout)
            layout.setAlignment(avatar_layout, Qt.AlignLeft)

        layout.addStretch(1)

        return bubble

    def set_language(self):
        global language
        self.send_button.setText(translate('send'))
        self.send_file_button.setText(translate('send_file'))

    def receive_message(self, message):
        bubble = self.create_message_bubble(self.target_user, message, is_sender=False)
        self.chat_output.addWidget(bubble)
        if message.startswith("File"):
            message = message[5:-5]
            self.client_socket.send(f"MSG:{self.target_user}:{message} received".encode())
            bubble = self.create_message_bubble(translate("You"), translate("file_received"), is_sender=True)
            self.chat_output.addWidget(bubble)

    def emoji_selection(self):
        self.emoji_widget = EmojiWidget(self.user_input)
        self.emoji_widget.show()

    def send_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.txt)")
        if filepath:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            self.client_socket.send(f"FILE:{self.target_user}:{filename}:{filesize}".encode('utf-8'))
            with open(filepath, "rb") as f:
                while chunk := f.read(1024):
                    self.client_socket.send(chunk)
            time.sleep(2)
            self.client_socket.send(f"MSG:{self.target_user}:File {filename} sent".encode())
            bubble = self.create_message_bubble(translate("You"), f"File {filename} sent to {self.target_user}")
            self.chat_output.addWidget(bubble)

    def animate_widget(self, widget):
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(50000)
        animation.setStartValue(widget.geometry())
        animation.setEndValue(widget.geometry().adjusted(0, 0, 0, 50))
        animation.start()

    def send_message(self):
        message = self.user_input.text()
        if message:
            bubble = self.create_message_bubble(translate("You"), message)#modified
            self.chat_output.addWidget(bubble)
            self.user_input.clear()
            self.client_socket.send(f"MSG:{self.target_user}:{message}".encode())
            self.animate_widget(bubble)


class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.client_socket = None
        self.file_buffer = {}
        self.chat_dialogs = {}

    def initUI(self):
        self.setWindowTitle("Python Chat App")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #2E3440;
                color: #D8DEE9;
            }
            QLineEdit, QTextEdit, QLabel {
                background-color: #3B4252;
                color: #D8DEE9;
                border: 1px solid #4C566A;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: 1px solid #5E81AC;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
            QListWidget {
                background-color: #3B4252;
                border: 1px solid #4C566A;
                padding: 5px;
                border-radius: 5px;
            }
        """)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.contact_list = QListWidget(self)
        self.contact_list.itemClicked.connect(self.open_chat_dialog)
        layout.addWidget(self.contact_list)

        self.chat_stack = QStackedWidget(self)
        layout.addWidget(self.chat_stack)

        layout.setStretch(0, 1)
        layout.setStretch(1, 3)

    def open_chat_dialog(self, item):
        target_user = item.text()
        if target_user not in self.chat_dialogs:
            chat_dialog = ChatDialog(self.username, target_user, self.client_socket)
            self.chat_dialogs[target_user] = chat_dialog
            self.chat_stack.addWidget(chat_dialog)
        self.chat_stack.setCurrentWidget(self.chat_dialogs[target_user])


    def connect_to_server(self, client_socket, username, token):
        self.username = username
        self.token = token
        self.client_socket = client_socket
        self.thread = ClientThread(self.client_socket)
        self.thread.userlist_signal.connect(self.update_user_list)
        self.thread.received_signal.connect(self.receive_message)
        self.thread.file_signal.connect(self.receive_file)

        self.thread.start()

    def receive_message(self, message):
        if message.startswith("USERLIST:"): 
            self.update_user_list(json.loads(message[len("USERLIST:"):]))
        else:
            target_user, msg = message.split(': ', 1)
            if target_user in self.chat_dialogs:
                self.chat_dialogs[target_user].receive_message(msg)
            else:
                self.chat_dialogs[target_user] = ChatDialog(self.username, target_user, self.client_socket)
                self.chat_stack.addWidget(self.chat_dialogs[target_user])
                self.chat_dialogs[target_user].receive_message(msg)
            self.chat_stack.setCurrentWidget(self.chat_dialogs[target_user])

    def receive_file(self, data, filename, start):
        if start:
            self.file_buffer[filename] = b''
        elif data == b'':
            if filename.endswith(".png"):
                with open(os.path.join(data_dir, f"avatar/{filename}"), "wb") as f:
                    f.write(self.file_buffer[filename])
            else:
                with open(os.path.join(data_dir, filename), "wb") as f:
                    f.write(self.file_buffer[filename])
            del self.file_buffer[filename]
        else:
            self.file_buffer[filename] += data

    def update_user_list(self, user_list):
        self.contact_list.clear()
        all_users = user_list.get("all", [])
        online_users = user_list.get("online", [])
        sorted_users = sorted(all_users, key=lambda user: (user not in online_users, user))  # 在线用户排序在前
        for user in sorted_users:
            item = QListWidgetItem(user)
            avatar = QPixmap(os.path.join(data_dir, f'avatar/{user}.png'))  # 替换为实际头像路径
            if avatar.isNull():
                avatar = QPixmap(os.path.join(data_dir, 'avatar/BloodyWolf.png'))
            avatar = avatar.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item.setIcon(QIcon(avatar))
            if user == self.username:
                item.setBackground(QColor("#FFD700"))  # 金色背景标识当前用户
            elif user in online_users:
                item.setBackground(QColor("#A3BE8C"))  # 绿色背景标识在线用户
            else:
                item.setBackground(QColor("#3B4252"))  # 默认背景色
            self.contact_list.addItem(item)


class MainWindow(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.login_window = LoginWindow()
        self.register_window = RegisterWindow()
        self.chat_window = ChatWindow()

        self.login_window.userlist.connect(self.show_chat_window)
        self.login_window.register_signal.connect(self.show_register_window)
        self.register_window.register_signal.connect(self.handle_registration)

        self.addWidget(self.login_window)
        self.addWidget(self.register_window)
        self.addWidget(self.chat_window)

        self.setCurrentWidget(self.login_window)

    def show_chat_window(self, client_socket, username, token):
        self.chat_window.connect_to_server(client_socket, username, token)
        self.setCurrentWidget(self.chat_window)

    def show_register_window(self):
        self.setCurrentWidget(self.register_window)

    def handle_registration(self, username, password):
        self.register_window.close()
        self.login_window.username.setText(username)
        self.login_window.password.setText(password)
        self.setCurrentWidget(self.login_window)
        self.login_window.slogan.setText("Registration successful. Please login.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

