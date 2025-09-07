import tweepy
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime, timedelta
from collections import Counter
import io
import time
import re

class FinalKazeAnalyzer:
    def __init__(self):
        # Twitter API認証
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        # Twitter APIクライアント初期化
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=False
        )
        
        # 表記ゆれ対応の症状クエリ
        self.symptom_patterns = {
            "喉の症状": [
                "のどの痛み", "喉の痛み", "喉が痛い", "喉痛い",
                "のど痛い", "ノドが痛い", "のどいたい"
            ],
            "咳": [
                "咳", "せき", "セキ", "咳が出る", "ゴホゴホ"
            ],
            "発熱": [
                "発熱", "熱", "熱が出る", "熱っぽい", "微熱"
            ],
            "鼻の症状": [
                "鼻水", "鼻づまり", "鼻が詰まる", "はなみず"
            ],
            "風邪による頭痛": [
                "(頭痛 風邪)", "(頭が痛い 風邪)", "(ずつう 風邪)",
                "(頭痛 鼻水)", "(頭痛 咳)", "(頭痛 発熱)",
                "(頭が痛い 体調悪い)", "(頭痛 調子悪い)",
                "(ずつう 鼻づまり)", "(頭痛 のど)"
            ]
        }
        
        # 風邪関連の文脈キーワード
        self.cold_indicators = [
            "風邪", "鼻水", "咳", "発熱", "のど", "喉", "体調悪い", 
            "調子悪い", "鼻づまり", "熱っぽい", "ゴホゴホ"
        ]
        
        # 風邪以外の頭痛原因（除外用）
        self.non_cold_headache_indicators = [
            "偏頭痛", "片頭痛", "緊張型頭痛", "肩こり", "眼精疲労",
            "ストレス", "寝不足", "二日酔い", "生理", "低気圧",
            "疲労", "肩が", "首が", "目が疲れ"
        ]
        
        # ノイズ除去キーワード
        self.noise_patterns = [
            "治った", "良くなった", "演技", "フリ", "嘘", "冗談",
            "昨日", "去年", "先週", "RT", "歌詞", "小説", "ドラマ",
            "映画", "アニメ", "ゲーム", "漫画", "bot"
        ]
    
    def is_cold_related_headache(self, tweet_text):
        """風邪関連の頭痛かどうか判定"""
        text_lower = tweet_text.lower()
        
        # 風邪の文脈があるか
        has_cold_context = any(indicator in text_lower for indicator in self.cold_indicators)
        
        # 風邪以外の頭痛原因があるか
        has_non_cold_context = any(indicator in text_lower for indicator in self.non_cold_headache_indicators)
        
        # 風邪の文脈があり、かつ他の原因がない場合のみ
        return has_cold_context and not has_non_cold_context
    
    def build_symptom_query(self, symptom_name):
        """表記ゆれを考慮したクエリ作成"""
        if symptom_name == "風邪による頭痛":
            # 頭痛の複合検索
            keywords = " OR ".join(self.symptom_patterns[symptom_name])
            return f"({keywords}) -is:retweet lang:ja"
        else:
            keywords = " OR ".join(self.symptom_patterns[symptom_name])
            return f"({keywords}) 風邪 -is:retweet lang:ja"
    
    def get_time_ranges(self):
        """24時間を4つの時間帯に分割"""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        time_ranges = []
        for i in range(4):
            start = yesterday + timedelta(hours=i*6)
            end = yesterday + timedelta(hours=(i+1)*6)
            time_ranges.append((start, end))
        
        return time_ranges
    
    def is_valid_tweet(self, text, symptom_name=None):
        """ツイートの有効性をチェック"""
        text_lower = text.lower()
        
        # ノイズパターンを含む場合は除外
        for noise in self.noise_patterns:
            if noise in text_lower:
                return False
        
        # RTやメンションは除外
        if text.startswith('RT') or text.startswith('@'):
            return False
        
        # 風邪による頭痛の場合は追加チェック
        if symptom_name == "風邪による頭痛":
            return self.is_cold_related_headache(text)
            
        return True
    
    def collect_symptom_data_with_time_distribution(self):
        """時間帯分散を考慮した症状データ収集"""
        print("症状データ収集開始（時間帯分散・頭痛判定対応）...")
        symptom_counts = {}
        time_ranges = self.get_time_ranges()
        
        for symptom_name in self.symptom_patterns.keys():
            symptom_counts[symptom_name] = 0
            query = self.build_symptom_query(symptom_name)
            
            print(f"  {symptom_name} の分析開始...")
            
            # 各時間帯から少しずつデータ収集
            for i, (start_time, end_time) in enumerate(time_ranges):
                try:
                    tweets = self.client.search_recent_tweets(
                        query=query,
                        start_time=start_time.isoformat(),
                        end_time=end_time.isoformat(),
                        max_results=20,
                        tweet_fields=['created_at', 'author_id', 'text']
                    )
                    
                    if tweets.data:
                        valid_tweets = [
                            tweet for tweet in tweets.data 
                            if self.is_valid_tweet(tweet.text, symptom_name)
                        ]
                        symptom_counts[symptom_name] += len(valid_tweets)
                        print(f"    時間帯{i+1}: {len(valid_tweets)}件")
                    
                    time.sleep(2)
                    
                except tweepy.TooManyRequests:
                    print(f"    時間帯{i+1}: レート制限（スキップ）")
                    continue
                except Exception as e:
                    print(f"    時間帯{i+1}: エラー - {str(e)}")
                    continue
            
            print(f"  {symptom_name}: 合計{symptom_counts[symptom_name]}件")
        
        return symptom_counts
    
    def create_ranking_chart(self, symptom_counts):
        """ランキングチャート作成"""
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
        # データ準備
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        symptoms = [item[0] for item in sorted_symptoms]
        counts = [item[1] for item in sorted_symptoms]
        
        # グラフ作成
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(symptoms, counts, 
                     color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
        
        # グラフ装飾
        ax.set_title('風邪症状トレンドランキング（AI判定・24時間分散）', fontsize=14, pad=20)
        ax.set_ylabel('報告件数', fontsize=12)
        ax.set_xlabel('症状', fontsize=12)
        
        # 数値表示
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{count}件', ha='center', va='bottom', fontsize=10)
        
        plt.xticks(rotation=15)
        plt.tight_layout()
        
        # 画像をバイト配列として保存
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def generate_tweet_text(self, symptom_counts):
        """ツイート文生成"""
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        today = datetime.now().strftime('%m/%d')
        
        # ランキング文字列作成
        ranking_text = ""
        for i, (symptom, count) in enumerate(sorted_symptoms, 1):
            emoji = "📈" if count > 25 else "→" if count > 10 else "📉"
            ranking_text += f"{i}位: {symptom} ({count}件) {emoji}\n"
        
        # 警告メッセージ
        top_symptom = sorted_symptoms[0][0]
        warning = f"⚠️ {top_symptom}の報告が目立っています。体調管理にご注意ください"
        
        tweet_text = f"""🤧 風邪症状トレンド ({today})

📊 AI判定・24時間分散ランキング
{ranking_text.rstrip()}

{warning}

#風邪症状トレンド #健康管理 #AI分析 #予防"""
        
        return tweet_text
    
    def post_tweet_with_image(self, text, image_buffer):
        """画像付きツイート投稿"""
        try:
            auth = tweepy.OAuth1UserHandler(
                self.api_key, self.api_secret,
                self.access_token, self.access_token_secret
            )
            api_v1 = tweepy.API(auth)
            
            image_buffer.seek(0)
            media = api_v1.media_upload(filename="trend_chart.png", file=image_buffer)
            
            response = self.client.create_tweet(
                text=text,
                media_ids=[media.media_id]
            )
            
            print(f"ツイート投稿成功: {response.data['id']}")
            return True
            
        except Exception as e:
            print(f"ツイート投稿エラー: {str(e)}")
            return False
    
    def run_analysis(self):
        """メイン分析処理"""
        print("Health Analytics 最終版分析開始")
        print(f"実行時刻: {datetime.now()}")
        
        try:
            # 1. 時間帯分散データ収集
            symptom_counts = self.collect_symptom_data_with_time_distribution()
            
            # 2. チャート作成
            print("チャート作成中...")
            chart_image = self.create_ranking_chart(symptom_counts)
            
            # 3. ツイート文生成
            print("ツイート文生成中...")
            tweet_text = self.generate_tweet_text(symptom_counts)
            
            # 4. ツイート投稿
            print("ツイート投稿中...")
            success = self.post_tweet_with_image(tweet_text, chart_image)
            
            if success:
                print("分析・投稿完了！")
            else:
                print("投稿に失敗しました")
                
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    analyzer = FinalKazeAnalyzer()
    analyzer.run_analysis()
