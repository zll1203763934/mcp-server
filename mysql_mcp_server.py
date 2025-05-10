#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL MCP Server - 命令行入口点

这个文件提供了一个命令行入口点，用于启动MySQL MCP服务器。
它整合了数据库连接、模式管理和服务器功能。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入MySQL MCP模块
from mysql_mcp.database import MySQLDatabase
from mysql_mcp.schema import SchemaManager
from server import app, init_database, init_security, setup_logging


def load_config(config_path: str = None) -> Dict[str, Any]:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认路径
    
    Returns:
        Dict[str, Any]: 配置信息
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        raise


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="MySQL MCP Server")
    parser.add_argument(
        "-c", "--config", 
        help="配置文件路径", 
        default=None
    )
    parser.add_argument(
        "-d", "--debug", 
        help="启用调试模式", 
        action="store_true"
    )
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置日志
    setup_logging(config)
    logger.info("MySQL MCP Server 正在启动...")
    
    # 初始化数据库连接
    try:
        database = init_database(config)
        logger.info("数据库连接初始化成功")
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        sys.exit(1)
    
    # 初始化模式管理器
    schema_manager = SchemaManager(config["database"]["database"])
    
    # 获取数据库模式并更新模式管理器
    try:
        schema_data = database.get_schema()
        schema_manager.update_schema(schema_data)
        logger.info(f"已加载数据库模式，共 {len(schema_data['tables'])} 个表")
    except Exception as e:
        logger.error(f"加载数据库模式失败: {e}")
    
    # 初始化安全管理器
    security = init_security(config)
    
    # 启动服务器
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    debug = args.debug or server_config.get("debug", False)
    
    logger.info(f"启动服务器: {host}:{port}")
    
    # 导入uvicorn并启动服务器
    import uvicorn
    uvicorn.run(
        "server:app", 
        host=host, 
        port=port, 
        reload=debug,
        log_level="debug" if debug else "info"
    )


if __name__ == "__main__":
    main()