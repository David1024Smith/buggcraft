from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, 
    QListWidgetItem, QHBoxLayout, QComboBox, QLineEdit, QFileDialog
)
from PySide6.QtGui import QIcon, QFont, QPalette, QPixmap
from PySide6.QtCore import Qt, QSize
import os


from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFontMetrics, QColor, QPainter, QLinearGradient

from config.settings import SettingsManager


import logging
logger = logging.getLogger(__name__)


class VersionSettingsPanel(QWidget):
    """游戏版本设置面板"""
    game_change = Signal(str)  # 切换游戏路径
    version_change = Signal(str)  # 切换版本

    def __init__(self, parent, settings_manager: SettingsManager, config_path, resource_path):
        super().__init__(parent)
        self.setStyleSheet("background-color: #fefefe; border: none;")
        self.settings_manager = settings_manager
        self.config_path = config_path
        self.resource_path = resource_path

        self.current_version = None  # 选择的游戏
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        
        version_list_layout = QVBoxLayout()
        version_list_layout.setContentsMargins(0, 15, 0, 15)
        # version_list_layout.setSpacing(10)

        # 版本列表
        version_label = QLabel("文件夹列表")
        version_label.setContentsMargins(13, 0, 15, 0)
        version_label.setStyleSheet("""
            font-size: 12px;
            color: #909090;
        """)
        version_list_layout.addWidget(version_label)
        
        # 版本列表
        self.version_list = QListWidget()
        self.version_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用滚动条
        self.version_list.currentItemChanged.connect(self.on_item_selected)
        version_list_layout.addWidget(self.version_list)


        # 添加导入
        
        version_label = QLabel("添加或导入游戏")
        version_label.setContentsMargins(13, 0, 0, 0)
        version_label.setStyleSheet("""
            font-size: 12px;
            color: #909090;
        """)
        version_list_layout.addWidget(version_label)

        self.import_button = QPushButton("+ 添加已有文件夹")
        self.import_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.import_button.setStyleSheet("""
            QPushButton {
                color: #404040;
                border: none;
                padding: 10px;
                font-size: 15px;
                font-weight: medium;
                text-align: left;  /* 文本左对齐 */
                padding-left: 13px;  /* 左侧内边距 */
            }
            QPushButton:hover {
                background-color: #e6f6ff;
            }
            QPushButton:pressed {
                background-color: #e6f6ff;
            }
        """)
        self.import_button.clicked.connect(self.add_custom_path)
        
        main_layout.addLayout(version_list_layout)
        main_layout.addWidget(self.import_button)
        main_layout.addStretch(1)

        self.load_config()
    
    def paintEvent(self, event):
        """重绘事件 - 使用变量确保背景绘制"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), "#fefefe")  # 使用变量
        super().paintEvent(event)
    
    def set_current_version(self, version_name):
        """设置当前选中的版本"""
        # 遍历所有项，找到匹配的版本
        for i in range(self.version_list.count()):
            item = self.version_list.item(i)
            item_data = item.data(Qt.UserRole)
            
            new_data = {'name': item_data.get('name'), 'path': item_data.get('path'), 'type': item_data.get('type')}
            if new_data and new_data == version_name:
                # 设置选中项
                self.version_list.setCurrentItem(item)
                # 更新样式
                self.on_item_selected(item, None)
                return
        
        # 如果没找到，选择第一项
        if self.version_list.count() > 0:
            self.version_list.setCurrentRow(0)
        
    def load_config(self):
        """加载配置文件"""
        # 加载版本列表
        self.version_list.clear()
        for version in self.settings_manager.get_setting('minecraft.directory.installed'):
            self.add_version_item(version["name"], version["path"], version['type'])
        # 设置当前选中的版本
        self.current_version = self.settings_manager.get_setting('minecraft.directory.enable')
        self.set_current_version(self.current_version)

    def add_version_item(self, name, path, path_type):
        """添加自定义版本项"""
        # 创建列表项
        item = QListWidgetItem(self.version_list)
        item.setSizeHint(QSize(0, 50))  # 设置项高度为60px
        
        # 创建自定义widget
        widget = QWidget()

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 左侧色块（默认隐藏）
        self.color_block = QWidget()
        self.color_block.setFixedWidth(4)
        self.color_block.setFixedHeight(32)
        self.color_block.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.color_block)
        
        # 文本容器
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        # text_layout.setContentsMargins(10, 10, 10, 10)
        text_layout.setSpacing(4)
        
        # 版本名称标签
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("""
            font-size: 15px;
            font-weight: normal;
            color: #404040;
        """)
        text_layout.addWidget(self.name_label)
        
        # 路径标签
        self.path_label = QLabel(path)
        self.path_label.setStyleSheet("""
            font-size: 13px;
            color: #808080;
        """)
        text_layout.addWidget(self.path_label)
        
        layout.addWidget(text_container)
        
        # 设置widget为列表项的内容
        self.version_list.setItemWidget(item, widget)
        
        # 存储样式组件引用
        item.setData(Qt.UserRole, {
            "color_block": self.color_block,
            "name_label": self.name_label,
            "path_label": self.path_label,
            "name": name,
            "path": path,
            "type": path_type  # 存储类型信息
        })
    
    def on_item_selected(self, current, previous):
        """处理选中项变化"""
        # 更新前一个选中项的样式
        if previous:
            prev_data = previous.data(Qt.UserRole)
            if prev_data:
                prev_data["color_block"].setStyleSheet("background-color: transparent;")
                prev_data["name_label"].setStyleSheet("""
                    font-size: 15px;
                    font-weight: normal;
                    color: #404040;
                """)
                prev_data["path_label"].setStyleSheet("""
                    font-size: 13px;
                    color: #808080;
                """)
        
        # 更新当前选中项的样式
        if current:
            curr_data = current.data(Qt.UserRole)
            if curr_data:
                curr_data["color_block"].setStyleSheet("background-color: #4169E1;")
                curr_data["name_label"].setStyleSheet("""
                    font-size: 15px;
                    font-weight: normal;
                    color: #4169E1;
                """)
                curr_data["path_label"].setStyleSheet("""
                    font-size: 13px;
                    color: #444444;
                """)
                # 保存当前选中的版本到配置文件
                self.current_version = {"name": curr_data['name'], "path": curr_data['path'], "type": curr_data['type']}
                self.save_current_version(self.current_version)

    def save_current_version(self, value):
        """保存当前选中的版本到配置文件"""
        import minecraft_launcher_lib
        minecraft_path = value.get('path')
        self.game_change.emit(minecraft_path)

        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_path)
        logger.info(f"在目录 {minecraft_path} 中找到 {len(installed_versions)} 个已安装版本:")
        if installed_versions and len(installed_versions) > 0 and minecraft_path:
            # 默认启用版本
            minecraft_version = [i['id'] for i in installed_versions]
            self.version_change.emit(minecraft_version[0])
            self.settings_manager.set_setting('minecraft.version.enable', minecraft_version[0])
            self.settings_manager.set_setting('minecraft.version.installed', minecraft_version)

            for version in installed_versions:
                logger.info(f"版本ID: {version['id']}")
                logger.info(f"  类型: {version['type']}")
                logger.info(f"  发布日期: {version['releaseTime']}")
                logger.info("---")

        self.settings_manager.set_setting('minecraft.directory.enable', value)
        self.settings_manager.save_settings()
        pass

    def validate_minecraft_folder(self, path):
        """验证Minecraft文件夹并返回详细结果"""
        results = {
            "valid": True,
            "missing_dirs": [],
            "missing_files": [],
            "empty_versions": False
        }
        
        # 检查必要文件夹
        required_dirs = ["versions"]
        for dir_name in required_dirs:
            dir_path = os.path.join(path, dir_name)
            if not os.path.exists(dir_path):
                results["missing_dirs"].append(dir_name)
                results["valid"] = False
        
        # 检查版本文件夹是否为空
        versions_dir = os.path.join(path, "versions")
        if os.path.exists(versions_dir) and not os.listdir(versions_dir):
            results["empty_versions"] = True
            results["valid"] = False
        
        # 检查必要文件
        # required_files = ["launcher_profiles.json"]
        # for file_name in required_files:
        #     file_path = os.path.join(path, file_name)
        #     if not os.path.exists(file_path):
        #         results["missing_files"].append(file_name)
        #         results["valid"] = False
        
        return results

    def show_error_message(self, title, message):
        """显示错误消息"""
        # 在实际应用中，您可以使用QMessageBox
        print(f"[ERROR] {title}: {message}")
        # 或者使用状态栏显示消息
        if self.parent() and hasattr(self.parent(), "show_status_message"):
            self.parent().show_toast(f"{title}: {message}", "error")

    def show_success_message(self, title, message):
        """显示成功消息"""
        print(f"[SUCCESS] {title}: {message}")
        if self.parent() and hasattr(self.parent(), "show_status_message"):
            self.parent().show_toast(f"{title}: {message}", "success")

    def show_warning_message(self, title, message):
        """显示警告消息"""
        print(f"[WARNING] {title}: {message}")
        if self.parent() and hasattr(self.parent(), "show_status_message"):
            self.parent().show_toast(f"{title}: {message}", "warning")


    def add_custom_path(self):
        """添加自定义路径"""
        # 打开文件夹选择对话框
        path = QFileDialog.getExistingDirectory(
            self, 
            "选择Minecraft文件夹",
            os.path.expanduser("~")
        )
        
        if not path:
            return  # 用户取消了选择
        
        # 验证文件夹结构
        validation = self.validate_minecraft_folder(path)
        if not validation["valid"]:
            error_message = "选择的文件夹无效:\n"
            
            if validation["missing_dirs"]:
                error_message += f"- 缺少文件夹: {', '.join(validation['missing_dirs'])}\n"
            
            if validation["missing_files"]:
                error_message += f"- 缺少文件: {', '.join(validation['missing_files'])}\n"
            
            if validation["empty_versions"]:
                error_message += "- versions文件夹为空\n"
            
            self.show_error_message("无效的Minecraft文件夹", error_message)
            return
    

        # 检查路径是否有效
        if not self.is_valid_minecraft_path(path):
            print(f"无效的Minecraft路径: {path}")
            return
        
        # 获取路径名称
        name = os.path.basename(path)
        if not name:
            name = "自定义路径"
        
        # 添加到配置
        self.add_version(name, path, 'custom')
    
    def is_valid_minecraft_path(self, path):
        """检查是否是有效的Minecraft路径"""
        # 检查是否存在必要的文件夹或文件
        required_dirs = ["versions", "mods", "saves"]
        required_files = ["launcher_profiles.json"]
        
        # 检查是否存在至少一个必要的文件夹
        for dir_name in required_dirs:
            if os.path.exists(os.path.join(path, dir_name)):
                return True
        
        # 检查是否存在必要的文件
        for file_name in required_files:
            if os.path.exists(os.path.join(path, file_name)):
                return True
        
        return False
    
    def add_version(self, name, path, type:str = "custom"):
        """添加新版本"""
        self.current_version = {"name": name, "path": path, "type": type}
        version = self.settings_manager.get_setting('minecraft.directory.installed')
        version.append(self.current_version)
        self.settings_manager.set_setting('minecraft.directory.installed', version)
        self.add_version_item(name, path, type)
        self.set_current_version(self.current_version)
        self.save_current_version(self.current_version)