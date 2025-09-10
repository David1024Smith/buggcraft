import time
import json
import traceback
import webbrowser
import logging

from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import Signal, QObject, QTimer

from core.skin import process_skin_info



logger = logging.getLogger(__name__)


class MicrosoftAuthSignals(QObject):
    """Microsoft 认证信号"""
    success = Signal(str, dict)  # 用户名, UUID
    failure = Signal(str)       # 错误消息
    progress = Signal(str)      # 进度消息


class MinecraftSignals(QObject):
    """Minecraft 信号类"""
    output = Signal(str)
    started = Signal()
    stopped = Signal(int)  # 退出代码
    error = Signal(str)
    progress = Signal(int)  # 进度百分比


import base64
from datetime import datetime

class JWTDecoder:
    """JWT Token 解码器类"""
    
    def __init__(self, token=None):
        self.token = token
        self.header = None
        self.payload = None
        self.signature = None
        self.decoded = False
        
    def decode(self):
        """解码 JWT Token"""
        try:
            # 分割 token 的三个部分
            parts = self.token.split('.')
            if len(parts) != 3:
                raise ValueError("无效的 JWT Token: 必须包含三个部分")
            
            # 解码头部
            header_encoded = parts[0]
            self.header = self._decode_part(header_encoded)
            
            # 解码载荷
            payload_encoded = parts[1]
            self.payload = self._decode_part(payload_encoded)
            
            # 签名部分
            self.signature = parts[2]
            
            self.decoded = True
            return True
            
        except Exception as e:
            return False
    
    def _decode_part(self, part):
        """解码单个 JWT 部分"""
        # 添加必要的填充
        padding = len(part) % 4
        if padding:
            part += '=' * (4 - padding)
        
        # 解码
        decoded_bytes = base64.urlsafe_b64decode(part)
        return json.loads(decoded_bytes)
    
    def get_expiration(self):
        """获取过期时间"""
        if not self.decoded:
            if not self.decode():
                return None
        
        if 'exp' in self.payload:
            exp_timestamp = self.payload['exp']
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            exp_formatted = exp_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'timestamp': exp_timestamp,
                'formatted': exp_formatted
            }
        return None
    
    def get_issued_at(self):
        """获取签发时间"""
        if not self.decoded:
            if not self.decode():
                return None
        
        if 'iat' in self.payload:
            iat_timestamp = self.payload['iat']
            iat_datetime = datetime.fromtimestamp(iat_timestamp)
            iat_formatted = iat_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'timestamp': iat_timestamp,
                'formatted': iat_formatted
            }
        return None
    
    def is_expired(self):
        """检查 Token 是否已过期"""
        expiration = self.get_expiration()
        if not expiration:
            return None
        
        current_time = datetime.now().timestamp()
        return expiration['timestamp'] < current_time
    
    def get_all_claims(self):
        """获取所有声明（claims）"""
        if not self.decoded:
            if not self.decode():
                return None
        return self.payload
    
    def get_header(self):
        """获取头部信息"""
        if not self.decoded:
            if not self.decode():
                return None
        return self.header


import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from utils.network import minecraft_httpx


class MinecraftHttpServer(HTTPServer):
    
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate = True):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.timeout = 500

    def serve_forever(self):
        self.stopped = False                    
        """Handle one request at a time until doomsday."""
        while not self.stopped:
            self.handle_request()

    def shutdown(self):
        self.stopped = True
        self.server_close()


