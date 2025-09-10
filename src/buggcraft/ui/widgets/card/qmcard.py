from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
import os


import logging
logger = logging.getLogger(__name__)

class QMCard(QWidget):
    """修复标题高度的自适应卡片组件"""
    
    def __init__(self,
        title="",
        icon="",
        fonts_color="#fff",
        content_spacing=15,  # 正文边距
        background_color = QColor("rgba(50, 50, 50, 0.68)"),
        parent=None
    ):
        """
        初始化卡片组件
        
        :param title: 卡片标题
        :param icon: 标题图标路径
        :param content: 卡片内容文本
        :param parent: 父组件
        """
        super().__init__(parent)
        self.setObjectName("minecraftCard")
        self.fonts_color = fonts_color
        self.background_color = "background_color" # 初始化背景颜色，默认为黑色
        self.backgroundColor = self.background_color
        # 设置卡片样式
        self.setStyleSheet(f"""
            QWidget#minecraftCard {{
                border-radius: 4px;
                border: 1px solid #333;
                padding: 12px;
            }}
            QWidget {{
                color: {self.fonts_color};
            }}
        """)
        
        # 设置自适应高度策略
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 30)  # 上边距8px
        
        # 创建标题区域（固定高度）
        self.title_widget = self.create_title_widget(title, icon)
        self.main_layout.addWidget(self.title_widget)
        
        # 添加分隔线
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.HLine)
        self.divider.setStyleSheet("background-color: #333;")
        self.divider.setFixedHeight(1)
        self.main_layout.addWidget(self.divider)
        
        # 创建内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(28, 10, 10, 0)  # 上边距8px
        self.content_layout.setSpacing(content_spacing)
        
        self.main_layout.addWidget(self.content_widget)
    
    def paintEvent(self, event):
        """重绘事件 - 使用变量确保背景绘制"""
        painter = QPainter(self)
        # 创建 QColor 对象并设置透明度
        bg_color = QColor(50, 50, 50)  # RGB 值
        bg_color.setAlphaF(0.68)        # 设置透明度 (0.0-1.0)
        
        # 使用 QColor 填充矩形
        painter.fillRect(self.rect(), bg_color)

        # painter.fillRect(self.rect(), self.backgroundColor)  # 使用变量
        super().paintEvent(event)

    def setBackgroundColor(self, color):
        """设置新的背景颜色并更新界面
        :param color: 可以是QColor, 或者Qt.GlobalColor, 或者十六进制字符串如 '#ff0000'
        """
        if isinstance(color, str):
            self.backgroundColor = QColor(color)  # 支持字符串
        else:
            self.backgroundColor = color  # 支持QColor或Qt.GlobalColor
        self.update()  # 关键：调用update()触发paintEvent

    def create_title_widget(self, title, icon):
        """创建标题区域（固定高度）"""
        title_widget = QWidget()
        title_widget.setFixedHeight(28)  # 固定高度24px
        title_widget.setStyleSheet("background-color: transparent;")

        title_layout = QHBoxLayout(title_widget)
        title_layout.setAlignment(Qt.AlignCenter)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        # 图标
        if icon and os.path.exists(icon):
            icon_label = QLabel()
            icon_label.setStyleSheet("background-color: transparent;")
            pixmap = QPixmap(icon)
            if not pixmap.isNull():
                # 设置图标大小为16x16，居中显示
                icon_label.setPixmap(pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedSize(28, 28)  # 固定图标大小
            title_layout.addWidget(icon_label)
        elif icon:
            logger.info(f"图标文件不存在: {icon}")
        
        # 标题文本
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #f0f0f0;
                font-size: 15px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        title_layout.addWidget(title_label)
        
        # 添加伸缩空间使标题靠左
        title_layout.addStretch()
        
        return title_widget
    
    def add_widget(self, widget):
        """向内容区域添加控件"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """向内容区域添加布局"""
        self.content_layout.addLayout(layout)
    
    def set_content(self, text):
        """设置卡片内容文本"""
        # 如果内容区域已经有文本标签，更新它
        if self.content_layout.count() > 0 and isinstance(self.content_layout.itemAt(0).widget(), QLabel):
            content_label = self.content_layout.itemAt(0).widget()
            content_label.setText(text)
        else:
            # 否则创建新的文本标签
            content_label = QLabel(text)
            content_label.setStyleSheet("""
                QLabel {
                    color: #aaa;
                    font-size: 12px;
                    background-color: transparent;
                }
            """)
            content_label.setWordWrap(True)
            self.content_layout.insertWidget(0, content_label)


