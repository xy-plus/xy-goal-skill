#!/usr/bin/env python3
"""检查 xy-goal 在办契约的格式、预算、原话索引与账本。"""

from dataclasses import dataclass, field
from pathlib import Path
import re
import sys


TOTAL_LIMIT = 5000
ITEM_LIMIT = 300

TASK_RE = re.compile(r"^\s*-\s*\[([^\]]*)\]\s*(\S+)(?:\s+.*)?$")
TASK_ID_RE = re.compile(r"T\d+[①②③④⑤⑥⑦⑧⑨⑩]?")
TASK_REF_RE = re.compile(r"(?<![A-Za-z0-9])T\d+[①②③④⑤⑥⑦⑧⑨⑩]?")
QUOTE_START_RE = re.compile(r"^\s*（原话\s+\d+\s*→")
QUOTE_RE = re.compile(r"^\s*（原话\s+(\d+)\s*→\s*(.*?)）")
SOURCE_RE = re.compile(r"原话\s+(\d+(?:(?:\s*～\s*\d+)|(?:\s*[、,，]\s*\d+))*)")
CRON_RE = re.compile(r"^\s*cron_job_id\s*:")
SESSION_RE = re.compile(r"^\s*session\s*:\s*(.*?)\s*$")

LEDGER_ACCEPTED_RE = re.compile(
    r"^-\s+T\d+[①②③④⑤⑥⑦⑧⑨⑩]?\s+.+（.+；验收\s+[^）]+）$"
)
LEDGER_CANCELLED_RE = re.compile(
    r"^-\s+\[~\]\s+T\d+[①②③④⑤⑥⑦⑧⑨⑩]?\s+.+（原话\s+\d+：「[^」]+」）$"
)


@dataclass
class Problem:
    path: Path
    line: int
    message: str


@dataclass
class Task:
    task_id: str
    status: str
    line: int
    source_line: int
    artifact_line: int
    source_ids: set = field(default_factory=set)
    wait_target: str = ""
    running_name: str = ""


@dataclass
class Contract:
    path: Path
    lines: list
    session: str
    list_chars: int
    list_line: int
    tasks: dict = field(default_factory=dict)


def _line_body(line):
    """去掉物理行尾，保留该行其余字符。"""
    return line.rstrip("\r\n")


def _line_number(index):
    return index + 1


def _expand_quote_numbers(value):
    """展开「原话 113～115、120」中的编号；返回编号与格式问题。"""
    numbers = set()
    malformed = []
    for match in SOURCE_RE.finditer(value):
        for component in re.split(r"\s*[、,，]\s*", match.group(1)):
            endpoints = re.split(r"\s*～\s*", component)
            if len(endpoints) == 1:
                numbers.add(int(endpoints[0]))
                continue
            if len(endpoints) != 2:
                malformed.append(component)
                continue
            first, last = map(int, endpoints)
            if last < first:
                malformed.append(component)
                continue
            numbers.update(range(first, last + 1))
    return numbers, malformed


def _is_task_id(value):
    return TASK_ID_RE.fullmatch(value) is not None


def _find_contract_files(directory):
    """D6：只看目录顶层契约；账本在单独的检查中处理。"""
    return sorted(
        (path for path in directory.glob("*.md") if not path.name.endswith(".done.md")),
        key=lambda path: path.name,
    )


def _find_ledger_files(directory):
    return sorted(directory.glob("*.done.md"), key=lambda path: path.name)


def _read_lines(path, problems):
    try:
        # newline="" 保留原始换行符，预算按原文件的 Unicode 字符计数。
        with path.open("r", encoding="utf-8", newline="") as stream:
            return stream.read().splitlines(keepends=True)
    except (OSError, UnicodeError) as error:
        problems.append(Problem(path, 1, f"无法读取文件：{error}"))
        return None


