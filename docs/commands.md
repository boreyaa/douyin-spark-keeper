# 命令参考

所有命令在仓库根目录执行。程序只用 Python 标准库，需要 Python 3.10 及以上。

## 全局参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--state PATH` | `config/state.json` | 状态文件路径 |
| `--templates PATH` | `config/messages.json` | 消息模板文件路径 |

模板文件不存在时，程序使用 `douyin_spark/messages.py` 里的内置模板池。

## 联系人管理

```bash
python -m douyin_spark list
python -m douyin_spark add "好友昵称" --days 93 --status 彩色
python -m douyin_spark add "好友昵称" --days 2 --status 重燃中 --progress 2/3
python -m douyin_spark remove "好友昵称"
```

`--status` 可选值为 `彩色`、`灰色`、`重燃中`、`未标注`。`--progress` 记录页面显示的重燃进度。

## 每日执行

```bash
python -m douyin_spark plan
python -m douyin_spark next
python -m douyin_spark mark "好友昵称" --text "早呀"
python -m douyin_spark set "好友昵称" --days 94 --status 彩色
python -m douyin_spark status
python -m douyin_spark report
python -m douyin_spark snapshot --file snapshot.json --apply
python -m douyin_spark fail "好友昵称" --reason "页面未找到会话"
python -m douyin_spark digest
```

| 命令 | 行为 |
| --- | --- |
| `plan` | 列出今日尚未发送的联系人，跨天清空已发名单；熔断时返回空名单 |
| `next` | 从模板池取下一条消息，避开上一条内容，并推进模板游标；加 `--text "[比心]"` 则固定发这一条 |
| `mark` | 记录当日已发送，同一联系人当天不重复记录，不修改火花天数 |
| `fail` | 记录一次失败与原因，累计达到阈值后 `plan` 自动熔断 |
| `snapshot` | 校验快照；追加 `--apply` 才写入状态，字段规范见 `docs/snapshot-contract.md` |
| `digest` | 生成 Markdown 日报，默认写入 `reports/<日期>.md`，可用 `--out` 指定 |
| `set` | 按页面实际读数更新字段，程序不推算 |
| `status` | 显示日期、已发数、待发数、失败数、熔断状态、上一条消息 |
| `report` | 输出可汇报的表格 |
| `dump` | 输出完整状态 JSON |

## 状态文件结构

```json
{
  "version": 1,
  "last_date": "2026-11-03",
  "sent_today": ["好友昵称"],
  "last_text": "早呀",
  "template_index": 3,
  "contacts": [
    {
      "name": "好友昵称",
      "spark_days": 93,
      "status": "彩色",
      "reignite_progress": "",
      "note": ""
    }
  ],
  "history": [
    {"date": "2026-11-03", "name": "好友昵称", "text": "早呀"}
  ]
}
```

`config/state.json` 与 `config/messages.json` 已被 `.gitignore` 排除，使用者不要把它们提交到公开仓库。

## 测试

```bash
python -m unittest discover -s tests -v
```

测试覆盖空状态、增删联系人、跨天重置、当日去重、模板不重复、读数更新与命令行端到端流程。
