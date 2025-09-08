# 辅助函数

import os
from PySide6.QtWidgets import (
    QApplication
)
from PySide6.QtCore import QSize
from PySide6.QtGui import QFont, QFontDatabase


import psutil  # 需要安装：pip install psutil
from PySide6.QtCore import QTimer


class MemorySliderManager:
    """内存滑块与系统内存监控管理器"""
    
    def __init__(self, slider, allocated_label, used_label, free_label):
        """
        初始化内存管理器
        
        :param slider: 内存滑块 (QSlider)
        :param allocated_label: 已分配内存标签 (QLabel)
        :param used_label: 已使用内存标签 (QLabel)
        :param free_label: 空闲内存标签 (QLabel)
        """
        self.slider = slider
        self.allocated_label = allocated_label
        self.used_label = used_label
        self.free_label = free_label
        
        # 连接滑块值改变信号
        self.slider.valueChanged.connect(self.update_allocated_memory)
        
        # 创建定时器更新系统内存使用情况
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system_memory)
        self.timer.start(1000)  # 每秒更新一次
    
    def update_allocated_memory(self, value):
        """更新分配的内存值"""
        # 更新分配值显示
        self.allocated_label.setText(f"{value} MB")
    
    def update_system_memory(self):
        """更新系统内存使用情况"""
        # 获取系统内存信息
        mem = psutil.virtual_memory()
        
        # 计算内存值（单位：MB）
        total_mb = mem.total // (1024 * 1024)
        used_mb = mem.used // (1024 * 1024)
        free_mb = mem.free // (1024 * 1024)
        
        # 更新UI显示
        self.used_label.setText(f"{used_mb} MB")
        self.free_label.setText(f"{free_mb} MB")
        
        # 可选：根据系统内存限制滑块最大值
        # self.slider.setMaximum(total_mb)
        self.slider.setRange(512, free_mb - 512)  # 系统预留512


def scale_component(original_size: QSize, target_size: QSize) -> float:
    """
    根据目标尺寸动态缩放组件
    
    :param original_size: 原始设计尺寸 (QSize)
    :param target_size: 当前目标尺寸 (QSize)
    """
    # 计算宽高缩放比例
    width_ratio = target_size.width() / original_size.width()
    height_ratio = target_size.height() / original_size.height()
    
    # 使用最小比例保持宽高比
    scale_ratio = min(width_ratio, height_ratio)
    return scale_ratio


def load_custom_font(HOME_PATH: str):
    """加载自定义字体文件并设置为全局字体"""
    # 字体文件路径
    fonts = [
        os.path.abspath(os.path.join(HOME_PATH, 'resources', 'fonts', 'ChuangKeTieJinGangTi-2.otf')),
        os.path.abspath(os.path.join(HOME_PATH, 'resources', 'fonts', 'SourceHanSansCN-Heavy.otf')),
        os.path.abspath(os.path.join(HOME_PATH, 'resources', 'fonts', 'SourceHanSansCN-Medium.ttf')),
    ]
    for font in fonts:
        # 加载字体文件
        font_id = QFontDatabase.addApplicationFont(font)
        if font_id == -1:
            print(f"无法加载字体文件: {font}")
            return
        
        # 获取字体家族名称
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if not font_families:
            print(f"字体文件中未找到有效的字体家族: {font}")
            return
        
        for i in font_families:
            app_font = QFont(i)
            QApplication.setFont(app_font)
            print(f"已设置全局字体: {i}")

