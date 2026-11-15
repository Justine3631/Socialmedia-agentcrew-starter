# Anime.js 参考源

- 来源：https://animejs.com/
- 官方仓库：https://github.com/juliangarnier/anime
- 核心仓库许可证：MIT；官网示例、CodePen 示例和外部素材另行核验，不默认视为可直接商用。
- 学习用途：提取运动语法，不直接复制品牌、文案、构图或素材。

## 已确认能力

- `stagger`：时间、数值和时间轴位置交错，适合四行卡、任务卡和节点错峰。
- `timeline`：标签、绝对时间、相对时间和同步，适合把主动作、次级动作和结果保持编排在一起。
- `easing`：内置缓动与弹簧，按材质选择，不把同一曲线批量套给 UI、纸张和字幕。
- `SVG`：形状变形、路径运动和描边绘制，适合流程路径、关系线和关键词标记。
- 模块化导入：可按功能拆分；是否引入运行时仍由视频渲染链决定。

## 本工作台用法

1. 当前视频需要某种动作时，先从现有 `editorial-motion.js` 组件中选择。
2. 缺少组件时，参考 Anime.js 的语法拆解，写成 paused GSAP timeline helper。
3. 通过 HyperFrames 关键帧、聚焦 shot、snapshot 和 `check` 验证后，才进入制作预览。
4. 外部可下载资源必须先保留来源、许可证和文件校验信息。

## 不直接采用

- Scroll Observer、Draggable 等依赖浏览器交互时钟的能力，不直接放入逐帧视频导出。
- 不把 Anime.js 时间轴和 GSAP/HyperFrames 双重驱动叠在同一镜头。
- 不因官网有示例就自动引入依赖；只有真实镜头需要且现有组件无法满足时才评估。
