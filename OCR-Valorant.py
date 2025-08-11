import re
import pyperclip
import pytesseract
import tkinter as tk
from PIL import Image, ImageTk, ImageGrab

def extract_code_from_image(img):
    text = pytesseract.image_to_string(img)
    match = re.search(r"\b[A-Z]{3}\d{3}\b", text)
    return text, (match.group(0) if match else None)

class ScreenSelectGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.config(cursor="crosshair")
        self.screen_img = ImageGrab.grab()
        self.tkimg = ImageTk.PhotoImage(self.screen_img)
        self.canvas = tk.Canvas(self.root, width=self.screen_img.width, height=self.screen_img.height)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tkimg)
        self.rect = None
        self.start_x = self.start_y = 0
        self.crop_area = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.mainloop()

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        self.crop_area = (min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
        self.root.destroy()

def main():
    gui = ScreenSelectGUI()
    if gui.crop_area:
        img = gui.screen_img.crop(gui.crop_area)
        text, code = extract_code_from_image(img)
        print("OCR识别全文本：")
        print(text.strip())
        if code:
            print(f"匹配到代码: {code}")
            pyperclip.copy(code)
            print(f"已复制到剪贴板: {code}")
        else:
            print("未匹配到符合格式的代码")
        print(f"截取的像素范围: {gui.crop_area}")
    else:
        print("未选取区域")

if __name__ == "__main__":
    main()
