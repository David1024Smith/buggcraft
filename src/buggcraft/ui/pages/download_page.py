# 下载页面

# src/buggcraft/ui/pages/download_page.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QScrollArea, QFrame, QProgressBar, QPushButton)
from PySide6.QtCore import Qt, Signal
from .base_page import BasePage


class DownloadPage(BasePage):
    """下载管理页面 - 继承BasePage"""
    
    # 定义信号
    download_paused = Signal(str)  # 下载暂停信号，参数为下载项名称
    download_canceled = Signal(str)  # 下载取消信号，参数为下载项名称
    download_removed = Signal(str)  # 下载移除信号，参数为下载项名称
    
    def __init__(self, home_path, scale_ratio=1.0, parent=None):
        super().__init__(home_path, scale_ratio, parent)
        self.downloads = []  # 下载项列表
        self.init_ui()
        self.load_sample_downloads()
        
    def init_ui(self):
        """初始化UI"""
        # 设置背景
        self.set_background('resources/images/minecraft_bg.png')
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建一个内容容器，添加内边距
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("下载管理")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        content_layout.addWidget(title)
        
        # 下载列表区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        
        self.download_list_widget = QWidget()
        self.download_list_layout = QVBoxLayout(self.download_list_widget)
        self.download_list_layout.setAlignment(Qt.AlignTop)
        self.download_list_widget.setStyleSheet("background-color: transparent;")
        
        self.scroll_area.setWidget(self.download_list_widget)
        content_layout.addWidget(self.scroll_area)
        
        # 将内容容器添加到主布局
        main_layout.addWidget(content_container)
    
    def load_sample_downloads(self):
        """加载示例下载项数据"""
        self.downloads = [
            {"name": "Hypixel游戏包", "progress": 75, "speed": "1.2 MB/s", "size": "2.4 GB"},
            {"name": "Mineplex游戏包", "progress": 30, "speed": "800 KB/s", "size": "1.8 GB"},
            {"name": "SkyBlock乐园资源包", "progress": 100, "speed": "0 KB/s", "size": "350 MB"},
            {"name": "生存大陆模组包", "progress": 45, "speed": "500 KB/s", "size": "1.2 GB"},
        ]
        
        self.display_downloads()
    
    def display_downloads(self):
        """显示下载项列表"""
        # 清空现有下载项列表
        for i in reversed(range(self.download_list_layout.count())): 
            widget = self.download_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # 添加下载项
        for dl in self.downloads:
            dl_frame = QFrame()
            dl_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(53, 53, 53, 200);
                    border-radius: 8px;
                    padding: 15px;
                }
            """)
            dl_layout = QVBoxLayout(dl_frame)
            
            # 名称
            name_label = QLabel(dl["name"])
            name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
            dl_layout.addWidget(name_label)
            
            # 进度条
            progress_bar = QProgressBar()
            progress_bar.setValue(dl["progress"])
            progress_bar.setFormat(f"{dl['progress']}%")
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #444444;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #2a2a2a;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 2px;
                }
            """)
            dl_layout.addWidget(progress_bar)
            
            # 信息
            info_layout = QHBoxLayout()
            
            speed_label = QLabel(f"速度: {dl['speed']}")
            speed_label.setStyleSheet("color: #cccccc;")
            info_layout.addWidget(speed_label)
            
            size_label = QLabel(f"大小: {dl['size']}")
            size_label.setStyleSheet("color: #cccccc;")
            info_layout.addWidget(size_label)
            
            info_layout.addStretch()
            
            # 操作按钮
            if dl["progress"] < 100:
                pause_btn = QPushButton("暂停")
                pause_btn.setFixedWidth(80)
                pause_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4a4a4a;
                        color: #ffffff;
                        border: none;
                        padding: 3px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #5a5a5a;
                    }
                """)
                pause_btn.clicked.connect(lambda checked=False, name=dl["name"]: self.on_pause_download(name))
                info_layout.addWidget(pause_btn)
                
                cancel_btn = QPushButton("取消")
                cancel_btn.setFixedWidth(80)
                cancel_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #8a1c1c;
                        color: #ffffff;
                        border: none;
                        padding: 3px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #9a2c2c;
                    }
                """)
                cancel_btn.clicked.connect(lambda checked=False, name=dl["name"]: self.on_cancel_download(name))
                info_layout.addWidget(cancel_btn)
            else:
                remove_btn = QPushButton("移除")
                remove_btn.setFixedWidth(80)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4a4a4a;
                        color: #ffffff;
                        border: none;
                        padding: 3px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #5a5a5a;
                    }
                """)
                remove_btn.clicked.connect(lambda checked=False, name=dl["name"]: self.on_remove_download(name))
                info_layout.addWidget(remove_btn)
            
            dl_layout.addLayout(info_layout)
            self.download_list_layout.addWidget(dl_frame)
    
    def on_pause_download(self, name):
        """暂停下载"""
        self.download_paused.emit(name)
        # 这里可以添加实际的暂停逻辑
        
    def on_cancel_download(self, name):
        """取消下载"""
        self.download_canceled.emit(name)
        # 这里可以添加实际的取消逻辑
        
    def on_remove_download(self, name):
        """移除下载"""
        self.download_removed.emit(name)
        # 这里可以添加实际的移除逻辑
    
    def add_download(self, download):
        """添加下载项"""
        self.downloads.append(download)
        self.display_downloads()
    
    def update_download_progress(self, name, progress, speed):
        """更新下载进度"""
        for dl in self.downloads:
            if dl["name"] == name:
                dl["progress"] = progress
                dl["speed"] = speed
                break
        self.display_downloads()
    
    def complete_download(self, name):
        """标记下载完成"""
        for dl in self.downloads:
            if dl["name"] == name:
                dl["progress"] = 100
                dl["speed"] = "0 KB/s"
                break
        self.display_downloads()
    
    def remove_download(self, name):
        """移除下载项"""
        self.downloads = [dl for dl in self.downloads if dl["name"] != name]
        self.display_downloads()

