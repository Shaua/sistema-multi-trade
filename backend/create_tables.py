from app.database import engine
from app.models import Base
print("Creating tables...")
Base.metadata.create_all(engine)
print("Done!")
