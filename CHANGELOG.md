# 更新日志

本文件记录 douyin-spark-keeper 的版本变更，格式遵循 Keep a Changelog，版本号遵循语义化版本。

## [0.3.0] - 2026-11-03

### 新增

- 独立运行器 `runner/douyin_spark_daily.py`：不依赖宿主应用，自己枚举会话、发送、记当日账，配置外置到 `config/runner.json`。支持 `--headed`、`--dry-run`、`--only`、`--limit`。
- 外壳脚本 `runner/run_daily.bat`：无头优先，退出码大于等于 2 时自动有头重跑一次。
- 定时任务独立说明 `docs/scheduling.md`：每小时守卫式调度、系统开机任务、退出码语义、日志排错、三道防重复的闸。
- 排除名单机制：`config/exclude.json` 里的会话不发也不计失败，示例文件 `config/exclude.example.json`，个人名单不入库。
- 发送结果校验口径：输入框已清空且会话预览出现 `[比心]`，不再依赖消息气泡数量。

### 变更

- 发送内容默认收敛为一个 `[比心]` 表情，不再使用寒暄模板。
- 技能定义与定时任务参数卡按实测结论重写：去掉固定时刻调度，改为守卫式；补上无头模式、虚拟滚动遍历、表情面板不可用的结论。

### 修复

- 会话列表为虚拟滚动时只抓首屏会漏大量会话。
- 消息区同为虚拟列表，条数可能不变，旧的条数校验会把已成功的发送误判为失败。

[0.3.0]: https://github.com/boreyaa/douyin-spark-keeper/releases/tag/v0.3.0
[0.2.0]: https://github.com/boreyaa/douyin-spark-keeper/releases/tag/v0.2.0

### 新增

- `next --text TEXT` 固定发送内容，续火花场景可以只发一个 `[比心]`。
- 页面定位契约文档 `docs/page-selectors.md`：实测通过的会话项、火花容器、输入框、发送按钮定位，虚拟滚动遍历方法，登录态判定口径，以及比心表情两条路径的实测结论。
- 发送结果校验口径：以消息气泡数量与最后一项变化为准，不看输入框是否清空。

### 修复

- 会话列表为虚拟滚动时，只抓首屏会漏掉大量会话；改为按 340 像素步进滚动并去重累加。
- 火花昵称节点混入天数与相对时间，取文本第一行再做匹配。

[0.2.0]: https://github.com/boreyaa/douyin-spark-keeper/releases/tag/v0.2.0

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
