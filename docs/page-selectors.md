# 页面定位契约

本文件记录在抖音网页版（`https://www.douyin.com/chat?isPopup=1`）上实测通过的定位规则。页面改版后，按本文件逐项复核，改完再跑发送流程。

## 登录态

只看会话级 Cookie：`sessionid`、`sid_tt`、`sessionid_ss`。

`passport_csrf_token`、`ttwid`、`UIFID` 这类匿名 Cookie 在未登录时同样存在，用它判断登录状态会得到假阳性，进而把「未登录」当成「已登录」去发消息，全部失败。

未登录时首页会出现「使用原设备扫码」安全验证，扫码通过后会话 Cookie 才会写入。

## 会话列表

| 目标 | 定位 |
| --- | --- |
| 会话项 | `[class*="conversationConversationItemwrapper"]` |
| 昵称 | `[class*="conversationConversationItemtitle"]` 的文本第一行 |
| 火花容器 | `[class*="commonStreakstreakContainer"]` |
| 火花天数 | `[class*="commonStreaknormalText"]` |

昵称节点里会混入火花天数与相对时间，例如 `想纵容你的坏\n59\n10分钟前`。取第一行，否则用整段文本去点会超时。

## 虚拟滚动

列表只渲染可视区附近十几项，直接 `scrollIntoView` 到底会漏掉大量会话。实测一个账号有 248 个会话，首屏只出 14 到 17 个。

正确做法：

1. 向上找到滚动容器：从第一个会话项往上遍历祖先，取第一个 `overflowY` 为 `auto` 或 `scroll` 且 `scrollHeight > clientHeight` 的节点，打标记 `data-spark-scroller`。
2. 把 `scrollTop` 归零，每次加 340 像素，每步收集一次当前渲染的会话并去重累加，直到滚到底。
3. 定位某个会话时，同样从头按步进滚动，命中昵称后再校验该项 `getBoundingClientRect()` 落在可视区，才点击。

## 输入与发送

| 目标 | 定位 |
| --- | --- |
| 输入框 | `div[contenteditable='true']`，页面可能有多个，取最后一个 |
| 发送按钮 | `svg.messageMsgInputpublishBtn` |
| 消息气泡 | `.messageMessageBoxcontentBox` |

输入框清空判定要去掉零宽字符：`inner_text().replace("\u200b", "").strip()`。发送后残留一个 `\u200b` 是正常的，按原样判空会把成功当失败。

## 比心的两条路径

**可用：文本码。** 在输入框键入 `[比心]` 再点发送，客户端把它渲染成比心表情，会话预览也变成 `[比心]`。

**不可用：表情面板。** 入口 `svg.messageMsgInputiconAction` 能正常打开面板，面板第一组是「续火花」，第二个表情就是比心。但面板是 `semi-modal` 结构，面板内表情项的合成点击与真实鼠标点击都不触发插入，输入框 DOM 完全不变。`elementFromPoint` 命中的确实是那张表情图，说明不是遮挡问题，是事件绑定问题。

## 发送结果校验

发送前后各取一次 `.messageMessageBoxcontentBox` 的数量与最后一项的尾部 HTML。数量增加或尾部变化，才算发出。仅看输入框是否清空不足以判定，因为空消息发送同样会清空输入框。

## 当日去重

发送成功即写入 `heart_ledger.json`，结构为 `{"YYYY-MM-DD": ["会话名", ...]}`。重复运行先读这份记录，已发过的直接跳过，避免同一天连发多条把「续火花」变成刷屏。
