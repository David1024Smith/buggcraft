# 应用设置

import json
import os
import minecraft_launcher_lib

from typing import Any, Dict, Optional
from utils.minecraft import find_minecraft_dirs

import logging
logger = logging.getLogger(__name__)


class SettingsManager:
    """
    设置管理类，用于统一处理应用的配置保存和加载
    使用JSON格式存储配置，支持中文和复杂数据结构
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.config_path = config_path
        self.config_file = os.path.join(self.config_path, 'settings.json')
        
        # 确保配置目录存在
        os.makedirs(self.config_path, exist_ok=True)
        
        # 当前配置字典
        self.current_settings: Dict[str, Any] = {}

        # 游戏路径及版本
        minecraft = {
            'directory': {
                "enable": None,
                "installed": []
            },
            'version': {
                "enable": None,
                "installed": []
            }
        }

        # 获取已安装版本列表 {"name": "当前文件夹", "path": i, "type": "current"}
        
        minecraft_installed_dirs: list = []

        for dir in find_minecraft_dirs():
            if self.is_current_folder(dir):
                minecraft_installed_dirs.append({"name": "当前文件夹", "path": dir, "type": "current"})
                continue
            elif self.is_official_folder(dir):
                minecraft_installed_dirs.append({"name": "官方启动器文件夹", "path": dir, "type": "official"})
            else:
                minecraft_installed_dirs.append({"name": "其他文件夹", "path": dir, "type": "other"})

        if minecraft_installed_dirs and len(minecraft_installed_dirs) > 0:
            minecraft_enable = minecraft_installed_dirs[0]
            minecraft_path = minecraft_enable.get('path')
            installed_versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_path)
            logger.info(f"在目录 {minecraft_path} 中找到 {len(installed_versions)} 个已安装版本:")
            if installed_versions and len(installed_versions) > 0 and minecraft_path:
                # 默认启用版本
                minecraft_version = [i['id'] for i in installed_versions]

                minecraft['directory']['enable'] = minecraft_enable
                minecraft['directory']['installed'] = minecraft_installed_dirs
                minecraft['version']['enable'] = minecraft_version[0]
                minecraft['version']['installed'] = minecraft_version

                for version in installed_versions:
                    logger.info(f"版本ID: {version['id']}")
                    logger.info(f"  类型: {version['type']}")
                    logger.info(f"  发布日期: {version['releaseTime']}")
                    logger.info("---")

        # 默认配置
        self.default_settings = {
            "minecraft": minecraft,
            "launcher": {
                "visibility": "游戏启动后保持不变",
                "process_priority": "中 (平衡)",
                "window_size": "默认"
            },
            "java": {
                "version": "自动选择",
                "path": None
            },
            "memory": {
                "allocation": 1024,
            },
            "game": {
                "launch_jvm_args": "",
                "launch_args": "",
                "launch_pre_command": ""
            },
            "gpu_enable": False,
            "debug_endble": False
        }
        
        # 加载现有配置或使用默认配置
        self.load_settings()
    
    def get_default_official_path(self):
        """获取官方启动器默认路径"""
        # Windows系统
        if os.name == 'nt':
            return os.path.join(os.getenv('APPDATA'), '.minecraft')
        # macOS系统
        elif os.name == 'posix':
            return os.path.expanduser('~/Library/Application Support/minecraft')
        # Linux系统
        else:
            return os.path.expanduser('~/.minecraft')
            
    def is_current_folder(self, path):
        """判断是否是当前文件夹"""
        return path == os.getcwd()
    
    def is_official_folder(self, path):
        """判断是否是官方启动器文件夹"""
        return path == self.get_default_official_path()
    
    def get_path_type_label(self, path_type):
        """获取路径类型标签文本"""
        if path_type == "current":
            return "当前文件夹"
        elif path_type == "official":
            return "官方启动器文件夹"
        else:
            return "自定义"
        
    def load_settings(self, file_path: Optional[str] = None) -> bool:
        """
        从JSON文件加载配置
        
        Args:
            file_path: 配置文件路径，如果为None则使用初始化时设置的路径
            
        Returns:
            bool: 是否成功加载
        """
        target_file = file_path or self.config_file
        
        try:
            if os.path.exists(target_file):
                with open(target_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # 合并加载的配置与默认配置（确保有新字段时使用默认值）
                self.current_settings = self._deep_merge(
                    self.default_settings, loaded_settings
                )
                logger.info(f"配置已从文件加载: {target_file}")
                return True
            else:
                # 文件不存在，使用默认配置
                self.current_settings = self.default_settings.copy()
                logger.info("未找到配置文件，使用默认配置")
                # 保存默认配置
                self.save_settings()
                return True
                
        except Exception as e:
            logger.info(f"加载配置时出错: {e}")
            # 出错时使用默认配置
            self.current_settings = self.default_settings.copy()
            return False
    
    def save_settings(self, file_path: Optional[str] = None) -> bool:
        """
        保存当前配置到JSON文件
        
        Args:
            file_path: 配置文件路径，如果为None则使用初始化时设置的路径
            
        Returns:
            bool: 是否成功保存
        """
        target_file = file_path or self.config_file
        
        try:
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.current_settings, 
                    f, 
                    indent=4, 
                    ensure_ascii=False  # 重要：确保中文正确显示
                )
            logger.info(f"配置已保存到文件: {target_file}")
            return True
        except Exception as e:
            logger.info(f"保存配置时出错: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点分隔的嵌套键（如 "launcher.visibility"）
        
        Args:
            key: 配置键，支持嵌套结构
            default: 如果键不存在时返回的默认值
            
        Returns:
            Any: 配置值
        """
        try:
            # 支持点分隔的嵌套键
            keys = key.split('.')
            value = self.current_settings
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """
        设置配置值，支持点分隔的嵌套键（如 "launcher.visibility"）
        
        Args:
            key: 配置键，支持嵌套结构
            value: 要设置的值
            
        Returns:
            bool: 是否成功设置
        """
        try:
            # 支持点分隔的嵌套键
            keys = key.split('.')
            settings = self.current_settings
            
            # 遍历到最后一个键的父级
            for k in keys[:-1]:
                if k not in settings:
                    settings[k] = {}
                settings = settings[k]
            
            # 设置值
            settings[keys[-1]] = value
            return True
        except Exception as e:
            logger.info(f"设置配置时出错: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self.current_settings = self.default_settings.copy()
        self.save_settings()
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并两个字典，用于合并默认配置和加载的配置
        
        Args:
            base: 基础字典（通常是默认配置）
            update: 要合并的字典（通常是从文件加载的配置）
            
        Returns:
            Dict[str, Any]: 合并后的字典
        """
        result = base.copy()
        
        for key, value in update.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                # 递归合并字典
                result[key] = self._deep_merge(result[key], value)
            else:
                # 直接设置或覆盖值
                result[key] = value
                
        return result


    @property
    def all_settings(self) -> Dict[str, Any]:
        """获取所有当前配置的副本"""
        return self.current_settings.copy()

# 单例模式：创建全局配置管理器实例
_settings_manager_instance = None

def get_settings_manager(path=None) -> SettingsManager:
    """获取全局配置管理器实例（单例模式）"""
    global _settings_manager_instance
    if _settings_manager_instance is None:
        _settings_manager_instance = SettingsManager(path)
    return _settings_manager_instance
