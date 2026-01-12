---
name: fix-portfolio-info-parsing
overview: 修复组合信息API解析错误，正确提取tp_plan_name（组合名称）和dynamic_text（简介）字段
todos:
  - id: search-api-code
    content: Use [subagent:code-explorer] to locate API response parsing code for portfolio info
    status: completed
  - id: fix-data-access
    content: Modify data access path from data.level to data.plan_info and data.plan_desc levels
    status: completed
    dependencies:
      - search-api-code
  - id: verify-output
    content: Verify RSS output displays correct portfolio name and description
    status: completed
    dependencies:
      - fix-data-access
---

## Product Overview

修复RSSHub项目中组合信息API的数据解析错误

## Core Features

- 修正API响应数据的层级访问路径
- 正确提取tp_plan_name字段（从data.plan_info层级获取）
- 正确提取dynamic_text字段（从data.plan_desc层级获取）
- 确保RSS channel title显示正确的组合名称而非默认策略ID

## Tech Stack

- 现有技术栈：Python + FastAPI（RSSHub-python项目）
- 保持现有架构，仅修改数据解析逻辑

## Tech Architecture

### System Architecture

- **范围**：局部修改，仅涉及API响应解析模块
- **遵循原则**：优先代码复用，基于现有项目逻辑进行精确修复

### Implementation Details

### Core Directory Structure

仅显示需要修改或检查的文件：

```
project-root/
├── lib/              # 可能包含API解析逻辑的工具库
├── routes/           # RSS路由定义
│   └── portfolio.py  # 组合信息相关的路由处理
└── utils/            # 辅助函数，可能包含数据解析
```

### Key Code Structures

**数据结构修正**：

```python
# 错误的实现（当前）
plan_name = data.get('tp_plan_name', '策略' + plan_id)
description = data.get('dynamic_text', '')

# 正确的实现（修复后）
plan_name = data.get('plan_info', {}).get('tp_plan_name', '策略' + plan_id)
description = data.get('plan_desc', {}).get('dynamic_text', '')
```

### Technical Implementation Plan

1. **问题定位**：查找组合信息API响应处理代码
2. **逻辑修正**：将data层级访问改为data.plan_info和data.plan_desc层级访问
3. **验证测试**：确认RSS输出显示正确的组合名称和简介

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 搜索并定位包含组合信息API解析逻辑的代码文件
- Expected outcome: 找到处理tp_plan_name和dynamic_text字段的具体代码位置