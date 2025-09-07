import tweepy
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime, timedelta
from collections import Counter
import io
import time

class PollenAnalyzer:
    def __init__(self):
        # Twitter API認証（花粉症版）
        self.bearer_token = os.getenv('POLLEN_TWITTER_BEARER_TOKEN')
        self.api_key = os.getenv('POLLEN_TWITTER_API_KEY')
        self.api_secret = os.getenv('POLLEN_TWITTER_API_SECRET')
        self.access_token = os.getenv('POLLEN_TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('POLLEN_TWITTER_ACCESS_TOKEN_SECRET')
        
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=False
        )
        
        self.pollen_symptoms = {
            "くしゃみ": ["くしゃみ", "ハクション", "連続くしゃみ", "くしゃみが止まらない"],
            "鼻水": ["鼻水", "水っぽい鼻水", "透明な鼻水", "はなみず", "鼻がグズグズ"],
            "目のかゆみ": ["目がかゆい", "目のかゆみ", "目が痒い", "涙が出る", "目がしょぼしょぼ"],
            "鼻づまり": ["鼻づまり", "鼻が詰まる", "鼻が通らない", "鼻がムズムズ"]
        }
        
        self.pollen_indicators = [
            "花粉", "花粉症", "アレルギー", "スギ", "ヒノキ", "イネ", "ブタクサ", "ヨモギ",
            "マスクしても", "外に出ると", "季節性", "毎年この時期"
        ]
        
        self.cold_exclusions = [
            "風邪", "発熱", "のど", "喉", "体調悪い", "寒気", "関節痛", "咳"
        ]

    def is_pollen_related_symptom(self, tweet_text):
        text_lower = tweet_text.lower()
        has_pollen_context = any(indicator in text_lower for indicator in self.pollen_indicators)
        has_cold_context = any(exclusion in text_lower for exclusion in self.cold_exclusions)
        return has_pollen_context and not has_cold_context

    def build_symptom_query(self, symptom_name):
        keywords = " OR ".join(self.pollen_symptoms[symptom_name])
        # 花粉症の文脈を含むクエリに改善
        return f"({keywords}) (花粉 OR アレルギー OR 花粉症 OR ブタクサ) -is:retweet lang:ja"

    def is_valid_tweet(self, text, symptom_name):
        if text.startswith('RT') or text.startswith('@'):
            return False
        # ノイズ除去
        noise_words = ["治った", "良くなった", "演技", "フリ", "嘘", "冗談", "昨日", "去年"]
        text_lower = text.lower()
        if any(noise in text_lower for noise in noise_words):
            return False
        return self.is_pollen_related_symptom(text)

    def collect_pollen_data(self):
        print("花粉症症状データ収集開始...")
        symptom_counts = {}
        
        for symptom_name in self.pollen_symptoms.keys():
            symptom_counts[symptom_name] = 0
            query = self.build_symptom_query(symptom_name)
            
            try:
                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=50,  # 件数を増加
                    tweet_fields=['created_at', 'text']
                )
                
                if tweets.data:
                    valid_tweets = [tweet for tweet in tweets.data if self.is_valid_tweet(tweet.text, symptom_name)]
                    symptom_counts[symptom_name] = len(valid_tweets)
                    print(f"{symptom_name}: {len(valid_tweets)}件")
                else:
                    print(f"{symptom_name}: 0件")
                
                time.sleep(3)  # API制限対策
                
            except Exception as e:
                print(f"{symptom_name}: エラー - {str(e)}")
                symptom_counts[symptom_name] = 0
        
        return symptom_counts

    def create_pollen_chart(self, symptom_counts):
        # 日本語フォント設定の改善
        try:
            import japanize_matplotlib
            japanize_matplotlib.japanize()
        except ImportError:
            # フォールバック設定
            plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'IPAexGothic']
        
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        symptoms = [item[0] for item in sorted_symptoms]
        counts = [item[1] for item in sorted_symptoms]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(symptoms, counts, color=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99'])
        
        ax.set_title('花粉症症状トレンドランキング', fontsize=16, pad=20, fontweight='bold')
        ax.set_ylabel('報告件数', fontsize=12)
        ax.set_xlabel('症状', fontsize=12)
        
        # グリッド追加で見やすく
        ax.grid(True, alpha=0.3, axis='y')
        
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{count}件', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        plt.xticks(rotation=0)
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer

    def generate_pollen_tweet(self, symptom_counts):
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        today = datetime.now().strftime('%m/%d')
        
        # 絵文字を大幅削減
        ranking_text = ""
        for i, (symptom, count) in enumerate(sorted_symptoms, 1):
            ranking_text += f"{i}位: {symptom} ({count}件)\n"
        
        top_symptom = sorted_symptoms[0][0]
        
        # シンプルで自然な文章に変更
        tweet_text = f"""花粉症症状トレンド ({today})

本日のランキング:
{ranking_text.rstrip()}

{top_symptom}の報告が多くなっています。
外出時はマスクや眼鏡での対策をおすすめします。

#花粉症 #アレルギー #健康管理 #花粉対策"""
        
        return tweet_text

    def post_tweet_with_image(self, text, image_buffer):
        try:
            auth = tweepy.OAuth1UserHandler(
                self.api_key, self.api_secret,
                self.access_token, self.access_token_secret
            )
            api_v1 = tweepy.API(auth)
            
            image_buffer.seek(0)
            media = api_v1.media_upload(filename="pollen_chart.png", file=image_buffer)
            
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
        print("Po Analytics 花粉症分析開始")
        print(f"実行時刻: {datetime.now()}")
        
        try:
            symptom_counts = self.collect_pollen_data()
            
            print("チャート作成中...")
            chart_image = self.create_pollen_chart(symptom_counts)
            
            print("ツイート文生成中...")
            tweet_text = self.generate_pollen_tweet(symptom_counts)
            
            print("ツイート投稿中...")
            success = self.post_tweet_with_image(tweet_text, chart_image)
            
            if success:
                print("花粉症分析・投稿完了")
            else:
                print("投稿に失敗しました")
                
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    analyzer = PollenAnalyzer()
    analyzer.run_analysis()
