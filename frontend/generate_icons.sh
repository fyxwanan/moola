#!/bin/bash
set -e

# Navigate to the script's directory
cd "$(dirname "$0")"

# 1. Generate icon.png (512x512) from public/favicon.svg
echo "Generating 512x512 icon.png from public/favicon.svg..."
sips -s format png -z 512 512 public/favicon.svg --out public/icon.png

# 2. Generate icon.icns (macOS)
echo "Generating macOS icon.icns..."
mkdir -p public/icon.iconset
sips -z 16 16     public/icon.png --out public/icon.iconset/icon_16x16.png
sips -z 32 32     public/icon.png --out public/icon.iconset/icon_16x16@2x.png
sips -z 32 32     public/icon.png --out public/icon.iconset/icon_32x32.png
sips -z 64 64     public/icon.png --out public/icon.iconset/icon_32x32@2x.png
sips -z 128 128   public/icon.png --out public/icon.iconset/icon_128x128.png
sips -z 256 256   public/icon.png --out public/icon.iconset/icon_128x128@2x.png
sips -z 256 256   public/icon.png --out public/icon.iconset/icon_256x256.png
sips -z 512 512   public/icon.png --out public/icon.iconset/icon_256x256@2x.png
sips -z 512 512   public/icon.png --out public/icon.iconset/icon_512x512.png
sips -z 1024 1024 public/icon.png --out public/icon.iconset/icon_512x512@2x.png
iconutil -c icns public/icon.iconset
rm -rf public/icon.iconset

# 3. Generate icon.ico (Windows) using Python and Pillow
echo "Generating Windows icon.ico..."
python3 -c "
from PIL import Image
img = Image.open('public/icon.png')
img.save('public/icon.ico', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
"

echo "All icons generated successfully in public/ directory!"
