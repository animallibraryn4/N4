from sqlalchemy.orm import Session
from . import models

def get_channel(db: Session, channel_id: str):
    return db.query(models.Channel).filter(models.Channel.channel_id == channel_id).first()

def create_channel(db: Session, channel_data: dict):
    db_channel = models.Channel(**channel_data)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

def get_post(db: Session, post_id: str):
    return db.query(models.Post).filter(models.Post.post_id == post_id).first()

def create_post(db: Session, post_data: dict):
    db_post = models.Post(**post_data)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post
