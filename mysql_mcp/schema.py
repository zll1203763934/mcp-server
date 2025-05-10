#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库模式处理模块

这个模块提供了数据库结构和关系的处理功能，包括：
- 解析数据库模式
- 生成表结构描述
- 分析表关系
"""

from typing import Dict, List, Any, Optional

from loguru import logger


class SchemaManager:
    """数据库模式管理器类"""
    
    def __init__(self, database_name: str):
        """初始化模式管理器
        
        Args:
            database_name: 数据库名称
        """
        self.database_name = database_name
        self.tables = {}
        self.relations = []
    
    def update_schema(self, schema_data: Dict[str, Any]) -> None:
        """更新数据库模式信息
        
        Args:
            schema_data: 数据库模式数据
        """
        if "tables" not in schema_data:
            logger.warning("模式数据中没有表信息")
            return
        
        # 更新表信息
        for table in schema_data["tables"]:
            table_name = table["name"]
            self.tables[table_name] = table
        
        logger.info(f"更新了 {len(schema_data['tables'])} 个表的模式信息")
    
    def update_relations(self, relations_data: List[Dict[str, Any]]) -> None:
        """更新表关系信息
        
        Args:
            relations_data: 表关系数据
        """
        self.relations = relations_data
        logger.info(f"更新了 {len(relations_data)} 个表关系信息")
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """获取表信息
        
        Args:
            table_name: 表名
        
        Returns:
            Optional[Dict[str, Any]]: 表信息，如果表不存在则返回None
        """
        return self.tables.get(table_name)
    
    def get_table_relations(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表关系
        
        Args:
            table_name: 表名，如果为None则返回所有关系
        
        Returns:
            List[Dict[str, Any]]: 表关系列表
        """
        if table_name is None:
            return self.relations
        
        # 过滤与指定表相关的关系
        return [
            relation for relation in self.relations
            if relation["table_name"] == table_name or relation["referenced_table"] == table_name
        ]
    
    def generate_table_description(self, table_name: str) -> str:
        """生成表结构描述
        
        Args:
            table_name: 表名
        
        Returns:
            str: 表结构描述
        """
        table_info = self.get_table_info(table_name)
        if not table_info:
            return f"表 {table_name} 不存在"
        
        description = f"表 {table_name} 的结构：\n"
        
        # 添加列信息
        description += "列：\n"
        for column in table_info["columns"]:
            nullable = "可为空" if column["nullable"] else "非空"
            key_info = f"({column['key']})" if column["key"] else ""
            default = f"默认值: {column['default']}" if column["default"] is not None else ""
            description += f"  - {column['name']}: {column['type']} {nullable} {key_info} {default} {column['extra']}\n"
        
        # 添加关系信息
        relations = self.get_table_relations(table_name)
        if relations:
            description += "\n关系：\n"
            for relation in relations:
                if relation["table_name"] == table_name:
                    description += f"  - 外键 {relation['column_name']} 引用 {relation['referenced_table']}.{relation['referenced_column']}\n"
                else:
                    description += f"  - 被 {relation['table_name']}.{relation['column_name']} 引用\n"
        
        return description
    
    def generate_database_summary(self) -> str:
        """生成数据库概要
        
        Returns:
            str: 数据库概要
        """
        summary = f"数据库 {self.database_name} 概要：\n\n"
        
        # 添加表信息
        summary += f"共有 {len(self.tables)} 个表：\n"
        for table_name in sorted(self.tables.keys()):
            table_info = self.tables[table_name]
            column_count = len(table_info["columns"])
            summary += f"  - {table_name}: {column_count} 列\n"
        
        # 添加关系信息
        if self.relations:
            summary += f"\n共有 {len(self.relations)} 个表关系\n"
        
        return summary