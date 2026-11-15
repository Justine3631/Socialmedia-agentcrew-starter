# GSAP Skills 参考源

- 来源：https://github.com/greensock/gsap-skills
- 官方参数参考：
  - https://gsap.com/docs/v3/Eases/CustomEase/
  - https://gsap.com/docs/v3/Plugins/DrawSVGPlugin/
  - https://gsap.com/docs/v3/Plugins/MorphSVGPlugin/
  - https://gsap.com/docs/v3/Plugins/Physics2DPlugin
  - https://gsap.com/docs/v3/Plugins/PhysicsPropsPlugin/
  - https://gsap.com/docs/v3/Eases/CustomBounce/
  - https://gsap.com/docs/v3/Eases/CustomWiggle/
  - https://gsap.com/docs/v3/Plugins/MotionPathPlugin/
  - https://gsap.com/docs/v3/Plugins/TextPlugin/
  - https://gsap.com/docs/v3/Plugins/SplitText/
  - https://gsap.com/docs/v3/Plugins/ScrambleTextPlugin/
  - https://gsap.com/docs/v3/GSAP/UtilityMethods/
- 审阅固定提交：`aed9cfd3277740755f6bfc1155c7aa645403b760`
- `gsap-skills` 仓库许可证：MIT。
- GSAP 运行库及插件：按 GSAP Standard License 免费使用，含商业项目；不要误写成 MIT。
- 学习用途：吸收官方 API 纪律和编排方法，不把上游 Skills 安装成第二套项目动效系统。

## 八个官方 Skill 的完整审阅结论

| 官方方向 | 今日结论 | 对 HyperFrames 的处理 |
|---|---|---|
| `gsap-core` | 显式 `fromTo`、transform aliases、`autoAlpha`、directional rotation、CustomEase、`immediateRender` 有直接价值 | 已吸收；固定视频不采用 `matchMedia` 作为输出分支 |
| `gsap-timeline` | position parameter、labels、defaults、嵌套时间轴是编排基础 | 已吸收；仍由组合提供唯一 paused timeline |
| `gsap-plugins` | SVG、Physics、CustomBounce/Wiggle、SplitText、Flip、交互插件覆盖面完整 | SVG 与固定参数 Physics 已做 helper；SplitText/Flip 逐镜验证；交互插件排除 |
| `gsap-utils` | mapRange、normalize、snap、distribute、interpolate 可把布局和数值提前固化 | 已吸收为 setup-time 纯函数；random/shuffle 排除 |
| `gsap-performance` | transform/opacity、批量 stagger、will-change、减少布局读写有直接价值 | 已吸收为 motion-kit 约束；`quickTo` 只适合实时输入，不接入视频 |
| `gsap-scrolltrigger` | scrub、pin、snap、containerAnimation 依赖滚动位置 | 已完整审阅，但固定视频路线排除 |
| `gsap-react` | `useGSAP`、scope、contextSafe、cleanup、SSR 边界适合 React 应用 | 已学习为架构知识；当前 HTML HyperFrames 不引入 React 生命周期 |
| `gsap-frameworks` | Vue/Svelte 的 mounted、scoped context、unmount cleanup 与 React 同类 | 已学习为架构知识；当前渲染链不复制框架适配层 |

## 这一轮新增审阅：文字与函数型修饰器

| 能力 | 事实 | HyperFrames 处理 |
|---|---|---|
| `TextPlugin` | 按字符或 delimiter 逐步替换文字；支持 `rtl`、`speed`、`type: "diff"` 等显式配置 | 已吸收为 `createTextPluginConfig` / `addTextReplacementTransition`；由具体工程注册插件 |
| `SplitText` | 可拆 chars/words/lines，支持 mask、中文自定义 `wordDelimiter`、ARIA 和字体/宽度变化后的 `autoSplit` | 已吸收为建轴前的预处理原则；当前不在时间轴播放时重拆 DOM，中文优先手工准备节点 |
| `ScrambleText` | 默认以随机字符刷新乱码区域，再逐步揭示目标文字 | 不直接吸收；随机刷新会让视频逐帧复现和审片证据变差。若真需要，先在建轴前固化字符帧 |
| `Modifiers` | 通过函数在渲染过程中修正属性值，适合 wrap、边界和循环值 | 不进入核心 helper；可用 `mapRange / snapValue / precomputeDistributedValues` 预计算同类结果，减少隐式逐帧函数 |
| Utils 其余方法 | `clamp`、`interpolate`、`wrap`、`unitize`、`pipe` 等可组合数值处理 | 只吸收对画面有明确收益且可在建轴前执行的部分；`random / shuffle` 继续排除 |

## 已吸收