def _parse_artifact(path, line_number, status, artifact, problems):
    """D4：检查在办与待验收条目的产物前缀，并返回运行名或等待 ID。"""
    if status == "x":
        if not artifact.startswith("待验收："):
            problems.append(Problem(path, line_number, "[x] 产物栏必须以「待验收：」开头"))
        elif not artifact[len("待验收："):].strip():
            problems.append(Problem(path, line_number, "[x] 「待验收：」后必须有产物指针"))
        return "", ""

    if artifact.startswith("在跑："):
        running_name = re.split(r"[；;]", artifact[len("在跑："):], maxsplit=1)[0].strip()
        if not running_name:
            problems.append(Problem(path, line_number, "「在跑：」后必须有任务或代理名"))
        return running_name, ""

    if artifact.startswith("等："):
        target = artifact[len("等："):].strip()
        if target.startswith("用户："):
            if not target[len("用户："):].strip():
                problems.append(Problem(path, line_number, "「等：用户：」后必须写待决定事项"))
            return "", ""
        match = re.match(r"^(T\d+[①②③④⑤⑥⑦⑧⑨⑩]?)(?=$|[；;，,。\s])", target)
        if match is None:
            problems.append(Problem(path, line_number, "「等：」后应为条目 ID 或「用户：…」"))
            return "", ""
        return "", match.group(1)

    problems.append(Problem(
        path, line_number,
        "[ ] 产物栏缺少「谁在动」前缀（应以「在跑：」或「等：」开头）",
    ))
    return "", ""


def _parse_contract(path, problems):
    raw_lines = _read_lines(path, problems)
    if raw_lines is None:
        return None
    lines = [_line_body(line) for line in raw_lines]

    list_indices = [i for i, line in enumerate(lines) if line.strip() == "## 清单"]
    quote_indices = [i for i, line in enumerate(lines) if line.strip() == "## 用户原话"]
    list_index = list_indices[0] if list_indices else -1
    quote_index = quote_indices[0] if quote_indices else -1
    header_end = list_index if list_index >= 0 else next(
        (i for i, line in enumerate(lines) if line.startswith("## ")), len(lines),
    )
    header_lines = lines[:header_end]

    # D4/D8：契约模板要有清单、原话区与 cron_job_id。
    if not list_indices:
        problems.append(Problem(path, 1, "缺少「## 清单」标题"))
    if not quote_indices:
        problems.append(Problem(path, 1, "缺少「## 用户原话」标题"))
    for duplicate in list_indices[1:]:
        problems.append(Problem(path, _line_number(duplicate), "「## 清单」标题重复"))
    for duplicate in quote_indices[1:]:
        problems.append(Problem(path, _line_number(duplicate), "「## 用户原话」标题重复"))
    if list_index >= 0 and quote_index >= 0 and list_index > quote_index:
        problems.append(Problem(path, _line_number(list_index), "「## 清单」必须位于「## 用户原话」之前"))
    if not any(CRON_RE.match(line) for line in header_lines):
        problems.append(Problem(path, 1, "缺少 cron_job_id: 行"))

    # D3：每份契约头显式记录会话；预算之后按这个值分组。
    session_rows = [(i, match.group(1)) for i, line in enumerate(header_lines)
                    if (match := SESSION_RE.match(line))]
    session = ""
    if not session_rows:
        problems.append(Problem(path, 1, "缺少 session: 行"))
    else:
        session = session_rows[0][1].strip()
        if not session:
            problems.append(Problem(path, _line_number(session_rows[0][0]), "session: 值不能为空"))
        for duplicate, _ in session_rows[1:]:
            problems.append(Problem(path, _line_number(duplicate), "session: 行重复"))

    # D3：清单部分是 ## 用户原话 之前的实际文本，包含模板头与换行。
    count_until = quote_index if quote_index >= 0 else len(raw_lines)
    list_chars = len("".join(raw_lines[:count_until]))
    list_line = _line_number(list_index if list_index >= 0 else 0)
    contract = Contract(path, lines, session, list_chars, list_line)

    checklist_start = list_index + 1 if list_index >= 0 else 0
    checklist_end = quote_index if quote_index >= checklist_start else len(lines)
    index = checklist_start
    while index < checklist_end:
        body = lines[index]
        stripped = body.strip()
        if stripped.startswith(("已验收：", "已取消：")) or re.match(
                r"^##\s*(已验收|已取消)(?:\s|$)", stripped):
            # D2：已验收、已取消内容应移入同目录账本，不留在契约清单。
            problems.append(Problem(path, _line_number(index), "已验收或已取消内容应移入 .done.md 账本"))

        task_match = TASK_RE.match(body)
        if task_match is None:
            index += 1
            continue

        status, task_id = task_match.groups()
        if status not in (" ", "x"):
            problems.append(Problem(path, _line_number(index), "清单状态只能是 [ ] 或 [x]"))
            index += 1
            continue
        if not _is_task_id(task_id):
            problems.append(Problem(path, _line_number(index), f"条目编号格式错误：{task_id}（应为 T 加编号）"))
        if task_id in contract.tasks:
            problems.append(Problem(path, _line_number(index), f"条目编号重复：{task_id}"))

        # D3/D4：判据可续行；条目由标题、判据全文、出处、产物组成。
        cursor = index + 1
        criteria_rows = []
        if cursor >= checklist_end or not lines[cursor].startswith("  - 判据："):
            problems.append(Problem(path, _line_number(cursor), f"条目 {task_id} 缺少「判据：」行"))
            index += 1
            continue
        criteria_rows.append(lines[cursor])
        cursor += 1
        while cursor < checklist_end and not lines[cursor].startswith("  - 出处："):
            continuation = lines[cursor]
            if (not continuation.strip()
                    or continuation.startswith("  - ")
                    or TASK_RE.match(continuation)
                    or continuation.startswith("## ")):
                break
            criteria_rows.append(continuation)
            cursor += 1

        if cursor >= checklist_end or not lines[cursor].startswith("  - 出处："):
            problems.append(Problem(path, _line_number(cursor), f"条目 {task_id} 缺少「出处：」行"))
            index = max(index + 1, cursor)
            continue
        source_index = cursor
        artifact_index = source_index + 1
        if artifact_index >= checklist_end or not lines[artifact_index].startswith("  - 产物："):
            problems.append(Problem(path, _line_number(artifact_index), f"条目 {task_id} 缺少「产物：」行"))
            index = artifact_index
            continue

        item_text = "".join(raw_lines[index:artifact_index + 1])
        if item_text.endswith("\r\n"):
            item_text = item_text[:-2]
        elif item_text.endswith(("\n", "\r")):
            item_text = item_text[:-1]
        item_chars = len(item_text)
        if item_chars > ITEM_LIMIT:
            problems.append(Problem(
                path, _line_number(index),
                f"条目合计 {item_chars} 字，超过 {ITEM_LIMIT} 字",
            ))

        source_value = lines[source_index][len("  - 出处："):]
        source_ids, malformed = _expand_quote_numbers(source_value)
        for component in malformed:
            problems.append(Problem(path, _line_number(source_index), f"出处中的原话区间格式错误：{component}"))

        artifact_value = lines[artifact_index][len("  - 产物："):]
        running_name, wait_target = _parse_artifact(
            path, _line_number(artifact_index), status, artifact_value, problems,
        )
        contract.tasks[task_id] = Task(
            task_id=task_id,
            status=status,
            line=_line_number(index),
            source_line=_line_number(source_index),
            artifact_line=_line_number(artifact_index),
            source_ids=source_ids,
            wait_target=wait_target,
            running_name=running_name,
        )
        index = artifact_index + 1

    return contract


