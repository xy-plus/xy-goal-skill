# xy-goal

一个 Claude Code skill：给长任务「设目标」补上两件事——
**每 10～30 分钟定时自查一次**，防止做到一半停下；**关掉提醒前必须由子代理验收**，防止自己判自己做完。

目标清单和你的原话会落盘到 `~/.claude/xy-goal/`：上下文被压缩、换了子代理，核对的都是同一份事实。

## 安装

```bash
git clone https://github.com/xy-plus/xy-goal-skill.git ~/.claude/skills/xy-goal
```

需要带定时任务工具（`CronCreate` / `CronList` / `CronDelete`）的 Claude Code。

## 怎么用

输入 `/xy-goal` 或明确说「用 xy-goal」，再说目标。只在明确要求时生效，不会自动触发。

启动、清理、验收、关闭四步的完整规则见 [`SKILL.md`](SKILL.md)。
