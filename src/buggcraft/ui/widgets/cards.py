# QMCard 类

from PySide6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QFrame)
from PySide6.QtCore import Signal


class QMCard(QFrame):
    """服务器卡片"""
    selected = Signal(str)
    
    def __init__(self, name, address, players, max_players, ping, description):
        super().__init__()
        self.name = name
        self.address = address
        self.players = players
        self.max_players = max_players
        self.ping = ping
        self.description = description
        
        self.setFixedHeight(120)
        self.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border-radius: 8px;
                border: 1px solid #555;
            }
            QFrame:hover {
                border: 1px solid #4CAF50;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 服务器名称
        name_label = QLabel(self.name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(name_label)
        
        # 服务器信息
        info_layout = QHBoxLayout()
        
        # 玩家数量
        players_label = QLabel(f"玩家: {self.players}/{self.max_players}")
        players_label.setStyleSheet("color: #aaaaaa;")
        info_layout.addWidget(players_label)
        
        # 延迟
        ping_label = QLabel(f"延迟: {self.ping}ms")
        if self.ping < 50:
            ping_label.setStyleSheet("color: #4CAF50;")
        elif self.ping < 100:
            ping_label.setStyleSheet("color: #FFC107;")
        else:
            ping_label.setStyleSheet("color: #F44336;")
        info_layout.addWidget(ping_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 描述
        desc_label = QLabel(self.description)
        desc_label.setStyleSheet("color: #cccccc;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
    
    def mousePressEvent(self, event):
        """点击选择服务器"""
        self.selected.emit(self.address)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 8px;
                border: 2px solid #4CAF50;
            }
        """)


