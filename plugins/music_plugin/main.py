"""
点名音乐插件
功能：监听点名信号，自动播放音乐
"""

__plugin_meta__ = {
    'name': '点名音乐插件',
    'version': '1.0.0',
    'generation': 1,
    'description': '点名时自动播放背景音乐',
    'author': 'Sankteco',
    'icon': 'MUSIC',
}

import os
import sys
from pathlib import Path
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog
)
from PySide2.QtCore import Qt, QTimer


class MusicPlayerWidget(QWidget):
    """音乐控制面板"""
    
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.music_file = None
        self.is_playing = False
        
        # 尝试导入 pygame
        try:
            import pygame
            self.pygame = pygame
            self.pygame.mixer.init()
            self.available = True
        except ImportError:
            self.available = False
            self.pygame = None
        
        self._setup_ui()
        self._connect_signals()
        self._load_config()
    
    def _setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("点名音乐插件")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 状态显示
        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
        
        # 音乐文件路径
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择音乐文件")
        self.file_label.setStyleSheet("color: #666;")
        self.file_btn = QPushButton("选择音乐")
        self.file_btn.clicked.connect(self._select_music)
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.file_btn)
        layout.addLayout(file_layout)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.clicked.connect(self._toggle_play)
        self.play_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("■ 停止")
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setEnabled(False)
        
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 是否支持音乐
        if not self.available:
            status = QLabel("⚠ pygame 未安装，音乐功能不可用")
            status.setStyleSheet("color: #e74c3c;")
            layout.addWidget(status)
    
    def _connect_signals(self):
        """连接全局信号"""
        # 监听点名完成信号
        self.context.student_selected.connect(self._on_student_selected)
    
    def _load_config(self):
        """加载配置"""
        data_dir = self.context.get_plugin_data_dir()
        if data_dir:
            config_file = data_dir / "config.txt"
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        path = f.read().strip()
                        if path and Path(path).exists():
                            self.music_file = path
                            self.file_label.setText(Path(path).name)
                            self.play_btn.setEnabled(True)
                except:
                    pass
    
    def _save_config(self):
        """保存配置"""
        data_dir = self.context.get_plugin_data_dir()
        if data_dir and self.music_file:
            config_file = data_dir / "config.txt"
            try:
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write(self.music_file)
            except:
                pass
    
    def _select_music(self):
        """选择音乐文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音乐文件",
            "",
            "音频文件 (*.mp3 *.wav *.flac *.ogg);;所有文件 (*.*)"
        )
        if file_path:
            self.music_file = file_path
            self.file_label.setText(Path(file_path).name)
            self.play_btn.setEnabled(True)
            self._save_config()
            self.context.log(f"已选择音乐: {file_path}")
    
    def _toggle_play(self):
        """切换播放/暂停"""
        if not self.music_file or not self.available:
            return
        
        if self.is_playing:
            self._pause()
        else:
            self._play()
    
    def _play(self):
        """播放音乐"""
        if not self.music_file or not self.available:
            return
        
        try:
            self.pygame.mixer.music.load(self.music_file)
            self.pygame.mixer.music.play()
            self.is_playing = True
            self.play_btn.setText("⏸ 暂停")
            self.stop_btn.setEnabled(True)
            self.status_label.setText("状态: 播放中")
            self.context.log(f"开始播放: {self.music_file}")
        except Exception as e:
            self.context.log(f"播放失败: {e}", "ERROR")
            self.status_label.setText(f"状态: 播放失败 - {e}")
    
    def _pause(self):
        """暂停播放"""
        if self.available and self.is_playing:
            self.pygame.mixer.music.pause()
            self.is_playing = False
            self.play_btn.setText("▶ 播放")
            self.status_label.setText("状态: 已暂停")
            self.context.log("播放已暂停")
    
    def _stop(self):
        """停止播放"""
        if self.available:
            self.pygame.mixer.music.stop()
            self.is_playing = False
            self.play_btn.setText("▶ 播放")
            self.stop_btn.setEnabled(False)
            self.status_label.setText("状态: 已停止")
            self.context.log("播放已停止")
    
    def _on_student_selected(self, student_name: str):
        """点名完成时触发"""
        self.context.log(f"学生被点名: {student_name}")
        if self.music_file and self.available:
            # 如果有音乐正在播放，先停止
            if self.is_playing:
                self.pygame.mixer.music.stop()
                self.is_playing = False
                self.play_btn.setText("▶ 播放")
            # 播放音乐（如果已选择音乐文件）
            self._play()
    
    def cleanup(self):
        """清理资源"""
        if self.available:
            self.pygame.mixer.music.stop()
            self.pygame.mixer.quit()


def register(context):
    """
    插件注册函数
    :param context: 插件上下文
    :return: QWidget 实例
    """
    context.log("点名音乐插件正在加载...")
    
    # 创建音乐控制面板
    widget = MusicPlayerWidget(context)
    widget.setObjectName("music_plugin_page")
    
    context.log("点名音乐插件加载完成")
    return widget


def unregister(context):
    """插件卸载前的清理"""
    context.log("点名音乐插件正在卸载...")
    # 清理会在 widget 被删除时自动进行
