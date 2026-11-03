# 更新日志

本文件记录 douyin-spark-keeper 的版本变更，格式遵循 Keep a Changelog，版本号遵循语义化版本。

## [0.1.0] - 2026-11-03

### 新增

- 三层结构：WorkBuddy 定时任务、WorkBuddy 技能、本地命令行程序。
- 联系人清单管理：`add`、`remove`、`list`。
- 每日去重：`plan` 列出待发联系人，`mark` 记录当日已发送，跨天自动重置。
- 消息模板轮换：`next` 按模板池取消息并避开上一条内容。
- 页面读数回写：`set` 记录火花天数、状态与重燃进度，程序不自行推算。
- 结果汇报：`status` 与 `report`。
- WorkBuddy 技能定义与每日定时任务配置，位于 `integrations/workbuddy/`。
- 使用文档与命令参考，位于 `docs/`。
- 单元测试与命令行端到端冒烟测试，覆盖快照、熔断与日报。
- GitHub Actions 测试工作流，覆盖 Python 3.10 至 3.13。
- 快照契约：`snapshot` 两阶段导入会话读数，页面改版不影响状态层。
- 熔断机制：`fail` 记录失败，当日失败达到阈值后 `plan` 自动停止。
- 每日日报：`digest` 生成可归档的 Markdown 日报。
- MIT 许可证、贡献指南、Issue 与 Pull Request 模板。

[0.1.0]: https://github.com/boreyaa/douyin-spark-keeper/releases/tag/v0.1.0
