# CustomTitleBar 类

import os

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QTabWidget, QHBoxLayout,
    QSizePolicy, QTabBar
)
from PySide6.QtGui import QFont, QPixmap, QColor,  QIcon, QPainter, QMouseEvent
from PySide6.QtCore import Qt, QPoint


class TitleBar(QWidget):
    """自定义标题栏 - 使用 setTabIcon 方法"""
    def __init__(self, parent, HOME_PATH, width=1200, scale_ratio=1):
        super().__init__(parent)
        self.parent = parent

        self.HOME_PATH = HOME_PATH
        self.setObjectName("TitleBar")
        self.scale_ratio = scale_ratio
        self.dragging = False
        self.drag_position = QPoint()
        
        # 图标资源
        self.app_icon = QIcon(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'bar', 'app.png')))
        start = QIcon(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'bar', 'ic.png')))
        # start
        self.tab_icons = {
            "启动": start,
            "联机大厅": start,
            "下载": start,
            "设置": start,
            "更多": start
        }
        
        # 创建透明图标（用于未选中状态）
        self.transparent_icon = QIcon(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'bar', 'ic_no.png')))
        self.transparent_icon.addPixmap(QPixmap(27 * self.scale_ratio, 27 * self.scale_ratio), QIcon.Normal, QIcon.Off)
        
        self.setFixedHeight(48 * self.scale_ratio)  # 固定高度
        self.init_ui()
    
    def paintEvent(self, event):
        """重绘事件 - 确保背景绘制"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#2b2b2b"))
        super().paintEvent(event)

    def init_ui(self):
        # 计算布局位置
        parent_width = self.parent.width()
        tabs_width = 455 * self.scale_ratio # 标签页区域宽度
        
        # 标签页位置 - 居中
        tabs_x = (parent_width - tabs_width) // 2
        
        # 创建标签页容器
        self.tabs_container = QWidget(self)
        self.tabs_container.setGeometry(tabs_x, 5 * self.scale_ratio, tabs_width, 35 * self.scale_ratio)
        
        # 标签页布局
        tabs_layout = QHBoxLayout(self.tabs_container)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.setSpacing(0)
        
        # app icon
        app_icon_container = QWidget(self)
        app_icon_layout = QHBoxLayout(app_icon_container)
        app_icon_layout.setContentsMargins(25 * self.scale_ratio, 18 * self.scale_ratio, 25 * self.scale_ratio, 18 * self.scale_ratio)
        app_icon_layout.setSpacing(10 * self.scale_ratio)
        app_icon_label = QLabel()
        app_icon_label.setPixmap(self.app_icon.pixmap(60 * self.scale_ratio, 20 * self.scale_ratio))
        app_icon_label.setVisible(True)  # 初始隐藏
        app_icon_label.setAlignment(Qt.AlignCenter)  # 图标居中
        app_icon_layout.addWidget(app_icon_label)

        # 标签页
        self.tabs = QTabWidget(self.tabs_container)
        self.tabs.setContentsMargins(0, 0, 0, 0)
        self.tabs.setFixedSize(tabs_width, 48 * self.scale_ratio)
        self.tabs.setTabBarAutoHide(False)
        self.tabs.setDocumentMode(True)
        
        # 修复白杠问题并确保字体居中
        self.tabs.setStyleSheet(f"""
            QTabBar {{
                background: transparent;
                border: none;
                spacing: {5 * self.scale_ratio}px;  /* 标签之间的间距 */
            }}
            
            QTabBar::tab {{
                background: transparent;
                padding: {10 * self.scale_ratio}px 0px;
                border: none;
            }}
            QLabel {{
                color: #8e8e8e;
                text-align: center;
            }}
            QLabel:hover {{
                color: #FFF;
            }}
            QTabBar::tab:selected {{
                color: #ffffff !important;
            }}
            
            /* 鼠标悬停高亮效果 */
            QTabBar::tab:hover {{
                color: #ffffff !important;
            }}
        """)

        # 添加标签页
        tab_names = ["启动", "联机大厅", "下载", "设置", "更多"]
        for name in tab_names:
            tab = QWidget()
            self.tabs.addTab(tab, "")  # 修改这里：使用 name 作为标签文本
            
            # 创建标签容器 - 弹性布局
            tab_container = QWidget()
            tab_layout = QHBoxLayout(tab_container)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.setSpacing(0)
            
            # 添加图标
            icon_label = QLabel()
            icon_label.setPixmap(self.transparent_icon.pixmap(22 * self.scale_ratio, 22 * self.scale_ratio))
            icon_label.setVisible(True)  # 初始隐藏
            icon_label.setStyleSheet(f"""
                QLabel {{
                    margin-top: -{3 * self.scale_ratio}px;
                }}
            """)
            icon_label.setAlignment(Qt.AlignTop)  # 图标居中
            tab_layout.addWidget(icon_label)
            
            # 添加文本 - 弹性布局
            text_label = QLabel(name)
            text_label.setStyleSheet(f"""
                QLabel {{
                    margin-right: {25 * self.scale_ratio}px;
                }}
            """)
            text_label.setFont(QFont("Source Han Sans CN Heavy", 13 * self.scale_ratio))
            text_label.setAlignment(Qt.AlignCenter)  # 文本居中
            text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 弹性大小
            tab_layout.addWidget(text_label)
            
            # 设置标签页的布局
            self.tabs.tabBar().setTabButton(self.tabs.count()-1, QTabBar.LeftSide, tab_container)
        
        # 连接标签页切换信号
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.tabs.currentChanged.connect(self.parent.switch_tab)
        
        # 按钮位置 - 右侧
        buttons_x = (parent_width - 75 * self.scale_ratio)# * self.scale_ratio  # 距离右侧10px
        
        # 创建按钮容器
        self.buttons_container = QWidget(self)
        self.buttons_container.setGeometry(buttons_x, 10 * self.scale_ratio, 70 * self.scale_ratio, 30 * self.scale_ratio)
        
        # 按钮布局
        buttons_layout = QHBoxLayout(self.buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5 * self.scale_ratio)
        
        # 最小化按钮
        self.minimize_btn = QPushButton()
        self.minimize_btn.setFixedSize(20 * self.scale_ratio, 20 * self.scale_ratio)
        self.minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #00AA36;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: #55BB6A;
            }}
        """)
        self.minimize_btn.clicked.connect(self.parent.showMinimized)
        buttons_layout.addWidget(self.minimize_btn)
        
        # 关闭按钮
        self.close_btn = QPushButton()
        self.close_btn.setFixedSize(20 * self.scale_ratio, 20 * self.scale_ratio)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF0000;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: #F00036;
            }}
        """)
        self.close_btn.clicked.connect(self.parent.close)
        buttons_layout.addWidget(self.close_btn)
        
        # 初始更新选中标签页
        self.on_tab_changed(self.tabs.currentIndex())

    def on_tab_changed(self, index):
        """标签页切换时更新图标显示"""
        # 隐藏所有标签页的图标
        
        for i in range(self.tabs.count()):
            tab_container = self.tabs.tabBar().tabButton(i, QTabBar.LeftSide)
            if not tab_container: continue
            layout = tab_container.layout()
            if not layout: continue
            icon_label = layout.itemAt(0).widget()
            if icon_label and isinstance(icon_label, QLabel):
                icon_label.setPixmap(self.transparent_icon.pixmap(22 * self.scale_ratio, 22 * self.scale_ratio))  # self.transparent_icon.pixmap(16, 16)
                icon_label.setAlignment(Qt.AlignTop)  # 图标居中
                icon_label.setVisible(True)

            txt_label = layout.itemAt(1).widget()
            if txt_label and isinstance(txt_label, QLabel):
                txt_label.setStyleSheet(f"""
                    QLabel {{
                        margin-top: -{3 * self.scale_ratio}px;
                        margin-right: {25 * self.scale_ratio}px;
                    }}
                """)
        
        if index >= 0 and index < self.tabs.count():
            tab_container = self.tabs.tabBar().tabButton(index, QTabBar.LeftSide)
            if not tab_container: return
            layout = tab_container.layout()
            if not layout: return
            txt_label = layout.itemAt(1).widget()
            if txt_label and isinstance(txt_label, QLabel):
                txt_label.setVisible(True)
                txt_label.setStyleSheet(f"""
                    QLabel {{
                        color: #FFF;
                        margin-top: -{2 * self.scale_ratio}px;
                        margin-right: {25 * self.scale_ratio}px;
                    }}
                """)

            icon_label = layout.itemAt(0).widget()
            if icon_label and isinstance(icon_label, QLabel):
                icon_label.setPixmap(self.tab_icons["启动"].pixmap(22 * self.scale_ratio, 22 * self.scale_ratio))  # self.transparent_icon.pixmap(16, 16)
                icon_label.setVisible(True)

    
    # 窗口拖动功能实现
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件 - 开始拖动窗口"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件 - 拖动窗口"""
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件 - 停止拖动"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
