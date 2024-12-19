# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class SearchItem(scrapy.Item):
    query = scrapy.Field()
    sort = scrapy.Field()
    category_id = scrapy.Field()
    video_duration = scrapy.Field()
    country = scrapy.Field()
    video_id = scrapy.Field()
    channel_id = scrapy.Field()
    kind = scrapy.Field()
    video_title = scrapy.Field()
    channel_title = scrapy.Field()
    video_description = scrapy.Field()
    published_at = scrapy.Field()
    thumbnail = scrapy.Field()
    thumbnail_width = scrapy.Field()
    thumbnail_height = scrapy.Field()

class VideoItem(scrapy.Item):
    video_id = scrapy.Field()
    channel_id = scrapy.Field()
    kind = scrapy.Field()
    title = scrapy.Field()
    channel_title = scrapy.Field()
    description = scrapy.Field()
    published_at = scrapy.Field()
    thumbnail = scrapy.Field()
    thumbnail_width = scrapy.Field()
    thumbnail_height = scrapy.Field()
    view_count = scrapy.Field()
    like_count = scrapy.Field()
    favorite_count = scrapy.Field()
    comment_count = scrapy.Field()

class ChannelItem(scrapy.Item):
    channel_id = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    published_at = scrapy.Field()
    country = scrapy.Field()
    thumbnail = scrapy.Field()
    thumbnail_width = scrapy.Field()
    thumbnail_height = scrapy.Field()
    view_count = scrapy.Field()
    subscriber_count = scrapy.Field()
    video_count = scrapy.Field()

class VideoCategoryItem(scrapy.Item):
    id = scrapy.Field()
    title = scrapy.Field()
    create_channel_id = scrapy.Field()
    assignable = scrapy.Field()
    created_at = scrapy.Field()
    updated_at = scrapy.Field()

