import os
from datetime import datetime
from sqlalchemy import Column
from flask_sqlalchemy import SQLAlchemy
import json

database_path = os.environ['DATABASE_URL']

db = SQLAlchemy()


def setup_db(app, database_path):
    """
    setup_db(app)
        binds a flask application and a SQLAlchemy service
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    db.create_all()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    auth0_id = db.Column(unique=True)

class Game(db.Model):
    __tablename__ = 'games'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String)


class Match(db.Model):
    __tablename__ = 'matches'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String)
    uuid = Column(db.String(64))
    creator_id = db.Column(db.Integer)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=True)
    created_at = db.Column(db.DateTime(), default=datetime.now)
    updated_at = db.Column(db.DateTime(), default=datetime.now, onupdate=datetime.now)


class Tournament(db.Model):
    __tablename__ = 'tournaments'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String)
    uuid = Column(db.String(64))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
