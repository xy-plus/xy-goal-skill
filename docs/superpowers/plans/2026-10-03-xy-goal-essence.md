# xy-goal 按本质重写：实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 spec `docs/superpowers/specs/2026-10-03-xy-goal-essence-design.md` 重写 xy-goal：检查脚本把能写成检查的规矩写进代码，SKILL.md 只留追得到本质的规矩，在用契约迁到新格式。

**Architecture:** `check.py`（零依赖、单文件）解析 `~/.claude/xy-goal/` 下所有在办契约，报字数总量、超长条目、缺「谁在动」、原话标注与出处对不上、格式错；SKILL.md 讲本质与四个动作（启动、自查、验收、关闭），细节由脚本保证；在用契约拆出账本 `<契约名>.done.md`。

**Tech Stack:** Python 3 标准库（`unittest`），Markdown。

## Global Constraints

| 项 | 值 |
|---|---|
| 铁律 | ① 追到本质不打补丁；② 约束做进设计、难误用；③ 勿增实体（③ 比 ② 重要） |
| 预算 | 每条（标题、判据、出处、产物四行，不含末尾空行）≤ 300 字；同一 `session` 的在办契约清单部分（`## 用户原话` 之前）合计 ≤ 5000 字；按 `LC_ALL=C.UTF-8 wc -m` 同口径计字符 |
| 不用默认值 | `check.py` 必须显式给契约目录：`python3 check.py <目录>`；不带参数报错退出 |
| 谁在动 | 每条 `[ ]` 的产物栏以 `在跑：<名>（pid <进程号>）` 或 `等：<条目 ID 或「用户：…」>` 开头；`[x]` 以 `待验收：` 开头；`等：` 指的条目必须还开着 |
| 账本 | 同目录 `<契约名>.done.md`，每行 `- <ID> …（…；验收 <报告路径>）` 或 `- [~] <ID> …（原话 N：「摘句」）`；`check.py` 检查格式、不计入预算 |
| 会话 | 契约头 `session: <会话 id>`；预算按 session 分组求和 |
| 语言 | SKILL.md、README、注释、报错用中文 |
| 提交 | 不传 `-c user.*`、不设 `GIT_*`；信息末尾 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`；实现者在 `essence` 分支提交、不合并不推送；审查过后由主会话按工作流 `--ff-only` 合入并推送 |

---

### Task 1: 检查脚本 `check.py`（测试先行）

**Files:**
- Create: `check.py`
- Create: `tests/test_check.py`

**Interfaces:**
- Produces: `python3 check.py <契约目录>` → 有问题时逐行打印 `<文件>:<行号>: <问题>` 并退出 1，没问题打印各 session 汇总（各契约字数与组总数）并退出 0；不给参数退出 2。只看目录顶层 `*.md`，`archive/` 与 `*.done.md` 不算在办契约（`*.done.md` 另查账本格式）。

- [ ] **Step 1: 写失败的测试**（`tests/test_check.py`，`unittest`，用临时目录造契约文件），每项检查各一正一反：
  1. 同一 `session` 两份契约各 3000 字（单份都不超）→ 合计超 5000 报错；不同 `session` 各 3000 字 → 通过；一份 4000 字 → 通过。
  2. 一条四行合计 301 字 → 报这条超长；300 字 → 通过。
  3. `[ ]` 的产物栏不以 `在跑：`／`等：` 开头 → 报缺谁在动；`[x]` 不以 `待验收：` 开头 → 报错；`等：T9` 而 T9 不在清单（已关闭）或不存在 → 报错；`等：用户：…` → 通过；汇总里列出全部 `在跑：` 的名字。
  4. 原话没有落点（`（原话 7 → ）`）→ 报错；落点是 `规矩：…` 或 `无：…` → 通过。
  5. 出处 `原话 113～115、120` 展开成 113、114、115、120；其中 114 在文件里不存在 → 报错。
  6. 原话 9 的落点列了在办条目 T3，但 T3 的出处没有 9 → 报错；落点列的条目不在清单里（已验收、在账本里）→ 通过。
  7. 缺 `## 清单` 或 `## 用户原话`、缺 `cron_job_id:` 或 `session:` 行 → 报格式错。
  8a. 原话正文里出现「（原话 3 说过…」这类字样 → 不当成标注；判据跨两行 → 计入该条字数、不误报格式。
  8b. 账本里有 `- [ ] T5 …` 这类在办格式的行、或既无「验收」也无「原话」的行 → 报账本格式错；正确的两种行 → 通过。
  8c. 报错带正确行号；有错退出 1，无错退出 0 并打印汇总。
  8. 不带参数运行 → 报错退出码 2。
