// Build 「運動員上架需填資料欄位總表」 .docx from the 20 system screenshots.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, BorderStyle, PageOrientation, LevelFormat, TableLayoutType, PageBreak,
} = require("docx");

const OUT = process.argv[2];
const FONT = "Microsoft JhengHei";
const GRAY = "F2F2F2", HEAD = "DCE6F1", REQ = "C00000", MUTED = "595959";

// ---------- helpers ----------
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: o.size || 20, bold: o.bold, color: o.color, italics: o.italics });
const p = (t, o = {}) => new Paragraph({ children: Array.isArray(t) ? t : [run(t, o)], spacing: { after: o.after ?? 100, before: o.before ?? 0 }, alignment: o.align, numbering: o.numbering });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(t, { size: 32, bold: true, color: "1F3864" })], spacing: { before: 360, after: 160 } });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(t, { size: 26, bold: true, color: "2E5496" })], spacing: { before: 280, after: 120 } });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [run(t, { size: 22, bold: true })], spacing: { before: 200, after: 80 } });
const note = (t) => p([run(t, { size: 18, color: MUTED })], { after: 80 });
const bullet = (t) => new Paragraph({ children: [run(t)], numbering: { reference: "bul", level: 0 }, spacing: { after: 60 } });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(text, w, o = {}) {
  const lines = String(text ?? "").split("\n");
  const paras = lines.map((ln) => {
    const children = [];
    // mark "*" required with red
    if (o.req && ln === "必填") children.push(run("必填", { size: 18, bold: true, color: REQ }));
    else children.push(run(ln, { size: o.size || 18, bold: o.bold, color: o.color }));
    return new Paragraph({ children, spacing: { after: 40 } });
  });
  return new TableCell({ children: paras, width: { size: w, type: WidthType.DXA }, borders,
    shading: o.shade ? { type: ShadingType.CLEAR, color: o.shade, fill: o.shade } : undefined,
    margins: { top: 60, bottom: 60, left: 90, right: 90 } });
}

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const hr = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { bold: true, shade: HEAD })) });
  const body = rows.map((r) => {
    if (r.length && r[0] && typeof r[0] === "object" && r[0].span) {
      // one merged sub-heading cell across all columns
      const c = new TableCell({ children: [new Paragraph({ children: [run(r[0].text, { size: 18, bold: true })], spacing: { after: 40 } })],
        columnSpan: widths.length, width: { size: total, type: WidthType.DXA }, borders,
        shading: { type: ShadingType.CLEAR, color: GRAY, fill: GRAY }, margins: { top: 60, bottom: 60, left: 90, right: 90 } });
      return new TableRow({ children: [c] });
    }
    return new TableRow({ children: r.map((c, i) => {
    const o = {};
    if (i === 2 && (c === "必填" || c === "選填")) { o.req = c === "必填"; if (!o.req) o.color = MUTED; }
    if (typeof c === "object" && c !== null) return cell(c.text, widths[i], { ...o, shade: c.shade, bold: c.bold });
    return cell(c, widths[i], o);
  }) });
  });
  return new Table({ rows: [hr, ...body], width: { size: total, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED });
}

// standard field table: 欄位 | 型態 | 必填 | 格式／選項／限制 | 填寫說明 | 舊平台對應來源
const FW = [2000, 1300, 800, 3400, 3700, 2800]; // sum 14000 (landscape A4 usable ≈ 14,170 with 1.5cm margins)
const FH = ["欄位", "型態", "必填", "格式／選項／限制", "填寫說明（依系統畫面）", "舊平台資料對應（sponsor_data.json）"];
const ftable = (rows) => table(FH, rows, FW);
const sub = (t) => ({ text: t, shade: GRAY, bold: true, span: true });

// ---------- content ----------
const doc = [];

doc.push(new Paragraph({ children: [run("運動員上架（歷史資料匯入）需填資料欄位總表", { size: 40, bold: true, color: "1F3864" })], spacing: { after: 120 } }));
doc.push(p([run("體育運動捐贈媒合平臺 新系統「匯入步驟」全 9 步欄位整理｜整理日期 2026-10-13｜來源：需填資料資料夾 20 張系統截圖（P1～P911-1）", { size: 18, color: MUTED })], { after: 240 }));

