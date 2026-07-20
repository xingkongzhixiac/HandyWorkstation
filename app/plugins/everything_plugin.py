# -*- coding: utf-8 -*-

import os
import shutil
import urllib.request
import json
import logging
from typing import Dict, List, Tuple, Any
from app.core.base_plugin import BasePlugin

logger = logging.getLogger("organizer.plugin.everything")

class EverythingConnector:
    """与本地 Everything 软件的 HTTP Server 进行通信"""
    def __init__(self, port: int = 80):
        self.base_url = f"http://localhost:{port}"

    def test_connection(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/?json=1&count=1", method='GET')
            with urllib.request.urlopen(req, timeout=1.0) as response:
                return response.status == 200
        except Exception:
            return False

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"{self.base_url}/?search={encoded_query}&json=1&count={limit}"
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                results = []
                for item in data.get("results", []):
                    results.append({
                        "name": item.get("name"),
                        "path": os.path.join(item.get("path"), item.get("name")),
                        "size": int(item.get("size", 0))
                    })
                return results
        except Exception as e:
            logger.debug(f"Everything 检索出错: {e}")
            return []


class EverythingPlugin(BasePlugin):
    def __init__(self, port: int = 80):
        self.port = port
        self.connector = EverythingConnector(port)

    @property
    def id(self) -> str:
        return "everything_cleanup"

    @property
    def name(self) -> str:
        return "⚡ Everything C盘空间救急插件"

    @property
    def description(self) -> str:
        return "本插件是附加救急工具。通过秒级联动 Windows Everything 搜索服务，闪电获取 C 盘大文件或全盘垃圾缓存，支持一键无损转移搬家。"

    def is_available(self) -> bool:
        return self.connector.test_connection()

    def run_test(self, sandbox_dir: str) -> Tuple[bool, str]:
        # 1. 优先测试 Everything 本地服务的连通性
        connected = self.connector.test_connection()
        if not connected:
            return False, (
                "连接失败：Everything 服务未在本地 HTTP 端口开启。\n"
                "【启用方法】打开 Everything -> 工具 -> 选项 -> HTTP 服务器 -> 勾选“启用 HTTP 服务器”，点击确定即可激活。"
            )

        # 2. 模拟大文件搬运验证（验证文件 IO 与沙箱环境的转移逻辑）
        mock_big_file = os.path.join(sandbox_dir, "mock_huge_movie.avi")
        mock_dest_dir = os.path.join(sandbox_dir, "D_Drive_Backup")
        
        try:
            # 建立一个假的模拟大文件
            with open(mock_big_file, "w", encoding="utf-8") as f:
                f.write("模拟大文件内容" * 100)
            
            # 验证搬运
            os.makedirs(mock_dest_dir, exist_ok=True)
            shutil.move(mock_big_file, os.path.join(mock_dest_dir, "mock_huge_movie.avi"))
            
            if not os.path.exists(os.path.join(mock_dest_dir, "mock_huge_movie.avi")):
                return False, "搬运逻辑测试失败：文件未成功被移动至目的地"
                
            return True, "连通性自测通过！Everything 服务正常响应。沙箱大文件搬运测试成功。"
        except Exception as e:
            return False, f"物理IO搬运测试发生崩溃: {e}"

    def execute(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        action = params.get("action")
        self.port = int(params.get("port", 80))
        self.connector = EverythingConnector(self.port)

        if not self.is_available():
            return False, f"Everything 连接测试失败，请确认本地端口 {self.port} 服务已启动"

        if action == "scan_big":
            # 检索C盘大于100MB的冗余大文件
            res = self.connector.search("c: size:>100mb", limit=50)
            return True, json.dumps(res, ensure_ascii=False)
            
        elif action == "scan_garbage":
            # 检索垃圾临时文件
            results = []
            patterns = ["c: ext:tmp", "c: file:~$*", "c: file:thumbs.db"]
            for p in patterns:
                res = self.connector.connector.search(p, limit=40) if hasattr(self.connector, 'connector') else self.connector.search(p, limit=40)
                results.extend(res)
            return True, json.dumps(results, ensure_ascii=False)
            
        elif action == "move_files":
            files = params.get("files", [])
            dest = params.get("dest")
            if not dest:
                return False, "未指定转移目的地目录"
            os.makedirs(dest, exist_ok=True)
            
            success_count = 0
            for item in files:
                src = item.get("path")
                if not src or not os.path.exists(src):
                    continue
                filename = os.path.basename(src)
                dest_path = os.path.join(dest, filename)
                
                # 解决重名
                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dest, f"{base}_{counter}{ext}")
                        counter += 1
                try:
                    shutil.move(src, dest_path)
                    success_count += 1
                except Exception:
                    pass
            return True, f"成功搬运 {success_count} 个大文件到 {dest}"
            
        elif action == "clean_files":
            files = params.get("files", [])
            success_count = 0
            for item in files:
                src = item.get("path")
                if not src or not os.path.exists(src):
                    continue
                try:
                    os.remove(src)
                    success_count += 1
                except Exception:
                    pass
            return True, f"成功删除 {success_count} 个系统缓存临时文件"

        return False, f"未知的 Everything 插件动作: {action}"
