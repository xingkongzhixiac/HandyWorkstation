# -*- coding: utf-8 -*-

import os
import logging
import threading
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

logger = logging.getLogger("organizer.gui")

class MainWindow:
    """管理平台主界面"""
    def __init__(self, root, plugin_manager):
        self.root = root
        self.pm = plugin_manager
        self.root.title("本地实用工具与插件管理控制台 (Utility Hub)")
        self.root.geometry("820x600")
        self.root.configure(bg="#0f172a")
        self.root.resizable(False, False)

        # 调色盘
        self.bg_color = "#0f172a"
        self.card_color = "#1e293b"
        self.text_white = "#f8fafc"
        self.text_gray = "#94a3b8"
        self.accent_blue = "#4f46e5"
        self.success_green = "#10b981"
        self.fail_red = "#ef4444"

        # 样式定义
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TScrollbar', background=self.card_color, borderwidth=0)

        # 插件状态颜色字典: plugin_id -> "gray" | "green" | "red"
        self.plugin_status = {p.id: "gray" for p in self.pm.get_plugins()}
        self.status_canvases = {}
        self.plugin_buttons = {}  # 记录按钮以高亮当前选中项

        # 渲染主骨架布局
        self._setup_layout()

        # 默认选中第一个插件
        plugins = self.pm.get_plugins()
        if plugins:
            self._select_plugin(plugins[0].id)

    def _setup_layout(self):
        # 1. 顶部栏 (Header)
        header_frame = tk.Frame(self.root, bg=self.bg_color)
        header_frame.pack(fill="x", padx=16, pady=8)
        
        title_lbl = tk.Label(header_frame, text="⚡ 本地工具与集成插件管理平台", font=("Microsoft YaHei", 14, "bold"), fg="#818cf8", bg=self.bg_color)
        title_lbl.pack(side="left")
        
        lbl_info = tk.Label(header_frame, text="沙箱测试目录: test_sandbox/", font=("Microsoft YaHei", 9), fg=self.text_gray, bg=self.bg_color)
        lbl_info.pack(side="right", pady=4)

        # 2. 左右分割主面板 (Main Body)
        body_frame = tk.Frame(self.root, bg=self.bg_color)
        body_frame.pack(fill="both", expand=True, padx=16, pady=8)

        # 左边栏：插件列表管理
        self.left_sidebar = tk.Frame(body_frame, width=240, bg=self.card_color, borderwidth=1, relief="solid")
        self.left_sidebar.pack(side="left", fill="y", padx=(0, 12))
        self.left_sidebar.pack_propagate(False)

        lbl_sidebar = tk.Label(self.left_sidebar, text="🔌 已加载插件模块", font=("Microsoft YaHei", 10, "bold"), fg=self.text_white, bg=self.card_color)
        lbl_sidebar.pack(fill="x", pady=12)

        # 插件按钮容器
        self.plugin_btn_container = tk.Frame(self.left_sidebar, bg=self.card_color)
        self.plugin_btn_container.pack(fill="both", expand=True, padx=8)

        self._render_plugin_list()

        # 左侧最下方“运行所有测试”按钮
        btn_test_all = tk.Button(
            self.left_sidebar, 
            text="🧪 运行所有插件结合测试", 
            font=("Microsoft YaHei", 9, "bold"), 
            bg=self.accent_blue, 
            fg="white", 
            relief="flat", 
            cursor="hand2", 
            command=self._run_all_tests
        )
        btn_test_all.pack(fill="x", padx=12, pady=16)
        self._bind_btn_effect(btn_test_all, self.accent_blue, "#6366f1")

        # 右侧：插件详细工作区
        self.right_workspace = tk.Frame(body_frame, bg=self.card_color, borderwidth=1, relief="solid")
        self.right_workspace.pack(side="right", fill="both", expand=True)
        self.right_workspace.pack_propagate(False)

        # 存放动态加载的工作面板
        self.active_plugin_id = None
        self.detail_area = tk.Frame(self.right_workspace, bg=self.card_color)
        self.detail_area.pack(fill="both", expand=True, padx=16, pady=16)

    def _bind_btn_effect(self, btn, normal_bg, active_bg):
        """为 flat 按钮绑定按压及悬停高亮反馈"""
        btn.configure(activebackground=normal_bg, activeforeground="white")
        def on_enter(e):
            if btn.cget("state") != "disabled":
                btn.configure(bg=active_bg)
        def on_leave(e):
            if btn.cget("state") != "disabled":
                btn.configure(bg=normal_bg)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def _render_plugin_list(self):
        for widget in self.plugin_btn_container.winfo_children():
            widget.destroy()

        for plugin in self.pm.get_plugins():
            p_id = plugin.id
            p_frame = tk.Frame(self.plugin_btn_container, bg=self.card_color, height=45)
            p_frame.pack(fill="x", pady=4)
            p_frame.pack_propagate(False)

            btn = tk.Button(
                p_frame, 
                text=f" {plugin.name} ➔", 
                font=("Microsoft YaHei", 9, "bold"), 
                fg=self.text_white, 
                bg=self.card_color, 
                activebackground="#334155", 
                activeforeground=self.text_white, 
                relief="flat", 
                anchor="w",
                cursor="hand2",
                command=lambda id=p_id: self._select_plugin(id)
            )
            btn.pack(side="left", fill="both", expand=True, padx=4)
            self.plugin_buttons[p_id] = btn

            # 状态灯
            canvas = tk.Canvas(p_frame, width=15, height=15, bg=self.card_color, highlightthickness=0)
            canvas.pack(side="right", padx=12)
            self.status_canvases[p_id] = canvas
            self._draw_status_light(p_id)

    def _draw_status_light(self, p_id):
        canvas = self.status_canvases.get(p_id)
        if not canvas:
            return
        canvas.delete("all")
        status = self.plugin_status.get(p_id, "gray")
        
        color = "#64748b"
        if status == "green":
            color = self.success_green
        elif status == "red":
            color = self.fail_red
            
        canvas.create_oval(2, 2, 13, 13, fill=color, outline="")

    def _select_plugin(self, p_id):
        self.active_plugin_id = p_id
        
        # 刷新左侧选中高亮
        for id, btn in self.plugin_buttons.items():
            if id == p_id:
                btn.configure(bg="#334155")
            else:
                btn.configure(bg=self.card_color)

        for widget in self.detail_area.winfo_children():
            widget.destroy()

        plugin = self.pm.get_plugin(p_id)
        if not plugin:
            return

        header = tk.Frame(self.detail_area, bg=self.card_color)
        header.pack(fill="x", pady=4)
        
        tk.Label(header, text=plugin.name, font=("Microsoft YaHei", 12, "bold"), fg="#818cf8", bg=self.card_color).pack(anchor="w")
        tk.Label(header, text=plugin.description, font=("Microsoft YaHei", 9), fg=self.text_gray, bg=self.card_color, wraplength=480, justify="left").pack(anchor="w", pady=4)

        btn_test = tk.Button(
            header, 
            text="🧪 结合测试验证 (集成沙箱自测)", 
            font=("Microsoft YaHei", 8, "bold"), 
            bg="#374151", 
            fg="white", 
            relief="flat", 
            cursor="hand2", 
            command=lambda id=p_id: self._run_single_test(id)
        )
        btn_test.pack(anchor="w", pady=8)
        self._bind_btn_effect(btn_test, "#374151", "#4b5563")

        divider = tk.Frame(self.detail_area, height=1, bg="#334155")
        divider.pack(fill="x", pady=12)

        if p_id == "organizer":
            self._render_organizer_panel(plugin)
        elif p_id == "everything_cleanup":
            self._render_everything_panel(plugin)

    def _run_single_test(self, p_id):
        def run():
            passed, detail = self.pm.run_plugin_test(p_id)
            if passed:
                self.plugin_status[p_id] = "green"
                messagebox.showinfo("自测通过", f"插件自测成功！\n{detail}")
            else:
                self.plugin_status[p_id] = "red"
                messagebox.showwarning("自测失败", f"插件结合测试失败：\n{detail}")
            self.root.after(10, self._draw_status_light, p_id)
        threading.Thread(target=run, daemon=True).start()

    def _run_all_tests(self):
        def run():
            for plugin in self.pm.get_plugins():
                passed, _ = self.pm.run_plugin_test(plugin.id)
                self.plugin_status[plugin.id] = "green" if passed else "red"
                self.root.after(10, self._draw_status_light, plugin.id)
            messagebox.showinfo("测试结束", "所有可用插件的结合性沙箱自测已全部执行完毕！")
        threading.Thread(target=run, daemon=True).start()

    # ================= 1. 目录整理插件面板 =================
    def _render_organizer_panel(self, plugin):
        panel = tk.Frame(self.detail_area, bg=self.card_color)
        panel.pack(fill="both", expand=True)

        # 目录选择
        dir_frame = tk.Frame(panel, bg=self.card_color)
        dir_frame.pack(fill="x", pady=8)
        
        tk.Label(dir_frame, text="目标目录:", font=("Microsoft YaHei", 9), fg=self.text_white, bg=self.card_color).pack(side="left")
        self.org_dir_entry = tk.Entry(dir_frame, font=("Microsoft YaHei", 9), bg="#0f172a", fg=self.text_white, insertbackground="white", borderwidth=1, relief="solid")
        self.org_dir_entry.pack(side="left", fill="x", expand=True, padx=8)
        
        # 默认将目标路径设为本地隔离沙箱路径，防范误伤用户真实C盘
        default_sandbox = os.path.abspath(os.path.join(os.getcwd(), "test_sandbox", "organizer"))
        self.org_dir_entry.insert(0, default_sandbox)
        
        btn_browse = tk.Button(dir_frame, text=" 浏览... ", font=("Microsoft YaHei", 8), bg=self.accent_blue, fg="white", relief="flat", cursor="hand2", command=self._browse_org_dir)
        btn_browse.pack(side="right")
        self._bind_btn_effect(btn_browse, self.accent_blue, "#6366f1")

        # 特别增加的“混乱演示文件生成”指引按钮
        demo_frame = tk.Frame(panel, bg=self.card_color)
        demo_frame.pack(fill="x", pady=4)
        
        tk.Label(demo_frame, text="首次测试？一键生成乱放的测试文件 ➔", font=("Microsoft YaHei", 9), fg="#e2e8f0", bg=self.card_color).pack(side="left")
        btn_setup_mock = tk.Button(
            demo_frame, 
            text=" 📥 生成10个混乱测试文件 ", 
            font=("Microsoft YaHei", 8, "bold"), 
            bg="#d97706", # 可视化橙色
            fg="white", 
            relief="flat", 
            cursor="hand2", 
            command=self._setup_mock_files
        )
        btn_setup_mock.pack(side="left", padx=8)
        self._bind_btn_effect(btn_setup_mock, "#d97706", "#f59e0b")

        opt_frame = tk.Frame(panel, bg=self.card_color)
        opt_frame.pack(fill="x", pady=8)
        
        self.org_rename_var = tk.BooleanVar(value=False)
        chk_rename = tk.Checkbutton(opt_frame, text="重命名文件(在名字中追加摘要)", variable=self.org_rename_var, font=("Microsoft YaHei", 9), fg=self.text_white, bg=self.card_color, selectcolor="#0f172a", activebackground=self.card_color, activeforeground=self.text_white)
        chk_rename.pack(side="left", padx=4)

        self.org_nollm_var = tk.BooleanVar(value=True)
        chk_nollm = tk.Checkbutton(opt_frame, text="强制使用本地静态模板 (不消耗AI)", variable=self.org_nollm_var, font=("Microsoft YaHei", 9), fg=self.text_white, bg=self.card_color, selectcolor="#0f172a", activebackground=self.card_color, activeforeground=self.text_white)
        chk_nollm.pack(side="left", padx=16)

        # 操作按钮区
        action_btn_frame = tk.Frame(panel, bg=self.card_color)
        action_btn_frame.pack(fill="x", pady=8)

        btn_go = tk.Button(action_btn_frame, text="🚀 开始智能物理规格化整理", font=("Microsoft YaHei", 9, "bold"), bg=self.success_green, fg="white", relief="flat", cursor="hand2", command=lambda: self._run_organizer(plugin))
        btn_go.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._bind_btn_effect(btn_go, self.success_green, "#34d399")

        btn_dnd = tk.Button(action_btn_frame, text="🖐️ 可视化拖拽自定义重组", font=("Microsoft YaHei", 9, "bold"), bg="#a78bfa", fg="black", relief="flat", cursor="hand2", command=lambda: self._open_dnd_dialog(plugin))
        btn_dnd.pack(side="right", fill="x", expand=True, padx=(4, 0))
        self._bind_btn_effect(btn_dnd, "#a78bfa", "#c084fc")

        log_frame = tk.Frame(panel, bg=self.card_color)
        log_frame.pack(fill="both", expand=True, pady=12)
        
        tk.Label(log_frame, text="插件运行日志:", font=("Microsoft YaHei", 9), fg=self.text_gray, bg=self.card_color).pack(anchor="w")
        self.org_log_text = tk.Text(log_frame, font=("Consolas", 8), bg="#0f172a", fg=self.text_white, state="disabled", wrap="word", borderwidth=0)
        self.org_log_text.pack(fill="both", expand=True, pady=8)

        # 注入日志
        class GuiLogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.after(10, self.append_log, msg)
            def append_log(self, msg):
                try:
                    self.text_widget.configure(state="normal")
                    self.text_widget.insert("end", msg + "\n")
                    self.text_widget.see("end")
                    self.text_widget.configure(state="disabled")
                except Exception:
                    pass

        self.gui_handler = GuiLogHandler(self.org_log_text)
        self.gui_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logger.parent.addHandler(self.gui_handler)

    def _browse_org_dir(self):
        path = filedialog.askdirectory(initialdir=self.org_dir_entry.get())
        if path:
            self.org_dir_entry.delete(0, "end")
            self.org_dir_entry.insert(0, path)

    def _setup_mock_files(self):
        """在目标目录下物理写入 10 个测试混乱文件供用户查看运行对比"""
        target = self.org_dir_entry.get()
        os.makedirs(target, exist_ok=True)
        
        files_to_mock = {
            "Resume_Draft_Older   Version.docx": "个人简历求职信内容...",
            "Family  Trip  Photo.JPG": b"\x00\x00\x00\x1aIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x8f\ndatJulyTripPhoto",
            "favorite_song.MP3": "MP3音乐音频...",
            "download_no_ext": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06",
            "~$temp_office_lock.xlsx": "Office临时垃圾缓存，应该被彻底过滤清除",
            "python_quick_main.py": "def main():\n    print('Hello')\nif __name__ == '__main__':\n    main()",
            "project_pkg.zip": "压缩包内容",
            "installer.exe": "EXE可执行文件",
            "movie_to_see.txt": "1. 盗梦空间\n2. 星际穿越"
        }

        created = 0
        for name, content in files_to_mock.items():
            f_path = os.path.join(target, name)
            mode = 'wb' if isinstance(content, bytes) or name.endswith(('.png', '.jpeg')) else 'w'
            encoding = None if 'b' in mode else 'utf-8'
            try:
                with open(f_path, mode, encoding=encoding) as f:
                    f.write(content)
                created += 1
            except Exception as e:
                logger.error(f"测试文件生成失败: {e}")
        
        messagebox.showinfo("生成成功", f"已成功在目录:\n{target}\n中写入了 {created} 个用于演示的混乱测试文件！\n\n现在您可以点击“开始物理规格化整理”或“可视化拖拽自定义重组”查看物理效果！")

    def _run_organizer(self, plugin):
        target = self.org_dir_entry.get()
        if not os.path.exists(target):
            messagebox.showerror("错误", "目标整理路径不存在！")
            return
        
        rename = self.org_rename_var.get()
        no_llm = self.org_nollm_var.get()

        def run():
            self.org_log_text.configure(state="normal")
            self.org_log_text.delete("1.0", "end")
            self.org_log_text.configure(state="disabled")

            params = {
                "target_dir": target,
                "use_llm": not no_llm,
                "rename_files": rename
            }
            logger.info("================= 整理插件启动 =================")
            success, msg = plugin.execute(params)
            logger.info(f"结果: {msg}")
            logger.info("================= 整理插件结束 =================")
            if success:
                messagebox.showinfo("完成", f"物理整理结束！看板已生成在:\n{os.path.join(target, 'dashboard.html')}")

        threading.Thread(target=run, daemon=True).start()

    # ================= 可视化拖拽自定义重组模态窗 =================
    def _open_dnd_dialog(self, plugin):
        target_dir = self.org_dir_entry.get()
        if not os.path.exists(target_dir):
            messagebox.showerror("错误", "当前目标目录不存在，请先选择有效路径！")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("🖐️ 可视化拖拽自定义重组编辑器")
        dialog.geometry("960x650")
        dialog.configure(bg="#0f172a")
        dialog.grab_set()  # 模态锁定
        dialog.resizable(False, False)

        # 头部说明
        header = tk.Frame(dialog, bg="#0f172a")
        header.pack(fill="x", padx=16, pady=12)
        tk.Label(header, text="📂 可视化拖拽编排", font=("Microsoft YaHei", 12, "bold"), fg="#a78bfa", bg="#0f172a").pack(anchor="w")
        tk.Label(header, text="左侧为待整理文件（只读）；使用鼠标左键多选拖拽至右侧目标文件夹上释放。划过文件夹时目标会自动点亮高亮响应！", font=("Microsoft YaHei", 9), fg="#94a3b8", bg="#0f172a").pack(anchor="w")

        # 主工作区分割
        main_work = tk.Frame(dialog, bg="#0f172a")
        main_work.pack(fill="both", expand=True, padx=16, pady=4)

        # 样式定制 Treeview
        tree_style = ttk.Style()
        tree_style.configure("CustomTree.Treeview", background="#1e293b", foreground="#f8fafc", fieldbackground="#1e293b", rowheight=24, borderwidth=0)
        tree_style.map("CustomTree.Treeview", background=[('selected', '#4f46e5')], foreground=[('selected', '#ffffff')])

        # 1. 左侧 Frame (Source) - 原物理目录待整理文件列表
        left_frame = tk.LabelFrame(main_work, text=" 原目录待整理文件 (Source) ", font=("Microsoft YaHei", 9, "bold"), fg="#94a3b8", bg="#1e293b", padx=8, pady=8, borderwidth=1, relief="solid")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        left_scroll = ttk.Scrollbar(left_frame)
        left_scroll.pack(side="right", fill="y")

        self.src_tree = ttk.Treeview(left_frame, style="CustomTree.Treeview", columns=("type", "path"), show="tree", yscrollcommand=left_scroll.set, selectmode="extended")
        self.src_tree.pack(fill="both", expand=True)
        self.src_tree["displaycolumns"] = ()  # 隐藏后面的 path 和 type 数据列
        self.src_tree.column("#0", width=380, minwidth=250, stretch=True)
        left_scroll.config(command=self.src_tree.yview)

        # 2. 中间操作控制栏 (右树的辅助控制)
        mid_control = tk.Frame(main_work, bg="#0f172a", width=120)
        mid_control.pack(side="left", fill="y", padx=4)
        mid_control.pack_propagate(False)

        lbl_ops = tk.Label(mid_control, text="右树控制项", font=("Microsoft YaHei", 9, "bold"), fg="#94a3b8", bg="#0f172a")
        lbl_ops.pack(pady=(40, 10))

        btn_new_dir = tk.Button(mid_control, text="📁 新建文件夹", font=("Microsoft YaHei", 9), bg="#374151", fg="white", relief="flat", cursor="hand2", command=lambda: self._dnd_new_folder())
        btn_new_dir.pack(fill="x", pady=6, padx=4)
        self._bind_btn_effect(btn_new_dir, "#374151", "#4b5563")

        btn_delete_item = tk.Button(mid_control, text="🗑️ 移出/撤销", font=("Microsoft YaHei", 9), bg="#991b1b", fg="white", relief="flat", cursor="hand2", command=lambda: self._dnd_delete_item())
        btn_delete_item.pack(fill="x", pady=6, padx=4)
        self._bind_btn_effect(btn_delete_item, "#991b1b", "#b91c1c")

        # 3. 右侧 Frame (Target) - 自定义目标文件夹（初始仅推荐标准空目录）
        right_frame = tk.LabelFrame(main_work, text=" 自定义目标结构 (Target) ", font=("Microsoft YaHei", 9, "bold"), fg="#a78bfa", bg="#1e293b", padx=8, pady=8, borderwidth=1, relief="solid")
        right_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        right_scroll = ttk.Scrollbar(right_frame)
        right_scroll.pack(side="right", fill="y")

        self.dest_tree = ttk.Treeview(right_frame, style="CustomTree.Treeview", columns=("type", "path"), show="tree", yscrollcommand=right_scroll.set, selectmode="extended")
        self.dest_tree.pack(fill="both", expand=True)
        self.dest_tree["displaycolumns"] = ()  
        self.dest_tree.column("#0", width=380, minwidth=250, stretch=True)
        right_scroll.config(command=self.dest_tree.yview)

        # 状态条
        self.dnd_status = tk.Label(dialog, text="状态: 准备就绪。按住 Ctrl/Shift 选中左侧文件，按住鼠标拖入右侧对应文件夹释放。", font=("Microsoft YaHei", 9), fg="#94a3b8", bg="#0f172a", anchor="w")
        self.dnd_status.pack(fill="x", padx=16, pady=8)

        # 底部提交栏
        bottom_bar = tk.Frame(dialog, bg="#0f172a")
        bottom_bar.pack(fill="x", padx=16, pady=12)

        btn_cancel = tk.Button(bottom_bar, text=" 取消并关闭 ", font=("Microsoft YaHei", 9), bg="#4b5563", fg="white", relief="flat", cursor="hand2", command=dialog.destroy)
        btn_cancel.pack(side="left")
        self._bind_btn_effect(btn_cancel, "#4b5563", "#6b7280")

        btn_confirm = tk.Button(bottom_bar, text=" ✔ 确认应用物理布局转换 ", font=("Microsoft YaHei", 9, "bold"), bg=self.success_green, fg="white", relief="flat", cursor="hand2", command=lambda: self._dnd_confirm_apply(plugin, target_dir, dialog))
        btn_confirm.pack(side="right")
        self._bind_btn_effect(btn_confirm, self.success_green, "#34d399")

        # 填充数据 (左侧原装文件，右侧置空仅放标准盒子)
        self._populate_dnd_trees_v3(target_dir)

        # 绑定跨控件 DND (从左树拖到右树)
        self.src_tree.bind("<ButtonPress-1>", self._on_src_drag_start)
        self.src_tree.bind("<B1-Motion>", self._on_src_drag_motion)
        self.src_tree.bind("<ButtonRelease-1>", self._on_src_drag_drop)
        
        # 同时也绑定右树内部的微调拖拽 (右树内拖拽调整)
        self.dest_tree.bind("<ButtonPress-1>", self._on_dest_drag_start)
        self.dest_tree.bind("<B1-Motion>", self._on_dest_drag_motion)
        self.dest_tree.bind("<ButtonRelease-1>", self._on_dest_drag_drop)

        # 拖拽临时变量
        self.dragged_src_items = []
        self.dragged_dest_items = []
        self.is_dragging_active = False
        self.drag_label = None  # 悬浮标签对象

    def _populate_dnd_trees_v3(self, target_dir):
        self.src_tree.delete(*self.src_tree.get_children())
        self.dest_tree.delete(*self.dest_tree.get_children())

        ignore_dirs = {'.git', 'node_modules', '.agents', '__pycache__', 'test_sandbox'}
        ignore_files = {'organizer.py', 'rules.json', 'dashboard.html', '.env'}

        # 1. 右树仅生成推荐的标准“分类空盒子”
        default_categories = {
            "Documents": "📁 Documents (办公/文档)",
            "Images": "📁 Images (图片素材)",
            "Videos": "📁 Videos (视频影音)",
            "Audios": "📁 Audios (音频媒体)",
            "Archives": "📁 Archives (压缩归档)",
            "Installers": "📁 Installers (软件安装包)",
            "others": "📁 others (其他文件)"
        }
        self.dest_cat_nodes = {}
        for cat_name, cat_text in default_categories.items():
            node = self.dest_tree.insert("", "end", text=cat_text, values=("dir", ""))
            self.dest_cat_nodes[cat_name] = node

        # 2. 左树仅填充真实的文件与子结构
        def load_src(parent_node, current_path):
            try:
                for entry in os.scandir(current_path):
                    name = entry.name
                    if entry.is_dir():
                        if name in ignore_dirs:
                            continue
                        src_node = self.src_tree.insert(parent_node, "end", text=f"📁 {name}", values=("dir", entry.path))
                        load_src(src_node, entry.path)
                    elif entry.is_file():
                        if name in ignore_files or name.startswith("dashboard.html"):
                            continue
                        self.src_tree.insert(parent_node, "end", text=f"📄 {name}", values=("file", entry.path))
            except Exception as e:
                logger.error(f"加载左树失败 {current_path}: {e}")

        load_src("", target_dir)

        # 全量展开左树与右树
        def expand_all(tree, parent=""):
            for item in tree.get_children(parent):
                tree.item(item, open=True)
                expand_all(tree, item)

        expand_all(self.src_tree)
        expand_all(self.dest_tree)

    def _create_drag_label(self, root_window, text):
        """动态创建一个无边框、置顶的悬浮提示标签"""
        if self.drag_label:
            try:
                self.drag_label.destroy()
            except Exception:
                pass
        self.drag_label = tk.Toplevel(root_window)
        self.drag_label.overrideredirect(True)
        self.drag_label.attributes("-topmost", True)
        self.drag_label.configure(bg="#4f46e5")
        
        lbl = tk.Label(self.drag_label, text=text, bg="#4f46e5", fg="white", font=("Microsoft YaHei", 9, "bold"), padx=6, pady=3, borderwidth=1, relief="solid")
        lbl.pack()

    def _destroy_drag_label(self):
        """销毁悬浮标签"""
        if self.drag_label:
            try:
                self.drag_label.destroy()
            except Exception:
                pass
            self.drag_label = None

    # ================= 跨控件拖动 (左 ➔ 右) =================
    def _on_src_drag_start(self, event):
        item = self.src_tree.identify_row(event.y)
        if not item:
            return
        
        selected = list(self.src_tree.selection())
        if item not in selected:
            self.src_tree.selection_set(item)
            selected = [item]
            
        self.dragged_src_items = [node for node in selected if self.src_tree.item(node, "values")[0] == "file"]
        if self.dragged_src_items:
            self.is_dragging_active = True
            
            # 记录第一个文件的名字和数量，作为鼠标跟随文字
            first_name = self.src_tree.item(self.dragged_src_items[0], "text")[2:]
            count = len(self.dragged_src_items)
            drag_text = f" 📄 {first_name} " if count == 1 else f" 📄 {first_name} 等 {count} 个文件 "
            self._create_drag_label(self.src_tree.winfo_toplevel(), drag_text)
            self.dnd_status.config(text=f"正在拖拽 {count} 个左侧文件，移动到右侧文件夹上方松开...", fg="#a78bfa")

    def _on_src_drag_motion(self, event):
        if not self.is_dragging_active or not self.dragged_src_items:
            return
            
        self.src_tree.config(cursor="hand2")
        
        # 1. 悬浮提示框实时跟随鼠标坐标
        if self.drag_label:
            self.drag_label.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

        # 2. 跨控件坐标投影：计算鼠标是否滑过右侧树的目标文件夹并进行“点亮高亮响应”
        x_root, y_root = event.x_root, event.y_root
        dest_x = self.dest_tree.winfo_rootx()
        dest_y = self.dest_tree.winfo_rooty()
        dest_w = self.dest_tree.winfo_width()
        dest_h = self.dest_tree.winfo_height()

        if dest_x <= x_root <= dest_x + dest_w and dest_y <= y_root <= dest_y + dest_h:
            ry = y_root - dest_y
            hover_item = self.dest_tree.identify_row(ry)
            if hover_item:
                target_vals = self.dest_tree.item(hover_item, "values")
                if target_vals and target_vals[0] == "dir":
                    # 鼠标划过文件夹，立即点亮高亮选中它！
                    self.dest_tree.selection_set(hover_item)
                    self.dest_tree.focus(hover_item)

    def _on_src_drag_drop(self, event):
        self.src_tree.config(cursor="")
        self._destroy_drag_label()
        
        if not self.is_dragging_active or not self.dragged_src_items:
            self.is_dragging_active = False
            return
        
        self.is_dragging_active = False
        dragged_list = self.dragged_src_items
        self.dragged_src_items = []

        x_root, y_root = event.x_root, event.y_root
        dest_x = self.dest_tree.winfo_rootx()
        dest_y = self.dest_tree.winfo_rooty()
        dest_w = self.dest_tree.winfo_width()
        dest_h = self.dest_tree.winfo_height()

        if not (dest_x <= x_root <= dest_x + dest_w and dest_y <= y_root <= dest_y + dest_h):
            self.dnd_status.config(text="拖拽失败：请将文件松开在右侧的目标盒子内！", fg=self.fail_red)
            return

        ry = y_root - dest_y
        target_item = self.dest_tree.identify_row(ry)
        
        if not target_item:
            target_item = self.dest_cat_nodes.get("others")

        target_vals = self.dest_tree.item(target_item, "values")
        if not target_vals:
            target_item = self.dest_cat_nodes.get("others")
            target_vals = self.dest_tree.item(target_item, "values")
            
        target_type = target_vals[0]
        if target_type != "dir":
            target_item = self.dest_tree.parent(target_item) or self.dest_cat_nodes.get("others")

        success_count = 0
        target_text = self.dest_tree.item(target_item, "text")
        
        for node in dragged_list:
            node_text = self.src_tree.item(node, "text")
            node_vals = self.src_tree.item(node, "values")
            if not node_vals:
                continue
            
            file_path = node_vals[1]
            self.dest_tree.insert(target_item, "end", text=node_text, values=("file", file_path))
            self.src_tree.delete(node)
            success_count += 1

        self.dest_tree.item(target_item, open=True)
        self.dnd_status.config(text=f"成功将左侧 {success_count} 个文件归纳移动至右侧 [{target_text[2:]}] 中！", fg=self.success_green)

    # ================= 右树内部拖动重排 (右 ➔ 右) =================
    def _on_dest_drag_start(self, event):
        item = self.dest_tree.identify_row(event.y)
        if not item:
            return
        
        selected = list(self.dest_tree.selection())
        if item not in selected:
            self.dest_tree.selection_set(item)
            selected = [item]
            
        self.dragged_dest_items = [node for node in selected if self.dest_tree.item(node, "values")[0] == "file"]
        if self.dragged_dest_items:
            # 创建悬浮框
            first_name = self.dest_tree.item(self.dragged_dest_items[0], "text")[2:]
            count = len(self.dragged_dest_items)
            drag_text = f" 📄 {first_name} " if count == 1 else f" 📄 {first_name} 等 {count} 个文件 "
            self._create_drag_label(self.dest_tree.winfo_toplevel(), drag_text)
            self.dnd_status.config(text=f"右树内部重编排：正在移动 {count} 个文件...", fg="#818cf8")

    def _on_dest_drag_motion(self, event):
        if not self.dragged_dest_items:
            return
            
        self.dest_tree.config(cursor="hand2")
        
        if self.drag_label:
            self.drag_label.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

        # 悬停高亮当前路过的目标文件夹
        item = self.dest_tree.identify_row(event.y)
        if item:
            vals = self.dest_tree.item(item, "values")
            if vals and vals[0] == "dir":
                self.dest_tree.selection_set(item)
                self.dest_tree.focus(item)

    def _on_dest_drag_drop(self, event):
        self.dest_tree.config(cursor="")
        self._destroy_drag_label()
        
        if not self.dragged_dest_items:
            return
        
        target = self.dest_tree.identify_row(event.y)
        dragged_list = self.dragged_dest_items
        self.dragged_dest_items = []

        if not target:
            return

        target_vals = self.dest_tree.item(target, "values")
        if not target_vals:
            return

        target_type = target_vals[0]
        final_parent = target if target_type == "dir" else self.dest_tree.parent(target)
        if not final_parent:
            return

        moved = 0
        for item in dragged_list:
            if item == final_parent or self.dest_tree.parent(item) == final_parent:
                continue
            self.dest_tree.move(item, final_parent, "end")
            moved += 1
            
        self.dnd_status.config(text=f"右树微调成功：已将 {moved} 个文件移至目标目录下", fg=self.success_green)

    def _dnd_new_folder(self):
        selected = self.dest_tree.selection()
        parent = ""
        if selected:
            vals = self.dest_tree.item(selected[0], "values")
            if vals and vals[0] == "dir":
                parent = selected[0]

        dialog_input = tk.Toplevel(self.root)
        dialog_input.title("新建文件夹")
        dialog_input.geometry("300x120")
        dialog_input.configure(bg="#1e293b")
        dialog_input.resizable(False, False)
        dialog_input.grab_set()

        tk.Label(dialog_input, text="输入文件夹名称:", font=("Microsoft YaHei", 9), fg=self.text_white, bg="#1e293b").pack(pady=10)
        entry = tk.Entry(dialog_input, font=("Microsoft YaHei", 9), bg="#0f172a", fg="white", borderwidth=1, relief="solid")
        entry.pack(fill="x", padx=20, pady=4)
        entry.insert(0, "Custom_Group")

        def submit():
            name = entry.get().strip()
            if not name:
                messagebox.showerror("错误", "文件夹名称不能为空！")
                return
            self.dest_tree.insert(parent, "end", text=f"📁 {name}", values=("dir", ""))
            self.dest_tree.item(parent, open=True) if parent else None
            dialog_input.destroy()

        tk.Button(dialog_input, text="确定", font=("Microsoft YaHei", 9, "bold"), bg=self.success_green, fg="white", relief="flat", command=submit).pack(pady=10)

    def _dnd_delete_item(self):
        selected = list(self.dest_tree.selection())
        if not selected:
            messagebox.showwarning("警告", "请先在右树选中要删除/撤销的文件节点！")
            return
        
        confirm = messagebox.askyesno("撤销重组确认", f"确定要撤销右树中选中的 {len(selected)} 个文件节点吗？\n（物理文件不受影响，文件将自动退回到左树待整理区）")
        if confirm:
            restored = 0
            for item in selected:
                node_text = self.dest_tree.item(item, "text")
                node_vals = self.dest_tree.item(item, "values")
                
                # 只有文件节点允许退回左树
                if node_vals and node_vals[0] == "file":
                    file_path = node_vals[1]
                    self.src_tree.insert("", "end", text=node_text, values=("file", file_path))
                    restored += 1
                
                self.dest_tree.delete(item)
                
            self.dnd_status.config(text=f"已在重排结构中移除指定节点，其中 {restored} 个文件已退回到左树待整理区", fg=self.fail_red)

    def _dnd_confirm_apply(self, plugin, target_dir, dialog):
        mapping = {}
        
        def traverse_node(node_id, current_rel_dir):
            node_text = self.dest_tree.item(node_id, "text")
            node_vals = self.dest_tree.item(node_id, "values")
            if not node_vals:
                return

            node_type = node_vals[0]
            clean_name = node_text[2:] if len(node_text) > 2 else node_text

            if node_type == "file":
                src_path = node_vals[1]
                dest_path = os.path.join(target_dir, current_rel_dir, clean_name)
                mapping[src_path] = dest_path
            elif node_type == "dir":
                new_rel = os.path.join(current_rel_dir, clean_name)
                for child in self.dest_tree.get_children(node_id):
                    traverse_node(child, new_rel)

        for root_child in self.dest_tree.get_children(""):
            traverse_node(root_child, "")

        if not mapping:
            messagebox.showwarning("警告", "自定义结构中不包含任何可搬移的文件节点！")
            return

        confirm = messagebox.askyesno("物理转换确认", f"确定要执行物理布局转换吗？\n本次将搬运挪动 {len(mapping)} 个文件，原空目录将自动回收清理。")
        if not confirm:
            return

        def run():
            self.dnd_status.config(text="正在开始物理重组磁盘文件并回收空目录...", fg="#a78bfa")
            params = {
                "target_dir": target_dir,
                "custom_mapping": mapping
            }
            logger.info("================= 自定义重排插件启动 =================")
            success, msg = plugin.execute(params)
            logger.info(f"结果: {msg}")
            logger.info("================= 自定义重排插件结束 =================")

            if success:
                messagebox.showinfo("重组完成", f"自定义布局转换成功！\n{msg}")
                dialog.destroy()
            else:
                messagebox.showerror("重组失败", f"物理搬移过程中出现报错: {msg}")

        threading.Thread(target=run, daemon=True).start()

    # ================= 2. Everything C盘急救面板 =================
    def _render_everything_panel(self, plugin):
        panel = tk.Frame(self.detail_area, bg=self.card_color)
        panel.pack(fill="both", expand=True)

        cfg_frame = tk.Frame(panel, bg=self.card_color)
        cfg_frame.pack(fill="x", pady=8)
        
        tk.Label(cfg_frame, text="Everything HTTP端口:", font=("Microsoft YaHei", 9), fg=self.text_white, bg=self.card_color).pack(side="left")
        self.ev_port_entry = tk.Entry(cfg_frame, font=("Microsoft YaHei", 9), width=8, bg="#0f172a", fg=self.text_white, borderwidth=1, relief="solid")
        self.ev_port_entry.pack(side="left", padx=8)
        self.ev_port_entry.insert(0, "80")

        scan_frame = tk.Frame(panel, bg=self.card_color)
        scan_frame.pack(fill="x", pady=8)

        btn_scan_big = tk.Button(scan_frame, text="🔍 扫描C盘冗余大文件 (>100MB)", font=("Microsoft YaHei", 9), bg=self.accent_blue, fg="white", relief="flat", cursor="hand2", command=lambda: self._scan_ev(plugin, "scan_big"))
        btn_scan_big.pack(side="left", fill="x", expand=True, padx=4)
        self._bind_btn_effect(btn_scan_big, self.accent_blue, "#6366f1")

        btn_scan_garbage = tk.Button(scan_frame, text="🧹 扫描全盘系统缓存垃圾", font=("Microsoft YaHei", 9), bg=self.accent_blue, fg="white", relief="flat", cursor="hand2", command=lambda: self._scan_ev(plugin, "scan_garbage"))
        btn_scan_garbage.pack(side="right", fill="x", expand=True, padx=4)
        self._bind_btn_effect(btn_scan_garbage, self.accent_blue, "#6366f1")

        # 转移搬运动作栏 (先 pack，防止被大框截断)
        action_frame = tk.Frame(panel, bg=self.card_color)
        action_frame.pack(fill="x", pady=8)

        tk.Label(action_frame, text="大容量转移地:", font=("Microsoft YaHei", 9), fg=self.text_white, bg=self.card_color).pack(side="left")
        self.ev_dest_entry = tk.Entry(action_frame, font=("Microsoft YaHei", 9), bg="#0f172a", fg=self.text_white, borderwidth=1, relief="solid")
        self.ev_dest_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.ev_dest_entry.insert(0, "D:\\C_Drive_BigFiles")

        btn_move = tk.Button(action_frame, text="🚀 一键转移至D盘", font=("Microsoft YaHei", 9, "bold"), bg=self.success_green, fg="white", relief="flat", cursor="hand2", command=lambda: self._move_ev_files(plugin))
        btn_move.pack(side="right", padx=4)
        self._bind_btn_effect(btn_move, self.success_green, "#34d399")

        btn_clean = tk.Button(action_frame, text="🗑️ 清理垃圾", font=("Microsoft YaHei", 9, "bold"), bg=self.fail_red, fg="white", relief="flat", cursor="hand2", command=lambda: self._clean_ev_files(plugin))
        btn_clean.pack(side="right", padx=8)
        self._bind_btn_effect(btn_clean, self.fail_red, "#f87171")

        res_frame = tk.Frame(panel, bg=self.card_color)
        res_frame.pack(fill="both", expand=True, pady=8)
        
        tk.Label(res_frame, text="扫描结果文件清单:", font=("Microsoft YaHei", 9), fg=self.text_gray, bg=self.card_color).pack(anchor="w")
        self.ev_list_text = tk.Text(res_frame, font=("Consolas", 8), bg="#0f172a", fg=self.text_white, wrap="none", borderwidth=0)
        self.ev_list_text.pack(fill="both", expand=True, pady=8)

        self.ev_scanned_results = []
        self.ev_scan_type = None

    def _scan_ev(self, plugin, action):
        port = self.ev_port_entry.get()
        
        def run():
            self.ev_list_text.configure(state="normal")
            self.ev_list_text.delete("1.0", "end")
            self.ev_list_text.insert("end", "正在联动 Everything 秒级扫描全盘，请稍候...\n")
            self.ev_list_text.configure(state="disabled")

            success, res_str = plugin.execute({"action": action, "port": port})
            
            self.ev_list_text.configure(state="normal")
            self.ev_list_text.delete("1.0", "end")
            
            if not success:
                self.ev_list_text.insert("end", f"扫描失败：{res_str}\n")
                self.ev_list_text.configure(state="disabled")
                return

            results = json.loads(res_str)
            self.ev_scanned_results = results
            self.ev_scan_type = action

            if not results:
                self.ev_list_text.insert("end", "未扫描到符合条件的数据。\n")
            else:
                for item in results:
                    size_mb = item['size'] / (1024 * 1024)
                    if size_mb > 0:
                        self.ev_list_text.insert("end", f"[{size_mb:.1f} MB] {item['path']}\n")
                    else:
                        self.ev_list_text.insert("end", f"[缓存垃圾] {item['path']}\n")
            self.ev_list_text.configure(state="disabled")

        threading.Thread(target=run, daemon=True).start()

    def _move_ev_files(self, plugin):
        if not self.ev_scanned_results or self.ev_scan_type != "scan_big":
            messagebox.showwarning("警告", "请先扫描C盘冗余大文件后再搬家！")
            return
        dest = self.ev_dest_entry.get()
        if not dest:
            messagebox.showerror("错误", "大容量目的地路径不能为空！")
            return
        
        def run():
            self.ev_list_text.configure(state="normal")
            self.ev_list_text.insert("end", "\n-------------- 开始规格搬运大文件 --------------\n")
            self.ev_list_text.configure(state="disabled")

            params = {
                "action": "move_files",
                "port": self.ev_port_entry.get(),
                "files": self.ev_scanned_results,
                "dest": dest
            }
            success, msg = plugin.execute(params)
            
            self.ev_list_text.configure(state="normal")
            self.ev_list_text.insert("end", f"{msg}\n")
            self.ev_list_text.configure(state="disabled")
            messagebox.showinfo("搬运结束", msg)
            self.ev_scanned_results = []

        threading.Thread(target=run, daemon=True).start()

    def _clean_ev_files(self, plugin):
        if not self.ev_scanned_results or self.ev_scan_type != "scan_garbage":
            messagebox.showwarning("警告", "请先扫描垃圾缓存后再清理！")
            return
        
        confirm = messagebox.askyesno("清理确认", "确定要物理删除扫描出的垃圾文件吗？")
        if not confirm:
            return

        def run():
            self.ev_list_text.configure(state="normal")
            self.ev_list_text.insert("end", "\n-------------- 开始物理粉碎垃圾缓存 --------------\n")
            self.ev_list_text.configure(state="disabled")

            params = {
                "action": "clean_files",
                "port": self.ev_port_entry.get(),
                "files": self.ev_scanned_results
            }
            success, msg = plugin.execute(params)
            
            self.ev_list_text.configure(state="normal")
            self.ev_list_text.insert("end", f"{msg}\n")
            self.ev_list_text.configure(state="disabled")
            messagebox.showinfo("清理完毕", msg)
            self.ev_scanned_results = []

        threading.Thread(target=run, daemon=True).start()
