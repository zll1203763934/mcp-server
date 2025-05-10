#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP工具测试

这个模块测试MySQL MCP工具的功能。
"""

import unittest
from unittest.mock import patch, MagicMock

from mysql_mcp.database import MySQLDatabase
from mysql_mcp.security import SecurityManager
from mysql_mcp.tools import register_tools


class TestMCPTools(unittest.TestCase):
    """测试MCP工具"""
    
    def setUp(self):
        """测试前准备"""
        # 模拟数据库和安全管理器
        self.mock_db = MagicMock(spec=MySQLDatabase)
        self.mock_security = MagicMock(spec=SecurityManager)
        
        # 设置安全管理器属性
        self.mock_security.allowed_tables = ["users", "products"]
        self.mock_security.max_rows = 100
        
        # 注册工具
        self.registry = register_tools(self.mock_db, self.mock_security)
    
    def test_execute_query_tool(self):
        """测试执行查询工具"""
        # 设置验证结果
        self.mock_security.validate_query.return_value = True
        self.mock_security.is_dangerous_query.return_value = False
        
        # 设置查询结果
        expected_result = {"success": True, "rows": [{"id": 1, "name": "测试"}]}
        self.mock_db.execute_query.return_value = expected_result
        
        # 执行工具
        tool = self.registry.get_tool("execute_query")
        result = tool("SELECT * FROM users")
        
        # 验证结果
        self.assertEqual(result, expected_result)
        self.mock_security.validate_query.assert_called_once_with("SELECT * FROM users")
        self.mock_security.is_dangerous_query.assert_called_once_with("SELECT * FROM users")
        self.mock_db.execute_query.assert_called_once_with("SELECT * FROM users", self.mock_security.max_rows)
    
    def test_execute_query_not_allowed(self):
        """测试不允许的查询"""
        # 设置验证结果
        self.mock_security.validate_query.return_value = False
        
        # 执行工具
        tool = self.registry.get_tool("execute_query")
        result = tool("DROP TABLE users")
        
        # 验证结果
        self.assertEqual(result, {"success": False, "error": "查询操作不被允许"})
        self.mock_db.execute_query.assert_not_called()
    
    def test_execute_dangerous_query(self):
        """测试危险查询"""
        # 设置验证结果
        self.mock_security.validate_query.return_value = True
        self.mock_security.is_dangerous_query.return_value = True
        
        # 执行工具
        tool = self.registry.get_tool("execute_query")
        result = tool("DELETE FROM users")
        
        # 验证结果
        self.assertEqual(result, {"success": False, "error": "查询包含危险操作"})
        self.mock_db.execute_query.assert_not_called()
    
    def test_get_schema_tool(self):
        """测试获取模式工具"""
        # 设置模式结果
        expected_schema = {"database": "test_db", "tables": []}
        self.mock_db.get_schema.return_value = expected_schema
        
        # 执行工具
        tool = self.registry.get_tool("get_schema")
        result = tool()
        
        # 验证结果
        self.assertEqual(result, expected_schema)
        self.mock_db.get_schema.assert_called_once_with(self.mock_security.allowed_tables)
    
    def test_get_table_structure_tool(self):
        """测试获取表结构工具"""
        # 设置表结构结果
        expected_result = {"success": True, "rows": []}
        self.mock_db.execute_query.return_value = expected_result
        
        # 执行工具
        tool = self.registry.get_tool("get_table_structure")
        result = tool("users")
        
        # 验证结果
        self.assertEqual(result, expected_result)
        self.mock_db.execute_query.assert_called_once_with("DESCRIBE `users`")
    
    def test_get_table_structure_not_allowed(self):
        """测试不允许的表结构查询"""
        # 执行工具
        tool = self.registry.get_tool("get_table_structure")
        result = tool("forbidden_table")
        
        # 验证结果
        self.assertEqual(result, {"success": False, "error": "表 forbidden_table 不被允许访问"})
        self.mock_db.execute_query.assert_not_called()
    
    def test_analyze_data_tool(self):
        """测试分析数据工具"""
        # 设置分析结果
        expected_result = {"success": True, "rows": [{"total_rows": 10}]}
        self.mock_db.execute_query.return_value = expected_result
        
        # 执行工具
        tool = self.registry.get_tool("analyze_data")
        result = tool("users")
        
        # 验证结果
        self.assertEqual(result, expected_result)
        self.mock_db.execute_query.assert_called_once()
    
    def test_analyze_data_with_column(self):
        """测试带列的数据分析"""
        # 设置分析结果
        expected_result = {"success": True, "rows": [{"total_rows": 10, "unique_values": 5}]}
        self.mock_db.execute_query.return_value = expected_result
        
        # 执行工具
        tool = self.registry.get_tool("analyze_data")
        result = tool("users", "name")
        
        # 验证结果
        self.assertEqual(result, expected_result)
        self.mock_db.execute_query.assert_called_once()
    
    def test_get_table_relations_tool(self):
        """测试获取表关系工具"""
        # 设置关系结果
        expected_result = {"success": True, "rows": []}
        self.mock_db.execute_query.return_value = expected_result
        
        # 执行工具
        tool = self.registry.get_tool("get_table_relations")
        result = tool()
        
        # 验证结果
        self.assertEqual(result, expected_result)
        self.mock_db.execute_query.assert_called_once()


if __name__ == "__main__":
    unittest.main()