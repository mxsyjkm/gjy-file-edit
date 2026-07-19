import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import base64
import os
from datetime import datetime
import json
from PIL import Image, ImageTk, ImageDraw
import io

class GJYEditorMobile:
    def __init__(self, root):
        self.root = root
        self.root.title("GJY编辑器 v1.0.3")
        self.root.geometry("450x750")
        self.root.resizable(False, False)
        
        self.version = "v1.0.3"
        self.config_file = "gjy_config.json"
        self.default_storage = os.path.join(os.path.expanduser("~"), "GJY_Files")
        if not os.path.exists(self.default_storage):
            os.makedirs(self.default_storage)
        
        # 加载配置
        self.current_folder = self.load_config()
        self.current_file = None
        self.current_file_type = None
        self.selected_image_path = None
        self.preview_image = None
        
        # 用于A4编辑器的变量
        self.a4_elements = []  # 存储所有元素
        self.selected_element = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        
        self.setup_ui()
    
    def load_config(self):
        """加载配置文件"""
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
        """保存配置"""
        try:
            config = {
                'save_directory': self.current_folder,
                'version': self.version
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题区域
        title_label = ttk.Label(main_frame, text="GJY编辑器 v1.0.3", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=8)
        
        # 文件夹选择区域
        folder_frame = ttk.LabelFrame(main_frame, text="存储位置", padding="8")
        folder_frame.pack(fill=tk.X, pady=6)
        
        display_path = self.current_folder
        if len(display_path) > 30:
            display_path = "..." + display_path[-27:]
        
        self.folder_var = tk.StringVar(value=display_path)
        folder_label = ttk.Label(folder_frame, textvariable=self.folder_var, 
                                font=("Arial", 9), wraplength=400)
        folder_label.pack(fill=tk.X)
        
        btn_frame = ttk.Frame(folder_frame)
        btn_frame.pack(fill=tk.X, pady=4)
        
        ttk.Button(btn_frame, text="更改位置", 
                  command=self.select_folder).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="设为默认", 
                  command=self.set_as_default).pack(side=tk.LEFT, padx=(8,0))
        # 文件列表区域
        list_frame = ttk.LabelFrame(main_frame, text="GJY文件", padding="8")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=6)
        
        list_controls = ttk.Frame(list_frame)
        list_controls.pack(fill=tk.X, pady=4)
        
        ttk.Button(list_controls, text="刷新", 
                  command=self.refresh_file_list).pack(side=tk.LEFT)
        ttk.Button(list_controls, text="打开文件夹", 
                  command=self.open_folder).pack(side=tk.LEFT, padx=(8,0))
        
        # 文件列表框
        self.file_listbox = tk.Listbox(list_frame, height=4, font=("Arial", 10))
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 文件操作按钮
        file_ops_frame = ttk.Frame(list_frame)
        file_ops_frame.pack(fill=tk.X, pady=4)
        
        ttk.Button(file_ops_frame, text="查看", 
                  command=self.view_selected_file).pack(side=tk.LEFT)
        ttk.Button(file_ops_frame, text="编辑", 
                  command=self.edit_selected_file).pack(side=tk.LEFT, padx=(8,0))
        ttk.Button(file_ops_frame, text="删除", 
                  command=self.delete_selected_file).pack(side=tk.LEFT, padx=(8,0))
        
        # 创建文件区域
        create_frame = ttk.LabelFrame(main_frame, text="创建GJY文件", padding="8")
        create_frame.pack(fill=tk.BOTH, expand=True, pady=6)
        
        # 文件类型选择
        type_frame = ttk.Frame(create_frame)
        type_frame.pack(fill=tk.X, pady=4)
        
        ttk.Label(type_frame, text="文件类型:").pack(side=tk.LEFT)
        self.file_type = tk.StringVar(value="text")
        ttk.Radiobutton(type_frame, text="文本", variable=self.file_type, 
                       value="text", command=self.on_type_change).pack(side=tk.LEFT, padx=(10,0))
        ttk.Radiobutton(type_frame, text="图片", variable=self.file_type, 
                       value="image", command=self.on_type_change).pack(side=tk.LEFT, padx=(10,0))
        ttk.Radiobutton(type_frame, text="A4混合", variable=self.file_type, 
                       value="a4", command=self.on_type_change).pack(side=tk.LEFT, padx=(10,0))
        
        # 当前编辑文件显示
        self.current_file_var = tk.StringVar(value="未选择文件")
        ttk.Label(create_frame, textvariable=self.current_file_var, 
                 font=("Arial", 9, "bold"), foreground="blue").pack(anchor=tk.W, pady=(5,0))
        
        # 文件名输入
        ttk.Label(create_frame, text="文件名:").pack(anchor=tk.W)
        self.filename_var = tk.StringVar()
        filename_entry = ttk.Entry(create_frame, textvariable=self.filename_var, 
                                  font=("Arial", 10))
        filename_entry.pack(fill=tk.X, pady=(2, 6))
        
        # 文本内容输入区域
        self.text_frame = ttk.Frame(create_frame)
        
        ttk.Label(self.text_frame, text="文本内容:").pack(anchor=tk.W)
        self.content_text = scrolledtext.ScrolledText(self.text_frame, height=3, 
                                                     wrap=tk.WORD, font=("Arial", 10))
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
        # 图片选择区域
        self.image_frame = ttk.Frame(create_frame)
        
        ttk.Label(self.image_frame, text="选择图片:").pack(anchor=tk.W)
        image_btn_frame = ttk.Frame(self.image_frame)
        image_btn_frame.pack(fill=tk.X, pady=2)
        
        self.image_path_var = tk.StringVar(value="未选择图片")
        ttk.Label(image_btn_frame, textvariable=self.image_path_var, 
                 font=("Arial", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(image_btn_frame, text="选择图片", 
                  command=self.select_image).pack(side=tk.RIGHT)
        
        # 图片预览区域
        self.preview_frame = ttk.LabelFrame(self.image_frame, text="图片预览", padding="5")
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_label = ttk.Label(self.preview_frame, text="暂无预览", 
                                      font=("Arial", 10), justify=tk.CENTER)
        self.preview_label.pack(expand=True, fill=tk.BOTH)
        
        # A4混合编辑区域
        self.a4_frame = ttk.Frame(create_frame)
        
        # A4编辑器控制按钮
        a4_controls = ttk.Frame(self.a4_frame)
        a4_controls.pack(fill=tk.X, pady=4)
        
        ttk.Button(a4_controls, text="添加文本", 
                  command=self.add_text_element).pack(side=tk.LEFT)
        ttk.Button(a4_controls, text="添加图片", 
                  command=self.add_image_element).pack(side=tk.LEFT, padx=(8,0))
        ttk.Button(a4_controls, text="删除选中", 
                  command=self.delete_selected_element).pack(side=tk.LEFT, padx=(8,0))
        # A4预览区域
        self.a4_preview_frame = ttk.LabelFrame(self.a4_frame, text="A4页面预览", padding="5")
        self.a4_preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建A4画布
        self.a4_canvas = tk.Canvas(self.a4_preview_frame, bg="white", width=350, height=500)
        self.a4_canvas.pack(expand=True, fill=tk.BOTH, pady=5)
        
        # 绘制A4页面边框
        self.a4_canvas.create_rectangle(10, 10, 340, 490, outline="black", width=1)
        
        # 绑定画布事件
        self.a4_canvas.bind("<Button-1>", self.on_canvas_click)
        self.a4_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.a4_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.a4_canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        
        # 按钮框架
        action_btn_frame = ttk.Frame(create_frame)
        action_btn_frame.pack(fill=tk.X, pady=4)
        
        ttk.Button(action_btn_frame, text="新建文件", 
                  command=self.create_gjy_file).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(action_btn_frame, text="保存修改", 
                  command=self.save_gjy_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8,0))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, font=("Arial", 9))
        status_bar.pack(fill=tk.X, pady=(8, 0))
        
        # 绑定事件
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        self.file_listbox.bind('<Double-Button-1>', lambda e: self.view_selected_file())
        
        # 初始显示文本编辑区域
        self.on_type_change()
        
        # 初始刷新
        self.refresh_file_list()
    
    def on_type_change(self):
        """文件类型切换"""
        file_type = self.file_type.get()
        if file_type == "text":
            self.text_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 6))
            self.image_frame.pack_forget()
            self.a4_frame.pack_forget()
        elif file_type == "image":
            self.text_frame.pack_forget()
            self.image_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 6))
            self.a4_frame.pack_forget()
        else:  # A4混合
            self.text_frame.pack_forget()
            self.image_frame.pack_forget()
            self.a4_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 6))
    
    def select_image(self):
        """选择图片文件并显示预览"""
        filetypes = [
            ('图片文件', '*.jpg *.jpeg *.png *.gif *.bmp'),
            ('所有文件', '*.*')
        ]
        
        filepath = filedialog.askopenfilename(
            title="选择图片",
            filetypes=filetypes
        )
        
        if filepath:
            self.selected_image_path = filepath
            
            # 显示短路径
            display_path = filepath
            if len(display_path) > 30:
                display_path = "..." + display_path[-27:]
            self.image_path_var.set(display_path)
            
            # 显示图片预览
            self.show_image_preview(filepath)
            self.update_status(f"已选择图片: {os.path.basename(filepath)}")
    
    def show_image_preview(self, image_path):
        """显示图片预览"""
        try:
            # 打开图片并调整大小以适应预览区域
            image = Image.open(image_path)
            
            # 获取预览区域的大致尺寸
            max_width = 300
            max_height = 200
            
            # 计算调整后的尺寸
            width, height = image.size
            if width > max_width or height > max_height:
                ratio = min(max_width/width, max_height/height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为Tkinter可用的格式
            self.preview_image = ImageTk.PhotoImage(image)
            
            # 更新预览标签
            self.preview_label.configure(image=self.preview_image, text="")
            
        except Exception as e:
            self.preview_label.configure(image="", text=f"预览失败: {str(e)}")
            self.update_status(f"图片预览失败: {e}")
    
    def add_text_element(self):
        """添加文本元素到A4页面"""
        text = tk.simpledialog.askstring("添加文本", "请输入文本内容:")
        if text:
            # 创建文本元素
            element = {
                "type": "text",
                "content": text,
                "x": 50,
                "y": 50,
                "id": None
            }
            
            # 在画布上创建文本
            element_id = self.a4_canvas.create_text(
                50, 50, 
                text=text, 
                fill="black",
                font=("Arial", 12),
                tags=("draggable", "element")
            )
            
            element["id"] = element_id
            self.a4_elements.append(element)
            self.update_status(f"已添加文本元素: {text}")
    
    def add_image_element(self):
        """添加图片元素到A4页面"""
        filetypes = [
            ('图片文件', '*.jpg *.jpeg *.png *.gif *.bmp'),
            ('所有文件', '*.*')
        ]
        
        filepath = filedialog.askopenfilename(
            title="选择图片",
            filetypes=filetypes
        )
        
        if filepath:
            try:
                # 打开并调整图片大小
                image = Image.open(filepath)
                max_size = 150
                width, height = image.size
                
                if width > max_size or height > max_size:
                    ratio = min(max_size/width, max_size/height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 转换为Tkinter格式
                photo = ImageTk.PhotoImage(image)
                
                # 创建图片元素
                element = {
                    "type": "image",
                    "content": filepath,
                    "x": 100,
                    "y": 100,
                    "id": None,
                    "photo": photo,
                    "width": new_width,
                    "height": new_height
                }
                # 在画布上创建图片
                element_id = self.a4_canvas.create_image(
                    100, 100, 
                    image=photo,
                    tags=("draggable", "element")
                )
                
                element["id"] = element_id
                self.a4_elements.append(element)
                self.update_status(f"已添加图片元素: {os.path.basename(filepath)}")
                
            except Exception as e:
                messagebox.showerror("错误", f"添加图片失败: {e}")
    
    def delete_selected_element(self):
        """删除选中的元素"""
        if self.selected_element:
            # 从画布删除
            self.a4_canvas.delete(self.selected_element["id"])
            
            # 从元素列表删除
            self.a4_elements = [e for e in self.a4_elements if e["id"] != self.selected_element["id"]]
            
            self.selected_element = None
            self.update_status("已删除选中元素")
        else:
            messagebox.showwarning("提示", "请先选择一个元素")
    
    def on_canvas_click(self, event):
        """画布点击事件"""
        # 查找点击的元素
        clicked_items = self.a4_canvas.find_overlapping(event.x-5, event.y-5, event.x+5, event.y+5)
        
        for item in clicked_items:
            tags = self.a4_canvas.gettags(item)
            if "element" in tags:
                # 找到对应的元素
                for element in self.a4_elements:
                    if element["id"] == item:
                        self.selected_element = element
                        
                        # 高亮显示选中的元素
                        if element["type"] == "text":
                            self.a4_canvas.itemconfig(item, fill="red")
                        else:
                            # 对于图片，添加一个选择框
                            if "selection_box" in element:
                                self.a4_canvas.delete(element["selection_box"])
                            
                            selection_box = self.a4_canvas.create_rectangle(
                                element["x"] - element["width"]//2 - 2,
                                element["y"] - element["height"]//2 - 2,
                                element["x"] + element["width"]//2 + 2,
                                element["y"] + element["height"]//2 + 2,
                                outline="red", width=2
                            )
                            element["selection_box"] = selection_box
                        
                        self.drag_data["x"] = event.x
                        self.drag_data["y"] = event.y
                        self.drag_data["item"] = item
                        return
        
        # 如果没有点击到元素，取消选择
        self.deselect_all()
    
    def on_canvas_drag(self, event):
        """画布拖动事件"""
        if self.drag_data["item"]:
            # 计算移动距离
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            
            # 移动元素
            self.a4_canvas.move(self.drag_data["item"], dx, dy)
            
            # 更新元素位置
            for element in self.a4_elements:
                if element["id"] == self.drag_data["item"]:
                    element["x"] += dx
                    element["y"] += dy
                    
                    # 更新选择框位置
                    if "selection_box" in element:
                        self.a4_canvas.coords(
                            element["selection_box"],
                            element["x"] - element["width"]//2 - 2,
                            element["y"] - element["height"]//2 - 2,
                            element["x"] + element["width"]//2 + 2,
                            element["y"] + element["height"]//2 + 2
                        )
                    break
            
            # 更新拖动数据
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
    
    def on_canvas_release(self, event):
        """画布释放事件"""
        self.drag_data["item"] = None
    
    def deselect_all(self):
        """取消所有选择"""
        if self.selected_element:
            if self.selected_element["type"] == "text":
                self.a4_canvas.itemconfig(self.selected_element["id"], fill="black")
            else:
                if "selection_box" in self.selected_element:
                    self.a4_canvas.delete(self.selected_element["selection_box"])
        
        self.selected_element = None
    
    def view_selected_file(self):
        """查看选中的文件"""
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
        """显示文件内容的窗口"""
        win = tk.Toplevel(self.root)
        
        if file_info['file_type'] == 'text':
            win.title(f"查看: {filename}")
            win.geometry("400x500")
        elif file_info['file_type'] == 'image':
            win.title(f"查看: {filename}")
            win.geometry("450x550")
        else:  # A4混合
            win.title(f"查看: {filename}")
            win.geometry("500x600")
        
        # 信息区域
        info_frame = ttk.LabelFrame(win, text="文件信息", padding="8")
        info_frame.pack(fill=tk.X, padx=8, pady=8)
        
        ttk.Label(info_frame, text=f"文件: {filename}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"类型: {file_info['file_type']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"版本: {file_info['version']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"创建: {file_info['created_time']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"修改: {file_info['modified_time']}").pack(anchor=tk.W)
        
        # 内容区域
        content_frame = ttk.LabelFrame(win, text="内容预览", padding="8")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        if file_info['file_type'] == 'text':
            text_widget = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, font=("Arial", 10))
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, file_info['content'])
            text_widget.config(state=tk.DISABLED)
        elif file_info['file_type'] == 'image':
            # 显示图片内容
            try:
                # 解码base64图片数据
                image_data = base64.b64decode(file_info['encoded_data'])
                image = Image.open(io.BytesIO(image_data))
                
                # 调整图片大小以适应窗口
                max_width = 350
                max_height = 300
                width, height = image.size
                
                if width > max_width or height > max_height:
                    ratio = min(max_width/width, max_height/height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(image)
                
                # 创建图片标签
                image_label = ttk.Label(content_frame, image=photo)
                image_label.image = photo  # 保持引用
                image_label.pack(expand=True)
                
                # 显示图片信息
                info_text = f"图片尺寸: {width} x {height}\n文件大小: {len(file_info['encoded_data'])} 字符"
                ttk.Label(content_frame, text=info_text, justify=tk.CENTER).pack(pady=5)
                
            except Exception as e:
                error_text = f"图片显示失败: {str(e)}"
                ttk.Label(content_frame, text=error_text, justify=tk.CENTER).pack(expand=True)
        else:  # A4混合
            # 显示A4布局预览
            canvas = tk.Canvas(content_frame, bg="white", width=400, height=400)
            canvas.pack(expand=True, fill=tk.BOTH, pady=5)
            
            # 绘制A4页面边框
            canvas.create_rectangle(20, 20, 380, 380, outline="black", width=1)
            
            # 绘制所有元素
            for element_data in file_info['a4_elements']:
                if element_data['type'] == 'text':
                    canvas.create_text(
                        element_data['x'], element_data['y'],
                        text=element_data['content'],
                        fill="black",
                        font=("Arial", 12)
                    )
                elif element_data['type'] == 'image':
                    try:
                        # 解码图片数据
                        image_data = base64.b64decode(element_data['image_data'])
                        image = Image.open(io.BytesIO(image_data))
                        
                        # 调整大小
                        if element_data.get('width') and element_data.get('height'):
                            image = image.resize(
                                (element_data['width'], element_data['height']), 
                                Image.Resampling.LANCZOS
                            )
                        
                        photo = ImageTk.PhotoImage(image)
                        canvas.create_image(element_data['x'], element_data['y'], image=photo)
                        # 保持引用
                        if not hasattr(canvas, 'images'):
                            canvas.images = []
                        canvas.images.append(photo)
                    except Exception as e:
                        canvas.create_text(
                            element_data['x'], element_data['y'],
                            text=f"[图片加载失败: {e}]",
                            fill="red"
                        )
            
            # 显示元素数量
            ttk.Label(content_frame, 
                     text=f"包含 {len(file_info['a4_elements'])} 个元素", 
                     justify=tk.CENTER).pack(pady=5)
        
        # 按钮
        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=8)
    
    def parse_gjy_file(self, filepath):
        """解析GJY文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        file_info = {
            'file_type': 'text',
            'version': "未知版本",
            'created_time': "未知时间",
            'modified_time': "无记录",
            'encoded_data': "",
            'content': "",
            'a4_elements': []
        }
        
        # 解析头部信息
        for i, line in enumerate(lines):
            if line.startswith("#GJY"):
                continue
            elif line.startswith("#v"):
                file_info['version'] = line[1:]
            elif line.startswith("#Created:"):
                file_info['created_time'] = line[9:]
            elif line.startswith("#Modified:"):
                file_info['modified_time'] = line[10:]
            elif line.startswith("#Type:"):
                file_info['file_type'] = line[6:]
            elif line.startswith("#A4_ELEMENTS:"):
                # 解析A4元素数据
                elements_data = line[13:]
                if elements_data:
                    try:
                        file_info['a4_elements'] = json.loads(elements_data)
                    except:
                        file_info['a4_elements'] = []
                break
            elif line and not line.startswith("#"):
                file_info['encoded_data'] = line.strip()
                break
        
        # 解码内容
        try:
            if file_info['file_type'] == 'text':
                file_info['content'] = base64.b64decode(file_info['encoded_data']).decode('utf-8')
        except:
            if file_info['file_type'] == 'text':
                file_info['content'] = "[无法解码的文本内容]"
        
        return file_info
    
    def set_as_default(self):
        """设置为默认存储位置"""
        self.save_config()
        messagebox.showinfo("成功", f"已设置为默认存储位置:\n{self.current_folder}")
    
    def select_folder(self):
        """选择文件夹"""
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
        """刷新文件列表"""
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
        """文件选择事件"""
        selection = self.file_listbox.curselection()
        if selection:
            filename = self.file_listbox.get(selection[0])
            self.update_status(f"已选择: {filename}")
    
    def clear_edit(self):
        """清空编辑区域"""
        self.current_file = None
        self.current_file_type = None
        self.current_file_var.set("未选择文件")
        self.filename_var.set("")
        self.content_text.delete("1.0", tk.END)
        self.image_path_var.set("未选择图片")
        self.preview_label.configure(image="", text="暂无预览")
        self.selected_image_path = None
        
        # 清空A4编辑器
        self.a4_canvas.delete("all")
        # 重新绘制A4页面边框
        self.a4_canvas.create_rectangle(10, 10, 340, 490, outline="black", width=1)
        self.a4_elements = []
        self.selected_element = None
        
        self.file_type.set("text")
        self.on_type_change()
    
    def edit_selected_file(self):
        """编辑选中的文件"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要编辑的文件")
            return
        
        filename = self.file_listbox.get(selection[0])
        filepath = os.path.join(self.current_folder, filename)
        
        try:
            file_info = self.parse_gjy_file(filepath)
            
            # 填充编辑区域
            self.current_file = filename
            self.current_file_type = file_info['file_type']
            self.current_file_var.set(f"正在编辑: {filename}")
            self.filename_var.set(filename.replace('.gjy', '').replace('.gjyx', ''))
            
            if file_info['file_type'] == 'text':
                self.file_type.set("text")
                self.content_text.delete("1.0", tk.END)
                self.content_text.insert("1.0", file_info['content'])
            elif file_info['file_type'] == 'image':
                self.file_type.set("image")
                self.image_path_var.set("[原图片数据 - 需要重新选择图片]")
                self.preview_label.configure(image="", text="编辑时需要重新选择图片")
            else:  # A4混合
                self.file_type.set("a4")
                # 加载A4元素到编辑器
                self.load_a4_elements(file_info['a4_elements'])
            
            self.on_type_change()
            self.update_status(f"已加载文件: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败: {e}")
    
    def load_a4_elements(self, elements_data):
        """加载A4元素到编辑器"""
        # 清空当前元素
        self.a4_canvas.delete("all")
        self.a4_canvas.create_rectangle(10, 10, 340, 490, outline="black", width=1)
        self.a4_elements = []
        
        # 加载元素
        for element_data in elements_data:
            if element_data['type'] == 'text':
                # 创建文本元素
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
                try:                                                             # 解码图片数据
                    image_data = base64.b64decode(element_data['image_data'])
                    image = Image.open(io.BytesIO(image_data))
                    
                    # 转换为Tkinter格式
                    photo = ImageTk.PhotoImage(image)
                    
                    # 创建图片元素
                    element_id = self.a4_canvas.create_image(
                        element_data['x'], element_data['y'], 
                        image=photo,
                        tags=("draggable", "element")
                    )
                    
                    element = {
                        "type": "image",
                        "content": element_data.get('original_path', ''),
                        "x": element_data['x'],
                        "y": element_data['y'],
                        "id": element_id,
                        "photo": photo,
                        "width": element_data.get('width', 100),
                        "height": element_data.get('height', 100)
                    }
                    
                    self.a4_elements.append(element)
                    
                except Exception as e:
                    self.update_status(f"加载图片元素失败: {e}")
    
    
    def on_mouse_wheel(self, event):
        """鼠标滚轮缩放选中图片"""
        if self.selected_element and self.selected_element["type"] == "image":
            scale = 1.1 if event.delta > 0 else 0.9
            new_w = int(self.selected_element["width"] * scale)
            new_h = int(self.selected_element["height"] * scale)
            if new_w > 10 and new_h > 10:
                self.selected_element["width"] = new_w
                self.selected_element["height"] = new_h
                from PIL import ImageTk, Image
                img = Image.open(self.selected_element["content"]).resize((new_w, new_h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.selected_element["photo"] = photo
                self.a4_canvas.itemconfig(self.selected_element["id"], image=photo)

    def save_gjy_file(self):
        """保存GJY文件（新建或修改）"""
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
        else:  # A4混合
            if not self.a4_elements:
                messagebox.showwarning("提示", "请至少添加一个元素到A4页面")
                return
        
        if not filename.endswith('.gjy'):
            filename += '.gjy'
        
        filepath = os.path.join(self.current_folder, filename)
        is_new_file = self.current_file is None or self.current_file != filename
        
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取原始创建时间（如果是修改现有文件）
            if not is_new_file and os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("#Created:"):
                            created_time = line.strip()[9:]
                            break
            else:
                created_time = current_time
            
            # 编码数据
            if file_type == "text":
                content = self.content_text.get("1.0", tk.END).strip()
                encoded_data = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            elif file_type == "image":
                # 读取并编码图片
                with open(self.selected_image_path, 'rb') as img_file:
                    image_data = img_file.read()
                encoded_data = base64.b64encode(image_data).decode('utf-8')
            else:  # A4混合
                # 准备A4元素数据
                a4_elements_data = []
                for element in self.a4_elements:
                    element_data = {
                        'type': element['type'],
                        'x': element['x'],
                        'y': element['y']
                    }
                    
                    if element['type'] == 'text':
                        element_data['content'] = element['content']
                    elif element['type'] == 'image':
                        # 读取并编码图片
                        with open(element['content'], 'rb') as img_file:
                            image_data = img_file.read()
                        element_data['image_data'] = base64.b64encode(image_data).decode('utf-8')
                        element_data['original_path'] = element['content']
                        element_data['width'] = element['width']
                        element_data['height'] = element['height']
                    
                    a4_elements_data.append(element_data)
                
                encoded_data = ""  # A4类型不使用encoded_data字段
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"#GJY\n")
                f.write(f"#{self.version}\n")
                f.write(f"#Type: {file_type}\n")
                f.write(f"#Created: {created_time}\n")
                f.write(f"#Modified: {current_time}\n")
                
                if file_type == "a4":
                    # 保存A4元素数据
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
        """创建新文件"""
        self.current_file = None
        self.current_file_type = None
        self.current_file_var.set("创建新文件")
        self.save_gjy_file()
    
    def delete_selected_file(self):
        """删除文件"""
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
        """打开文件夹"""
        try:
            messagebox.showinfo("存储位置", f"文件保存在:\n{self.current_folder}")
        except Exception as e:
            self.update_status(f"打开失败: {e}")
    
    def update_status(self, message):
        """更新状态"""
        self.status_var.set(message)

def main():
    """主函数"""
    try:
        root = tk.Tk()
        app = GJYEditorMobile(root)
        root.mainloop()
    except Exception as e:
        print(f"程序错误: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()    	                 