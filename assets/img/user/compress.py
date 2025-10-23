# 将图像压缩以适合网络传输
import os
from PIL import Image
from PIL.ExifTags import TAGS

SIZE = (512, 512)
QUALITY = 50

# 自定义标记的键名（建议使用私有EXIF范围，如0xE000-0xEFFF）
CUSTOM_TAG = "CompressionFlag"
CUSTOM_TAG_ID = 0xE001  # 选择一个未公开使用的EXIF ID

os.chdir(os.path.dirname(__file__))

def is_compressed(img):
    """检查图片是否已被标记为压缩过"""
    try:
        exif = img.getexif()
        if exif is None:
            return False
        # 查找自定义标记
        return exif.get(CUSTOM_TAG_ID) == "Compressed"
    except Exception:
        return False

def compress_image(image_path):
    """压缩图片并写入标记"""
    img = Image.open(image_path)
    if is_compressed(img):
        print(f"跳过已压缩图片: {image_path}")
        return
    output_path = f"{image_path[:-4]}_compressed.jpg"  # 输出路径（jpg格式）
    if os.path.exists(output_path):
        print(f"跳过已存在压缩文件的原文件: {output_path}")
        return
    print(f"开始压缩图片: {image_path}")
    # 写入自定义标记
    exif = img.getexif()
    exif[CUSTOM_TAG_ID] = "Compressed"  # 写入标记
    # 调整尺寸
    img.thumbnail(SIZE)
    img.save(output_path, exif=exif, quality=QUALITY, optimize=True)
    print(f"压缩完成并标记: {output_path}")


# 压缩图片目录下的所有图片
def compress_images_in_dir(dir_path):
    for img_name in os.listdir(dir_path):
        if not img_name.endswith(".jpg"):
            continue
        img_path = os.path.join(dir_path, img_name)
        if os.path.isfile(img_path):
            compress_image(img_path)

# 压缩图片目录下的所有图片
def compress_images_in_dirs(dirs_path):
    for dir_path in dirs_path:
        compress_images_in_dir(dir_path)

if __name__ == '__main__':
    # 压缩图片目录下的所有图片
    compress_images_in_dirs(["."])