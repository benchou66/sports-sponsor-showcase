# 抓舊資料平台 — 體育運動捐贈媒合平臺 資料重製站

- **線上網址**：https://benchou66.github.io/sports-sponsor-showcase/ （GitHub Pages，推上 main 後由 Actions 自動部署 `site/`）
- **GitHub repo**：https://github.com/benchou66/sports-sponsor-showcase

從 https://sponsor.sports.gov.tw/Home/Sitemap 的「運動員搜尋」抓下全部運動員與運動團隊資料（三個分頁：關於我們／關於計畫／捐贈需求）與所有圖片，重新做成一個靜態展示網站。

## 目錄

| 路徑 | 內容 |
|---|---|
| `site/index.html` | 首頁（精選故事、依運動種類／縣市／偏鄉篩選、搜尋、排序） |
| `site/p/<id>.html` | 每位運動員／團隊一頁（9 大區塊，見下） |
| `site/img/<id>/` | 壓縮後的圖片（封面 1600px、卡片 720px、故事／照片 1400px） |
| `site/assets/` | 共用 CSS / JS |
| `site/athletes.json` | 整理後的結構化資料（給其他系統用）；所有圖片欄位都是 `img/<id>/…` 本機路徑 |
| `data/sponsor_data.json` | 完整抓取結果；所有圖片欄位都是 `data/images_original/<id>/<原檔名>` 本機路徑，每張圖的 `original_url` 只作來源註記 |
| `data/images_original/<id>/` | 官網原始解析度圖檔（1,056 張、1.6 GB，檔名維持官網原名）。只存本機與 OneDrive，不進 git |
| `data/enrich/` | 網路搜尋補充的媒體報導／社群連結（含出處） |
| `scripts/scrape.py` | 抓取程式 |
| `scripts/build.py` | 網站產生器 |
| `scripts/check_links.py` | 補充連結存活檢查 |

## 每頁區塊

1. 我的故事（含推薦理由、故事圖片）
2. 參賽成績（官方頁面的「歷屆成績」清單；金／銀／銅自動標示）
3. 基本資料（姓名、運動種類、年齡、性別、身分別、在學狀態、縣市別、偏鄉、指導教練、推薦者）＋相關照片／影片／連結
4. 關於計畫（訓練與參賽計畫）
5. 預期效益
6. 捐贈需求：我想達到…
7. 我這樣訓練：訓練週期規劃＋訓練方式
8. 所以我需要…（經費需求含合計、物資需求）
9. 聯絡人資訊
10. 媒體報導與社群（網路搜尋補充，每則附原始出處連結）

每頁右上「前往官方平臺捐贈」直接連回官方頁面（含 paramToken）。

## 重新產生

```bash
py -I -X utf8 scripts/scrape.py <listing.html> <out_dir> <raw_detail_dir> <raw_img_dir>
py -I -X utf8 scripts/build.py <scrape_out>/sponsor_data.json data/images_original data/enrich site data
```

第 5 個參數 `data` 會把圖片欄位改成本機路徑後輸出 `data/sponsor_data.json`。

listing.html 為 https://sponsor.sports.gov.tw/Home/ApplySearch 的原始 HTML。

## 本機預覽

```bash
py -m http.server 8787 --directory site
```

然後開 http://localhost:8787/ 。直接用檔案總管雙擊 `site/index.html` 也可以（所有路徑皆為相對路徑）。

## 注意事項

- 官方公開頁面只有「歷屆成績」的自由文字清單，沒有結構化的賽事名稱／資格類別／賽事子層級／參賽規模／名次欄位，因此第 2 區塊呈現的是官方清單原文。
- 聯絡人資料依官方頁面呈現（「不公開」者維持不公開）。
- 媒體／社群連結全部來自網路搜尋結果並逐一開啟確認，仍可能有同名誤判；每則皆附出處連結，請以原始頁面為準。
