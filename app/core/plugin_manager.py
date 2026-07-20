# -*- coding: utf-8 -*-

import os
import shutil
import logging
from typing import Dict, List, Tuple, Optional
from app.core.base_plugin import BasePlugin

logger = logging.getLogger("organizer.manager")

class PluginManager:
    """管理注册插件的生命周期及结合性集成测试"""
    def __init__(self, sandbox_root: str):
        self.sandbox_root = os.path.abspath(sandbox_root)
        self._plugins: Dict[str, BasePlugin] = {}

    def register_plugin(self, plugin: BasePlugin):
        """注册一个插件"""
        self._plugins[plugin.id] = plugin
        logger.info(f"成功注册插件: {plugin.name} ({plugin.id})")

    def get_plugins(self) -> List[BasePlugin]:
        """获取所有已注册的插件列表"""
        return list(self._plugins.values())

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """根据 ID 获取特定插件"""
        return self._plugins.get(plugin_id)

    def run_plugin_test(self, plugin_id: str) -> Tuple[bool, str]:
        """为特定插件建立物理隔离沙箱并运行其结合自测试"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False, f"未找到 ID 为 {plugin_id} 的插件"

        # 隔离的测试沙箱目录
        plugin_sandbox = os.path.join(self.sandbox_root, plugin_id)
        
        # 先清理并重建沙箱，保证测试无污染
        try:
            if os.path.exists(plugin_sandbox):
                shutil.rmtree(plugin_sandbox, ignore_errors=True)
            os.makedirs(plugin_sandbox, exist_ok=True)
        except Exception as e:
            return False, f"创建隔离测试沙箱失败: {e}"

        # 运行插件的结合性测试
        try:
            passed, detail = plugin.run_test(plugin_sandbox)
            return passed, detail
        except Exception as e:
            return False, f"集成测试执行发生崩溃: {e}"
