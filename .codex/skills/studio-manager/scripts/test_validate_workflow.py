import tempfile
import unittest
import hashlib
import re
from pathlib import Path

import validate_workflow
import audit_skill_routing
import generate_dashboard
import set_project_state


class ContentValidationTest(unittest.TestCase):
    def project(self, brief: str) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "brief.md").write_text(brief, encoding="utf-8")
        return root

    def test_outline_requires_handoff_sections(self):
        project = self.project("- 平台计划：抖音\n- **当前阶段**：写稿中\n")
        path = project / "02script/outline.md"
        path.parent.mkdir()
        path.write_text("# 大纲\n## 目标观众\n小白", encoding="utf-8")
        errors, _ = validate_workflow.validate_content(project, project.joinpath("brief.md").read_text(), "写稿中")
        self.assertTrue(any("outline missing" in item for item in errors))

    def test_publish_pack_rejects_unplanned_platform(self):
        project = self.project("- 平台计划：抖音主发\n- **当前阶段**：讲戏中\n")
        path = project / "02script/publish-pack.md"
        path.parent.mkdir()
        path.write_text("# 发布包\n## 抖音主版\n内容\n## 小红书适配版\n内容", encoding="utf-8")
        errors, _ = validate_workflow.validate_content(project, project.joinpath("brief.md").read_text(), "讲戏中")
        self.assertTrue(any("unplanned platform" in item for item in errors))

    def test_publish_record_requires_default_snapshots(self):
        project = self.project("- 平台计划：抖音\n- **当前阶段**：已发布\n")
        path = project / "07publish/publish.md"
        path.parent.mkdir(parents=True)
        path.write_text("# 发布记录\nT+1", encoding="utf-8")
        errors, _ = validate_workflow.validate_content(project, project.joinpath("brief.md").read_text(), "已发布")
        self.assertTrue(any("T+7" in item for item in errors))
        self.assertFalse(any("T+3" in item or "T+30" in item for item in errors))

    def test_outline_accepts_equivalent_handoff_headings(self):
        project = self.project("- 平台计划：抖音\n- **当前阶段**：写稿中\n")
        path = project / "02script/outline.md"
        path.parent.mkdir()
        path.write_text(
            "## 目标观众\n小白\n## 承诺链\n结果\n## 证据来源\n来源\n"
            "## 风险边界\n边界\n## 主故事结构\n结构",
            encoding="utf-8",
        )
        errors, _ = validate_workflow.validate_content(project, project.joinpath("brief.md").read_text(), "写稿中")
        self.assertFalse(any("outline missing" in item for item in errors))

    def test_outline_rejects_empty_required_section(self):
        project = self.project("- 平台计划：抖音\n- **当前阶段**：写稿中\n")
        path = project / "02script/outline.md"
        path.parent.mkdir()
        path.write_text(
            "## 目标观众\n小白\n## 核心承诺\n待填\n## 证据来源\n来源\n"
            "## 风险边界\n边界\n## 内容结构\n结构",
            encoding="utf-8",
        )
        errors, _ = validate_workflow.validate_content(project, project.joinpath("brief.md").read_text(), "写稿中")
        self.assertTrue(any("核心承诺" in item for item in errors))

    def test_outline_v2_requires_experiment_packaging_and_experience_fields(self):
        project = self.project("- 平台计划：抖音\n- **当前阶段**：写稿中\n")
        path = project / "02script/outline.md"
        path.parent.mkdir()
        path.write_text(
            "- 大纲契约版本：2\n## 目标观众\n小白\n## 核心承诺\n结果\n"
            "## 证据来源\n来源\n## 风险边界\n边界\n## 内容结构\n结构",
            encoding="utf-8",
        )
        errors, _ = validate_workflow.validate_content(project, project.joinpath("brief.md").read_text(), "写稿中")
        self.assertTrue(any("outline v2 missing" in item for item in errors))

    def test_outline_v2_accepts_complete_contract(self):
        project = self.project("- 平台计划：抖音\n- **当前阶段**：写稿中\n")
        path = project / "02script/outline.md"
        path.parent.mkdir()
        path.write_text(
            "- 大纲契约版本：2\n- 目标观众：小白\n- 核心承诺：完成任务\n"
            "- 证据来源：本人实测\n- 风险边界：不保证平台结果\n- 内容结构：结果到步骤\n"
            "- 生产策略：探索性实验\n- 假设来源：探索性实验\n- 已知混杂变量：发布时间\n"
            "## 临时包装原型\n同一承诺\n- 首个可见兑现：前 12 秒展示结果\n"
            "- 体验峰值：真实运行成功\n- 结束记忆：一句可复述结论",
            encoding="utf-8",
        )
        errors, _ = validate_workflow.validate_content(project, project.joinpath("brief.md").read_text(), "写稿中")
        self.assertFalse(any("outline" in item for item in errors))

    def test_outline_v2_requires_first_proof_time(self):
        project = self.project("- 平台计划：抖音\n- **当前阶段**：写稿中\n")
        path = project / "02script/outline.md"
        path.parent.mkdir()
        path.write_text(
            "- 大纲契约版本：2\n- 目标观众：小白\n- 核心承诺：完成任务\n"
            "- 证据来源：本人实测\n- 风险边界：无夸大\n- 内容结构：结果到步骤\n"
            "- 生产策略：已验证模式复用\n- 假设来源：learning-log.md 第9条\n"
            "- 已知混杂变量：发布时间\n## 临时包装原型\n同一承诺\n"
            "- 首个可见兑现：展示结果\n- 体验峰值：运行成功\n- 结束记忆：记住一句话",
            encoding="utf-8",
        )
        errors, _ = validate_workflow.validate_content(project, project.joinpath("brief.md").read_text(), "写稿中")
        self.assertTrue(any("expected time" in item for item in errors))

    def test_publish_pack_allows_populated_nested_list(self):
        project = self.project("- 平台计划：抖音\n- **当前阶段**：讲戏中\n")
        path = project / "02script/publish-pack.md"
        path.parent.mkdir()
        path.write_text(
            "# 发布包\n## 内容母版\n- 核心事实与来源：\n  - 官方来源\n"
            "## 抖音主版\n- 包装版本：DY-v1",
            encoding="utf-8",
        )
        errors, _ = validate_workflow.validate_content(project, project.joinpath("brief.md").read_text(), "讲戏中")
        self.assertFalse(any("blank fields" in item for item in errors))

    def test_publish_pack_rejects_truly_blank_list_field(self):
        self.assertTrue(validate_workflow.has_blank_list_field("- 首选：\n## 下一节\n"))