class CallbackHandler(BaseHTTPRequestHandler):
    """本地服务器请求处理器"""
    def do_GET(self):
        """处理 GET 请求"""
        # 只处理指定的回调路径
        if self.path.startswith('/auth_callback'):
            # 解析URL中的查询参数
            query = urlparse(self.path).query
            params = parse_qs(query)
            code = params.get('code', [None])[0]  # 获取授权码
            error = params.get('error', [None])[0]  # 获取错误信息（如果有）
            
            # 根据是否获取到授权码进行不同处理
            if code:
                # 发送HTTP 200响应给浏览器
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()  # 结束头部设置
                response_content = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>认证成功</title>
                    </head>
                    <body>
                        <h1>认证成功！</h1>
                        <p>你可以安全地关闭此窗口并返回应用程序。</p>
                    </body>
                    </html>
                """
                self.wfile.write(response_content.encode('utf-8'))  # 关键修改：添加 .encode('utf-8')
                # 将授权码设置到服务器对象中，以便主线程获取
                self.server.auth_code = code
                # 安排服务器在短时间内关闭
                self.server.shutdown()
            elif error:
                # 处理错误情况
                error_description = params.get('error_description', ['未知错误'])[0]
                logger.info(f'error_description {error_description}')
                self.send_error(500, f"OAuth Error: {error}", error_description)
                self.server.auth_error = f"{error}: {error_description}"
                self.server.shutdown()
            else:
                self.send_error(404, "Not Found", "未找到指定的回调参数")
        else:
            self.send_error(404, "Not Found", "页面未找到")

    def log_message(self, format, *args):
        """禁用默认日志输出，保持控制台整洁"""
        return


class AsyncAuthServer(QObject):
    """异步认证服务器"""
    code_received = Signal(str)  # 授权码信号
    error_occurred = Signal(str)  # 错误信号
    signal_timeout = Signal()  # 超时信号
    
    def __init__(self, port=47952, timeout=300):
        super().__init__()
        self.port = port
        self.timeout = timeout
        self.server = None
        self.server_thread = None
        self.auth_code = None
        self.auth_error = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_timeout)
        self.shutdown_timeout = 5  # 服务器关闭超时时间(秒)
        
    def start(self):
        """启动服务器"""
        try:
            self.server = MinecraftHttpServer(('localhost', self.port), CallbackHandler)
            self.server.auth_code = None
            self.server.auth_error = None
            
            # 启动服务器线程
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # 启动超时计时器
            self.start_time = time.time()
            self.timer.start(100)  # 每100毫秒检查一次
            
            return True
        except Exception as e:
            self.error_occurred.emit(f"启动服务器失败: {str(e)}")
            return False
    
    def check_timeout(self):
        """检查是否超时"""
        if self.auth_code or self.auth_error:
            logger.info('检查是否超时1')
            self.timer.stop()
            return
            
        if time.time() - self.start_time > self.timeout:
            logger.info('检查是否超时2')
            self.timer.stop()
            self.timeout.emit()
            
        # 检查服务器状态
        if self.server:
            if self.server.auth_code:
                self.auth_code = self.server.auth_code
                self.code_received.emit(self.auth_code)
                self.stop()
            elif self.server.auth_error:
                self.auth_error = self.server.auth_error
                self.error_occurred.emit(self.auth_error)
                self.stop()
        
    def stop(self):
        """停止服务器 - 最终版"""
        self.timer.stop()
        if self.server:
            try:
                self.server.shutdown()
                logger.info('服务器关闭完成')
            except Exception as e:
                traceback.logger.info_exc()
                logger.info(f'服务器关闭异常: {e}')
        
        # 清理线程
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)


class MicrosoftAuthenticator(QObject):
    """Microsoft 正版登录认证类"""
    
    def __init__(self, parent=None, skins_cache_path=None):
        super().__init__(parent)
        self.oauth_thread = None
        self.signals = MicrosoftAuthSignals()
        self.skins_cache_path = skins_cache_path  # 头像save
        self.decoder = JWTDecoder()  # 创建解码器实例

        # OAuth 认证参数
        # self.client_id = "00000000402b5328"
        self.client_id = "9372e575-a673-4100-bed9-b5d2e4023d30"
        self.client_secret = ""
        self.scope = "XboxLive.signin offline_access"
        self.redirect_uri = "http://localhost:47952/auth_callback"
        self.authorization_url = (
            f"https://login.live.com/oauth20_authorize.srf?"
            f"client_id={self.client_id}&"
            f"client_secret={self.client_secret}&"
            f"response_type=code&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={self.scope}"
        )
        
        # 状态变量
        self.authorization_code = None
        self.microsoft_token = None
        self.refresh_token = None
        self.user_hash = None
        self.xbox_token = None
        self.xsts_token = None
        
        self.minecraft_uuid = None
        self.minecraft_username = None
        self.minecraft_token = None
        self.minecraft_version = '1.21.8-Forge_58.1.0-OptiFine_J6_pre16'
        self.minecraft_skin = None
        self.minecraft_login_type = "offline"
        

    def start_login(self):
        """启动登录流程（使用系统浏览器和本地服务器）"""
        # 创建异步服务器
        self.auth_server = AsyncAuthServer()
        self.auth_server.code_received.connect(self.handle_auth_code)
        self.auth_server.error_occurred.connect(self.signals.failure)
        self.auth_server.signal_timeout.connect(lambda: self.signals.failure.emit("登录超时，请重试"))
        
        if self.auth_server.start():
            # 打开浏览器
            self.signals.progress.emit("[0/9] 正在调起认证...")
            webbrowser.open(self.authorization_url)
            self.signals.progress.emit("[1/9] 请在完成登录...")
        else:
            self.signals.failure.emit("无法启动服务器")
    
    def handle_auth_code(self, auth_code):
        """处理接收到的授权码"""
        self.authorization_code = auth_code
        self.signals.progress.emit("[2/9] 交换令牌...")

        # 启动服务器线程
        self.oauth_thread = threading.Thread(target=self.get_oauth20_token)
        self.oauth_thread.daemon = True
        self.oauth_thread.start()
        
    def get_oauth20_token(self):
        """使用授权码获取Microsoft访问令牌"""
        try:
            url = "https://login.live.com/oauth20_token.srf"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': self.authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
            }

            self.signals.progress.emit("[3/9] 获取令牌...")
            status_code, response_data = minecraft_httpx.post(url, data)
            
            if status_code == 200:
                self.oauth20_token = response_data.get('access_token')
                self.refresh_token = response_data.get('refresh_token')
                
                if self.oauth20_token:
                    self.get_xbox_live_token()
                else:
                    self.signals.failure.emit("Microsoft令牌响应中缺少访问令牌")
            else:
                logger.info(f"get_oauth20_token 获取Microsoft令牌失败: HTTP {status_code}\n{response_data}")
                self.signals.failure.emit(f"获取Microsoft令牌失败: HTTP {status_code}\n{response_data}")
        except Exception as e:
            self.signals.failure.emit(f"获取Microsoft令牌时发生异常: {str(e)}")
    
    def get_xbox_live_token(self):
        """获取Xbox Live令牌"""
        try:
            url = "https://user.auth.xboxlive.com/user/authenticate"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            data = {
                "Properties": {
                    "AuthMethod": "RPS",
                    "SiteName": "user.auth.xboxlive.com",
                    "RpsTicket": f"d={self.oauth20_token}"
                },
                "RelyingParty": "http://auth.xboxlive.com",
                "TokenType": "JWT"
            }
            
            self.signals.progress.emit("[4/9] 获取令牌...")
            status_code, response_data = minecraft_httpx.post(url, data, headers=headers)
            
            if status_code == 200:
                self.xbox_token = response_data.get('Token')
                self.user_hash = response_data.get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs')
                
                if self.xbox_token and self.user_hash:
                    self.get_xsts_token()
                else:
                    self.signals.failure.emit("Xbox Live令牌响应中缺少必要字段")
            else:
                self.signals.failure.emit(f"获取Xbox Live令牌失败: HTTP {status_code}\n{response_data}")
        except Exception as e:
            self.signals.failure.emit(f"获取Xbox Live令牌时发生异常: {str(e)}")
    
    def get_xsts_token(self):
        """获取XSTS令牌"""
        try:
            url = "https://xsts.auth.xboxlive.com/xsts/authorize"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            data = {
                "Properties": {
                    "SandboxId": "RETAIL",
                    "UserTokens": [self.xbox_token]
                },
                "RelyingParty": "rp://api.minecraftservices.com/",
                "TokenType": "JWT"
            }
            
            self.signals.progress.emit("[5/9] 获取令牌...")
            status_code, response_data = minecraft_httpx.post(url, data, headers=headers)
            
            if status_code == 200:
                self.xsts_token = response_data.get('Token')
                
                if self.xsts_token:
                    self.get_minecraft_token()
                else:
                    self.signals.failure.emit("XSTS令牌响应中缺少令牌")
            else:
                self.signals.failure.emit(f"获取XSTS令牌失败: HTTP {status_code}\n{response_data}")
        except Exception as e:
            self.signals.failure.emit(f"获取XSTS令牌时发生异常: {str(e)}")
    
    def get_minecraft_token(self):
        """获取Minecraft访问令牌"""
        try:
            url = "https://api.minecraftservices.com/authentication/login_with_xbox"
            headers = {
                'Content-Type': 'application/json'
            }
            data = {
                "identityToken": f"XBL3.0 x={self.user_hash};{self.xsts_token}"
            }
            
            self.signals.progress.emit("[6/9] 获取Minecraft令牌...")
            status_code, response_data = minecraft_httpx.post(url, data, headers=headers)
            
            if status_code == 200:
                self.minecraft_token = response_data.get('access_token')
                if self.minecraft_token:
                    if not self.get_minecraft_mcstore():
                        return
                    
                    self.get_minecraft_profile()
                else:
                    self.signals.failure.emit("缺少访问令牌")
            else:
                self.signals.failure.emit(f"网络可能异常，获取Minecraft令牌失败 STATUS: {status_code}\n{response_data}")
        except Exception as e:
            self.signals.failure.emit(f"获取Minecraft令牌时发生异常: {str(e)}")
    
    def get_minecraft_profile(self):
        """获取Minecraft玩家档案"""
        try:
            url = "https://api.minecraftservices.com/minecraft/profile"
            headers = {
                'Authorization': f'Bearer {self.minecraft_token}',
                'Content-Type': 'application/json'
            }
            
            self.signals.progress.emit("[8/9] 获取玩家档案...")
            status_code, response_data = minecraft_httpx.get(url, headers=headers)
            
            if status_code == 404:
                self.signals.failure.emit("玩家档案未建立，请先使用官方Minecraft启动器创建游戏名称​​")
                return
            
            if status_code == 200:
                self.minecraft_username = response_data.get('name')
                self.minecraft_uuid = response_data.get('id')
                minecraft_skins = response_data.get('skins', [])
                if minecraft_skins and self.skins_cache_path:
                    self.signals.progress.emit("[9/9] 获取玩家头像...")
                    self.minecraft_skin = process_skin_info(uuid=self.minecraft_uuid, skin_info=minecraft_skins[0], output_dir=self.skins_cache_path)
                
                if self.minecraft_username and self.minecraft_uuid:
                    self.minecraft_login_type = "online"
                    self.signals.success.emit(self.minecraft_username, {
                        'uuid': self.minecraft_uuid,
                        'skin': self.minecraft_skin,
                        'token': self.minecraft_token,
                        'type': self.minecraft_login_type
                    })
                else:
                    self.signals.failure.emit("玩家档案响应中缺少用户名或UUID")
            else:
                self.signals.failure.emit(f"获取玩家档案失败: HTTP {status_code}\n{response_data}")
        except Exception as e:
            traceback.logger.info_exc()
            self.signals.failure.emit(f"获取玩家档案时发生异常: {str(e)}")
    
    def get_minecraft_mcstore(self):
        """检查游戏拥有情况
        使用Minecraft的访问令牌来检查该账号是否包含产品许可。"""
        headers = {
            'Authorization': f'Bearer {self.minecraft_token}',
            'Content-Type': 'application/json'
        }
        try:
            self.signals.progress.emit("[7/9] 查询正版许可...")
            status_code, response_data = minecraft_httpx.get('https://api.minecraftservices.com/entitlements/mcstore', headers=headers)
            
            if status_code == 200:
                minecraft_signature = []
                for i in response_data['items']:
                    name = i.get('name', None)
                    if not name in ['game_minecraft', 'product_minecraft']:
                        continue
                    minecraft_signature.append(name)
                
                if 'game_minecraft' in minecraft_signature and 'product_minecraft' in minecraft_signature:
                    return True
                
                self.minecraft_login_type = "offline"
                self.signals.failure.emit("未购买正版")
            else:
                self.signals.failure.emit(f"网络可能异常，获取产品许可失败 STATUS: {status_code}")
        except Exception as e:
            self.signals.failure.emit(f"获取产品许可时发生异常: {str(e)}")

        return False

    def get_auth_parameters(self):
        """获取认证参数（用于启动游戏）"""
        return {
            "username": self.minecraft_username,
            "uuid": self.minecraft_uuid,
            "token": self.minecraft_token
        }
    
    def save_credentials(self, filepath):
        """保存认证信息到文件"""
        import os, shutil
        filepath = os.path.join(filepath, "auth_credentials.json")
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        try:
            # 获取过期时间
            self.decoder.token = self.minecraft_token
            expiration = self.decoder.get_expiration()
            if expiration and self.minecraft_token:
                # self.signals.progress.emit(f"Token 过期时间: {expiration['timestamp']}")
                logger.info(f"Token 过期时间戳: {expiration['timestamp']}")
                logger.info(f"Token 过期时间: {expiration['formatted']}")
            
            # 检查是否已过期
            if self.decoder.is_expired() and expiration is not None:
                logger.info("⚠️  Token 已过期")
                if os.path.isfile(filepath):
                    os.remove(filepath)
                self.signals.failure.emit(f"Token 已过期")
                return False

            credentials = {
                "minecraft_uuid": self.minecraft_uuid,
                "minecraft_username": self.minecraft_username,
                "refresh_token": self.refresh_token,
                "minecraft_token": self.minecraft_token,
                "minecraft_skin": self.minecraft_skin
            }
            
            with open(filepath, 'w') as f:
                json.dump(credentials, f)

            return True
        except Exception as e:
            import traceback
            traceback.logger.info_exc()
            self.signals.failure.emit(f"保存凭据失败: {str(e)}")
            return False
    
    def load_credentials(self, filepath):
        """从文件加载认证信息"""
        import os, shutil

        filepath = os.path.join(filepath, "auth_credentials.json")
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        if not os.path.isfile(filepath):
            return False
        
        self.signals.progress.emit("自动登录...")
        try:
            with open(filepath, 'r') as f:
                credentials = json.load(f)
            
            self.decoder.token = credentials.get('minecraft_token')
            expiration = self.decoder.get_expiration()
            if expiration:
                logger.info(f"Token 过期时间戳: {expiration['timestamp']}")
                logger.info(f"Token 过期时间: {expiration['formatted']}")
            
            # 检查是否已过期
            if self.decoder.is_expired() and expiration is not None:
                logger.info("⚠️  Token 已过期")
                if os.path.isfile(filepath):
                    os.remove(filepath)
                
                self.signals.failure.emit(f"Token 已过期")
                return False

            self.refresh_token = credentials.get('refresh_token')
            self.minecraft_username = credentials.get('minecraft_username')
            self.minecraft_uuid = credentials.get('minecraft_uuid')
            self.minecraft_skin = credentials.get('minecraft_skin')
            self.minecraft_token = credentials.get('minecraft_token')
            if self.minecraft_username and self.minecraft_uuid and self.minecraft_token:
                # 正版登录
                self.minecraft_login_type = "online"
                self.signals.success.emit(self.minecraft_username, {
                    'uuid': self.minecraft_uuid,
                    'skin': self.minecraft_skin,
                    'token': self.minecraft_token,
                    'type': self.minecraft_login_type
                })
            elif self.minecraft_username and not self.minecraft_token:
                # 离线登录
                self.minecraft_login_type = "offline"
                self.signals.success.emit(self.minecraft_username, {
                    'uuid': self.minecraft_uuid,
                    'skin': self.minecraft_skin,
                    'token': None,
                    'type': self.minecraft_login_type
                })

            return True
        except Exception as e:
            self.signals.failure.emit(f"加载凭据失败: {str(e)}")
            return False
    
    def is_authenticated(self):
        """检查是否已认证"""
        return bool(self.minecraft_token and self.minecraft_username and self.minecraft_uuid)
    
    def clear(self, filepath=None):
        """清空认证信息"""
        import os
        
        self.authorization_code = None
        self.microsoft_token = None
        self.refresh_token = None
        self.user_hash = None
        self.xbox_token = None
        self.xsts_token = None
        self.minecraft_token = None
        self.minecraft_username = None
        self.minecraft_uuid = None
        self.minecraft_skin = None

        filepath = os.path.join(filepath, "auth_credentials.json")
        if os.path.isfile(filepath):
            os.remove(filepath)


# 使用示例
if __name__ == "__main__":
    # 你的 JWT Token
    jwt_token = "..xkkXt7GSR----"
    
    # 创建解码器实例
    decoder = JWTDecoder(jwt_token)
    
    # 获取过期时间
    expiration = decoder.get_expiration()
    if expiration:
        logger.info(f"Token 过期时间戳: {expiration['timestamp']}")
        logger.info(f"Token 过期时间: {expiration['formatted']}")
        
        # 检查是否已过期
        if decoder.is_expired():
            logger.info("⚠️  Token 已过期")
        else:
            logger.info("✅  Token 仍然有效")
    
    # 获取签发时间
    issued_at = decoder.get_issued_at()
    if issued_at:
        logger.info(f"Token 签发时间: {issued_at['formatted']}")
    
    # 获取所有声明
    claims = decoder.get_all_claims()
    if claims:
        logger.info("\nToken 中的所有声明:")
        for key, value in claims.items():
            logger.info(f"  {key}: {value}")

# if __name__ == "__main__":
#     headers = {
#         'Authorization': f'Bearer eyJraWQiOiIwNDkxODEiLCJhbGciOiJSUzI1NiJ9.eyJ4dWlkIjoiMjUzNTQ0NDgzNjA5NzgwNyIsImFnZyI6IkFkdWx0Iiwic3ViIjoiM2M2NmYzZjctMjZmMC01MjQxLWIwNTgtZDdlMGMzY2FjYTczIiwiYXV0aCI6IlhCT1giLCJucyI6ImRlZmF1bHQiLCJyb2xlcyI6W10sImlzcyI6ImF1dGhlbnRpY2F0aW9uIiwiZmxhZ3MiOlsib3JkZXJzXzIwMjIiLCJtdWx0aXBsYXllciIsInR3b2ZhY3RvcmF1dGgiLCJtc2FtaWdyYXRpb25fc3RhZ2U0Il0sInByb2ZpbGVzIjp7Im1jIjoiYmVhMDU5MmYtZTBiNC00MjkzLTlmMWYtYjYxM2FmZWQ1ZDBlIn0sInBsYXRmb3JtIjoiUENfTEFVTkNIRVIiLCJwZmQiOlt7InR5cGUiOiJtYyIsImlkIjoiYmVhMDU5MmYtZTBiNC00MjkzLTlmMWYtYjYxM2FmZWQ1ZDBlIiwibmFtZSI6Ikp1bnNpenoifV0sIm5iZiI6MTc1NjkxMzE2MywiZXhwIjoxNzU2OTk5NTYzLCJpYXQiOjE3NTY5MTMxNjN9.xkkXt7GSR-5zPmb6tnijzYDElnOt0fhHzmZ3Vd_gEc6LWvvMZmP01GArfnBQegMx-rRKUj4vrCVVCaUT87PIJ7gCLGlIzwXrpcLkgDBFui7Bk4n_YMhPw2WJeMusMXuzGXbvOF2BREe-ZUr8KNHJBMzkKyoPNe0HTkjj4bTCNDttqYe6Ok0SQNYnze-wXN1pspx1WHKbWNt6stAIemw84hdjcNSiOiHqxdaXe2hmXM9GUOV8PmiPdoZPyF3w9B1oIlongSsHxiewec26TjswW_R8vjyAb5fAFH_dq1HdIOYqvIRY3rQPjZ0OepOndcMGdze_h6I9qGg1KXam5qca2Q',
#         'Content-Type': 'application/json'
#     }
#     response = requests.get('https://api.minecraftservices.com/entitlements/mcstore', headers=headers)
#     if response.status_code == 200:
#         data = response.json()
#         minecraft_signature = []
#         for i in data['items']:
#             name = i.get('name', None)
#             if not name in ['game_minecraft', 'product_minecraft']:
#                 continue
#             minecraft_signature.append(name)
        
#         if 'game_minecraft' in minecraft_signature and 'product_minecraft' in minecraft_signature:
#             logger.info('YES')
