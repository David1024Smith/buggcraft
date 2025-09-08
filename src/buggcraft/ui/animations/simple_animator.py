# SimpleAnimator 类 TODO REMOVE

from PySide6.QtCore import QPropertyAnimation, QEasingCurve


class SimpleAnimator:
    """最简单的淡入淡出动画实现"""
    
    def fade_out_hide(self, widget):
        """
        淡出隐藏控件
        :param widget: 要隐藏的控件
        """
        # 创建淡出动画
        fade_out = QPropertyAnimation(widget, b"windowOpacity")
        fade_out.setDuration(500)  # 500毫秒动画时间
        fade_out.setStartValue(1.0)  # 完全不透明
        fade_out.setEndValue(0.0)    # 完全透明
        fade_out.setEasingCurve(QEasingCurve.OutCubic)  # 平滑的缓动曲线
        
        # 动画完成后隐藏控件
        def on_finished():
            widget.hide()
            widget.setWindowOpacity(1.0)  # 重置透明度以备下次使用
        
        fade_out.finished.connect(on_finished)
        fade_out.start()
    
    def fade_in_show(self, widget):
        """
        淡入显示控件
        :param widget: 要显示的控件
        """
        # 设置初始透明状态
        widget.setWindowOpacity(0.0)
        widget.show()
        
        # 创建淡入动画
        fade_in = QPropertyAnimation(widget, b"windowOpacity")
        fade_in.setDuration(500)  # 500毫秒动画时间
        fade_in.setStartValue(0.0)  # 完全透明
        fade_in.setEndValue(1.0)    # 完全不透明
        fade_in.setEasingCurve(QEasingCurve.OutCubic)  # 平滑的缓动曲线
        
        fade_in.start()

