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
        self.app_icon = QIcon(os.path.abspath(os.path.join(self.resource_path, 'images', 'bar', 'app.png')))
        start_icon = QIcon(os.path.abspath(os.path.join(self.resource_path, 'images', 'bar', 'ic.png')))
        
        # 标签页配置
        self.tab_icons = {
            "启动": start_icon,
            "设置": start_icon
        }
        self.tab_names = ["启动", "设置"]
        
        # 创建透明图标（用于未选中状态）
        self.transparent_icon = QIcon(os.path.abspath(os.path.join(self.resource_path, 'images', 'bar', 'ic_no.png')))
        
        self.setFixedHeight(40)  # 固定高度
        self.init_ui()
    
    def paintEvent(self, event):
        """重绘事件 - 确保背景绘制"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#2b2b2b"))
        super().paintEvent(event)

    def init_ui(self):
        # 主水平布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 0, 15, 0)
        main_layout.setSpacing(0)
        
        # 左侧应用图标
        app_icon_label = QLabel()
        app_icon_label.setPixmap(self.app_icon.pixmap(45, 45))
        app_icon_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(app_icon_label)
        main_layout.addSpacing(5)  # 添加间距
        
        # 中间标签区域 (居中显示)
        main_layout.addStretch(1)  # 左侧拉伸
        
        self.tab_widget = QWidget()
        tab_layout = QHBoxLayout(self.tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(20)
        
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
        """创建单个标签按钮 - 水平排列图标和文本"""
        tab_button = QWidget()
        tab_button.setObjectName(f"tab_{name}")
        tab_button.mousePressEvent = lambda event: self.on_tab_clicked(name)
        
        # 使用水平布局替代垂直布局
        layout = QHBoxLayout(tab_button)
        layout.setContentsMargins(5, 0, 5, 0)  # 减少左右边距使更紧凑
        layout.setSpacing(1)  # 减少图标和文本间距
        
        # 图标
        icon_label = QLabel()
        icon_label.setPixmap(self.transparent_icon.pixmap(15, 15))  # 稍微减小图标尺寸
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # 文本
        text_label = QLabel(name)
        text_label.setFont(QFont("Source Han Sans CN Heavy", 10))
        text_label.setStyleSheet("color: #8e8e8e; margin-top: 1px; font-weight: bold;")  # 添加微小上边距使文本偏下
        layout.addWidget(text_label)
        
        # 存储引用以便后续更新
        tab_button.icon_label = icon_label
        tab_button.text_label = text_label
        
        return tab_button

    def set_active_tab(self, index):
        """设置活动标签页"""
        for i, tab_button in enumerate(self.tab_buttons):
            icon_label = tab_button.findChild(QLabel, "", Qt.FindDirectChildrenOnly)
            text_label = tab_button.findChildren(QLabel)[-1] if tab_button.findChildren(QLabel) else None
            
            if i == index:
                # 激活状态
                if icon_label:
                    icon_label.setPixmap(self.tab_icons[self.tab_names[i]].pixmap(22, 22))
                if text_label:
                    text_label.setStyleSheet("color: #FFFFFF;")
            else:
                # 非激活状态
                if icon_label:
                    icon_label.setPixmap(self.transparent_icon.pixmap(22, 22))
                if text_label:
                    text_label.setStyleSheet("color: #8e8e8e;")

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
