import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import base64
import os
from datetime import datetime

class GJYEditorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GJY 文件编辑器 v1.0.0")
        self.root.geometry("400x700")
        self.root.resizable(True, True)
        
        # 当前选定的文件夹
        self.current_folder = os.getcwd()
        self.version = "v1.0.0"
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架 - 竖屏布局
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="GJY 文件编辑器", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 版本信息
        version_label = ttk.Label(main_frame, text=f"版本 {self.version}", 
                                 font=("Arial", 10))
        version_label.pack(pady=5)
        
        # 文件夹选择区域
        folder_frame = ttk.LabelFrame(main_frame, text="工作文件夹", padding="10")
        folder_frame.pack(fill=tk.X, pady=10)
        
        self.folder_var = tk.StringVar(value=self.current_folder)
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, state='readonly')
        folder_entry.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        folder_btn = ttk.Button(folder_frame, text="浏览", command=self.select_folder)
        folder_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 文件列表区域
        list_frame = ttk.LabelFrame(main_frame, text="GJY 文件列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 文件列表和滚动条
        list_controls = ttk.Frame(list_frame)
        list_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(list_controls, text="刷新列表", command=self.refresh_file_list).pack(side=tk.LEFT)
        ttk.Button(list_controls, text="打开所在文件夹", command=self.open_folder).pack(side=tk.LEFT, padx=(5, 0))
        
        self.file_listbox = tk.Listbox(list_frame, height=8)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # 文件操作按钮
        file_ops_frame = ttk.Frame(list_frame)
        file_ops_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_ops_frame, text="查看文件", command=self.view_selected_file).pack(side=tk.LEFT)
        ttk.Button(file_ops_frame, text="删除文件", command=self.delete_selected_file).pack(side=tk.LEFT, padx=(5, 0))
        
        # 创建新文件区域
        create_frame = ttk.LabelFrame(main_frame, text="创建新GJY文件", padding="10")
        create_frame.pack(fill=tk.X, pady=10)
        
        # 文件名输入
        ttk.Label(create_frame, text="文件名:").pack(anchor=tk.W)
        self.filename_var = tk.StringVar()
        filename_entry = ttk.Entry(create_frame, textvariable=self.filename_var)
        filename_entry.pack(fill=tk.X, pady=(2, 10))
        
        # 内容输入
        ttk.Label(create_frame, text="文件内容:").pack(anchor=tk.W)
        self.content_text = scrolledtext.ScrolledText(create_frame, height=6, wrap=tk.WORD)
        self.content_text.pack(fill=tk.BOTH, expand=True, pady=(2, 10))
        
        # 创建按钮
        create_btn = ttk.Button(create_frame, text="创建GJY文件", command=self.create_gjy_file)
        create_btn.pack(fill=tk.X)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # 初始刷新文件列表
        self.refresh_file_list()
    
    def select_folder(self):
        """选择工作文件夹"""
        folder = filedialog.askdirectory(initialdir=self.current_folder)
        if folder:
            self.current_folder = folder
            self.folder_var.set(folder)
            self.refresh_file_list()
            self.update_status(f"已切换到文件夹: {folder}")
    
    def refresh_file_list(self):
        """刷新文件列表"""
        self.file_listbox.delete(0, tk.END)
        
        try:
            gjy_files = []
            for file in os.listdir(self.current_folder):
                if file.endswith('.gjy') or file.endswith('.gjyx'):
                    gjy_files.append(file)
            
            # 按文件名排序
            gjy_files.sort()
            
            for file in gjy_files:
                self.file_listbox.insert(tk.END, file)
                
            self.update_status(f"找到 {len(gjy_files)} 个GJY文件")
            
        except Exception as e:
            self.update_status(f"刷新文件列表失败: {e}")
    
    def on_file_select(self, event):
        """文件选择事件"""
        selection = self.file_listbox.curselection()
        if selection:
            filename = self.file_listbox.get(selection[0])
            self.update_status(f"已选择: {filename}")
    
    def view_selected_file(self):
        """查看选中的文件"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文件")
            return
        
        filename = self.file_listbox.get(selection[0])
        filepath = os.path.join(self.current_folder, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 解析文件头信息
            version = "未知版本"
            created_time = "未知时间"
            encoded_text = ""
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith("#GJY"):
                    continue
                elif line.startswith("#v"):
                    version = line[1:]
                elif line.startswith("#Created:"):
                    created_time = line[9:]
                elif line and not line.startswith("#"):
                    encoded_text = line
                    if i + 1 < len(lines):
                        encoded_text += "".join(lines[i+1:]).strip()
                    break
            
            # 解码base64文本
            try:
                decoded_text = base64.b64decode(encoded_text).decode('utf-8')
            except:
                decoded_text = "[无法解码的内容]"
            
            # 在新窗口中显示内容
            self.show_file_content(filename, version, created_time, decoded_text)
            
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败: {e}")
    
    def show_file_content(self, filename, version, created_time, content):
        """在新窗口中显示文件内容"""
        content_window = tk.Toplevel(self.root)
        content_window.title(f"查看文件 - {filename}")
        content_window.geometry("500x600")
        
        # 文件信息区域
        info_frame = ttk.LabelFrame(content_window, text="文件信息", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"文件名: {filename}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"版本: {version}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"创建时间: {created_time}").pack(anchor=tk.W)
        
        # 内容区域
        content_frame = ttk.LabelFrame(content_window, text="文件内容", padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD)
        content_text.pack(fill=tk.BOTH, expand=True)
        content_text.insert(tk.END, content)
        content_text.config(state=tk.DISABLED)
        
        # 关闭按钮
        ttk.Button(content_window, text="关闭", 
                  command=content_window.destroy).pack(pady=10)
    
    def delete_selected_file(self):
        """删除选中的文件"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文件")
            return
        
        filename = self.file_listbox.get(selection[0])
        filepath = os.path.join(self.current_folder, filename)
        
        if messagebox.askyesno("确认删除", f"确定要删除文件 {filename} 吗？"):
            try:
                os.remove(filepath)
                self.refresh_file_list()
                self.update_status(f"已删除文件: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"删除文件失败: {e}")
    
    def create_gjy_file(self):
        """创建新的GJY文件"""
        filename = self.filename_var.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()
        
        if not filename:
            messagebox.showwarning("警告", "请输入文件名")
            return
        
        if not content:
            messagebox.showwarning("警告", "请输入文件内容")
            return
        
        # 确保文件名以.gjy结尾
        if not filename.endswith('.gjy'):
            filename += '.gjy'
        
        filepath = os.path.join(self.current_folder, filename)
        
        if os.path.exists(filepath):
            if not messagebox.askyesno("文件已存在", "文件已存在，是否覆盖？"):
                return
        
        try:
            # 对文本进行base64编码
            encoded_text = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"#GJY\n")
                f.write(f"#{self.version}\n")
                f.write(f"#Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(encoded_text)
            
            self.update_status(f"成功创建文件: {filename}")
            self.refresh_file_list()
            
            # 清空输入框
            self.filename_var.set("")
            self.content_text.delete("1.0", tk.END)
            
            messagebox.showinfo("成功", f"文件 {filename} 创建成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"创建文件失败: {e}")
    
    def open_folder(self):
        """打开所在文件夹"""
        try:
            os.startfile(self.current_folder)  # Windows
        except:
            try:
                os.system(f'open "{self.current_folder}"')  # macOS
            except:
                try:
                    os.system(f'xdg-open "{self.current_folder}"')  # Linux
                except:
                    messagebox.showerror("错误", "无法打开文件夹")
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
        self.root.update_idletasks()

def main():
    """主函数"""
    root = tk.Tk()
    app = GJYEditorUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
        