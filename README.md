# MySQL MCP Server

这是一个基于Model Context Protocol (MCP)的MySQL数据库集成服务器，允许Trae AI智能体安全地与MySQL数据库进行交互。

## 功能特点

- 安全连接到MySQL数据库
- 执行SQL查询并返回结果
- 支持数据库模式检查
- 提供表结构和关系信息
- 配置化的访问控制
- 完整的错误处理和日志记录

## 项目结构

```
mcp-server/
├── README.md                 # 项目文档
├── requirements.txt          # 依赖项
├── config.json               # 配置文件
├── server.py                 # 主服务器入口
├── mysql_mcp/
│   ├── __init__.py
│   ├── database.py           # 数据库连接和操作
│   ├── tools.py              # MCP工具定义
│   ├── schema.py             # 数据库模式处理
│   └── security.py           # 安全和访问控制
└── tests/                    # 测试目录
    ├── __init__.py
    ├── test_database.py
    └── test_tools.py
```

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/mysql-mcp-server.git
cd mysql-mcp-server

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 配置

编辑`config.json`文件，设置数据库连接信息和访问控制：

```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "your_username",
    "password": "your_password",
    "database": "your_database"
  },
  "security": {
    "allowed_tables": ["table1", "table2"],
    "allowed_operations": ["SELECT", "INSERT", "UPDATE"],
    "max_rows": 1000
  }
}
```

## 使用方法

1. 启动MCP服务器：

```bash
python server.py
```

2. 在Trae IDE中配置MySQL MCP服务器：
   - 打开Trae IDE
   - 进入MCP市场或设置
   - 添加自定义MCP服务器，输入本地服务器URL（通常为`http://localhost:8000`）
   - 保存配置

3. 现在可以在Trae中使用MySQL智能体，执行数据库操作。

## 示例查询

在Trae中，你可以使用以下方式与MySQL MCP服务器交互：

```
@MySQL 查询所有用户表中的记录
@MySQL 创建一个新表来存储产品信息
@MySQL 分析销售数据并生成报表
```

## 安全注意事项

- 不要在生产环境中使用默认配置
- 限制数据库用户权限
- 使用允许表和操作列表来限制访问
- 定期审查日志以检测异常活动

## 许可证

MIT