doc.push(h1("0. 文件用途與使用方式"));
doc.push(bullet("目的：把運動員（個人）上架時系統要求的每一個欄位、型態、是否必填、格式限制與填寫說明一次列清，供人工填寫前備料，以及日後程式自動上架（匯入）時作為欄位規格。"));
doc.push(bullet("每個欄位最右欄標示「舊平台資料對應」：舊平台（sponsor.sports.gov.tw）已抓下的 103 筆資料（data/sponsor_data.json）可直接帶入的欄位名稱；標示「無來源」者必須另向運動員蒐集。"));
doc.push(bullet("系統畫面上以紅色星號標示的欄位，本表記為「必填」；未標星號者記為「選填」。表格／清單型欄位（可「＋新增」多筆）記為「表格（多筆）」。"));
doc.push(bullet("系統每三分鐘自動儲存至裝置，亦可手動「儲存至此裝置」；各步驟可「上一步／下一步」，最後一步為「確認匯入內容」。"));

doc.push(h2("匯入流程總覽（共 9 步）"));
doc.push(table(["步驟", "名稱", "主要內容", "必填欄位數（截圖可見）", "備註"], [
  ["1", "受贈帳號", "建立新受贈帳號（運動員）", "2", "登入帳號、帳號電子郵件"],
  ["2", "個人資料", "受贈者基本身分、戶籍／通訊地址、聯絡資料", "12+", "截圖於「聯絡電話（手機）」處截斷，下方可能尚有欄位"],
  ["3", "基本資料", "代表縣市、運動類型與賽事、銀行帳戶、計畫期間、原申請紀錄", "10+", "截圖於「原核准日期」處截斷"],
  ["4", "運動員資格", "資格類別（6 類勾選）、特殊身分（可複選＋證明上傳）、未指定捐贈款分配", "0（勾選題）", "歷史匯入不重新評估資格"],
  ["5", "訓練背景", "個人簡介、過去兩年參賽成績、指導教練、訓練期程", "0（皆未標星號）", "四個子區塊，多為表格"],
  ["6", "計畫與資源", "參賽規劃、預期效益、經費需求（10 科目）、聯絡人", "0（皆未標星號）", "經費表可匯出／匯入 Excel"],
  ["7", "附件", "身分證正反面、存摺封面", "3", "PDF／JPG／PNG，單檔 ≤ 20 MB"],
  ["8", "文宣", "個人頁面／捐贈項目／感謝文 三個分頁", "6", "封面圖片、推薦內容、計畫名稱、計畫內容、目標賽事、感謝標題、感謝內容"],
  ["9", "確認匯入內容", "總覽並送出", "—", "無截圖"],
], [700, 1600, 5200, 2400, 4100]));

// ---- Step 1
doc.push(h1("1. 受贈帳號"));
doc.push(note("畫面說明：新帳號會使用此帳號名稱與登入電子郵件；帳號持有人可透過「忘記密碼」設定密碼。畫面另有「個人／單位資料摘要」（姓名、聯絡電話）會隨第 2 步填寫內容自動更新，以及「清除資料並重新選擇」按鈕。"));
doc.push(ftable([
  ["帳號類型", "標籤", "—", "固定為「運動員」", "由前一畫面選擇受贈者類型帶入", "type（運動員）"],
  ["登入帳號", "文字", "必填", "3–20 個字元；僅能使用英文字母、數字、底線與連字號", "建議以英文姓名拼音或固定規則產生，避免重複", "無來源（需自訂規則產生）"],
  ["帳號電子郵件", "Email", "必填", "Email 格式", "作為登入與忘記密碼信箱", "contact.電子郵件（多數為「不公開」，需另蒐集）"],
]));

