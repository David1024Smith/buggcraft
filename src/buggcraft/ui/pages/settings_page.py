# 设置页面

import os
from typing import Any, Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QStackedWidget, QLineEdit, QPlainTextEdit,
    QCheckBox, QComboBox, QSpinBox, QSlider, QGroupBox,
    QRadioButton, QButtonGroup, QScrollArea, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from .base_page import BasePage
from utils.helpers import MemorySliderManager
from config.settings import get_settings_manager
from config.javafinder import JavaPathFinder


class SettingsPage(BasePage):
    """设置页面 - 继承BasePage"""
    
    # 定义信号
    settings_changed = Signal(str, object)  # 设置改变信号，参数为设置键和值
    
    def __init__(self, home_path, scale_ratio=1.0, parent=None):
        super().__init__(home_path, scale_ratio, parent)
        self.settings_manager = get_settings_manager(home_path)  # 获取配置管理器
        self.init_ui()
        # 加载设置
        self.load_settings_to_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 设置背景
        self.set_background('resources/images/minecraft_bg.png')
        
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧导航
        nav_frame = QFrame()
        nav_frame.setFixedWidth(200)
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: #252325;
                border-radius: 0px;
                padding: 15px;
            }
        """)
        nav_layout = QVBoxLayout(nav_frame)
        
        nav_buttons = [
            ("启动选项", self.show_launch_settings),
            # ("个性化", self.show_personalization),
            # ("其他", self.show_other_settings)
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
        
        # 右侧设置内容
        self.settings_stack = QStackedWidget()
        self.settings_stack.setContentsMargins(5, 5, 5, 5)
        # self.settings_stack.setStyleSheet("""
        #     QStackedWidget {
        #         border-radius: 8px;
        #     }
        # """)
        main_layout.addWidget(self.settings_stack)
        
        # 添加设置页面
        self.create_launch_settings()
        # self.create_personalization_settings()
        # self.create_other_settings()
    
    def create_launch_settings(self):
        """创建启动选项设置页面"""
        # 创建滚动区域以容纳所有设置
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # scroll_area.setStyleSheet("""
        #     QScrollArea {
        #         background-color: #252627;
        #         color: #AEAEAE;
        #     }
        # """)
        scroll_area.setStyleSheet("background-color: transparent;")

        import os
        from ui.widgets.card.qmcard import QMCard
        from ui.widgets.slider import StepSlider

        main_layout = QWidget()
        main_layout.setStyleSheet("background-color: transparent;")
        # main_layout.setStyleSheet("""
        # QWidget {
        #     background-color: #252627;
        #     color: #AFAFAF;
        # }
        # """)

        layout = QVBoxLayout(main_layout)
        # layout.setContentsMargins(15, 15, 15, 15)
        
        ######################################################
        crad_widget = QMCard(
            title="启动选项",
            icon=os.path.join(self.home_path, "resources/icons/union@2x.png")
        )
        crad_widget.setBackgroundColor("#252627")
        crad_widget.setStyleSheet("""
            QWidget {
                background-color: #252627;
                color: #AFAFAF;
            }
        """)
        
        ####################
        # 启动器可见性：选项 #
        launcher_visibility_layout = QFormLayout()
        self.launcher_visibility_combo = QComboBox()  # 使用唯一变量名
        self.launcher_visibility_combo.addItems(["游戏启动后保持不变", "游戏启动后最小化", "游戏启动后隐藏，游戏退出后重新打开", "游戏启动后立即关闭"])
        self.launcher_visibility_combo.currentTextChanged.connect(
            lambda t: self.on_setting_changed("launcher.visibility", t)
        )

        launcher_visibility_layout.addRow("启动器可见性", self.launcher_visibility_combo)
        ###################
        # 进程优先级: 选项 #
        self.process_priority_combo = QComboBox()  # 使用唯一变量名
        self.process_priority_combo.addItems(["高 (优先保证游戏运行，但可能造成其他程序卡顿)", "中 (平衡)", "低 (优先保证其他程序运行，但可能造成游戏卡顿)"])
        self.process_priority_combo.currentTextChanged.connect(
            lambda t: self.on_setting_changed("launcher.process_priority", t)
        )
        launcher_visibility_layout.addRow("进程优先级", self.process_priority_combo)
        #################
        # 窗口大小: 选项 #
        self.window_size_combo = QComboBox()  # 使用唯一变量名
        self.window_size_combo.addItems(["默认", "与启动器一致", "最大化"])
        self.window_size_combo.currentTextChanged.connect(
            lambda t: self.on_setting_changed("launcher.window_size", t)
        )
        launcher_visibility_layout.addRow("窗口大小", self.window_size_combo)

        #################
        # 游戏Java: 选项 #
        #################
        self.game_java_combo = QComboBox()  # 使用唯一变量名
        self.game_java_combo.addItems(["自动选择合适的Java"])
        self.game_java_combo.currentTextChanged.connect(
            lambda t: self.on_setting_changed("java.path", t)
        )
        launcher_visibility_layout.addRow("游戏Java", self.game_java_combo)

        # 在选项框下方添加按钮行
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        button_layout.setSpacing(8)  # 按钮间距

        # 自动搜索按钮
        self.auto_search_button = QPushButton("自动搜索")
        self.auto_search_button.setFixedHeight(25)  # 固定高度
        self.auto_search_button.setFixedWidth(80)
        self.auto_search_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                font-size: 12px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.auto_search_button.clicked.connect(self.auto_search_java)
        button_layout.addWidget(self.auto_search_button)

        # 手动导入按钮  TODO: 待实现
        manual_import_button = QPushButton("手动导入")
        manual_import_button.setFixedHeight(25)  # 固定高度
        manual_import_button.setFixedWidth(80)
        manual_import_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                font-size: 12px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        # manual_import_button.clicked.connect(self.manual_import_java)
        # button_layout.addWidget(manual_import_button)
        button_layout.addStretch()
        # 添加按钮行到表单布局（空标签占位第一列）
        launcher_visibility_layout.addRow("", button_container)  # 空标签使按钮对齐下拉框

        # 将表单布局添加到卡片的内容区域
        crad_widget.add_layout(launcher_visibility_layout)
        layout.addWidget(crad_widget)
        # 添加间隔 - 方法2：使用透明占位控件（更可靠）
        spacer = QWidget()
        spacer.setFixedHeight(10)
        spacer.setStyleSheet("background-color: transparent;")
        layout.addWidget(spacer)
        

        ################
        crad_game_memory_widget = QMCard(
            title="游戏内存",
            icon=os.path.join(self.home_path, "resources/icons/union@2x.png"),
            # content="这是一个Minecraft服务器，支持多种游戏模式。"
        )
        crad_game_memory_widget.setBackgroundColor("#252627")
        crad_game_memory_widget.setStyleSheet("""
            QWidget {
                background-color: #252627;
                color: #AFAFAF;
            }
        """)
        ###############
        # 创建内存滑块 #
        ###############
        # 创建步长滑块
        game_memory_layout = QFormLayout()
        self.memory_slider = StepSlider(step=512, orientation=Qt.Horizontal)
        self.memory_slider.setTickPosition(QSlider.TicksBelow)
        self.memory_slider.setTickInterval(512)  # 每512MB一个刻度
        self.memory_slider.setSingleStep(256)  # 步长256MB
        self.memory_slider.setPageStep(1024)  # 页步长1GB
        self.memory_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: rgba(217, 217, 217, 1);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: rgba(255, 152, 0, 1);
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: rgba(255, 152, 0, 1);
                border-radius: 3px;
            }
        """)
        game_memory_layout.addRow("自定义内存", self.memory_slider)  # 空标签使按钮对齐下拉框
        
        # 创建内存值显示标签
        memory_container = QWidget()
        memory_layout = QHBoxLayout(memory_container)
        memory_layout.setContentsMargins(0, 0, 0, 0)
        memory_layout.setSpacing(10)
        game_memory_layout.addRow(memory_container)

        # 添加内存使用情况显示
        memory_usage_container = QWidget()
        memory_usage_layout = QHBoxLayout(memory_usage_container)
        memory_usage_layout.setContentsMargins(0, 0, 0, 0)
        memory_usage_layout.setSpacing(5)

        # 已分配内存标签
        allocated_label = QLabel("游戏分配:")
        allocated_label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 11px;
            }
        """)
        # 已分配内存值
        self.allocated_value = QLabel("2048 MB")
        self.allocated_value.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        # 分隔符
        separator = QLabel("|")
        separator.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
                padding: 0 5px;
            }
        """)
        # 已使用内存标签
        used_label = QLabel("已使用:")
        used_label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 11px;
            }
        """)
        # 已使用内存值
        self.used_value = QLabel("1024 MB")
        self.used_value.setStyleSheet("""
            QLabel {
                color: #FF9800;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        # 分隔符
        separator2 = QLabel("|")
        separator2.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
                padding: 0 5px;
            }
        """)
        # 空闲内存标签
        free_label = QLabel("空闲:")
        free_label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 11px;
            }
        """)
        # 空闲内存值
        self.free_value = QLabel("1024 MB")
        self.free_value.setStyleSheet("""
            QLabel {
                color: #2196F3;
                font-size: 11px;
                font-weight: bold;
            }
        """)

        memory_usage_layout.addWidget(allocated_label)
        memory_usage_layout.addWidget(self.allocated_value)
        memory_usage_layout.addWidget(separator)
        memory_usage_layout.addWidget(used_label)
        memory_usage_layout.addWidget(self.used_value)
        memory_usage_layout.addWidget(separator2)
        memory_usage_layout.addWidget(free_label)
        memory_usage_layout.addWidget(self.free_value)
        memory_usage_layout.addStretch()

        game_memory_layout.addRow("", memory_usage_container)

        # 连接滑块值改变信号
        self.memory_manager = MemorySliderManager(
            slider=self.memory_slider,
            allocated_label=allocated_label,
            used_label=self.used_value,
            free_label=self.free_value,
        )
        self.memory_manager.update_system_memory()
        self.memory_slider.valueChanged.connect(lambda: self.on_setting_changed("memory.allocation", self.memory_slider.value()))

        # 将表单布局添加到卡片的内容区域
        crad_game_memory_widget.add_layout(game_memory_layout)
        layout.addWidget(crad_game_memory_widget)
        # 添加间隔 - 方法2：使用透明占位控件（更可靠）
        spacer = QWidget()
        spacer.setFixedHeight(10)
        spacer.setStyleSheet("background-color: transparent;")
        layout.addWidget(spacer)

        ###############
        # 高级启动选项 #
        crad_advanced_options_widget = QMCard(
            title="高级启动选项",
            icon=os.path.join(self.home_path, "resources/icons/union@2x.png")
        )
        crad_advanced_options_widget.setBackgroundColor("#252627")
        crad_advanced_options_widget.setStyleSheet("""
            QWidget {
                background-color: #252627;
                color: #AFAFAF;
            }
        """)
        # JVM参数
        advanced_options_layout = QFormLayout()
        self.jvm_args_input = QLineEdit()
        self.jvm_args_input.textChanged.connect(
            lambda t: self.on_setting_changed("game.launch_jvm_args", t)
        )
        advanced_options_layout.addRow("Java虚拟机参数", self.jvm_args_input)
        # 启动参数
        self.launch_args_input = QLineEdit()
        self.launch_args_input.textChanged.connect(
            lambda t: self.on_setting_changed("game.launch_args", t)
        )
        advanced_options_layout.addRow("启动参数", self.launch_args_input)
        # 启动前执行命令
        self.pre_launch_command = QLineEdit()
        self.pre_launch_command.textChanged.connect(
            lambda t: self.on_setting_changed("game.launch_pre_command", t)
        )
        advanced_options_layout.addRow("启动前执行命令", self.pre_launch_command)
        
        # 启用独立显卡
        self.high_perf_java_yes = QRadioButton("是")
        self.high_perf_java_no = QRadioButton("否")
        self.high_perf_java_no.setChecked(True)  # 默认选中“否”
        self.high_perf_java_yes.toggled.connect(lambda: self.on_setting_changed("gpu_enable", self.high_perf_java_yes.isChecked()))
        self.high_perf_java_no.toggled.connect(lambda: self.on_setting_changed("gpu_enable", self.high_perf_java_yes.isChecked()))

        # 启用独立显卡
        high_perf_layout = QHBoxLayout()
        self.high_perf_java_no.setChecked(True)
        high_perf_group = QButtonGroup(self)
        high_perf_group.addButton(self.high_perf_java_yes)
        high_perf_group.addButton(self.high_perf_java_no)
        high_perf_layout.addWidget(self.high_perf_java_yes)
        high_perf_layout.addWidget(self.high_perf_java_no)
        high_perf_layout.addStretch()
        advanced_options_layout.addRow("启用独立显卡", high_perf_layout)

        crad_advanced_options_widget.add_layout(advanced_options_layout)
        layout.addWidget(crad_advanced_options_widget)
        # 添加间隔 - 方法2：使用透明占位控件（更可靠）
        spacer = QWidget()
        spacer.setFixedHeight(10)
        spacer.setStyleSheet("background-color: transparent;")
        layout.addWidget(spacer)


        ###############
        # BUG调试模式 #
        debug_widget = QMCard(
            title="高级启动选项",
            icon=os.path.join(self.home_path, "resources/icons/union@2x.png")
        )
        debug_widget.setBackgroundColor("#252627")
        debug_widget.setStyleSheet("""
            QWidget {
                background-color: #252627;
                color: #AFAFAF;
            }
        """)
        # BUG调试
        debug_layout = QFormLayout()
        self.bug_debug_mode = QCheckBox("BUG调试模式")
        self.bug_debug_mode.toggled.connect(lambda: self.on_setting_changed("debug_endble", self.bug_debug_mode.isChecked()))

        debug_layout.addRow("测试", self.bug_debug_mode)

        debug_widget.add_layout(debug_layout)
        layout.addWidget(debug_widget)
        # 添加间隔 - 方法2：使用透明占位控件（更可靠）
        spacer = QWidget()
        spacer.setFixedHeight(10)
        spacer.setStyleSheet("background-color: transparent;")
        layout.addWidget(spacer)

        # 设置滚动区域的内容
        scroll_area.setWidget(main_layout)
        
        # 创建容器页面
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.addWidget(scroll_area)
        self.settings_stack.addWidget(page)

    def create_personalization_settings(self):
        """创建个性化设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("个性化设置 (开发中)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff; margin-bottom: 20px;")
        layout.addWidget(title)
        
        layout.addStretch()
        self.settings_stack.addWidget(page)
    
    def create_other_settings(self):
        """创建其他设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("其他设置 (开发中)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff; margin-bottom: 20px;")
        layout.addWidget(title)
        
        layout.addStretch()
        self.settings_stack.addWidget(page)
    
    def get_groupbox_style(self):
        """获取GroupBox的样式"""
        return """
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
        """
    
    def show_launch_settings(self):
        """显示启动参数设置"""
        self.settings_stack.setCurrentIndex(0)
    
    def show_personalization(self):
        """显示个性化设置"""
        self.settings_stack.setCurrentIndex(1)
    
    def show_other_settings(self):
        """显示其他设置"""
        self.settings_stack.setCurrentIndex(2)

        
    def auto_search_java(self, java_path=None):
        """自动搜索Java安装"""
        # 显示搜索中状态
        self.auto_search_button.setEnabled(False)
        self.auto_search_button.setText("搜索中...")
        
        # 在后台线程中执行搜索（避免阻塞UI）
        from PySide6.QtCore import QThread, Signal, QObject
        
        class JavaSearchWorker(QObject):
            finished = Signal(list)
            error = Signal(str)
            
            def run(self):
                try:
                    finder = JavaPathFinder()
                    java_installations = finder.find_all_java_installations()
                    self.finished.emit(java_installations)
                except Exception as e:
                    self.error.emit(str(e))
        
        # 创建和工作线程
        self.search_thread = QThread()
        self.worker = JavaSearchWorker()
        self.worker.moveToThread(self.search_thread)
        
        # 连接信号和槽
        self.search_thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda t: self.on_java_search_finished(t, java_path))
        self.worker.finished.connect(self.search_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.on_java_search_error)
        self.search_thread.finished.connect(self.search_thread.deleteLater)
        
        # 启动线程
        self.search_thread.start()

    def on_java_search_finished(self, java_installations, find_java):
        """Java搜索完成处理"""
        self.auto_search_button.setEnabled(True)
        self.auto_search_button.setText("自动搜索")
        
        if not java_installations:
            self.show_message("未找到Java安装", "请手动安装Java或指定Java路径")
            return
        
        # 更新Java选择下拉框
        current_count = self.game_java_combo.count()
        for i in range(current_count - 1, 0, -1): # 从后往前删，避免索引变化
            self.game_java_combo.removeItem(i)

        # 添加新的Java路径选项，并将路径设置为UserData
        for java_path, version in java_installations: # 假设这是你的搜索结果
            print(f'  -> {version} - {java_path}')
            self.game_java_combo.addItem(java_path, java_path) # 添加Item并设置UserData  version, 

        # 自动选择推荐的Java
        finder = JavaPathFinder()
        best_java = finder.recommend_best_java(java_installations)
        if find_java:
            best_java = finder.recommend_best_java([(find_java, find_java)])
        
        found_index = -1
        for i in range(1, self.game_java_combo.count()): # 从索引1开始，跳过提示项
            if self.game_java_combo.itemData(i) == best_java:
                found_index = i
                break

        if found_index != -1:
            self.game_java_combo.setCurrentIndex(found_index)
        else:
            print("未找到对应的Java路径，可能需更新选项列表")
            # 可选：设置为“自动选择”或第一个可用选项
            self.game_java_combo.setCurrentIndex(0)

        self.show_message("搜索完成", f"找到 {len(java_installations)} 个Java安装")

    def on_java_search_error(self, error_message):
        """Java搜索错误处理"""
        self.auto_search_button.setEnabled(True)
        self.auto_search_button.setText("自动搜索")
        self.show_message("搜索出错", f"错误信息: {error_message}")

    def show_message(self, title, message):
        """显示消息（实现取决于你的UI框架）"""
        # 这里可以使用QMessageBox或你的自定义弹窗
        print(f"{title}: {message}")
        

    def on_setting_changed(self, key: str, value: Any):
        """处理设置改变，更新配置管理器并保存"""
        # 更新配置管理器
        success = self.settings_manager.set_setting(key, value)
        if success:
            # 立即保存配置（或可以延迟保存以提高性能）
            self.settings_manager.save_settings()
            self.settings_changed.emit(key, value)
        else:
            print(f"保存设置失败: {key} = {value}")
    
    def save_all_settings(self):
        """显式保存所有设置（可用于点击保存按钮时）"""
        # 这里可以添加一些验证逻辑
        success = self.settings_manager.save_settings()
        if success:
            print("所有设置已保存")
        else:
            print("保存设置失败")

    def load_settings_to_ui(self):
        """将配置加载到UI控件"""
        try:
            # 启动器可见性
            visibility = self.settings_manager.get_setting("launcher.visibility", "保持不变")
            self.launcher_visibility_combo.setCurrentText(visibility)
            
            # 进程优先级
            priority = self.settings_manager.get_setting("launcher.process_priority", "中 (平衡)")
            self.process_priority_combo.setCurrentText(priority)

            # 窗口大小
            size = self.settings_manager.get_setting("launcher.window_size", "默认")
            self.window_size_combo.setCurrentText(size)

            ##############################
            # 游戏Java，自动选择Java运行时 #
            java_path = self.settings_manager.get_setting("java.path", "自动选择合适的Java")
            self.auto_search_java(java_path)

            # 内存分配 y
            memory = self.settings_manager.get_setting("memory.allocation", 2048)
            self.memory_slider.setValue(memory)
            
            # JVM参数
            jvm_args = self.settings_manager.get_setting("game.launch_jvm_args", "-XX:+UseG1GC -XX:-UseAdaptiveSizePolicy -XX:-OmitStackTraceInFastThrow -Djdk.lang.Process.allowAmbiguousCommands=true -Dfml.ignoreInvalidMinecraftCertificates=True -Dfml.ignorePatchDiscrepancies=True -Dlog4j2.formatMsgNoLookups=true")
            self.jvm_args_input.setText(jvm_args)

            # 启动参数
            launch_args = self.settings_manager.get_setting("game.launch_args", "")
            self.launch_args_input.setText(launch_args)

            # 启动前执行命令
            pre_launch_command = self.settings_manager.get_setting("game.launch_pre_command", "")
            self.pre_launch_command.setText(pre_launch_command)

            # 启用独立显卡
            pre_launch_command = self.settings_manager.get_setting("gpu_enable", False)
            if pre_launch_command:
                self.high_perf_java_yes.setChecked(True)
            else:
                self.high_perf_java_no.setChecked(True)

            # 调试模式
            debug_mode = self.settings_manager.get_setting("debug_endble", False)
            self.bug_debug_mode.setChecked(debug_mode)
            
            print("配置已加载到UI")
            
        except Exception as e:
            print(f"加载配置到UI时出错: {e}")
