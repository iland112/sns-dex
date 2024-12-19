from peewee import *

sqliteDB = SqliteDatabase('./data/youtube1.db')

class BaseModel(Model):
    class Meta:
        database = sqliteDB

class RegionCode(BaseModel):
    code = CharField()
    name = CharField()

    class Meta:
        table_name = 'i18n_region_codes'

class VideoCategoryCode(BaseModel):
    code = CharField
    name = CharField
    channel_id = CharField

    class Meta:
        table_name = 'video_category_codes'

class SearchCondition(BaseModel):
    query = CharField()
    sort_type = CharField()
    video_duration = CharField()
    video_category = CharField()
    country = CharField()

    class Meta:
        table_name = 'search_conditions'