# Crew · Content Studio Workbench

English · [简体中文](README.md)

Run content production as a small studio. You set the goal; a producer coordinates eight specialist roles. Files preserve project state, and four approval cards keep key decisions with you. Built for talking-head videos, tutorials, screen recordings, and commerce content.

This is a **complete project workspace**, not a standalone installable skill. Download the whole repository, including hidden directories. This starter includes only a fictional `demo` account, with no original user's projects, media, login data, or Git history. Workflow instructions are primarily Chinese; the English README explains setup and operation.

## Quick start

1. Clone the repository, or choose **Code → Download ZIP** on GitHub and extract it:

   ```bash
   git clone https://github.com/Justine3631/Socialmedia-agentcrew-starter.git
   cd Socialmedia-agentcrew-starter
   ```

2. Open this directory in a coding agent with local file access and command execution. The original workflow targets Codex. Other hosts need their own skill-loading and independent-subagent support.
3. Send:

   > Read AGENTS.md and studio-state.json. Help me configure the demo account's positioning, audience, publishing platform, and production constraints. Then start a video about [your idea]. Respond in English.

4. Review the approval cards and supply required footage. Editing and generation services are unnecessary before approving the first topic card.

Canonical skills live in `.codex/skills/`; `.agents/skills/` contains repository-relative links to those folders. If your host does not discover them, explicitly ask it to read `AGENTS.md` and `.codex/skills/studio-manager/SKILL.md`. Keep these roles inside the repository: they depend on its rules, templates, and account files.

## Everyday commands

| Say | Result |
|---|---|
| Start an episode about … | Confirm the account, create a project, prepare the topic card |
| Continue the current video | Check actual files and state, then resume from missing work |
| I'm ready to review | Show the card awaiting approval |
| Here are the metrics … | Record data, review results, and log hypotheses |
| Save this idea … | Add it to the active account's idea pool without creating a project |
| Show the project board | Generate a read-only dashboard |

The approval cards are **topic → content and shooting → production preview → complete video and publishing**. Approval of the final card does not mean the video has been published. Record the actual publishing result separately.

## Roles and deliverables

| Role | Skill | Main deliverables |
|---|---|---|
| Producer | `studio-manager` | Account/project state and handoffs |
| Strategist | `media-pitcher` | Evidence, topic validation, outline |
| Scriptwriter | `media-screenwriter` | Script and platform publishing package |
| Director | `media-director` | Storyboard, filming guidance, checklist |
| Asset producer | `media-asset-researcher` | Sourced and licensed assets, covers, narration QA |
| Editor | `media-editor` | Timeline, preview, final video or edit plan |
| Reviewer | `media-reviewer` | Independent review report; no edits |
| Analyst | `media-retro` | Pre-publication prediction, publishing log, retrospective |

Ordinary roles load their skills directly. Pre-publication review requires an isolated independent subagent. Without that capability, report a blocker rather than reviewing within the creative conversation.

## Dependencies and fallbacks

The workbench does not automatically install tools, sign into services, or purchase access. Check availability and cost when a capability becomes necessary.

| Capability | Optional dependency | Fallback |
|---|---|---|
| Validation and dashboard | Python 3.10+, standard library | Install Python; never claim unperformed checks passed |
| Web/platform research | Agent Reach, available search tools, or browser | Use supplied sources and mark evidence gaps |
| Douyin research script | OpenCLI with your own browser profile | Skip the script and use available read-only research |
| Main editing and export | Connected ChatCut tools and skills | Deliver `edit-plan.md`; do not claim a rendered video exists |
| Deterministic motion | HyperFrames and project-local GSAP | Simplify the shot or record the gap; pin dependencies when used |
| Covers, AI video, synthetic voice | Relevant generation tools/plugins | Use footage, recordings, or licensed assets; disclose material changes |
| Speech content and media search | External skills such as `interflowai-koubo-script` and `media-use` | Use included role methods and supplied assets; document fallback |

Node.js is needed only for motion development and its tests; use a supported LTS release. External skills, ChatCut, HyperFrames, and generation services are not bundled. Full layered collage / AI narrative production belongs in a separately configured workspace, which is not included. Platform and product claims in reference notes require current official-source verification.

## Structure and state

```text
AGENTS.md                  # Entry point and routing
studio-state.json          # Active account and project
.codex/skills/             # Eight role bodies, scripts, and resources
.codex/agents/             # Independent reviewer instructions
.agents/skills/            # Repository-local discovery links
shared/workflow-rules.md   # Cross-role source of truth
shared/skill-bases/        # Shared methods
shared/templates/          # Templates used at the appropriate stage
accounts/demo/             # Fictional configuration and empty rules
```

Create projects only under `accounts/<account>/videos/YYYY-MM-DD_short-title/`, with eight stage folders from `01assets/` through `08retro/`. A project's `brief.md` stores its stage, status, and blockers. Actual nonempty deliverables establish completion. `PROJECT_BOARD.md` is a derived view, not a state source.

Edit `accounts/demo/config.md` to set your positioning. To add an account, copy the example structure and update the account list and active pointers in `studio-state.json`. Record confirmed preferences in the relevant `account-rules.md`; tentative observations belong in `learning-log.md`. Empty templates never count as finished work.

## Checks

Run from the repository root:

```bash
python3 .codex/skills/studio-manager/scripts/audit_skill_routing.py
python3 .codex/skills/studio-manager/scripts/generate_dashboard.py
python3 -m unittest discover -s .codex/skills/studio-manager/scripts -p 'test_*.py'
python3 -m unittest discover -s .codex/skills/media-pitcher/scripts -p 'test_*.py'
node --test .codex/skills/media-editor/assets/motion-kit/editorial-motion.test.mjs
```

After creating a project:

```bash
python3 .codex/skills/studio-manager/scripts/validate_workflow.py accounts/demo/videos/YYYY-MM-DD_short-title
```

Change lifecycle fields only through `set_project_state.py`; see its `--help`. Passing automated checks does not establish that external editing services, generation quality, or publishing performance have been tested.

## Privacy and licensing

This starter was exported from an explicit file allowlist with fresh Git history. It excludes private accounts, video projects, voice samples, original safe-zone screenshots, browser profiles, session logs, and credentials. Test data is fictional. Obtain licensed sound effects yourself. Fonts retain their licenses.

`.gitignore` excludes new account/video data, environment files, session files, and output directories by default. **Already tracked example files and `studio-state.json` remain tracked after editing.** Review every diff before committing or publishing personal configurations. Never put credentials into Markdown, scripts, or Git history.

Workflow and code retain the [MIT License](LICENSE) and original copyright notice. Bundled fonts use their directory-specific SIL OFL licenses. External tools, plugins, GSAP, and other third-party content retain their respective terms; the repository's MIT license does not override them. Method references remain credited in the relevant files.
