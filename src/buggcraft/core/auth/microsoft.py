import time
import json
import requests
import traceback

from urllib.parse import urlparse, parse_qs, quote
from base64 import urlsafe_b64encode
from hashlib import sha256
from secrets import token_urlsafe

from PySide6.QtWidgets import (QVBoxLayout, QDialog)
from PySide6.QtCore import Signal, QObject, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView

from core.skin import process_skin_info

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
import json
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


class MicrosoftAuthenticator(QObject):
    """Microsoft 正版登录认证类"""
    
    def __init__(self, parent=None, minecraft_directory=None):
        super().__init__(parent)
        self.signals = MicrosoftAuthSignals()
        self.minecraft_directory = minecraft_directory
        # 创建解码器实例
        self.decoder = JWTDecoder()
        # OAuth 认证参数
        self.client_id = "00000000402b5328"
        self.scope = "XboxLive.signin offline_access"
        self.redirect_uri = "https://login.live.com/oauth20_desktop.srf"
        self.authorization_url = f"https://login.live.com/oauth20_authorize.srf?client_id={self.client_id}&response_type=code&redirect_uri={quote(self.redirect_uri)}&scope={quote(self.scope)}"
        
        # 状态变量
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

    def start_login(self):
        """启动登录流程（打开浏览器窗口）"""
        self.signals.progress.emit("正在打开微软登录页面...")
        self.open_login_dialog()

    def open_login_dialog(self):
        """打开内置浏览器登录窗口"""
        dialog = QDialog()
        dialog.setWindowTitle("Microsoft 登录")
        dialog.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        self.webview = QWebEngineView()
        self.webview.load(QUrl(self.authorization_url))
        
        # 监听 URL 变化以捕获授权码
        self.webview.urlChanged.connect(lambda url: self.handle_url_changed(url, dialog))
        
        layout.addWidget(self.webview)
        dialog.setLayout(layout)
        dialog.exec_()

    def handle_url_changed(self, url, dialog):
        """处理浏览器URL变化"""
        url_str = url.toString()
        if url_str.startswith(self.redirect_uri):
            # 提取授权码
            if "code=" in url_str:
                try:
                    parsed = urlparse(url_str)
                    query = parse_qs(parsed.query)
                    self.authorization_code = query.get('code', [None])[0]
                    
                    if self.authorization_code:
                        dialog.close()
                        self.signals.progress.emit("成功获取授权码，正在交换令牌...")
                        self.get_oauth20_token()
                    else:
                        self.signals.failure.emit("未能从重定向URL中获取授权码")
                except Exception as e:
                    self.signals.failure.emit(f"解析重定向URL时出错: {str(e)}")
    
    def get_oauth20_token(self):
        """使用授权码获取Microsoft访问令牌"""
        try:
            url = "https://login.live.com/oauth20_token.srf"
            data = {
                'client_id': self.client_id,
                'code': self.authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
            }
            
            self.signals.progress.emit("正在获取Microsoft访问令牌...")
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.oauth20_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                
                if self.oauth20_token:
                    self.signals.progress.emit("成功获取Microsoft令牌，正在获取Xbox Live令牌...")
                    self.get_xbox_live_token()
                else:
                    self.signals.failure.emit("Microsoft令牌响应中缺少访问令牌")
            else:
                self.signals.failure.emit(f"获取Microsoft令牌失败: HTTP {response.status_code}\n{response.text}")
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
            
            self.signals.progress.emit("正在获取Xbox Live令牌...")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.xbox_token = token_data.get('Token')
                self.user_hash = token_data.get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs')
                
                if self.xbox_token and self.user_hash:
                    self.signals.progress.emit("成功获取Xbox Live令牌，正在获取XSTS令牌...")
                    self.get_xsts_token()
                else:
                    self.signals.failure.emit("Xbox Live令牌响应中缺少必要字段")
            else:
                self.signals.failure.emit(f"获取Xbox Live令牌失败: HTTP {response.status_code}\n{response.text}")
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
            
            self.signals.progress.emit("正在获取XSTS令牌...")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.xsts_token = token_data.get('Token')
                
                if self.xsts_token:
                    self.signals.progress.emit("成功获取XSTS令牌，正在获取Minecraft令牌...")
                    self.get_minecraft_token()
                else:
                    self.signals.failure.emit("XSTS令牌响应中缺少令牌")
            else:
                self.signals.failure.emit(f"获取XSTS令牌失败: HTTP {response.status_code}\n{response.text}")
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
            
            self.signals.progress.emit("正在获取Minecraft令牌...")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.minecraft_token = token_data.get('access_token')
                if self.minecraft_token:
                    self.signals.progress.emit("成功获取Minecraft令牌!")
                    self.signals.progress.emit("正在查询许可...")
                    print(self.minecraft_token)
                    if not self.get_minecraft_mcstore():
                        return
                    self.signals.progress.emit("正在获取玩家档案...")
                    self.get_minecraft_profile()
                else:
                    self.signals.failure.emit("缺少访问令牌")
            else:
                self.signals.failure.emit(f"网络可能异常，获取Minecraft令牌失败 STATUS: {response.status_code}")
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
            
            self.signals.progress.emit("正在获取Minecraft玩家档案...")
            response = requests.get(url, headers=headers)
            if response.status_code == 404:
                self.signals.failure.emit("玩家档案未建立，请先使用官方Minecraft启动器创建游戏名称​​")
                return
            
            if response.status_code == 200:
                profile_data = response.json()
                self.minecraft_username = profile_data.get('name')
                self.minecraft_uuid = profile_data.get('id')
                minecraft_skins = profile_data.get('skins', [])
                if minecraft_skins and self.minecraft_directory:
                    self.minecraft_skin = process_skin_info(uuid=self.minecraft_uuid, skin_info=minecraft_skins[0], output_path=self.minecraft_directory)
                
                if self.minecraft_username and self.minecraft_uuid:
                    self.signals.success.emit(self.minecraft_username, {
                        'uuid': self.minecraft_uuid,
                        'skin': self.minecraft_skin,
                        'token': self.minecraft_token
                    })
                    self.signals.progress.emit("认证成功！")
                else:
                    self.signals.failure.emit("玩家档案响应中缺少用户名或UUID")
            else:
                self.signals.failure.emit(f"获取玩家档案失败: HTTP {response.status_code}\n{response.text}")
        except Exception as e:
            traceback.print_exc()
            self.signals.failure.emit(f"获取玩家档案时发生异常: {str(e)}")
    
    def get_minecraft_mcstore(self):
        """检查游戏拥有情况
        使用Minecraft的访问令牌来检查该账号是否包含产品许可。"""
        headers = {
            'Authorization': f'Bearer {self.minecraft_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get('https://api.minecraftservices.com/entitlements/mcstore', headers=headers)
            if response.status_code == 200:
                data = response.json()
                minecraft_signature = []
                for i in data['items']:
                    name = i.get('name', None)
                    if not name in ['game_minecraft', 'product_minecraft']:
                        continue
                    minecraft_signature.append(name)
                
                if 'game_minecraft' in minecraft_signature and 'product_minecraft' in minecraft_signature:
                    return True
                
                self.signals.failure.emit("未购买正版")
            else:
                self.signals.failure.emit(f"网络可能异常，获取产品许可失败 STATUS: {response.status_code}")
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
        filepath = os.path.join(filepath, "user", "auth_credentials.json")
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        try:
            # 获取过期时间
            self.decoder.token = self.minecraft_token
            expiration = self.decoder.get_expiration()
            if expiration and self.minecraft_token:
                self.signals.progress.emit(f"Token 过期时间: {expiration['timestamp']}")
                print(f"Token 过期时间戳: {expiration['timestamp']}")
                print(f"Token 过期时间: {expiration['formatted']}")
            
            # 检查是否已过期
            if self.decoder.is_expired() and expiration is not None:
                print("⚠️  Token 已过期")
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
            traceback.print_exc()
            self.signals.failure.emit(f"保存凭据失败: {str(e)}")
            return False
    
    def load_credentials(self, filepath):
        """从文件加载认证信息"""
        import os, shutil

        filepath = os.path.join(filepath, "user", "auth_credentials.json")
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        if not os.path.isfile(filepath):
            return False
        
        self.signals.progress.emit("检测到保存的认证信息，尝试自动登录...")
        try:
            with open(filepath, 'r') as f:
                credentials = json.load(f)
            
            self.decoder.token = credentials.get('minecraft_token')
            expiration = self.decoder.get_expiration()
            if expiration:
                print(f"Token 过期时间戳: {expiration['timestamp']}")
                print(f"Token 过期时间: {expiration['formatted']}")
            
            # 检查是否已过期
            if self.decoder.is_expired() and expiration is not None:
                print("⚠️  Token 已过期")
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
                self.signals.success.emit(self.minecraft_username, {
                    'uuid': self.minecraft_uuid,
                    'skin': self.minecraft_skin,
                    'token': self.minecraft_token
                })
                self.signals.progress.emit("认证成功！")
            elif self.minecraft_username and not self.minecraft_token:
                # 离线登录
                self.signals.success.emit(self.minecraft_username, {
                    'uuid': self.minecraft_uuid,
                    'skin': self.minecraft_skin,
                    'token': self.minecraft_token
                })
                self.signals.progress.emit("认证成功！")

            return True
        except Exception as e:
            self.signals.failure.emit(f"加载凭据失败: {str(e)}")
            return False
    
    def is_authenticated(self):
        """检查是否已认证"""
        return bool(self.minecraft_token and self.minecraft_username and self.minecraft_uuid)
    
    def clear(self, filepath=None):
        """清空认证信息"""
        import os, shutil
        filepath = os.path.join(filepath, "user", "auth_credentials.json")
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

        if os.path.isfile(filepath):
            os.remove(filepath)


# 使用示例
if __name__ == "__main__":
    # 你的 JWT Token
    jwt_token = "eyJraWQiOiIwNDkxODEiLCJhbGciOiJSUzI1NiJ9.eyJ4dWlkIjoiMjUzNTQ0NDgzNjA5NzgwNyIsImFnZyI6IkFkdWx0Iiwic3ViIjoiM2M2NmYzZjctMjZmMC01MjQxLWIwNTgtZDdlMGMzY2FjYTczIiwiYXV0aCI6IlhCT1giLCJucyI6ImRlZmF1bHQiLCJyb2xlcyI6W10sImlzcyI6ImF1dGhlbnRpY2F0aW9uIiwiZmxhZ3MiOlsib3JkZXJzXzIwMjIiLCJtdWx0aXBsYXllciIsInR3b2ZhY3RvcmF1dGgiLCJtc2FtaWdyYXRpb25fc3RhZ2U0Il0sInByb2ZpbGVzIjp7Im1jIjoiYmVhMDU5MmYtZTBiNC00MjkzLTlmMWYtYjYxM2FmZWQ1ZDBlIn0sInBsYXRmb3JtIjoiUENfTEFVTkNIRVIiLCJwZmQiOlt7InR5cGUiOiJtYyIsImlkIjoiYmVhMDU5MmYtZTBiNC00MjkzLTlmMWYtYjYxM2FmZWQ1ZDBlIiwibmFtZSI6Ikp1bnNpenoifV0sIm5iZiI6MTc1NjkxMzE2MywiZXhwIjoxNzU2OTk5NTYzLCJpYXQiOjE3NTY5MTMxNjN9.xkkXt7GSR-5zPmb6tnijzYDElnOt0fhHzmZ3Vd_gEc6LWvvMZmP01GArfnBQegMx-rRKUj4vrCVVCaUT87PIJ7gCLGlIzwXrpcLkgDBFui7Bk4n_YMhPw2WJeMusMXuzGXbvOF2BREe-ZUr8KNHJBMzkKyoPNe0HTkjj4bTCNDttqYe6Ok0SQNYnze-wXN1pspx1WHKbWNt6stAIemw84hdjcNSiOiHqxdaXe2hmXM9GUOV8PmiPdoZPyF3w9B1oIlongSsHxiewec26TjswW_R8vjyAb5fAFH_dq1HdIOYqvIRY3rQPjZ0OepOndcMGdze_h6I9qGg1KXam5qca2Q"
    
    # 创建解码器实例
    decoder = JWTDecoder(jwt_token)
    
    # 获取过期时间
    expiration = decoder.get_expiration()
    if expiration:
        print(f"Token 过期时间戳: {expiration['timestamp']}")
        print(f"Token 过期时间: {expiration['formatted']}")
        
        # 检查是否已过期
        if decoder.is_expired():
            print("⚠️  Token 已过期")
        else:
            print("✅  Token 仍然有效")
    
    # 获取签发时间
    issued_at = decoder.get_issued_at()
    if issued_at:
        print(f"Token 签发时间: {issued_at['formatted']}")
    
    # 获取所有声明
    claims = decoder.get_all_claims()
    if claims:
        print("\nToken 中的所有声明:")
        for key, value in claims.items():
            print(f"  {key}: {value}")

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
#             print('YES')
