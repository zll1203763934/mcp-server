#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL数据库连接和操作模块

这个模块提供了与MySQL数据库交互的基本功能，包括：
- 建立和管理数据库连接
- 执行SQL查询
- 获取数据库模式信息
- 处理查询结果
"""

import time
from typing import Dict, List, Any, Optional, Union, Tuple

import mysql.connector
from loguru import logger
from mysql.connector import Error as MySQLError


class MySQLDatabase:
    """MySQL数据库连接和操作类"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        """初始化数据库连接
        
        Args:
            host: 数据库主机地址
            port: 数据库端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.connect()
    
    def connect(self) -> None:
        """建立数据库连接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logger.info(f"成功连接到MySQL数据库: {self.host}:{self.port}/{self.database}")
        except MySQLError as e:
            logger.error(f"连接MySQL数据库失败: {e}")
            raise
    
    def is_connected(self) -> bool:
        """检查数据库连接是否有效
        
        Returns:
            bool: 连接是否有效
        """
        if self.connection is None:
            return False
        return self.connection.is_connected()
    
    def reconnect_if_needed(self) -> None:
        """如果连接已断开，则重新连接"""
        if not self.is_connected():
            logger.warning("数据库连接已断开，尝试重新连接...")
            self.connect()
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.connection and self.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")
            self.connection = None
    
    def execute_query(self, query: str, max_rows: int = 1000) -> Dict[str, Any]:
        """执行SQL查询
        
        Args:
            query: SQL查询语句
            max_rows: 最大返回行数
        
        Returns:
            Dict[str, Any]: 查询结果
        """
        self.reconnect_if_needed()
        
        start_time = time.time()
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            # 执行查询
            cursor.execute(query)
            
            # 处理不同类型的查询
            if query.strip().upper().startswith("SELECT") or \
               query.strip().upper().startswith("SHOW") or \
               query.strip().upper().startswith("DESCRIBE"):
                # 获取结果
                rows = cursor.fetchmany(max_rows)
                has_more = cursor.fetchone() is not None
                
                # 获取列信息
                columns = []
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "rows": rows,
                    "row_count": len(rows),
                    "has_more": has_more,
                    "columns": columns,
                    "execution_time": execution_time
                }
            else:
                # 对于非查询操作，提交事务并返回影响的行数
                self.connection.commit()
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "affected_rows": cursor.rowcount,
                    "execution_time": execution_time
                }
        except MySQLError as e:
            logger.error(f"执行查询失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
    
    def get_schema(self, allowed_tables: List[str] = None) -> Dict[str, Any]:
        """获取数据库模式信息
        
        Args:
            allowed_tables: 允许的表列表，如果为空则获取所有表
        
        Returns:
            Dict[str, Any]: 数据库模式信息
        """
        self.reconnect_if_needed()
        
        schema = {
            "database": self.database,
            "tables": []
        }
        
        try:
            # 获取所有表
            tables_query = "SHOW TABLES"
            tables_result = self.execute_query(tables_query)
            
            if not tables_result["success"]:
                return schema
            
            tables = [list(row.values())[0] for row in tables_result["rows"]]
            
            # 如果指定了允许的表，则过滤表列表
            if allowed_tables:
                tables = [table for table in tables if table in allowed_tables]
            
            # 获取每个表的结构
            for table in tables:
                table_info = {
                    "name": table,
                    "columns": []
                }
                
                # 获取表结构
                columns_query = f"DESCRIBE `{table}`"
                columns_result = self.execute_query(columns_query)
                
                if columns_result["success"]:
                    for column in columns_result["rows"]:
                        column_info = {
                            "name": column["Field"],
                            "type": column["Type"],
                            "nullable": column["Null"] == "YES",
                            "key": column["Key"],
                            "default": column["Default"],
                            "extra": column["Extra"]
                        }
                        table_info["columns"].append(column_info)
                
                schema["tables"].append(table_info)
            
            return schema
        except MySQLError as e:
            logger.error(f"获取数据库模式失败: {e}")
            return schema