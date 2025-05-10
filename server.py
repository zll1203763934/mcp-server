#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL MCP Server - 主服务器入口

这个文件实现了MCP服务器的主要功能，包括：
- 加载配置
- 初始化数据库连接
- 注册MCP工具
- 启动HTTP服务器
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, Request, Response
from loguru import logger
from pydantic import BaseModel

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入MySQL MCP模块
from mysql_mcp.database import MySQLDatabase
from mysql_mcp.tools import register_tools
from mysql_mcp.security import SecurityManager

# 创建FastAPI应用
app = FastAPI(title="MySQL MCP Server", description="Trae AI的MySQL数据库集成服务器")

# 全局变量
config: Dict[str, Any] = {}
database: Optional[MySQLDatabase] = None
security: Optional[SecurityManager] = None


class MCPRequest(BaseModel):
    """MCP请求模型"""
    query: str
    parameters: Dict[str, Any] = {}


class MCPResponse(BaseModel):
    """MCP响应模型"""
    result: Any
    error: Optional[str] = None


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        raise


def setup_logging(config: Dict[str, Any]) -> None:
    """设置日志"""
    log_config = config.get("logging", {"level": "INFO", "file": "mysql_mcp.log"})
    log_level = log_config.get("level", "INFO")
    log_file = log_config.get("file", "mysql_mcp.log")
    
    logger.remove()  # 移除默认处理器
    logger.add(sys.stderr, level=log_level)
    logger.add(log_file, rotation="10 MB", level=log_level)


def init_database(config: Dict[str, Any]) -> MySQLDatabase:
    """初始化数据库连接"""
    db_config = config.get("database", {})
    return MySQLDatabase(
        host=db_config.get("host", "localhost"),
        port=db_config.get("port", 3306),
        user=db_config.get("user", "root"),
        password=db_config.get("password", ""),
        database=db_config.get("database", "test")
    )


def init_security(config: Dict[str, Any]) -> SecurityManager:
    """初始化安全管理器"""
    security_config = config.get("security", {})
    return SecurityManager(
        allowed_tables=security_config.get("allowed_tables", []),
        allowed_operations=security_config.get("allowed_operations", ["SELECT", "SHOW", "DESCRIBE"]),
        max_rows=security_config.get("max_rows", 1000),
        timeout_seconds=security_config.get("timeout_seconds", 30)
    )


@app.on_event("startup")
async def startup_event():
    """服务器启动事件"""
    global config, database, security
    
    # 加载配置
    config = load_config()
    
    # 设置日志
    setup_logging(config)
    logger.info("MySQL MCP Server 正在启动...")
    
    # 初始化数据库连接
    try:
        database = init_database(config)
        logger.info("数据库连接初始化成功")
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        raise
    
    # 初始化安全管理器
    security = init_security(config)
    logger.info("安全管理器初始化成功")
    
    # 注册MCP工具
    try:
        tool_registry = register_tools(database, security)
        logger.info(f"已成功注册 {len(tool_registry.tools)} 个MCP工具")
    except Exception as e:
        logger.error(f"注册MCP工具失败: {e}")
        raise
    
    logger.info("MySQL MCP Server 启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """服务器关闭事件"""
    global database
    
    logger.info("MySQL MCP Server 正在关闭...")
    
    # 关闭数据库连接
    if database:
        database.close()
        logger.info("数据库连接已关闭")
    
    logger.info("MySQL MCP Server 已关闭")


@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """处理MCP请求"""
    global database, security
    
    logger.info(f"收到MCP请求: {request.query}")
    
    try:
        # 验证请求
        if not security.validate_query(request.query):
            return MCPResponse(result=None, error="查询操作不被允许")
        
        # 执行查询
        result = database.execute_query(request.query, security.max_rows)
        
        return MCPResponse(result=result)
    except Exception as e:
        logger.error(f"处理MCP请求失败: {e}")
        return MCPResponse(result=None, error=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    global database
    
    try:
        # 检查数据库连接
        if database and database.is_connected():
            return {"status": "healthy", "database": "connected"}
        else:
            return {"status": "unhealthy", "database": "disconnected"}
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.get("/schema")
async def get_schema():
    """获取数据库模式"""
    global database, security
    
    try:
        # 获取数据库模式
        schema = database.get_schema(security.allowed_tables)
        return {"schema": schema}
    except Exception as e:
        logger.error(f"获取数据库模式失败: {e}")
        return {"error": str(e)}


def main():
    """主函数"""
    # 加载配置
    config = load_config()
    server_config = config.get("server", {})
    
    # 启动服务器
    uvicorn.run(
        "server:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        reload=server_config.get("debug", False)
    )


if __name__ == "__main__":
    main()