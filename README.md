# 🔌 本地实用工具与集成插件管理平台 (Local Utility Hub)

一个为 **电脑普通新手与系统维护需求** 设计的轻量级、模块化本地实用工具与集成插件管理控制台。通过本平台，您可以管理多种系统维护与文件归档插件，并一键运行沙箱结合性测试。

---

## 🌟 平台架构设计

本平台打破了单脚本的脆弱设计，采用高内聚、低耦合的 **微插件架构**：

1. **核心逻辑层 (`app/core/`)**：
   - **`base_plugin.py`**：定义所有插件的接口契约（ID、名称、描述、环境可用性检测 `is_available`、沙箱结合测试 `run_test` 与核心执行 `execute`）。
   - **`plugin_manager.py`**：管理插件的注册、生命周期调用，并为每次结合测试物理分配独立的、防止相互污染的测试沙箱。
2. **插件层 (`app/plugins/`)**：
   - **`organizer_plugin.py` (目录整理插件)**：本地自完备规格整理引擎，清除文件名排版顽疾、补充无后缀类型并生成 HTML 交互看板。
   - **`everything_plugin.py` (C盘空间救急插件)**：联动本地 Everything 服务，在 10 毫秒内检索大文件或缓存垃圾，一键物理搬运或粉碎。
3. **隔离测试沙箱 (`test_sandbox/`)**：
   - 专为测试插件而设立的沙箱空间。每个插件的结合测试（`run_test`）都在各自独立的子文件夹（如 `test_sandbox/organizer/`）中进行，保障自测数据不泄露、不污染用户盘符。
4. **图形控制台 (`app/gui/`)**：
   - **`main_window.py`**：基于 Tkinter 构建的现代化两栏式控制面板。左侧管理插件状态与**结合测试验证灯**（未测试灰/通过绿/异常红）；右侧动态渲染选中插件的控制面板与执行日志。

---

## 📅 项目目录结构

```text
for/
├── app/                        # 平台主程序包
│   ├── core/                   # 核心服务层
│   │   ├── base_plugin.py      # 插件契约基类
│   │   └── plugin_manager.py   # 插件管理器及沙箱隔离驱动
│   ├── plugins/                # 工具插件库
│   │   ├── organizer_plugin.py # 文件规格化整理插件
│   │   └── everything_plugin.py# Everything C盘急救箱插件
│   └── gui/                    # 统一控制台界面
│       └── main_window.py      # 插件平台主界面
├── test_sandbox/               # 物理隔离测试沙箱 (自动生成)
├── main.py                     # 平台唯一控制与执行入口
├── rules.json                  # 文件规格化整理规则库
├── run.bat                     # Windows 一键平台启动与测试脚本
└── README.md                   # 平台架构及开发说明文档
```

---

## 🚀 启动与使用指南

### 1. 双击快捷运行 (推荐)
- **快捷管理控制台**: 双击运行 [run.bat](file:///e:/tools/selfDefinetion/HandyWorkstation/run.bat) 进行启动、自测或搭建演示沙箱。
- **流程门禁质量校验**: 双击运行 [check.bat](file:///e:/tools/selfDefinetion/HandyWorkstation/check.bat) 自动完成静态代码校验、防泄露检查、沙箱断言自测及 `.exe` 产物功能测试。

### 2. 命令行控制指令
- **运行图形控制台**：
  ```powershell
  python main.py
  ```
- **一键静默自测试 (用于工程回归校验)**：
  ```powershell
  python main.py --test-all
  ```
  该命令将自动在 `test_sandbox` 下对所有已注册插件运行断言，并返回执行结果。

---

## 📦 项目一键打包 (Executable Packaging)

本平台支持通过 **PyInstaller** 一键打包为免 Python 环境的独立 Windows 可执行文件 (`.exe`)。

### 使用方法
1. 双击运行 [build.bat](file:///e:/tools/selfDefinetion/HandyWorkstation/build.bat)。
2. 脚本将自动检测环境、安装 `pyinstaller`、编译生成独立运行包。
3. 打包产物位于：`dist/HandyWorkstation/HandyWorkstation.exe`。
4. 将 `dist/HandyWorkstation` 目录分发或直接双击运行 `.exe` 即可。

---

## 💡 开发一个新插件 (Plugin Developer Guide)

如果您想为本平台添加一个全新的功能小工具，极其简单：

1. **新建文件**：在 `app/plugins/` 文件夹下新建一个 Python 模块（例如 `dup_finder_plugin.py`）。
2. **继承基类**：定义一个继承自 `BasePlugin` 的类并实现必要接口：
   ```python
   from app.core.base_plugin import BasePlugin
   
   class DuplicateFinderPlugin(BasePlugin):
       @property
       def id(self) -> str: return "dup_finder"
       
       @property
       def name(self) -> str: return "🔍 重复文件定位插件"
       
       @property
       def description(self) -> str: return "扫描并列出重复的冗余文件"

       def run_test(self, sandbox_dir: str) -> Tuple[bool, str]:
           # 1. 在 sandbox_dir 里放测试文件
           # 2. 调用 execute 校验结果
           # 3. 断言返回 (True, "说明") 或 (False, "异常")
           return True, "测试通过"
           
       def execute(self, params: Dict[str, Any]) -> Tuple[bool, str]:
           # 核心业务逻辑
           return True, "执行成功"
   ```
3. **注册插件**：在 [main.py](file:///E:/tools/selfDefinetion/for/main.py) 的 `main()` 函数中加入一行注册代码：
   ```python
   pm.register_plugin(DuplicateFinderPlugin())
   ```
平台将**自动检测**新插件、在左侧列表加载它、并在右侧渲染其测试状态！
