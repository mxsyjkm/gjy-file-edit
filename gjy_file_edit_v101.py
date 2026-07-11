import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import base64
import os
from datetime import datetime
import json

class GJYEditorMobile:
    def __init__(self, root):
        self.root = root
        self.root.title("GJY编辑器 v1.0.1")
        self.root.geometry("350x650")
        self.root.resizable(False, False)
        
        self.version = "v1.0.1"
        self.config_file = "gjy_config.json"
        
        self.default_storage = os.path.join(os.path.expanduser("~"), "GJY_Files")
        if not os.path.exists(self.default_storage):
            os.makedirs(self.default_storage)
        
        # 加载配置
        self.current_folder = self.load_config()
        self.current_file = None  # 当前编辑的文件
        
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
        title_label = ttk.Label(main_frame, text="GJY编辑器 v1.0.1", 
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
                                font=("Arial", 9), wraplength=300)
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
        self.file_listbox = tk.Listbox(list_frame, height=5, font=("Arial", 10))
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
        
        # 创建/编辑文件区域
        edit_frame = ttk.LabelFrame(main_frame, text="编辑GJY文件", padding="8")
        edit_frame.pack(fill=tk.X, pady=6)
        
        # 当前编辑文件显示
        self.current_file_var = tk.StringVar(value="未选择文件")
        ttk.Label(edit_frame, textvariable=self.current_file_var, 
                 font=("Arial", 9, "bold"), foreground="blue").pack(anchor=tk.W)
        
        # 文件名输入
        ttk.Label(edit_frame, text="文件名:").pack(anchor=tk.W)
        self.filename_var = tk.StringVar()
        filename_entry = ttk.Entry(edit_frame, textvariable=self.filename_var, 
                                  font=("Arial", 10))
        filename_entry.pack(fill=tk.X, pady=(2, 6))
        
        # 内容输入
        ttk.Label(edit_frame, text="内容:").pack(anchor=tk.W)
        self.content_text = scrolledtext.ScrolledText(edit_frame, height=3, 
                                                     wrap=tk.WORD, font=("Arial", 10))
        self.content_text.pack(fill=tk.X, pady=(2, 6))
        
        # 按钮框架
        action_btn_frame = ttk.Frame(edit_frame)
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
        
        # 初始刷新
        self.refresh_file_list()
    
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
        self.current_file_var.set("未选择文件")
        self.filename_var.set("")
        self.content_text.delete("1.0", tk.END)
    
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
    
    def parse_gjy_file(self, filepath):
        """解析GJY文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        file_info = {
            'version': "未知版本",
            'created_time': "未知时间",
            'modified_time': "无记录",
            'encoded_text': "",
            'decoded_text': ""
        }
        
        for line in lines:
            if line.startswith("#GJY"):
                continue
            elif line.startswith("#v"):
                file_info['version'] = line[1:]
            elif line.startswith("#Created:"):
                file_info['created_time'] = line[9:]
            elif line.startswith("#Modified:"):
                file_info['modified_time'] = line[10:]
            elif line and not line.startswith("#"):
                file_info['encoded_text'] = line
                break
        
        # 解码内容
        try:
            file_info['decoded_text'] = base64.b64decode(file_info['encoded_text']).decode('utf-8')
        except:
            file_info['decoded_text'] = "[无法解码的内容]"
        
        return file_info
    
    def show_content_window(self, filename, file_info):
        """显示文件内容的窗口"""
        win = tk.Toplevel(self.root)
        win.title(f"查看: {filename}")
        win.geometry("320x500")
        
        # 信息区域
        info_frame = ttk.LabelFrame(win, text="文件信息", padding="8")
        info_frame.pack(fill=tk.X, padx=8, pady=8)
        
        ttk.Label(info_frame, text=f"{filename}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"{file_info['version']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"创建: {file_info['created_time']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"修改: {file_info['modified_time']}").pack(anchor=tk.W)
        
        # 内容区域
        content_frame = ttk.LabelFrame(win, text="内容", padding="8")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        text_widget = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, font=("Arial", 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, file_info['decoded_text'])
        text_widget.config(state=tk.DISABLED)
        
        # 按钮
        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=8)
    
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
            self.current_file_var.set(f"正在编辑: {filename}")
            self.filename_var.set(filename.replace('.gjy', '').replace('.gjyx', ''))
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert("1.0", file_info['decoded_text'])
            
            self.update_status(f"已加载文件: {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败: {e}")
    
    def save_gjy_file(self):
        """保存GJY文件（新建或修改）"""
        filename = self.filename_var.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()
        
        if not filename:
            messagebox.showwarning("提示", "请输入文件名")
            return
        
        if not content:
            messagebox.showwarning("提示", "请输入内容")
            return
        
        if not filename.endswith('.gjy'):
            filename += '.gjy'
        
        filepath = os.path.join(self.current_folder, filename)
        is_new_file = self.current_file is None or self.current_file != filename
        
        try:
            encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 修复：正确获取原始创建时间
            if not is_new_file and os.path.exists(filepath):
                # 读取原文件的所有行
                with open(filepath, 'r', encoding='utf-8') as f:
                    original_lines = f.readlines()
                
                # 从原文件中提取创建时间
                created_time = "未知时间"
                for line in original_lines:
                    if line.startswith("#Created:"):
                        created_time = line.strip()[9:]  # 去掉 "#Created: " 前缀
                        break
            else:
                # 新文件使用当前时间
                created_time = current_time
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"#GJY\n")
                f.write(f"#{self.version}\n")
                f.write(f"#Created: {created_time}\n")
                f.write(f"#Modified: {current_time}\n")
                f.write(encoded)
            
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