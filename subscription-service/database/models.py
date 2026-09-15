from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    username = Column(String)
    email = Column(String)
    password = Column(String)
    role = Column(String)
    birthdate = Column(Date)
    registerdate = Column(Date)
    last_username_change = Column(DateTime)
    last_email_change = Column(DateTime)
    last_password_change = Column(DateTime)

    # Relaciones
    artist_profile = relationship("Artist", back_populates="user", uselist=False)
    subscriptions = relationship(
        "ArtistSubscription", back_populates="subscriber", cascade="all, delete-orphan"
    )


class Artist(Base):
    __tablename__ = "artists"
    __table_args__ = {"schema": "music_streaming"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("music_streaming.users.id"), unique=True, nullable=False
    )
    artist_name = Column(String, nullable=False, unique=True)
    bio = Column(Text)
    profile_pic = Column(String)
    social_links = Column(JSON)
    created_at = Column(Date)
    updated_at = Column(Date)

    # Relaciones
    user = relationship("User", back_populates="artist_profile")
    subscribers = relationship(
        "ArtistSubscription", back_populates="artist", cascade="all, delete-orphan"
    )


class ArtistSubscription(Base):
    __tablename__ = "artist_subscriptions"
    __table_args__ = {"schema": "music_streaming"}

    user_id = Column(
        Integer,
        ForeignKey("music_streaming.users.id"),
        primary_key=True,
        nullable=False,
    )
    artist_id = Column(
        Integer,
        ForeignKey("music_streaming.artists.id"),
        primary_key=True,
        nullable=False,
    )
    created_at = Column(Date)

    # Relaciones
    subscriber = relationship("User", back_populates="subscriptions")
    artist = relationship("Artist", back_populates="subscribers")
