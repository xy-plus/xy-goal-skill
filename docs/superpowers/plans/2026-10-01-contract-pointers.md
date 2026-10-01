# 契约只放判法与出处：实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal：** 按 spec 改 `SKILL.md`：条目只放判法与出处、工作规矩不挂原话、已取消条目一行、字数线 5000，并在在用的契约上实证。

**Architecture：** 只改一份说明文件；「测试」是对改后的 `SKILL.md` 做 grep 断言，加上在真实契约上跑一遍自查命令与完整清理。

**Tech Stack：** Markdown、bash（grep／awk）。

spec：`docs/superpowers/specs/2026-10-01-contract-pointers-design.md`（同树）。

## Global Constraints

- 只动 `SKILL.md`（`README.md` 若提到被改的规则就同步）；不加脚本。
- 规则只说一遍；能用表就不写长句；中文。
- 提交不传 `-c user.*`、不用 `git add -A`；提交信息末尾 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。不推送、不合并（合并与推送归 main）。
- 工作树：`~/.claude/skills/xy-goal/.worktree/contract-pointers`（分支 `contract-pointers`，从 `origin/master` `ce9cfe6` 开）。

---

### Task 1：改 `SKILL.md`

**Files：** Modify `SKILL.md`（模板、「原话和清单要对得上」那段、状态与判据那段、自查 prompt、「清理」整节）。

- [ ] **Step 1：写失败的检查**（存成 `/tmp` 外的临时脚本，放 `$CLAUDE_JOB_DIR/tmp/check_skill.sh`，不进仓）：
  ```bash
  f=SKILL.md
  ! grep -q '全部未完成条目' $f            # D3：这一类标注取消
  ! grep -q '1.2 万\|12000' $f              # D5：字数线改 5000
  ! grep -q '判据只能往后加' $f             # D2
  grep -q '5000' $f                         # D5
  grep -q '→ 规矩：' $f                     # D3 的新标注
  grep -q '\[~\] ID' $f                     # D4 的一行格式
  grep -q '出处' $f                         # D1
  ```
  每行单独判返回码（不靠 `set -e`），全部满足才算过。在 `ce9cfe6` 上跑，确认红。
- [ ] **Step 2：改文。** 逐条落 spec 的 D1～D7：
  - 模板里一条条目改成四行：标题、`判据：`（怎么判完成，可核实）、`出处：`（原话编号、spec／文档路径）、`产物：`（现状指针与还差什么）；写明以 300 字为度、设计内容不进契约。
  - 「原话和清单要对得上」那段：标注三类——落到条目、`→ 规矩：<写在哪>`（当场写进记忆、CLAUDE.md 或对应 skill）、`→ 无：<为什么>`；命令展开只记一行；一段原话两类都有时并写「（原话 N → T3；规矩：…）」。
  - 状态与判据那段：删「判据只能往后加」；改成「新要求加出处、改口改判法；删字或改写走清理第 4 步」。已取消条目一行格式。
  - 自查 prompt：12000 改 5000；标注检查认三类合法目标；加一句「在跑的定时器要按新 prompt 重建」。
  - 「清理」：第 2 步把「→ 规矩：」与「→ 无」一起送验后删；第 4 步的字数线改 5000；其余照旧，长句拆短。
- [ ] **Step 3：跑 Step 1 的检查确认绿**；再通读一遍，确认同一条规则只出现一次。
- [ ] **Step 4：提交**（`git add SKILL.md`，涉及 README 时一起）。

### Task 2：在用的契约上实证（spec C2、C3）

**Files：** 不动仓库；动 `~/.claude/xy-goal/20260923-022357-cf1m-cost-model-for-lp.md`（由 main 做，或 main 指定的子代理做草稿）。

- [ ] **Step 1：** 按新规矩做一遍完整清理：先存原文 `archive/<契约名>.before-criteria-<YYYYMMDD-HHMM>.md`；草稿写 `archive/<契约名>.criteria-draft-<YYYYMMDD-HHMM>.md`：条目改成四行格式、设计内容换成出处、已取消条目一行、21 段「全部未完成条目」原话按三类重标（通用规矩先核对已写进记忆再标 `→ 规矩：`）。
- [ ] **Step 2：** 派核对子代理（只给三个路径：存档原文、草稿、契约），逐条判据给结论（保留／覆盖到哪句／丢了什么／放宽了什么），并核 `→ 规矩：` 指的记忆确实写了那条规矩；全部通过才换入。
- [ ] **Step 3：** 换入后量我写的部分（`awk '/^## 用户原话/{exit} {print}' <契约> | LC_ALL=C.UTF-8 wc -m`）≤ 5000；跑新自查 prompt 里的两条命令，三类标注都读得出、没有落空的原话与条目。

### Task 3：审查、合入、重建定时器（spec C4）

- [ ] **Step 1：** 派审查子代理按三条铁律与仓库规范审 `git diff ce9cfe6..HEAD -- SKILL.md README.md`。
- [ ] **Step 2：** 采纳意见后，核对 spec、计划、`SKILL.md` 三者对齐、每条决定都落了；删 spec 与计划；合入 master，推 GitHub（`git push origin <sha>:master`）。
- [ ] **Step 3：** 在用的契约按新自查 prompt 重建定时器（删旧的、建新的、id 回填契约、`CronList` 核对）。
