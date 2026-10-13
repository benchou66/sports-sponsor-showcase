// Render a filled 上架 form (JSON) into a Word document, colour-coding AI-generated content.
// Usage: node make_filled_docx.js <filled.json> <out.docx>
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, BorderStyle, PageOrientation, LevelFormat, TableLayoutType,
} = require("docx");

const [SRC, OUT] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(SRC, "utf8"));
const FONT = "Microsoft JhengHei";
const GRAY = "F2F2F2", HEAD = "DCE6F1", MUTED = "595959";
const COLORS = { "官方": "000000", "AI生成": "C55A11", "AI推定": "C55A11", "網路搜尋": "2E75B6", "需另提供": "C00000" };
const TOTAL = 14000;

const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: o.size || 19, bold: o.bold, color: o.color, italics: o.italics });
const p = (children, o = {}) => new Paragraph({ children, spacing: { after: o.after ?? 100, before: o.before ?? 0 }, numbering: o.numbering });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(t, { size: 30, bold: true, color: "1F3864" })], spacing: { before: 340, after: 140 } });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(t, { size: 23, bold: true, color: "2E5496" })], spacing: { before: 220, after: 100 } });
const bullet = (t) => new Paragraph({ children: [run(t)], numbering: { reference: "bul", level: 0 }, spacing: { after: 60 } });
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };

function tagOf(source) {
  const s = source || "";
  if (s.includes("需另提供")) return "需另提供";
  if (s.includes("AI")) return s.includes("推定") && !s.includes("生成") ? "AI推定" : "AI生成";
  if (s.includes("網路搜尋")) return s.startsWith("官方") ? "官方" : "網路搜尋";
  return "官方";
}
function valueParas(text, source, size = 18) {
  const tag = tagOf(source); const color = COLORS[tag];
  const lines = String(text ?? "").split("\n");
  return lines.map((ln, i) => new Paragraph({ children: [
    ...(i === 0 && tag !== "官方" ? [run(`【${tag}】`, { size, bold: true, color })] : []),
    run(ln, { size, color: tag === "官方" ? undefined : color }),
  ], spacing: { after: ln === "" ? 60 : 30 } }));
}
function cell(children, w, o = {}) {
  return new TableCell({ children, width: { size: w, type: WidthType.DXA }, borders,
    shading: o.shade ? { type: ShadingType.CLEAR, color: o.shade, fill: o.shade } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 }, columnSpan: o.span });
}
const tcell = (t, w, o = {}) => cell([new Paragraph({ children: [run(t, { size: o.size || 18, bold: o.bold, color: o.color })], spacing: { after: 30 } })], w, o);

function kvTable(rows, title) {
  const W = [2600, 8400, 3000];
  const out = [];
  if (title) out.push(new TableRow({ children: [tcell(title, TOTAL, { bold: true, shade: GRAY, span: 3 })] }));
  out.push(new TableRow({ tableHeader: !title, children: ["欄位", "填寫內容", "來源／備註"].map((h, i) => tcell(h, W[i], { bold: true, shade: HEAD })) }));
  for (const r of rows) {
    const src = [new Paragraph({ children: [run(r.source || "", { size: 17, bold: true, color: COLORS[tagOf(r.source)] })], spacing: { after: 30 } })];
    if (r.remark) src.push(new Paragraph({ children: [run(r.remark, { size: 16, color: MUTED })], spacing: { after: 30 } }));
    out.push(new TableRow({ children: [tcell(r.field, W[0], { bold: true }), cell(valueParas(r.value, r.source), W[1]), cell(src, W[2])] }));
  }
  return new Table({ rows: out, width: { size: TOTAL, type: WidthType.DXA }, columnWidths: W, layout: TableLayoutType.FIXED });
}
function gridTable(block) {
  const cols = block.columns; const srcW = 2600;
  const base = Math.floor((TOTAL - srcW) / cols.length);
  const W = cols.map(() => base); W.push(TOTAL - base * cols.length);
  const out = [];
  if (block.title) out.push(new TableRow({ children: [tcell(block.title, TOTAL, { bold: true, shade: GRAY, span: W.length })] }));
  out.push(new TableRow({ children: [...cols, "來源／備註"].map((h, i) => tcell(h, W[i], { bold: true, shade: HEAD })) }));
  for (const r of block.rows) {
    const cells = r.cells.map((c, i) => cell(valueParas(c, i === 0 ? r.source : "官方", 17), W[i]));
    const src = [new Paragraph({ children: [run(r.source || "", { size: 16, bold: true, color: COLORS[tagOf(r.source)] })], spacing: { after: 30 } })];
    if (r.remark) src.push(new Paragraph({ children: [run(r.remark, { size: 15, color: MUTED })], spacing: { after: 30 } }));
    cells.push(cell(src, W[W.length - 1]));
    out.push(new TableRow({ children: cells }));
  }
  return new Table({ rows: out, width: { size: TOTAL, type: WidthType.DXA }, columnWidths: W, layout: TableLayoutType.FIXED });
}

