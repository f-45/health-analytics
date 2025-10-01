# -*- coding: utf-8 -*-
import csv
from datetime import datetime, timedelta, timezone
import sys

import pandas as pd
import snscrape.modules.twitter as sntwitter

# ===== 設定 =====
# 必須: 「風邪」 + いずれかの症状ワード、言語は日本語
QUERY = '(風邪) (咳 OR 喉 OR 熱 OR 倦怠感 OR 頭痛 OR 鼻水 OR 鼻づまり OR 痰) lang:ja'
MAX_TWEETS = 250   # 1回の取得上限（控えめに）
# =================

def jst_now():
    # JST時刻関数
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9)))

def run():
    jst = jst_now()
    ts = jst.strftime('%Y%m%d_%H%M')
    out_csv = f'kaze_{ts}.csv'

    scraper = sntwitter.TwitterSearchScraper(QUERY)

    # 1. 前回の last_id を読み込み
    last_id = None
    try:
        with open("last_id.txt", "r") as f:
            last_id = int(f.read().strip())
    except FileNotFoundError:
        pass

    new_last_id = last_id

    rows = []
    count = 0
    for i, tweet in enumerate(scraper.get_items()):
        # 2. 前回までに取得したものはスキップ
        if last_id and tweet.id <= last_id:
            break

        # 3. ツイートを追加
        rows.append({
            '日時': tweet.date.astimezone(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S'),
            '本文': tweet.rawContent.replace('\n', ' ').replace('\r', ' ').strip(),
            '地域': tweet.user.location or '',
            'リツイート数': tweet.retweetCount,
            'いいね数': tweet.likeCount,
        })
        count += 1

        # 4. 上限件数に達したら終了
        if i >= MAX_TWEETS:
            break

        # 今回の最大IDを更新
        if not new_last_id or tweet.id > new_last_id:
            new_last_id = tweet.id

    # 5. ソートしてCSVに保存
    df = pd.DataFrame(rows)
    if not df.empty:
        df.sort_values(by=['いいね数', 'リツイート数'], ascending=[False, False], inplace=True)
        df.to_csv(out_csv, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_MINIMAL)

    print(f'[{jst.strftime("%Y-%m-%d %H:%M:%S")}] 取得件数: {count}件 -> {out_csv}')

    # 6. 新しい last_id を保存
    if new_last_id:
        with open("last_id.txt", "w") as f:
            f.write(str(new_last_id))

if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
