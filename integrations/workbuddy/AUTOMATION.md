# WorkBuddy 每日定时任务参数

项目根目录：`PROJECT_ROOT`，启用前请替换为仓库绝对路径。

| 字段 | 取值 |
| --- | --- |
| scheduleType | `recurring` |
| rrule | `FREQ=DAILY;BYHOUR=21;BYMINUTE=0` |
| status | `ACTIVE` |
| cwds | 仓库绝对路径 |

提示词原文：

```
在 PROJECT_ROOT 项目中执行抖音每日续火花任务。先加载 douyin-spark 技能，运行 python -m douyin_spark plan 取今日待发名单，若返回熔断提示则立即停止。用浏览器控制能力打开抖音网页版聊天页，把会话列表整理成快照 JSON，运行 python -m douyin_spark snapshot --file 快照文件 --apply 导入读数。对名单中每个联系人发送一条由 python -m douyin_spark next 生成的消息，每发一条间隔 1 到 2 秒。发送成功运行 python -m douyin_spark mark 记录，发送失败运行 python -m douyin_spark fail 记录原因。全部完成后运行 python -m douyin_spark digest 生成日报，并运行 python -m douyin_spark report 输出本次结果。若浏览器控制能力不可用、抖音网页版未登录或任一环节失败，立即停止并报告原因，不要重试、不要重复发送。
```

启用前需要确认两项前置条件：WorkBuddy 设置里的浏览器控制能力已开启；本机 Chrome 或 Edge 中抖音网页版已登录。定时任务一旦启用就会每天向外发送消息，启用动作由使用者决定。
