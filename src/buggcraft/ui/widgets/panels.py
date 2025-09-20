# UserPanel 类

import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QSize, QEasingCurve, QPropertyAnimation, QPoint, QRect, QParallelAnimationGroup, QTimer
from PySide6.QtGui import QFont, QPixmap, QColor, QPainter

from core.auth.microsoft import MicrosoftAuthenticator, MinecraftSignals
from ui.widgets.user_widget import QMWidget
from ui.widgets.buttons import QMButton


import logging
logger = logging.getLogger(__name__)


class UserPanel(QWidget):
    """用户面板 - 可折叠"""
    
    login_success = Signal(dict, str)  # 用户名, 登录类型
    panel_hide = Signal()  # 整体面板收起
    panel_show = Signal()  # 整体面板展开
    
    def __init__(self, parent, resource_path, cache_path):
        super().__init__(parent)
        self.parent = parent

        self.cache_path = cache_path
        self.resource_path = resource_path
        self.login_index = 0  # 第几次登录
        self.background_color = QColor(0, 0, 0, 0)  # 透明背景
        self.backgroundColor = self.background_color

        self.signals = MinecraftSignals()
        self.auth = MicrosoftAuthenticator(skins_cache_path=self.cache_path)

        # 连接认证信号
        self.auth.signals.success.connect(self.handle_auth_success)
        self.auth.signals.failure.connect(self.handle_auth_failure)
        self.auth.signals.progress.connect(self.handle_auth_progress)

        self.setFixedWidth(260)  # 固定宽度，但内部使用自适应布局
        self.init_ui()

    def save_original_geometry(self):
        """保存原始几何信息 - 确保UI已完全布局"""
        # 强制更新布局
        self.updateGeometry()
        self.layout().activate()
        
        # 等待布局完成
        QTimer.singleShot(100, self._save_geometry_after_layout)

    def _save_geometry_after_layout(self):
        """布局完成后保存几何信息"""
        self.original_size = self.size()
        self.original_pos = self.pos()
        logger.info(f"保存原始尺寸: {self.original_size}, 位置: {self.original_pos}")

    def paintEvent(self, event):
        """重绘事件 - 透明背景"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.backgroundColor)    
        super().paintEvent(event)

    def setBackgroundColor(self, color):
        """设置新的背景颜色并更新界面"""
        if isinstance(color, str):
            self.backgroundColor = QColor(color)
        else:
            self.backgroundColor = color
        self.update()

    def init_ui(self):
        # 主垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 用户信息内部布局
        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(20, 20, 20, 0)
        
        # 创建 登录信息组件
        self.login_info_widget = QWidget()
        self.login_info_widget.setFixedSize(400, 450)   
        login_info_layout = QVBoxLayout(self.login_info_widget)
        login_info_layout.setContentsMargins(0, 0, 0, 0)
        login_info_layout.setSpacing(0)
        
        # MINECRAFT图片
        self.minecraft_logo = QLabel()
        self.minecraft_logo.setAlignment(Qt.AlignCenter)
        minecraft_logo_path = os.path.abspath(os.path.join(self.resource_path, 'images', 'user', 'MINECRAFT.png'))
        if os.path.exists(minecraft_logo_path):
            minecraft_pixmap = QPixmap(minecraft_logo_path)
            if not minecraft_pixmap.isNull():
                self.minecraft_logo.setPixmap(minecraft_pixmap)
                self.minecraft_logo.setFixedSize(minecraft_pixmap.size())
                logger.info(f"MINECRAFT图片加载成功: {minecraft_logo_path}")
            else:
                logger.error(f"MINECRAFT图片加载失败: {minecraft_logo_path}")
        else:
            logger.error(f"MINECRAFT图片文件不存在: {minecraft_logo_path}")
        
        # 头像
        self.avatar = QLabel()
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setFixedSize(80, 80)
        self.avatar.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 1px solid #ffffff;
            }
        """)
        # 设置默认头像
        default_avatar_path = os.path.abspath(os.path.join(self.resource_path, 'images', 'user', 'unlogged_avatar.png'))
        if os.path.exists(default_avatar_path):
            pixmap = QPixmap(default_avatar_path)
            if not pixmap.isNull():
                self.avatar.setPixmap(pixmap.scaled(80, 80, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
                logger.info(f"初始化时加载默认头像: unlogged_avatar.png")
            else:
                logger.error(f"默认头像加载失败，图片格式可能有问题: {default_avatar_path}")
        else:
            logger.error(f"默认头像文件不存在: {default_avatar_path}")
        
        # 用户名标签
        self.username_label = QLabel("未登录")
        self.username_label.setFont(QFont("Source Han Sans CN Heavy", 12))
        self.username_label.setAlignment(Qt.AlignCenter)
        self.username_label.setStyleSheet("font-weight: bold; color: #f8f8f8;")

        # 创建正版登录按钮 
        self.legal_login_btn = self.create_image_button(
            "正版登录", 
            os.path.abspath(os.path.join(self.resource_path, 'images', 'user', 'legal_login_btn.png')),
            self.authorized_online_login,
            230, 40,   
            font_size=10
        )
        
        # 创建启动游戏按钮 
        self.start_game_btn = None
        
        # 将组件添加到登录信息组件
        login_info_layout.addWidget(self.minecraft_logo, 0, Qt.AlignCenter)
        login_info_layout.addSpacing(20)   
        login_info_layout.addWidget(self.avatar, 0, Qt.AlignCenter)
        login_info_layout.addSpacing(10)
        login_info_layout.addWidget(self.username_label, 0, Qt.AlignCenter)
        login_info_layout.addSpacing(50)  
        login_info_layout.addWidget(self.legal_login_btn, 0, Qt.AlignCenter)
        login_info_layout.addSpacing(30)   
        
        # 启动游戏按钮容器
        self.start_game_container = QWidget()
        self.start_game_layout = QVBoxLayout(self.start_game_container)
        self.start_game_layout.setContentsMargins(0, 0, 0, 0)
        self.start_game_layout.setAlignment(Qt.AlignCenter)
        login_info_layout.addWidget(self.start_game_container, 0, Qt.AlignCenter)
        
        # 登录状态标签 
        self.login_status = QLabel("请选择登录方式")
        self.login_status.setFont(QFont("Source Han Sans CN Medium", 10))
        self.login_status.setAlignment(Qt.AlignCenter)
        self.login_status.setStyleSheet("color: #808080;")

        # 添加用户信息组件
        user_layout.addStretch()
        user_layout.addWidget(self.login_status, 0, Qt.AlignCenter)
        user_layout.addSpacing(15)
        
        # 登录账户上下文（登录后显示）
        self.login_account_context = QWidget()
        login_account_layout = QVBoxLayout(self.login_account_context)
        login_account_layout.setContentsMargins(0, 0, 0, 0)
        
        self.login_switch_btn = QMButton(
            text='切换账号',
            parent=self,
            icon=os.path.abspath(os.path.join(self.resource_path, 'images', 'user', 'switch.png')),
            font_size=10,
            size=(230-230/4, 44-44/4)
        )
        self.login_switch_btn.clicked.connect(self.logout)
        
        login_account_layout.addWidget(self.login_switch_btn, 0, Qt.AlignCenter)
        login_account_layout.addSpacing(10)
        
        user_layout.addWidget(self.login_account_context, 0, Qt.AlignCenter)
        user_layout.addStretch()
        
        self.login_account_context.hide()

        # 选项卡容器
        self.tab_container = QWidget()
        tab_container_layout = QVBoxLayout(self.tab_container)
        tab_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 选项卡按钮区域
        tab_buttons_widget = QWidget()
        tab_buttons_layout = QVBoxLayout(tab_buttons_widget)   
        tab_buttons_layout.setContentsMargins(30, 20, 0, 0)
        tab_buttons_layout.setSpacing(30)   
        tab_buttons_layout.addStretch()
        
        # 离线选项卡按钮 
        self.offline_tab_btn = self.create_tab_button("离线登录", self.offline_tab_btn_clicked, size=(155, 44), font_size=10)  # 使用背景图片实际大小155x44
        tab_buttons_layout.addWidget(self.offline_tab_btn)
        
        # 正版选项卡按钮 
        self.external_tab_btn = self.create_tab_button("正版登录", self.external_tab_btn_clicked, size=(155, 44), font_size=10)  # 使用背景图片实际大小155x44
        tab_buttons_layout.addWidget(self.external_tab_btn)
        tab_buttons_layout.addStretch()
        
        # 设置初始状态：正版登录默认选中
        self.update_tab_button_style("正版登录", True)
        self.update_tab_button_style("离线登录", False)
        
        tab_container_layout.addWidget(tab_buttons_widget)
        tab_container_layout.addSpacing(20)
        
        # 选项卡内容区域
        self.tab_content = QWidget()
        tab_content_layout = QVBoxLayout(self.tab_content)
        tab_content_layout.setContentsMargins(0, 0, 0, 0)
        # tab_content_layout.setSpacing(30)
        # tab_content_layout.addStretch()
        
        # 正版登录内容
        self.external_content = self.create_external_content()
        tab_content_layout.addWidget(self.external_content)
        
        # 离线登录内容
        self.offline_content = self.create_offline_content()
        tab_content_layout.addWidget(self.offline_content)
        self.offline_content.hide()
        
        tab_container_layout.addWidget(self.tab_content)
        
        main_layout.addWidget(self.tab_container)

    def create_tab_button(self, text, click_handler, size=(155, 44), font_size=12):
        """创建选项卡按钮"""
        button = QLabel()
        button.mousePressEvent = lambda event: click_handler()
        button.setFixedSize(*size)
        
        # 初始状态 保持透明
        button.setStyleSheet("background-color: transparent;")
        
        # 添加文本
        text_label = QLabel(text, button)
        text_label.setFont(QFont("Source Han Sans CN Heavy", font_size))
        text_label.setAlignment(Qt.AlignCenter)  
        text_label.setStyleSheet("color: white; background-color: transparent;")
        text_label.setGeometry(0, 0, *size)   
        
        return button
    
    def create_external_content(self):
        """创建正版登录内容"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        layout.addStretch()
        
        return content
    
    def create_offline_content(self):
        """创建离线登录内容"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        # 用户名输入框
        self.username = QLineEdit()
        self.username.setPlaceholderText("请输入用户名")
        self.username.setFont(QFont("Source Han Sans CN Medium", 10))
        self.username.setFixedSize(230-230/4, 50-50/4)
        self.username.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 60, 60, 150);
                color: #f2f2f2;
                border: 1px solid #000;
                border-radius: 0px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.username)
        layout.addSpacing(10)
        
        # 登录按钮
        login_btn = self.create_image_button(
            "登录",
            os.path.abspath(os.path.join(self.resource_path, 'images', 'user', 'login_btn.png')),
            self.authorized_login,
            230-230/4, 45-45/4,
            font_size=10
        )
        layout.addWidget(login_btn)
        layout.addStretch()
        
        return content
    
    def create_image_button(self, text, image_path, click_handler, width, height, font_size=11):
        """创建图片按钮"""
        button = QLabel()
        button.mousePressEvent = lambda event: click_handler()
        button.setFixedSize(width, height)
        button.setPixmap(QPixmap(image_path).scaled(
            width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        ))
        
        text_label = QLabel(text, button)
        text_label.setFont(QFont("Source Han Sans CN Heavy", font_size))
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("color: #f2f2f2; background-color: transparent;")
        text_label.setGeometry(0, 0, width, height)
        
        return button
    
    def external_tab_btn_clicked(self):
        """正版登录按钮点击事件"""
        self.external_content.show()
        self.offline_content.hide()
        # 更新按钮样式：正版登录激活，离线登录透明
        self.update_tab_button_style("正版登录", True)
        self.update_tab_button_style("离线登录", False)

    def offline_tab_btn_clicked(self):
        """离线登录按钮点击事件"""
        self.external_content.hide()
        self.offline_content.show()
        # 更新按钮样式：离线登录激活，正版登录透明
        self.update_tab_button_style("正版登录", False)
        self.update_tab_button_style("离线登录", True)

    def update_tab_button_style(self, tab_name, is_active):
        """更新选项卡按钮样式"""
        if tab_name == "正版登录":
            btn = self.external_tab_btn
            active_image = os.path.abspath(os.path.join(self.resource_path, 'images', 'user', 'external_tab_btn_active.png'))
        else:
            btn = self.offline_tab_btn
            active_image = os.path.abspath(os.path.join(self.resource_path, 'images', 'user', 'external_tab_btn_active.png'))
        
        if is_active:
            # 激活状态显示背景图片
            btn.setPixmap(QPixmap(active_image).scaled(155, 44, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        else:
            # 未激活状态保持透明背景
            btn.clear()  # 清除背景图片
            btn.setStyleSheet("background-color: transparent;")

    def authorized_login(self):
        """离线登录"""
        username = self.username.text().strip()
        if not username:
            self.login_status.setText("<font color='#F44336'>请输入用户名</font>")
            return
        
        self.login_index += 1
        self.handle_auth_success(username=username, data={
            'uuid': None,
            'token': None,
            'skin': None
        })

    def authorized_online_login(self):
        """正版登录"""
        self.legal_login_btn.setEnabled(False)
        self.signals.output.emit("正在启动正版登录...")
        self.login_index += 1
        self.auth.start_login()

    def authorized_online_auto(self):
        """尝试自动登录"""
        if self.cache_path:
            if self.auth.load_credentials(os.path.join(self.cache_path)):
                logger.info(f"自动登录成功，欢迎 {self.auth.minecraft_username}!")
                return True
            else:
                logger.info("自动登录失败，需要重新认证")
                self.signals.output.emit("自动登录失败，需要重新认证")
        
        return False
    
    def resizeEvent(self, event):
        """窗口大小变化事件 - 确保布局自适应"""
        super().resizeEvent(event)

    def animations_show_user_info(self, call=None, user_hide_time=300, user_show_time=600):
        """登录成功 过度效果"""
        def ani_show_():
            if call: call()
            self.tab_container.hide()
            self.login_account_context.show()
            self.setBackgroundColor('#000')

        tab_effect = QGraphicsOpacityEffect(self.tab_container)
        self.tab_container.setGraphicsEffect(tab_effect)
        self.tab_container_out = QPropertyAnimation(tab_effect, b"opacity")
        self.tab_container_out.setDuration(user_hide_time)  # 300毫秒动画时间
        self.tab_container_out.setStartValue(1.0)
        self.tab_container_out.setEndValue(0.0)
        self.tab_container_out.setEasingCurve(QEasingCurve.OutCubic)
        self.tab_container_out.finished.connect(ani_show_)  # 动画完成后隐藏
        self.tab_container_out.start()
    
    def animations_show_user_login(self, user_hide_time=100, user_show_time=300):
        """切换账户 过度效果"""
        def ani_show_():
            self.tab_container.show()
            self.login_account_context.hide()
            self.setBackgroundColor(self.background_color)

        tab_effect = QGraphicsOpacityEffect(self.tab_container)
        self.tab_container.setGraphicsEffect(tab_effect)
        self.tab_container_out = QPropertyAnimation(tab_effect, b"opacity")
        self.tab_container_out.setDuration(user_hide_time)  # 300毫秒动画时间
        self.tab_container_out.setStartValue(0.0)
        self.tab_container_out.setEndValue(1.0)
        self.tab_container_out.setEasingCurve(QEasingCurve.OutCubic)
        self.tab_container_out.finished.connect(ani_show_)  # 动画完成后隐藏
        self.tab_container_out.start()

    def animations_show_user(self):
        """显示用户面板动画 - 父容器跟随展开"""
        # 确保有原始尺寸数据
        if not hasattr(self, 'original_size'):
            self.save_original_geometry()
            return  # 等待下一次调用
        
        logger.info(f"显示动画开始 - 原始尺寸: {self.original_size}, 位置: {self.original_pos}")
        
        # 确保控件可见
        self.show()
        
        # 先设置为0宽度和透明，以便动画展开
        self.resize(0, self.original_size.height())
        
        # # 计算并设置初始位置（向左偏移一个完整宽度）
        initial_pos = self.original_pos - QPoint(self.original_size.width(), 0)
        self.move(initial_pos)
        
        # 创建父容器透明度效果
        container_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(container_effect)
        container_effect.setOpacity(0.0)  # 初始透明度为0
        
        # 透明度动画
        self.container_opacity_animation = QPropertyAnimation(container_effect, b"opacity")
        self.container_opacity_animation.setDuration(0)
        self.container_opacity_animation.setStartValue(0.0)
        self.container_opacity_animation.setEndValue(1.0)
        self.container_opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 父容器尺寸动画 - 从0展开到原始宽度
        self.container_size_animation = QPropertyAnimation(self, b"size")
        self.container_size_animation.setDuration(30)
        self.container_size_animation.setStartValue(QSize(0, self.original_size.height()))
        self.container_size_animation.setEndValue(self.original_size)
        self.container_size_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 父容器位置动画 - 向右移动回原始位置
        self.container_pos_animation = QPropertyAnimation(self, b"pos")
        self.container_pos_animation.setDuration(0)
        self.container_pos_animation.setStartValue(initial_pos)
        self.container_pos_animation.setEndValue(self.original_pos)
        self.container_pos_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 创建并行动画组
        self.container_animation_group = QParallelAnimationGroup()
        self.container_animation_group.addAnimation(self.container_opacity_animation)
        self.container_animation_group.addAnimation(self.container_size_animation)
        self.container_animation_group.addAnimation(self.container_pos_animation)
        self.container_animation_group.finished.connect(self.on_show_animation_finished)
        
        # 启动动画
        self.container_animation_group.start()
        
    def animations_hide_user(self):
        """隐藏用户面板动画 - 父容器跟随收缩"""
        # 确保有原始尺寸数据
        if not hasattr(self, 'original_size'):
            self.save_original_geometry()
        
        # 创建父容器透明度效果
        container_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(container_effect)
        
        # 透明度动画
        self.container_opacity_animation = QPropertyAnimation(container_effect, b"opacity")
        self.container_opacity_animation.setDuration(300)
        self.container_opacity_animation.setStartValue(1.0)
        self.container_opacity_animation.setEndValue(0.0)
        self.container_opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 父容器尺寸动画 - 收缩到0宽度
        self.container_size_animation = QPropertyAnimation(self, b"size")
        self.container_size_animation.setDuration(300)
        self.container_size_animation.setStartValue(self.original_size)
        self.container_size_animation.setEndValue(QSize(0, self.original_size.height()))
        self.container_size_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 父容器位置动画 - 向左移动
        target_pos = self.original_pos - QPoint(self.original_size.width(), 0)
        self.container_pos_animation = QPropertyAnimation(self, b"pos")
        self.container_pos_animation.setDuration(300)
        self.container_pos_animation.setStartValue(self.original_pos)
        self.container_pos_animation.setEndValue(target_pos)
        self.container_pos_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 创建并行动画组
        self.container_animation_group = QParallelAnimationGroup()
        self.container_animation_group.addAnimation(self.container_opacity_animation)
        self.container_animation_group.addAnimation(self.container_size_animation)
        self.container_animation_group.addAnimation(self.container_pos_animation)
        self.container_animation_group.finished.connect(self.on_hide_animation_finished)
        
        # 启动动画
        self.container_animation_group.start()
    
    def on_hide_animation_finished(self):
        """隐藏动画完成后的回调"""
        self.tab_container.hide()
        self.panel_hide.emit()
        self.setGraphicsEffect(None)  # 移除效果
    
    def on_show_animation_finished(self):
        """显示动画完成后的回调"""
        # 确保所有子控件可见
        self.show()
        self.tab_container.show()
        if self.auth.minecraft_username:
            self.animations_show_user_info(user_hide_time=0, user_show_time=0)
        else:
            self.animations_show_user_login(user_hide_time=0, user_show_time=0)

        self.setGraphicsEffect(None)
        logger.info(f"显示动画完成 - 最终尺寸: {self.size()}, 位置: {self.pos()}")

    def moveEvent(self, event):
        """重写 moveEvent 以跟踪位置变化"""
        super().moveEvent(event)

    def init_animations(self):
        """初始化动画效果"""
        # 创建动画对象
        self.external_animation = QPropertyAnimation(self.external_content, b"geometry")
        self.offline_animation = QPropertyAnimation(self.offline_content, b"geometry")
        
        # 设置动画持续时间
        self.external_animation.setDuration(300)
        self.offline_animation.setDuration(300)
        
        # 设置缓动曲线
        self.external_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.offline_animation.setEasingCurve(QEasingCurve.OutQuad)

    def logout(self):
        """退出正版登录"""
        self.setBackgroundColor(self.backgroundColor)
        self.auth.clear(os.path.join(self.cache_path))
        self.avatar.clear()
        self.avatar.setStyleSheet(f"""
            QLabel {{
                background-color: #2b2b2b;
                border: {2}px solid #ffffff;
            }}
        """)
        self.username_label.setText("未登录")
        self.username_label.setStyleSheet(f"font-weight: bold; color: #f8f8f8;")
        self.login_status.setText("请选择登录方式")
        self.login_status.setStyleSheet(f"color: #808080;")
        self.signals.output.emit("已退出正版登录")
        self.animations_show_user_login()
        
    def collcall_login(
        self,
        uuid,
        username,
        token=None,
        login_type="online",
        skin_avatar=None
    ):
        """处理登录成功事件"""
        self.username_label.setText(username)
        self.login_status.setText(f"<font color='#4CAF50'>{'正版登录' if login_type == 'online' else '离线登录'}</font>")

        # 更新头像
        border_color = '#4CAF50'
        if not login_type == "online":
            border_color = '#2196F3'

        self.avatar.setStyleSheet(f"""
            QLabel {{
                background-color: #2b2b2b;
                border-radius: 0px;
                border: 2px solid {border_color};
            }}
        """)
        
        if not skin_avatar:
            skin_avatar=os.path.abspath(os.path.join(self.resource_path, 'images', 'user', 'unlogged_avatar.png'))

        self.avatar.setPixmap(QPixmap(skin_avatar).scaled(80, 80, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        self.login_success.emit({'uuid': uuid, 'username': username, 'token': token}, login_type)

    def is_expired_token(self):
        # 定时验证token有效性
        is_expired = self.auth.decoder.is_expired()
        if is_expired and is_expired is None:
            # token 过期
            self.logout()
            self.login_status.setText("正版授权已到有效期，需重新授权登录")

    def handle_auth_progress(self, progress):
        self.login_status.setText(f"<font color='#9e9e9e'>{progress}</font>")

    def handle_auth_success(self, username, data):
        """处理登录成功"""
        uuid = data.get('uuid')
        token = data.get('token')
        login_type = data.get('type')
        skin_avatar = data.get('skin')
        self.signals.output.emit(f"欢迎 {username}! 认证成功")

        if login_type == "online":
            # 正版时 定时验证token有效性
            QTimer.singleShot(5000, lambda: self.is_expired_token())

        # 保存认证信息
        self.auth.save_credentials(os.path.join(self.cache_path))
        
        logger.info(f"欢迎 {username}, {login_type} !")
        user_hide_time, user_show_time = 100, 200
        if self.login_index == 0:
            user_hide_time, user_show_time = 0, 0

        self.animations_show_user_info(
            call=lambda: self.collcall_login(uuid, username, token, login_type, skin_avatar),
            user_hide_time=user_hide_time,
            user_show_time=user_show_time
        )
        self.legal_login_btn.setEnabled(True)
        
    def handle_auth_failure(self, message):
        """处理登录失败"""
        self.signals.error.emit(f"登录失败: {message}")
        self.login_status.setText(message)
        self.login_status.setText(f"登录失败")
        # self.logout()
        logger.info(f'handle_auth_failure {message}')

