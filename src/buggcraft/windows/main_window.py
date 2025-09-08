# 主窗口

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QFrame, QMessageBox, QScrollArea, QSlider, QCheckBox, QButtonGroup, QRadioButton,
    QProgressBar
)
from PySide6.QtCore import Qt, QTimer, QUrl, QSize
from PySide6.QtGui import QPixmap, QDesktopServices, QPainter

from core.launcher import MinecraftLibLauncher
from ui.widgets.titlebar import TitleBar
from ui.widgets.buttons import QMStartButton
from ui.widgets.cards import QMCard
from ui.widgets.panels import UserPanel
from utils.helpers import scale_component
from ui.pages.singleplayer_page import SinglePlayerPage
from ui.pages.multiplayer_page import MultiplayerPage
from ui.pages.download_page import DownloadPage
from ui.pages.settings_page import SettingsPage
from ui.pages.more_page import MorePage


class MinecraftLauncher(QMainWindow):
    """主启动器界面 - PCL风格"""

    def __init__(self, HOME_PATH):
        super().__init__()
        self.HOME_PATH = HOME_PATH
        self.launcher = None  # 游戏线程
        # 原始设计尺寸（例如1920x1080）  875  (875 - 48 + 2) * self.scale_ratio
        # self.scale_ratio = scale_component(QSize(1280, 832), QSize(1280, 832))
        self.scale_ratio = scale_component(QSize(1280, 832), QSize(1280-1280/4, 832-832/4))

        # 用户信息
        self.minecraft_uuid = None
        self.minecraft_username = None
        self.minecraft_token = None
        self.minecraft_version = '1.21.8-Forge_58.1.0-OptiFine_J6_pre16'
        self.login_type = ""

        # 对应服务器客户端整合包是否下载
        self.current_server = ""
        self.current_client = False  # 游戏是否启动
        self.current_server_download = "未下载"  # 未下载 已下载 发现更新
        self.current_server_download_progress = 0  # 下载进度
        self.game_mode = "singleplayer"  # 或 "multiplayer"
        self.current_tab = "singleplayer"

        # 移除默认标题栏
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setFixedWidth(1280 * self.scale_ratio)
        self.setFixedHeight(832 * self.scale_ratio)

        # 创建并启动游戏线程
        # 初始化启动器
        self.minecraft_directory = os.path.join(self.HOME_PATH, ".minecraft")
        self.launcher = MinecraftLibLauncher(home_path=self.HOME_PATH)
        self.launcher.signals.output.connect(self.minecraft_handle_output)
        self.launcher.signals.started.connect(self.minecraft_handle_started)
        self.launcher.signals.stopped.connect(self.minecraft_handle_stopped)
        self.launcher.signals.error.connect(self.minecraft_handle_error)
        self.launcher.signals.progress.connect(self.minecraft_handle_progress)

        self.init_ui()

    def on_resize(self, event):
        """窗口大小改变事件处理"""
        # 获取当前窗口大小
        current_size = self.central_widget.size()
        
        # 缩放组件
        scale_component(
            self.original_size, 
            current_size, 
            self.image_label
        )
        
        # 调用基类方法
        super().resizeEvent(event)

    def minecraft_handle_output(self, message):
        """处理输出"""
        print('minecraft_handle_output', message)
    
    def minecraft_handle_started(self):
        """游戏启动处理"""
        def handle_status():
            self.startedplayer_page.launch_btn.set_texts(f"停止游戏", self.minecraft_version)
            self.startedplayer_page.launch_btn.set_stop_style()
            self.startedplayer_page.launch_btn.setEnabled(True)
            self.current_client = True  # 游戏启动状态：已启动

        print('minecraft_handle_started', '游戏已启动')
        QTimer.singleShot(5000, lambda: handle_status())
    
    def minecraft_handle_stopped(self, exit_code):
        """游戏停止处理"""
        def handle_status(code):
            if code == 0:
                self.user_panel.login_status.setText("<font color='#4CAF50'>游戏已正常退出</font>")
            
            self.startedplayer_page.launch_btn.set_texts("启动游戏", self.minecraft_version)
            self.startedplayer_page.launch_btn.set_start_style()
            self.startedplayer_page.launch_btn.setEnabled(True)
            self.current_client = False  # 游戏启动状态：未启动

            # 5秒后恢复状态
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: {
                self.user_panel.login_status.setText("<font color='#4CAF50'>准备就绪</font>")
                
            })

        print('minecraft_handle_stopped', f"游戏已退出，代码: {exit_code}")
        QTimer.singleShot(5000, lambda: handle_status(exit_code))
    
    def minecraft_handle_error(self, message):
        """错误处理"""
        print('minecraft_handle_error', message)
        # self.log_view.append(f"<font color='red'>{message}</font>")
        # self.start_btn.setEnabled(True)
        # self.stop_btn.setEnabled(False)
        # self.progress_bar.setVisible(False)
    
    def minecraft_handle_progress(self, progress):
        """处理进度更新"""
        print('minecraft_handle_progress', progress)
    
    # ==========================

    def init_ui(self):
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 自定义标题栏
        self.title_bar = TitleBar(self, HOME_PATH=self.HOME_PATH, scale_ratio=self.scale_ratio)
        main_layout.addWidget(self.title_bar)
        
        # 主内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 左侧用户面板
        self.user_panel = UserPanel(self, HOME_PATH=self.HOME_PATH, scale_ratio=self.scale_ratio)
        self.user_panel.login_success.connect(self.handle_login_success)
        self.user_panel.panel_hide.connect(self.user_panel.hide)
        self.user_panel.panel_show.connect(self.user_panel.show)
        self.user_panel.authorized_online_auto()
        content_layout.addWidget(self.user_panel)
        
        # 右侧内容区域
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        
        # 添加页面
        self.create_pages()
        main_layout.addWidget(content_widget)
    
    def create_pages(self):
        """创建所有页面"""
        # 单机页面
        self.startedplayer_page = SinglePlayerPage(self.HOME_PATH, self.minecraft_version, self.scale_ratio)
        self.startedplayer_page.started_changed.connect(self.launch_game)
        self.content_stack.addWidget(self.startedplayer_page)
        
        # 多人游戏页面
        self.multiplayer_page = MultiplayerPage(self.HOME_PATH, self.scale_ratio)
        self.content_stack.addWidget(self.multiplayer_page)
        
        # 下载页面
        self.download_page = DownloadPage(self.HOME_PATH, self.scale_ratio)
        self.content_stack.addWidget(self.download_page)
        
        # 设置页面
        self.settings_page = SettingsPage(self.HOME_PATH, self.scale_ratio)
        self.content_stack.addWidget(self.settings_page)
        
        # 更多页面
        self.more_page = MorePage(self.HOME_PATH, self.scale_ratio)
        self.content_stack.addWidget(self.more_page)

    def switch_tab(self, index):
        """切换标签页"""
        tab_names = ["singleplayer", "multiplayer", "download", "settings", "more"]
        self.current_tab = tab_names[index]
        self.content_stack.setCurrentIndex(index)
        if index == 0:
            self.user_panel.on_show_animation_finished()
        else:
            self.user_panel.on_hide_animation_finished()
    
    def handle_login_success(self, data, login_type):
        """处理登录成功事件"""
        self.minecraft_uuid = data.get('uuid', None)
        self.minecraft_username = data.get('username', None)
        self.minecraft_token = data.get('token', None)
        self.login_type = login_type
    
    def select_server(self, server_address):
        """选择服务器"""
        self.current_server = server_address
        self.game_mode = "multiplayer"
        
        # 选择服务器后的进入操作
        self.current_server_download = "未下载"
        self.current_server_download_progress = 0
        # self.startedplayer_page.launch_btn.set_texts("下载游戏", self.minecraft_version)
        self.title_bar.tabs.setCurrentIndex(0)  # 切换到启动
        self.launch_game()


    def closeEvent(self, event):
        self.settings_page.save_all_settings()  # 假设 settings_page 是 SettingsPage 实例
        super().closeEvent(event)

    def launch_game(self):
        """启动游戏"""
        from PySide6.QtCore import QTimer

        self.current_server_download = "已下载"
        if not self.minecraft_username:
            # self.startedplayer_page.launch_btn.set_texts(f"请先设置角色", self.minecraft_version)
            self.user_panel.login_status.setText("<font color='#F44800'>请先设置游戏角色</font>")

            # if self.current_server_download == "未下载":
            #     QTimer.singleShot(5000, lambda: self.startedplayer_page.launch_btn.set_texts("下载游戏", self.minecraft_version)) # 切换到联机大厅
            # else:
            #     QTimer.singleShot(5000, lambda: self.startedplayer_page.launch_btn.set_texts(f"启动游戏", self.minecraft_version)) # 切换到联机大厅
            return
        
        if self.current_server_download == "未下载":
            # 开始下载过程
            self.current_server_download_progress = 0
            # self.startedplayer_page.launch_btn.setEnabled(False)
            # self.startedplayer_page.launch_btn.set_texts(f"[{self.current_server_download_progress}%] 下载中...", self.minecraft_version)
            # 使用 QTimer 实现非阻塞下载模拟
            self.download_timer = QTimer()
            self.download_timer.timeout.connect(self.update_download_progress)
            self.download_timer.start(50)  # 每50毫秒更新一次进度
            return
        elif self.current_server_download == "已下载":
            if not self.current_client:
                # 游戏未启动 - 启动过程
                self.startedplayer_page.launch_btn.setEnabled(False)
                self.startedplayer_page.launch_btn.set_texts(f"启动中...", self.minecraft_version)
                self.launcher.set_language('简体中文')
                self.launcher.set_options(
                    uuid=self.minecraft_uuid,
                    username=self.minecraft_username,
                    token=self.minecraft_token,
                    server=self.current_server if self.game_mode == "multiplayer" else None,
                    version=self.minecraft_version,
                    minecraft_directory=self.minecraft_directory,
                    memory=1024
                )

                # 启动线程
                self.launcher.start()
            else:
                # 游戏已启动 - 停止过程
                self.startedplayer_page.launch_btn.set_texts(f"正在停止游戏...", self.minecraft_version)
                self.launcher.stop()
    
    def update_download_progress(self):
        """更新下载进度"""
        self.current_server_download_progress += 1
        self.startedplayer_page.launch_btn.set_texts(f"[{self.current_server_download_progress}%] 下载中...", self.minecraft_version)
        
        if self.current_server_download_progress >= 100:
            # 下载完成
            self.download_timer.stop()
            self.startedplayer_page.launch_btn.set_texts("启动游戏", self.minecraft_version)
            self.startedplayer_page.launch_btn.set_start_style()
            self.current_server_download = "已下载"
            self.startedplayer_page.launch_btn.setEnabled(True)
            # 下载完成后启动游戏
            self.launch_game()

    def show_launch_settings(self):
        """显示启动参数设置"""
        self.settings_stack.setCurrentIndex(0)
    
    def show_personalization(self):
        """显示个性化设置"""
        self.settings_stack.setCurrentIndex(1)
    
    def show_other_settings(self):
        """显示其他设置"""
        self.settings_stack.setCurrentIndex(2)
    
    def show_about(self):
        """显示关于页面"""
        self.more_stack.setCurrentIndex(0)
    
    def show_feedback(self):
        """显示反馈页面"""
        self.more_stack.setCurrentIndex(1)
    
    def submit_feedback(self):
        """提交反馈"""
        QDesktopServices.openUrl(QUrl("https://github.com/minecraft-launcher/issues"))
        QMessageBox.information(self, "提交成功", "您的反馈已提交，感谢您的支持！")
