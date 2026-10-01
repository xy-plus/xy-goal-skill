# 契约只放判法与出处：实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal：** 按 spec 改 `SKILL.md`：条目只放判法与出处、工作规矩不挂原话、已取消条目一行、字数线 5000，并在在用的契约上实证。

**Architecture：** 只改一份说明文件；「测试」是对改后的 `SKILL.md` 做 grep 断言，加上在真实契约上跑一遍自查命令与完整清理。

**Tech Stack：** Markdown、bash（grep／awk）。

spec：`docs/superpowers/specs/2026-10-01-contract-pointers-design.md`（同树）。

## Global Constraints

- 只动 `SKILL.md`；不加脚本。
- 规则只说一遍；能用表就不写长句；中文。
- 提交不传 `-c user.*`、不用 `git add -A`；提交信息末尾 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。不推送、不合并（合并与推送归 main）。
- 工作树：`~/.claude/skills/xy-goal/.worktree/contract-pointers`（分支 `contract-pointers`，从 `origin/master` `ce9cfe6` 开）。

---

### Task 1：改 `SKILL.md`

**Files：** Modify `SKILL.md`。逐行落点以 `external:/home/xy/.claude-subagent/reports/xy-goal-pointers/spec-review-detail.md` 末尾「SKILL.md 改动落点清单」为准（行号按 `ce9cfe6`），加上 spec D7 的验收节与 D6 的定时器那句。`README.md` 不动（只指向 `SKILL.md`，审查已核）。

- [ ] **Step 1：写失败的检查**（放 `$CLAUDE_JOB_DIR/tmp/check_skill.sh`，不进仓；每行单独判返回码，不靠 `set -e`）：
  ```bash
  f=SKILL.md
  ! grep -q '1.2 万\|12000' $f        # D5：旧字数线没了
  ! grep -q '判据只能往后加' $f       # D2
  grep -q '5000' $f                   # D5
  grep -q '→ 规矩：' $f               # D3
  grep -q '出处' $f                   # D1
  grep -q '\[~\] ID' $f               # D4
  grep -q '按出处' $f                 # D6、D7：读条目与验收都按出处找齐要求
  grep -q '定时器文案在建时冻结' $f   # D6
  ```
  在 `ce9cfe6` 上跑，确认前两行之外全红（前两行在旧文件上就红，是因为旧字还在）。
- [ ] **Step 2：改文**，逐条落 spec 的 D1～D8：
  - 模板：条目四行（标题、`判据：`、`出处：`、`产物：`），写明 300 字为度、设计内容不进契约、出处要指向能活到验收的东西；`[~]` 一行格式。
  - 原话那段：D3 的三类标注与并写格式、命令展开只记一行、「来源」并进「出处」、各类的删除条件；「→ 无」保留原判据线并加上催促、状态查询、命令展开。
  - 状态与判据那段：删「判据只能往后加」与「措辞可以压……只在完整清理时」；改成 D2：新要求加出处、改口当场改判法、改前存一份原文、下一次送验时核对。
  - 自查 prompt：12000 改 5000；两头核对认 D3 的标注并查出处里的原话编号都在、标注指回；「先按出处把要求找齐」；其余句子不精简。
  - 「清理」：标题与第 4 步的字数线改 5000；第 2 步的删除条件按 D3、D4；长句拆短。
  - 「验收」：要求三条改四条，加 D7 那条。
  - 启动第 3 步后加 D6 那句「定时器文案在建时冻结，skill 改版后把在跑的定时器删掉、按新文案重建」。
- [ ] **Step 3：跑 Step 1 的检查确认全绿**；通读一遍，确认除自查 prompt 外同一条规则只出现一次。
- [ ] **Step 4：提交**（`git add SKILL.md`）。

### Task 2：在用的契约上实证（spec C2、C3）

**Files：** 不动仓库；动 `~/.claude/xy-goal/20260923-022357-cf1m-cost-model-for-lp.md`（由 main 做，或 main 指定的子代理做草稿）。

- [ ] **Step 1：** 按新规矩做一遍完整清理：先存原文 `archive/<契约名>.before-criteria-<YYYYMMDD-HHMM>.md`；草稿写 `archive/<契约名>.criteria-draft-<YYYYMMDD-HHMM>.md`：条目改成四行格式、设计内容换成出处、已取消条目一行、21 段「全部未完成条目」原话按三类重标（通用规矩先核对已写进记忆再标 `→ 规矩：`）。
- [ ] **Step 2：** 派核对子代理（只给三个路径：存档原文、草稿、契约），逐条判据给结论（保留／覆盖到哪句／丢了什么／放宽了什么），并核 `→ 规矩：` 指的记忆确实写了那条规矩；全部通过才换入。
- [ ] **Step 3：** 换入后量我写的部分（`awk '/^## 用户原话/{exit} {print}' <契约> | LC_ALL=C.UTF-8 wc -m`）≤ 5000；跑新自查 prompt 里的两条命令，三类标注都读得出、没有落空的原话与条目。

### Task 3：审查、合入、重建定时器（spec C4）

- [ ] **Step 1：** 派审查子代理按三条铁律与仓库规范审 `git diff ce9cfe6..HEAD -- SKILL.md README.md`。
- [ ] **Step 2：** 采纳意见后，核对 spec、计划、`SKILL.md` 三者对齐、每条决定都落了；删 spec 与计划；合入 master，推 GitHub（`git push origin <sha>:master`）。
- [ ] **Step 3：** 在用的契约按新自查 prompt 重建定时器（删旧的、建新的、id 回填契约、`CronList` 核对）。
