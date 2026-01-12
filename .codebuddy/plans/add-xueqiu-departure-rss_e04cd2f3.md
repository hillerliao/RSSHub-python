---
name: add-xueqiu-departure-rss
overview: 在RSSHub-python项目中添加新的RSS节点，用于获取雪球投顾组合的调仓动态数据（来自蛋卷基金API），并提供RSS feed输出。
todos:
  - id: explore-project
    content: 使用[code-explorer]探索RSSHub-python项目结构和路由机制
    status: completed
  - id: create-route-file
    content: 创建雪球投顾调仓路由文件并实现API调用逻辑
    status: completed
    dependencies:
      - explore-project
  - id: implement-rss-generation
    content: 实现JSON数据到RSS feed的转换功能
    status: completed
    dependencies:
      - create-route-file
  - id: register-route
    content: 将新路由注册到应用路由表中
    status: completed
    dependencies:
      - create-route-file
  - id: integrate-test
    content: 测试RSS节点并验证输出格式
    status: completed
    dependencies:
      - implement-rss-generation
      - register-route
---

## 产品概述

在RSSHub-python项目中添加雪球投顾组合调仓动态RSS节点，通过蛋卷基金API获取投顾组合的调仓记录并提供RSS feed订阅。

## 核心功能

- 调用蛋卷基金API获取投顾组合调仓数据
- 支持strategy_code参数指定不同的投顾组合
- 将JSON数据转换为标准RSS格式
- 提供基金名称、调仓时间、调仓类型等信息
- 支持分页或按时间限制返回数据

## 技术栈

- 项目语言：Python
- HTTP请求：使用requests或aiohttp（取决于项目现有依赖）
- RSS生成：使用项目现有的RSS生成库（如feedgen）

## 技术架构

### 系统架构

基于RSSHub-python现有架构添加新路由节点，遵循项目现有的路由注册和数据获取模式。

### 模块划分

- **路由模块**：添加新的路由处理器，处理雪球投顾调仓请求
- **数据获取模块**：调用蛋卷基金API获取调仓数据
- **RSS生成模块**：将JSON数据转换为RSS feed格式

### 数据流

用户请求RSS → 路由处理器 → 调用蛋卷基金API → 解析JSON响应 → 生成RSS feed → 返回XML

## 实现细节

### 核心目录结构

```
RSSHub-python/
├── routes/                    # 路由目录（假设位置）
│   ├── xueqiu.py             # 新增：雪球相关路由
└── ...
```

### 关键代码结构

**路由处理器**：处理请求并返回RSS feed

```python
async def route_xueqiu_departure(request):
    strategy_code = request.args.get('strategy_code', 'TIA08030')
    data = await fetch_departure_data(strategy_code)
    rss = generate_rss_feed(data)
    return rss
```

**数据获取函数**：调用蛋卷基金API

```python
async def fetch_departure_data(strategy_code):
    url = "https://danjuanfunds.com/djapi/fundx/ic/activity/server/departure/scheme/list"
    params = {"strategy_code": strategy_code}
    # 实现API调用逻辑
```

**RSS生成函数**：将数据转换为RSS格式

```python
def generate_rss_feed(data):
    # 使用项目现有的RSS生成工具
    # 遍历data['data']['list']创建RSS条目
    # 包含：title（基金名称）、description（调仓信息）、link、pubDate等
```

### 技术实施计划

1. **探索项目结构**：了解RSSHub-python的路由注册机制和RSS生成方式
2. **创建路由文件**：在适当的routes目录下创建xueqiu.py文件
3. **实现API调用**：编写函数调用蛋卷基金API并处理响应
4. **实现RSS生成**：解析JSON数据并生成RSS feed
5. **注册路由**：将新路由添加到应用的路由注册表中

### 集成点

- 路由注册：与现有路由系统集成
- RSS生成：使用项目统一的RSS生成工具
- 错误处理：遵循项目现有的错误处理模式

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 探索RSSHub-python项目的目录结构和路由注册机制
- Expected outcome: 了解项目架构，确定新路由文件的位置和注册方式