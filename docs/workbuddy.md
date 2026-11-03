# WorkBuddy 集成说明

本文档说明本项目如何接入 WorkBuddy 环境。使用者需要先阅读 README.md 的快速开始章节。

## 三层结构

| 层 | 位置 | 职责 |
| --- | --- | --- |
| 调度层 | WorkBuddy 定时任务 | 每天固定时间唤起一次任务 |
| 执行层 | `integrations/workbuddy/SKILL.md` | 指引 AI 打开抖音网页版聊天页并逐个发送消息 |
| 状态层 | `douyin_spark` 命令行程序 | 清单、当日去重、消息轮换、读数回写、报告 |

## 安装技能

使用者把 `integrations/workbuddy/SKILL.md` 复制到 `~/.workbuddy/skills/douyin-spark/SKILL.md`。Windows 环境下该路径为 `C:\Users\<用户名>\.workbuddy\skills\douyin-spark\SKILL.md`。

复制后，使用者需要把文件里的 `PROJECT_ROOT` 全部替换为本仓库的绝对路径。技能生效后，使用者可以说「帮我续火花」「查看火花联系人列表」「把 XXX 加到火花联系人」。

## 前置条件

1. 使用者在 WorkBuddy 设置里开启浏览器控制能力。
2. 使用者在本机 Chrome 或 Edge 中登录抖音网页版。
3. 使用者在仓库根目录能执行 `python -m douyin_spark --help`。

任一项不满足时，技能停止执行并报告原因。项目不检测浏览器控制能力的开关状态，也不接管登录流程。

## 定时任务参数

| 字段 | 取值 |
| --- | --- |
| scheduleType | `recurring` |
| rrule | `FREQ=DAILY;BYHOUR=21;BYMINUTE=0` |
| status | `ACTIVE` |
| cwds | 仓库绝对路径 |

提示词原文见 `integrations/workbuddy/AUTOMATION.md`。提示词自包含仓库路径、命令序列与失败即停条件。

定时任务一旦启用，就会每天自动向好友发送消息。启用动作由使用者决定，项目不会自动启用它。

## 执行流程

1. 技能运行 `python -m douyin_spark plan` 取今日待发名单。
2. 技能打开 `https://www.douyin.com/chat?isPopup=1`，按浏览器快照现场定位会话。
3. 技能把会话列表整理成快照 JSON，运行 `python -m douyin_spark snapshot --file ... --apply` 导入读数。字段规范见 `docs/snapshot-contract.md`，页面改版只需重新生成快照。
4. 技能对每个会话运行 `python -m douyin_spark next` 取消息并发送，每人每天一条，间隔 1 到 2 秒。发送失败时运行 `fail` 记录原因，当日失败达到阈值后 `plan` 自动熔断。
5. 技能运行 `mark` 记录成功发送，运行 `digest` 生成当日日报。
6. 技能运行 `report` 汇报结果。任一环节失败时立即停止，不重试、不重复发送。

## 故障排查

| 现象 | 处理 |
| --- | --- |
| 技能没有被加载 | 确认 SKILL.md 位于用户级技能目录，且 frontmatter 中 name 为 `douyin-spark`；重启 WorkBuddy 后重试 |
| 页面会话定位失败 | 抖音页面结构变化，按浏览器快照重新校准定位，不要修改状态层代码 |
| 提示未登录 | 在本机浏览器重新登录抖音网页版 |
| `plan` 名单为空 | 运行 `add` 添加联系人，或运行 `status` 确认今天已全部发送 |
| 状态文件异常 | 备份后删除 `config/state.json`，程序会在下次写入时重建 |

## 相关说明

灰色火花、彩色火花、重燃中 X/3 三类状态描述来自第三方技能页面 (bazg3452-del, "douyin-spark")。本项目只把它们当作可记录字段，不把它们写成计算规则，也不把它们当作平台官方公告。
