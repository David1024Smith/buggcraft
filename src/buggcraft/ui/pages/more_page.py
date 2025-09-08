# 更多页面

# src/buggcraft/ui/pages/more_page.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QFrame, QPushButton, QStackedWidget, QTextEdit, QButtonGroup,
                              QScrollArea, QTextBrowser, QLineEdit, QComboBox,
                              QGroupBox, QRadioButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from .base_page import BasePage
import os

class MorePage(BasePage):
    """更多页面 - 继承BasePage"""
    
    # 定义信号
    feedback_submitted = Signal(str, str, str)  # 反馈提交信号，参数为反馈类型、标题和内容
    
    def __init__(self, home_path, scale_ratio=1.0, parent=None):
        super().__init__(home_path, scale_ratio, parent)
        self.feedback_buttons = []  # 存储反馈类型单选按钮
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 设置背景
        self.set_background('resources/images/minecraft_bg.png')
        
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧导航
        nav_frame = QFrame()
        nav_frame.setFixedWidth(200)
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(53, 53, 53, 200);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        nav_layout = QVBoxLayout(nav_frame)
        
        nav_buttons = [
            ("关于与鸣谢", self.show_about),
            ("反馈", self.show_feedback)
        ]
        
        for text, callback in nav_buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: white;
                    border-radius: 4px;
                    text-align: left;
                    padding-left: 15px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QPushButton:pressed {
                    background-color: #5a5a5a;
                }
            """)
            btn.clicked.connect(callback)
            nav_layout.addWidget(btn)
        
        nav_layout.addStretch()
        main_layout.addWidget(nav_frame)
        
        # 右侧内容
        self.more_stack = QStackedWidget()
        self.more_stack.setStyleSheet("""
            QStackedWidget {
                background-color: rgba(53, 53, 53, 200);
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.more_stack)
        
        # 添加更多页面
        self.create_about_page()
        self.create_feedback_page()
    
    def create_about_page(self):
        """创建关于与鸣谢页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("关于与鸣谢")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # 启动器信息
        info_group = QGroupBox("启动器信息")
        info_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        info_layout = QVBoxLayout(info_group)
        
        info_layout.addWidget(QLabel("版本: v1.0.0"))
        info_layout.addWidget(QLabel("构建日期: 2023-10-15"))
        info_layout.addWidget(QLabel("开发者: Minecraft启动器团队"))
        
        layout.addWidget(info_group)
        
        # 鸣谢
        thanks_group = QGroupBox("鸣谢")
        thanks_group.setStyleSheet(info_group.styleSheet())
        thanks_layout = QVBoxLayout(thanks_group)
        
        thanks_layout.addWidget(QLabel("感谢以下项目对本启动器的支持:"))
        thanks_layout.addWidget(QLabel("- Minecraft Launcher Library"))
        thanks_layout.addWidget(QLabel("- PySide6"))
        thanks_layout.addWidget(QLabel("- Qt Framework"))
        
        layout.addWidget(thanks_group)
        
        # 开源协议
        license_group = QGroupBox("开源协议")
        license_group.setStyleSheet(info_group.styleSheet())
        license_layout = QVBoxLayout(license_group)
        
        license_layout.addWidget(QLabel("本启动器基于MIT开源协议发布"))
        license_layout.addWidget(QLabel("源代码可在GitHub仓库获取"))
        
        layout.addWidget(license_group)
        
        self.more_stack.addWidget(page)
    
    def create_feedback_page(self):
        """创建反馈页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("反馈")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # 提示信息
        tip = QLabel("提交新反馈时请先搜索是否存在，以免重复提交。如无法打开链接，请使用VPN")
        tip.setStyleSheet("color: #FFC107;")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        
        # 反馈类型
        type_group = QGroupBox("反馈类型")
        type_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        type_layout = QVBoxLayout(type_group)
        
        types = [
            ("游戏崩溃", "游戏在运行过程中崩溃"),
            ("无法启动", "游戏无法正常启动"),
            ("性能问题", "游戏运行卡顿或帧率低"),
            ("网络问题", "无法连接服务器或延迟高"),
            ("其他问题", "其他未列出的问题")
        ]
        
        # 创建单选按钮组
        self.feedback_type_group = QButtonGroup(self)
        for text, desc in types:
            radio = QRadioButton(text)
            radio.setToolTip(desc)
            type_layout.addWidget(radio)
            self.feedback_type_group.addButton(radio)
        
        layout.addWidget(type_group)
        
        # 反馈内容
        content_group = QGroupBox("反馈内容")
        content_group.setStyleSheet(type_group.styleSheet())
        content_layout = QVBoxLayout(content_group)
        
        content_layout.addWidget(QLabel("问题描述:"))
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("请详细描述您遇到的问题")
        content_layout.addWidget(self.description_input)
        
        content_layout.addWidget(QLabel("重现步骤:"))
        
        self.steps_input = QLineEdit()
        self.steps_input.setPlaceholderText("请描述如何重现此问题")
        content_layout.addWidget(self.steps_input)
        
        layout.addWidget(content_group)
        
        # 提交按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        submit_btn = QPushButton("提交反馈")
        submit_btn.setFixedHeight(40)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        submit_btn.clicked.connect(self.submit_feedback)
        btn_layout.addWidget(submit_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        cancel_btn.clicked.connect(self.clear_feedback_form)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.more_stack.addWidget(page)
    
    def show_about(self):
        """显示关于与鸣谢页面"""
        self.more_stack.setCurrentIndex(0)
    
    def show_feedback(self):
        """显示反馈页面"""
        self.more_stack.setCurrentIndex(1)
    
    def submit_feedback(self):
        """提交反馈"""
        # 获取选中的反馈类型
        selected_button = self.feedback_type_group.checkedButton()
        if not selected_button:
            # 这里应该显示错误提示
            print("请选择反馈类型")
            return
        
        feedback_type = selected_button.text()
        description = self.description_input.text()
        steps = self.steps_input.text()
        
        if not description:
            # 这里应该显示错误提示
            print("请填写问题描述")
            return
        
        # 组合反馈内容
        content = f"问题描述: {description}\n重现步骤: {steps}"
        
        # 发出信号
        self.feedback_submitted.emit(feedback_type, description, content)
        
        # 清空表单
        self.clear_feedback_form()
        
        # 这里应该显示提交成功的提示
        print("反馈提交成功")
    
    def clear_feedback_form(self):
        """清空反馈表单"""
        # 清除单选按钮选择
        self.feedback_type_group.setExclusive(False)
        for button in self.feedback_type_group.buttons():
            button.setChecked(False)
        self.feedback_type_group.setExclusive(True)
        
        # 清空输入框
        self.description_input.clear()
        self.steps_input.clear()
