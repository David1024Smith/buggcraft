import os
import platform

def find_minecraft_dirs():
    """
    查找全系统所有可能的 Minecraft 目录，按优先级从高到低返回一个列表。
    返回: 一个包含所有真实存在的 .minecraft 绝对路径的列表，按优先级排序。
    """
    system = platform.system()
    home_dir = os.path.expanduser("~")
    checked_paths = []  # 按优先级顺序检查的路径列表
    found_dirs = []     # 真实存在的目录列表

    # 1. 优先级 1: 当前工作目录及其子目录 (最高优先级)
    current_dir = os.getcwd()
    # 检查当前目录下的 .minecraft
    checked_paths.append(os.path.join(current_dir, ".minecraft"))
    # 检查当前目录的父目录下的 .minecraft
    parent_dir = os.path.dirname(current_dir)
    checked_paths.append(os.path.join(parent_dir, ".minecraft"))
    # 检查当前目录下所有一级子目录中的 .minecraft
    try:
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path):
                mc_candidate = os.path.join(item_path, ".minecraft")
                checked_paths.append(mc_candidate)
    except OSError:
        pass  # 无权限访问等错误，静默跳过

    # 2. 优先级 2: 用户家目录下的标准路径
    if system == "Windows":
        # Windows 标准路径
        appdata_roaming = os.getenv('APPDATA')
        if appdata_roaming:
            checked_paths.append(os.path.join(appdata_roaming, ".minecraft"))
        # 也检查一些旧版本或某些环境可能存在的路径
        checked_paths.append(os.path.join(home_dir, ".minecraft"))
        checked_paths.append(os.path.join(home_dir, "AppData", "Roaming", ".minecraft")) # 再次确认
    elif system == "Darwin":  # macOS
        checked_paths.append(os.path.join(home_dir, "Library", "Application Support", "minecraft"))
    elif system == "Linux":
        checked_paths.append(os.path.join(home_dir, ".minecraft"))

    # 3. 优先级 3: 其他常见或第三方启动器可能使用的路径
    if system == "Windows":
        # 检查其他盘符的常见游戏安装目录
        for drive in ["D:", "E:", "F:"]:  # 可以根据需要添加更多盘符
            checked_paths.append(os.path.join(drive, "Games", "Minecraft", ".minecraft"))
            checked_paths.append(os.path.join(drive, "Minecraft", ".minecraft"))
            checked_paths.append(os.path.join(drive, "Program Files", "Minecraft", ".minecraft"))
            checked_paths.append(os.path.join(drive, "Program Files (x86)", "Minecraft", ".minecraft"))
    elif system == "Darwin":
        # macOS 下其他可能的位置
        checked_paths.append(os.path.join(home_dir, "Games", "minecraft"))
    elif system == "Linux":
        # Linux 下其他可能的位置，如 Snap 或 Flatpak 安装
        checked_paths.append(os.path.join(home_dir, "Games", "minecraft"))
        checked_paths.append(os.path.join(home_dir, "snap", "minecraft-launcher", "common", ".minecraft")) # Snap package
        checked_paths.append(os.path.join(home_dir, ".var", "app", "com.mojang.Minecraft", ".minecraft")) # Flatpak potential location

    # 4. 遍历所有候选路径，收集所有真实存在的目录（不重复）
    seen_paths = set()  # 用于去重
    for path in checked_paths:
        abs_path = os.path.abspath(path)  # 获取绝对路径以规范化比较
        if abs_path not in seen_paths and os.path.isdir(abs_path):
            seen_paths.add(abs_path)
            found_dirs.append(abs_path)

    # 5. (可选) 低优先级: 如果以上均未找到，可以尝试系统搜索（性能较低，通常不需要）
    # 因为返回的是列表，即使系统搜索找到，也会加在最后（优先级最低）
    # 如果需要，可以取消注释以下代码，但请注意性能影响
    """
    if not found_dirs:
        sys_search_dir = _search_minecraft_directory_fallback(system)
        if sys_search_dir and sys_search_dir not in seen_paths:
            found_dirs.append(sys_search_dir)
    """

    return found_dirs  # 返回按检查顺序（优先级）排列的列表


# 备用搜索函数（如果需要）
def _search_minecraft_directory_fallback(system):
    """
    备用方案：在文件系统中搜索 .minecraft 目录（较慢）。
    参数 system: 操作系统类型
    返回: 找到的路径 (字符串) 或 None
    """
    home = os.path.expanduser("~")
    search_paths = []
    if system == "Windows":
        search_paths.append(home)
        drives = ["C:\\"]  # 主要搜索C盘用户目录
        for drive in drives:
            if os.path.exists(drive):
                search_paths.append(drive)
    elif system in ["Darwin", "Linux"]:
        search_paths.append(home)

    for start_path in search_paths:
        for root, dirs, files in os.walk(start_path):
            if ".minecraft" in dirs:
                found_path = os.path.join(root, ".minecraft")
                if os.path.isdir(found_path):
                    return os.path.abspath(found_path)
    return None


# --- 使用示例 ---
if __name__ == "__main__":
    minecraft_dirs = find_minecraft_dirs()

    if minecraft_dirs:
        print("找到以下 Minecraft 目录（按优先级排序）:")
        for i, dir_path in enumerate(minecraft_dirs, 1):
            print(f"{i}. {dir_path}")
            
        # 你的启动器逻辑可以选择第一个（优先级最高）的目录
        primary_dir = minecraft_dirs[0]
        print(f"\n自动选择最高优先级目录: {primary_dir}")
        # ... 接下来可以使用 primary_dir 来定位 versions, mods 等
    else:
        print("未找到任何 Minecraft 目录。请手动指定。")
        # 这里可以触发一个 GUI 对话框或命令行输入让用户手动选择
