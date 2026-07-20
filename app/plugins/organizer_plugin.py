# -*- coding: utf-8 -*-

import os
import shutil
import fnmatch
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Any, Optional
from app.core.base_plugin import BasePlugin

logger = logging.getLogger("organizer.plugin.organizer")

# ================= 插件独立规则、分析与整理工具类 =================

class LocalConfigManager:
    """管理分类规则与配置项"""
    DEFAULT_RULES = {
        "active_profile": "general",
        "profiles": {
            "general": [
                {
                    "name": "Documents",
                    "patterns": ["*.pdf", "*.docx", "*.doc", "*.xlsx", "*.xls", "*.pptx", "*.ppt", "*.csv", "*.txt", "*.md", "*.epub"],
                    "description": "办公文档、学习资料与电子书",
                    "suffix_templates": {
                        ".pdf": "PDF 电子文档/书籍",
                        ".docx": "Word 办公文书/草稿",
                        ".doc": "旧版 Word 文档",
                        ".xlsx": "Excel 数据分析报表/电子表格",
                        ".xls": "旧版 Excel 数据表",
                        ".pptx": "PPT 演示汇报幻灯片",
                        ".ppt": "旧版 PPT 幻灯片",
                        ".csv": "CSV 逗号分隔数据表",
                        ".txt": "TXT 简易文本文档",
                        ".md": "Markdown 标记文档说明",
                        ".epub": "EPUB 移动端电子书"
                    }
                },
                {
                    "name": "Images",
                    "patterns": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg", "*.raw", "*.psd", "*.ai"],
                    "description": "个人照片、设计稿与图档资产",
                    "suffix_templates": {
                        ".png": "PNG 静态图片素材",
                        ".jpg": "JPG 照片/图档文件",
                        ".jpeg": "JPEG 静态图档",
                        ".gif": "GIF 动态图片资产",
                        ".webp": "WEBP 高压缩网络图片",
                        ".svg": "SVG 矢量图形素材",
                        ".psd": "Photoshop 设计源文件",
                        ".ai": "Illustrator 矢量设计源文件",
                        ".raw": "RAW 相机原始无损照片"
                    }
                },
                {
                    "name": "Videos",
                    "patterns": ["*.mp4", "*.mkv", "*.mov", "*.avi", "*.wmv", "*.flv"],
                    "description": "视频录像、影视娱乐与教程资源",
                    "suffix_templates": {
                        ".mp4": "MP4 通用视频录像",
                        ".mkv": "MKV 高清多媒体视频",
                        ".mov": "MOV 苹果设备录像视频",
                        ".avi": "AVI 经典音视频媒体",
                        ".wmv": "WMV 微软视窗流视频",
                        ".flv": "FLV Flash 流媒体视频"
                    }
                },
                {
                    "name": "Audios",
                    "patterns": ["*.mp3", "*.wav", "*.flac", "*.aac", "*.m4a", "*.wma"],
                    "description": "音乐、有声书与录音文件",
                    "suffix_templates": {
                        ".mp3": "MP3 压缩音频音乐",
                        ".wav": "WAV 无损录音音频",
                        ".flac": "FLAC 高保真无损音乐",
                        ".aac": "AAC 高压缩音频素材",
                        ".m4a": "M4A 苹果设备音频/录音",
                        ".wma": "WMA 微软音频媒体"
                    }
                },
                {
                    "name": "Archives",
                    "patterns": ["*.zip", "*.rar", "*.7z", "*.tar", "*.gz", "*.tgz"],
                    "description": "压缩归档、数据备份与打包文件",
                    "suffix_templates": {
                        ".zip": "ZIP 标准数据压缩包",
                        ".rar": "RAR 专有压缩归档",
                        ".7z": "7Z 高压缩比备份包",
                        ".tar": "TAR Linux打包归档",
                        ".gz": "GZ 压缩包",
                        ".tgz": "TGZ Linux系统归档包"
                    }
                },
                {
                    "name": "Installers",
                    "patterns": ["*.exe", "*.msi", "*.apk", "*.dmg", "*.pkg", "*.bat", "*.cmd"],
                    "description": "软件安装程序与可执行脚本",
                    "suffix_templates": {
                        ".exe": "Windows 软件/可执行程序",
                        ".msi": "Windows 安装引导包",
                        ".apk": "Android 安卓应用安装包",
                        ".dmg": "macOS 磁盘镜像文件",
                        ".pkg": "macOS 软件安装包",
                        ".bat": "Windows 批处理自动脚本",
                        ".cmd": "Windows 命令行自动脚本"
                    }
                }
            ]
        },
        "default_folder": "others",
        "constraints": {
            "auto_lowercase_extension": True,
            "clean_filename_whitespace": True,
            "max_filename_length": 60,
            "filter_garbage_temp": True,
            "guess_missing_extensions": True
        }
    }

    @classmethod
    def load_rules(cls, rules_path: Optional[str]) -> Dict[str, Any]:
        if not rules_path or not os.path.exists(rules_path):
            return cls.DEFAULT_RULES
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return cls.DEFAULT_RULES


