# ShotCraft 镜头卡 → HyperFrames 适配索引

用途：当分镜需要产品级 UI / 数据 / 标题 / 运镜动效，而现有 `assets/motion-kit/` 没有合适组件时，借鉴
`video-shotcraft` 的镜头语法与调校参数，再用 HyperFrames + paused GSAP 重做。该文件是选镜索引，不复制
ShotCraft 的 Remotion 工程、第二套状态机或音频素材。

152 张卡的全量分流见 [`shotcraft-catalog.md`](shotcraft-catalog.md)；本文件保留选择、转译和验收规则。

## 来源与边界

- 来源仓库：[Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft)
- 固定审计版本：`0d6f0b57f0d4d6700761644c07f7ef03c3e50234`（2026-08-14）
- 上游许可：仓库 Apache-2.0；若直接复制代码，保留许可与来源记录。默认只转译可观察的运动语法，不复制
  Logo、品牌资产、原文案、具体构图、原音乐或原音效。
- 主时间线仍归 ChatCut；HyperFrames 只产确定性动效、信息卡、界面演示或透明叠加。Remotion 不是默认后端。

## 何时查卡

满足任一条件时读取本索引，再按卡名读取上游卡片与对应 demo：

1. 分镜明确标注“重点 / 产品级动效”；
2. 现有 motion-kit 缺少表达该观看任务的组件；
3. 参考片拆解需要更精确的错峰、缓动、落稳、2.5D 页面空间或节拍设计。

普通标题、逐句字幕、真人主剪辑不查卡：账号标题默认硬切，ChatCut 负责真人和时间线。

## 选卡顺序

先写观看任务，再选运动，不按“看起来酷”选卡：

1. **真实操作 / 屏幕证据**：`cursor-flyover`、`type-and-filter`、`command-palette-summon`、
   `ai-stream-response`。
2. **结果对比 / 数据解释**：`before-after-slider-scrub`、`chart-live-moves`、`timeline-travel`、
   `odometer-digit-roll`。
3. **界面组装 / 内容进入槽位**：`row-embed`、`list-reveal`、`product-card-progressive-assemble`、
   `skeleton-reveal`、`deck-deal-flyin`。
4. **重点标题 / 章节字卡**：`type-assembly-moves`、`marker-underline-title`、`title-demote-to-label`。
   只用于分镜明确的重点镜头，不覆盖账号普通标题的硬切规则。
5. **节奏 / 转场**：`montage-rhythm-moves`、`line-carry-transition`、`transition-hidden-cut`、
   `speed-ramp-freeze`。优先硬切与运动匹配；禁止逐切堆装饰性转场。

同一条片最多让两种高注意力动效当主角；同一功能只选一个主运动。信息密集段优先可读性，不因卡片样式
牺牲真实截图、结果证据或字幕安全区。

## 转译协议

读取卡片全文和准确 demo 后，先把实现还原成这八项，不直接复制 TSX：

`观看任务 | 起始状态 | 主状态变化 | 持续帧数 | easing/错峰 | 落稳与 hold | 声音峰值 | 已知坑`

然后按以下顺序重做：

1. 把 1920×1080 的示例改成项目实际画布；9:16 先留中央主舞台和字幕带，不能机械裁切。
2. 真实网页/录屏使用截图与 layout 坐标；需要页面空间运动时，让 overlay 与同一 HyperFrames 相机坐标系绑定。
3. 只使用一条 paused GSAP master timeline；禁止计时器、随机数、第二动画运行时。
4. 动效接入 ChatCut 前运行 `hyperframes keyframes`、聚焦 shot 和关键帧检查；检查首帧、8–12 帧、落稳帧、
   中段、结束前帧及前后边界。
5. 先做一张关键帧和 10 秒无精修样片。只有输入、执行、结果 / 验证更清楚且主文字可读，才扩展到全片。
6. 声音遵守账号声音系统：一个动作最多一个主音效，峰值对准接触、锁定、完成或验证帧；不复制 ShotCraft
   音频包。外部音效必须逐项有许可证与来源证据。

## 适配记录模板

```text
ShotCraft card: <name> / <style-key>
Source commit: 0d6f0b57f0d4d6700761644c07f7ef03c3e50234
观看任务: <观众此刻要理解什么>
采用语法: <状态变化 + 时长 + easing + 锚点>
HyperFrames 实现: <composition / component / output>
账号适配: <画布、安全区、字幕、素材限制>
弃用项: <为何不复制原卡的某部分>
验收帧: <frame list>
声音: <动作 / 音源 / 峰值帧 / 许可证证据>
```

## 失败与回退

- 卡片依赖 Remotion 特有组件：只提取运动参数，改用现有 HyperFrames 组件；无法等价表达时记录缺口。
- 卡片需要复杂 3D、粒子或高成本资产：先做最低成本单镜头试验，不把整片切到 Remotion。
- 动效遮挡真人、录屏、字幕或结果证据：删减层级、减速并增加 hold；可读性失败即回退到硬切 / 简单信息卡。
- 上游卡片、demo 或音频许可证无法核验：保留为参考，不声称已复刻或可商用。
