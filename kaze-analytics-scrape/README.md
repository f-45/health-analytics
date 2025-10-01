# 風邪症状トレンド収集システム 🤧

Twitter上の「風邪」関連ツイートを収集し、CSVに保存するシステムです。  
GitHub Actionsで自動実行し、症状トレンドの基礎データを蓄積します。

---

## 機能
- Twitter検索ページをスクレイピングし、指定症状を含むツイートを収集
- 日本語ツイートに限定（`lang:ja`）
- 重複排除（前回取得以降のツイートのみ保存）
- いいね数・リツイート数でソート
- CSV形式で保存（UTF-8 BOM付き）
- GitHub Actionsによる完全自動実行

---

## 分析対象症状
- 咳  
- 喉  
- 熱  
- 倦怠感  
- 頭痛  
- 鼻水  
- 鼻づまり  
- 痰  

※必ず「風邪」というワードを含むツイートが対象

---

## 自動実行スケジュール
1日4回、日本時間で以下のタイミングに自動実行されます：  
- 09:10  
- 15:10  
- 21:10  
- 03:10  

（GitHub ActionsのcronはUTCで `00:10 / 06:10 / 12:10 / 18:10`）

---

## 技術スタック
- Python 3.11  
- [snscrape](https://github.com/JustAnotherArchivist/snscrape)（ツイート取得）  
- pandas（CSV出力とソート）  
- GitHub Actions（自動実行とArtifacts保存）  

---

## セットアップ
1. 本リポジトリをクローン  
2. 依存関係をインストール  
   ```bash
   pip install -r requirements.txt


Health Analytics プロジェクトの一部として開発
