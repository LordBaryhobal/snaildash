from PIL import Image
import numpy as np
import os

path = os.path.join("images",input("folder: "))
if not os.path.isdir(path):
    print("unknowned folder")
    exit()
listfile = os.listdir(path)
x, y, w, h = 286, 126, 188, 241
#x, y, w, h = 260, 153, 241, 241
cropcoo = (x, y, x+w, y+h)
os.makedirs(path+"_cropped", exist_ok=True)
for i, p in enumerate(listfile):
    img = Image.open(os.path.join(path, p))
    img = img.crop(cropcoo)
    img.save(os.path.join(path+"_cropped",f"image{i}.png"))
    
    