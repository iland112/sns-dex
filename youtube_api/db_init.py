import datetime
import json
from urllib.parse import urlencode

import requests
from requests import Response
from sqlmodel import Session, select, SQLModel
from db import create_db_and_tables, engine
from models import I18RegionCode, I18LanguageCode, VideoCategoryCode, SearchContent, Channel, ChannelStatistic, Video, VideoStatistic

YOUTUBE_API_KEY = "AIzaSyAlTmAytStJLjhENxoW0ctNP7qdYvKAZbQ"

def is_code_exist(sql_model: SQLModel) -> bool:
    with Session(engine) as session:
        codes = session.exec(select(sql_model)).all()
        if len(codes) == 0:
            return False
        else:
            return True

def _insert_region_code_data():
    with Session(engine) as session:
        codes = session.exec(select(I18RegionCode)).all()
        if len(codes) == 0:
            params = {
                'key': YOUTUBE_API_KEY,
                'part': 'snippet',
            }
            url = f"https://www.googleapis.com/youtube/v3/i18nRegions?"
            response = requests.get(url, params)
            items = response.json()["items"]
            for item in items:
                snippet = item["snippet"]
                result = session.exec(
                    select(I18RegionCode)
                    .where(I18RegionCode.code == snippet["gl"])
                    .where(I18RegionCode.name == snippet["name"])
                ).first()
                if not result:
                    code = I18RegionCode(code=snippet["gl"], name=snippet["name"])
                    session.add(code)
                    session.commit()

def _insert_language_code_data():
    with Session(engine) as session:
        codes = session.exec(select(I18LanguageCode)).all()
        if len(codes) == 0:
            params = {
                'key': YOUTUBE_API_KEY,
                'part': 'snippet',
            }
            url = f"https://youtube.googleapis.com/youtube/v3/i18nLanguages?"
            response = requests.get(url, params)
            items = response.json()["items"]
            for item in items:
                snippet = item["snippet"]
                result = session.exec(
                    select(I18LanguageCode)
                    .where(I18LanguageCode.code == snippet["hl"])
                    .where(I18LanguageCode.name == snippet["name"])
                ).first()
                if not result:
                    code = I18LanguageCode(code=snippet["hl"], name=snippet["name"])
                    session.add(code)
                    session.commit()

def _insert_video_category_code_data():
    with Session(engine) as session:
        codes = session.exec(select(VideoCategoryCode)).all()
        if len(codes) == 0:
            params = {
                'key': YOUTUBE_API_KEY,
                'part': 'snippet',
                'regionCode': 'US'
            }
            url = f"https://www.googleapis.com/youtube/v3/videoCategories?"
            response = requests.get(url, params)
            items = response.json()["items"]
            for item in items:
                snippet = item["snippet"]
                result = session.exec(
                    select(VideoCategoryCode)
                    .where(VideoCategoryCode.id == item["id"])
                    .where(VideoCategoryCode.title == snippet["title"])
                ).first()
                if not result:
                    code = VideoCategoryCode(id=item["id"], title=snippet["title"], channel_id=snippet["channelId"])
                    session.add(code)
                    session.commit()

def init_db():
    create_db_and_tables()
    _insert_region_code_data()
    _insert_language_code_data()
    _insert_video_category_code_data()