class BriefValidationHelpersTest(unittest.TestCase):
    def test_status_and_mode_vocabularies_are_explicit(self):
        self.assertNotIn("未阻塞", validate_workflow.STATUSES)
        self.assertEqual({"标准", "快速"}, validate_workflow.WORK_MODES)

    def metadata_errors(self, status: str, blocked: str, mode: str = "标准") -> list[str]:
        project = Path(tempfile.mkdtemp()) / "accounts/测试账号/videos/测试项目"
        text = (
            "- 账号：测试账号\n"
            f"- 工作模式：{mode}\n"
            f"- **阶段状态**：{status}\n"
            f"- **阻塞原因**：{blocked}\n"
        )
        return validate_workflow.validate_brief_metadata(project, text)

    def test_waiting_requires_confirmation_object(self):
        self.assertTrue(any("confirmation object" in item for item in self.metadata_errors("等待老板确认", "无")))

    def test_blocked_requires_reason(self):
        self.assertTrue(any("must name" in item for item in self.metadata_errors("阻塞", "无")))

    def test_active_requires_no_blocker(self):
        self.assertTrue(any("进行中" in item for item in self.metadata_errors("进行中", "仍缺素材")))

    def test_invalid_mode_is_rejected(self):
        self.assertTrue(any("工作模式" in item for item in self.metadata_errors("进行中", "无", "极速")))

    def test_account_must_match_project_path(self):
        project = Path(tempfile.mkdtemp()) / "accounts/甲/videos/项目"
        text = "- 账号：乙\n- 工作模式：标准\n- **阶段状态**：进行中\n- **阻塞原因**：无\n"
        errors = validate_workflow.validate_brief_metadata(project, text)
        self.assertTrue(any("账号与项目路径不一致" in item for item in errors))

    def test_legacy_exception_keeps_metadata_strict_but_downgrades_missing_chain(self):
        project = Path(tempfile.mkdtemp()) / "accounts/测试账号/videos/历史项目"
        project.mkdir(parents=True)
        (project / "brief.md").write_text(
            "- 平台计划：抖音\n- 账号：测试账号\n- 工作模式：标准\n- 风险等级：B\n"
            "- **当前阶段**：已发布\n- **阶段状态**：完成\n- **阻塞原因**：无\n"
            "- 历史例外：已实际发布，但旧流程未保留完整证据链\n",
            encoding="utf-8",
        )
        errors, warnings, _, _ = validate_workflow.validate_project(project)
        self.assertEqual([], errors)
        self.assertTrue(any("历史例外" in item for item in warnings))
        self.assertTrue(any("历史证据缺口" in item for item in warnings))

    def test_downstream_artifact_exposes_stale_shooting_stage(self):
        project = Path(tempfile.mkdtemp()) / "accounts/测试账号/videos/测试项目"
        project.mkdir(parents=True)
        (project / "brief.md").write_text(
            "- 平台计划：抖音\n- 账号：测试账号\n- 工作模式：标准\n- 风险等级：B\n"
            "- **当前阶段**：拍摄中\n- **阶段状态**：进行中\n- **阻塞原因**：无\n",
            encoding="utf-8",
        )
        review = project / "06video/review.md"
        review.parent.mkdir(parents=True)
        review.write_text("# 发布前审核\n- 结论：修改后复审\n- 阻断问题数：4\n", encoding="utf-8")

        errors, _, _, _ = validate_workflow.validate_project(project)

        self.assertTrue(any("downstream artifact/state drift" in item for item in errors))

    def test_failed_review_can_remain_during_editing_rework(self):
        project = Path(tempfile.mkdtemp()) / "accounts/测试账号/videos/测试项目"
        project.mkdir(parents=True)
        review = project / "06video/review.md"
        review.parent.mkdir(parents=True)
        review.write_text("# 发布前审核\n- 结论：修改后复审\n- 阻断问题数：1\n", encoding="utf-8")

        self.assertEqual([], validate_workflow.validate_downstream_artifact_drift(project, "剪辑中"))


