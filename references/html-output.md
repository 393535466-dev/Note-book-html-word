# HTML 学习页

## 布局

使用 `assets/notes-template.html`：白色阅读区、浅灰背景、蓝色重点色、约 1000px 宽度、清楚的标题与表头。避免大封面、统计卡和装饰动效；首屏能看到重点。

至少一张语义正确的表格，带表头、caption。窄屏表格区域横向滚动，页面本身不溢出，长词可换行。问答和附录用原生 details 默认收起，打印时展开。影响理解的冲突和条件在主表可见，不能只藏附录。

输出 UTF-8 单文件，内嵌 CSS、系统字体，不依赖 CDN、网络字体、远程图片或脚本。外部核实来源可保留 HTTP(S) 链接，正文离线可读。输入文本须转义，不能直接执行原文中的 HTML/脚本。

## 渲染

内容 JSON 结构如下。默认按 [双格式交付](dual-output.md) 运行 `render_notes_pair.py` 同时生成 HTML 与 Word；用户明确只要 HTML 时，才单独运行 `python3 <skill目录>/scripts/render_notes.py <内容.json> <输出.html>`。默认拒绝覆盖；明确修改已有结果时用 `--overwrite`。

```json
{
  "title": "主题",
  "meta": "学习笔记 · 材料日期与覆盖范围",
  "summary": "一句话主旨",
  "highlights": ["核心结论"],
  "sections": [
    {"title": "核心知识", "intro": "主题连接句",
     "table": {"caption": "知识对照", "columns": ["知识点", "级别", "通俗解释", "例子或标准"],
       "rows": [["概念A", "重点", "解释", "标准 [S1]"]]}},
    {"title": "实际步骤", "steps": ["先做什么", "再做什么"]}
  ],
  "questions": [{"question": "为什么？", "answer": "答案与条件"}],
  "appendices": [{"title": "来源与纠错", "paragraphs": ["S1 · 文件名 · 实际时间戳或段落"]}],
  "sources": [{"label": "核实来源", "url": "https://example.com/document"}],
  "review": "可调整复习建议"
}
```

必需 `title`、`summary`、`sections`，至少一个主 section 包含非空表格。其他按需，不凑栏目。section/appendix 支持 `intro`、`paragraphs`、`bullets`、`steps`、`table`，appendix 默认折叠。所有字符串是纯文本，不解析 Markdown。table 为 `caption`、非空 `columns`、每行与列数匹配的 `rows`。sources 只接受 HTTP(S)。

图表或复杂公式需要时可在模板基础上添加自包含内联 SVG；简易 JSON 不是能力上限。脚本负责排版和转义，内容判断与事实核实仍由模型完成。

## 验证

检查摘要、主表、自测答案一致；保留来源与补充标记。实际打开 HTML，检查桌面及窄屏、长文本、表格、问答折叠与附录，打印时折叠内容可读。无浏览器时说明只做结构检查。

最后分别给 HTML 和 Word 文件链接及少量收获，不另贴一篇长 Markdown。默认本地交付，不自动托管，不把用户记录提交到技能仓库。
