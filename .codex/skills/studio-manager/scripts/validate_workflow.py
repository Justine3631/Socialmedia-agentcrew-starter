#!/usr/bin/env python3
"""Validate project lifecycle against real, non-placeholder artifacts."""

from __future__ import annotations

import argparse
import hashlib
import re
from datetime import datetime
from pathlib import Path


STAGES = [
    "提案中",
    "写稿中",
    "讲戏中",
    "素材中",
    "拍摄中",
    "剪辑中",
    "审核中",
    "审核通过",
    "已发布",
    "已复盘",
]

PLACEHOLDERS = (
    "通过 / 修改后复审",
    "待发布 / 已发布",
    "状态：待发布",
    "写入时间：\n",
)

PLATFORMS = {"抖音": "抖音", "小红书": "小红书"}
STATUSES = {"进行中", "等待老板确认", "阻塞", "完成"}
WORK_MODES = {"标准", "快速"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}

DOWNSTREAM_ARTIFACT_STAGES = {
    "06video/edit-log.md": "剪辑中",
    "06video/review.md": "剪辑中",
    "prediction.md": "审核通过",
    "07publish/upload-kit.md": "审核通过",
    "07publish/publish.md": "已发布",
    "08retro/retro.md": "已发布",
}


def meaningful(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    text = path.read_text(encoding="utf-8")
    return not any(marker in text for marker in PLACEHOLDERS)


def extract(text: str, label: str) -> str | None:
    match = re.search(rf"(?:\*\*)?{re.escape(label)}(?:\*\*)?：\s*([^\n]+)", text)
    return match.group(1).strip() if match else None


def actual_videos(project: Path) -> list[Path]:
    return [
        path for path in (project / "06video").glob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS and path.stat().st_size > 0
    ]


def manifest_complete(project: Path) -> bool:
    path = project / "04media/asset-manifest.md"
    if not meaningful(path):
        return False
    text = path.read_text(encoding="utf-8")
    gap = re.search(r"## 必需素材缺口\s*\n(?P<body>.*?)(?:\n##|\Z)", text, re.S)
    return not gap or gap.group("body").strip() in {"", "- 无", "-"}


def shoot_complete(project: Path) -> bool:
    path = project / "04media/shoot-log.md"
    if not meaningful(path):
        return False
    text = path.read_text(encoding="utf-8")
    required = (
        "[x] 所有必拍镜头完成",
        "[x] 所有必需录屏完成",
        "[x] 素材研究员已按 `shot-checklist.md` 完成验收",
    )
    return all(item in text for item in required)


def locked_video(project: Path, text: str) -> tuple[Path | None, str | None]:
    relative = field_value(text, "锁定成片文件")
    recorded_hash = field_value(text, "锁定成片 SHA-256")
    if not relative:
        return None, recorded_hash
    path = (project / relative).resolve()
    try:
        path.relative_to(project.resolve())
    except ValueError:
        return None, recorded_hash
    return path, recorded_hash


def locked_video_valid(project: Path, text: str) -> bool:
    path, recorded_hash = locked_video(project, text)
    return bool(
        path
        and path.is_file()
        and path.suffix.lower() in VIDEO_EXTENSIONS
        and path.stat().st_size > 0
        and recorded_hash
        and recorded_hash.lower() == sha256(path)
    )


def validate_locked_video_chain(project: Path, paths: list[Path]) -> list[str]:
    errors: list[str] = []
    references: list[tuple[Path, str]] = []
    for path in paths:
        if not meaningful(path):
            continue
        video, recorded_hash = locked_video(project, path.read_text(encoding="utf-8"))
        if not video or not recorded_hash or not locked_video_valid(project, path.read_text(encoding="utf-8")):
            errors.append(f"invalid locked video reference: {path.relative_to(project)}")
            continue
        references.append((video, recorded_hash.lower()))
    if references and len(set(references)) > 1:
        errors.append("locked video path or SHA-256 differs across lifecycle records")
    return errors


def review_passed(project: Path) -> bool:
    path = project / "06video/review.md"
    if not meaningful(path):
        return False
    text = path.read_text(encoding="utf-8")
    return bool(
        re.search(r"结论：\s*通过\s*$", text, re.M)
        and re.search(r"阻断问题数：\s*0\s*$", text, re.M)
        and field_value(text, "审核执行方式") == "独立子 Agent"
        and field_value(text, "审核任务 ID")
        and field_value(text, "审核输入清单")
        and locked_video_valid(project, text)
    )


def platform_section(text: str, platform: str) -> str | None:
    match = re.search(
        rf"^##\s+{re.escape(platform)}(?:[^\n]*)\n(?P<body>.*?)(?=^##\s+|\Z)",
        text,
        re.M | re.S,
    )
    return match.group("body") if match else None


def published_sections(project: Path, platforms: set[str]) -> list[str]:
    path = project / "07publish/publish.md"
    if not meaningful(path):
        return []
    text = path.read_text(encoding="utf-8")
    published: list[str] = []
    for platform in platforms:
        section = platform_section(text, platform)
        if section is None:
            continue
        status = field_value(section, "状态")
        if status == "已发布" and all(
            field_value(section, label) for label in ("发布时间", "链接或平台 ID", "使用的包装版本")
        ):
            published.append(section)
    return published


def publish_complete(project: Path, platforms: set[str]) -> bool:
    path = project / "07publish/publish.md"
    if not meaningful(path):
        return False
    text = path.read_text(encoding="utf-8")
    return all(platform_section(text, platform) is not None for platform in platforms) and bool(
        published_sections(project, platforms)
    ) and locked_video_valid(project, text)


def field_value(text: str, label: str) -> str | None:
    match = re.search(rf"^-\s*{re.escape(label)}：\s*(\S.*?)\s*$", text, re.M)
    return match.group(1).strip() if match else None


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("T", " ").replace("/", "-").strip()
    for format_string in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(normalized, format_string)
        except ValueError:
            continue
    return None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_prediction_lock(project: Path, platforms: set[str]) -> list[str]:
    errors: list[str] = []
    prediction = project / "prediction.md"
    publish = project / "07publish/publish.md"
    if not (meaningful(prediction) and meaningful(publish)):
        return errors
    prediction_text = prediction.read_text(encoding="utf-8")
    publish_text = publish.read_text(encoding="utf-8")
    prediction_time = parse_time(field_value(prediction_text, "写入时间"))
    publish_times = [parse_time(field_value(section, "发布时间")) for section in published_sections(project, platforms)]
    valid_publish_times = [item for item in publish_times if item]
    publish_time = min(valid_publish_times) if valid_publish_times else None
    if prediction_time is None:
        errors.append("prediction has missing or invalid 写入时间")
    if publish_time is None:
        errors.append("publish record has missing or invalid 发布时间")
    if prediction_time and publish_time and prediction_time >= publish_time:
        errors.append("prediction 写入时间 must be before 发布时间")
    recorded_hash = field_value(publish_text, "发布前 prediction.md SHA-256")
    if not recorded_hash:
        errors.append("publish record missing prediction SHA-256")
    elif recorded_hash.lower() != sha256(prediction):
        errors.append("prediction.md changed after publish hash was recorded")
    return errors


def has_data_snapshot(project: Path) -> bool:
    path = project / "07publish/publish.md"
    if not meaningful(path):
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\|\s*T\+(?:1|3|7|30)\s*\|", line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            has_time = len(cells) > 1 and bool(cells[1])
            has_metric = any(cells[2:-1])
            has_evidence = len(cells) > 2 and bool(cells[-1])
            if has_time and has_metric and has_evidence:
                return True
    return False


def inferred_stage(project: Path, platforms: set[str] | None = None) -> str:
    platforms = platforms or set(PLATFORMS.values())
    stage = "提案中"
    if not meaningful(project / "02script/outline.md"):
        return stage
    stage = "写稿中"
    if not (meaningful(project / "02script/script.md") and meaningful(project / "02script/publish-pack.md")):
        return stage
    stage = "讲戏中"
    if not (meaningful(project / "03outputs/分镜.md") and meaningful(project / "03outputs/shot-checklist.md")):
        return stage
    stage = "素材中"
    if not manifest_complete(project):
        return stage
    stage = "拍摄中"
    if not shoot_complete(project):
        return stage
    stage = "剪辑中"
    edit_log = project / "06video/edit-log.md"
    if not (actual_videos(project) and meaningful(edit_log) and locked_video_valid(project, edit_log.read_text(encoding="utf-8"))):
        return stage
    stage = "审核中"
    if not review_passed(project):
        return stage
    stage = "审核通过"
    if not (meaningful(project / "prediction.md") and publish_complete(project, platforms)):
        return stage
    stage = "已发布"
    if meaningful(project / "08retro/retro.md") and has_data_snapshot(project):
        return "已复盘"
    return stage


def planned_platforms(brief_text: str) -> set[str]:
    line = next((line for line in brief_text.splitlines() if "平台计划：" in line), "")
    return {name for token, name in PLATFORMS.items() if token in line}


def markdown_sections(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^#{2,6}\s+(.+?)\s*$", text, re.M))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group(1).strip(), text[match.end():end].strip()))
    return sections


def has_section(text: str, aliases: tuple[str, ...]) -> bool:
    placeholders = {"", "-", "无", "待填", "待补充", "todo", "tbd"}
    for heading, body in markdown_sections(text):
        normalized = re.sub(r"[*_`]", "", body).strip().lower()
        if any(alias in heading for alias in aliases) and normalized not in placeholders:
            return True
    for alias in aliases:
        match = re.search(
            rf"^\s*-\s*(?:\*\*)?{re.escape(alias)}(?:\*\*)?：\s*(?P<body>.+?)\s*$",
            text,
            re.M,
        )
        if match and re.sub(r"[*_`]", "", match.group("body")).strip().lower() not in placeholders:
            return True
    return False


def section_or_field_value(text: str, aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        value = extract(text, alias)
        if value:
            return value
    for heading, body in markdown_sections(text):
        if any(alias in heading for alias in aliases):
            normalized = re.sub(r"[*_`]", "", body).strip()
            if normalized:
                return normalized
    return None


def has_blank_list_field(text: str) -> bool:
    """Reject empty list fields, but allow a populated nested list below them."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not re.match(r"^\s*-\s+[^：\n]+：\s*$", line):
            continue
        following = lines[index + 1 :]
        next_line = next((item for item in following if item.strip()), "")
        if not re.match(r"^\s{2,}-\s+\S", next_line):
            return True
    return False


def validate_brief_metadata(project: Path, text: str) -> list[str]:
    errors: list[str] = []
    status = extract(text, "阶段状态")
    blocked = extract(text, "阻塞原因")
    mode = extract(text, "工作模式")
    account = extract(text, "账号")
    if status not in STATUSES:
        errors.append(f"invalid 阶段状态: {status or 'missing'}")
    if mode not in WORK_MODES:
        errors.append(f"invalid 工作模式: {mode or 'missing'}")
    if not blocked:
        errors.append("missing 阻塞原因")
    elif status == "等待老板确认" and blocked == "无":
        errors.append("等待老板确认 must name confirmation object in 阻塞原因")
    elif status == "阻塞" and blocked == "无":
        errors.append("阻塞 status must name 阻塞原因")
    elif status in {"进行中", "完成"} and blocked != "无":
        errors.append(f"{status} status must use 阻塞原因: 无")
    expected_account = project.parent.parent.name if project.parent.name == "videos" else None
    if expected_account and account != expected_account:
        errors.append(f"账号与项目路径不一致: brief={account or 'missing'}, path={expected_account}")
    return errors


def validate_downstream_artifact_drift(project: Path, declared: str | None) -> list[str]:
    """Catch stale brief stages even when an earlier missing artifact stalls inference."""
    if declared not in STAGES:
        return []
    errors: list[str] = []
    declared_index = STAGES.index(declared)
    for relative, minimum_stage in DOWNSTREAM_ARTIFACT_STAGES.items():
        path = project / relative
        if meaningful(path) and declared_index < STAGES.index(minimum_stage):
            errors.append(
                "downstream artifact/state drift: "
                f"{relative} exists while brief={declared}; minimum plausible stage={minimum_stage}"
            )
    return errors


def validate_content(project: Path, brief_text: str, declared: str | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    platforms = planned_platforms(brief_text)
    if not platforms:
        errors.append("missing or unsupported 平台计划")

    outline = project / "02script/outline.md"
    if outline.exists():
        text = outline.read_text(encoding="utf-8")
        required = {
            "目标观众": ("目标观众",),
            "核心承诺": ("核心承诺", "结果承诺", "承诺链"),
            "证据来源": ("证据来源", "证据/参考来源"),
            "风险边界": ("风险边界", "不可改变的风险边界"),
            "内容结构": ("内容结构", "主故事结构", "结构"),
        }
        missing = [name for name, aliases in required.items() if not has_section(text, aliases)]
        if missing:
            errors.append(f"outline missing sections: {', '.join(missing)}")
        if re.search(r"大纲契约版本(?:\*\*)?：\s*2(?:\s|$)", text):
            required_v2 = {
                "生产策略": ("生产策略",),
                "假设来源": ("假设来源",),
                "已知混杂变量": ("已知混杂变量",),
                "临时包装原型": ("临时包装原型",),
                "首个可见兑现": ("首个可见兑现",),
                "体验峰值": ("体验峰值",),
                "结束记忆": ("结束记忆",),
            }
            missing_v2 = [name for name, aliases in required_v2.items() if not has_section(text, aliases)]
            if missing_v2:
                errors.append(f"outline v2 missing sections: {', '.join(missing_v2)}")
            strategy = section_or_field_value(text, ("生产策略",))
            if strategy and strategy not in {"探索性实验", "已验证模式复用"}:
                errors.append(f"outline v2 invalid 生产策略: {strategy}")
            hypothesis = section_or_field_value(text, ("假设来源",))
            if hypothesis and "learning-log" not in hypothesis and "探索性实验" not in hypothesis:
                errors.append("outline v2 假设来源 must cite learning-log or say 探索性实验")
            first_proof = section_or_field_value(text, ("首个可见兑现",))
            if first_proof and "秒" not in first_proof:
                errors.append("outline v2 首个可见兑现 must include expected time in 秒")

    publish_pack = project / "02script/publish-pack.md"
    if publish_pack.exists():
        text = publish_pack.read_text(encoding="utf-8")
        if "内容母版" not in text:
            errors.append("publish-pack missing content master")
        for platform in PLATFORMS.values():
            present = platform in text
            if platform in platforms and not present:
                errors.append(f"publish-pack missing planned platform: {platform}")
            if platform not in platforms and present:
                errors.append(f"publish-pack contains unplanned platform: {platform}")
        if not re.search(r"包装版本：\s*\S+", text):
            errors.append("publish-pack missing packaging version")
        if has_blank_list_field(text):
            errors.append("publish-pack contains blank fields")

    checklist = project / "03outputs/shot-checklist.md"
    if checklist.exists():
        rows = [
            line for line in checklist.read_text(encoding="utf-8").splitlines()
            if line.startswith("|") and "镜头ID" not in line and "---" not in line
        ]
        if any(len([cell for cell in row.split("|")[1:-1] if cell.strip()]) < 4 for row in rows):
            errors.append("shot-checklist has row without stable ID or acceptance criteria")

    manifest = project / "04media/asset-manifest.md"
    if manifest.exists() and declared in {"拍摄中", "剪辑中", "审核中", "审核通过", "已发布", "已复盘"}:
        text = manifest.read_text(encoding="utf-8")
        gap = re.search(r"## 必需素材缺口\s*\n(?P<body>.*?)(?:\n##|\Z)", text, re.S)
        if gap and gap.group("body").strip() not in {"", "- 无", "-"}:
            errors.append("asset-manifest still has required gaps")

    shoot_log = project / "04media/shoot-log.md"
    if shoot_log.exists() and declared in {"剪辑中", "审核中", "审核通过", "已发布", "已复盘"}:
        text = shoot_log.read_text(encoding="utf-8")
        if "[ ] 所有必拍镜头完成" in text or "[ ] 所有必需录屏完成" in text:
            errors.append("shoot-log required work is incomplete")

    review = project / "06video/review.md"
    if review.exists() and declared in {"审核通过", "已发布", "已复盘"}:
        text = review.read_text(encoding="utf-8")
        if not re.search(r"结论：\s*通过\s*$", text, re.M):
            errors.append("review is not passed")
        if not re.search(r"阻断问题数：\s*0\s*$", text, re.M):
            errors.append("review blocking count is not zero")

    prediction = project / "prediction.md"
    if declared in {"已发布", "已复盘"} and not meaningful(prediction):
        errors.append("missing completed prediction before publish")

    if declared in {"审核中", "审核通过", "已发布", "已复盘"}:
        if not actual_videos(project):
            errors.append("missing real exported video")
        if not meaningful(project / "06video/edit-log.md"):
            errors.append("missing completed edit-log")
        else:
            edit_text = (project / "06video/edit-log.md").read_text(encoding="utf-8")
            if not locked_video_valid(project, edit_text):
                errors.append("edit-log locked video path or SHA-256 is invalid")

    if declared in {"审核通过", "已发布", "已复盘"} and not review_passed(project):
        errors.append("missing passed independent review")
    if declared in {"审核通过", "已发布", "已复盘"}:
        errors.extend(validate_locked_video_chain(project, [
            project / "06video/edit-log.md",
            project / "06video/review.md",
        ]))

    if declared in {"已发布", "已复盘"} and not publish_complete(project, platforms):
        errors.append("missing completed publish record with time and link")
    if declared in {"已发布", "已复盘"}:
        errors.extend(validate_prediction_lock(project, platforms))
        publish_text = (project / "07publish/publish.md").read_text(encoding="utf-8") if (project / "07publish/publish.md").is_file() else ""
        if publish_text and not locked_video_valid(project, publish_text):
            errors.append("publish record locked video path or SHA-256 is invalid")
        errors.extend(validate_locked_video_chain(project, [
            project / "06video/edit-log.md",
            project / "06video/review.md",
            project / "prediction.md",
            project / "07publish/publish.md",
        ]))

    if declared == "已复盘":
        if not meaningful(project / "08retro/retro.md"):
            errors.append("missing completed retro")
        if not has_data_snapshot(project):
            errors.append("retro requires at least one populated data snapshot")

    publish = project / "07publish/publish.md"
    if publish.exists():
        text = publish.read_text(encoding="utf-8")
        for snapshot in ("T+1", "T+7"):
            if snapshot not in text:
                errors.append(f"publish record missing fixed snapshot: {snapshot}")

    return errors, warnings


def validate_project(project: Path) -> tuple[list[str], list[str], str | None, str]:
    project = project.resolve()
    brief = project / "brief.md"
    if not brief.is_file():
        return [f"missing {brief}"], [], None, "提案中"

    text = brief.read_text(encoding="utf-8")
    declared = extract(text, "当前阶段")
    status = extract(text, "阶段状态")
    risk = extract(text, "风险等级")
    legacy_note = extract(text, "历史例外")
    is_legacy = bool(legacy_note and legacy_note not in {"无", "否"})
    platforms = planned_platforms(text)
    inferred = inferred_stage(project, platforms)

    content_errors, warnings = validate_content(project, text, declared)
    if is_legacy:
        errors: list[str] = []
        warnings.append(f"历史例外：{legacy_note}")
        warnings.extend(f"历史证据缺口：{item}" for item in content_errors)
    else:
        errors = content_errors
    if declared not in STAGES:
        errors.append(f"invalid 当前阶段: {declared or 'missing'}")
    errors.extend(validate_brief_metadata(project, text))
    drift_errors = validate_downstream_artifact_drift(project, declared)
    if status == "阻塞" or is_legacy:
        warnings.extend(f"返工中保留下游产物: {item}" for item in drift_errors)
    else:
        errors.extend(drift_errors)
    if risk not in {"A", "B", "C"}:
        errors.append(f"invalid 风险等级: {risk or 'missing'}")
    if declared in STAGES and STAGES.index(declared) < STAGES.index(inferred):
        message = f"阶段落后于产物: brief={declared}, inferred={inferred}"
        if status == "阻塞" or is_legacy:
            warnings.append(f"返工中保留旧产物: {message}")
        else:
            errors.append(message)
    elif declared in STAGES and STAGES.index(declared) > STAGES.index(inferred):
        message = f"阶段缺少连续前置产物: brief={declared}, complete_through={inferred}"
        if is_legacy:
            warnings.append(f"历史证据缺口：{message}")
        else:
            errors.append(message)

    return errors, warnings, declared, inferred


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    errors, warnings, declared, inferred = validate_project(args.project)

    for item in errors:
        print(f"ERROR {item}")
    for item in warnings:
        print(f"WARN {item}")
    if errors:
        return 1
    print(f"OK stage={declared} inferred={inferred}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
