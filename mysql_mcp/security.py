#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安全和访问控制模块

这个模块提供了SQL查询验证和访问控制功能，包括：
- 验证SQL查询是否允许执行
- 限制可访问的表和操作
- 设置查询超时和最大返回行数
"""

import re
from typing import List, Optional

from loguru import logger


class SecurityManager:
    """安全管理器类"""
    
    def __init__(self, allowed_tables: List[str] = None, allowed_operations: List[str] = None,
                 max_rows: int = 1000, timeout_seconds: int = 30):
        """初始化安全管理器
        
        Args:
            allowed_tables: 允许访问的表列表，空列表表示允许所有表
            allowed_operations: 允许的SQL操作列表，默认为SELECT, SHOW, DESCRIBE
            max_rows: 最大返回行数
            timeout_seconds: 查询超时时间（秒）
        """
        self.allowed_tables = allowed_tables or []
        self.allowed_operations = allowed_operations or ["SELECT", "SHOW", "DESCRIBE"]
        self.max_rows = max_rows
        self.timeout_seconds = timeout_seconds
        
        logger.info(f"安全管理器初始化: 允许的表={self.allowed_tables}, 允许的操作={self.allowed_operations}")
    
    def validate_query(self, query: str) -> bool:
        """验证SQL查询是否允许执行
        
        Args:
            query: SQL查询语句
        
        Returns:
            bool: 查询是否允许执行
        """
        if not query.strip():
            logger.warning("空查询被拒绝")
            return False
        
        # 提取SQL操作类型
        operation_match = re.match(r'^\s*(\w+)', query, re.IGNORECASE)
        if not operation_match:
            logger.warning(f"无法识别的查询操作: {query}")
            return False
        
        operation = operation_match.group(1).upper()
        
        # 检查操作是否允许
        if operation not in self.allowed_operations:
            logger.warning(f"操作不被允许: {operation}")
            return False
        
        # 如果指定了允许的表，则检查查询中的表是否允许
        if self.allowed_tables:
            # 提取查询中的表名
            # 注意：这是一个简化的实现，可能无法处理所有SQL语法
            tables_pattern = r'\bFROM\s+`?([\w\d_]+)`?|\bJOIN\s+`?([\w\d_]+)`?|\bUPDATE\s+`?([\w\d_]+)`?|\bINTO\s+`?([\w\d_]+)`?'
            tables_matches = re.finditer(tables_pattern, query, re.IGNORECASE)
            
            query_tables = []
            for match in tables_matches:
                # 获取匹配的组中非None的值
                table = next((g for g in match.groups() if g is not None), None)
                if table:
                    query_tables.append(table.lower())
            
            # 检查查询中的表是否都在允许列表中
            for table in query_tables:
                if table not in [t.lower() for t in self.allowed_tables]:
                    logger.warning(f"表不被允许访问: {table}")
                    return False
        
        return True
    
    def is_dangerous_query(self, query: str) -> bool:
        """检查查询是否包含危险操作
        
        Args:
            query: SQL查询语句
        
        Returns:
            bool: 查询是否包含危险操作
        """
        # 检查是否包含DROP, TRUNCATE, DELETE等危险操作
        dangerous_patterns = [
            r'\bDROP\b',
            r'\bTRUNCATE\b',
            r'\bDELETE\b\s+(?!WHERE)',  # DELETE没有WHERE条件
            r'\bUPDATE\b\s+(?!WHERE)',  # UPDATE没有WHERE条件
            r'--',  # SQL注释
            r';\s*\w',  # 多条语句
            r'\bEXEC\b',
            r'\bXP_\w',
            r'\bSYSTEM\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"检测到危险查询模式: {pattern}")
                return True
        
        return False