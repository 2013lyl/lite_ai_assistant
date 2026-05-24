from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QTextEdit, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import warnings
import threading

warnings.filterwarnings("ignore", category=DeprecationWarning)

class Window(QWidget):
    def __init__(self, respond_func):
        super().__init__()
        self.respond_func = respond_func
        self.is_ai_thinking = False
        self.history = []
        self.init_ui()

    def init_ui(self):
        self.WIDTH, self.HEIGHT = 2000, 1400

        self.setWindowTitle("Lite AI Assistant")
        self.setGeometry(0, 0, self.WIDTH, self.HEIGHT)

        self.layout = QVBoxLayout()

        self.title_font = QFont("微软雅黑", 40)
        self.text_edit_font = QFont("微软雅黑", 20)
        self.submit_button_font = QFont("微软雅黑", 20)
        self.chat_text_font = QFont("微软雅黑", 20)

        self.title_label = QLabel("Lite AI Assistant")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(self.title_font)
        self.layout.addWidget(self.title_label)

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
