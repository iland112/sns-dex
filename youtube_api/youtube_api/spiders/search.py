import scrapy
import sqlite3
import datetime
import requests
from youtube_api.items import SearchItem, VideoItem, ChannelItem

# query = "roleal serum"
# country = "vn"

API_KEY = "AIzaSyAlTmAytStJLjhENxoW0ctNP7qdYvKAZbQ"

class SearchSpider(scrapy.Spider):
    name = "search"
    # allowed_domains = ["www.googleapis.com"]
    # start_urls = ["https://www.googleapis.com/youtube/v3/search"]

    def __init__(self, query=None, country=None, **kwargs):
        super().__init__(**kwargs)
        self.query = query
        self.country = country
        self.total_results = None
        self.results_per_page = None
        self.next_page_token = None
        self.prev_page_token = None
        self.con = sqlite3.connect('./data/youtube.db')

        self.cur = self.con.cursor()

    def start_requests(self):
        # print(self.query, self.country)
        url = f"https://youtube.googleapis.com/youtube/v3/search?part=snippet&type=video&order=viewCount&maxResults=50&q={self.query}&regionCode={self.country}&key={API_KEY}"
        yield scrapy.Request(url)

    def parse(self, response):
        r = response.json()
        self.country = r['regionCode']
        self.total_results = r['pageInfo']['totalResults']
        self.results_per_page = r['pageInfo']['resultsPerPage']
        self.next_page_token = r.get('nextPageToken', None)
        self.prev_page_token =  r.get('prevPageToke', None)

        pages = int(self.total_results / self.results_per_page)
        self.log(f"pages: {pages}")

        items = r['items']
        self.log(f"item count: {len(items)}")
        for item in items:
            self.log(f"previous page token: {self.prev_page_token}, next page token: {self.next_page_token}")
            # print(item)
            searchItem = SearchItem()
            searchItem['query'] = self.query
            searchItem['country'] = self.country
            searchItem['video_id'] = item['id']['videoId']
            video_api_url = f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={searchItem['video_id']}&key={API_KEY}"
            response = requests.get(video_api_url)
            self.parse_video(response)
            searchItem['channel_id'] = item['snippet']['channelId']
            channel_api_url = f"https://youtube.googleapis.com/youtube/v3/channels?part=snippet,contentDetails,statistics&id={searchItem['channel_id']}&key={API_KEY}"
            response = requests.get(channel_api_url)
            self.parse_channel(response)
            searchItem['kind'] = item['id']['kind']
            searchItem['video_title'] = item['snippet']['title']
            searchItem['channel_title'] = item['snippet']['channelTitle']
            searchItem['video_description'] = item['snippet']['description']
            searchItem['published_at'] = item['snippet']['publishedAt']
            searchItem['thumbnail'] = item['snippet']['thumbnails']['default']['url']
            searchItem['thumbnail_width'] = item['snippet']['thumbnails']['default']['width']
            searchItem['thumbnail_height'] = item['snippet']['thumbnails']['default']['height']
            yield searchItem

        # if self.next_page_token:
        #     for i in range(pages):
        #         self.log(f"Call {i+1}/{pages}, next_page_token: {self.next_page_token}\n")
        #         url = f"https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=50&q={self.query}&regionCode={self.country}&pageToken={self.next_page_token}&key={API_KEY}"
        #         yield scrapy.Request(url, callback=self.parse)

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
            videoItem = VideoItem()
            videoItem['video_id'] = item['id']
            videoItem['channel_id'] = item['snippet']['channelId']
            videoItem['kind'] = item['kind']
            videoItem['title'] = item['snippet']['title']
            videoItem['description'] = item['snippet']['description']
            videoItem['published_at'] = item['snippet']['publishedAt']
            videoItem['thumbnail'] = item['snippet']['thumbnails']['high']['url']
            videoItem['thumbnail_width'] = item['snippet']['thumbnails']['high']['width']
            videoItem['thumbnail_height'] = item['snippet']['thumbnails']['high']['height']
            statistics = item['statistics']
            videoItem['view_count'] = statistics.get('viewCount', 0)
            videoItem['like_count'] = statistics.get('likeCount', 0)
            videoItem['favorite_count'] = statistics.get('favoriteCount', 0)
            videoItem['comment_count'] = statistics.get('commentCount', 0)

            self.cur.execute("select * from videos where video_id = ?", (videoItem['video_id'],))
            result = self.cur.fetchone()

            if result:
                self.log(f"VideoID already in database: {videoItem['video_id']}")
            else:
                published_at = datetime.datetime.strptime(videoItem['published_at'], '%Y-%m-%dT%H:%M:%SZ')
                inserted_at = datetime.datetime.now()
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
                        videoItem['video_id'], videoItem['channel_id'], videoItem['kind'],
                        videoItem['title'], videoItem['description'], published_at,
                        videoItem['thumbnail'], videoItem['thumbnail_width'], videoItem['thumbnail_height'],
                        videoItem['view_count'], videoItem['like_count'], videoItem['favorite_count'], videoItem['comment_count'],
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
            channelItem = ChannelItem()
            channelItem['channel_id'] = item['id']
            channelItem['title'] = item['snippet']['title']
            channelItem['description'] = item['snippet']['description']
            channelItem['published_at'] = item['snippet']['publishedAt']
            channelItem['thumbnail'] = item['snippet']['thumbnails']['default']['url']
            channelItem['thumbnail_width'] = item['snippet']['thumbnails']['default']['width']
            channelItem['thumbnail_height'] = item['snippet']['thumbnails']['default']['height']
            channelItem['view_count'] = item['statistics']['viewCount']
            channelItem['subscriber_count'] = item['statistics']['subscriberCount']
            channelItem['video_count'] = item['statistics']['videoCount']

            self.cur.execute("select * from channels where channel_id = ?", (channelItem['channel_id'],))
            result = self.cur.fetchone()

            if result:
                self.log(f"Channel already in database: {channelItem['channel_id']}")
            else:
                published_at = channelItem['published_at']
                published_at_list = published_at.strip().split('.')
                print(f"published at: {published_at_list}")
                if len(published_at_list) == 1:
                    published_at = datetime.datetime.strptime(channelItem['published_at'], '%Y-%m-%dT%H:%M:%SZ')
                elif len(published_at_list) == 2:
                    published_at = datetime.datetime.strptime(channelItem['published_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                inserted_at = datetime.datetime.now()
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
                        channelItem['channel_id'], channelItem['title'], channelItem['description'],
                        published_at, channelItem['thumbnail'], channelItem['thumbnail_width'], channelItem['thumbnail_height'],
                        channelItem['view_count'], channelItem['subscriber_count'], channelItem['video_count'],
                        inserted_at, inserted_at
                    )
                )

                self.con.commit()