def _check_original_quotes(contract, problems):
    lines = contract.lines
    quote_headers = [i for i, line in enumerate(lines) if line.strip() == "## 用户原话"]
    if not quote_headers:
        return
    start = quote_headers[0] + 1
    next_header = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    origins = {}
    paragraph_start = True

    for index in range(start, next_header):
        body = lines[index]
        if not body.strip():
            paragraph_start = True
            continue
        if not paragraph_start:
            continue
        paragraph_start = False

        # D1：只认段首的「原话 N →」；原话正文提到「原话 N 说过」只是内容。
        if not QUOTE_START_RE.match(body):
            continue
        match = QUOTE_RE.match(body)
        if match is None:
            problems.append(Problem(contract.path, _line_number(index), "原话标注格式错误，应为「（原话 N → 落点）」"))
            continue

        number = int(match.group(1))
        landing = match.group(2).strip()
        if not landing:
            problems.append(Problem(contract.path, _line_number(index), f"原话 {number} 缺少落点"))
        elif not TASK_REF_RE.search(landing) and not landing.startswith(("规矩：", "无：")):
            problems.append(Problem(contract.path, _line_number(index), f"原话 {number} 落点须为条目号、规矩：… 或 无：…"))

        targets = set(TASK_REF_RE.findall(landing))
        if number in origins:
            problems.append(Problem(contract.path, _line_number(index), f"原话编号重复：{number}"))
            origins[number]["targets"].update(targets)
        else:
            origins[number] = {"line": _line_number(index), "targets": targets}

    # D1：原话落到在办条目时，条目出处必须列出该原话编号。
    for number, origin in origins.items():
        for task_id in origin["targets"]:
            task = contract.tasks.get(task_id)
            if task is not None and number not in task.source_ids:
                problems.append(Problem(
                    contract.path, origin["line"],
                    f"原话 {number} 落到 {task_id}，但 {task_id} 的出处没有原话 {number}",
                ))

    # D1：每条出处引用的原话必须存在，且落点要包含对应的在办条目。
    for task in contract.tasks.values():
        for number in sorted(task.source_ids):
            origin = origins.get(number)
            if origin is None:
                problems.append(Problem(contract.path, task.source_line, f"出处引用的原话 {number} 不存在"))
            elif task.task_id not in origin["targets"]:
                problems.append(Problem(
                    contract.path, task.source_line,
                    f"{task.task_id} 的出处含原话 {number}，但原话落点没有 {task.task_id}",
                ))


