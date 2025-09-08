# 单机页面

# src/buggcraft/ui/pages/singleplayer_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from ..widgets.buttons import QMStartButton
from .base_page import BasePage

class SinglePlayerPage(BasePage):
    """单机游戏页面"""
    
    def __init__(self, home_path, scale_ratio=1.0, parent=None):
        super().__init__(home_path, scale_ratio, parent)
        self.minecraft_version = ""  # 将在外部设置
        self.launch_btn = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 设置背景
        self.set_background('resources/images/minecraft_bg.png')
        self.setContentsMargins(0, 20, 0, 0)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建一个垂直布局容器，用于放置内容
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加一个弹簧将内容推到底部
        content_layout.addStretch(1)
        
        # 添加半透明遮罩层，使文字更易读
        overlay = QWidget()
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建启动按钮
        self.launch_btn = QMStartButton(scale_ratio=self.scale_ratio)
        self.launch_btn.set_texts('启动游戏', self.minecraft_version)
        overlay_layout.addWidget(self.launch_btn, 0, Qt.AlignCenter)
        
        content_layout.addWidget(overlay)
        
        # 将内容容器添加到主布局
        main_layout.addWidget(content_container)
    
    def set_minecraft_version(self, version):
        """设置Minecraft版本"""
        self.minecraft_version = version
        if self.launch_btn:
            self.launch_btn.set_texts('启动游戏', version)
    
    def connect_launch_handler(self, handler):
        """连接启动按钮的点击处理器"""
        if self.launch_btn:
            self.launch_btn.clicked.connect(handler)
