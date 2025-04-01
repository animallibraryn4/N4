from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from database.database import Base

class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String, unique=True)
    name = Column(String)
    username = Column(String, nullable=True)
    added_by = Column(Integer)
    added_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String, unique=True)
    channel_id = Column(String)
    text = Column(Text)
    media = Column(String, nullable=True)
    media_type = Column(String, nullable=True)
    buttons = Column(JSON, default=[])
    created_at = Column(DateTime)
    created_by = Column(Integer)
    is_published = Column(Boolean, default=False)
