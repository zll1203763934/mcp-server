#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP工具定义模块

这个模块定义了与MySQL数据库交互的MCP工具集，包括：
- 执行SQL查询工具
- 获取数据库模式工具
- 获取表结构工具
- 分析数据工具
"""

from typing import Dict, List, Any, Optional, Callable

from loguru import logger
from python_mcp import ToolRegistry

# 使用python_mcp模块中的工具注册功能

from mysql_mcp.database import MySQLDatabase
from mysql_mcp.security import SecurityManager


def register_tools(database: MySQLDatabase, security: SecurityManager) -> ToolRegistry:
    """注册MCP工具
    
    Args:
        database: MySQL数据库连接
        security: 安全管理器
    
    Returns:
        ToolRegistry: MCP工具注册表
    """
    registry = ToolRegistry()
    
    # 执行SQL查询工具
    @registry.tool("execute_query")
    def execute_query(query: str) -> Dict[str, Any]:
        """执行SQL查询
        
        Args:
            query: SQL查询语句
        
        Returns:
            Dict[str, Any]: 查询结果
        """
        logger.info(f"执行SQL查询: {query}")
        
        # 验证查询
        if not security.validate_query(query):
            return {"success": False, "error": "查询操作不被允许"}
        
        # 检查危险查询
        if security.is_dangerous_query(query):
            return {"success": False, "error": "查询包含危险操作"}
        
        # 执行查询
        return database.execute_query(query, security.max_rows)
    
    # 获取数据库模式工具
    @registry.tool("get_schema")
    def get_schema() -> Dict[str, Any]:
        """获取数据库模式信息
        
        Returns:
            Dict[str, Any]: 数据库模式信息
        """
        logger.info("获取数据库模式信息")
        return database.get_schema(security.allowed_tables)
    
    # 获取表结构工具
    @registry.tool("get_table_structure")
    def get_table_structure(table_name: str) -> Dict[str, Any]:
        """获取表结构
        
        Args:
            table_name: 表名
        
        Returns:
            Dict[str, Any]: 表结构信息
        """
        logger.info(f"获取表结构: {table_name}")
        
        # 检查表是否允许访问
        if security.allowed_tables and table_name not in security.allowed_tables:
            return {"success": False, "error": f"表 {table_name} 不被允许访问"}
        
        # 获取表结构
        query = f"DESCRIBE `{table_name}`"
        return database.execute_query(query)
    
    # 分析数据工具
    @registry.tool("analyze_data")
    def analyze_data(table_name: str, column_name: Optional[str] = None) -> Dict[str, Any]:
        """分析表数据
        
        Args:
            table_name: 表名
            column_name: 列名，如果为空则分析整个表
        
        Returns:
            Dict[str, Any]: 分析结果
        """
        logger.info(f"分析数据: 表={table_name}, 列={column_name}")
        
        # 检查表是否允许访问
        if security.allowed_tables and table_name not in security.allowed_tables:
            return {"success": False, "error": f"表 {table_name} 不被允许访问"}
        
        # 构建分析查询
        if column_name:
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT `{column_name}`) as unique_values,
                MIN(`{column_name}`) as min_value,
                MAX(`{column_name}`) as max_value,
                AVG(`{column_name}`) as avg_value
            FROM `{table_name}`
            """
        else:
            query = f"SELECT COUNT(*) as total_rows FROM `{table_name}`"
        
        return database.execute_query(query)
    
    # 获取表关系工具
    @registry.tool("get_table_relations")
    def get_table_relations() -> Dict[str, Any]:
        """获取表之间的关系
        
        Returns:
            Dict[str, Any]: 表关系信息
        """
        logger.info("获取表关系信息")
        
        # 查询外键关系
        query = """
        SELECT 
            TABLE_NAME as table_name,
            COLUMN_NAME as column_name,
            REFERENCED_TABLE_NAME as referenced_table,
            REFERENCED_COLUMN_NAME as referenced_column
        FROM 
            INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE 
            REFERENCED_TABLE_SCHEMA = DATABASE()
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """
        
        return database.execute_query(query)
    
    return registry