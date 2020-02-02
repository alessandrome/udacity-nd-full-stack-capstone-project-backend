import os
from datetime import datetime
from sqlalchemy import Column
from flask_sqlalchemy import SQLAlchemy
import json


db = SQLAlchemy()


def setup_db(app, database_path):
    """
    setup_db(app)
        binds a flask application and a SQLAlchemy service
    """
    database_path = database_path or os.environ['DATABASE_URL']
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)


class ModelAction(db.Model):
    __abstract__ = True
    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class User(ModelAction):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    auth0_id = db.Column(db.String(64), unique=True)
    match_participations = db.relationship('MatchParticipants', backref='user')
    matches = db.relationship('Match', backref=db.backref('matches', cascade="all, delete-orphan"))
    tournament_participations = db.relationship('TournamentParticipants', backref='user')
    tournaments = db.relationship('Tournament', backref=db.backref('tournaments', cascade="all, delete-orphan"))


class Game(ModelAction):
    __tablename__ = 'games'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String)


class Match(ModelAction):
    __tablename__ = 'matches'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String)
    uuid = Column(db.String(64))
    creator_id = db.Column(db.Integer)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    is_private = db.Column(db.Boolean, default=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=True)
    max_participants = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(), default=datetime.now)
    updated_at = db.Column(db.DateTime(), default=datetime.now, onupdate=datetime.now)
    creator = db.relationship('User', backref='created_tournaments')
    match_participations = db.relationship('MatchParticipants', backref='match')
    users = db.relationship('User', backref=db.backref('users', cascade="all, delete-orphan"))

    def short(self):
        match = {
            'id': self.id,
            'name': self.name,
            'game': self.game,
            'max_participants': self.max_participants,
        }
        return match


class Tournament(ModelAction):
    __tablename__ = 'tournaments'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String)
    uuid = Column(db.String(64))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
    start_date = db.Column(db.DateTime, nullable=True)
    creator = db.relationship('User', backref='tournaments')
    tournament_participations = db.relationship('TournamentParticipants', backref='tournament')
    users = db.relationship('User', backref=db.backref('users', cascade="all, delete-orphan"))


class TournamentParticipants(ModelAction):
    __tablename__ = 'tournament_participants'
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    participate_date = db.Column(db.DateTime(), default=datetime.now)


class MatchParticipants(ModelAction):
    __tablename__ = 'match_participants'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    participate_date = db.Column(db.DateTime(), default=datetime.now)
