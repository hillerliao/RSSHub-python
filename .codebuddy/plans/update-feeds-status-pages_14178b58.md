---
name: update-feeds-status-pages
overview: 更新 /feeds 和 /status 页面，添加蛋卷基金调仓动态 (danjuan/departure) feed 的文档说明和状态检查
todos:
  - id: explore-project
    content: 使用 [subagent:code-explorer] 探索项目结构，定位 /feeds 和 /status 页面文件
    status: completed
  - id: add-feed-doc
    content: 在 /feeds 页面添加 danjuan/departure feed 的使用文档
    status: completed
    dependencies:
      - explore-project
  - id: add-status-check
    content: 在 /status 页面添加 danjuan/departure feed 的状态检查条目
    status: completed
    dependencies:
      - explore-project
  - id: verify-functionality
    content: 验证文档显示和状态检查功能正常工作
    status: completed
    dependencies:
      - add-feed-doc
      - add-status-check
---

## 产品概述

在 RSSHub-python 项目中为蛋卷基金调仓动态 (danjuan/departure) feed 添加文档说明和状态监控

## 核心功能

- 在 /feeds 页面添加 danjuan/departure feed 的使用文档
- 在 /status 页面添加该 feed 的状态检查条目
- 确保新 feed 的可用性监控和用户文档完整

## 技术栈

- 保持项目现有技术栈（Python）

## 技术架构

### 系统架构

- 依托现有 RSSHub-python 项目架构
- 路由：/feeds 页面和 /status 页面

### 模块划分

- **文档模块**：维护 feeds 文档列表
- **监控模块**：维护各 feed 的健康状态检查

### 数据流

Feed 请求 → 状态检查脚本 → /status 页面展示监控结果
用户访问 /feeds → 读取 feed 文档 → 展示使用说明

## 实现细节

### 核心目录结构

由于是现有项目更新，仅展示可能需要修改的文件：

```
project-root/
├── routes/
│   └── danjuan/
│       └── departure.py  # 已存在的 feed 实现
├── docs/              # 或文档相关目录
│   └── feeds.md       # 或 feeds 文档文件
├── routes/
│   └── status.ts      # 或 status 页面路由
└── lib/
    └── status.js      # 或状态检查逻辑
```

### 关键代码结构

**Feed 文档条目**：描述 danjuan/departure feed 的使用方法、参数说明和示例

**状态检查配置**：添加该 feed 到状态监控列表，定义检查方式和失败阈值

## Agent Extensions

### SubAgent

- **code-explorer**
- 用途：探索 RSSHub-python 项目结构，定位 /feeds 和 /status 页面的实现位置
- 预期结果：找到需要修改的具体文件路径和实现方式