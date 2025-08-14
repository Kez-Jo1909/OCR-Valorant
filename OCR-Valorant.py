import re
import pyperclip
import pytesseract
import tkinter as tk
from PIL import Image, ImageTk, ImageGrab
import threading
import time


def extract_code_from_image(img):
    text = pytesseract.image_to_string(img)

    # 改进的匹配规则：前三字符可以是字母或数字0，后三字符必须是数字
    matches = re.findall(r"\b([A-Z0-9]{3})(\d{3})\b", text)

    for match in matches:
        prefix, suffix = match
        # 将前缀中的0替换为O
        corrected_prefix = prefix.replace('0', 'O')
        full_code = corrected_prefix + suffix

        # 验证修正后的代码格式：前三字母后三数字
        if re.match(r"^[A-Z]{3}\d{3}$", full_code):
            return text, full_code

    # 如果没有找到符合格式的代码，尝试原始匹配方式
    match = re.search(r"\b[A-Z]{3}\d{3}\b", text)
    return text, (match.group(0) if match else None)


class CodeMonitorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("代码监控工具")

        # 主窗口组件
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10)

        # ROI显示区域
        self.roi_label = tk.Label(self.main_frame)
        self.roi_label.pack()

        # 信息显示区域
        self.info_var = tk.StringVar()
        self.info_var.set("请先选择监控区域")
        self.info_label = tk.Label(self.main_frame, textvariable=self.info_var, font=('Arial', 12))
        self.info_label.pack(pady=10)

        # 控制按钮
        self.btn_frame = tk.Frame(self.main_frame)
        self.btn_frame.pack(pady=10)

        self.select_btn = tk.Button(self.btn_frame, text="选择区域", command=self.start_selection)
        self.select_btn.pack(side=tk.LEFT, padx=5)

        self.monitor_btn = tk.Button(self.btn_frame, text="开始监控", command=self.start_monitoring, state=tk.DISABLED)
        self.monitor_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(self.btn_frame, text="停止", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 监控状态变量
        self.monitoring = False
        self.crop_area = None
        self.last_code = None

    def start_selection(self):
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.config(cursor="crosshair")

        # 获取屏幕截图
        self.screen_img = ImageGrab.grab()
        self.tkimg = ImageTk.PhotoImage(self.screen_img)

        self.canvas = tk.Canvas(self.selection_window, width=self.screen_img.width, height=self.screen_img.height)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tkimg)

        self.rect = None
        self.start_x = self.start_y = 0
        self.crop_area = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red",
                                                 width=2)

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        self.crop_area = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

        # 显示选中的ROI
        roi_img = self.screen_img.crop(self.crop_area)
        roi_img.thumbnail((300, 300))  # 缩放到合适大小显示
        self.roi_img = ImageTk.PhotoImage(roi_img)
        self.roi_label.config(image=self.roi_img)

        self.info_var.set(f"已选择区域: {self.crop_area}\n点击'开始监控'按钮开始识别")
        self.monitor_btn.config(state=tk.NORMAL)
        self.selection_window.destroy()

    def start_monitoring(self):
        if not self.crop_area:
            self.info_var.set("请先选择监控区域")
            return

        self.monitoring = True
        self.select_btn.config(state=tk.DISABLED)
        self.monitor_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_area, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        self.select_btn.config(state=tk.NORMAL)
        self.monitor_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.info_var.set("监控已停止\n最后识别到的代码: " + (self.last_code if self.last_code else "无"))

    def monitor_area(self):
        while self.monitoring:
            try:
                # 捕获ROI区域
                img = ImageGrab.grab(bbox=self.crop_area)

                # 更新ROI显示
                display_img = img.copy()
                display_img.thumbnail((300, 300))
                self.display_img = ImageTk.PhotoImage(display_img)
                self.roi_label.config(image=self.display_img)

                # 识别文本
                text, code = extract_code_from_image(img)

                if code:
                    self.last_code = code
                    pyperclip.copy(code)
                    self.info_var.set(f"识别到代码: {code}\n已自动复制到剪贴板")

                    # 显示识别到的代码3秒后继续监控
                    time.sleep(3)
                else:
                    self.info_var.set(
                        f"监控中...\n最后识别: {self.last_code if self.last_code else '无'}\n当前内容: {text.strip()[:50]}...")

                # 控制监控频率
                time.sleep(1)

            except Exception as e:
                self.info_var.set(f"监控出错: {str(e)}")
                time.sleep(5)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = CodeMonitorApp()
    app.run()
