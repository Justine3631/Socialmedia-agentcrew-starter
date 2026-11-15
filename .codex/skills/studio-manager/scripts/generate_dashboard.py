#!/usr/bin/env python3
"""Generate a read-only Markdown project dashboard."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from validate_workflow import extract, validate_project


NEXT_ROLE = {
    "提案中": "提案师",
    "写稿中": "编剧",
    "讲戏中": "导演",
    "素材中": "资产制片",
    "拍摄中": "拍摄",
    "剪辑中": "剪辑师",
    "审核中": "审核员",
    "审核通过": "复盘员（发布前预测）",
    "已发布": "复盘员",
    "已复盘": "无",
}

APPROVAL_CARD = {
    "提案中": "选题卡",
    "写稿中": "内容与开拍卡",
    "讲戏中": "内容与开拍卡",
    "素材中": "内容与开拍卡",
    "拍摄中": "内容与开拍卡",
    "剪辑中": "制作预览卡",
    "审核中": "完整成片与发布卡",
    "审核通过": "完整成片与发布卡",
    "已发布": "无（等待数据复盘）",
    "已复盘": "无（项目完成）",
}


def approval_card(stage: str, status: str, blocked: str) -> str:
    if status == "等待老板确认":
        for card in ("选题卡", "内容与开拍卡", "制作预览卡", "完整成片与发布卡"):
            if card in blocked:
                return card
    return APPROVAL_CARD.get(stage, "历史 / 异常处理")


def boss_action(stage: str, status: str, blocked: str) -> str:
    if status == "等待老板确认":
        return blocked
    if status == "阻塞":
        return f"异常：{blocked}"
    if stage in {"已发布", "已复盘"}:
        return "无"
    return f"无；团队自动推进到{approval_card(stage, status, blocked)}"


def generate(workspace: Path, output: Path | None = None) -> Path:
    workspace = workspace.resolve()
    items: list[dict[str, str]] = []
    for brief in sorted(workspace.glob("accounts/*/videos/*/brief.md")):
        text = brief.read_text(encoding="utf-8")
        project = brief.parent
        stage = extract(text, "当前阶段") or "未知"
        status = extract(text, "阶段状态") or "未知"
        blocked = extract(text, "阻塞原因") or "未填写"
        risk = extract(text, "风险等级") or "未知"
        errors, warnings, _, _ = validate_project(project)
        legacy = extract(text, "历史例外") or "无"
        if errors:
            health = f"需处理 {len(errors)} 项"
        elif warnings:
            health = f"提醒 {len(warnings)} 项"
        else:
            health = "正常"
        modified = datetime.fromtimestamp(max(p.stat().st_mtime for p in project.rglob("*") if p.is_file())).strftime("%Y-%m-%d")
        items.append({
            "account": project.parent.parent.name,
            "project": project.name,
            "relative": project.relative_to(workspace).as_posix(),
            "stage": stage,
            "status": status,
            "risk": risk,
            "blocked": blocked,
            "next_role": NEXT_ROLE.get(stage, "待判断"),
            "health": health,
            "modified": modified,
            "legacy": legacy,
        })

    def row(item: dict[str, str]) -> str:
        return (
            f"| {item['account']} | {item['project']} | {item['stage']} | {item['status']} | {item['risk']} | "
            f"{item['blocked']} | {item['next_role']} | {item['health']} | {item['modified']} |"
        )

    active_rows = [
        row(item) for item in items
        if item["stage"] not in {"已发布", "已复盘"} and item["legacy"] == "无"
    ]
    history_rows = [
        row(item) for item in items
        if item["stage"] in {"已发布", "已复盘"} or item["legacy"] != "无"
    ]

    state_path = workspace / "studio-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    current_relative = state.get("current_video")
    current = next((item for item in items if item["relative"] == current_relative), None)
    if current:
        current_view = [
            f"- 当前账号：{current['account']}",
            f"- 当前项目：[{current['project']}]({current['relative']})",
            f"- 当前阶段：{current['stage']} / {current['status']}",
            f"- 下一批准卡：{approval_card(current['stage'], current['status'], current['blocked'])}",
            f"- 现在需要老板：{boss_action(current['stage'], current['status'], current['blocked'])}",
            f"- 项目校验：{current['health']}",
        ]
    else:
        current_view = [
            f"- 当前项目：{current_relative or '未设置'}",
            "- 现在需要老板：选择或新建一个真实项目",
        ]

    table_header = [
        "| 账号 | 项目 | 阶段 | 状态 | 风险 | 阻塞原因 | 下一岗位 | 校验 | 最近修改 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    content = "\n".join([
        "# 项目看板",
        "",
        "> 自动生成，只读；不要手工维护。状态来源仍是各项目 `brief.md` 和真实产物。",
        "",
        "## 老板当前视图",
        "",
        *current_view,
        "",
        "## 四个入口",
        "",
        "- `开始一期`：新建一期，团队自动推进到选题卡。",
        "- `继续当前视频`：读取真实状态，从当前缺口继续。",
        "- `我来确认`：只展示当前等待批准的一张卡。",
        "- `数据来了`：登记发布数据并进入复盘。",
        "",
        "## 在制项目",
        "",
        *table_header,
        *(active_rows or ["| - | 暂无 | - | - | - | - | - | - | - |"]),
        "",
        "<details>",
        "<summary>历史、已完成与例外项目</summary>",
        "",
        *table_header,
        *(history_rows or ["| - | 暂无 | - | - | - | - | - | - | - |"]),
        "",
        "</details>",
        "",
    ])
    output = output or workspace / "PROJECT_BOARD.md"
    output.write_text(content, encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = generate(args.workspace, args.output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
