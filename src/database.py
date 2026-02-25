from peewee import *
import datetime
import os

from playhouse.sqliteq import SqliteQueueDatabase

# Database Path
DB_PATH = os.path.join(os.path.dirname(__file__), "content_factory.db")

# Use QueueDatabase for absolute thread safety across QThreads and ThreadPools
db = SqliteQueueDatabase(DB_PATH, autostart=True, queue_max_size=64, results_timeout=10.0)

class BaseModel(Model):
    class Meta:
        database = db

class Content(BaseModel):
    """Represents a primary piece of content (Scene)"""
    source_path = CharField(unique=True)
    file_hash = CharField(index=True, null=True)
    file_size = BigIntegerField()
    
    # Scene metadata
    scene_name = CharField(null=True)
    scene_number = IntegerField(null=True)
    content_date = DateField(null=True)
    content_type = CharField(null=True)  # PPV, TRAILER, STREAMVOD
    
    # v2.0: Category & Organization
    content_category = CharField(default="HQ PPV")  # HQ PPV, SEMIPPV, STREAMVOD
    video_aspect_ratio = CharField(null=True)       # 16:9, 9:16
    
    # v2.0: Linked Assets
    trailer_path = CharField(null=True)
    trailer_aspect_ratio = CharField(null=True)
    thumbnail_path = CharField(null=True)
    thumbnail_aspect_ratio = CharField(null=True)
    
    # v2.0: Video Metadata
    duration_seconds = IntegerField(null=True)  # Auto-extracted via ffprobe
    price = IntegerField(default=50)            # In dollars
    
    # v2.0: AI-Generated Content
    ai_description = TextField(null=True)
    ai_tags = TextField(null=True)  # Comma-separated
    sensor_log_raw = TextField(null=True) # Factual pixel-level log
    intensity_score = IntegerField(null=True) # 1-10 scale
    
    # Status
    status = CharField(default="pending")  # pending, processing, completed, failed
    error_log = TextField(null=True)
    
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

class Asset(BaseModel):
    """Represents secondary assets (Thumbnails, Trailers, FYP clips, Metadata)"""
    content = ForeignKeyField(Content, backref='assets', on_delete='CASCADE')
    asset_type = CharField() # thumb, trailer, fyp, meta
    local_path = CharField()
    remote_path = CharField(null=True)
    status = CharField(default="pending")
    
    created_at = DateTimeField(default=datetime.datetime.now)

def init_db():
    db.connect()
    db.create_tables([Content, Asset])
    print(f"Initialized Database at {DB_PATH}")

if __name__ == "__main__":
    init_db()
