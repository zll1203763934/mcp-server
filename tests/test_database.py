#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库模块测试

这个模块测试MySQL数据库连接和操作功能。
"""

import unittest
from unittest.mock import patch, MagicMock

from mysql_mcp.database import MySQLDatabase


class TestMySQLDatabase(unittest.TestCase):
    """测试MySQLDatabase类"""
    
    @patch('mysql.connector.connect')
    def setUp(self, mock_connect):
        """测试前准备"""
        # 模拟数据库连接
        self.mock_connection = MagicMock()
        mock_connect.return_value = self.mock_connection
        
        # 创建数据库实例
        self.db = MySQLDatabase(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db"
        )
    
    def test_is_connected(self):
        """测试连接状态检查"""
        # 设置连接状态
        self.mock_connection.is_connected.return_value = True
        self.assertTrue(self.db.is_connected())
        
        self.mock_connection.is_connected.return_value = False
        self.assertFalse(self.db.is_connected())
    
    def test_reconnect_if_needed(self):
        """测试重新连接功能"""
        # 设置连接断开
        self.mock_connection.is_connected.return_value = False
        
        # 调用重连方法
        with patch.object(self.db, 'connect') as mock_connect:
            self.db.reconnect_if_needed()
            mock_connect.assert_called_once()
    
    def test_execute_select_query(self):
        """测试执行SELECT查询"""
        # 模拟游标
        mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = mock_cursor
        
        # 设置查询结果
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchmany.return_value = [{"id": 1, "name": "测试"}]
        mock_cursor.fetchone.return_value = None
        
        # 执行查询
        result = self.db.execute_query("SELECT * FROM test_table")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["rows"], [{"id": 1, "name": "测试"}])
        self.assertEqual(result["row_count"], 1)
        self.assertFalse(result["has_more"])
        self.assertEqual(result["columns"], ["id", "name"])
    
    def test_execute_update_query(self):
        """测试执行UPDATE查询"""
        # 模拟游标
        mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = mock_cursor
        
        # 设置影响行数
        mock_cursor.rowcount = 2
        
        # 执行查询
        result = self.db.execute_query("UPDATE test_table SET name = '新名称' WHERE id = 1")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["affected_rows"], 2)
        
        # 验证提交事务
        self.mock_connection.commit.assert_called_once()
    
    def test_execute_query_error(self):
        """测试查询错误处理"""
        # 模拟游标
        mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = mock_cursor
        
        # 设置查询异常
        mock_cursor.execute.side_effect = Exception("测试错误")
        
        # 执行查询
        result = self.db.execute_query("SELECT * FROM test_table")
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "测试错误")
    
    def test_get_schema(self):
        """测试获取数据库模式"""
        # 模拟execute_query方法
        with patch.object(self.db, 'execute_query') as mock_execute:
            # 设置表查询结果
            mock_execute.side_effect = [
                # SHOW TABLES 结果
                {
                    "success": True,
                    "rows": [{"Tables_in_test_db": "test_table"}]
                },
                # DESCRIBE test_table 结果
                {
                    "success": True,
                    "rows": [
                        {"Field": "id", "Type": "int", "Null": "NO", "Key": "PRI", "Default": None, "Extra": "auto_increment"},
                        {"Field": "name", "Type": "varchar(255)", "Null": "YES", "Key": "", "Default": None, "Extra": ""}
                    ]
                }
            ]
            
            # 获取模式
            schema = self.db.get_schema()
            
            # 验证结果
            self.assertEqual(schema["database"], "test_db")
            self.assertEqual(len(schema["tables"]), 1)
            self.assertEqual(schema["tables"][0]["name"], "test_table")
            self.assertEqual(len(schema["tables"][0]["columns"]), 2)
    
    def test_close(self):
        """测试关闭连接"""
        # 设置连接状态
        self.mock_connection.is_connected.return_value = True
        
        # 关闭连接
        self.db.close()
        
        # 验证连接关闭
        self.mock_connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()