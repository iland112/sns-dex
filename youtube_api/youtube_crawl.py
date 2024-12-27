import sqlite3
import json
import requests
import datetime as dt
import pandas as pd


DB_FILE_PATH = "./data/youtube1.db"
YOUTUBE_API_KEY = "AIzaSyAlTmAytStJLjhENxoW0ctNP7qdYvKAZbQ"

class YoutubeCrawl:
    
    def __init__(self, query, order="relevance", category="ALL", country="ALL", language="ALL", duration='any'):
        self.query = query
        self.order = order
        self.category = category
        self.country = country
        self.language = language
        self.duration = duration
        self.total_results = None
        self.results_per_page = None
        self.next_page_token = None
        self.prev_page_token = None
        self.con = sqlite3.connect(DB_FILE_PATH)
        self.cur = self.con.cursor()
        
    def __del__(self):
        self.cur.close()
        self.con.close()
        
    
    def search_contents(self):
        print(self.query, self.country)
        params = {
            'key': YOUTUBE_API_KEY,
            'part': 'snippet',
            'type': 'video',
            'safeSearch': 'strict',
            'videoDuration': self.duration,
            'q': self.query,
            'maxResults': '10',
        }
        # optional parameters
        if self.order != "relevance":
            params['order'] = self.order

        if self.category and self.category != "ALL":
            params['videoCategoryId'] = self.category

        if self.country and self.country != "ALL":
            params['regionCode'] = self.country

        if self.language and self.language != "ALL":
            params['relevanceLanguage'] = self.language

        print("url_params: ", json.dumps(params, indent=2))
        url = f"https://youtube.googleapis.com/youtube/v3/search?"
        response = requests.get(url=url, params=params)
        if response.status_code != 200:
            print("Error: ", response.status_code, response.text)
            return None
        
        # create search_contents table if does not exists        
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS search_contents(
                id INTEGER PRIMARY KEY,
                query TEXT NOT NULL,
                sort TEXT NOT NULL,
                category_id TEXT NOT NULL,
                country TEXT NOT NULL,
                video_duration TEXT NOT NULL,
                published_at TIMESTAMP,
                kind TEXT,
                channel_id TEXT NOT NULL,
                channel_title TEXT,
                video_id TEXT NOT NULL,
                video_title TEXT,
                video_description TEXT,
                thumbnail TEXT,
                thumbnail_width INTEGER,
                thumbnail_height INTEGER,
                inserted_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        r = response.json()
        self.total_results = r['pageInfo']['totalResults']
        self.results_per_page = r['pageInfo']['resultsPerPage']
        self.next_page_token = r.get('nextPageToken', None)
        self.prev_page_token =  r.get('prevPageToken', None)
        self.country = r['regionCode']

        pages = int(self.total_results / self.results_per_page)
        print(f"pages: {pages}")

        items = r['items']
        print(f"item count: {len(items)}")
        print(f"previous page token: {self.prev_page_token}, next page token: {self.next_page_token}")
        for item in items:
            self.save_search_content_data(item)
                        
            # load video data    
            params = {
                'key': YOUTUBE_API_KEY,
                'part': 'snippet,contentDetails,statistics',
                'id': item['id']['videoId'],
            }
            video_api_url = f"https://youtube.googleapis.com/youtube/v3/videos?"
            response = requests.get(url=video_api_url, params=params)
            self.parse_video(response)
            # load channel data
            
            params = {
                'key': YOUTUBE_API_KEY,
                'part': 'snippet,contentDetails,statistics',
                'id': item['snippet']['channelId'],
            }
            channel_api_url = f"https://youtube.googleapis.com/youtube/v3/channels?"
            response = requests.get(url=channel_api_url, params=params)
            self.parse_channel(response)

    def save_search_content_data(self, item):
        video_id = item['id']['videoId']
        kind = item['id']['kind']
        channel_id = item['snippet']['channelId']
        video_title = item['snippet']['title']
        channel_title = item['snippet']['channelTitle']
        video_description = item['snippet']['description']
        published_at = item['snippet']['publishedAt']
        thumbnail = item['snippet']['thumbnails']['default']['url']
        thumbnail_width = item['snippet']['thumbnails']['default']['width']
        thumbnail_height = item['snippet']['thumbnails']['default']['height']
            
        search_query = """
            SELECT * FROM search_contents WHERE video_id = ? and channel_id = ?
        """

        self.cur.execute(search_query, (video_id, channel_id,))
        result = self.cur.fetchone()

        if result:
            print(f"Content Data already in database: channel_id[{channel_id}], video_id[{video_id}]")
        else:
            published_at = dt.datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
            inserted_at = dt.datetime.now()
            self.cur.execute("""
                INSERT INTO search_contents (
                    query, sort, category_id, country, video_duration, published_at, kind,
                    channel_id, channel_title, video_id, video_title, video_description,
                    thumbnail, thumbnail_width, thumbnail_height,
                    inserted_at, updated_at)
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?
                )
            """, (
                    self.query, self.sort, self.category_id, self.country, self.video_duration, published_at, kind,
                    channel_id, channel_title, video_id, video_title, video_description,
                    thumbnail, thumbnail_width, thumbnail_height,
                    inserted_at, inserted_at
                )
            )
            self.con.commit()
        
    def parse_video(self, response):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS videos(
                id INTEGER PRIMARY KEY,
                video_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                kind TEXT,
                title TEXT,
                description TEXT,
                published_at TIMESTAMP,
                thumbnail TEXT,
                thumbnail_width INTEGER,
                thumbnail_height INTEGER,
                view_count INTEGER,
                like_count INTEGER,
                favorite_count INTEGER,
                comment_count INTEGER,
                inserted_at DATETIME,
                updated_at DATETIME
            )
        """)

        items = response.json()['items']

        for item in items:
            video_id = item['id']
            channel_id = item['snippet']['channelId']
            kind = item['kind']
            title = item['snippet']['title']
            description = item['snippet']['description']
            published_at = item['snippet']['publishedAt']
            thumbnail = item['snippet']['thumbnails']['high']['url']
            thumbnail_width = item['snippet']['thumbnails']['high']['width']
            thumbnail_height = item['snippet']['thumbnails']['high']['height']
            statistics = item['statistics']
            view_count = statistics.get('viewCount', 0)
            like_count = statistics.get('likeCount', 0)
            favorite_count = statistics.get('favoriteCount', 0)
            comment_count = statistics.get('commentCount', 0)

            self.cur.execute("select * from videos where video_id = ?", (video_id,))
            result = self.cur.fetchone()

            if result:
                print(f"VideoID already in database: {video_id}")
            else:
                published_at = dt.datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                inserted_at = dt.datetime.now()
                self.cur.execute("""
                    INSERT INTO videos (
                        video_id, channel_id, kind,
                        title, description, published_at,
                        thumbnail, thumbnail_width, thumbnail_height,
                        view_count, like_count, favorite_count, comment_count,
                        inserted_at, updated_at
                    ) 
                    VALUES (
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?
                    )
                    """,(
                        video_id, channel_id, kind,
                        title, description, published_at,
                        thumbnail, thumbnail_width, thumbnail_height,
                        view_count, like_count, favorite_count, comment_count,
                        inserted_at, inserted_at
                    )
                )
                self.con.commit()

    def parse_channel(self, response):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS channels(
                id INTEGER PRIMARY KEY,
                channel_id TEXT NOT NULL,
                title TEXT,
                description TEXT,
                published_at TIMESTAMP,
                thumbnail TEXT,
                thumbnail_width INTEGER,
                thumbnail_height INTEGER,
                view_count INTEGER,
                subscriber_count INTEGER,
                video_count INTEGER,
                inserted_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        items = response.json()['items']

        for item in items:
            channel_id = item['id']
            title = item['snippet']['title']
            description = item['snippet']['description']
            published_at = item['snippet']['publishedAt']
            # channelItem['country'] = item['snippet']['country']
            thumbnail = item['snippet']['thumbnails']['default']['url']
            thumbnail_width = item['snippet']['thumbnails']['default']['width']
            thumbnail_height = item['snippet']['thumbnails']['default']['height']
            view_count = item['statistics']['viewCount']
            subscriber_count = item['statistics']['subscriberCount']
            video_count = item['statistics']['videoCount']

            self.cur.execute("select * from channels where channel_id = ?", (channel_id,))
            result = self.cur.fetchone()

            if result:
                print(f"Channel already in database: {channel_id}")
            else:
                published_at = published_at
                published_at_list = published_at.strip().split('.')
                print(f"published at: {published_at_list}")
                if len(published_at_list) == 1:
                    published_at = dt.datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                elif len(published_at_list) == 2:
                    published_at = dt.datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%S.%fZ')
                inserted_at = dt.datetime.now()
                self.cur.execute("""
                    INSERT INTO channels (
                        channel_id, title, description,
                        published_at, thumbnail, thumbnail_width, thumbnail_height,
                        view_count, subscriber_count, video_count,
                        inserted_at, updated_at
                    ) 
                    VALUES (
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?
                    )
                    """, (
                        channel_id, title, description,
                        published_at, thumbnail, thumbnail_width, thumbnail_height,
                        view_count, subscriber_count, video_count,
                        inserted_at, inserted_at
                    )
                )

                self.con.commit()
        