from datetime import datetime

from pandas.plotting import table
from sqlmodel import SQLModel, Field, Relationship

# Base Model
class BaseModel(SQLModel):
    inserted_at: datetime = Field(default=datetime.now())
    updated_at: datetime | None = Field(default=None)

# Code tables
class I18RegionCode(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True)
    name: str

class I18LanguageCode(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True)
    name: str

class VideoCategoryCode(BaseModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    channel_id: str

# Data tables
class SearchContent(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    query: str = Field(nullable=False, index=True)
    sort: str = Field(nullable=False, index=True)
    category_id: str = Field(nullable=False, index=True)
    country: str = Field(nullable=False, index=True)
    video_duration: str = Field(nullable=False, index=True)
    published_at: datetime = Field(nullable=False, index=True)
    kind: str | None = Field(default=None)
    channel_id: str = Field(nullable=False)
    channel_title: str = Field()
    video_id: str = Field(nullable=False)
    video_title: str = Field()
    video_description: str = Field()
    thumbnail: str = Field()
    thumbnail_width: int = Field()
    thumbnail_height: int = Field()


class Channel(BaseModel, table=True):
    channel_id: str = Field(primary_key=True)
    title: str = Field()
    description: str = Field()
    published_at: datetime = Field()
    thumbnail: str = Field()
    thumbnail_width: str = Field()
    thumbnail_height: str = Field()

    videos: list["Video"] = Relationship(back_populates="channel")
    statistics: list["ChannelStatistic"] = Relationship(back_populates="channel")


class ChannelStatistic(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    channel_id: str = Field(foreign_key="channel.channel_id")
    view_count: int = Field()
    subscriber_count: int = Field()
    video_count: int = Field()

    channel: Channel = Relationship(back_populates="statistics")

class Video(BaseModel, table=True):
    video_id: str = Field(nullable=False, primary_key=True)
    channel_id: str = Field(nullable=False, index=True, foreign_key="channel.channel_id")

    kind: str = Field()
    title: str = Field()
    description: str = Field()
    published_at: datetime = Field()
    thumbnail: str = Field()
    thumbnail_width: str = Field()
    thumbnail_height: str = Field()

    channel: Channel = Relationship(back_populates="videos")
    statistics: list["VideoStatistic"] = Relationship(back_populates="video")

class VideoStatistic(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    video_id: str = Field(foreign_key="video.video_id")

    view_count: int = Field()
    like_count: int = Field()
    favorite_count: int = Field()
    comment_count: int = Field()

    video: Video = Relationship(back_populates="statistics")
