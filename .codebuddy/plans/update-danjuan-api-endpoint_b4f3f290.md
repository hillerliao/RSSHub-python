---
name: update-danjuan-api-endpoint
overview: 修改danjuan departure RSS节点，使用新的API接口获取组合名称和简介信息。
todos:
  - id: search-danjuan-code
    content: 使用[code-explorer]搜索并定位danjuan相关的代码文件
    status: completed
  - id: analyze-api-logic
    content: 分析现有API调用逻辑和数据处理代码
    status: completed
    dependencies:
      - search-danjuan-code
  - id: update-api-endpoint
    content: 修改API端点URL至新的danjuan接口地址
    status: completed
    dependencies:
      - analyze-api-logic
  - id: extract-new-fields
    content: 添加逻辑提取portfolio_name和portfolio_intro字段
    status: completed
    dependencies:
      - update-api-endpoint
  - id: update-rss-output
    content: 在RSS生成逻辑中添加组合名称和简介显示
    status: completed
    dependencies:
      - extract-new-fields
---

## Product Overview

修改RSSHub-python中的蛋卷基金（danjuan）RSS节点，使用新的API接口获取组合名称和简介信息。

## Core Features

- 更新API端点至 https://danjuanfunds.com/djapi/fundx/portfolio/ic/plan/info
- 从新接口提取组合名称（portfolio_name）和简介（portfolio_intro）
- 在RSS输出的标题或描述中显示组合名称和简介信息

## Tech Stack

- 后端框架: Python (RSSHub-radar)
- 数据获取: HTTP请求 (requests/urllib)

## Tech Architecture

### System Architecture

- 架构模式: RSS路由 + 数据获取器模式
- 现有项目代码结构，遵循RSSHub-python规范

### Module Division

- **Routes Module**: 路由定义，处理HTTP请求
- **Data Fetcher**: 从API获取数据的核心逻辑
- **RSS Generator**: 格式化RSS输出

### Data Flow

用户请求RSS → 调用danjuan路由 → 请求新API → 提取组合名称和简介 → 生成RSS响应

## Implementation Details

### Key Code Structures

**API响应数据结构**: 新接口返回的JSON结构包含组合名称和简介字段

```python
# 预期的API响应结构
{
    "data": {
        "portfolio_name": "组合名称",
        "portfolio_intro": "组合简介",
        # ...其他字段
    }
}
```

**修改核心逻辑**: 更新API端点URL，添加数据提取逻辑

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 在RSSHub-python代码库中搜索和定位danjuan相关的代码文件
- Expected outcome: 找到包含danjuan路由定义和API调用的具体文件位置和代码段