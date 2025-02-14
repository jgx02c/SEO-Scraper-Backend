from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from db.database import Base
import datetime

class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    report_type = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    report_data = Column(JSON)

    user = relationship("User", back_populates="reports")
