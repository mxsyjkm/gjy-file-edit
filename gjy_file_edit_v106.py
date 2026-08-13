# gjy编辑器1.0.6.py
# GJY编辑器 v1.0.6
# 说明：修复 image 文件解析、A4 图片等比例缩放手柄、重新编辑大小还原等问题

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import base64
import os
from datetime import datetime
import json
from PIL import Image, ImageTk
import io

class GJYEditorMobile:
    def __init__(self, root):
        self.root = root
        self.root.title("GJY编辑器 v1.0.6")
        self.root.geometry("450x750")
        self.root.resizable(False, False)

        self.version = "v1.0.6"
        self.config_file = "gjy_config.json"

        # 默认存储路径
        self.default_storage = os.path.join(os.path.expanduser("~"), "GJY_Files")
        if not os.path.exists(self.default_storage):
            os.makedirs(self.default_storage)

        # 加载配置
        self.current_folder = self.load_config()
        self.current_file = None
        self.current_file_type = None
        self.selected_image_path = None
        self.preview_image = None

        # A4编辑相关
        self.a4_elements = []
        self.selected_element = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        # resize_data 用于缩放手柄拖拽
        self.resize_data = {"active": False, "element": None, "start_x": 0, "start_y": 0, "start_w": 0, "start_h": 0}

        self.setup_ui()

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    folder = config.get('save_directory', self.default_storage)
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                    return folder
        except:
            pass
        return self.default_storage

    def save_config(self):
        try:
            config = {'save_directory': self.current_folder, 'version': self.version}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="GJY编辑器 v1.0.6", font=("Arial", 16, "bold"))
        title_label.pack(pady=8)

        folder_frame = ttk.LabelFrame(main_frame, text="存储位置", padding="8")
        folder_frame.pack(fill=tk.X, pady=6)

        display_path = self.current_folder
        if len(display_path) > 30:
            display_path = "..." + display_path[-27:]

        self.folder_var = tk.StringVar(value=display_path)
        folder_label = ttk.Label(folder_frame, textvariable=self.folder_var, font=("Arial", 9), wraplength=400)
        folder_label.pack(fill=tk.X)

        btn_frame = ttk.Frame(folder_frame)
        btn_frame.pack(fill=tk.X, pady=4)

        ttk.Button(btn_frame, text="更改位置", command=self.select_folder).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="设为默认", command=self.set_as_default).pack(side=tk.LEFT, padx=(8,0))

        list_frame = ttk.LabelFrame(main_frame, text="GJY文件", padding="8")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=6)

        list_controls = ttk.Frame(list_frame)
        list_controls.pack(fill=tk.X, pady=4)

        ttk.Button(list_controls, text="刷新", command=self.refresh_file_list).pack(side=tk.LEFT)
        ttk.Button(list_controls, text="打开文件夹", command=self.open_folder).pack(side=tk.LEFT, padx=(8,0))

        self.file_listbox = tk.Listbox(list_frame, height=4, font=("Arial", 10))
        self.file_listbox.pack(fill=tk.BOTH, expand=True)

        file_ops_frame = ttk.Frame(list_frame)
        file_ops_frame.pack(fill=tk.X, pady=4)

        ttk.Button(file_ops_frame, text="查看", command=self.view_selected_file).pack(side=tk.LEFT)
        ttk.Button(file_ops_frame, text="编辑", command=self.edit_selected_file).pack(side=tk.LEFT, padx=(8,0))
        ttk.Button(file_ops_frame, text="删除", command=self.delete_selected_file).pack(side=tk.LEFT, padx=(8,0))

        create_frame = ttk.LabelFrame(main_frame, text="创建GJY文件", padding="8")
        create_frame.pack(fill=tk.BOTH, expand=True, pady=6)

        type_frame = ttk.Frame(create_frame)
        type_frame.pack(fill=tk.X, pady=4)

        ttk.Label(type_frame, text="文件类型:").pack(side=tk.LEFT)
        self.file_type = tk.StringVar(value="text")
        ttk.Radiobutton(type_frame, text="文本", variable=self.file_type, value="text", command=self.on_type_change).pack(side=tk.LEFT, padx=(10,0))
        ttk.Radiobutton(type_frame, text="图片", variable=self.file_type, value="image", command=self.on_type_change).pack(side=tk.LEFT, padx=(10,0))
        ttk.Radiobutton(type_frame, text="A4混合", variable=self.file_type, value="a4", command=self.on_type_change).pack(side=tk.LEFT, padx=(10,0))

        self.current_file_var = tk.StringVar(value="未选择文件")
        ttk.Label(create_frame, textvariable=self.current_file_var, font=("Arial", 9, "bold"), foreground="blue").pack(anchor=tk.W, pady=(5,0))

        ttk.Label(create_frame, text="文件名:").pack(anchor=tk.W)
        self.filename_var = tk.StringVar()
        filename_entry = ttk.Entry(create_frame, textvariable=self.filename_var, font=("Arial", 10))
        filename_entry.pack(fill=tk.X, pady=(2, 6))

        # 文本区域
        self.text_frame = ttk.Frame(create_frame)
        ttk.Label(self.text_frame, text="文本内容:").pack(anchor=tk.W)
        self.content_text = scrolledtext.ScrolledText(self.text_frame, height=3, wrap=tk.WORD, font=("Arial", 10))
        self.content_text.pack(fill=tk.BOTH, expand=True)

        # 图片区域（单图）
        self.image_frame = ttk.Frame(create_frame)
        ttk.Label(self.image_frame, text="选择图片:").pack(anchor=tk.W)
        image_btn_frame = ttk.Frame(self.image_frame)
        image_btn_frame.pack(fill=tk.X, pady=2)
        self.image_path_var = tk.StringVar(value="未选择图片")
        ttk.Label(image_btn_frame, textvariable=self.image_path_var, font=("Arial", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(image_btn_frame, text="选择图片", command=self.select_image).pack(side=tk.RIGHT)

        self.preview_frame = ttk.LabelFrame(self.image_frame, text="图片预览", padding="5")
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.preview_label = ttk.Label(self.preview_frame, text="暂无预览", font=("Arial", 10), justify=tk.CENTER)
        self.preview_label.pack(expand=True, fill=tk.BOTH)

        # A4编辑器
        self.a4_frame = ttk.Frame(create_frame)
        a4_controls = ttk.Frame(self.a4_frame)
        a4_controls.pack(fill=tk.X, pady=4)
        ttk.Button(a4_controls, text="添加文本", command=self.add_text_element).pack(side=tk.LEFT)
        ttk.Button(a4_controls, text="添加图片", command=self.add_image_element).pack(side=tk.LEFT, padx=(8,0))
        ttk.Button(a4_controls, text="删除选中", command=self.delete_selected_element).pack(side=tk.LEFT, padx=(8,0))

        self.a4_preview_frame = ttk.LabelFrame(self.a4_frame, text="A4页面预览", padding="5")
        self.a4_preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 画布使用固定比例显示 A4（内边距）
        self.a4_canvas = tk.Canvas(self.a4_preview_frame, bg="white", width=350, height=500)
        self.a4_canvas.pack(expand=True, fill=tk.BOTH, pady=5)
        self.a4_canvas.create_rectangle(10, 10, 340, 490, outline="black", width=1)

        # 绑定事件：点击用于选择，拖拽用于移动或缩放
        self.a4_canvas.bind("<Button-1>", self.on_canvas_click)
        self.a4_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.a4_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        action_btn_frame = ttk.Frame(create_frame)
        action_btn_frame.pack(fill=tk.X, pady=4)

        ttk.Button(action_btn_frame, text="新建文件", command=self.create_gjy_file).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(action_btn_frame, text="保存修改", command=self.save_gjy_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8,0))

        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, font=("Arial", 9))
        status_bar.pack(fill=tk.X, pady=(8, 0))

        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        self.file_listbox.bind('<Double-Button-1>', lambda e: self.view_selected_file())

        self.on_type_change()
        self.refresh_file_list()

    def on_type_change(self):
        file_type = self.file_type.get()
        if file_type == "text":
            self.text_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 6))
            self.image_frame.pack_forget()
            self.a4_frame.pack_forget()
        elif file_type == "image":
            self.text_frame.pack_forget()
            self.image_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 6))
            self.a4_frame.pack_forget()
        else:
            self.text_frame.pack_forget()
            self.image_frame.pack_forget()
            self.a4_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 6))

    def select_image(self):
        filetypes = [('图片文件', '*.jpg *.jpeg *.png *.gif *.bmp *webp'), ('所有文件', '*.*')]
        filepath = filedialog.askopenfilename(title="选择图片", filetypes=filetypes)
        if filepath:
            self.selected_image_path = filepath
            display_path = filepath
            if len(display_path) > 30:
                display_path = "..." + display_path[-27:]
            self.image_path_var.set(display_path)
            self.show_image_preview(filepath)
            self.update_status(f"已选择图片: {os.path.basename(filepath)}")

    def show_image_preview(self, image_path):
        try:
            image = Image.open(image_path)
            max_w, max_h = 300, 200
            w, h = image.size
            if w > max_w or h > max_h:
                ratio = min(max_w/w, max_h/h)
                image = image.resize((int(w*ratio), int(h*ratio)), Image.Resampling.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=self.preview_image, text="")
        except Exception as e:
            self.preview_label.configure(image="", text=f"预览失败: {str(e)}")
            self.update_status(f"图片预览失败: {e}")

    def add_text_element(self):
        text = simpledialog.askstring("添加文本", "请输入文本内容:")
        if text:
            element = {"type": "text", "content": text, "x": 50, "y": 50, "id": None}
            element_id = self.a4_canvas.create_text(50, 50, text=text, fill="black", font=("Arial", 12), tags=("draggable", "element"))
            element["id"] = element_id
           
            self.a4_elements.append(element)
            self.update_status(f"已添加文本元素: {text}")

    def add_image_element(self):
        filetypes = [('图片文件', '*.jpg *.jpeg *.png *.gif *.bmp *webp'), ('所有文件', '*.*')]
        filepath = filedialog.askopenfilename(title="选择图片", filetypes=filetypes)
        if not filepath:
            return
        try:
            image = Image.open(filepath)
            # 初始显示尺寸限制
            max_size = 150
            w, h = image.size
            if w > max_size or h > max_size:
                ratio = min(max_size/w, max_size/h)
                new_w = int(w*ratio)
                new_h = int(h*ratio)
                image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            else:
                new_w, new_h = w, h

            photo = ImageTk.PhotoImage(image)
            element = {
                "type": "image",
                "content": filepath,
                "x": 100,
                "y": 100,
                "id": None,
                "photo": photo,
                "width": new_w,
                "height": new_h
            }
            element_id = self.a4_canvas.create_image(100, 100, image=photo, tags=("draggable", "element"))
            element["id"] = element_id
            self.a4_elements.append(element)
            self.update_status(f"已添加图片元素: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("错误", f"添加图片失败: {e}")

    def delete_selected_element(self):
        if self.selected_element:
            # 删除选择框/手柄
            if self.selected_element["type"] == "image":
                if "selection_box" in self.selected_element:
                    try:
                        self.a4_canvas.delete(self.selected_element["selection_box"])
                    except: pass
                if "handle" in self.selected_element:
                    try:
                        self.a4_canvas.delete(self.selected_element["handle"])
                    except: pass
            else:
                # 文本不需要特殊处理
                pass

            self.a4_canvas.delete(self.selected_element["id"])
            self.a4_elements = [e for e in self.a4_elements if e["id"] != self.selected_element["id"]]
            self.selected_element = None
            self.update_status("已删除选中元素")
        else:
            messagebox.showwarning("提示", "请先选择一个元素")

    def on_canvas_click(self, event):
        # 优先检查是否点击到缩放手柄
        clicked_items = self.a4_canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
        for item in clicked_items:
            tags = self.a4_canvas.gettags(item)
            if "resize_handle" in tags:
                # 找到哪个元素包含此 handle
                for element in self.a4_elements:
                    if element.get("handle") == item:
                        self.selected_element = element
                        # 初始化 resize_data
                        self.resize_data["active"] = True
                        self.resize_data["element"] = element
                        self.resize_data["start_x"] = event.x
                        self.resize_data["start_y"] = event.y
                        self.resize_data["start_w"] = element["width"]
                        self.resize_data["start_h"] = element["height"]
                        return

        # 否则查找点击的元素（文本或图片）
        clicked_items = self.a4_canvas.find_overlapping(event.x-5, event.y-5, event.x+5, event.y+5)
        for item in clicked_items:
            tags = self.a4_canvas.gettags(item)
            if "element" in tags:
                for element in self.a4_elements:
                    if element["id"] == item:
                        # 选择该元素
                        self.select_element(element)
                        # 准备拖动
                        self.drag_data["x"] = event.x
                        self.drag_data["y"] = event.y
                        self.drag_data["item"] = item
                        return

        # 没选中任何元素时取消选择
        self.deselect_all()

    def select_element(self, element):
        # 取消上一个选择
        self.deselect_all()
        self.selected_element = element
        if element["type"] == "text":
            self.a4_canvas.itemconfig(element["id"], fill="red")
        else:
            # 为图片创建红色选择框和缩放手柄（右下）
            w = element.get("width", 100)
            h = element.get("height", 100)
            x = element["x"]
            y = element["y"]
            # 删除可能存在的旧框/手柄
            if "selection_box" in element:
                try:
                    self.a4_canvas.delete(element["selection_box"])
                except: pass
            if "handle" in element:
                try:
                    self.a4_canvas.delete(element["handle"])
                except: pass

            sel_box = self.a4_canvas.create_rectangle(
                x - w//2 - 2, y - h//2 - 2,
                x + w//2 + 2, y + h//2 + 2,
                outline="red", width=2
            )
            element["selection_box"] = sel_box

            # 缩放手柄：放在右下角
            size = 6
            hx = x + w//2
            hy = y + h//2
            handle = self.a4_canvas.create_rectangle(hx-size, hy-size, hx+size, hy+size, fill="blue", tags=("resize_handle",))
            element["handle"] = handle

    def deselect_all(self):
        if self.selected_element:
            if self.selected_element["type"] == "text":
                try:
                    self.a4_canvas.itemconfig(self.selected_element["id"], fill="black")
                except: pass
            else:
                if "selection_box" in self.selected_element:
                    try:
                        self.a4_canvas.delete(self.selected_element["selection_box"])
                    except: pass
                if "handle" in self.selected_element:
                    try:
                       self.a4_canvas.delete(self.selected_element["handle"])
                    except: pass
        self.selected_element = None
        # 清 resize_data
        self.resize_data = {"active": False, "element": None, "start_x": 0, "start_y": 0, "start_w": 0, "start_h": 0}

    def on_canvas_drag(self, event):
        # 如果正在缩放
        if self.resize_data.get("active"):
            self.on_handle_drag(event)
            return

        if self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            self.a4_canvas.move(self.drag_data["item"], dx, dy)
            # 更新元素位置
            for element in self.a4_elements:
                if element["id"] == self.drag_data["item"]:
                    element["x"] += dx
                    element["y"] += dy
                    # 更新选择框和手柄位置（如果存在）
                    if "selection_box" in element:
                        self.a4_canvas.coords(
                            element["selection_box"],
                            element["x"] - element["width"]//2 - 2,
                            element["y"] - element["height"]//2 - 2,
                            element["x"] + element["width"]//2 + 2,
                            element["y"] + element["height"]//2 + 2
                        )
                    if "handle" in element:
                        size = 6
                        hx = element["x"] + element["width"]//2
                        hy = element["y"] + element["height"]//2
                        self.a4_canvas.coords(element["handle"], hx-size, hy-size, hx+size, hy+size)
                    break
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_handle_drag(self, event):
        # 缩放保持等比例，使用起始宽度作为基准
        rd = self.resize_data
        element = rd.get("element")
        if not element:
            return
        dx = event.x - rd["start_x"]
        dy = event.y - rd["start_y"]
        # 使用 dx 和 dy 的最大值进行等比例缩放（向右下为增，向左上为减）
        delta = max(dx, dy)
        new_w = max(20, int(rd["start_w"] + delta*1))  # delta 缩放系数 1:1
        scale = new_w / rd["start_w"] if rd["start_w"] > 0 else 1.0
        new_h = max(20, int(rd["start_h"] * scale))

        try:
            # 读取原始图片并按新尺寸生成 PhotoImage
            # 如果 element['content'] 是路径，优先读取路径文件（更高质量）；否则如果没有路径则尝试把存在的 photo 重新缩放（但通常保留路径）
            if os.path.exists(element.get("content", "")):
                img = Image.open(element["content"]).resize((new_w, new_h), Image.Resampling.LANCZOS)
            else:
                # 如果没有原路径，尝试从 element['photo'] 的图片来源再构造（退级方案）
                # 这里通常不会触发，因为保存时我们都会存 original_path
                img = Image.new("RGBA", (new_w, new_h), (255,255,255,0))
            photo = ImageTk.PhotoImage(img)
            element["photo"] = photo
            element["width"] = new_w
            element["height"] = new_h
            # 更新画布图片
            self.a4_canvas.itemconfig(element["id"], image=photo)
            # 更新选择框和手柄
            if "selection_box" in element:
                self.a4_canvas.coords(
                    element["selection_box"],
                    element["x"] - new_w//2 - 2,
                    element["y"] - new_h//2 - 2,
                    element["x"] + new_w//2 + 2,
                    element["y"] + new_h//2 + 2
                )
            if "handle" in element:
                size = 6
                hx = element["x"] + new_w//2
                hy = element["y"] + new_h//2
                self.a4_canvas.coords(element["handle"], hx-size, hy-size, hx+size, hy+size)
        except Exception as e:
            self.update_status(f"缩放失败: {e}")

    def on_canvas_release(self, event):
        self.drag_data["item"] = None
        # 结束缩放
        if self.resize_data.get("active"):
            self.resize_data["active"] = False
            self.resize_data["element"] = None

    def view_selected_file(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个文件")
            return
        filename = self.file_listbox.get(selection[0])
        filepath = os.path.join(self.current_folder, filename)
        try:
            file_info = self.parse_gjy_file(filepath)
            self.show_content_window(filename, file_info)
        except Exception as e:
            messagebox.showerror("错误", f"读取失败: {e}")

    def show_content_window(self, filename, file_info):
        win = tk.Toplevel(self.root)
        win.title(f"查看: {filename}")
        win.geometry("500x600")

        info_frame = ttk.LabelFrame(win, text="文件信息", padding="8")
        info_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(info_frame, text=f"文件: {filename}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"类型: {file_info['file_type']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"版本: {file_info['version']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"创建: {file_info['created_time']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"修改: {file_info['modified_time']}").pack(anchor=tk.W)

        content_frame = ttk.LabelFrame(win, text="内容预览", padding="8")                                                 
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        if file_info['file_type'] == 'text':
            text_widget = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, font=("Arial", 10))
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, file_info.get('content', ''))
            text_widget.config(state=tk.DISABLED)

        elif file_info['file_type'] == 'image':
            try:
                # encoded_data 可能是多行，parse 已合并为完整 base64
                image_data = base64.b64decode(file_info.get('encoded_data', ''))
                image = Image.open(io.BytesIO(image_data))
                max_w, max_h = 350, 400
                w, h = image.size
                if w > max_w or h > max_h:
                    ratio = min(max_w/w, max_h/h)
                    image = image.resize((int(w*ratio), int(h*ratio)), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                image_label = ttk.Label(content_frame, image=photo)
                image_label.image = photo
                image_label.pack(expand=True)
                info_text = f"图片原始尺寸: {w} x {h}\n已缩放显示"
                ttk.Label(content_frame, text=info_text, justify=tk.CENTER).pack(pady=5)
            except Exception as e:
                ttk.Label(content_frame, text=f"图片显示失败: {e}", justify=tk.CENTER).pack(expand=True)

        else:  # A4混合
            canvas = tk.Canvas(content_frame, bg="white", width=400, height=400)
            canvas.pack(expand=True, fill=tk.BOTH, pady=5)
            canvas.create_rectangle(20, 20, 380, 380, outline="black", width=1)

            for element_data in file_info.get('a4_elements', []):
                if element_data['type'] == 'text':
                    canvas.create_text(element_data['x'], element_data['y'], text=element_data['content'], fill="black", font=("Arial", 12))
                elif element_data['type'] == 'image':
                    try:
                        image_data = base64.b64decode(element_data['image_data'])
                        image = Image.open(io.BytesIO(image_data))
                        # 使用保存的 width/height 来还原
                        w = int(element_data.get('width', image.size[0]))
                        h = int(element_data.get('height', image.size[1]))
                        if w <= 0 or h <= 0:
                            w, h = image.size
                        image = image.resize((w, h), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        canvas.create_image(element_data['x'], element_data['y'], image=photo)
                        # 保持引用
                        if not hasattr(canvas, 'images'):
                            canvas.images = []
                        canvas.images.append(photo)
                    except Exception as e:
                        canvas.create_text(element_data['x'], element_data['y'], text=f"[图片加载失败: {e}]", fill="red")

            ttk.Label(content_frame, text=f"包含 {len(file_info.get('a4_elements', []))} 个元素", justify=tk.CENTER).pack(pady=5)

        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=8)

    def parse_gjy_file(self, filepath):
        """
        解析 gjy 文件。
        规则：
          - 以 # 开始的是注释/元信息
          - 对于 image 类型，文件中剩余所有非注释行都应当拼接为 base64 数据
          - 对于 a4 类型，#A4_ELEMENTS: 后跟 JSON 字符串（可能包含中文等）
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()

        file_info = {
            'file_type': 'text',
            'version': "未知版本",
            'created_time': "未知时间",
            'modified_time': "无记录",
            'encoded_data': "",
            'content': "",
            'a4_elements': []
        }

        # 先解析头部行，遇到 #A4_ELEMENTS: 时读取 json，其它以 # 开头为元信息
        for i, line in enumerate(lines):
            if not line:
                continue
            if line.startswith("#GJY"):
                continue
            elif line.startswith("#v"):
                file_info['version'] = line[1:].strip()
            elif line.startswith("#Created:"):
                file_info['created_time'] = line[9:].strip()
            elif line.startswith("#Modified:"):
                file_info['modified_time'] = line[10:].strip()
            elif line.startswith("#Type:"):
                file_info['file_type'] = line[6:].strip()
            elif line.startswith("#A4_ELEMENTS:"):
                elements_data = line[13:].strip()
                if elements_data:
                    try:
                       
                      file_info['a4_elements'] = json.loads(elements_data)
                    except Exception:
                        # 如果 #A4_ELEMENTS: 后面的JSON因为换行等问题被拆分，尝试合并后续注释以恢复
                        try:
                            joined = line[13:].strip()
                            j = i + 1
                            while j < len(lines) and not lines[j].startswith("#"):
                                joined += lines[j]
                                j += 1
                            file_info['a4_elements'] = json.loads(joined)
                        except:
                            file_info['a4_elements'] = []
                # A4 数据一般在头部一行给出，解析完退出
                break
            elif line and not line.startswith("#"):
                # 对于非注释行，认为后面都是编码数据（可能多行），合并所有非#行
                # 从当前行开始合并到文件末尾所有不是注释行的行
                encoded = ''.join(l.strip() for l in lines[i:] if not l.startswith('#'))
                file_info['encoded_data'] = encoded
                break

        # 解码文本（如果是 text 类型）
        try:
            if file_info['file_type'] == 'text' and file_info['encoded_data']:
                file_info['content'] = base64.b64decode(file_info['encoded_data']).decode('utf-8')
        except Exception:
            if file_info['file_type'] == 'text':
                file_info['content'] = "[无法解码的文本内容]"

        return file_info

    def set_as_default(self):
        self.save_config()
        messagebox.showinfo("成功", f"已设置为默认存储位置:\n{self.current_folder}")

    def select_folder(self):
        try:
            folder = filedialog.askdirectory(initialdir=self.current_folder)
            if folder:
                self.current_folder = folder
                display_path = folder
                if len(display_path) > 30:
                    display_path = "..." + display_path[-27:]
                self.folder_var.set(display_path)
                self.refresh_file_list()
                self.clear_edit()
                self.update_status(f"已切换到: {os.path.basename(folder)}")
        except Exception as e:
            self.update_status(f"选择文件夹失败: {e}")

    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        try:
            if not os.path.exists(self.current_folder):
                os.makedirs(self.current_folder)
            files = os.listdir(self.current_folder)
            gjy_files = [f for f in files if f.endswith(('.gjy', '.gjyx'))]
            gjy_files.sort()
            for file in gjy_files:
                self.file_listbox.insert(tk.END, file)
            self.update_status(f"找到 {len(gjy_files)} 个文件")
        except Exception as e:
            self.update_status(f"刷新失败: {e}")

    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            filename = self.file_listbox.get(selection[0])
            self.update_status(f"已选择: {filename}")

    def clear_edit(self):
        self.current_file = None
        self.current_file_type = None
        self.current_file_var.set("未选择文件")
        self.filename_var.set("")
        self.content_text.delete("1.0", tk.END)
        self.image_path_var.set("未选择图片")
        self.preview_label.configure(image="", text="暂无预览")
        self.selected_image_path = None

        self.a4_canvas.delete("all")
        self.a4_canvas.create_rectangle(10, 10, 340, 490, outline="black", width=1)
        self.a4_elements = []
        self.selected_element = None

        self.file_type.set("text")
        self.on_type_change()

    def edit_selected_file(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要编辑的文件")
            return
        filename = self.file_listbox.get(selection[0])
        filepath = os.path.join(self.current_folder, filename)
        try:
            file_info = self.parse_gjy_file(filepath)
            self.current_file = filename
            self.current_file_type = file_info['file_type']
            self.current_file_var.set(f"正在编辑: {filename}")
            self.filename_var.set(filename.replace('.gjy', '').replace('.gjyx', ''))

            if file_info['file_type'] == 'text':
                self.file_type.set("text")
                self.content_text.delete("1.0", tk.END)
                self.content_text.insert("1.0", file_info.get('content', ''))
            elif file_info['file_type'] == 'image':
                self.file_type.set("image")
                # 当编辑 image 类型的原始图片不存在时提示需要重新选择
                self.image_path_var.set("[原图片数据 - 预览可查看文件内容，编辑需重新选择图片以替换]")
                self.preview_label.configure(image="", text="编辑时需要重新选择图片")
            else:
                self.file_type.set("a4")
                self.load_a4_elements(file_info.get('a4_elements', []))

            self.on_type_change()
            self.update_status(f"已加载文件: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败: {e}")

    def load_a4_elements(self, elements_data):
        # 清空并重绘边框
        self.a4_canvas.delete("all")
        self.a4_canvas.create_rectangle(10, 10, 340, 490, outline="black", width=1)
        self.a4_elements = []

        for element_data in elements_data:
            if element_data['type'] == 'text':
                element_id = self.a4_canvas.create_text(
                    element_data['x'], element_data['y'],

text=element_data['content'],
                    fill="black",
                    font=("Arial", 12),
                    tags=("draggable", "element")
                )
                element = {
                    "type": "text",
                    "content": element_data['content'],
                    "x": element_data['x'],
                    "y": element_data['y'],
                    "id": element_id
                }
                self.a4_elements.append(element)

            elif element_data['type'] == 'image':
                try:
                    # 解码图片数据并按保存的 width/height 还原
                    image_data = base64.b64decode(element_data['image_data'])
                    image = Image.open(io.BytesIO(image_data))
                    w = int(element_data.get('width', image.size[0]))
                    h = int(element_data.get('height', image.size[1]))
                    if w <= 0 or h <= 0:
                        w, h = image.size
                    image = image.resize((w, h), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    element_id = self.a4_canvas.create_image(element_data['x'], element_data['y'], image=photo, tags=("draggable", "element"))
                    element = {
                        "type": "image",
                        "content": element_data.get('original_path', ''),  # 原始路径（可能为空）
                        "x": element_data['x'],
                        "y": element_data['y'],
                        "id": element_id,
                        "photo": photo,
                        "width": w,
                        "height": h
                    }
                    self.a4_elements.append(element)
                except Exception as e:
                    self.update_status(f"加载图片元素失败: {e}")

    def save_gjy_file(self):
        filename = self.filename_var.get().strip()
        file_type = self.file_type.get()

        if not filename:
            messagebox.showwarning("提示", "请输入文件名")
            return

        if file_type == "text":
            content = self.content_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("提示", "请输入文本内容")
                return
        elif file_type == "image":
            if not self.selected_image_path or self.image_path_var.get() == "未选择图片":
                messagebox.showwarning("提示", "请选择图片文件")
                return
        else:
            if not self.a4_elements:
                messagebox.showwarning("提示", "请至少添加一个元素到A4页面")
                return

        if not filename.endswith('.gjy'):
            filename += '.gjy'
        filepath = os.path.join(self.current_folder, filename)
        is_new_file = self.current_file is None or self.current_file != filename

        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if not is_new_file and os.path.exists(filepath):
                created_time = current_time
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("#Created:"):
                            created_time = line.strip()[9:]
                            break
            else:
                created_time = current_time

            if file_type == "text":
                content = self.content_text.get("1.0", tk.END).strip()
                encoded_data = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            elif file_type == "image":
                with open(self.selected_image_path, 'rb') as img_file:
                    image_data = img_file.read()
                encoded_data = base64.b64encode(image_data).decode('utf-8')
            else:
                a4_elements_data = []
                for element in self.a4_elements:
                    element_data = {'type': element['type'], 'x': element['x'], 'y': element['y']}
                    if element['type'] == 'text':
                        element_data['content'] = element['content']
                    elif element['type'] == 'image':
                        # 读取图片文件内容并编码。如果 element['content'] 是空，则尝试从画布 photo 导出（不理想）
                        try:
                            if element.get('content') and os.path.exists(element['content']):
                                with open(element['content'], 'rb') as img_file:
                                    image_bytes = img_file.read()
                            else:
                                # 退级：尝试从 element['photo'] 获取（PIL 无直接方法），所以这里尽量提醒用户最好保留原文件路径
                                raise FileNotFoundError("原始图片路径不存在，无法直接读取")
                            element_data['image_data'] = base64.b64encode(image_bytes).decode('utf-8')
                            element_data['original_path'] = element.get('content', '')
                            element_data['width'] = int(element.get('width', 100))
                            element_data['height'] = int(element.get('height', 100))
                        except Exception as e:
                            # 如果失败，仍尝试用当前画布图片的现有宽高，但 image_data 为空时加载会失败，用户需注意
                            element_data['image_data'] = ""
                            element_data['original_path'] = element.get('content', '')
                            element_data['width'] = int(element.get('width', 100))
                            element_data['height'] = int(element.get('height', 100))
                    a4_elements_data.append(element_data)
                encoded_data = ""

            # 写文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"#GJY\n")
                f.write(f"#{self.version}\n")
                f.write(f"#Type: {file_type}\n")
                f.write(f"#Created: {created_time}\n")
                f.write(f"#Modified: {current_time}\n")
                if file_type == "a4":
                    f.write(f"#A4_ELEMENTS: {json.dumps(a4_elements_data, ensure_ascii=False)}\n")
                else:
                    f.write(encoded_data)

            self.update_status(f"{'创建' if is_new_file else '修改'}成功: {filename}")
            self.refresh_file_list()
            if is_new_file:
                self.clear_edit()
            else:
                self.current_file_var.set(f"已保存: {filename}")
            messagebox.showinfo("成功", f"文件已{'创建' if is_new_file else '修改'}!\n{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def create_gjy_file(self):
        self.current_file = None
        self.current_file_type = None
        self.current_file_var.set("创建新文件")
        self.save_gjy_file()

    def delete_selected_file(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择文件")
            return
        filename = self.file_listbox.get(selection[0])
        filepath = os.path.join(self.current_folder, filename)
        if messagebox.askyesno("确认", f"删除 {filename}?"):
            try:
                os.remove(filepath)
                self.refresh_file_list()
                if self.current_file == filename:
                    self.clear_edit()
                self.update_status(f"已删除: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}")

    def open_folder(self):
        try:
            messagebox.showinfo("存储位置", f"文件保存在:\n{self.current_folder}")
        except Exception as e:
            self.update_status(f"打开失败: {e}")

    def update_status(self, message):
        self.status_var.set(message)

def main():
    try:
        root = tk.Tk()
        app = GJYEditorMobile(root)
        root.mainloop()
    except Exception as e:
        print(f"程序错误: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()                                                                                                                                                                                                                                                                                                                                                                                                                          