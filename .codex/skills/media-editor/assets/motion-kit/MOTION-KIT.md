# Editorial Motion Kit

可复用的二十八个原创动效语法与配置工具：

- `addThreeStageFrame`：Detect、Frame、Lock 三段式装框。
- `addDelayedLabel`：主体先行，标签按帧延迟。
- `addMatchCut`：保持位置、尺度、旋转和速度的材质硬切。
- `addSemanticCollapse`：语义内容逐级减为符号。
- `addKeywordEmphasis`：关键词先变色，手绘线再展开。
- `addCountUp`：数值按 paused timeline 进度可重现地增长。
- `addFlowPath`：SVG 路径先绘制，节点再错峰落位。
- `addMaskedTextCascade`：对调用方已拆好的字/词做遮罩级联；显式起止态，禁止随机 stagger。
- `addSelectionRail`：游戏化选项栏切换；旧项降级、新项高亮、详情面板同步交接。
- `addExplicitStateTransition`：吸收 FLIP 思维，但由调用方预先提供几何状态，不在渲染时测量布局。
- `addMotionPathFollower`：从显式路径起点沿 SVG 路径运动；起跑前姿态也固定，插件由项目加载和注册。
- `createCustomEaseProfile`：保存命名 CustomEase 曲线；由具体工程注册一次，再把名称用于 timeline。
- `addDrawSvgTransition`：用 DrawSVG 的显式起止区间做路径中心向外、局部线段或整线绘制。
- `addMorphSvgTransition`：用 MorphSVG 在两个明确 SVG 形状或 path data 之间变形。
- `createTextPluginConfig` / `addTextReplacementTransition`：用 TextPlugin 做可读的文字替换、打字机或逐词替换；插件由工程注册。
- `addMapPanAndPin`：地图背景连续平移/缩放，按“图钉 → 标签 → 说明 → 高亮”错峰定位。
- `addModelCompareCard`：组合选项栏切换与模型名称替换；特征行和文案由调用方提供。
- `addEvidenceHold`：证据卡进入后保留明确阅读停顿，再按需退出；停顿是真实时间轴空档。
- `createCustomBounceProfile` / `createCustomWiggleProfile`：保存固定参数的触感缓动；由工程注册一次。
- `mapRange` / `normalizeRange` / `snapValue` / `precomputeDistributedValues`：在建轴前预计算数值、分布和吸附，不在逐帧读取布局。
- `addPhysics2DTransition`：固定速度、角度、重力的二维运动。
- `addPhysicsPropsTransition`：固定速度、加速度、摩擦的数值属性运动。
- `addTactileLanding`：位置 bounce 与可选 squash 同步落地。

使用方式：

```js
import {
  addThreeStageFrame,
  addDelayedLabel,
  addMatchCut,
  addSemanticCollapse,
  addKeywordEmphasis,
  addCountUp,
  addFlowPath,
  addMaskedTextCascade,
  addSelectionRail,
  addExplicitStateTransition,
  addMotionPathFollower,
  createCustomEaseProfile,
  addDrawSvgTransition,
  addMorphSvgTransition,
  createTextPluginConfig,
  addTextReplacementTransition,
  addMapPanAndPin,
  addModelCompareCard,
  addEvidenceHold,
  createCustomBounceProfile,
  createCustomWiggleProfile,
  mapRange,
  normalizeRange,
  snapValue,
  precomputeDistributedValues,
  addPhysics2DTransition,
  addPhysicsPropsTransition,
  addTactileLanding
} from "./editorial-motion.js";
```

插件配置示意：

```js
const easeProfile = createCustomEaseProfile({
  name: "editorial-soft-out",
  path: "M0,0 C0.14,0.72 0.24,1 1,1"
});
CustomEase.create(easeProfile.name, easeProfile.path);

addDrawSvgTransition(timeline, {
  target: route,
  from: "50% 50%",
  to: "0% 100%",
  ease: easeProfile.name
});
```

约束：