def _check_wait_targets(contracts, problems):
    # D4：等：Tn 必须指向同一 session 中仍留在清单的条目。
    tasks_by_session = {}
    for contract in contracts:
        tasks_by_session.setdefault(contract.session, set()).update(contract.tasks)
    for contract in contracts:
        open_tasks = tasks_by_session.get(contract.session, set())
        for task in contract.tasks.values():
            if task.wait_target and task.wait_target not in open_tasks:
                problems.append(Problem(
                    contract.path, task.artifact_line,
                    f"等：{task.wait_target} 指向不在清单中的条目（可能已关闭或不存在）",
                ))


def _check_ledger(path, problems):
    lines = _read_lines(path, problems)
    if lines is None:
        return
    for index, raw_line in enumerate(lines):
        line = _line_body(raw_line)
        if not line.strip():
            problems.append(Problem(path, _line_number(index), "账本格式错误（不允许空行）"))
            continue
        # D2：账本只能记已验收产物或有原话依据的取消事项。
        if not LEDGER_ACCEPTED_RE.fullmatch(line) and not LEDGER_CANCELLED_RE.fullmatch(line):
            problems.append(Problem(
                path, _line_number(index),
                "账本格式错误（应为验收记录或带原话编号的取消记录）",
            ))


def _check_budgets(contracts, problems):
    # D3：按 session 汇总所有在办契约，拆文件不会降低总量。
    groups = {}
    for contract in contracts:
        groups.setdefault(contract.session, []).append(contract)
    for session, members in groups.items():
        total = sum(contract.list_chars for contract in members)
        if total <= TOTAL_LIMIT:
            continue
        session_label = session if session else "（缺失）"
        used = 0
        location = members[-1]
        for contract in members:
            used += contract.list_chars
            if used > TOTAL_LIMIT:
                location = contract
                break
        problems.append(Problem(
            location.path, location.list_line,
            f"session {session_label} 的清单部分合计 {total} 字，超过 {TOTAL_LIMIT} 字上限",
        ))


def _print_summary(contracts):
    groups = {}
    for contract in contracts:
        groups.setdefault(contract.session, []).append(contract)

    if not groups:
        print("通过：无在办契约；无 session 预算")
        return

    parts = []
    for session in sorted(groups):
        members = groups[session]
        total = sum(contract.list_chars for contract in members)
        files = "、".join(
            f"{contract.path.name} {contract.list_chars} 字" for contract in members
        )
        running_names = list(dict.fromkeys(
            task.running_name
            for contract in members
            for task in contract.tasks.values()
            if task.running_name
        ))
        running = "、".join(running_names) if running_names else "无"
        parts.append(
            f"session={session}：{files}；合计 {total}/{TOTAL_LIMIT} 字；在跑：{running}"
        )
    print("通过：" + "；".join(parts))


def check_directory(directory):
    problems = []
    contracts = []
    for path in _find_contract_files(directory):
        contract = _parse_contract(path, problems)
        if contract is not None:
            contracts.append(contract)
            _check_original_quotes(contract, problems)
    _check_wait_targets(contracts, problems)
    _check_budgets(contracts, problems)
    for path in _find_ledger_files(directory):
        _check_ledger(path, problems)

    problems.sort(key=lambda problem: (problem.path.name, problem.line, problem.message))
    if problems:
        for problem in problems:
            print(f"{problem.path.name}:{problem.line}: {problem.message}", file=sys.stderr)
        return 1
    _print_summary(contracts)
    return 0


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("用法：python3 check.py <契约目录>；必须显式提供契约目录", file=sys.stderr)
        return 2
    directory = Path(args[0]).expanduser()
    if not directory.exists() or not directory.is_dir():
        print(f"契约目录不存在或不是目录：{directory}", file=sys.stderr)
        return 2
    return check_directory(directory)


if __name__ == "__main__":
    raise SystemExit(main())