// ---- Step 2
doc.push(h1("2. 個人資料"));
doc.push(ftable([
  [sub("受贈者資料"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["姓名", "文字", "必填", "—", "與身分證一致", "name／info.運動員姓名"],
  ["出生日期", "日期", "必填", "YYYY-MM-DD（日期選擇器）", "—", "無來源（info.年齡 僅有年齡）"],
  ["身分證字號", "文字", "必填", "—", "外籍人士請勾選右側核取方塊", "無來源"],
  ["外籍人士", "核取方塊", "選填", "勾選／不勾選", "勾選後身分證字號欄位改填居留證號（推測）", "無來源"],
  ["性別", "下拉", "必填", "請選擇（選項截圖未展開）", "—", "info.性別"],
  [sub("戶籍地址"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["縣市", "下拉", "必填", "台灣縣市清單", "—", "info.縣市別（前 3 字）"],
  ["區", "下拉", "必填", "依縣市連動", "需先選縣市", "info.縣市別（後段鄉鎮市區）"],
  ["詳細地址", "文字", "必填", "街道、巷弄、號及樓層", "—", "無來源"],
  ["同戶籍地址", "核取方塊", "選填", "勾選後通訊地址同戶籍", "可省略下方通訊地址", "—"],
  [sub("通訊地址"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["縣市", "下拉", "必填", "台灣縣市清單", "—", "無來源"],
  ["區", "下拉", "必填", "依縣市連動", "—", "無來源"],
  ["詳細地址", "文字", "必填", "街道、巷弄、號及樓層", "—", "無來源"],
  [sub("聯絡資料"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["聯絡電話（手機）", "文字", "必填", "手機號碼", "會同步顯示於第 1 步的資料摘要", "contact.手機（部分為「不公開」）"],
  ["（截圖截斷）", "—", "—", "P2 截圖於此處截斷", "下方可能尚有市話、Email 等欄位，請於系統確認", "—"],
]));

// ---- Step 3
doc.push(h1("3. 基本資料"));
doc.push(ftable([
  [sub("申請資料"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["代表出賽縣市", "下拉", "必填", "請選擇", "—", "info.縣市別（前 3 字）"],
  ["運動類型", "下拉（可搜尋）", "必填", "搜尋運動項目", "—", "sport"],
  ["單項運動賽事", "下拉", "必填", "依運動類型連動；請先選擇運動類型", "—", "goals／achievements 內賽事名稱（需人工對應）"],
  [sub("受贈者銀行帳戶"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["銀行名稱", "下拉（可搜尋）", "必填", "搜尋銀行名稱或代碼", "—", "無來源"],
  ["戶名", "文字", "必填", "—", "應與受贈者姓名一致", "無來源"],
  ["分行", "下拉／文字", "選填", "搜尋或輸入分行名稱；可選建議分行或直接輸入", "—", "無來源"],
  ["銀行帳號", "文字", "必填", "—", "—", "無來源"],
  [sub("計畫期間"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["原計畫開始日期", "日期", "必填", "YYYY-MM-DD", "舊平台核准之計畫期間", "無來源（需查原申請資料）"],
  ["原計畫結束日期", "日期", "必填", "YYYY-MM-DD", "—", "無來源"],
  [sub("原申請紀錄"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["原申請日期", "日期", "必填", "YYYY-MM-DD", "—", "無來源"],
  ["原核准日期", "日期", "必填", "YYYY-MM-DD", "—", "無來源"],
  ["（截圖截斷）", "—", "—", "P3 截圖於此處截斷", "下方可能尚有原申請案號等欄位，請於系統確認", "—"],
]));

// ---- Step 4
doc.push(h1("4. 運動員資格"));
doc.push(note("畫面說明：請記錄原申請的資格類別與參賽證明；歷史匯入不重新評估目前資格。勾選的資格類別會在第 5 步「申請資格賽事」表格要求填寫對應賽事（日期、地點、賽事名稱、層級、名次、參賽規模）。"));
doc.push(ftable([
  [sub("運動員資格（勾選，可複選）"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["國際綜合性運動會", "核取方塊", "選填", "—", "如奧林匹克運動會、亞運、世大運、青奧、世運等（子層級於第 5 步選擇）", "achievements（需人工判讀）"],
  ["國際單項運動錦標賽", "核取方塊", "選填", "包括公開賽、巡迴賽、大獎賽、排名賽或經典賽", "—", "achievements（需人工判讀）"],
  ["全國綜合性運動會", "核取方塊", "選填", "—", "如全國運動會、全國大專運動會", "achievements（需人工判讀）"],
  ["全國性單項運動錦標賽最優級組", "核取方塊", "選填", "—", "—", "achievements（需人工判讀）"],
  ["經運動部核定辦理之學生聯賽最優級組", "核取方塊", "選填", "—", "—", "achievements（需人工判讀）"],
  ["職業運動聯盟主辦之職業比賽", "核取方塊", "選填", "—", "—", "achievements（需人工判讀）"],
  [sub("運動員特殊身分（可複選；皆不符合可不勾選；每個勾選項目下方需上傳證明文件）"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["低收入戶", "核取方塊＋上傳", "選填", "證明文件上傳", "—", "無來源"],
  ["中低收入戶", "核取方塊＋上傳", "選填", "證明文件上傳", "—", "無來源"],
  ["身心障礙人士", "核取方塊＋上傳", "選填", "證明文件上傳", "—", "info.身分別（如「身心障礙」）"],
  ["大學以下學生", "核取方塊＋上傳", "選填", "證明文件上傳", "—", "info.在學狀態（如「高中」）"],
  ["（截圖截斷）", "—", "—", "P4 於「大學以下學生」後截斷", "可能尚有其他身分選項", "—"],
  [sub("過去一年已領取及未來預計受捐贈、補助金額之相關文件資料"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["未指定捐贈款分配", "單選", "必填（預設）", "不申請未指定捐贈款分配（預設）／申請未指定捐贈款分配（請填寫下列明細）", "選「申請」時會展開明細表（截圖未展開）", "無來源"],
]));

// ---- Step 5
doc.push(h1("5. 訓練背景"));
doc.push(ftable([
  [sub("一、個人簡介及目標（含開始訓練時間）"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["個人簡介及目標", "多行文字", "選填", "—", "含開始訓練時間", "story（我的故事）"],
  [sub("二、過去兩年內參賽成績"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["申請資格賽事", "表格（由第 4 步資格帶入）", "—", "欄位：日期（起迄）、地點、賽事名稱／種類、層級、名次、參賽規模", "層級＝資格類別＋子層級（例：國際綜合性運動會 奧林匹克運動會）；名次例「第 1 名」；參賽規模例「4 人以上」", "achievements（需拆解為結構化欄位）"],
  ["過去兩年內參賽成績", "表格（多筆）", "選填", "欄位：開始日期、結束日期、地點、賽事名稱／種類項目、成績", "「＋新增二、過去兩年內參賽成績」", "achievements（近兩年者）"],
  [sub("三、指導教練（可多位，「＋新增三、指導教練」／「移除此教練」）"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["教練類型", "文字", "選填", "—", "—", "無來源"],
  ["教練姓名", "文字", "選填", "—", "—", "info.指導教練"],
  ["專項專長", "文字", "選填", "—", "—", "sport（推測）"],
  ["教練證照", "文字", "選填", "證照名稱／級別", "—", "無來源"],
  ["現職", "文字", "選填", "—", "—", "無來源"],
  ["學歷", "文字", "選填", "—", "—", "無來源"],
  ["工作經歷", "多行文字", "選填", "—", "—", "無來源"],
  ["教練證照正面", "上傳", "選填", "PDF、JPG 或 PNG，最大 20 MB；選取後即上傳", "—", "無來源"],
  ["教練證照背面", "上傳", "選填", "PDF、JPG 或 PNG，最大 20 MB；選取後即上傳", "—", "無來源"],
  [sub("四、訓練期程（「＋新增四、訓練期程」）"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["訓練期程", "表格（多筆）", "選填", "欄位：開始日期、結束日期、訓練重點、訓練時間、地點", "—", "training_periods（準備期／比賽期／過渡期 → 訓練重點）、training_methods"],
]));

// ---- Step 6
doc.push(h1("6. 計畫與資源"));
doc.push(ftable([
  [sub("五、參賽規劃"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["參賽規劃", "表格（多筆）", "選填", "欄位：開始日期、結束日期、地點、賽事名稱／種類項目、預期成績", "列出計畫期間（2 年）內預計參加之所有賽事（含國內外）。「預期成績」填具體目標名次或成績，如「賽事前 3 名」「突破台灣國家紀錄」，避免「盡力發揮」", "goals（我想達到…）"],
  [sub("六、預期效益"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["預期效益", "表格（多筆）", "選填", "欄位：效益", "列出可量測的具體成果，如「打破哪項紀錄」「達到哪個國際排名」「取得哪個資格或積分」", "benefits（需拆成逐條）"],
  [sub("七、經費需求及用途（可匯出／匯入 Excel；單位：新臺幣元）"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["支出科目", "固定 10 科目", "—", "見下表「10 項法定支出科目」；每科目最多 20 筆細項", "依「個人捐贈運動員專戶與所得稅列舉扣除實施辦法」第 10 條第 1 項編列", "needs（category＝經費需求，item 需對應科目）"],
  ["細項名稱", "文字", "選填", "例：餐費", "—", "needs.item"],
  ["數量", "數字", "選填", "例：1", "—", "無來源（舊平台僅有總額）"],
  ["單位", "文字", "選填", "例：天", "—", "無來源"],
  ["單價（元）", "數字", "選填", "例：0", "小計＝數量 × 單價（系統自動計算）；科目小計為細項加總", "needs.qty（舊平台金額可當單價、數量 1）"],
  ["說明", "多行文字", "選填", "填寫計算依據及必要性", "例：一、餐費：每日 150 元，兩年日數。二、營養補劑：每日 200 元，兩年日數（綜合維他命、魚油、胺基酸等）", "無來源"],
  ["總計金額", "自動", "—", "系統加總", "—", "amount（可用來核對）"],
  [sub("八、聯絡人（「＋新增八、聯絡人」）"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["聯絡人", "表格（多筆）", "選填（建議至少 2 位）", "欄位：姓名、關係、聯絡電話（手機）、電子郵件", "以非選手本人為宜（教練、經紀人、配偶、父母等）；主管機關審查期間若有疑義將優先聯繫", "contact（聯絡人／手機／電子郵件）"],
]));
doc.push(h3("10 項法定支出科目（每科目最多 20 筆細項）"));
doc.push(table(["#", "科目", "舊平台常見對應項目（needs.item）"], [
  ["1", "選手營養費", "選手營養費"], ["2", "教練指導費", "教練指導費"], ["3", "課業輔導費", "—"],
  ["4", "運動科學支援費", "運動科學支援費"], ["5", "運動防護費", "運動防護費"], ["6", "訓練器材裝備費", "訓練器材裝備費"],
  ["7", "參賽報名費", "參賽報名費"], ["8", "移地訓練費", "移地訓練費"], ["9", "選手零用金", "—"], ["10", "參賽旅運費", "參賽旅運費"],
], [700, 3300, 10000]));

// ---- Step 7
doc.push(h1("7. 附件"));
doc.push(ftable([
  ["身分證正面", "上傳", "必填", "PDF、JPG 或 PNG，最大 20 MB；選取後即上傳", "—", "無來源"],
  ["身分證反面", "上傳", "必填", "PDF、JPG 或 PNG，最大 20 MB；選取後即上傳", "—", "無來源"],
  ["存摺封面", "上傳", "必填", "PDF、JPG 或 PNG，最大 20 MB；選取後即上傳", "需與第 3 步銀行帳戶一致", "無來源"],
]));

// ---- Step 8
doc.push(h1("8. 文宣（三個分頁：個人頁面／捐贈項目／感謝文）"));
doc.push(h2("8-1 個人頁面"));
doc.push(ftable([
  [sub("封面照"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["封面圖片", "上傳（含裁切預覽）", "必填", "JPG、GIF、PNG、WebP；自動最佳化至約 600 KB；最佳化後上限 2 MB；原始檔上限 10 MB", "選取公開宣傳使用的圖片；選擇圖片以預覽實際裁切效果；過大會顯示「圖片最佳化後仍超過允許的檔案大小上限」", "data/images_original/<id>/封面照片.*（建議先縮至 10 MB 以下）"],
  [sub("關於我們（可「清除故事內容」）"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["選擇版型", "單選卡片", "必填", "純文字／圖文編排／圖文影音編排", "依是否有圖片、影片選擇", "有 story_images → 圖文編排；有 videos → 圖文影音編排"],
  ["段落標題", "文字", "選填", "—", "—", "story_title"],
  ["故事內容", "多行文字", "選填", "—", "—", "story"],
  ["參賽歷程", "多行文字", "選填（自動帶入）", "由第 5 步申請資格賽事帶入，格式「日期 地點 賽事 層級 名次」", "可再編修", "achievements"],
  ["推薦內容", "多行文字", "必填", "—", "舊平台僅 32／103 筆有推薦理由，其餘需補寫", "recommendation（缺者需補）"],
  ["相關照片", "清單（＋新增）", "選填", "上傳多張", "—", "data/images_original/<id>/相關照片*.*"],
  ["相關影片", "清單（＋新增）", "選填", "影片連結（YouTube）", "—", "videos（url／title）"],
  ["相關連結", "清單（＋新增）", "選填", "網址＋名稱", "—", "links（url／text）；另可加 media 補充連結"],
  [sub("關於計畫"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["計畫名稱", "文字", "必填", "—", "—", "plan_title（缺者用 name＋「訓練與參賽計畫」）"],
  ["計畫內容", "多行文字", "必填", "—", "—", "plan（12 筆為空，需補）"],
  ["計畫效益", "多行文字", "選填", "—", "—", "benefits"],
]));
doc.push(h2("8-2 捐贈項目"));
doc.push(ftable([
  ["目標賽事", "多行文字", "必填", "—", "—", "goals（逐條合併）"],
  ["經費需求及用途", "表格（唯讀）", "—", "自第 6 步驟經費表帶入；欄位：細項名稱、數量、單位、單價、說明、小計；含 10 科目與總計金額", "如需修改請回第 6 步編輯", "needs（經費需求）"],
  ["所需物資", "清單（＋新增）", "選填", "品項＋數量（截圖未展開）", "—", "needs（category＝物資需求：item／qty）"],
  [sub("聯絡人資訊（顯示於個人捐款頁面，請謹慎選擇是否公開；可「從聯絡人資料帶入」第 6 步聯絡人）"), sub(""), sub(""), sub(""), sub(""), sub("")],
  ["公開聯絡人", "文字", "選填", "—", "—", "contact.聯絡人"],
  ["公開電話", "文字", "選填", "—", "—", "contact.手機"],
  ["不公開電話", "核取方塊", "選填", "勾選後不顯示電話", "舊平台「不公開」者勾選", "contact.手機＝「不公開」→ 勾選"],
  ["公開電子郵件", "Email", "選填", "—", "—", "contact.電子郵件"],
  ["不公開電子郵件", "核取方塊", "選填", "勾選後不顯示 Email", "舊平台「不公開」者勾選", "contact.電子郵件＝「不公開」→ 勾選"],
]));
doc.push(h2("8-3 感謝文"));
doc.push(note("畫面說明：當捐贈者完成捐款後，系統將展示此感謝文內容。提供三個範本（簡短真誠型／情感敘事型／承諾回報型），按「套用此範本」後可自由修改。"));
doc.push(ftable([
  ["感謝標題", "文字", "必填", "—", "—", "無來源（可用「謝謝您支持〈姓名〉的〈運動〉之路」等固定句型）"],
  ["感謝內容", "多行文字", "必填", "—", "可套用範本後修改", "無來源（可由範本＋story 生成）"],
  ["感謝圖片", "清單（＋新增）", "選填", "上傳多張", "—", "photos"],
  ["感謝影片", "清單（＋新增）", "選填", "影片連結", "—", "videos"],
]));
doc.push(note("最後按「確認匯入內容」進入第 9 步確認頁（無截圖）。"));

// ---- Mapping summary
doc.push(h1("9. 自動上架資料準備總表"));
doc.push(h2("9-1 可直接由舊平台資料帶入"));
doc.push(table(["新系統欄位", "舊平台欄位（sponsor_data.json）", "轉換注意事項"], [
  ["姓名", "name", "團隊名稱含「－」前綴者（如「追風少年-國風田徑隊」）為團隊，非本表（運動員）範圍"],
  ["運動類型", "sport", "需對應新系統運動項目下拉選項"],
  ["代表出賽縣市／戶籍縣市、區", "info.縣市別", "拆成「縣市」「區」兩欄；2 筆為空"],
  ["性別、身分別、在學狀態", "info.性別／身分別／在學狀態", "身分別「身心障礙」→ 特殊身分勾選；在學狀態 → 大學以下學生"],
  ["教練姓名", "info.指導教練", "—"],
  ["故事內容／段落標題", "story／story_title", "2 筆 story 為空（內容在圖片中）"],
  ["參賽歷程、申請資格賽事、過去兩年參賽成績", "achievements（＋achievements_updated）", "舊平台為自由文字清單，需人工拆成日期／地點／賽事／層級／名次／規模"],
  ["推薦內容", "recommendation", "僅 32 筆有值；必填，缺者需補寫"],
  ["計畫名稱／計畫內容／計畫效益", "plan_title／plan／benefits", "plan 有 12 筆為空"],
  ["目標賽事、參賽規劃", "goals", "2 筆為空；參賽規劃需補日期與預期成績"],
  ["訓練期程", "training_periods／training_methods", "週期名稱＋內容 → 訓練重點；日期需補"],
  ["經費需求（10 科目）", "needs（category＝經費需求）", "項目名稱與科目幾乎一致；數量填 1、單價填金額、說明需補計算依據"],
  ["所需物資", "needs（category＝物資需求）", "item／qty 直接帶入"],
  ["公開聯絡人／電話／Email 與不公開勾選", "contact", "「不公開」→ 勾選不公開"],
  ["封面圖片、相關照片", "data/images_original/<id>/", "封面需 ≤ 10 MB（原檔有些超過，先縮圖）"],
  ["相關影片、相關連結", "videos／links（＋media 補充）", "—"],
  ["需求總額核對", "amount", "與經費表總計比對"],
], [3600, 4200, 6200]));
doc.push(h2("9-2 舊平台沒有、必須另向運動員蒐集"));
doc.push(table(["類別", "欄位", "步驟"], [
  ["帳號", "登入帳號、帳號電子郵件", "1"],
  ["身分", "出生日期、身分證字號、外籍人士、戶籍與通訊詳細地址", "2"],
  ["金融", "銀行名稱、戶名、分行、銀行帳號、存摺封面", "3、7"],
  ["申請紀錄", "原計畫開始／結束日期、原申請日期、原核准日期", "3"],
  ["資格", "資格類別勾選、特殊身分證明文件、未指定捐贈款分配", "4"],
  ["教練", "教練類型、證照、現職、學歷、工作經歷、證照正反面", "5"],
  ["經費細節", "每筆細項的數量、單位、單價、計算依據說明", "6"],
  ["證件", "身分證正反面", "7"],
  ["感謝文", "感謝標題、感謝內容", "8"],
], [2400, 9000, 2600]));

doc.push(h2("9-3 截圖未涵蓋、需於系統再確認之處"));
doc.push(bullet("第 2 步「聯絡資料」在「聯絡電話（手機）」之後的欄位。"));
doc.push(bullet("第 3 步「原申請紀錄」在「原核准日期」之後的欄位。"));
doc.push(bullet("第 4 步「運動員特殊身分」在「大學以下學生」之後的選項，以及「申請未指定捐贈款分配」展開後的明細表欄位。"));
doc.push(bullet("性別、代表出賽縣市、運動類型、單項運動賽事、銀行等下拉選單的完整選項值。"));
doc.push(bullet("「相關照片／影片／連結」「所需物資」「感謝圖片／影片」按「＋新增」後的子欄位。"));
doc.push(bullet("第 9 步「確認匯入內容」頁面。"));

// ---------- build ----------
const document = new Document({
  creator: "Ben Chou",
  title: "運動員上架需填資料欄位總表",
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE }, margin: { top: 850, bottom: 850, left: 850, right: 850 } } },
    children: doc,
  }],
});
Packer.toBuffer(document).then((buf) => { fs.writeFileSync(OUT, buf); console.log("written", OUT, buf.length, "bytes"); });
