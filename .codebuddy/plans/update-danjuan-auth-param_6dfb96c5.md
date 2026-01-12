---
name: update-danjuan-auth-param
overview: 修改danjuan departure RSS节点的认证参数，从cookie参数改为accesstoken参数，简化用户使用方式。
todos:
  - id: search-danjuan-code
    content: 使用 [subagent:code-explorer] 搜索项目中danjuan departure相关的代码文件
    status: completed
  - id: analyze-auth-logic
    content: 分析当前cookie认证逻辑的实现方式
    status: completed
    dependencies:
      - search-danjuan-code
  - id: modify-auth-param
    content: 将认证参数从cookie字典改为单一accesstoken参数
    status: completed
    dependencies:
      - analyze-auth-logic
  - id: update-api-call
    content: 简化API调用请求头构造逻辑
    status: completed
    dependencies:
      - modify-auth-param
  - id: update-documentation
    content: 更新函数文档和参数说明
    status: completed
    dependencies:
      - update-api-call
---

## Product Overview

修改danjuan departure RSS节点的认证机制，将复杂的cookie参数简化为accesstoken参数，提升用户配置便利性。

## Core Features

- 将认证方式从多个cookie参数简化为单一accesstoken参数
- 优化参数命名，使API调用更加直观简洁
- 保持原有RSS数据输出功能不变

## Tech Stack

- **语言**: Python (基于现有项目RSSHub-python)
- **框架**: 保持项目现有架构（通常是Flask或FastAPI）

## Tech Architecture

### 现有项目修改

- **目标文件定位**: 需要找到danjuan departure相关的RSS路由文件
- **修改范围**: 仅修改认证参数获取和验证逻辑
- **数据流保持**: RSS输出逻辑不变，仅改变输入参数

### 代码变更点

- 参数接收层: 从接收cookie字典改为接收accesstoken字符串
- API调用层: 使用accesstoken构造请求头替代cookie传递
- 文档更新: 更新参数说明文档

## Implementation Details

### 修改前后对比

**修改前 (Cookie方式)**:

```python
# 可能的实现
def get_danjuan_rss(cookie_dict):
    headers = {'Cookie': f"accesstoken={cookie_dict.get('accesstoken')}"}
    # ... 其他cookie参数
```

**修改后 (AccessToken方式)**:

```python
def get_danjuan_rss(accesstoken):
    headers = {'Cookie': f"accesstoken={accesstoken}"}
    # 直接使用accesstoken
```

### 关键步骤

1. 定位danjuan departure相关的路由文件
2. 修改函数签名，将cookie参数改为accesstoken参数
3. 简化请求头构造逻辑
4. 更新路由参数绑定和文档注释

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 搜索并定位RSSHub-python项目中danjuan departure相关的代码文件
- Expected outcome: 找到包含danjuan departure RSS节点实现的具体文件路径和函数