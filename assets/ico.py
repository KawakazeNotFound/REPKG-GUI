from PIL import Image
import os

base = os.path.dirname(__file__)  # 脚本所在目录
png_file = os.path.join(base, "icon.png")  # 指向 assets/icon.png
ico_file = os.path.join(base, "app.ico")   # 输出 app.ico

sizes = [16, 32, 48, 64, 128, 256]

img = Image.open(png_file).convert("RGBA")
img.save(ico_file, format="ICO", sizes=[(s, s) for s in sizes])

print(f"已生成标准 ICO 文件: {ico_file}")
