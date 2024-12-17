# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3
import datetime

DB_FILE_PATH = "./data/youtube.db"

class SearchPipeline:
    def __init__(self):
        # Create/Connect to database
        self.con = sqlite3.connect(DB_FILE_PATH)

        self.cur = self.con.cursor()

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS search_contents(
            id INTEGER PRIMARY KEY,
            query TEXT NOT NULL,
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
        # self.con.commit()

    def process_item(self, item, spider):
        spider.logger.debug(item)

        search_query = """
           SELECT * FROM search_contents WHERE video_id = ? and channel_id = ?
        """

        self.cur.execute(search_query, (item['video_id'], item['channel_id'],))
        result = self.cur.fetchone()

        if result:
            spider.logger.warn(f"Content Data already in database: channel_id[{item['channel_id']}], video_id[{item['video_id']}]")
        else:
            published_at = datetime.datetime.strptime(item['published_at'], '%Y-%m-%dT%H:%M:%SZ')
            inserted_at = datetime.datetime.now()
            self.cur.execute("""
                INSERT INTO search_contents (
                    query, country, video_duration, published_at, kind,
                    channel_id, channel_title, video_id, video_title, video_description,
                    thumbnail, thumbnail_width, thumbnail_height,
                    inserted_at, updated_at)
                VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?
                )
            """, (
                    item['query'], item['country'], item['video_duration'], published_at, item['kind'],
                    item['channel_id'], item['channel_title'], item['video_id'], item['video_title'], item['video_description'],
                    item['thumbnail'], item['thumbnail_width'], item['thumbnail_height'],
                    inserted_at, inserted_at
                )
            )
            self.con.commit()
        return item
