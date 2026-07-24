# 全局交付规范与开发制约 (Global Delivery Constraints)

为了保障智能体开发的工程规范，在执行任何项目开发时必须强制遵守以下制约：

## 1. 交付完整性 (Definition of Done)
- **文档齐备**：任何新项目、工具或脚本在交付给用户前，**必须无条件附带** `README.md` 说明文档。文档中必须包含：
  - 项目核心特性与设计架构。
  - 配置指南与外部依赖说明。
  - 多入口启动/运行方法（如命令行、图形化 GUI、快捷批处理）。
- **零依赖降级**：工具类脚本设计时应尽量遵循零安装依赖原则（使用 Python 内置标准库如 `urllib`, `tkinter` 等），保障极简部署。

## 2. 代码质量制约 (Quality Gate)
- **规范校验**：交付前必须对核心代码运行一次 `ruff check` 等规范工具的静态扫描，保障零代码规约缺陷。

## 3. 经验进化自启动 (Silent Retrospective)
- **静默提炼**：任务通过或用户纠错后，智能体必须**自动、静默地**将经验并入 `global-learnings.md` 错题本中，严禁以对话形式阻塞用户确认。

## 4. 工程师思维默认自启与行规机制 (Developer Mindset & Standardized Skills)
- **全局行规自启**：凡涉及代码修改、重构、Bug 调试或新功能开发，智能体**必须默认无条件调用并严格执行**以下全局 SOTA 行业规约：
  - **`junior-to-senior` (高级架构师对抗审查)**：强制对所有设计和代码做资深 review，禁用 blanket Exception、防御性捕获具体 IO 异常，保证代码健壮。
  - **`agentic-tdd-orchestrator` (TDD 测试门禁)**：强制执行测试先行，用 Assert 断言守门，禁止无断言空跑。
  - **`writing-clearly-and-concisely` (精炼写作)**：确保文档与日志精简无 AI 废话。
- **禁绝项目级自造**：严禁在项目级自创、重写任何与上述全局行规同类的技能模块。仅允许维护项目特色插件业务级扩展。

## 5. 多平台技能共享排查制约 (Shared-Skills Standard Operating Procedure)
- **全局工具优先检测**：排查或检索 Agent 跨平台/跨 CLI (WSL/IDE/终端) 技能与配置共享时，**必须首先运行全局工具检查**（如 `npm list -g --depth=0` 识别 `shareskills`）。
- **单源链接架构**：所有跨 Agent 技能共享统一通过 `shareskills` 的 Central Hub 及符号链接 (Symlink/Junction) 进行管理，禁止直接硬编码或私自在包缓存中分裂衍生。

