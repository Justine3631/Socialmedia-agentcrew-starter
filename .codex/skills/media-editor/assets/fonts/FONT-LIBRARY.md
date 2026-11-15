# 剪辑字体库

这是剪辑师唯一的免费商用字体库。只收录许可证可核验、允许商业使用和嵌入成片的字体；不收录付费字体、来源不明字体或 macOS 专有字体文件。

## 已收录

| 字体 | 用途 | 字重建议 | 文件 | 许可证 |
|---|---|---|---|---|
| Inter | 英文、数字、UI、状态标签 | 正文 400；UI 500；标题 600 | `Inter/Inter-Variable.ttf` | SIL OFL 1.1，见 `Inter/OFL.txt` |
| Noto Sans SC | 中文界面、字幕、信息卡、现代标题 | 正文 400；UI 500；标题 600 | `NotoSansSC/index.css` + `NotoSansSC/files/` | SIL OFL 1.1，见 `NotoSansSC/LICENSE` |
| Noto Serif SC | Editorial 标题、章节页、片尾完成句 | 正文 400；标题 500–600 | `NotoSerifSC/index.css` + `NotoSerifSC/files/` | SIL OFL 1.1，见 `NotoSerifSC/LICENSE` |

Noto Sans SC / Noto Serif SC 是思源黑体 / 思源宋体的 Google 对应字族，适合作为免费商用、可随项目携带的中文版替代。

## 当前推荐组合

```text
英文和数字：Inter
中文界面和字幕：Noto Sans SC
Editorial 标题和片尾：Noto Serif SC
```

Kimi 风格参考的起始配置：

```text
UI 英文：Inter 400–500
中文正文：Noto Sans SC 400
中文重点：Noto Sans SC 500–600
片尾衬线：Noto Serif SC 500
英文大写标签：Inter 500，letter-spacing: 0.08em–0.14em
```

## 使用

HyperFrames / Web 动效：

1. 把所需字体目录复制到当前项目的 `assets/fonts/`。
2. Noto 字体加载目录内的 `index.css`；该 CSS 已按 Unicode 范围引用 `files/` 中的 WOFF2。
3. Inter 用本地 `@font-face` 引用 `Inter-Variable.ttf`。
4. 项目交付时保留相应许可证文件。

示例：

```css
@import url("./assets/fonts/NotoSansSC/index.css");
@import url("./assets/fonts/NotoSerifSC/index.css");

@font-face {
  font-family: "Inter";
  src: url("./assets/fonts/Inter/Inter-Variable.ttf") format("truetype");
  font-style: normal;
  font-weight: 100 900;
}
```

## 收录规则

- 必须能从字体作者、官方仓库或可信发行渠道核验许可证。
- 默认只接收 SIL OFL、Apache 2.0 等明确允许商业使用和嵌入的许可证。
- 许可证必须和字体文件一起保存。
- 付费字体即使本机已安装，也不得复制到此库。
- macOS 自带的苹方、宋体、Helvetica Neue、Times 只可按系统许可在本机调用，不进入共享库。
- 不单独出售字体文件；修改 OFL 字体时遵守保留字体名称等条款。

## 来源与版本

- Inter：Google Fonts 官方仓库当前发行文件；SIL OFL 1.1。
- Noto Sans SC：Fontsource `@fontsource-variable/noto-sans-sc@5.3.0`，上游 Google Noto CJK；SIL OFL 1.1。
- Noto Serif SC：Fontsource `@fontsource-variable/noto-serif-sc@5.3.0`，上游 Google Noto CJK；SIL OFL 1.1。

