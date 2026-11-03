---
name: douyin-spark
description: "为抖音私信里带火花的会话每日发送一个「比心」表情，只发表情不发文字。识别火花会话、遍历虚拟滚动列表、按当日记录去重、跳过排除名单、汇报发送结果。当用户说「帮我续火花」「给有火花的都续上」「续火花，发个比心」「查看火花会话列表」时使用。依赖浏览器控制能力与已登录的抖音网页版。"
display_name: 抖音自动续火花
display_name_en: Douyin Spark Keeper
description_zh: "为抖音私信里带火花的会话每日发送一个「比心」表情，只发表情不发文字。识别火花会话、遍历虚拟滚动列表、按当日记录去重、跳过排除名单、汇报发送结果。当用户说「帮我续火花」「给有火花的都续上」「续火花，发个比心」「查看火花会话列表」时使用。依赖浏览器控制能力与已登录的抖音网页版。"
description_en: "Send exactly one heart emoji per spark conversation on Douyin every day. Detect spark rows, traverse the virtualized list, dedupe by a daily ledger, skip an exclusion list, and report results."
category: 生活工具 > 社交辅助
version: 0.3.0
agent_created: true
---

# 抖音自动续火花

## 用途

给抖音私信里带火花（连续互动天数）的会话，每个只发一个「比心」表情，把当日火花续上。只发比心，不发任何其他文字。

## 硬规则

1. 每个会话每天只发一条，内容只有一个比心，不追加文字、不换成寒暄。
2. 登录态复用本机浏览器配置目录，不读账号密码、不写 Cookie、不碰验证码；登录失效就停下报告。
3. 只处理页面上真实显示火花的会话；「重燃中」同样算有火花。
4. 当日已发过的会话不重复发，排除名单里的会话一律不发。
5. 会话名称只在对话里出现，不写进任何仓库文件、文档或模板。

## 前置条件

1. WorkBuddy 设置里已开启浏览器控制能力。
2. 本机浏览器配置目录中抖音网页版已登录。
3. 仓库根目录可执行 `python -m douyin_spark --help`。

任一项不满足时停止执行并报告原因，不尝试绕过登录或风控。

## 执行流程

1. 打开 `https://www.douyin.com/chat?isPopup=1`，等 9 到 10 秒让列表加载完。
2. 用滚动累加的方式枚举全部会话：列表是虚拟滚动，首屏只渲染十几项，必须从顶部按 340 像素步进往下滚并去重收集，直到滚到底。会话总量可达数百，不要只用首屏。
3. 筛出带火花的会话，读火花天数一并记录。
4. 剔除排除名单与当日已发，得到本次待发名单。名单为空就直接结束，不打开会话。
5. 逐个发送：定位会话 → 点开 → 输入框键入 `[比心]` → 点发送按钮 → 校验。
6. 每成功一个写一条当日记录；失败的单独列出并重试一次，仍失败就如实报告，不换内容硬发。
7. 汇报表格：会话、火花天数、发送结果、失败原因。

## 已验证的页面定位

| 目标 | 定位 |
| --- | --- |
| 会话项 | `[class*="conversationConversationItemwrapper"]` |
| 会话昵称 | `[class*="conversationConversationItemtitle"]`，取文本第一行 |
| 火花容器 | `[class*="commonStreakstreakContainer"]` |
| 火花天数 | `[class*="commonStreaknormalText"]` |
| 输入框 | `div[contenteditable='true']`，取最后一个 |
| 发送按钮 | `svg.messageMsgInputpublishBtn` |
| 消息气泡 | `.messageMessageBoxcontentBox` |

细节与踩坑记录见仓库 `docs/page-selectors.md`。

## 比心的发法

在输入框键入 `[比心]` 后点发送，抖音客户端会渲染成比心表情，会话预览也显示 `[比心]`。这是当前唯一稳定可用的路径。

表情面板入口 `svg.messageMsgInputiconAction` 能打开面板，第一组就是「续火花」表情，第二个是比心；但面板是 semi-modal 结构，面板内表情项的合成点击与真实鼠标点击都不触发插入，编辑器 DOM 完全不变。不要走这条路。

## 发送结果校验

两处一起看，只靠一处会误判：

- 输入框是否已清空，判断前去掉零宽字符。
- 会话列表该会话的预览是否出现 `[比心]`。

不要只用消息气泡数量判断。消息区也是虚拟列表，新消息插入时会回收旧节点，条数可能一条不变，实测有条数恒定不变但消息已发出并标已读的情况。

## 排除名单

带火花但不想续的会话写进数据目录的 `exclude.json`：

```json
{"exclude": ["会话名称"]}
```

发送前先读，命中的直接跳过，不发送、不计入失败。名单是使用者个人数据，不写进仓库、文档或模板。

## 命令

状态层命令、快照契约与日报见仓库 `docs/commands.md` 与 `docs/snapshot-contract.md`。只想发比心时用：

```bash
python -m douyin_spark next --text "[比心]"
```

## 限流与边界

- 相邻两次发送间隔 1.2 秒以上。
- 页面改版时先按上表重新校准，再执行发送。
- 火花规则来自页面读数，不是平台官方文档，不做推断。
