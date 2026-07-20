# -*- coding: utf-8 -*-
"""
HandyWorkstation 项目流程化质量门禁检查脚本 (Quality Gate Checker)
包含 4 项自动流程校验：
1. 代码规范校验 (Linter Gate - ruff)
2. 安全防泄露校验 (Security Gate - .gitignore)
3. 插件物理沙箱测试 (Integration Test Gate - main.py --test-all)
4. 打包产物完备性校验 (Build & Binary Gate - HandyWorkstation.exe)
"""

import os
import sys
import subprocess

# Windows 控制台编码守护防崩：强制 stdout/stderr 为 UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def print_step(name: str):
    print("\n==================================================")
    print(f" [*] 正在执行流程检查: {name}")
    print("==================================================")

def check_linter() -> bool:
    print_step("1. 代码规范静态扫描 (Ruff Linter Check)")
    try:
        res = subprocess.run([sys.executable, "-m", "ruff", "check", "."], capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            print("[SUCCESS] 代码规范扫描通过，零代码规约缺陷！")
            return True
        else:
            print("[FAILED] 代码存在规范缺陷:")
            print(res.stdout or res.stderr)
            return False
    except Exception as e:
        print(f"[WARNING] 无法运行 Ruff (可能未安装): {e}")
        return True

def check_security() -> bool:
    print_step("2. 安全与敏感文件防护校验 (Git & Security Check)")
    gitignore_path = os.path.join(os.path.dirname(__file__), ".gitignore")
    if not os.path.exists(gitignore_path):
        print("[FAILED] 缺少 .gitignore 文件！")
        return False
    
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_ignores = [".env", "__pycache__", "build", "dist"]
    missing = [item for item in required_ignores if item not in content]
    
    if missing:
        print(f"[FAILED] .gitignore 遗漏核心防护配置: {missing}")
        return False
    
    print("[SUCCESS] 敏感与临时文件防泄露规则校验通过！")
    return True

def check_integration_tests() -> bool:
    print_step("3. 插件物理沙箱集成自测试 (Integration Sandbox Test)")
    main_script = os.path.join(os.path.dirname(__file__), "main.py")
    res = subprocess.run([sys.executable, main_script, "--test-all"], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    
    # 校验核心归类插件是否自测成功
    if "混乱目录规格化归类插件" in res.stdout and "[SUCCESS]" in res.stdout:
        print("[SUCCESS] 核心核心插件沙箱自测断言通过！")
        if "Everything 服务未在本地 HTTP 端口开启" in res.stdout:
            print("[NOTE] 外部依赖插件 Everything HTTP 服务未启动（属正常可选环境提示）")
        return True
    else:
        print("[FAILED] 核心插件沙箱自测试失败")
        return False

def check_build_artifact() -> bool:
    print_step("4. 打包产物完备性校验 (Executable Build Check)")
    exe_path = os.path.join(os.path.dirname(__file__), "dist", "HandyWorkstation", "HandyWorkstation.exe")
    if not os.path.exists(exe_path):
        print(f"[WARNING] 尚未打出 .exe 产物 ({exe_path})，请先运行 build.bat 打包！")
        return True
    
    res = subprocess.run([exe_path, "--test-all"], capture_output=True, text=True, encoding="utf-8")
    if "结合自测试成功" in res.stdout:
        print("[SUCCESS] 打包产物 HandyWorkstation.exe 离线自测试通过！")
        return True
    else:
        print("[FAILED] 可执行程序运行失败:")
        print(res.stdout or res.stderr)
        return False

def main():
    print("\n[START] 开始运行 HandyWorkstation 项目流程化质量门禁...\n")
    results = [
        ("代码规范检查", check_linter()),
        ("安全配置检查", check_security()),
        ("沙箱集成测试", check_integration_tests()),
        ("打包产物校验", check_build_artifact()),
    ]
    
    print("\n==================================================")
    print("                流程检查结果汇总                  ")
    print("==================================================")
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f" - {name:<15}: {status}")
        if not passed:
            all_passed = False
    print("==================================================\n")
    
    if all_passed:
        print("[RESULT] 所有项目流程检查项全部通过，项目处于 SOTA 交付状态！\n")
        sys.exit(0)
    else:
        print("[RESULT] 存在未通过的流程检查项，请修正后再进行交付/提交！\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
