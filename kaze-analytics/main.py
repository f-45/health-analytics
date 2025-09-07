import tweepy
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime, timedelta
from collections import Counter
import io
import base64
import re

class KazeAnalyzer:
    def __init__(self):
        # Twitter API認証（GitHub Secretsから取得）
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
            wait_on_rate_limit=True
        )
        
        # 症状キーワード
        self.symptoms = ["咳", "鼻水", "鼻づまり", "のどの痛み", "発熱", "頭痛", "倦怠感"]
        
        # ノイズ除去キーワード
        self.noise_patterns = [
            "治った", "良くなった", "演技", "フリ", "嘘", "冗談",
            "昨日", "去年", "先週", "RT", "歌詞", "小説", "ドラマ",
            "映画", "アニメ", "ゲーム", "漫画"
        ]
    
    def is_valid_tweet(self, text):
        """ツイートの有効性をチェック"""
        text_lower = text.lower()
        
        # ノイズパターンを含む場合は除外
        for noise in self.noise_patterns:
            if noise in text_lower:
                return False
        
        # RTやメンションは除外
        if text.startswith('RT') or text.startswith('@'):
            return False
            
        return True
    
    def collect_symptom_data(self):
        """症状データを収集"""
        print("🔍 症状データ収集開始...")
        symptom_counts = {}
        
        for symptom in self.symptoms:
            try:
                query = f"{symptom} 風邪 -is:retweet lang:ja"
                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=100,
                    tweet_fields=['created_at', 'author_id', 'text']
                )
                
                if tweets.data:
                    valid_tweets = [
                        tweet for tweet in tweets.data 
                        if self.is_valid_tweet(tweet.text)
                    ]
                    symptom_counts[symptom] = len(valid_tweets)
                    print(f"  {symptom}: {len(valid_tweets)}件（{len(tweets.data)}件中）")
                else:
                    symptom_counts[symptom] = 0
                    print(f"  {symptom}: 0件")
                    
            except Exception as e:
                print(f"  {symptom}: エラー - {str(e)}")
                symptom_counts[symptom] = 0
        
        return symptom_counts
    
    def create_ranking_chart(self, symptom_counts):
        """ランキングチャートを作成"""
        # 日本語フォント設定
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
        # データ準備
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        symptoms = [item[0] for item in sorted_symptoms]
        counts = [item[1] for item in sorted_symptoms]
        
        # グラフ作成
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(symptoms, counts, 
                     color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'])
        
        # グラフ装飾
        ax.set_title('🤧 風邪症状トレンドランキング', fontsize=16, pad=20)
        ax.set_ylabel('報告件数', fontsize=12)
        ax.set_xlabel('症状', fontsize=12)
        
        # 数値表示
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{count}件', ha='center', va='bottom', fontsize=10)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 画像をバイト配列として保存
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def generate_tweet_text(self, symptom_counts):
        """ツイート文を生成"""
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        today = datetime.now().strftime('%m/%d')
        
        # ランキング文字列作成
        ranking_text = ""
        for i, (symptom, count) in enumerate(sorted_symptoms[:5], 1):
            emoji = "📈" if count > 50 else "→" if count > 20 else "📉"
            ranking_text += f"{i}位: {symptom} ({count}件) {emoji}\n"
        
        # 警告メッセージ
        top_symptom = sorted_symptoms[0][0]
        warning = f"⚠️ {top_symptom}の報告が多くなっています！早めの対策を心がけましょう"
        
        tweet_text = f"""🤧 風邪症状トレンド ({today})

📊 今日のランキング
{ranking_text.rstrip()}

{warning}

#風邪症状トレンド #健康管理 #体調管理 #予防"""
        
        return tweet_text
    
    def post_tweet_with_image(self, text, image_buffer):
        """画像付きツイートを投稿"""
        try:
            # Twitter API v1.1用の認証（画像アップロード用）
            auth = tweepy.OAuth1UserHandler(
                self.api_key, self.api_secret,
                self.access_token, self.access_token_secret
            )
            api_v1 = tweepy.API(auth)
            
            # 画像アップロード
            image_buffer.seek(0)
            media = api_v1.media_upload(filename="trend_chart.png", file=image_buffer)
            
            # ツイート投稿（v2 API）
            response = self.client.create_tweet(
                text=text,
                media_ids=[media.media_id]
            )
            
            print(f"✅ ツイート投稿成功: {response.data['id']}")
            return True
            
        except Exception as e:
            print(f"❌ ツイート投稿エラー: {str(e)}")
            return False
    
    def run_analysis(self):
        """メイン分析処理"""
        print("🚀 Health Analytics 分析開始")
        print(f"実行時刻: {datetime.now()}")
        
        try:
            # 1. データ収集
            symptom_counts = self.collect_symptom_data()
            
            # 2. チャート作成
            print("📊 チャート作成中...")
            chart_image = self.create_ranking_chart(symptom_counts)
            
            # 3. ツイート文生成
            print("✍️ ツイート文生成中...")
            tweet_text = self.generate_tweet_text(symptom_counts)
            
            # 4. ツイート投稿
            print("📤 ツイート投稿中...")
            success = self.post_tweet_with_image(tweet_text, chart_image)
            
            if success:
                print("🎉 分析・投稿完了！")
            else:
                print("⚠️ 投稿に失敗しました")
                
        except Exception as e:
            print(f"💥 エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    analyzer = KazeAnalyzer()
    analyzer.run_analysis()
