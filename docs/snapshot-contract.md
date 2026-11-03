# 快照契约

本文档定义浏览器层与状态层之间的数据格式。这份契约是本项目与已有续火花方案的主要区别。

## 问题

已有方案把页面定位写进执行层：技能包使用固定的元素引用，油猴脚本维护选择器表，安卓模块直接读取宿主进程的会话对象 (bazg3452-del, "douyin-spark"; dr-190, "ScriptCat-Douyin-Fire-Helper"; WorldMargin, "SparkFlame")。页面结构或宿主接口变化时，执行层与状态层需要一起改。

本项目把两层之间的数据固定成一份与页面无关的 JSON。浏览器层负责「看见什么」，状态层只消费这份 JSON。页面改版只影响浏览器层如何生成快照。

## 格式

```json
{
  "version": 1,
  "captured_at": "2026-11-03T21:00:00",
  "conversations": [
    {
      "name": "好友甲",
      "spark_days": 93,
      "status": "彩色",
      "reignite_progress": ""
    },
    {
      "name": "好友乙",
      "spark_days": 2,
      "status": "重燃中",
      "reignite_progress": "2/3"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `version` | 整数 | 否 | 契约版本，当前为 1 |
| `captured_at` | 字符串 | 否 | 快照采集时间，仅作记录 |
| `conversations` | 数组 | 是 | 会话列表 |
| `conversations[].name` | 字符串 | 是 | 页面显示的会话名称，作为唯一键 |
| `conversations[].spark_days` | 整数 | 否 | 页面显示的火花天数 |
| `conversations[].status` | 字符串 | 否 | `彩色`、`灰色`、`重燃中`、`未标注` 四选一 |
| `conversations[].reignite_progress` | 字符串 | 否 | 页面显示的重燃进度，例如 `2/3` |

完整示例见 `config/snapshot.example.json`。

## 校验规则

`snapshot` 命令按以下顺序校验，任一条不通过就拒绝导入且不写入状态：

1. 顶层必须是对象。
2. `conversations` 必须是数组。
3. 每个条目必须有非空 `name`。
4. `status` 出现时必须属于四个取值。
5. `spark_days` 出现时必须能转为整数。

## 两阶段导入

```bash
python -m douyin_spark snapshot --file snapshot.json
python -m douyin_spark snapshot --file snapshot.json --apply
```

第一阶段只校验并输出会话数量，不修改状态。第二阶段才把读数写入 `config/state.json`：名称不存在的会话新增，已存在的会话更新字段。写入后状态里会追加一条快照记录，包含采集时间、会话数、新增数与更新数。

程序不推算火花天数与重燃进度。字段值一律来自页面显示，缺失的字段保持原值。

## 生成快照

浏览器层可以用任意方式产出符合上述格式的 JSON，例如浏览器快照转写、页面文本解析或人工填写。项目不限制生成方式，也不提供页面选择器。字段来源与准确性由采集方负责。
