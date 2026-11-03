---
name: douyin-spark
description: "在 WorkBuddy 环境里为抖音私信联系人每日续火花。识别带火花的会话、逐个发送自定义消息、维护联系人清单、按页面读数回写状态、追踪重燃进度。当用户说「帮我续火花」「给火花联系人发消息」「续火花，说：你好呀」「查看火花联系人列表」「把 XXX 加到火花联系人」时使用。依赖当前会话的浏览器控制能力与已登录的抖音网页版。"
display_name: 抖音自动续火花
display_name_en: Douyin Spark Keeper
description_zh: "在 WorkBuddy 环境里为抖音私信联系人每日续火花。识别带火花的会话、逐个发送自定义消息、维护联系人清单、按页面读数回写状态、追踪重燃进度。当用户说「帮我续火花」「给火花联系人发消息」「续火花，说：你好呀」「查看火花联系人列表」「把 XXX 加到火花联系人」时使用。依赖当前会话的浏览器控制能力与已登录的抖音网页版。"
description_en: "Daily Douyin spark keeper for the WorkBuddy environment: detect spark conversations, send one custom message per contact, maintain the contact list, write back on-screen readings, and track reignite progress."
category: 生活工具 > 社交辅助
version: 0.1.0
agent_created: true
---

# 抖音自动续火花

## 用途

本技能为抖音私信联系人维持每日互动火花。技能负责在浏览器里完成页面操作，`PROJECT_ROOT` 下的 `douyin_spark` 命令行程序负责清单、当日去重、消息轮换、读数回写与结果汇报。

## 前置条件

1. 使用者已在 WorkBuddy 设置里开启浏览器控制能力。
2. 使用者本机 Chrome 或 Edge 中抖音网页版已登录。
3. `PROJECT_ROOT` 已替换为仓库绝对路径，且该目录下可执行 `python -m douyin_spark --help`。

任一项不满足时，本技能停止执行并报告原因，不尝试绕过登录或风控。

## 何时使用

- 「帮我续火花」
- 「给火花联系人发消息」
- 「续火花，说：你好呀」
- 「查看火花联系人列表」
- 「把 XXX 加到火花联系人」

## 执行流程

1. 本技能在 `PROJECT_ROOT` 下运行 `python -m douyin_spark plan`，取得今日尚未发送的联系人名单。名单为空时，本技能直接运行 `python -m douyin_spark status` 并结束。
2. 本技能用浏览器控制能力打开 `https://www.douyin.com/chat?isPopup=1`，获取当前会话列表快照，逐项定位名单中的会话。
3. 本技能把会话列表整理成快照 JSON，运行 `python -m douyin_spark snapshot --file 快照文件 --apply` 导入读数。本技能不硬编码页面元素，字段规范见 `docs/snapshot-contract.md`，页面改版时重新生成快照即可。
4. 本技能对每个待发会话运行 `python -m douyin_spark next` 取一条消息，在会话输入框输入并发送。每个会话每天只发一条，相邻两次发送间隔 1 到 2 秒。使用者指定消息内容时，本技能改用使用者给出的内容。发送失败时，本技能运行 `fail` 记录原因，当日失败达到阈值后 `plan` 自动熔断。
5. 每发送成功一个，本技能运行 `python -m douyin_spark mark "联系人" --text "实际发送内容"` 记录。全部完成后，本技能运行 `digest` 生成当日日报。
6. 本技能运行 `python -m douyin_spark report`，按表格汇报每个联系人的火花天数、状态、重燃进度与今日发送结果。任一环节失败时，本技能立即停止，不重试、不重复发送。

## 状态与命令

| 目的 | 命令 |
| --- | --- |
| 查看清单 | `python -m douyin_spark list` |
| 添加联系人 | `python -m douyin_spark add "名字" --days 93 --status 彩色` |
| 移除联系人 | `python -m douyin_spark remove "名字"` |
| 导入快照 | `python -m douyin_spark snapshot --file 快照文件 --apply` |
| 今日待发 | `python -m douyin_spark plan` |
| 取下一条消息 | `python -m douyin_spark next` |
| 记录已发 | `python -m douyin_spark mark "名字" --text "内容"` |
| 记录失败 | `python -m douyin_spark fail "名字" --reason "原因"` |
| 回写读数 | `python -m douyin_spark set "名字" --days 93 --status 彩色` |
| 今日状态 | `python -m douyin_spark status` |
| 生成日报 | `python -m douyin_spark digest` |
| 结果汇报 | `python -m douyin_spark report` |

状态文件位于 `PROJECT_ROOT/config/state.json`，消息模板位于 `PROJECT_ROOT/config/messages.json`。两者都不进入版本库。

## 限流与边界

- 本技能不硬编码页面元素引用，每次按浏览器快照现场定位。页面改版时重新校准定位即可。
- 本技能不使用相同内容连续发送，消息由模板轮换产生。群聊同样可以带火花，名单里出现群聊时按同一流程处理。
- 本技能不读取账号密码、Cookie 或 Token，不写入任何凭据，不提供绕过登录、验证码与平台风控的能力。
- 火花状态与重燃规则来自第三方技能页面描述 (bazg3452-del, "douyin-spark")，本技能只记录页面读数，不把它们当作平台官方规则。