def search_list(query, order="relevance", category="ALL", country="ALL", language="ALL", duration='any') -> list:
    params = {
        'key': YOUTUBE_API_KEY,
        'part': 'snippet',
        'type': 'video',
        'safeSearch': 'strict',
        'videoDuration': duration,
        'q': query,
        'maxResults': '10',
    }
    # optional parameters
    if order != "relevance":
        params['order'] = order

    if category and category != "ALL":
        params['videoCategoryId'] = category

    if country and country != "ALL":
        params['regionCode'] = country

    if language and language != "ALL":
        params['relevanceLanguage'] = language

    print("url_params: ", json.dumps(params, indent=2))
    url = f"https://youtube.googleapis.com/youtube/v3/search?"
    response = requests.get(url, params)
    print("Headers:", response.request.headers)
    if response.status_code != 200:
        print("Error: ", response.status_code, response.text)
        return None

    r = response.json()
    total_results = r['pageInfo']['totalResults']
    results_per_page = r['pageInfo']['resultsPerPage']
    next_page_token = r.get('nextPageToken', None)
    prev_page_token = r.get('prevPageToken', None)

    pages = int(total_results / results_per_page)
    print(f"pages: {pages}")

    items = r['items']
    print(f"item count: {len(items)}")

    search_contents = []
    with Session(engine) as session:
        for item in items:
            print(f"previous page token: {prev_page_token}, next page token: {next_page_token}")
            # print(item)
            published_at = datetime.datetime.strptime(item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
            search_content = SearchContent(
                query=query,
                sort=order,
                category_id=category,
                country=r['regionCode'],
                video_duration=duration,
                published_at=published_at,
                kind=item['id']['kind'],
                channel_id=item['snippet']['channelId'],
                channel_title=item['snippet']['channelTitle'],
                video_id=item['id']['videoId'],
                video_title=item['snippet']['title'],
                video_description=item['snippet']['description'],
                thumbnail=item['snippet']['thumbnails']['default']['url'],
                thumbnail_width=item['snippet']['thumbnails']['default']['width'],
                thumbnail_height=item['snippet']['thumbnails']['default']['height']
            )
            session.add(search_content)
            session.commit()
            session.refresh(search_content)
            print(search_content)
            search_contents.append(search_content)

            params = {
                'key': YOUTUBE_API_KEY,
                'part': 'snippet,contentDetails,statistics',
                'id': item['snippet']['channelId'],
            }
            channel_api_url = f"https://youtube.googleapis.com/youtube/v3/channels?"
            response = requests.get(channel_api_url + urlencode(params))
            parse_channel(response)

            params = {
                'key': YOUTUBE_API_KEY,
                'part': 'snippet,contentDetails,statistics',
                'id': item['id']['videoId'],
            }
            video_api_url = f"https://youtube.googleapis.com/youtube/v3/videos?"
            response = requests.get(video_api_url + urlencode(params))
            parse_video(response)

def parse_channel(response: Response)->None:
    items = response.json()['items']
    with Session(engine) as session:
        for item in items:
            published_at = item['snippet']['publishedAt']
            published_at_list = published_at.strip().split('.')
            print(f"published at: {published_at_list}")
            if len(published_at_list) == 1:
                published_at = datetime.datetime.strptime(item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
            elif len(published_at_list) == 2:
                published_at = datetime.datetime.strptime(item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%S.%fZ')

            channel = Channel(
                channel_id=item['id'],
                title=item['snippet']['title'],
                description=item['snippet']['description'],
                published_at=published_at,
                thumbnail=item['snippet']['thumbnails']['default']['url'],
                thumbnail_width=item['snippet']['thumbnails']['default']['width'],
                thumbnail_height=item['snippet']['thumbnails']['default']['height']
            )
            session.add(channel)
            session.commit()

            statistics = item['statistics']
            channel_statistic = ChannelStatistic(
                channel_id=item['id'],
                view_count=statistics.get('viewCount', 0),
                subscriber_count=statistics.get('subscriberCount', 0),
                video_count=statistics.get('videoCount', 0),
            )
            session.add(channel_statistic)
            session.commit()

def parse_video(response: Response)->None:
    items = response.json()['items']
    with Session(engine) as session:
        for item in items:
            published_at = datetime.datetime.strptime(item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
            video = Video(
                video_id=item['id'],
                channel_id=item['snippet']['channelId'],
                kind=item['kind'],
                title=item['snippet']['title'],
                description=item['snippet']['description'],
                published_at=published_at,
                thumbnail=item['snippet']['thumbnails']['high']['url'],
                thumbnail_width=item['snippet']['thumbnails']['high']['width'],
                thumbnail_height=item['snippet']['thumbnails']['high']['height']
            )
            session.add(video)
            session.commit()

            statistics = item['statistics']
            video_statistic = VideoStatistic(
                video_id=item['id'],
                view_count=statistics.get('viewCount', 0),
                like_count=statistics.get('likeCount', 0),
                favorite_count=statistics.get('favoriteCount', 0),
                comment_count=statistics.get('commentCount', 0)
            )
            session.add(video_statistic)
            session.commit()

if __name__ == "__main__":
    init_db()