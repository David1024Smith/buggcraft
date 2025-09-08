import requests
from PIL import Image
import os
import tempfile

def download_skin(url):
    """从URL下载Minecraft皮肤图片"""
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"无法下载皮肤，HTTP状态码: {response.status_code}")
    return response.content

def extract_minecraft_head(skin_data, output_path=None, scale_factor=8):
    """
    从Minecraft皮肤数据中提取头部头像
    
    Args:
        skin_data (bytes): 皮肤图片的二进制数据
        output_path (str, optional): 输出头像的路径
        scale_factor (int): 放大倍数
        
    Returns:
        PIL.Image.Image: 提取并放大后的头像图像
    """
    # 创建临时文件保存皮肤
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_file.write(skin_data)
        temp_path = temp_file.name
    
    try:
        # 打开皮肤图像
        skin_image = Image.open(temp_path)
        width, height = skin_image.size
        
        # 定义标准皮肤尺寸和对应的头部坐标比例
        standard_sizes = {
            (64, 32): (8/64, 8/32, 16/64, 16/32),    # 旧版皮肤 64x32
            (64, 64): (8/64, 8/64, 16/64, 16/64),    # 标准皮肤 64x64
            (128, 128): (16/128, 16/128, 32/128, 32/128), # 高清皮肤 128x128
            (256, 256): (32/256, 32/256, 64/256, 64/256), # 超清皮肤 256x256
        }
        
        # 检查是否是标准尺寸
        if (width, height) in standard_sizes:
            ratios = standard_sizes[(width, height)]
            head_coords = (
                ratios[0] * width,
                ratios[1] * height,
                ratios[2] * width,
                ratios[3] * height
            )
        else:
            # 对于非标准尺寸，使用比例计算头部位置
            ratio_x = width / 64
            ratio_y = height / 64
            head_coords = (8 * ratio_x, 8 * ratio_y, 16 * ratio_x, 16 * ratio_y)
        
        # 将坐标转换为整数
        head_coords = tuple(int(coord) for coord in head_coords)
        
        # 裁剪出头部区域
        head_front = skin_image.crop(head_coords)
        
        # 使用最近邻插值法放大图像，保持像素风格和清晰度
        original_size = head_front.size
        new_size = (original_size[0] * scale_factor, original_size[1] * scale_factor)
        head_upscaled = head_front.resize(new_size, Image.Resampling.NEAREST)
        
        # 设置默认输出路径
        if output_path is None:
            output_path = "minecraft_head.png"
        
        # 保存图像
        head_upscaled.save(output_path, format='PNG', optimize=True)
        
        print(f"皮肤尺寸: {width}x{height}")
        print(f"头部区域坐标: {head_coords}")
        print(f"头像已保存至: {output_path}")
        
        return output_path
    
    finally:
        # 删除临时文件
        os.unlink(temp_path)

def process_skin_info(uuid, skin_info, output_path=None, scale_factor=8):
    """
    处理皮肤信息字典，下载皮肤并提取头像
    
    Args:
        uuid (str): 用户名uuid
        skin_info (dict): 包含皮肤信息的字典
        output_path (str, optional): 输出头像的路径
        scale_factor (int): 放大倍数
        
    Returns:
        PIL.Image.Image: 提取并放大后的头像图像
    """
    # 从字典中提取URL
    skin_url = skin_info.get('url')
    if not skin_url:
        raise ValueError("皮肤信息字典中缺少'url'字段")
    
    # 下载皮肤
    print(f"正在下载皮肤: {skin_url}")
    skin_data = download_skin(skin_url)
    
    # 提取头像、
    return extract_minecraft_head(skin_data, os.path.join(output_path, "user", f"{uuid}.png"), scale_factor)

# 示例皮肤信息
skin_info = {
    'id': '3e0f41c9-e7df-4df1-95cf-60eab1a38443',
    'state': 'ACTIVE',
    'url': 'http://textures.minecraft.net/texture/7b738ad7ffa7132876f266c4c6e48ee4009f6c8fc4073d2b8c9e54e9e7562fe',
    'textureKey': '7b738ad7ffa7132876f266c4c6e48ee4009f6c8fc4073d2b8c9e54e9e7562fe',
    'variant': 'CLASSIC'
}

# 处理皮肤信息并获取头像
if __name__ == "__main__":
    try:
        # 处理皮肤信息并保存头像
        head_image = process_skin_info(skin_info, output_path="custom_head.png", scale_factor=8)
        
        # 显示头像
        head_image.show()
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")