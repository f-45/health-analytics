# 風邪症状トレンド分析システム 🤧

Twitter上の風邪症状に関するツイートを分析し、症状別のトレンドを可視化するシステムです。

## 機能
- Twitter APIを使用した症状ツイートの収集
- ノイズ除去による高精度な分析
- 症状別ランキングの自動生成
- グラフ付きツイートの自動投稿
- GitHub Actionsによる完全自動化

## 分析対象症状
- 咳
- 鼻水
- 鼻づまり  
- のどの痛み
- 発熱
- 頭痛
- 倦怠感

## 自動実行スケジュール
3日に1回、日本時間朝7時に自動実行

## 技術スタック
- Python 3.9
- Twitter API v2
- matplotlib（グラフ生成）
- GitHub Actions（自動化）

## セットアップ
1. Twitter API認証情報をGitHub Secretsに設定
2. GitHub Actionsが自動実行

---
Health Analytics プロジェクトの一部として開発
