from sqlalchemy import create_engine, Column, DateTime
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy.sql import func
from app.config import settings
from typing import Literal


class SoftDeleteQuery(Query):
    def __new__(cls, *args, **kwargs):
        # Automatically filter out soft-deleted records
        if args and hasattr(args[0], "__soft_delete__"):
            args = (args[0].__soft_delete__(*args),) + args[1:]
        return super().__new__(cls, *args, **kwargs)


@as_declarative()
class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    query_class = SoftDeleteQuery

    # Add a `deleted_at` column to all models
    deleted_at = Column(DateTime, nullable=True)

    @classmethod
    def __soft_delete__(cls, query):
        """Apply a default filter to exclude soft-deleted records."""
        return query.filter(cls.deleted_at == None)