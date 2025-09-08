import os
import subprocess
import sys
import platform
from pathlib import Path
from typing import List, Optional, Tuple

class JavaPathFinder:
    """自动查找系统中Java安装路径的工具类"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.found_java_paths = []
    
    def find_all_java_installations(self) -> List[Tuple[str, str]]:
        """
        查找系统中所有Java安装路径
        
        Returns:
            List[Tuple[str, str]]: 包含(路径, 版本)的元组列表
        """
        self.found_java_paths = []
        
        # 按优先级尝试不同的查找方法
        methods = [
            self._check_environment_variables,
            self._check_common_install_paths,
            self._search_with_system_command,
            self._search_in_program_files
        ]
        
        for method in methods:
            try:
                method()
            except Exception as e:
                print(f"方法 {method.__name__} 执行出错: {e}")
                continue
        
        return self._remove_duplicates_and_validate()
    
    def _check_environment_variables(self):
        """检查环境变量中的Java路径"""
        env_vars = ['JAVA_HOME', 'JRE_HOME']
        
        for env_var in env_vars:
            java_home = os.environ.get(env_var)
            if java_home and os.path.exists(java_home):
                java_exe = self._find_java_exe_in_path(java_home)
                if java_exe:
                    version = self._get_java_version(java_exe)
                    self.found_java_paths.append((java_exe, version or "未知版本"))
    
    def _check_common_install_paths(self):
        """检查常见的Java安装路径"""
        common_paths = []
        
        if self.system == "windows":
            common_paths = [
                "C:\\Program Files\\Java",
                "C:\\Program Files (x86)\\Java",
                os.path.expanduser("~\\AppData\\Local\\Programs\\Java"),
                os.path.expanduser("~\\AppData\\Local\\Packages"),
                "C:\\Program Files",
                "C:\\Program Files (x86)",
            ]
        elif self.system == "darwin":  # macOS
            common_paths = [
                "/Library/Java/JavaVirtualMachines",
                "/System/Library/Java/JavaVirtualMachines",
                os.path.expanduser("~/Library/Java/JavaVirtualMachines")
            ]
        elif self.system == "linux":
            common_paths = [
                "/usr/lib/jvm",
                "/usr/java",
                "/opt/java"
            ]
        
        for base_path in common_paths:
            if os.path.exists(base_path):
                self._search_java_in_directory(base_path)
    
    def _search_with_system_command(self):
        """使用系统命令查找Java"""
        try:
            if self.system == "windows":
                # 使用where命令查找java.exe
                result = subprocess.run(
                    ["where", "java.exe"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        java_path = line.strip()
                        if java_path and os.path.exists(java_path):
                            version = self._get_java_version(java_path)
                            self.found_java_paths.append((java_path, version or "未知版本"))
            
            else:  # Linux/MacOS
                # 使用which命令查找java
                result = subprocess.run(
                    ["which", "java"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    java_path = result.stdout.strip()
                    if java_path and os.path.exists(java_path):
                        version = self._get_java_version(java_path)
                        self.found_java_paths.append((java_path, version or "未知版本"))
                        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass  # 命令执行失败时静默处理
    
    def _search_in_program_files(self):
        """在Program Files目录中搜索Java安装"""
        if self.system != "windows":
            return
        
        program_files_dirs = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        ]
        
        for program_files in program_files_dirs:
            if os.path.exists(program_files):
                for item in os.listdir(program_files):
                    if item.lower().startswith("java"):
                        java_dir = os.path.join(program_files, item)
                        if os.path.isdir(java_dir):
                            self._search_java_in_directory(java_dir)
    
    def _search_java_in_directory(self, directory: str):
        """在指定目录中搜索Java可执行文件"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower() in ["java", "java.exe"]:
                    java_path = os.path.join(root, file)
                    # 检查是否是真正的可执行文件
                    if self._is_valid_java_exe(java_path):
                        version = self._get_java_version(java_path)
                        self.found_java_paths.append((java_path, version or "未知版本"))
    
    def _find_java_exe_in_path(self, java_home: str) -> Optional[str]:
        """在JAVA_HOME路径中查找java可执行文件"""
        possible_paths = []
        
        if self.system == "windows":
            possible_paths = [
                os.path.join(java_home, "bin", "java.exe"),
                os.path.join(java_home, "java.exe")
            ]
        else:
            possible_paths = [
                os.path.join(java_home, "bin", "java"),
                os.path.join(java_home, "java")
            ]
        
        for path in possible_paths:
            if os.path.exists(path) and self._is_valid_java_exe(path):
                return path
        
        return None
    
    def _is_valid_java_exe(self, path: str) -> bool:
        """验证找到的文件是真正的Java可执行文件"""
        if not os.path.isfile(path):
            return False
        
        # 检查文件大小（Java可执行文件通常不会太小）
        file_size = os.path.getsize(path)
        if file_size < 1024:  # 小于1KB可能是无效文件
            return False
        
        # 检查文件权限（在Unix系统上需要可执行权限）
        if self.system != "windows":
            return os.access(path, os.X_OK)
        
        return True
    
    def _get_java_version(self, java_path: str) -> Optional[str]:
        """获取Java版本信息"""
        try:
            result = subprocess.run(
                [java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 or result.stderr:
                # Java版本信息通常输出到stderr
                output = result.stderr or result.stdout
                lines = output.split('\n')
                for line in lines:
                    if "version" in line.lower():
                        return line.strip()
            return None
        except Exception:
            return None
    
    def _remove_duplicates_and_validate(self) -> List[Tuple[str, str]]:
        """去除重复路径并验证Java有效性"""
        unique_paths = {}
        for path, version in self.found_java_paths:
            # 规范化路径（解析符号链接等）
            try:
                real_path = os.path.realpath(path)
                if real_path not in unique_paths:
                    unique_paths[real_path] = version
            except Exception:
                continue
        
        # 返回排序后的结果（按路径长度排序，通常较短的路径是系统默认安装）
        return sorted(
            [(path, version) for path, version in unique_paths.items()],
            key=lambda x: len(x[0])
        )
    
    def recommend_best_java(self, java_installations: List[Tuple[str, str]]) -> Optional[str]:
        """从找到的Java安装中推荐最佳选择"""
        if not java_installations:
            return None
        
        # 优先选择JAVA_HOME中的Java
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            java_home = os.path.realpath(java_home)
            for path, version in java_installations:
                if java_home in os.path.realpath(path):
                    return path
        
        # 选择最新版本或最合适的版本
        return java_installations[0][0]


# 使用示例
if __name__ == "__main__":
    finder = JavaPathFinder()
    java_installations = finder.find_all_java_installations()
    
    print("找到的Java安装路径:")
    for i, (path, version) in enumerate(java_installations, 1):
        print(f"{i}. {version} - {path}")
    
    if java_installations:
        best_java = finder.recommend_best_java(java_installations)
        print(f"\n推荐使用的Java: {best_java}")
    else:
        print("未找到Java安装")