class LocalFileAnalyzer:
    """启发式分析文件，支持大模型和本地静态正则降级"""
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm

    @staticmethod
    def is_binary(file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\x00' in chunk:
                    return True
                return False
        except Exception:
            return True

    def _extract_first_meaningful_line(self, ext: str, content: str) -> Optional[str]:
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if not lines:
            return None
        if ext == '.md':
            for line in lines[:5]:
                if line.startswith('#'):
                    title = line.lstrip('# \t').strip()
                    if title and len(title) < 20:
                        return title
            return None
        if ext == '.txt' and len(lines[0]) < 20:
            return lines[0]
        for line in lines[:5]:
            if line.startswith(('#', '//', '/*', '*')):
                clean = line.lstrip('#/* \t\'"')
                if clean.strip() and len(clean) < 20:
                    return clean.strip()
        return None

    def analyze(self, file_path: str, suffix_templates: Optional[Dict[str, str]] = None) -> str:
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        is_bin = self.is_binary(file_path)
        content = ""
        if not is_bin:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2048)
            except Exception:
                pass

        if suffix_templates and ext in suffix_templates:
            base_template = suffix_templates[ext]
            if content.strip():
                first_info = self._extract_first_meaningful_line(ext, content)
                if first_info:
                    combined = f"{first_info} ({base_template})"
                    if len(combined) <= 30:
                        return combined
            return base_template

        if is_bin:
            if ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
                return "静态图片资源"
            elif ext in ['.mp3', '.wav', '.ogg']:
                return "音频媒体资源"
            elif ext in ['.mp4', '.mov', '.webm', '.avi']:
                return "视频媒体文件"
            elif ext in ['.pdf']:
                return "PDF 电子文档"
            elif ext in ['.zip', '.rar', '.tar', '.gz', '.7z']:
                return "压缩归档包"
            elif ext in ['.exe', '.dll', '.so', '.dylib']:
                return "可执行程序或库"
            return f"二进制文件 ({ext[1:].upper()})"

        if ext == '.md':
            return "Markdown 文档"
        return f"{ext[1:].upper()} 配置文件/源文件"


