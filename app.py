from flask import Flask, jsonify
import feedparser
import json
from datetime import datetime
from typing import List
from newspaper import Article
import warnings

# Suppress newspaper warnings
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)

class DisasterNewsFilter:
    def __init__(self):
        # Keywords related to natural disasters
        self.natural_disaster_keywords = [
            'भूकंप', 'बाढ़', 'सुनामी', 'चक्रवात', 'हरिकेन',
            'भूस्खलन', 'सूखा', 'जंगल की आग', 'ज्वालामुखी',
            'टोर्नेडो', 'तूफान', 'हिमस्खलन', 'लू', 'शीत लहर'
        ]

        # Keywords related to man-made disasters
        self.manmade_disaster_keywords = [
            'विस्फोट', 'आग', 'पतन', 'दुर्घटना', 'रासायनिक रिसाव',
            'तेल रिसाव', 'परमाणु', 'संदूषण', 'पटरी से उतरना',
            'भवन पतन', 'औद्योगिक दुर्घटना'
        ]

    def fetch_feed(self, feed_url: str) -> List[dict]:
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                print(f"Warning: No entries found in feed: {feed_url}")
            return feed.entries
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {str(e)}")
            return []

    def is_disaster_related(self, text: str) -> tuple:
        text = text.lower()

        # Check for natural disasters
        for keyword in self.natural_disaster_keywords:
            if keyword in text:
                return True, 'natural'

        # Check for man-made disasters
        for keyword in self.manmade_disaster_keywords:
            if keyword in text:
                return True, 'man-made'

        return False, None

    def filter_disaster_news(self, feeds: List[str]) -> List[dict]:
        disaster_news = []
        for feed_url in feeds:
            entries = self.fetch_feed(feed_url)
            for entry in entries:
                text_to_check = f"{entry.get('title', '')} {entry.get('description', '')}"
                is_disaster, disaster_type = self.is_disaster_related(text_to_check)
                if is_disaster:
                    image_url = None
                    if 'media_content' in entry:
                        image_url = entry['media_content'][0].get('url')
                    disaster_news.append({
                        'title': entry.get('title', 'N/A'),
                        'link': entry.get('link', 'N/A'),
                        'description': entry.get('description', 'N/A'),
                        'publish_date': entry.get('published', 'N/A'),
                        'disaster_type': disaster_type,
                        'image_url': image_url
                    })
        return disaster_news


def parse_article(url: str) -> dict:
    try:
        article = Article(url, language='hi')
        article.download()
        article.parse()

        date = article.publish_date.strftime("%Y-%m-%d") if article.publish_date else None
        return {
            "title": article.title,
            "content": article.text,
            "text_length": len(article.text),
            "publish_date": date,
            "url": url,
            "status": "success"
        }
    except Exception as e:
        return {
            "url": url,
            "status": "failed",
            "error": str(e)
        }


def scrape_articles(urls: List[str]) -> List[dict]:
    results = []
    for url in urls:
        result = parse_article(url)
        results.append(result)
    return results


@app.route('/v1/hindi-news', methods=['GET'])
def get_disaster_news():
    feeds = [
        'https://www.aajtak.in/rssfeeds/?id=home',
        'https://www.abplive.com/home/feed',
        'https://feeds.feedburner.com/ndtvkhabar-latest',
        'https://hindi.news18.com/rss/khabar/nation/nation.xml',
        'https://www.amarujala.com/rss/breaking-news.xml'
    ]

    disaster_filter = DisasterNewsFilter()

    # Filter disaster-related news
    disaster_news = disaster_filter.filter_disaster_news(feeds)

    disaster_news_urls = [news['link'] for news in disaster_news]

    # Scrape articles from disaster-related news URLs
    scraped_results = scrape_articles(disaster_news_urls)

    return jsonify({
        'status': 'success',
        'data': scraped_results
    })


if __name__ == "__main__":
    app.run(debug=True)
