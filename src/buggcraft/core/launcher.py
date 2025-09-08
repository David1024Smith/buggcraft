# MinecraftLauncher 类

import os
import platform
import subprocess
import signal
import time
import psutil
import minecraft_launcher_lib
from urllib.parse import urlparse, parse_qs, quote
from base64 import urlsafe_b64encode
from hashlib import sha256
from secrets import token_urlsafe
from PySide6.QtCore import Signal, QObject, QThread


class MinecraftSignals(QObject):
    """Minecraft 信号类"""
    output = Signal(str)
    started = Signal()
    stopped = Signal(int)  # 退出代码
    error = Signal(str)
    progress = Signal(int)  # 进度百分比


class OutputHandlerThread(QThread):
    """处理游戏输出的 Qt 线程"""
    output_received = Signal(str, bool)  # 消息, 是否标准输出
    
    def __init__(self, process):
        super().__init__()
        self.process = process
        self.running = True
    
    def run(self):
        """线程主函数"""
        while self.running and self.process and self.process.poll() is None:
            try:
                # 尝试读取stdout
                if self.process.stdout:
                    try:
                        raw_line = self.process.stdout.readline()
                        if raw_line:
                            try:
                                line = raw_line.decode('utf-8', errors='replace').strip()
                                self.output_received.emit(line, True)
                            except:
                                pass
                    except:
                        pass
                
                # 短暂睡眠
                time.sleep(0.01)  # 等待10毫秒
            except Exception as e:
                self.output_received.emit(f"输出处理错误: {str(e)}", False)
                break
    
    def stop(self):
        """停止线程"""
        self.running = False


