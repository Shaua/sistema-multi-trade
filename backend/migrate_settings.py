import os
from dotenv import load_dotenv
load_dotenv()

from app.database import engine
from app.models import SystemSettings

print("Dropping SystemSettings table...")
SystemSettings.__table__.drop(engine, checkfirst=True)

print("Creating SystemSettings table...")
SystemSettings.__table__.create(engine)

print("Done!")