- Core：显式 `fromTo`、transform aliases、`autoAlpha`、同属性多段动画的 `immediateRender` 边界。
- Timeline：标签、position parameter、统一 defaults；不用一串 `delay` 拼接动作。
- Stagger / Utils：固定顺序、中心/边缘扩散、数值映射和 snap 思维；视频正式渲染禁止 random/shuffle。
- Plugins：MotionPath 的显式路径配置；SplitText 的“先拆分再按字/词动画”；FLIP 的“同一主体跨状态连续运动”。
- SVG / Ease：CustomEase 先命名并注册一次；DrawSVG 用显式区间控制整线、局部线段和中心向外；MorphSVG 固定起止形状并按需要设置映射、精度。
- Performance：优先 transform/opacity，批量 stagger，避免布局属性和读写交错。
- Utils：把 `mapRange / normalize / snap / distribute` 变成建轴前的显式数值，减少运行时布局读取。
- Physics / EasePack：固定参数的 Physics2D、PhysicsProps、CustomBounce、CustomWiggle 可用于少量触感镜头；物理插件忽略普通 ease，必须单独检查终态。
- Text：`TextPlugin` 用于可读的文字替换、打字机和逐词变化；`SplitText` 只负责建轴前拆分，中文断词由调用方明确控制。
- MotionPath：`path / align / alignOrigin / autoRotate / start / end` 都应显式给出；适合让图标、箭头或点位沿路线移动，但不等于真实地图镜头。
- Accessibility：文字拆分时保留可读语义；正式视频仍以静态排版和最终像素检查为准。

## HyperFrames 翻译规则

- 所有正式动作进入调用方提供的唯一 paused GSAP timeline，并由 HyperFrames seek。
- FLIP 不在渲染时调用 `getState()` 或改变布局；预先计算 `x / y / scale / rotation`，再用 `addExplicitStateTransition`。
- SplitText 只作为预处理思路；时间轴同步建立前完成拆分，helper 不在播放中改 DOM。
- MotionPathPlugin 由具体 HyperFrames 工程按需加载、注册和锁版本；helper 用显式路径起止进度稳定首帧，motion-kit 不暗装依赖。
- CustomEase 由具体 HyperFrames 工程同步注册一次，motion-kit 只保存命名曲线定义，不在 timeline 中创建插件实例。
- DrawSVGPlugin 的 `from / to` 使用固定区间；不使用 `live`，避免逐帧重算响应式路径长度。
- MorphSVGPlugin 的 `fromShape / toShape` 和映射选项显式传入；先从简单图标状态做样片，复杂形状必要时预编译。
- MotionPathPlugin 的路径和对齐配置由具体工程注册；`autoRotate` 只在方向本身有语义时使用，地图背景仍用显式 `x / y / scale` 相机状态。
- Physics2D / PhysicsProps 的速度、角度、重力、加速度、摩擦都在建轴前固定；不使用交互输入、实时速度或碰撞模拟。
- CustomBounce 的位置 ease 与 squash ease 可并行写入同一时间段；CustomWiggle 只允许固定的 `easeOut / easeInOut / anticipate / uniform` 预设。
- 路径、字词、选项状态与时间全部显式，确保相同时间得到相同像素。

## 明确排除

- `ScrollTrigger`、`ScrollSmoother`：依赖滚动位置，不属于固定视频时间轴。
- `Draggable`、`Observer`、`Inertia`、`quickTo`：依赖输入事件或持续更新。
- `matchMedia`：仅可用于浏览器预览辅助，不能替代固定输出尺寸。
- React/Vue/Svelte 生命周期写法：与当前 HTML HyperFrames 渲染链无关。
- `random()`、`shuffle()`、`from: "random"`：正式渲染禁用；若需随机感，预先生成并固化数值。
- GSDevTools：只用于开发，不进入交付工程。
- Physics2D、PhysicsProps：不是完整物理引擎；不做碰撞、实时速度或互动拖拽，只保留固定参数的装饰性落点。

## 单镜头验证后才能采用

- `SplitText`：中文断词、字体加载和 DOM 包装必须先验证；常规项目优先手工字/词节点。
- `MorphSVG`：先统一 path 身份并检查中间形态，复杂图形必要时预编译。
- `TextPlugin`：只处理文字内容的显式变化，不负责字幕布局、换行和屏幕安全区。
- `Flip`：官方能力会读取状态并可能写入 width/height；当前视频 helper 继续使用预计算状态，不在逐帧渲染时调用 `getState()`。
- `ScrambleText`：只用于短暂状态词，不能破坏需要阅读和核验的正文。
- Physics、CustomWiggle、CustomBounce：必须证明 seek 后状态一致，且视觉语气确实需要；通过后才可复用。
- Flip 插件：只有静态预计算替代方案无法表达时才评估；不能在逐帧渲染中依赖实时布局变化。

## 许可证边界

官方 Skill 文档可按 MIT 吸收和改写；GSAP 本体与插件遵守其 Standard License。外部 CodePen、图片、字体、品牌和演示素材不因出现在官方文档中自动获得复用许可。
