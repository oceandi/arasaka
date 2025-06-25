from app import db, FiberAriza
import sqlalchemy

# Tablo sütunlarını listele
for column in FiberAriza.__table__.columns:
    print(f"{column.name}: {column.type}")