- 调用方提供唯一的 paused GSAP timeline。
- 组件不创建 timeline、不调用 `play()`、不使用计时器或随机数。
- 参数是起始范围，不是每条视频都必须相同；根据画面几何和语义调整。
- `addDelayedLabel` 使用 `delayFrames / fps`，不得手写近似秒数。
- `addCountUp` 的 `target` 必须是 DOM 元素，不接受选择器字符串。
- `addFlowPath` 的 `path` 默认通过 `getTotalLength()` 取长度；非 SVG path 必须显式传 `length`。
- `addMaskedTextCascade` 不拆字、不改 DOM；中文按字、英文按词的节点由调用方在时间轴建立前准备。
- `addSelectionRail` 可用 `itemOffset` 把选项升降与新面板入场对齐，并用 `panelExitDuration` 独立控制旧面板退出；默认值保持原有交接节奏。
- stagger 只能使用固定数字或 `start / end / center / edges / 索引`，禁止 `random`。
- `addExplicitStateTransition` 只接受预计算的变换/视觉状态；拒绝 `width / height / top / left / margin / padding / display / visibility`。
- `addMotionPathFollower` 需要项目先加载并注册 `MotionPathPlugin`；helper 用显式 `fromTo` 固定路径起点，但不 import、不注册、不异步加载。
- `createCustomEaseProfile` 只返回 `{ name, path }`；`CustomEase.create()` 由具体工程在同步建轴前调用一次，名称不得覆盖 GSAP 标准 ease。
- `addDrawSvgTransition` 需要项目先加载并注册 `DrawSVGPlugin`；`from / to` 必须显式，禁止 `live` 动态重算。
- `addMorphSvgTransition` 需要项目先加载并注册 `MorphSVGPlugin`；`fromShape / toShape` 必须显式，复杂形状先用 `morphOptions` 固定映射、精度并逐帧检查。
- `createTextPluginConfig` / `addTextReplacementTransition` 需要项目先加载并注册 `TextPlugin`；文字起止值、delimiter、方向和速度必须显式，`TextPlugin` 只改变文字内容，不替代字幕排版。
- `SplitText` 只作为建轴前的拆分思路：中文优先调用方预先准备字/词节点，再交给 `addMaskedTextCascade`；不在 timeline 播放中重拆 DOM，也不依赖字体加载后的实时重排。
- `addMapPanAndPin` 要求 `mapFrom / mapTo` 显式提供相机状态；图钉、标签、说明和高亮只是错峰辅助层，不得替代真实画面证据。
- `addModelCompareCard` 复用 `addSelectionRail` 的状态切换；模型名称如需变化必须注册 `TextPlugin`，特征文案不得在 helper 内硬编码。
- `addEvidenceHold` 必须显式提供 `holdDuration`；停留长度按信息密度和口播节奏设置，不用 timer 或 callback 维持画面。
- `createCustomBounceProfile` / `createCustomWiggleProfile` 只返回注册定义；禁止 CustomWiggle 的 `random` 类型。
- 数值工具只在建轴前运行；正式 timeline 不使用 GSAP `random()`、`shuffle()` 或函数型随机值。
- `addPhysics2DTransition` 需要项目先注册 `Physics2DPlugin`，并显式提供 `velocity / angle`；插件忽略 ease，所以 helper 固定写 `none`。
- `addPhysicsPropsTransition` 需要项目先注册 `PhysicsPropsPlugin`；只接受确定性数字配置，拒绝布局属性。
- `addTactileLanding` 需要已注册的 bounce/squash ease；bounce 只用于有触感语义的卡片、印章或按钮，不作为全片默认。
- Match Cut 前后必须使用同一主体几何状态；只靠同时隐藏/显示不算运动匹配。
- 制作后必须执行 `hyperframes keyframes`、聚焦 shot、关键时刻 snapshots 和最终 `check`。

## 选择顺序

1. 先用现有 helper 或 HyperFrames atomic rule。
2. 只有真实镜头缺能力时，查看 `gsap-skills-reference.md` 与 `animejs-reference.md`。
3. 把外部语法翻译到唯一 paused timeline；不并行引入另一条播放时钟。
4. 先做单镜头样片，通过逐帧验证后才扩散到整片。

## Anime.js 参考边界

- 只借鉴 stagger、timeline、SVG path 和 easing 语法；正式工程不引入 Anime.js 运行时。
- 不复制官网示例的品牌、文案、构图或素材；组件按本账号视觉规则重新设计。
- 视频渲染仍由 HyperFrames 逐帧 seek paused GSAP timeline，避免独立时钟导致预览与导出不一致。
