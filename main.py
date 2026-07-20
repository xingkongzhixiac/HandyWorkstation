# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging

# Windows 控制台编码守护防崩：强制 stdout/stderr 为 UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.core.plugin_manager import PluginManager
from app.plugins.organizer_plugin import OrganizerPlugin
from app.plugins.everything_plugin import EverythingPlugin

# 开启基础日志，指定 stream 用重置后的 sys.stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("organizer.main")

def main():
    parser = argparse.ArgumentParser(description="本地实用工具与集成插件管理平台")
    parser.add_argument("--test-all", action="store_true", help="对所有注册插件运行结合性自测试并输出校验报告")
    parser.add_argument("--setup-test", action="store_true", help="在当前目录下初始化一个用于演示的混乱测试目录(test_messy_dir)")
    args = parser.parse_args()

    # 确定沙箱路径在当前项目目录下
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sandbox_root = os.path.join(current_dir, "test_sandbox")
    
    # 实例化插件管理器并分配沙箱目录
    pm = PluginManager(sandbox_root=sandbox_root)
    
    # 注册默认可用的功能插件
    pm.register_plugin(OrganizerPlugin())
    pm.register_plugin(EverythingPlugin(port=80))

    if args.setup_test:
        from app.plugins.organizer_plugin import setup_test_environment
        setup_test_environment(current_dir)
        sys.exit(0)

    if args.test_all:
        print("\n================= 开始执行所有插件的结合性测试 =================")
        success_all = True
        for plugin in pm.get_plugins():
            print(f"[*] 正在为插件 [{plugin.name}] 物理分配独立沙箱并运行集成测试...")
            passed, detail = pm.run_plugin_test(plugin.id)
            status = "SUCCESS" if passed else "FAILED"
            print(f"[{status}] {detail}\n")
            if not passed:
                success_all = False
        print("================================================================\n")
        sys.exit(0 if success_all else 1)

    # 默认：唤起图形化控制中心
    import tkinter as tk
    from app.gui.main_window import MainWindow

    root = tk.Tk()
    MainWindow(root, pm)
    root.mainloop()

if __name__ == "__main__":
    main()
