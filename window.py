from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QTextEdit, QListWidget, QListWidgetItem, QHBoxLayout, QDialog, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import threading
import rw_data

model_name = None

class SettingWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.WIDTH, self.HEIGHT = 500, 400
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("设置")
        self.setGeometry(0, 0, self.WIDTH, self.HEIGHT)

        self.title_font = QFont("微软雅黑", 40)
        self.setting_text_font = QFont("微软雅黑", 20)
        self.setting_button_font = QFont("微软雅黑", 20)
        self.tip_font = QFont("微软雅黑", 10)

        self.layout = QVBoxLayout()

        self.title_label = QLabel("设置")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(self.title_font)
        self.layout.addWidget(self.title_label)

        self.tip_label = QLabel("贴士：在保存后请重启程序")
        self.tip_label.setAlignment(Qt.AlignCenter)
        self.tip_label.setFont(self.tip_font)
        self.layout.addWidget(self.tip_label)

        self.model_name_label = QLabel("模型名称：")
        self.model_name_label.setFont(self.setting_text_font)
        self.layout.addWidget(self.model_name_label)

        self.model_name_edit = QLineEdit()
        self.model_name_edit.setFont(self.setting_text_font)
        self.layout.addWidget(self.model_name_edit)

        self.save_settings_button = QPushButton("保存")
        self.save_settings_button.setFont(self.setting_button_font)
        self.save_settings_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_settings_button)

        self.setLayout(self.layout)
        
        self.activateWindow()
        self.raise_()

    def save_settings(self):
        new_model_data_settings = {}

        new_model_data_settings['model_name'] = self.model_name_edit.text()

        rw_data.write_data(new_model_data_settings)

class Window(QWidget):
    def __init__(self, respond_func):
        super().__init__()
        self.respond_func = respond_func
        self.is_ai_thinking = False
        self.history = []
        self.read_settings()
        self.init_ui()

    def read_settings(self):
        global model_name

        result_data = rw_data.return_data()

        model_name = result_data['model_name']

    def init_ui(self):
        self.WIDTH, self.HEIGHT = 2000, 1400

        self.setWindowTitle("Lite AI Assistant")
        self.setGeometry(0, 0, self.WIDTH, self.HEIGHT)

        self.layout = QVBoxLayout()

        self.title_font = QFont("微软雅黑", 40)
        self.text_edit_font = QFont("微软雅黑", 20)
        self.submit_button_font = QFont("微软雅黑", 20)
        self.chat_text_font = QFont("微软雅黑", 20)
        self.setting_button_font = QFont("微软雅黑", 8)

        self.title_label = QLabel("Lite AI Assistant")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(self.title_font)
        self.layout.addWidget(self.title_label)

        self.top_layout = QHBoxLayout()
        self.top_layout.addStretch()
        self.layout.addLayout(self.top_layout)

        self.setting_button = QPushButton("设置")
        self.setting_button.setFixedSize(self.WIDTH * 1 / 20, self.WIDTH * 1 / 20)
        self.setting_button.setFont(self.setting_button_font)
        self.setting_button.clicked.connect(self.setting_button_click)
        self.top_layout.addWidget(self.setting_button)

        self.chat_area = QListWidget()
        self.chat_area.setFont(self.chat_text_font)
        self.layout.addWidget(self.chat_area)

        self.text_edit = QTextEdit()
        self.text_edit.setFixedSize(self.WIDTH, self.HEIGHT * 1 / 5)
        self.text_edit.setFont(self.text_edit_font)
        self.layout.addWidget(self.text_edit)

        self.submit_button = QPushButton("提交")
        self.submit_button.setFont(self.submit_button_font)
        self.submit_button.setFixedSize(self.WIDTH, self.HEIGHT / 5)
        self.submit_button.clicked.connect(self.submit_button_click)
        self.layout.addWidget(self.submit_button)

        self.setLayout(self.layout)

    def setting_button_click(self):
        self.setting_window = SettingWindow(self)
        self.setting_window.show()

    def submit_button_click(self):
        if self.is_ai_thinking:
            return
        message = self.text_edit.toPlainText()
        item = QListWidgetItem(f"我：{message}")
        item.setFont(self.chat_text_font)
        item.setTextAlignment(Qt.AlignRight)
        self.chat_area.addItem(item)

        self.text_edit.clear()
        
        self.is_ai_thinking = True
        self.ai_answer_thread = threading.Thread(target=self.ai_answer, args=(message,))
        self.ai_answer_thread.start()
    
    def ai_answer(self, message):
        ai_message = self.respond_func(message, self.history)
        
        ai_item = QListWidgetItem(f"AI：{ai_message}")
        ai_item.setFont(self.chat_text_font)
        ai_item.setTextAlignment(Qt.AlignLeft)
        self.chat_area.addItem(ai_item)

        self.history.append((message, ai_message))
        
        self.is_ai_thinking = False

def start(respond_func):
    app = QApplication(sys.argv)
    window = Window(respond_func)
    window.show()
    sys.exit(app.exec_())
