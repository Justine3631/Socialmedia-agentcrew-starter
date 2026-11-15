# Crew · 自媒体工作台

[English](README.en.md) · 简体中文

把内容创作组织成一间小型工作室：你说明目标，总制片人协调八个岗位，文件保存进度，四张批准卡控制关键决策。适合真人口播、教程、录屏和带货内容。

这是**整套项目工作台**，不是单个可独立安装的 Skill。请下载整个仓库，保留隐藏目录。此分享版只有虚构的 `demo` 账号，不含原使用者的项目、素材、登录信息或 Git 历史。

## 快速开始

1. 克隆仓库，或在 GitHub 选择 **Code → Download ZIP** 后解压：

   ```bash
   git clone https://github.com/Justine3631/Socialmedia-agentcrew-starter.git
   cd Socialmedia-agentcrew-starter
   ```

2. 用支持本地文件与命令执行的编码 Agent 打开这个目录。原工作流面向 Codex；其他宿主须自行确认技能加载和独立子 Agent 能力。
3. 发送：

   > 读取 AGENTS.md 和 studio-state.json。先帮我设置 demo 账号的定位、受众、发布平台和制作条件，然后开始一期视频：〔你的想法〕。

4. 按批准卡确认方向，提供所需真人素材；首次选题卡通过前不需要配置剪辑或生成服务。

岗位正文在 `.codex/skills/`，`.agents/skills/` 是指向正文的仓库内相对链接。若宿主未自动发现技能，请明确要求它读取 `AGENTS.md` 和 `.codex/skills/studio-manager/SKILL.md`。无需把整套岗位复制到全局技能目录；它们依赖本仓库的规则、模板与账号文件。

## 日常怎么用

| 你说 | 工作台处理 |
|---|---|
| 开始一期：…… | 确认账号，创建项目，推进到选题卡 |
| 继续当前视频 | 核对真实产物和状态，从缺口继续 |
| 我来确认 | 展示当前等待批准的卡片 |
| 数据来了：…… | 登记数据，复盘与记录假设 |
| 记个灵感：…… | 进入当前账号灵感池，不自动立项 |
| 项目看板 | 生成当前状态的只读看板 |

四张批准卡依次是：**选题卡 → 内容与开拍卡 → 制作预览卡 → 完整成片与发布卡**。最后一张卡通过不表示已经发布；实际发布结果须另行登记。

## 岗位与交付物

| 岗位 | Skill | 主要交付物 |
|---|---|---|
| 总制片人 | `studio-manager` | 项目与账号状态、岗位衔接 |
| 提案师 | `media-pitcher` | 调研证据、选题、大纲 |
| 编剧 | `media-screenwriter` | 逐字稿、分平台发布包 |
| 导演 | `media-director` | 分镜、拍摄提示和清单 |
| 资产制片 | `media-asset-researcher` | 素材来源与许可、封面、旁白验收 |
| 剪辑师 | `media-editor` | 时间线、样片、成片或剪辑说明书 |
| 审核员 | `media-reviewer` | 独立审核报告，只审不改 |
| 复盘员 | `media-retro` | 发布前预测、发布记录与数据复盘 |

普通岗位直接读取 Skill；发布前审核必须使用隔离的独立子 Agent。宿主不支持时应报告阻塞，不以创作上下文自审代替。

## 依赖与降级

工作台不会自动安装、登录或购买外部服务。需要哪项能力时，再确认可用工具和费用。

| 能力 | 可选依赖 | 不可用时 |
|---|---|---|
| 状态校验与看板 | Python 3.10+，标准库 | 安装 Python 后运行；不要伪造校验通过 |
| 网页、平台调研 | Agent Reach、可用搜索工具或浏览器 | 使用你提供的资料，标明未核验证据 |
| 抖音检索脚本 | OpenCLI 与使用者自己的浏览器 profile | 跳过脚本，使用可用的只读检索方式 |
| 主剪辑与导出 | 已连接的 ChatCut 及其工具/技能 | 交付 `edit-plan.md`，不声称已有成片 |
| 确定性动效 | HyperFrames、项目内 GSAP 依赖 | 简化镜头或记录缺口；项目内按需锁版本 |
| 封面、AI 视频、合成声音 | 相应生成工具或插件 | 使用实拍、录屏或已有授权素材；影响交付时说明 |
| 口播内容包、媒体检索 | `interflowai-koubo-script`、`media-use` 等外部技能 | 使用岗位内方法与已有素材，记录降级 |

Node.js 只在动效开发与相应测试时需要，建议使用受支持的 LTS 版本。本仓库不附带外部 Skill、ChatCut、HyperFrames 或生成服务。完整多层拼贴 / AI 叙事属于另行配置的独立工作台，本仓库不包含它。共享知识中的平台机制和工具信息属于方法参考，使用前核验当前官方来源。

## 目录与状态

```text
AGENTS.md                  # 入口与路由
studio-state.json          # 当前账号与项目
.codex/skills/             # 八个岗位正文、脚本与资源
.codex/agents/             # 独立审核员说明
.agents/skills/            # 仓库内技能发现链接
shared/workflow-rules.md   # 跨岗位流程唯一规则
shared/skill-bases/        # 共享方法
shared/templates/          # 按阶段使用的模板
accounts/demo/             # 虚构账号配置与空规则
```

项目仅创建在 `accounts/<账号>/videos/YYYY-MM-DD_短标题/`，内部使用 `01assets/` 至 `08retro/` 八个阶段目录。项目 `brief.md` 记录阶段、状态和阻塞原因；实际非空产物证明完成情况。`PROJECT_BOARD.md` 只是派生看板。

修改账号定位请编辑 `accounts/demo/config.md`；增加账号时复制示例结构，并同步 `studio-state.json` 的账号列表、当前账号和项目指针。稳定偏好按岗位记录到 `account-rules.md`，临时观察写 `learning-log.md`。不要将占位模板当成完成产物。

## 检查命令

在仓库根目录运行：

```bash
python3 .codex/skills/studio-manager/scripts/audit_skill_routing.py
python3 .codex/skills/studio-manager/scripts/generate_dashboard.py
python3 -m unittest discover -s .codex/skills/studio-manager/scripts -p 'test_*.py'
python3 -m unittest discover -s .codex/skills/media-pitcher/scripts -p 'test_*.py'
node --test .codex/skills/media-editor/assets/motion-kit/editorial-motion.test.mjs
```

项目创建后校验：

```bash
python3 .codex/skills/studio-manager/scripts/validate_workflow.py accounts/demo/videos/YYYY-MM-DD_短标题
```

生命周期字段只能通过 `set_project_state.py` 更新；运行其 `--help` 查看参数。自动化检查通过不代表实际剪辑服务、生成质量或发布效果已经验证。

## 隐私与许可

分享版从允许的文件清单重新导出，使用全新 Git 历史；不附带私人账号、视频项目、声音样本、安全区原截图、浏览器配置、会话记录或密钥。测试数据使用虚构示例。音效需自行取得授权；字体附原许可证。

`.gitignore` 默认忽略新账号与视频数据、环境变量、会话文件和输出目录。但**已经被 Git 跟踪的示例配置与 `studio-state.json`，修改后仍会进入差异**；你填写个人资料后，提交或公开前必须审阅差异。不要将凭据写入 Markdown、脚本或版本历史。

工作流与代码沿用 [MIT License](LICENSE)，保留原版权声明。附带字体遵守各字体目录中的 SIL OFL；外部工具、插件、GSAP 及其他第三方内容适用各自许可，不能因本仓库采用 MIT 就视为全部可再分发。方法引用与来源保留在对应文件中。
