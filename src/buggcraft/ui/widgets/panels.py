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


class UserPanel(QWidget):
    """用户面板 - 可折叠"""
    login_success = Signal(dict, str)  # 用户名, 登录类型
    panel_hide = Signal()  # 整体面板收起
    panel_show = Signal()  # 整体面板展开
    
    def __init__(self, parent, HOME_PATH, scale_ratio=1):
        super().__init__(parent)
        self.HOME_PATH = HOME_PATH
        self.parent = parent
        self.scale_ratio = scale_ratio
        self.is_collapsed = False
        self.login_index = 0  # 第几次登录
        self.background_color = QColor("#272727")  # 初始化背景颜色，默认为黑色
        self.backgroundColor = self.background_color
        self.minecraft_directory = os.path.abspath(os.path.join(self.HOME_PATH, '.minecraft'))

        self.signals = MinecraftSignals()
        self.auth = MicrosoftAuthenticator(minecraft_directory=self.minecraft_directory)

        # 连接认证信号
        self.auth.signals.success.connect(self.handle_auth_success)
        self.auth.signals.failure.connect(self.handle_auth_failure)
        self.auth.signals.progress.connect(self.signals.output)

        self.setFixedWidth(360 * self.scale_ratio)  # 380
        self.init_ui()

        # 保存原始尺寸和位置（在UI初始化后）
        self.save_original_geometry()  # 延迟执行以确保尺寸已确定

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
        print(f"保存原始尺寸: {self.original_size}, 位置: {self.original_pos}")

    def paintEvent(self, event):
        """重绘事件 - 使用变量确保背景绘制"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.backgroundColor)  # 使用变量
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

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 背景区域 加载背景图片
        self.user = QMWidget(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'user_info_bg.png'))) # 使用自定义的Widget
        self.main_layout.addWidget(self.user, 0, Qt.AlignCenter)  # 用户信息区域水平居中

        # 用户信息区域
        self.user_info = QVBoxLayout(self.user)
        self.user_info.setContentsMargins(10 * self.scale_ratio, 20 * self.scale_ratio, 10 * self.scale_ratio, 0)
        
        # 用户头像
        self.avatar = QLabel()
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setFixedSize(80 * self.scale_ratio, 80 * self.scale_ratio)
        self.avatar.setStyleSheet(f"""
            QLabel {{
                background-color: #2b2b2b;
                border: {2 * self.scale_ratio}px solid #ffffff;
            }}
        """)
        
        # 用户名标签
        self.username_label = QLabel("未登录")
        self.username_label.setFont(QFont("Source Han Sans CN Heavy", 14 * self.scale_ratio))
        self.username_label.setAlignment(Qt.AlignCenter)
        self.username_label.setStyleSheet("font-weight: bold; color: #f8f8f8;")

        # 登录状态标签
        self.login_status = QLabel("请选择登录方式")
        self.login_status.setFont(QFont("Source Han Sans CN Medium", 12 * self.scale_ratio))
        self.login_status.setAlignment(Qt.AlignCenter)
        self.login_status.setStyleSheet(f"color: #808080;")

        # 添加布局
        self.user_info.addStretch()  # 权重可根据效果调整
        self.user_info.addWidget(self.avatar, 0, Qt.AlignCenter)  # 用户信息区域水平居中
        self.user_info.addSpacing(25 * self.scale_ratio)  # 在头像和用户名之间添加10像素的空白
        self.user_info.addWidget(self.username_label, 0, Qt.AlignCenter)  # 用户信息区域水平居中
        self.user_info.addSpacing(5 * self.scale_ratio)  # 在头像和用户名之间添加10像素的空白
        self.user_info.addWidget(self.login_status, 0, Qt.AlignCenter)  # 用户信息区域水平居中
        self.user_info.addSpacing(15 * self.scale_ratio)  # 在头像和用户名之间添加10像素的空白
        self.user_info.addStretch()  # 权重可根据效果调整

        ####################################################
        # 登录成功后切换账号
        ####################################################
        self.login_account_context = QWidget()
        self.login_account_bbox = QVBoxLayout(self.login_account_context)
        self.login_account_bbox.setContentsMargins(0, 0, 0, 0)

        self.login_switch_btn = QMButton(
            text='切换账号',
            parent=self,
            icon = os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'switch.png')),
            scale_ratio=self.scale_ratio
        )
        self.login_switch_btn.clicked.connect(self.logout)

        self.version_ = QWidget()
        self.user_version = QHBoxLayout(self.version_)
        
        self.version_selection_btn = QMButton(
            text='版本选择',
            parent=self,
            size=(115, 38),
            font_size=12,
            icon_after=True,
            offset_right=10,
            icon_size=(17 - 4, 10 - 4),
            icon = os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'options.png')),
            scale_ratio=self.scale_ratio
        )
        # 版本设置 Switch account
        self.version_settings_btn = QMButton(
            text='版本设置',
            parent=self,
            size=(115, 38),
            font_size=12,
            scale_ratio=self.scale_ratio
        )

        self.user_version.setContentsMargins(0, 0, 0, 0)
        self.user_version.addWidget(self.version_selection_btn, 0, Qt.AlignCenter)  # 用户信息区域水平居中
        self.user_version.addSpacing(5 * self.scale_ratio)
        self.user_version.addWidget(self.version_settings_btn, 0, Qt.AlignCenter)  # 用户信息区域水平居中
        
        self.login_account_bbox.addWidget(self.login_switch_btn, 0, Qt.AlignCenter)
        self.login_account_bbox.addSpacing(10 * self.scale_ratio)
        self.login_account_bbox.addWidget(self.version_, 0, Qt.AlignCenter)

        self.user_info.addWidget(self.login_account_context, 0, Qt.AlignCenter)  # 用户信息区域水平居中
        self.user_info.addStretch()  # 权重可根据效果调整
        self.login_account_context.hide()

        ####################################################

        # 登录方式选项卡容器
        self.tab_container = QWidget()
        self.tab_container.setFixedSize(360 * self.scale_ratio, 856 * self.scale_ratio)  # 固定大小

        # 选项卡按钮容器
        self.tab_buttons_container = QWidget(self.tab_container)
        self.tab_buttons_container.setGeometry(0, 30 * self.scale_ratio, 360 * self.scale_ratio, 54 * self.scale_ratio)  # 距离顶部6px
        
        ###############
        # 正版 #
        # self.version_settings_btn = QMButton(
        #     text='正版',
        #     parent=self,
        #     size=(115, 38),
        #     font_size=12,
        #     scale_ratio=self.scale_ratio
        # )

        self.external_tab_btn = QLabel(self.tab_buttons_container)
        self.external_tab_btn.mousePressEvent = lambda event: self.external_tab_btn_clicked()
        self.external_tab_btn.setGeometry((50-1) * self.scale_ratio, 0, 124 * self.scale_ratio, 48 * self.scale_ratio)
        self.external_tab_btn.setPixmap(QPixmap(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'external_tab_btn.png'))).scaled(124 * self.scale_ratio, 48 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        online_text = QLabel('正版', self.external_tab_btn)
        online_text.setFont(QFont("Source Han Sans CN Heavy", 12 * self.scale_ratio))
        online_text.setGeometry(4 * self.scale_ratio, 4 * self.scale_ratio, 124 * self.scale_ratio, 48 * self.scale_ratio)
        online_text.setAlignment(Qt.AlignCenter)
        online_text.setStyleSheet(f"""
            QLabel {{
                color: white;
                background-color: transparent;
            }}
        """)

        ###############
        # 离线 #
        self.offline_tab_btn = QLabel(self.tab_buttons_container)
        self.offline_tab_btn.mousePressEvent = lambda event: self.offline_tab_btn_clicked()
        self.offline_tab_btn.setGeometry((50 -1 + 124) * self.scale_ratio, 0, 124 * self.scale_ratio, 48 * self.scale_ratio)
        self.offline_tab_btn.setPixmap(QPixmap(
            os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'offline_tab_btn.png'))
        ).scaled(124 * self.scale_ratio, 48 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        offline_text = QLabel('离线', self.offline_tab_btn)
        offline_text.setFont(QFont("Source Han Sans CN Heavy", 12 * self.scale_ratio))
        offline_text.setGeometry(4 * self.scale_ratio, 4 * self.scale_ratio, 124 * self.scale_ratio, 48 * self.scale_ratio)
        offline_text.setAlignment(Qt.AlignCenter)
        offline_text.setStyleSheet(f"""
            QLabel {{
                color: white;
                background-color: transparent;
            }}
        """)

        # 选项卡内容区域
        self.tab_content = QWidget(self.tab_container)
        self.tab_content.setGeometry(0, 76 * self.scale_ratio, 360 * self.scale_ratio, 250 * self.scale_ratio)  # 距离顶部50px
        
        ###############
        # 外置登录内容 #
        self.external_content = QWidget(self.tab_content)
        self.external_content.setGeometry(0, 0, 360 * self.scale_ratio, 250 * self.scale_ratio)
        
        # 正版登录
        # self.legal_login_btn = QMButton(
        #     text='正版授权登录',
        #     parent=self.external_content,
        #     size=(240, 54),
        #     background_image=os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'legal_login_btn.png')),
        #     font_size=12,
        #     scale_ratio=self.scale_ratio
        # )
        # self.legal_login_btn.clicked.connect(self.authorized_online_login)

        self.legal_login_btn = QLabel(self.external_content)
        self.legal_login_btn.mousePressEvent = lambda event: self.authorized_online_login()
        self.legal_login_btn.setGeometry(57 * self.scale_ratio, 37 * self.scale_ratio, 240 * self.scale_ratio, 54 * self.scale_ratio)  # x=57, y=64, width=240, height=30
        self.legal_login_btn.setPixmap(QPixmap(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'legal_login_btn.png'))).scaled(240 * self.scale_ratio, 54 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        self.online_text = QLabel('正版授权登录', self.legal_login_btn)
        self.online_text.setFont(QFont("Source Han Sans CN Heavy", 12 * self.scale_ratio))
        self.online_text.setGeometry(0, 0, 240 * self.scale_ratio, 54 * self.scale_ratio)
        self.online_text.setAlignment(Qt.AlignCenter)
        self.online_text.setStyleSheet(f"""
            QLabel {{
                color: #f2f2f2;
                background-color: transparent;
            }}
        """)

        ##########################
        # 外置登录内容（初始隐藏） #
        self.offline_content = QWidget(self.tab_content)
        self.offline_content.setGeometry(0, 0, 360 * self.scale_ratio, 250 * self.scale_ratio)
        self.offline_content.hide()

        # 用户名输入框
        self.username = QLineEdit(self.offline_content)
        self.username.setPlaceholderText("请输入用户名")
        self.username.setFont(QFont("Source Han Sans CN Medium", 12 * self.scale_ratio))
        self.username.setGeometry(57 * self.scale_ratio, 37 * self.scale_ratio, 240 * self.scale_ratio, 50 * self.scale_ratio)  # x=57, y=64, width=240, height=30
        self.username.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(60, 60, 60, 150);
                color: #f2f2f2;
                border: {1 * self.scale_ratio}px solid #000;
                border-radius: 0px;
                padding: {8 * self.scale_ratio}px;
            }}
        """)

        # 登录按钮
        self.login_btn = QLabel(self.offline_content)
        self.login_btn.mousePressEvent = lambda event: self.authorized_login()
        self.login_btn.setGeometry(57 * self.scale_ratio, (50+26+37) * self.scale_ratio, 240 * self.scale_ratio, 45 * self.scale_ratio)
        self.login_btn.setPixmap(QPixmap(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'login_btn.png'))).scaled(240 * self.scale_ratio, 45 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        online_text = QLabel('登录', self.login_btn)
        online_text.setFont(QFont("Source Han Sans CN Heavy", 13 * self.scale_ratio))
        online_text.setGeometry(0, 0, 240 * self.scale_ratio, 45 * self.scale_ratio)
        online_text.setAlignment(Qt.AlignCenter)
        online_text.setStyleSheet(f"""
            QLabel {{
                color: #f2f2f2;
                background-color: transparent;
            }}
        """)
        
        # # 外置登录 TODO 默认关闭
        # self.third_login_btn = QLabel(self.offline_content)
        # # self.third_login_btn.mousePressEvent = lambda event: self.authorized_online_login()
        # self.third_login_btn.setGeometry(57 * self.scale_ratio, (50+26+37+35+14 + 10) * self.scale_ratio, 240 * self.scale_ratio, 49 * self.scale_ratio)
        # self.third_login_btn.setPixmap(QPixmap(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'legal_login_btn.png'))).scaled(240 * self.scale_ratio, 49 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        # self.third_text = QLabel('外置登录', self.third_login_btn)
        # self.third_text.setFont(QFont("Source Han Sans CN Heavy", 13 * self.scale_ratio))
        # self.third_text.setGeometry(0, 0, 240 * self.scale_ratio, 49 * self.scale_ratio)
        # self.third_text.setAlignment(Qt.AlignCenter)
        # self.third_text.setStyleSheet(f"""
        #     QLabel {{
        #         color: #f2f2f2;
        #     }}
        # """)

        self.main_layout.addWidget(self.tab_container, 0, Qt.AlignCenter)  # 选项卡容器水平居中
        # 添加动画效果
        self.init_animations()

    def animations_show_user_info(self, call=None, user_hide_time=300, user_show_time=600):
        """登录成功 过度效果"""
        def ani_show_():
            if call: call()
            background_path = os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'user-login-success.png'))
            self.user.background_pixmap = QPixmap(background_path)
            self.user.update()

            self.tab_container.hide()
            self.login_account_context.show()
            self.user.show()
            self.setBackgroundColor('#000')

        user_effect = QGraphicsOpacityEffect(self.user)
        self.user.setGraphicsEffect(user_effect)
        self.user_hide = QPropertyAnimation(user_effect, b"opacity")
        self.user_hide.setDuration(user_hide_time)  # 300毫秒动画时间
        self.user_hide.setStartValue(1.0)
        self.user_hide.setEndValue(0.0)
        self.user_hide.setEasingCurve(QEasingCurve.OutCubic)

        tab_effect = QGraphicsOpacityEffect(self.tab_container)
        self.tab_container.setGraphicsEffect(tab_effect)
        self.tab_container_out = QPropertyAnimation(tab_effect, b"opacity")
        self.tab_container_out.setDuration(user_hide_time)  # 300毫秒动画时间
        self.tab_container_out.setStartValue(1.0)
        self.tab_container_out.setEndValue(0.0)
        self.tab_container_out.setEasingCurve(QEasingCurve.OutCubic)
        self.tab_container_out.finished.connect(ani_show_)  # 动画完成后隐藏

        self.user.setGraphicsEffect(user_effect)
        self.user_show = QPropertyAnimation(user_effect, b"opacity")
        self.user_show.setDuration(user_show_time)  # 300毫秒动画时间
        self.user_show.setStartValue(0.0)
        self.user_show.setEndValue(1.0)
        self.user_show.setEasingCurve(QEasingCurve.InCubic)
        self.user_show.finished.connect(self.user.show)

        self.user_hide.start()
        self.user_show.start()
        self.tab_container_out.start()
    
    def animations_show_user_login(self, user_hide_time=100, user_show_time=300):
        """切换账户 过度效果"""
        def ani_show_():
            background_path = os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'user_info_bg.png'))
            self.user.background_pixmap = QPixmap(background_path)
            self.user.update()

            self.user.show()
            self.tab_container.show()
            self.login_account_context.hide()
            self.setBackgroundColor(self.background_color)

        user_effect = QGraphicsOpacityEffect(self.user)
        self.user.setGraphicsEffect(user_effect)
        self.user_hide = QPropertyAnimation(user_effect, b"opacity")
        self.user_hide.setDuration(user_hide_time)  # 300毫秒动画时间
        self.user_hide.setStartValue(1.0)
        self.user_hide.setEndValue(0.0)
        self.user_hide.setEasingCurve(QEasingCurve.OutCubic)

        tab_effect = QGraphicsOpacityEffect(self.tab_container)
        self.tab_container.setGraphicsEffect(tab_effect)
        self.tab_container_out = QPropertyAnimation(tab_effect, b"opacity")
        self.tab_container_out.setDuration(user_hide_time)  # 300毫秒动画时间
        self.tab_container_out.setStartValue(0.0)
        self.tab_container_out.setEndValue(1.0)
        self.tab_container_out.setEasingCurve(QEasingCurve.OutCubic)
        self.tab_container_out.finished.connect(ani_show_)  # 动画完成后隐藏

        self.user.setGraphicsEffect(user_effect)
        self.user_show = QPropertyAnimation(user_effect, b"opacity")
        self.user_show.setDuration(user_show_time)  # 300毫秒动画时间
        self.user_show.setStartValue(0.0)
        self.user_show.setEndValue(1.0)
        self.user_show.setEasingCurve(QEasingCurve.InCubic)
        self.user_show.finished.connect(self.user.show)

        self.user_hide.start()
        self.user_show.start()
        self.tab_container_out.start()

    def animations_show_user(self):
        """显示用户面板动画 - 父容器跟随展开"""
        # 确保有原始尺寸数据
        if not hasattr(self, 'original_size'):
            self.save_original_geometry()
            return  # 等待下一次调用
        
        print(f"显示动画开始 - 原始尺寸: {self.original_size}, 位置: {self.original_pos}")
        
        # 确保控件可见
        self.show()
        self.user.hide()
        
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
        # self.on_show_animation_finished()
        

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
        # 隐藏后重置为原始尺寸和位置，以便下次显示时使用
        self.resize(self.original_size)
        self.move(self.original_pos)
        self.setGraphicsEffect(None)  # 移除效果
    
    def on_show_animation_finished(self):
        """显示动画完成后的回调"""
        # 确保所有子控件可见
        self.show()
        self.user.show()
        self.tab_container.show()
        if self.auth.minecraft_username:
            self.animations_show_user_info(user_hide_time=0, user_show_time=0)
        else:
            self.animations_show_user_login(user_hide_time=0, user_show_time=0)

        self.setGraphicsEffect(None)
        print(f"显示动画完成 - 最终尺寸: {self.size()}, 位置: {self.pos()}")

    def resizeEvent(self, event):
        """重写 resizeEvent 以跟踪尺寸变化"""
        super().resizeEvent(event)

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
    
    def external_tab_btn_clicked(self):
        """外置登录按钮点击事件 - 添加过渡效果"""
        # 如果已经是外置登录内容显示，则无需切换
        if self.external_content.isVisible():
            return

        def offline_finished():
            self.offline_tab_btn.setPixmap(QPixmap(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'offline_tab_btn.png'))).scaled(124 * self.scale_ratio, 48 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            self.offline_content.hide()

        def external_finished():
            self.external_tab_btn.setPixmap(QPixmap(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'external_tab_btn.png'))).scaled(124 * self.scale_ratio, 48 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            self.external_content.show()

        QTimer.singleShot(50, offline_finished) # 切换到联机大厅
        QTimer.singleShot(50, external_finished) # 切换到联机大厅

        self.offline_animation.setStartValue(self.offline_content.geometry())
        self.offline_animation.setEndValue(QRect(-360, 0, 360, 250))
        
        # 设置动画起始位置 - 外置内容从右侧移入
        self.external_content.setGeometry(360, 0, 360, 250)
        self.external_content.show()
        self.external_animation.setStartValue(self.external_content.geometry())
        self.external_animation.setEndValue(QRect(0, 0, 360, 250))
        
        # 动画完成后隐藏离线内容
        self.offline_animation.finished.connect(lambda: self.offline_content.hide())
        self.external_animation.finished.connect(lambda: self.external_content.show())

        # 启动动画
        self.offline_animation.start()
        self.external_animation.start()
    
    def offline_tab_btn_clicked(self):
        """离线登录按钮点击事件 - 添加过渡效果"""
        # 如果已经是离线登录内容显示，则无需切换
        if self.offline_content.isVisible():
            return
        
        def offline_finished():
            self.offline_tab_btn.setPixmap(QPixmap(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'external_tab_btn.png'))).scaled(124 * self.scale_ratio, 48 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            self.offline_content.show()

        def external_finished():
            self.external_tab_btn.setPixmap(QPixmap(os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'offline_tab_btn.png'))).scaled(124 * self.scale_ratio, 48 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            self.external_content.hide()

        QTimer.singleShot(50, offline_finished) # 切换到联机大厅
        QTimer.singleShot(50, external_finished) # 切换到联机大厅

        # 设置动画起始位置 - 外置内容向左移出
        self.external_animation.setStartValue(self.external_content.geometry())
        self.external_animation.setEndValue(QRect(360, 0, 360, 250))
        
        # 设置动画起始位置 - 离线内容从右侧移入
        self.offline_content.setGeometry(-360, 0, 360, 250)
        self.offline_content.show()
        self.offline_animation.setStartValue(self.offline_content.geometry())
        self.offline_animation.setEndValue(QRect(0, 0, 360, 250))
        
        # 动画完成后隐藏外置内容
        self.offline_animation.finished.connect(lambda: self.offline_content.show())
        self.external_animation.finished.connect(lambda: self.external_content.hide())

        # 启动动画
        self.external_animation.start()
        self.offline_animation.start()

    def authorized_login(self):
        """离线和外置登录"""
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
    
    def authorized_online_login(self,):
        """正版登录 - 打开浏览器进行认证"""
        self.signals.output.emit("正在启动正版登录...")
        self.online_text.setText("正在启动正版登录...")
        QTimer.singleShot(1000, lambda: self.online_text.setText("等待结果响应..."))
        self.login_index += 1
        self.auth.start_login()

    def authorized_online_auto(self):
        """尝试自动登录"""
        if self.minecraft_directory:
            if self.auth.load_credentials(os.path.join(self.minecraft_directory)):
                print(f"自动登录成功，欢迎 {self.auth.minecraft_username}!")
                return True
            else:
                print("自动登录失败，需要重新认证")
                self.signals.output.emit("自动登录失败，需要重新认证")
        
        return False
    
    def logout(self):
        """退出正版登录"""
        self.setBackgroundColor(self.backgroundColor)
        self.auth.clear(os.path.join(self.minecraft_directory))
        self.avatar.clear()
        self.avatar.setStyleSheet(f"""
            QLabel {{
                background-color: #2b2b2b;
                border: {2 * self.scale_ratio}px solid #ffffff;
            }}
        """)
        self.username_label.setText("未登录")
        self.username_label.setStyleSheet(f"font-weight: bold; color: #f8f8f8;")
        self.login_status.setText("请选择登录方式")
        self.login_status.setStyleSheet(f"color: #808080;")
        self.signals.output.emit("已退出正版登录")
        self.animations_show_user_login()
        
    def set_login_status(
        self,
        uuid,
        username,
        token=None,
        login_type="online",
        skin_avatar=None
    ):
        """处理登录成功事件"""
        self.username_label.setText(username)
        status_text = f"<font color='#4CAF50'>{'正版登录' if login_type == 'online' else '离线登录'}</font>"
        self.login_status.setText(status_text)

        # 更新头像
        if login_type == "online":
            # 正版用户显示头像
            self.avatar.setStyleSheet(f"""
                QLabel {{
                    background-color: #2b2b2b;
                    border-radius: 0px;
                    border: {2 * self.scale_ratio}px solid #4CAF50;
                }}
            """)
            self.online_text.setText("正版登录")
            # 保存认证信息
            if self.minecraft_directory:
                self.auth.save_credentials(os.path.join(self.minecraft_directory))
        else:
            # 离线用户显示默认头像
            self.avatar.setStyleSheet(f"""
                QLabel {{
                    background-color: #2b2b2b;
                    border-radius: 0px;
                    border: {2 * self.scale_ratio}px solid #2196F3;
                }}
            """)
        
        if not skin_avatar:
            skin_avatar=os.path.abspath(os.path.join(self.HOME_PATH, 'resources', 'images', 'user', 'head.png'))

        self.avatar.setPixmap(QPixmap(skin_avatar).scaled(80 * self.scale_ratio, 80 * self.scale_ratio, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        # 通知主窗口
        self.login_success.emit({
            'uuid': uuid,
            'username': username,
            'token': token
        }, login_type)

    def is_expired_token(self):
        # 定时验证token有效性
        is_expired = self.auth.decoder.is_expired()
        if is_expired and is_expired is None:
            # token 过期
            self.logout()
            self.login_status.setText("正版授权已到有效期，需重新授权登录")

    def handle_auth_success(self, username, data):
        """处理登录成功"""
        uuid = data.get('uuid')
        token = data.get('token')
        skin_avatar = data.get('skin')
        self.signals.output.emit(f"欢迎 {username}! 认证成功")

        login_type = "online"
        if not token:
            self.auth.minecraft_uuid = None
            self.auth.minecraft_username = username
            self.auth.minecraft_token = None
            self.auth.minecraft_skin = None
            login_type = "offline"
        else:
            # 正版时 定时验证token有效性
            QTimer.singleShot(5000, lambda: self.is_expired_token())

        # 保存认证信息
        if self.minecraft_directory:
            self.auth.save_credentials(os.path.join(self.minecraft_directory))
        
        print(f"欢迎 {username}!")
        user_hide_time, user_show_time = 100, 200
        if self.login_index == 0:
            user_hide_time, user_show_time = 0, 0

        self.animations_show_user_info(
            call=lambda: self.set_login_status(uuid, username, token, login_type, skin_avatar),
            user_hide_time=user_hide_time,
            user_show_time=user_show_time
        )
        
    def handle_auth_failure(self, message):
        """处理登录失败"""
        self.signals.error.emit(f"登录失败: {message}")
        self.login_status.setText(message)
        self.online_text.setText(f"登录失败")