// ---------- document ----------
const a = data.athlete;
const doc = [];
doc.push(new Paragraph({ children: [run(`運動員上架填寫範例：${a.name}（${a.sport}／${a.type}）`, { size: 38, bold: true, color: "1F3864" })], spacing: { after: 100 } }));
doc.push(p([run(`舊平台申請編號 ${a.id}｜官方資料擷取日 ${a.data_date}｜填寫日期 2026-10-13｜官方頁面：${a.source_url}`, { size: 17, color: MUTED })], { after: 200 }));

doc.push(h1("0. 標示說明"));
doc.push(p([run("每個欄位右側標示資料來源；填寫內容依來源著色：", { size: 19 })]));
doc.push(bullet("官方：直接取自 sponsor.sports.gov.tw 官方頁面（黑字）。"));
doc.push(p([run("【AI生成】", { bold: true, color: COLORS["AI生成"] }), run("：官方沒有的資料，由 AI 生成之佔位值或文案（橘字），上架前必須由本人或教練確認、修改。", { size: 19 })], { numbering: { reference: "bul", level: 0 }, after: 60 }));
doc.push(p([run("【AI推定】", { bold: true, color: COLORS["AI推定"] }), run("：AI 依官方既有資料推斷的選項或值（橘字），請確認。", { size: 19 })], { numbering: { reference: "bul", level: 0 }, after: 60 }));
doc.push(p([run("【網路搜尋】", { bold: true, color: COLORS["網路搜尋"] }), run("：來自網路公開來源，備註欄附出處（藍字）。", { size: 19 })], { numbering: { reference: "bul", level: 0 }, after: 60 }));
doc.push(p([run("【需另提供】", { bold: true, color: COLORS["需另提供"] }), run("：證件、金融帳戶等必須由運動員本人提供的資料，本文件只放佔位（紅字）。", { size: 19 })], { numbering: { reference: "bul", level: 0 }, after: 60 }));
doc.push(p([run("同一份內容的機器可讀版本：填寫範例_姚宥米_3433.json（每個欄位含 source 標記，可直接供自動上架程式使用）。", { size: 18, color: MUTED })], { before: 80 }));

const todo = [];
for (const s of data.steps) {
  doc.push(h1(`${s.no}. ${s.title}`));
  if (s.note) doc.push(p([run(s.note, { size: 18, color: MUTED })]));
  for (const b of s.blocks) {
    if (b.type === "kv") {
      doc.push(kvTable(b.rows, b.title));
      for (const r of b.rows) { const t = tagOf(r.source); if (t !== "官方" && t !== "網路搜尋") todo.push([`${s.no}. ${s.title}`, (b.title ? b.title + " › " : "") + r.field, t]); }
    } else {
      doc.push(gridTable(b));
      for (const r of b.rows) { const t = tagOf(r.source); if (t !== "官方" && t !== "網路搜尋") todo.push([`${s.no}. ${s.title}`, (b.title || "") + " › " + String(r.cells[0]).slice(0, 30), t]); }
    }
    doc.push(p([run("", { size: 8 })], { after: 60 }));
  }
}

doc.push(h1("附錄：上架前需確認／補齊清單（自動彙整）"));
const W = [2600, 8800, 2600];
const rows = [new TableRow({ tableHeader: true, children: ["步驟", "欄位／項目", "狀態"].map((h, i) => tcell(h, W[i], { bold: true, shade: HEAD })) })];
for (const [st, f, t] of todo) rows.push(new TableRow({ children: [tcell(st, W[0]), tcell(f, W[1]), tcell(`【${t}】`, W[2], { bold: true, color: COLORS[t] })] }));
doc.push(new Table({ rows, width: { size: TOTAL, type: WidthType.DXA }, columnWidths: W, layout: TableLayoutType.FIXED }));

const document = new Document({
  creator: "Ben Chou", title: `運動員上架填寫範例 ${a.name}`,
  styles: { default: { document: { run: { font: FONT, size: 19 } } } },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 260 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE }, margin: { top: 850, bottom: 850, left: 850, right: 850 } } }, children: doc }],
});
Packer.toBuffer(document).then((buf) => { fs.writeFileSync(OUT, buf); console.log("written", OUT, buf.length, "bytes;", todo.length, "items to confirm"); });
