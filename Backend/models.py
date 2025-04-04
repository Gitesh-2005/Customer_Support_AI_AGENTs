from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TicketErrorLog(Base):
    __tablename__ = "ticket_error_logs"

    id = Column(Integer, primary_key=True, index=True)
    issue_text = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    error_message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
