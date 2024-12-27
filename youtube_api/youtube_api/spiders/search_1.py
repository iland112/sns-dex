import json
import scrapy
import sqlite3
import datetime
import requests
from urllib.parse import urlencode
from scrapy.utils.project import get_project_settings
from youtube_api.items import SearchItem, VideoItem, ChannelItem

DB_FILE_PATH = "./data/youtube1.db"

# API_KEY = "AIzaSyAlTmAytStJLjhENxoW0ctNP7qdYvKAZbQ"

class Search1Spider(scrapy.Spider):
    name = "search1"
    # allowed_domains = ["www.googleapis.com"]
    # start_urls = ["https://www.googleapis.com/youtube/v3/search"]
    # install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")

    def __init__(self, query, order="relevance", category="ALL", country="ALL", language="ALL", duration='any', **kwargs):
        super().__init__(**kwargs)
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

    def start_requests(self):
        print(self.query, self.country)
        params = {
            'key': get_project_settings().get("YOUTUBE_API_KEY"),
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
        yield scrapy.Request(url + urlencode(params))
        # if self.language != "ALL":
        #     yield scrapy.Request(url + urlencode(params), headers={"Accept-Language": self.language})
        # else:
        #     yield scrapy.Request(url + urlencode(params))

    def parse(self, response):
        print("Headers:", response.request.headers)
        if response.status != 200:
            print("Error: ", response.status, response.body)
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
        self.log(f"pages: {pages}")

        items = r['items']
        self.log(f"item count: {len(items)}")
        self.log(f"previous page token: {self.prev_page_token}, next page token: {self.next_page_token}")
        for item in items:
            self.save_search_content_data(item)
                        
            # load video data    
            params = {
                'key': get_project_settings().get("YOUTUBE_API_KEY"),
                'part': 'snippet,contentDetails,statistics',
                'id': item['id']['videoId'],
            }
            video_api_url = f"https://youtube.googleapis.com/youtube/v3/videos?"
            response = requests.get(video_api_url + urlencode(params))
            self.parse_video(response)
            # load channel data
            
            params = {
                'key': get_project_settings().get("YOUTUBE_API_KEY"),
                'part': 'snippet,contentDetails,statistics',
                'id': item['snippet']['channelId'],
            }
            channel_api_url = f"https://youtube.googleapis.com/youtube/v3/channels?"
            response = requests.get(channel_api_url + urlencode(params))
            self.parse_channel(response)

        # if self.next_page_token:
        #     for i in range(pages):
        #         self.log(f"Call {i+1}/{pages}, next_page_token: {self.next_page_token}\n")
        #         params = {
        #             'key': get_project_settings().get("YOUTUBE_API_KEY"),
        #             'part': 'snippet',
        #             'type': 'video',
        #             'order': 'viewCount',
        #             'maxResults': '50',
        #             'q': self.query,
        #             'videoDuration': self.duration,
        #             'pageToken': self.next_page_token
        #         }
        #         if self.country and self.country != "ALL":
        #             params['regionCode'] = self.country
        #
        #         page_url = f"https://youtube.googleapis.com/youtube/v3/search?"
        #         yield scrapy.Request(page_url + urlencode(params),  callback=self.parse)

    def save_search_content_data(self, item):
        # print(item)
        searchItem = SearchItem()
        searchItem['query'] = self.query
        searchItem['sort'] = self.order
        searchItem['category_id'] = self.category
        searchItem['video_duration'] = self.duration
        searchItem['country'] = self.country
        searchItem['video_id'] = item['id']['videoId']
        searchItem['kind'] = item['id']['kind']
        searchItem['channel_id'] = item['snippet']['channelId']
        searchItem['video_title'] = item['snippet']['title']
        searchItem['channel_title'] = item['snippet']['channelTitle']
        searchItem['video_description'] = item['snippet']['description']
        searchItem['published_at'] = item['snippet']['publishedAt']
        searchItem['thumbnail'] = item['snippet']['thumbnails']['default']['url']
        searchItem['thumbnail_width'] = item['snippet']['thumbnails']['default']['width']
        searchItem['thumbnail_height'] = item['snippet']['thumbnails']['default']['height']
            
        search_query = """
            SELECT * FROM search_contents WHERE video_id = ? and channel_id = ?
        """

        self.cur.execute(search_query, (searchItem['video_id'], searchItem['channel_id'],))
        result = self.cur.fetchone()

        if result:
            self.log(f"Content Data already in database: channel_id[{item['channel_id']}], video_id[{item['video_id']}]")
        else:
            published_at = datetime.datetime.strptime(item['published_at'], '%Y-%m-%dT%H:%M:%SZ')
            inserted_at = datetime.datetime.now()
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
                    searchItem['query'], searchItem['sort'], searchItem['category_id'], searchItem['country'], searchItem['video_duration'], published_at, searchItem['kind'],
                    searchItem['channel_id'], searchItem['channel_title'], searchItem['video_id'], searchItem['video_title'], searchItem['video_description'],
                    searchItem['thumbnail'], searchItem['thumbnail_width'], searchItem['thumbnail_height'],
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
            # channelItem['country'] = item['snippet']['country']
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
