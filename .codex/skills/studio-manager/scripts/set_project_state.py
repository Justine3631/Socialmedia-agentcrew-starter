#!/usr/bin/env python3
"""Update brief lifecycle fields atomically, validate, then refresh dashboard."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from generate_dashboard import generate
from validate_workflow import STAGES, STATUSES, extract, validate_project


RISKS = {"A", "B", "C"}
PLANNING_STAGES = {"提案中", "写稿中"}
PRODUCTION_STAGES = {"讲戏中", "素材中", "拍摄中", "剪辑中", "审核中", "审核通过"}


def workspace_for(project: Path) -> Path:
    for parent in (project, *project.parents):
        if (parent / "studio-state.json").is_file():
            return parent
    raise ValueError("project is not inside a studio workspace")


def replace_field(text: str, label: str, value: str) -> str:
    pattern = re.compile(
        rf"^(?P<prefix>-\s*(?:\*\*)?{re.escape(label)}(?:\*\*)?：)\s*[^\n]*$",
        re.M,
    )
    updated, count = pattern.subn(rf"\g<prefix>{value}", text, count=1)
    if count != 1:
        raise ValueError(f"brief missing field: {label}")
    return updated


def wip_category(stage: str) -> str | None:
    if stage in PLANNING_STAGES:
        return "提案/写稿"
    if stage in PRODUCTION_STAGES:
        return "制作"
    return None


def wip_conflicts(project: Path, stage: str, status: str) -> list[Path]:
    category = wip_category(stage)
    if category is None or status in {"阻塞", "完成"}:
        return []
    account = project.parent.parent
    conflicts: list[Path] = []
    for brief in account.glob("videos/*/brief.md"):
        other = brief.parent.resolve()
        if other == project.resolve():
            continue
        text = brief.read_text(encoding="utf-8")
        other_stage = extract(text, "当前阶段")
        other_status = extract(text, "阶段状态")
        if wip_category(other_stage or "") == category and other_status not in {"阻塞", "完成"}:
            conflicts.append(other)
    return conflicts


def update_project(
    project: Path,
    *,
    stage: str,
    status: str,
    blocker: str,
    risk: str | None = None,
) -> Path:
    project = project.resolve()
    if stage not in STAGES:
        raise ValueError(f"invalid stage: {stage}")
    if status not in STATUSES:
        raise ValueError(f"invalid status: {status}")
    if risk is not None and risk not in RISKS:
        raise ValueError(f"invalid risk: {risk}")
    if not blocker.strip():
        raise ValueError("blocker cannot be blank")

    brief = project / "brief.md"
    if not brief.is_file():
        raise ValueError(f"missing brief: {brief}")
    original = brief.read_text(encoding="utf-8")
    updated = replace_field(original, "当前阶段", stage)
    updated = replace_field(updated, "阶段状态", status)
    updated = replace_field(updated, "阻塞原因", blocker.strip())
    if risk is not None:
        updated = replace_field(updated, "风险等级", risk)

    brief.write_text(updated, encoding="utf-8")
    conflicts = wip_conflicts(project, stage, status)
    if conflicts:
        brief.write_text(original, encoding="utf-8")
        paths = "\n".join(str(path) for path in conflicts)
        raise ValueError(f"WIP limit exceeded for {wip_category(stage)}; brief restored:\n{paths}")
    errors, _, _, _ = validate_project(project)
    if errors:
        brief.write_text(original, encoding="utf-8")
        raise ValueError("state rejected; brief restored:\n" + "\n".join(errors))

    return generate(workspace_for(project))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--stage", required=True, choices=STAGES)
    parser.add_argument("--status", required=True, choices=sorted(STATUSES))
    parser.add_argument("--blocker", required=True)
    parser.add_argument("--risk", choices=sorted(RISKS))
    args = parser.parse_args()
    try:
        board = update_project(
            args.project,
            stage=args.stage,
            status=args.status,
            blocker=args.blocker,
            risk=args.risk,
        )
    except ValueError as error:
        print(f"ERROR {error}")
        return 1
    print(f"OK project={args.project.resolve()}")
    print(f"BOARD {board}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
