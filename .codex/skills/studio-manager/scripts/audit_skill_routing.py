#!/usr/bin/env python3
"""Audit Crew skill ownership and project-type routing metadata."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


GLOBAL_MEDIA_SKILLS = (
    "media-asset-researcher",
    "media-director",
    "media-editor",
    "media-pitcher",
    "media-retro",
    "media-reviewer",
    "media-screenwriter",
    "media-studio-manager",
)

PROJECT_SKILLS = (
    "media-asset-researcher",
    "media-director",
    "media-editor",
    "media-pitcher",
    "media-retro",
    "media-reviewer",
    "media-screenwriter",
    "studio-manager",
)


def description(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^description:\s*(.+)$", text, re.M)
    return match.group(1).strip() if match else ""


def skill_name(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^name:\s*(.+)$", text, re.M)
    return match.group(1).strip() if match else ""


def audit(project_root: Path, global_skills: Path | None = None) -> list[str]:
    errors: list[str] = []
    studio_state = project_root / "studio-state.json"
    film_state = project_root / "film-state.json"
    if not studio_state.is_file():
        errors.append("project missing studio-state.json")
    if studio_state.exists() and film_state.exists():
        errors.append("project contains both studio-state.json and film-state.json")

    skill_root = project_root / ".codex/skills"
    missing = [name for name in PROJECT_SKILLS if not (skill_root / name / "SKILL.md").is_file()]
    for name in missing:
        errors.append(f"missing canonical project skill: {name}")
    for path in sorted(skill_root.glob("*/SKILL.md")):
        value = description(path)
        if path.parent.name not in PROJECT_SKILLS:
            errors.append(f"noncanonical project skill directory: {path.parent.name}")
        if skill_name(path) != path.parent.name:
            errors.append(f"skill name does not match directory: {path.parent.name}")
        if "studio-state.json" not in value or "FilmCrew" not in value:
            errors.append(f"skill routing metadata incomplete: {path.parent.name}")

    douyin_research = skill_root / "media-pitcher/scripts/douyin_research.py"
    if not douyin_research.is_file():
        errors.append("missing media-pitcher Douyin research script")

    for account in sorted((project_root / "accounts").glob("*")):
        if not account.is_dir():
            continue
        if not (account / "style-bible.md").is_file():
            errors.append(f"account missing style-bible.md: {account.name}")
        for rules in sorted(account.glob("skill-base/*/account-rules.md")):
            text = rules.read_text(encoding="utf-8")
            if "## 老板锁定偏好" not in text or "## 数据验证规则" not in text:
                errors.append(f"account rules missing canonical sections: {rules.relative_to(project_root)}")
            if "已废止" in text or "原始来源待补录" in text:
                errors.append(f"inactive rule kept in active file: {rules.relative_to(project_root)}")

    consistency_files = (
        project_root / "shared/skill-bases/素材研究员/素材方法.领域.md",
        skill_root / "media-asset-researcher/SKILL.md",
        project_root / "shared/skill-bases/剪辑师/剪辑方法.领域.md",
        skill_root / "media-director/SKILL.md",
    )
    for path in consistency_files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "封面默认比例为抖音 `9:16`" in text or "默认抖音主版 `9:16`" in text:
            errors.append(f"stale Douyin cover ratio: {path.relative_to(project_root)}")
        if "运动与声音联合样片" in text or "运动＋声音联合样片" in text:
            errors.append(f"preview incorrectly requires sound: {path.relative_to(project_root)}")

    if global_skills is not None:
        for name in GLOBAL_MEDIA_SKILLS:
            if (global_skills / name).exists():
                errors.append(f"redundant global Crew skill: {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--global-skills", type=Path)
    args = parser.parse_args()
    errors = audit(args.project_root.resolve(), args.global_skills)
    for item in errors:
        print(f"ERROR {item}")
    if errors:
        return 1
    print("OK skill ownership and routing metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
