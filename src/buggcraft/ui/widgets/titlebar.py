import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, 
    QSizePolicy, QVBoxLayout, QSpacerItem
)
from PySide6.QtGui import QFont, QPixmap, QColor, QIcon, QPainter, QMouseEvent
from PySide6.QtCore import Qt, QPoint, QSize


class TitleBar(QWidget):
    """优化的自定义标题栏 - 使用布局管理器实现自适应"""
    
    def __init__(self, parent, resource_path):
        super().__init__(parent)
        self.parent = parent
        self.resource_path = resource_path
        self.setObjectName("TitleBar")
        self.dragging = False
        self.drag_position = QPoint()
        
        # 图标资源
        start_icon = QIcon(os.path.abspath(os.path.join(self.resource_path, 'images', 'bar', 'ic.png')))
        
        # 标签页配置
        self.tab_icons = {
            "开始": start_icon,
            "设置": start_icon
        }
        self.tab_names = ["开始", "设置"]
        
        # 创建透明图标 
        self.transparent_icon = QIcon(os.path.abspath(os.path.join(self.resource_path, 'images', 'bar', 'ic_no.png')))
        
        self.setFixedHeight(40)  # 固定高度
        self.init_ui()
    
    def paintEvent(self, event):
        """重绘事件 - 确保背景绘制"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))   
        super().paintEvent(event)

    def init_ui(self):
        # 主水平布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 0, 15, 0)
        main_layout.setSpacing(0)
        
         
        # 中间标签区域  
        main_layout.addStretch(1)  # 左侧拉伸
        
        self.tab_widget = QWidget()
        tab_layout = QHBoxLayout(self.tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 创建标签按钮
        self.tab_buttons = []
        for name in self.tab_names:
            tab_button = self.create_tab_button(name)
            self.tab_buttons.append(tab_button)
            tab_layout.addWidget(tab_button)
        
        main_layout.addWidget(self.tab_widget)
        main_layout.addStretch(1)  # 右侧拉伸
        
        # 右侧按钮区域
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        
        # 最小化按钮
        self.minimize_btn = QPushButton()
        self.minimize_btn.setFixedSize(15, 15)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #00AA36;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: #55BB6A;
            }
        """)
        self.minimize_btn.clicked.connect(self.parent.showMinimized)
        buttons_layout.addWidget(self.minimize_btn)
        
        # 关闭按钮
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(15, 15)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF0000;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: #F00036;
            }
        """)
        self.close_btn.clicked.connect(self.parent.close)
        buttons_layout.addWidget(self.close_btn)
        
        main_layout.addWidget(buttons_widget)
        
        # 设置初始选中状态
        self.set_active_tab(0)

    def create_tab_button(self, name):
        """创建单个标签按钮 - 使用背景图片和居中文字"""
        tab_button = QLabel()
        tab_button.setObjectName(f"tab_{name}")
        tab_button.mousePressEvent = lambda event: self.on_tab_clicked(name)
        
        # 设置按钮文字
        tab_button.setText(name)
        tab_button.setFont(QFont("Source Han Sans CN Heavy", 10))
        tab_button.setAlignment(Qt.AlignCenter)   
        
        # 设置初始样式 
        tab_button.setStyleSheet("""
            QLabel {
                color: #8e8e8e;
                font-weight: bold;
                background: transparent;
                 padding-left: 15px;
                padding-top: 5px;
            }
        """)
        
        # 设置  背景图片
        tab_button.setFixedSize(123, 45)
        
        return tab_button

    def set_active_tab(self, index):
        """设置活动标签页"""
        for i, tab_button in enumerate(self.tab_buttons):
            if i == index:
                # 激活状态 - 设置ic.png作为背景图片
                bg_path = str(self.resource_path / 'images' / 'bar' / 'ic.png').replace('\\', '/')
                tab_button.setStyleSheet(f"""
                    QLabel {{
                        color: #FFFFFF;
                        font-weight: bold;
                        background-image: url({bg_path});
                        background-repeat: no-repeat;
                        background-position: center;
                        padding-left: 15px;
                        padding-top: 5px;
                    }}
                """)
            else:
                # 非激活状态 - 透明背景
                tab_button.setStyleSheet("""
                    QLabel {
                        color: #8e8e8e;
                        font-weight: bold;
                        background: transparent;
                        padding-left: 15px;
                        padding-top: 5px;
                    }
                """)

    def on_tab_clicked(self, name):
        """标签点击事件处理"""
        if name in self.tab_names:
            index = self.tab_names.index(name)
            self.set_active_tab(index)
            # 调用父窗口的标签切换方法
            if hasattr(self.parent, 'switch_pages'):
                self.parent.switch_pages(index)
    
    # 保留原有的窗口拖动功能
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