class StartGameThread(QThread):
    """启动游戏的 Qt 线程"""
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, launcher):
        super().__init__()
        self.launcher = launcher
    
    def run(self):
        """线程主函数"""
        try:
            self.launcher._start_game()
        except Exception as e:
            self.error.emit(f"启动错误: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.finished.emit()


class MinecraftLibLauncher(QObject):
    """Minecraft 启动器核心类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = MinecraftSignals()
        
        self.process = None
        self.running = False
        self.stopping = False
        self.output_thread = None
        self.start_thread = None
        self.minecraft_directory = None
        self.language = "zh_cn"  # 默认语言
        self.version = None
        self.username = "Player"
        self.server = None
        self.memory = 4096
        self.languages = {
            "English": "en_us",
            "简体中文": "zh_cn",
            "繁體中文": "zh_tw",
            "Français": "fr_fr",
            "Deutsch": "de_de",
            "Español": "es_es",
            "日本語": "ja_jp",
            "한국어": "ko_kr",
            "Русский": "ru_ru"
        }
    
    def set_language(self, language='简体中文'):
        """设置游戏语言"""
        self.language = self.languages[language]

    def set_options(self, minecraft_directory, version, uuid=None, username="Player", token=None, server=None, memory=4096):
        """设置启动选项"""
        self.minecraft_directory = minecraft_directory
        self.version = version
        self.uuid = uuid
        self.username = username
        self.token = token
        self.server = server
        self.memory = memory

    def start(self):
        """启动 Minecraft 游戏"""
        if self.running:
            self.signals.error.emit("游戏已经在运行中")
            return
        
        # 创建并启动 Qt 线程
        self.start_thread = StartGameThread(self)
        self.start_thread.finished.connect(self._on_start_finished)
        self.start_thread.error.connect(self.signals.error)
        self.start_thread.start()
    
    def _on_start_finished(self):
        """启动线程完成处理"""
        self.start_thread = None
    
    def _start_game(self):
        """在工作线程中启动游戏"""
        try:
            # 准备启动环境
            if not os.path.exists(self.minecraft_directory):
                os.makedirs(self.minecraft_directory, exist_ok=True)

            # 确保游戏语言设置文件正确配置
            self._ensure_language_setting()

            # 准备启动选项
            options = {
                "username": self.username,
                "server": self.server,
                "gameDirectory": self.minecraft_directory,
                "version": self.version,
                "jvmArguments": [
                    f"-Xmx{self.memory}M", 
                    f"-Xms{self.memory}M",
                    f"-Dfile.encoding=UTF-8"
                ],
                "launcherName": "BuggCraft Launcher",
                "launcherVersion": "1.0"
            }
            
            if self.uuid: options['uuid'] = self.uuid

            if self.token:
                options['token'] = self.token
                self.signals.output.emit(f"使用离线账户: {self.username}")

            if self.server: self.signals.output.emit(f"连接服务器: {self.server}")
            
            # 安装游戏库文件
            self.signals.output.emit("正在安装游戏库文件...")
            minecraft_launcher_lib.install.install_minecraft_version(
                self.version, 
                self.minecraft_directory,
                callback={
                    "setStatus": lambda msg: self.signals.output.emit(f"[安装] {msg}"),
                    "setProgress": lambda progress: self.signals.progress.emit(progress),
                    "setMax": lambda max_value: self.signals.output.emit(f"[最大] {max_value}")
                }
            )

            # 获取启动命令
            command = minecraft_launcher_lib.command.get_minecraft_command(
                self.version, 
                self.minecraft_directory,
                options
            )
            
            # 清理命令参数
            command = [arg for arg in command if arg != "None" and arg is not None]

            # 打印命令用于调试
            self.signals.output.emit(f"启动命令: {' '.join(command)}")

            # 启动游戏进程
            startup_flags = 0
            if platform.system() == "Windows":
                startup_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            
            # 创建环境变量副本
            env = os.environ.copy()
            # 设置环境变量确保使用UTF-8
            env['LANG'] = self.language + '.UTF-8'
            env['LC_ALL'] = self.language + '.UTF-8'
            env['JAVA_OPTS'] = '-Dfile.encoding=UTF-8'

            self.process = subprocess.Popen(
                command,
                cwd=self.minecraft_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                creationflags=startup_flags,
                env=env
            )
            
            # 记录进程ID
            self.signals.output.emit(f"游戏进程PID: {self.process.pid}")
            
            # 启动输出处理线程
            self.output_thread = OutputHandlerThread(self.process)
            self.output_thread.output_received.connect(self._handle_output)
            self.output_thread.start()
            
            # 设置状态
            self.running = True
            self.stopping = False
            
            # 发送启动信号
            self.signals.started.emit()
            
            # 等待进程结束
            self.exit_code = self.process.wait()
            
            # 发送停止信号
            self.signals.stopped.emit(self.exit_code)
        finally:
            self.running = False
            self.stopping = False
            self.process = None

    def _ensure_language_setting(self):
        """确保游戏语言设置文件正确配置"""
        options_file = os.path.join(self.minecraft_directory, "options.txt")
        
        try:
            # 读取现有选项
            options = {}
            if os.path.exists(options_file):
                with open(options_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            options[key.strip()] = value.strip()
            
            # 强制设置语言选项
            options['lang'] = self.language
            
            # 写入新选项
            with open(options_file, 'w', encoding='utf-8') as f:
                for key, value in options.items():
                    f.write(f"{key}:{value}\n")
            
            self.signals.output.emit(f"已设置游戏语言: {self.language}")
        except Exception as e:
            self.signals.error.emit(f"设置游戏语言时出错: {str(e)}")

    def _handle_output(self, message, is_stdout):
        """处理输出消息"""
        # 检查语言设置是否生效
        if "Setting user: " in message:
            self.signals.output.emit(f"语言设置: {self.language}")
        
        # 发送消息
        if is_stdout:
            self.signals.output.emit(message)
        else:
            self.signals.error.emit(message)
    
    def stop(self, force=False):
        """停止游戏进程"""
        print('正在停止游戏', self.running, self.stopping)
        if not self.running or self.stopping:
            return
        
        self.stopping = True
        
        try:
            # 通知停止
            print('正在停止游戏')
            self.signals.output.emit("正在停止游戏...")
            
            # 首先尝试向主进程发送信号
            try:
                if platform.system() == "Windows":
                    # Windows: 使用terminate
                    print('正在停止游戏 terminate')
                    self.process.terminate()
                else:
                    # Unix: 发送SIGTERM
                    self.process.send_signal(signal.SIGTERM)
            except:
                pass

            # 记录要终止的进程
            pids_to_kill = []
            
            # 获取主进程信息
            if self.process.poll() is None:
                pids_to_kill.append(self.process.pid)
            
            # 获取所有子进程
            for child in self.process_tree:
                try:
                    if child.is_running() and child.pid != os.getpid():
                        pids_to_kill.append(child.pid)
                except psutil.NoSuchProcess:
                    continue
            
            # 去重
            pids_to_kill = list(set(pids_to_kill))
            
            print(f'尝试停止进程 {pids_to_kill}')
            self.output.emit(f"尝试停止进程: {pids_to_kill}")
            
            # 如果需要强制停止或普通停止失败
            if force or not self.wait_for_exit(5):
                # 强制终止所有进程
                for pid in pids_to_kill:
                    try:
                        if platform.system() == "Windows":
                            # Windows: 使用taskkill
                            print(f'尝试停止进程 使用taskkill {pid}')
                            subprocess.run([
                                "taskkill", 
                                "/F",  # 强制
                                "/T",  # 终止子进程
                                "/PID", str(pid)
                            ], check=False, timeout=5)
                        else:
                            # Unix: 发送SIGKILL
                            os.kill(pid, signal.SIGKILL)
                    except Exception as e:
                        self.output.emit(f"停止进程错误: {str(e)}")
            
            # 确保进程终止
            for pid in pids_to_kill:
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    process.wait(timeout=2)
                except:
                    print(f'尝试停止进程 确保进程终止 {pid}')
                    pass
            
            # 清除标准输出
            if self.process.poll() is None:
                self.process.stdout.close()
            
            # 尝试正常停止
            if self._attempt_graceful_shutdown():
                return
                
            # 强制终止
            self._force_shutdown()

            # 停止输出线程
            if self.output_thread:
                self.output_thread.stop()
                self.output_thread.quit()
                self.output_thread.wait()
                self.output_thread = None

        except Exception as e:
            self.signals.error.emit(f"停止请求错误: {str(e)}")

    def _attempt_graceful_shutdown(self):
        """尝试正常停止进程"""
        try:
            if not self.process or not self.process.pid:
                return False
                
            # 对于 Windows 系统
            if platform.system() == "Windows":
                # 发送 CTRL_C_EVENT
                os.kill(self.process.pid, signal.CTRL_C_EVENT)
            else:
                # 对于 Unix 系统
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            
            # 等待一段时间
            for _ in range(10):
                if self.process.poll() is not None:
                    return True
                time.sleep(0.2)
                
            return False
        except:
            return False
    
    def _force_shutdown(self):
        """强制停止进程树"""
        try:
            if not self.process or not self.process.pid:
                return False
                
            # 获取要终止的进程列表
            pids_to_kill = [self.process.pid]
            try:
                parent = psutil.Process(self.process.pid)
                children = parent.children(recursive=True)
                pids_to_kill.extend(p.pid for p in children)
            except:
                pass
            
            # 终止所有进程
            for pid in pids_to_kill:
                try:
                    if platform.system() == "Windows":
                        subprocess.run([
                            "taskkill", 
                            "/F",  # 强制
                            "/T",  # 终止子进程
                            "/PID", str(pid)
                        ], timeout=5, capture_output=True)
                    else:
                        os.kill(pid, signal.SIGKILL)
                except:
                    continue
        except:
            pass
    
    def is_running(self):
        """检查游戏是否正在运行"""
        return self.running
    
    def get_exit_code(self):
        """获取游戏退出代码"""
        return self.exit_code if hasattr(self, 'exit_code') else None
    
    def cleanup(self):
        """清理所有资源"""
        if self.running:
            self.stop()
        
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                if self.process.stdout:
                    self.process.stdout.close()
                self.process.terminate()
            except:
                pass
            self.process = None


