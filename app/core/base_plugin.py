# -*- coding: utf-8 -*-

from typing import Tuple, Dict, Any

class BasePlugin:
    """所有平台组件插件的契约基类"""
    
    @property
    def id(self) -> str:
        """插件的唯一字符串ID标识"""
        raise NotImplementedError

    @property
    def name(self) -> str:
        """插件显示名称"""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """插件的功能/用途描述"""
        raise NotImplementedError

    def is_available(self) -> bool:
        """检测当前环境（如网络、依赖、本地服务等）下该插件是否可用"""
        return True

    def run_test(self, sandbox_dir: str) -> Tuple[bool, str]:
        """结合测试验证接口。在物理隔离的 sandbox_dir 内进行结合自测。
        返回: (是否通过测试, 详细说明/结果)
        """
        raise NotImplementedError

    def execute(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """实际执行插件的业务功能。
        返回: (是否成功, 执行日志/说明)
        """
        raise NotImplementedError
