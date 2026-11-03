# 贡献指南

感谢你愿意改进 douyin-spark-keeper。

## 报告问题

使用者可以在 GitHub Issues 提交问题 (dr-190, "ScriptCat-Douyin-Fire-Helper")。提交时请提供：

- 操作系统与 Python 版本
- WorkBuddy 版本与浏览器控制能力状态
- 复现步骤与命令原文
- `python -m douyin_spark dump` 的输出，输出中请自行隐去联系人昵称

使用者不要在 Issue 里粘贴 Cookie、Token、账号密码或真实聊天内容。

## 提交代码

1. Fork 本仓库到个人账户。
2. 创建功能分支：`git checkout -b feature/your-change`。
3. 提交改动：`git commit -m "描述改动"`。
4. 推送分支：`git push origin feature/your-change`。
5. 发起 Pull Request。

## 验证要求

提交前请在仓库根目录运行：

```bash
python -m unittest discover -s tests -v
```

新增状态字段或命令时，请同步补充 `tests/test_smoke.py` 与 `docs/commands.md`。项目代码只用 Python 标准库，新增第三方依赖需要在 Pull Request 里说明理由。

## 边界

本项目不接受以下改动：绕过登录、验证码或平台风控；读取或上传账号凭据；硬编码抖音页面元素选择器；推算火花天数与重燃进度；提高批量发送频率。相关改动会被直接关闭。
