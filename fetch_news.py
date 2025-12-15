import feedparser
import json
import time
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

#Gemini APIキーを設定
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEYが設定されていません。.envファイルまたは環境変数を確認してください。")

genai.configure(api_key=GEMINI_API_KEY)
print(f"✅ APIキーを読み込みました: {GEMINI_API_KEY[:10]}...")

RSS_FEEDS = {
    'technology': [
        'https://news.yahoo.co.jp/rss/topics/it.xml',
        'https://www.itmedia.co.jp/rss/2.0/news_bursts.xml',
        'https://forest.watch.impress.co.jp/data/rss/1.0/wf/feed.rdf'
    ],
    'business': [
        'https://news.yahoo.co.jp/rss/topics/business.xml',
        'https://www.nhk.or.jp/rss/news/cat0.xml',
        'https://biz-journal.jp/index.xml'
    ],
    'sports': [
        'https://news.yahoo.co.jp/rss/topics/sports.xml',
        'https://www.nhk.or.jp/rss/news/cat6.xml',
        'https://www.nikkansports.com/rss/news.rdf'
    ],
    'entertainment': [
        'https://news.yahoo.co.jp/rss/topics/entertainment.xml',
        'https://natalie.mu/music/feed/news',
        'https://www.cinematoday.jp/rss/1.0/news.rdf'
    ]
}

def fetch_rss_feed(url, max_items=5):
    """RSSフィードから記事を取得"""
    try:
        print(f"📡 Fetching: {url}")
        feed = feedparser.parse(url)
        return feed.entries[:max_items]
    except Exception as e:
        print(f"❌ Error fetching {url}: {str(e)}")
        return []

def clean_text(text):
    """HTMLタグを除去"""
    if not text:
        return ""
    import re
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    return text.strip()

def generate_tags_with_gemini(title, description):
    """Gemini APIでタグを生成"""
    try:
        model = genai.GenerativeModel('gemini-robotics-er-1.5-preview')
        
        prompt = f"""以下のニュース記事に対して、内容を表す3-5個の適切な日本語タグを生成してください。
タグはカンマ区切りで出力してください。

タイトル: {title}
概要: {description[:200]}

タグのみを出力してください（説明文は不要）:"""

        response = model.generate_content(prompt)
        tags_text = response.text.strip()
        
        tags = [tag.strip() for tag in tags_text.replace('、', ',').split(',')]
        tags = [tag for tag in tags if tag and len(tag) < 20][:5]
        
        print(f"  🏷️  Tags: {', '.join(tags)}")
        return tags
        
    except Exception as e:
        print(f"  ❌ Gemini API error: {str(e)}")
        return ['AI分析中']

def format_date(date_str):
    """日付をフォーマット"""
    try:
        if hasattr(date_str, 'tm_year'):
            return time.strftime('%Y-%m-%d %H:%M:%S', date_str)
        return date_str
    except:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def main():
    """メイン処理"""
    print('🚀 Starting news aggregation with Gemini API...\n')
    
    all_articles = []
    article_id = 1
    
    for category, feeds in RSS_FEEDS.items():
        print(f'\n📂 Category: {category.upper()}')
        
        for feed_url in feeds:
            entries = fetch_rss_feed(feed_url, max_items=4)
            
            for entry in entries:
                title = clean_text(entry.get('title', ''))
                description = clean_text(entry.get('description', '') or entry.get('summary', ''))[:300]
                link = entry.get('link', '')
                pub_date = format_date(entry.get('published_parsed', ''))
                
                if title and link:
                    print(f"\n  📰 Processing: {title[:60]}...")
                    
                    #Gemini APIでタグを生成
                    tags = generate_tags_with_gemini(title, description)
                    
                    all_articles.append({
                        'id': article_id,
                        'title': title,
                        'link': link,
                        'description': description,
                        'category': category,
                        'tags': tags,
                        'pubDate': pub_date,
                        'source': feed_url.split('/')[2].replace('www.', '')
                    })
                    
                    article_id += 1
                    
                    time.sleep(1)
    
    # all_topics.jsonに保存
    print(f'\n💾 Saving {len(all_articles)} articles to all_topics.json...')
    with open('all_topics.json', 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    
    print('✅ Done! News aggregation completed successfully.')
    print(f'📊 Total articles: {len(all_articles)}')
    
    # カテゴリ別の統計
    for category in RSS_FEEDS.keys():
        count = sum(1 for a in all_articles if a['category'] == category)
        print(f'   - {category}: {count} articles')

if __name__ == '__main__':
    main()