class LocalOrganizerEngine:
    """物理分类执行引擎"""
    def __init__(self, target_dir: str, rules_path: Optional[str] = None, use_llm: bool = False, rename_files: bool = False):
        self.target_dir = os.path.abspath(target_dir)
        self.config = LocalConfigManager.load_rules(rules_path)
        self.analyzer = LocalFileAnalyzer(use_llm=use_llm)
        self.rename_files = rename_files
        self.report_data: List[Dict[str, Any]] = []

        self.active_profile = self.config.get("active_profile", "general")
        if "profiles" in self.config:
            self.rules = self.config["profiles"].get(self.active_profile, [])
        else:
            self.rules = self.config.get("rules", [])
        
        self.constraints = self.config.get("constraints", {})

        self.suffix_templates = {}
        for rule in self.rules:
            if "suffix_templates" in rule:
                self.suffix_templates.update(rule["suffix_templates"])

    def _match_rule(self, filename: str) -> str:
        for rule in self.rules:
            patterns = rule.get("patterns", [])
            for pattern in patterns:
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    return rule["name"]
        return self.config.get("default_folder", "others")

    def _apply_constraints(self, file_path: str) -> Tuple[Optional[str], str]:
        filename = os.path.basename(file_path)
        base, ext = os.path.splitext(filename)
        
        if self.constraints.get("filter_garbage_temp", True):
            garbage_patterns = ["~$*", "*.tmp", ".ds_store", "thumbs.db", "desktop.ini"]
            for pattern in garbage_patterns:
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                    return None, ""

        if not ext and self.constraints.get("guess_missing_extensions", True) and os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(16)
                    if header.startswith(b'%PDF'):
                        ext = '.pdf'
                    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                        ext = '.png'
                    elif header.startswith(b'\xff\xd8\xff'):
                        ext = '.jpg'
                    elif header.startswith(b'ID3') or header.startswith(b'\xff\xfb'):
                        ext = '.mp3'
                    elif header.startswith(b'PK\x03\x04'):
                        ext = '.zip'
            except Exception:
                pass

        if self.constraints.get("auto_lowercase_extension", True):
            ext = ext.lower()

        if self.constraints.get("clean_filename_whitespace", True):
            import re
            base = re.sub(r'[\s_\-\+]+', '_', base).strip('_')

        max_len = self.constraints.get("max_filename_length", 60)
        if len(base) > max_len:
            base = base[:max_len]

        return file_path, f"{base}{ext}"

    def _sanitize_filename(self, filename: str, summary: str) -> str:
        base, ext = os.path.splitext(filename)
        safe_summary = "".join(c for c in summary if c not in r'\/:*?"<>|[] ,.')
        if not safe_summary:
            return filename
        return f"{base} [{safe_summary}]{ext}"

    def execute_整理(self) -> Tuple[bool, str]:
        if not os.path.exists(self.target_dir):
            return False, "目标目录不存在"

        ignore_files = ['organizer.py', 'rules.json', 'dashboard.html', '.env']
        ignore_dirs = ['.git', 'node_modules', '.agents', '__pycache__', 'test_sandbox']
        rule_folder_names = {rule["name"] for rule in self.rules}
        rule_folder_names.add(self.config.get("default_folder", "others"))

        files_to_process = []
        cleaned_mappings = {}

        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            rel_path = os.path.relpath(root, self.target_dir)
            first_seg = rel_path.split(os.sep)[0]
            if first_seg in rule_folder_names:
                continue

            for file in files:
                if file in ignore_files or file.startswith("dashboard.html"):
                    continue
                full_path = os.path.join(root, file)
                
                clean_path, new_name = self._apply_constraints(full_path)
                if clean_path is None:
                    continue

                final_path = clean_path
                if new_name != file:
                    new_path = os.path.join(root, new_name)
                    if os.path.exists(new_path) and os.path.abspath(full_path) != os.path.abspath(new_path):
                        base, ext = os.path.splitext(new_name)
                        counter = 1
                        while os.path.exists(new_path):
                            new_path = os.path.join(root, f"{base}_{counter}{ext}")
                            counter += 1
                        new_name = os.path.basename(new_path)
                    try:
                        os.rename(full_path, new_path)
                        final_path = new_path
                    except Exception:
                        pass
                
                files_to_process.append(final_path)
                cleaned_mappings[final_path] = new_name

        if not files_to_process:
            return True, "未找到需要整理的文件"

        # 并发分析
        analysis_results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(self.analyzer.analyze, f, self.suffix_templates): f for f in files_to_process}
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    analysis_results[file_path] = future.result()
                except Exception:
                    analysis_results[file_path] = "未知类型"

        # 物理移动
        for file_path, summary in analysis_results.items():
            filename = cleaned_mappings[file_path]
            category = self._match_rule(filename)
            dest_dir = os.path.join(self.target_dir, category)
            os.makedirs(dest_dir, exist_ok=True)

            new_filename = filename
            if self.rename_files:
                new_filename = self._sanitize_filename(filename, summary)

            dest_path = os.path.join(dest_dir, new_filename)
            if os.path.exists(dest_path) and os.path.abspath(file_path) != os.path.abspath(dest_path):
                base, ext = os.path.splitext(new_filename)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                    counter += 1
                new_filename = os.path.basename(dest_path)

            try:
                shutil.move(file_path, dest_path)
                self.report_data.append({
                    "original_name": filename,
                    "new_name": new_filename,
                    "category": category,
                    "summary": summary,
                    "size_bytes": os.path.getsize(dest_path),
                    "relative_path": os.path.relpath(dest_path, self.target_dir).replace(os.sep, '/')
                })
            except Exception:
                pass

        self._generate_html()
        return True, f"成功归纳整理 {len(self.report_data)} 个文件"

    def execute_custom_mapping(self, mapping):
        """按照自定义映射物理搬运文件，并回收旧空文件夹"""
        import shutil
        import os
        import logging
        logger = logging.getLogger("organizer.custom")
        self.report_data = []
        moved_count = 0

        for src_path, dest_path in mapping.items():
            src = src_path if os.path.isabs(src_path) else os.path.abspath(os.path.join(self.target_dir, src_path))
            dest = dest_path if os.path.isabs(dest_path) else os.path.abspath(os.path.join(self.target_dir, dest_path))

            if not os.path.exists(src):
                logger.warning(f"源文件不存在，跳过: {src}")
                continue

            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(src, dest)
                
                rel_dest = os.path.relpath(dest, self.target_dir).replace(os.sep, '/')
                category = rel_dest.split('/')[0] if '/' in rel_dest else "others"
                
                self.report_data.append({
                    "original_name": os.path.basename(src),
                    "new_name": os.path.basename(dest),
                    "category": category,
                    "summary": "拖拽自定义重排归档",
                    "size_bytes": os.path.getsize(dest),
                    "relative_path": rel_dest
                })
                moved_count += 1
            except Exception as e:
                logger.error(f"自定义搬运失败 {src} -> {dest}: {e}")

        self._clean_empty_dirs()
        self._generate_html()
        return True, f"成功重编排归档 {moved_count} 个文件，并回收冗余空目录"

    def _clean_empty_dirs(self):
        """递归清理空文件夹，精确排除保护目录全称"""
        import os
        ignore_dirs = {'.git', 'node_modules', '.agents', '__pycache__', 'test_sandbox'}
        for root, dirs, files in os.walk(self.target_dir, topdown=False):
            # 过滤被保护目录，防止在项目根目录下运行时删除这些系统目录
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            if os.path.basename(root) in ignore_dirs:
                continue
            for d in dirs:
                dir_path = os.path.join(root, d)
                try:
                    if os.path.exists(dir_path) and not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except Exception:
                    pass

    def _generate_html(self):
        dashboard_path = os.path.join(self.target_dir, "dashboard.html")
        category_counts = {}
        for item in self.report_data:
            cat = item["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        stats_js = json.dumps(category_counts)
        files_js = json.dumps(self.report_data, ensure_ascii=False)
        rules_desc = {rule["name"]: rule["description"] for rule in self.rules}
        rules_desc["others"] = "其他未匹配规则的文件"
        rules_desc_js = json.dumps(rules_desc, ensure_ascii=False)

        # 写入极具现代感、满足 interface-kit 美学规范的交互看板
        html_code = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件规格整理看板</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --background: 224 71% 4%;
            --foreground: 213 31% 91%;
            --card: 222 47% 11%;
            --card-foreground: 213 31% 91%;
            --primary: 263 90% 68%;
            --primary-foreground: 210 40% 98%;
            --muted-foreground: 215.4 16.3% 56.9%;
            --accent: 216 34% 17%;
            --border: 216 34% 17%;
            --radius: 12px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        html {{
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
        }}

        body {{
            font-family: 'Outfit', system-ui, -apple-system, sans-serif;
            background: radial-gradient(circle at top, #1e1b4b 0%, hsl(var(--background)) 70%);
            color: hsl(var(--foreground));
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        header {{
            padding: 1.5rem 3rem;
            background: rgba(15, 23, 42, 0.4);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        h1 {{
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            text-wrap: balance;
            background: linear-gradient(to right, #a78bfa, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .subtitle {{
            font-size: 0.85rem;
            color: hsl(var(--muted-foreground));
            margin-top: 0.25rem;
        }}

        .layout {{
            display: grid;
            grid-template-columns: 280px 1fr;
            flex: 1;
            overflow: hidden;
        }}

        .sidebar {{
            background: rgba(15, 23, 42, 0.2);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            padding: 2rem 1.5rem;
            overflow-y: auto;
        }}

        .sidebar-title {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: hsl(var(--muted-foreground));
            margin-bottom: 1.25rem;
            font-weight: 600;
        }}

        .category-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.6rem 0.9rem;
            border-radius: 8px; /* Concentric (12 - 4) */
            cursor: pointer;
            margin-bottom: 0.5rem;
            transition: background-color 150ms ease-out, transform 150ms ease-out;
            font-size: 0.9rem;
            font-weight: 500;
        }}

        .category-item:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}

        .category-item:active {{
            transform: scale(0.97);
        }}

        .category-item.active {{
            background: hsl(var(--primary));
            color: #000;
            font-weight: 600;
        }}

        .category-item .count {{
            background: rgba(255, 255, 255, 0.1);
            padding: 0.1rem 0.45rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-variant-numeric: tabular-nums;
        }}

        .category-item.active .count {{
            background: rgba(0, 0, 0, 0.15);
        }}

        .workspace {{
            padding: 2.5rem 3rem;
            overflow-y: auto;
        }}

        .search-container {{
            margin-bottom: 2rem;
            position: relative;
        }}

        .search-input {{
            width: 100%;
            padding: 0.8rem 1.25rem;
            border-radius: var(--radius);
            background: rgba(30, 41, 59, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            color: hsl(var(--foreground));
            font-size: 0.95rem;
            outline: none;
            backdrop-filter: blur(8px);
            transition: border-color 150ms ease-out, box-shadow 150ms ease-out;
        }}

        .search-input:focus {{
            border-color: hsl(var(--primary));
            box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.2);
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.25rem;
        }}

        .card {{
            background: rgba(30, 41, 59, 0.4);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: var(--radius);
            padding: 1.25rem;
            cursor: pointer;
            transition: transform 150ms ease-out, border-color 150ms ease-out, box-shadow 150ms ease-out;
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .card:hover {{
            transform: translateY(-2px);
            border-color: rgba(167, 139, 250, 0.3);
            box-shadow: 0 10px 25px -10px rgba(0, 0, 0, 0.5), 0 0 15px rgba(167, 139, 250, 0.05);
        }}

        .card:active {{
            transform: scale(0.98) translateY(0);
        }}

        .card-title {{
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
            color: hsl(var(--foreground));
            word-break: break-all;
            margin-bottom: 0.75rem;
            text-wrap: pretty;
        }}

        .card-summary {{
            font-size: 0.8rem;
            color: #d8b4fe;
            background: rgba(167, 139, 250, 0.08);
            padding: 0.5rem 0.75rem;
            border-radius: 6px; /* Concentric (12 - 6 = 6) */
            margin-bottom: 1rem;
            border-left: 2px solid hsl(var(--primary));
            line-height: 1.4;
        }}

        .card-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
            color: hsl(var(--muted-foreground));
        }}

        .card-meta span:last-child {{
            font-variant-numeric: tabular-nums;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <header>
        <div>
            <h1>📁 规格化目录智能看板</h1>
            <div class="subtitle">已应用 constraints 自定义规则清洗排版并分类归档。</div>
        </div>
    </header>

    <div class="layout">
        <div class="sidebar">
            <div class="sidebar-title">归类目录</div>
            <div id="category-list"></div>
        </div>

        <div class="workspace">
            <div class="search-container">
                <input type="text" id="search" class="search-input" placeholder="输入关键字搜索文件名或用途摘要...">
            </div>
            <div class="grid" id="file-grid"></div>
        </div>
    </div>

    <script>
        const filesData = {files_js};
        const statsData = {stats_js};
        const rulesDesc = {rules_desc_js};

        let currentCategory = 'all';
        let searchQuery = '';

        function formatBytes(bytes) {{
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }}

        function renderSidebar() {{
            const list = document.getElementById('category-list');
            let html = `<div class="category-item ${{currentCategory === 'all' ? 'active' : ''}}" onclick="setCategory('all')">
                <span>全部归档</span>
                <span class="count">${{filesData.length}}</span>
            </div>`;

            Object.keys(rulesDesc).forEach(cat => {{
                const count = statsData[cat] || 0;
                if (count > 0 || cat !== 'others') {{
                    html += `<div class="category-item ${{currentCategory === cat ? 'active' : ''}}" onclick="setCategory('${{cat}}')">
                        <span>${{cat}} <small style="opacity: 0.6; display:block; font-size:0.7rem; font-weight:normal;">${{rulesDesc[cat]}}</small></span>
                        <span class="count">${{count}}</span>
                    </div>`;
                }}
            }});
            list.innerHTML = html;
        }}

        function setCategory(cat) {{
            currentCategory = cat;
            renderSidebar();
            renderFiles();
        }}

        function renderFiles() {{
            const grid = document.getElementById('file-grid');
            let filtered = filesData;

            if (currentCategory !== 'all') {{
                filtered = filtered.filter(f => f.category === currentCategory);
            }}

            if (searchQuery) {{
                const query = searchQuery.toLowerCase();
                filtered = filtered.filter(f => 
                    f.original_name.toLowerCase().includes(query) || 
                    f.new_name.toLowerCase().includes(query) ||
                    f.summary.toLowerCase().includes(query)
                );
            }}

            if (filtered.length === 0) {{
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: hsl(var(--muted-foreground)); padding: 4rem 0;">没有找到符合条件的文件。</div>';
                return;
            }}

            grid.innerHTML = filtered.map(f => `
                <div class="card">
                    <div>
                        <div class="card-title">${{f.new_name}}</div>
                        <div class="card-summary">${{f.summary || "未检测到特征摘要"}}</div>
                    </div>
                    <div class="card-meta">
                        <span>${{f.category}}</span>
                        <span>${{formatBytes(f.size_bytes)}}</span>
                    </div>
                </div>
            `).join('');
        }}

        document.getElementById('search').addEventListener('input', (e) => {{
            searchQuery = e.target.value;
            renderFiles();
        }});

        renderSidebar();
        renderFiles();
    </script>
</body>
</html>
"""
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(html_code)


# ================= 插件核心 BasePlugin 实现 =================

class OrganizerPlugin(BasePlugin):
    @property
    def id(self) -> str:
        return "organizer"

    @property
    def name(self) -> str:
        return "📂 混乱目录规格化归类插件"

    @property
    def description(self) -> str:
        return "本地自完备规格整理引擎，对混乱目录文件进行物理归类，消除文件名空格、多重后缀等顽疾并生成HTML统计看板。"

    def is_available(self) -> bool:
        return True

    def run_test(self, sandbox_dir: str) -> Tuple[bool, str]:
        # 1. 自动生成 10 个测试样本
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

        for name, content in files_to_mock.items():
            f_path = os.path.join(sandbox_dir, name)
            mode = 'wb' if isinstance(content, bytes) or name.endswith(('.png', '.jpeg')) else 'w'
            encoding = None if 'b' in mode else 'utf-8'
            try:
                with open(f_path, mode, encoding=encoding) as f:
                    f.write(content)
            except Exception as e:
                return False, f"沙箱模拟数据生成失败: {e}"

        # 2. 物理整理自测
        engine = LocalOrganizerEngine(
            target_dir=sandbox_dir,
            use_llm=False,
            rename_files=True
        )
        success, log = engine.execute_整理()
        if not success:
            return False, f"物理整理动作失败: {log}"

        # 3. 验证断言
        # 验证临时文件 ~$temp_office_lock.xlsx 确实被彻底过滤清除了
        garbage_exists = os.path.exists(os.path.join(sandbox_dir, "others", "~$temp_office_lock.xlsx")) or \
                         os.path.exists(os.path.join(sandbox_dir, "~$temp_office_lock.xlsx"))
        if garbage_exists:
            return False, "测试失败：垃圾临时文件 ~$* 未被自动剔除物理清理"

        # 验证 HTML 看板是否成功生成
        if not os.path.exists(os.path.join(sandbox_dir, "dashboard.html")):
            return False, "测试失败：未在沙箱根目录成功生成 dashboard.html 交互式看板"

        # 验证文件夹是否正确归纳了（Documents，Images 等）
        doc_dir = os.path.join(sandbox_dir, "Documents")
        img_dir = os.path.join(sandbox_dir, "Images")
        if not os.path.exists(doc_dir) or not os.path.exists(img_dir):
            return False, "测试失败：没有正确按 rules.json 分割出归类目标文件夹 (Documents/Images)"

        # 4. TDD 门禁：测试自定义拖拽重排与旧空文件夹回收
        possible_src_paths = [
            os.path.join(sandbox_dir, "Music", "favorite_song.mp3"),
            os.path.join(sandbox_dir, "Music", "favorite_song_1.mp3"),
            os.path.join(sandbox_dir, "others", "favorite_song.mp3")
        ]
        real_src = None
        for p in possible_src_paths:
            if os.path.exists(p):
                real_src = p
                break
        
        if not real_src:
            real_src = os.path.join(sandbox_dir, "Music", "favorite_song.mp3")
            os.makedirs(os.path.dirname(real_src), exist_ok=True)
            with open(real_src, "w") as f:
                f.write("mock song")

        custom_dest = os.path.join(sandbox_dir, "Custom_Music", "cool_favorite_song.mp3")
        test_mapping = {real_src: custom_dest}
        
        custom_ok, custom_log = engine.execute_custom_mapping(test_mapping)
        if not custom_ok:
            return False, f"测试失败：自定义重组物理移动执行失败: {custom_log}"
            
        # 断言 A: 目标文件必须存在
        if not os.path.exists(custom_dest):
            return False, "测试失败：自定义重排目标文件 cool_favorite_song.mp3 物理上不存在"
            
        # 断言 B: 原文件必须已挪走
        if os.path.exists(real_src):
            return False, "测试失败：自定义重排原文件没有被成功移除"
            
        # 断言 C: 旧的空目录 Music 必须被彻底自动清理回收
        old_dir = os.path.dirname(real_src)
        if os.path.exists(old_dir) and not os.listdir(old_dir):
            return False, f"测试失败：原有空目录 {old_dir} 物理移动后未能自动回收清除"

        return True, "结合自测试成功！已自动理顺目录文件，验证拖拽物理布局转换及空目录回收，生成最新看板。" 

    def execute(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        target = params.get("target_dir")
        if not target:
            return False, "未指定目标整理目录"
        
        custom_mapping = params.get("custom_mapping")
        use_llm = params.get("use_llm", False)
        rename = params.get("rename_files", False)
        rules_path = params.get("rules_path")

        engine = LocalOrganizerEngine(
            target_dir=target,
            rules_path=rules_path,
            use_llm=use_llm,
            rename_files=rename
        )
        if custom_mapping:
            return engine.execute_custom_mapping(custom_mapping)
        return engine.execute_整理()