class DashboardTest(unittest.TestCase):
    def test_dashboard_exposes_only_current_decision_and_folds_history(self):
        root = Path(tempfile.mkdtemp())
        current = root / "accounts/测试账号/videos/当前项目"
        current.mkdir(parents=True)
        (current / "brief.md").write_text(
            "- 平台计划：抖音\n- 账号：测试账号\n- 工作模式：标准\n- 风险等级：B\n"
            "- **当前阶段**：提案中\n- **阶段状态**：等待老板确认\n"
            "- **阻塞原因**：等待确认选题卡\n",
            encoding="utf-8",
        )
        (root / "studio-state.json").write_text(
            '{"current_video":"accounts/测试账号/videos/当前项目"}',
            encoding="utf-8",
        )
        output = generate_dashboard.generate(root)
        text = output.read_text(encoding="utf-8")
        self.assertIn("## 老板当前视图", text)
        self.assertIn("下一批准卡：选题卡", text)
        self.assertIn("现在需要老板：等待确认选题卡", text)
        for command in ("开始一期", "继续当前视频", "我来确认", "数据来了"):
            self.assertIn(command, text)
        self.assertIn("<summary>历史、已完成与例外项目</summary>", text)


class ProjectStateSetterTest(unittest.TestCase):
    def project(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "studio-state.json").write_text("{}", encoding="utf-8")
        project = root / "accounts/测试账号/videos/测试项目"
        project.mkdir(parents=True)
        (project / "brief.md").write_text(
            "- 平台计划：抖音\n- 账号：测试账号\n- 工作模式：标准\n"
            "- 风险等级：B\n- **当前阶段**：提案中\n- **阶段状态**：进行中\n"
            "- **阻塞原因**：无\n",
            encoding="utf-8",
        )
        return project

    def test_valid_update_refreshes_dashboard(self):
        project = self.project()
        board = set_project_state.update_project(
            project,
            stage="提案中",
            status="等待老板确认",
            blocker="等待确认选题卡",
            risk="C",
        )
        text = (project / "brief.md").read_text(encoding="utf-8")
        self.assertIn("风险等级：C", text)
        self.assertIn("等待确认选题卡", text)
        self.assertTrue(board.is_file())
        self.assertIn("测试项目", board.read_text(encoding="utf-8"))

    def test_invalid_transition_rolls_back(self):
        project = self.project()
        original = (project / "brief.md").read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "brief restored"):
            set_project_state.update_project(
                project,
                stage="写稿中",
                status="进行中",
                blocker="无",
            )
        self.assertEqual(original, (project / "brief.md").read_text(encoding="utf-8"))

    def test_invalid_enum_never_writes(self):
        project = self.project()
        original = (project / "brief.md").read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid stage"):
            set_project_state.update_project(
                project,
                stage="快完成了",
                status="进行中",
                blocker="无",
            )
        self.assertEqual(original, (project / "brief.md").read_text(encoding="utf-8"))

    def test_wip_limit_rolls_back_second_planning_project(self):
        first = self.project()
        second = first.parent / "另一项目"
        second.mkdir()
        (second / "brief.md").write_text(
            (first / "brief.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        original = (second / "brief.md").read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "WIP limit exceeded"):
            set_project_state.update_project(
                second,
                stage="提案中",
                status="进行中",
                blocker="无",
            )
        self.assertEqual(original, (second / "brief.md").read_text(encoding="utf-8"))


class LifecycleIntegrationTest(unittest.TestCase):
    def complete_project(self, stage: str = "已复盘") -> Path:
        root = Path(tempfile.mkdtemp())
        project = root / "accounts/测试账号/videos/测试项目"
        project.mkdir(parents=True)
        (project / "brief.md").write_text(
            "- 平台计划：抖音\n- 账号：测试账号\n- 工作模式：标准\n- 风险等级：B\n"
            f"- **当前阶段**：{stage}\n- **阶段状态**：完成\n- **阻塞原因**：无\n",
            encoding="utf-8",
        )
        video_bytes = b"real-video"
        video_hash = hashlib.sha256(video_bytes).hexdigest()
        files = {
            "02script/outline.md": "## 目标观众\n小白\n## 核心承诺\n结果\n## 证据来源\n来源\n## 风险边界\n边界\n## 内容结构\n结构",
            "02script/script.md": "# 逐字稿\n真实正文",
            "02script/publish-pack.md": "# 发布包\n## 内容母版\n真实内容\n## 抖音主版\n- 包装版本：DY-v1",
            "03outputs/分镜.md": "# 分镜\n真实镜头",
            "03outputs/shot-checklist.md": "| 镜头ID | 必拍 | 验收标准 | 状态 |\n|---|---|---|---|\n| S01 | 是 | 看清结果 | 完成 |",
            "04media/asset-manifest.md": "# 素材清单\n真实素材\n## 必需素材缺口\n- 无",
            "04media/shoot-log.md": "# 拍摄记录\n[x] 所有必拍镜头完成\n[x] 所有必需录屏完成\n[x] 素材研究员已按 `shot-checklist.md` 完成验收",
            "06video/edit-log.md": f"# 剪辑记录\n- 锁定成片文件：06video/final.mp4\n- 锁定成片 SHA-256：{video_hash}",
            "06video/review.md": f"# 发布前审核\n- 审核执行方式：独立子 Agent\n- 审核任务 ID：review-001\n- 审核输入清单：brief / config / 成片\n- 锁定成片文件：06video/final.mp4\n- 锁定成片 SHA-256：{video_hash}\n- 结论：通过\n- 阻断问题数：0",
            "prediction.md": f"# 发布前预测\n- 写入时间：2026-07-23 10:00\n- 锁定成片文件：06video/final.mp4\n- 锁定成片 SHA-256：{video_hash}\n- 一句话预测：定性",
            "07publish/publish.md": f"# 发布记录\n- 锁定成片文件：06video/final.mp4\n- 锁定成片 SHA-256：{video_hash}\n## 抖音\n- 状态：已发布\n- 发布时间：2026-07-23 12:00\n- 链接或平台 ID：https://example.com/1\n- 使用的包装版本：DY-v1\nT+1\nT+3\nT+7\nT+30\n| T+1 | 2026-07-24 12:00 | 100 | | | 5 | | | | | | screenshot.png |",
            "08retro/retro.md": "# 复盘\n## 数据摘要\n已有真实数据",
        }
        for relative, content in files.items():
            path = project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        prediction_hash = hashlib.sha256((project / "prediction.md").read_bytes()).hexdigest()
        publish = project / "07publish/publish.md"
        publish.write_text(
            publish.read_text(encoding="utf-8")
            + f"\n- 发布前 prediction.md SHA-256：{prediction_hash}\n",
            encoding="utf-8",
        )
        (project / "06video/final.mp4").write_bytes(video_bytes)
        return project

    def errors(self, project: Path) -> list[str]:
        return validate_workflow.validate_project(project)[0]

    def test_complete_lifecycle_passes(self):
        self.assertEqual([], self.errors(self.complete_project()))

    def test_published_requires_real_video(self):
        project = self.complete_project("已发布")
        (project / "06video/final.mp4").unlink()
        self.assertTrue(any("exported video" in item for item in self.errors(project)))

    def test_published_requires_edit_log(self):
        project = self.complete_project("已发布")
        (project / "06video/edit-log.md").unlink()
        self.assertTrue(any("edit-log" in item for item in self.errors(project)))

    def test_published_requires_passed_review(self):
        project = self.complete_project("已发布")
        (project / "06video/review.md").write_text("- 结论：修改后复审\n- 阻断问题数：1", encoding="utf-8")
        self.assertTrue(any("independent review" in item for item in self.errors(project)))

    def test_published_requires_prediction(self):
        project = self.complete_project("已发布")
        (project / "prediction.md").unlink()
        self.assertTrue(any("prediction" in item for item in self.errors(project)))

    def test_published_requires_time_and_link(self):
        project = self.complete_project("已发布")
        (project / "07publish/publish.md").write_text("- 状态：已发布\nT+1\nT+3\nT+7\nT+30", encoding="utf-8")
        self.assertTrue(any("publish record" in item for item in self.errors(project)))

    def test_retro_requires_publish_record(self):
        project = self.complete_project()
        (project / "07publish/publish.md").unlink()
        self.assertTrue(any("publish record" in item for item in self.errors(project)))

    def test_retro_requires_populated_snapshot(self):
        project = self.complete_project()
        publish = project / "07publish/publish.md"
        publish.write_text("- 状态：已发布\n- 发布时间：2026-07-23\n- 链接或平台 ID：id\nT+1\nT+3\nT+7\nT+30", encoding="utf-8")
        self.assertTrue(any("data snapshot" in item for item in self.errors(project)))

    def test_published_rejects_prediction_after_publish(self):
        project = self.complete_project("已发布")
        prediction = project / "prediction.md"
        prediction.write_text(prediction.read_text(encoding="utf-8").replace("2026-07-23 10:00", "2026-07-23 13:00"), encoding="utf-8")
        prediction_hash = hashlib.sha256(prediction.read_bytes()).hexdigest()
        publish = project / "07publish/publish.md"
        text = re.sub(r"发布前 prediction\.md SHA-256：\S+", f"发布前 prediction.md SHA-256：{prediction_hash}", publish.read_text(encoding="utf-8"))
        publish.write_text(text, encoding="utf-8")
        self.assertTrue(any("before 发布时间" in item for item in self.errors(project)))

    def test_published_rejects_changed_prediction(self):
        project = self.complete_project("已发布")
        prediction = project / "prediction.md"
        prediction.write_text(prediction.read_text(encoding="utf-8") + "\n事后修改", encoding="utf-8")
        self.assertTrue(any("changed after publish" in item for item in self.errors(project)))

    def test_edit_plan_is_not_real_video(self):
        project = self.complete_project("审核中")
        (project / "06video/final.mp4").unlink()
        (project / "06video/edit-plan.md").write_text("# 剪辑说明书", encoding="utf-8")
        self.assertTrue(any("exported video" in item for item in self.errors(project)))

    def test_review_requires_independent_audit_metadata(self):
        project = self.complete_project("审核通过")
        review = project / "06video/review.md"
        review.write_text("- 结论：通过\n- 阻断问题数：0", encoding="utf-8")
        self.assertTrue(any("independent review" in item for item in self.errors(project)))

    def test_lifecycle_rejects_different_locked_video(self):
        project = self.complete_project("已发布")
        other = project / "06video/other.mp4"
        other.write_bytes(b"other-video")
        other_hash = hashlib.sha256(other.read_bytes()).hexdigest()
        prediction = project / "prediction.md"
        text = prediction.read_text(encoding="utf-8")
        text = text.replace("06video/final.mp4", "06video/other.mp4")
        text = re.sub(r"锁定成片 SHA-256：\S+", f"锁定成片 SHA-256：{other_hash}", text)
        prediction.write_text(text, encoding="utf-8")
        publish = project / "07publish/publish.md"
        publish_text = publish.read_text(encoding="utf-8")
        prediction_hash = hashlib.sha256(prediction.read_bytes()).hexdigest()
        publish.write_text(re.sub(r"发布前 prediction\.md SHA-256：\S+", f"发布前 prediction.md SHA-256：{prediction_hash}", publish_text), encoding="utf-8")
        self.assertTrue(any("differs across" in item for item in self.errors(project)))

    def test_publish_fields_cannot_mix_across_platforms(self):
        project = self.complete_project("已发布")
        brief = project / "brief.md"
        brief.write_text(brief.read_text(encoding="utf-8").replace("平台计划：抖音", "平台计划：抖音 / 小红书"), encoding="utf-8")
        publish = project / "07publish/publish.md"
        text = publish.read_text(encoding="utf-8")
        text = text.replace("- 发布时间：2026-07-23 12:00", "- 发布时间：")
        text += "\n## 小红书\n- 状态：待发布\n- 发布时间：2026-07-24\n- 链接或平台 ID：xhs-id\n- 使用的包装版本：XHS-v1\n"
        publish.write_text(text, encoding="utf-8")
        self.assertTrue(any("publish record" in item for item in self.errors(project)))

    def test_snapshot_requires_metric_and_evidence(self):
        project = self.complete_project()
        publish = project / "07publish/publish.md"
        text = re.sub(
            r"\| T\+1 \|[^\n]+",
            "| T+1 | 2026-07-24 12:00 | | | | | | | | | | screenshot.png |",
            publish.read_text(encoding="utf-8"),
        )
        publish.write_text(text, encoding="utf-8")
        self.assertTrue(any("data snapshot" in item for item in self.errors(project)))


class SkillRoutingAuditTest(unittest.TestCase):
    def test_rejects_missing_style_bible_and_inactive_account_rule(self):
        root = Path(tempfile.mkdtemp())
        (root / "studio-state.json").write_text("{}", encoding="utf-8")
        rules = root / "accounts/测试账号/skill-base/提案师/account-rules.md"
        rules.parent.mkdir(parents=True)
        rules.write_text("# 规则\n\n| X | 已废止 |\n", encoding="utf-8")

        errors = audit_skill_routing.audit(root)

        self.assertTrue(any("missing style-bible" in item for item in errors))
        self.assertTrue(any("canonical sections" in item for item in errors))
        self.assertTrue(any("inactive rule" in item for item in errors))

    def test_rejects_redundant_global_skill_and_missing_marker(self):
        root = Path(tempfile.mkdtemp())
        (root / "studio-state.json").write_text("{}", encoding="utf-8")
        skill = root / ".codex/skills/media-pitcher/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: media-pitcher\ndescription: 选题\n---\n", encoding="utf-8")
        global_skills = root / "global-skills"
        (global_skills / "media-pitcher").mkdir(parents=True)

        errors = audit_skill_routing.audit(root, global_skills)

        self.assertTrue(any("routing metadata incomplete" in item for item in errors))
        self.assertTrue(any("redundant global Crew skill" in item for item in errors))

    def test_rejects_missing_douyin_research_script(self):
        root = Path(tempfile.mkdtemp())
        (root / "studio-state.json").write_text("{}", encoding="utf-8")
        skill_root = root / ".codex/skills"
        for name in audit_skill_routing.PROJECT_SKILLS:
            skill = skill_root / name / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text(
                f"---\nname: {name}\ndescription: studio-state.json FilmCrew\n---\n",
                encoding="utf-8",
            )
        errors = audit_skill_routing.audit(root)
        self.assertTrue(any("Douyin research script" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