- [ ] **Step 2: 跑测试看它红**：`python3 -m unittest discover -s tests -v`，预期全部失败（`check.py` 不存在）。
- [ ] **Step 3: 写 `check.py`**：只用标准库；计字符用 `len(str)`（与 `LC_ALL=C.UTF-8 wc -m` 同口径，测试里核一次）；注释写清每项检查对应 spec 哪条决定。
- [ ] **Step 4: 跑测试看它绿**，再对一份照模板手写的样例契约跑一次看输出可读。
- [ ] **Step 5: 提交**。

### Task 2: 重写 SKILL.md 与 README

**Files:**
- Modify: `SKILL.md`、`README.md`

**Interfaces:**
- Consumes: Task 1 的 `check.py` 命令行与报错格式。

- [ ] **Step 1: 按 spec D1～D8 重写 SKILL.md**：开头「本质」表（四种毛病、四样机制）；契约模板（只放在办、四行写法、谁在动、账本）；原话（照抄、三类标注、来话先记再想）；定时器（间隔规则与新提示词原文，提示词里调用 `python3 ~/.claude/skills/xy-goal/check.py ~/.claude/xy-goal`，并且把「跑完脚本后逐条答谁在动、能派的当场派出、批了的改动当场派人起草 spec」写成提示词里紧跟脚本的第一步——用户原话 535、536：这件事要靠 skill 里真会来提醒的东西，不靠记忆）；自查四件事；验收；关闭。脚本已保证的事不在正文复述，只写「跑 `check.py`、按它报的改」。删掉「拆目标」、改前存档／草稿／核对、「完整清理五步」。
- [ ] **Step 2: 逐条核**：SKILL.md 每条规矩都能指回「本质」表的一样（在提交信息里附一张「规矩 → 本质」对照）；篇幅短于 12839 字节。
- [ ] **Step 3: README** 改成与 SKILL.md 一致的三句话介绍与安装、用法（含 `check.py` 一行）。
- [ ] **Step 4: 提交**。

### Task 3: 迁移在用契约（主会话执行；skill 合入 master、主目录有 `check.py` 之后才做）

**Files:**
- Modify: `~/.claude/xy-goal/20260923-022357-cf1m-cost-model-for-lp.md`
- Create: `~/.claude/xy-goal/20260923-022357-cf1m-cost-model-for-lp.done.md`

- [ ] **Step 1:** 改前整份存到 `archive/<契约名>.before-essence-<YYYYMMDD-HHMM>.md`。
- [ ] **Step 2:** 「已验收」行（含引用存档的那行）、`[~]` 行按账本格式移进 `<契约名>.done.md`；契约里删掉这两段；头部补 `session: <会话 id>`。
- [ ] **Step 3:** 条目压回 ≤ 300 字；每条产物栏按真实状态改成 `在跑：<名>（pid <进程号>）` 或 `等：<条目 ID 或「用户：…」>` 开头；写不出的当场派出再写。
- [ ] **Step 4:** `python3 check.py ~/.claude/xy-goal` 退出码 0。
- [ ] **Step 5:** 按新 SKILL.md 的提示词先建新定时器、回填 `cron_job_id`、`CronList` 核对，再删旧定时器；告诉用户间隔与 7 天过期。
- [ ] **Step 6:** 派子代理核迁移：契约＋账本合起来与存档相比没丢条目、没丢原话、没改判据原意。
- [ ] **Step 7:** 删掉记忆 `/home/xy/.claude/projects/-home-xy-quant-workspace/memory/dispatch-everything-unblocked.md`、`contract-budget-is-the-total.md` 及 `MEMORY.md` 里对应两行（已由 skill 与 `check.py` 承载）；`grep` 确认 `MEMORY.md` 不再提到这两个名字。
