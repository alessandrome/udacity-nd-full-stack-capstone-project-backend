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

    def long(self):
        raise NotImplementedError

    def short(self):
        raise NotImplementedError


class User(ModelAction):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    match_participations = db.relationship('MatchParticipants', backref='user')
    matches = db.relationship('Match', secondary='match_participants', backref=db.backref('participants', cascade="all, delete-orphan", single_parent=True))
    tournament_participations = db.relationship('TournamentParticipants', backref='user')
    tournaments = db.relationship('Tournament', secondary='tournament_participants', backref=db.backref('participants', cascade="all, delete-orphan", single_parent=True))

    def get_user(self, auth0_id=None):
        if not auth0_id:
            pass

    def base_info(self):
        oauth_accounts = []
        for oauth in self.oauth_accounts:
            oauth_accounts.append(oauth.oauth_id)
        return {
            'id': self.id,
            'name': self.name,
            'oauth_id_list': oauth_accounts,
        }

    def short(self):
        return {
            'id': self.id,
            'name': self.name,
        }

    def long(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class UserAccount(ModelAction):
    __tablename__ = 'user_accounts'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    oauth_id = db.Column(db.String(255), primary_key=True)
    user = db.relationship('User', backref='oauth_accounts')


class Game(ModelAction):
    __tablename__ = 'games'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String)

    def short(self):
        return {
            'id': self.id,
            'name': self.name
        }

    def long(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Match(ModelAction):
    __tablename__ = 'matches'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String)
    uuid = Column(db.String(64), unique=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    is_private = db.Column(db.Boolean, default=False)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=True)
    max_participants = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(), default=datetime.now)
    updated_at = db.Column(db.DateTime(), default=datetime.now, onupdate=datetime.now)
    creator = db.relationship('User', backref='created_matches')
    match_participations = db.relationship('MatchParticipants', backref='match')
    # users = db.relationship('User', backref=db.backref('matches', cascade="all, delete-orphan"))
    game = db.relationship('Game', backref='matches')

    def short(self):
        game = self.game.short() if self.game else None
        participants = []
        for participant in self.participants:
            participants.append(participant.short())
        match = {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'game_id': self.game_id,
            'game': game,
            'max_participants': self.max_participants,
            'participants': participants,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
        return match

    def long(self):
        tournament = None
        if self.tournament:
            tournament = {
                'tournament_id': self.tournament.id,
                'tournament_uuid': self.tournament.uuid,
                'tournament_name': self.tournament.name,
            }
        game = self.game
        if game:
            game = game.short()
        creator = self.creator
        if creator:
            creator.short()
        participants = []
        for participant in self.participants:
            participants.append(participant.short())

        match = {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'creator_id': self.creator_id,
            'game_id': self.game_id,
            'game': game,
            'max_participants': self.max_participants,
            'tournament': tournament,
            'participants': participants,
            'is_private': self.is_private,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        return match

class Tournament(ModelAction):
    __tablename__ = 'tournaments'
    id = Column(db.Integer, primary_key=True)
    name = Column(db.String)
    uuid = Column(db.String(64), unique=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    max_participants = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    start_date_tz = db.Column(db.String(127), nullable=True, default='+00:00')
    creator = db.relationship('User', backref='created_tournaments')
    tournament_participations = db.relationship('TournamentParticipants', backref='tournament')
    users = db.relationship('User', backref=db.backref('users', cascade="all, delete-orphan"))
    matches = db.relationship('Match', backref='tournament')
    game = db.relationship('Game', backref='tournaments')

    def short(self):
        game = self.game.short() if self.game else None
        participants = []
        for participant in self.participants:
            participants.append(participant.short())
        match = {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'game_id': self.game_id,
            'game': game,
            'creator_id': self.creator_id,
            'max_participants': self.max_participants,
            'participants': participants,
            'start_date': self.start_date,
            'start_date_tz': self.start_date_tz,
        }
        return match

    def long(self):
        matches = []
        for match in self.matches:
            matches.append(match.short())
        game = self.game
        if game:
            game = game.short()
        creator = self.creator
        if creator:
            creator.short()
        participants = []
        for participant in self.participants:
            participants.append(participant.short())

        match = {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'creator_id': self.creator_id,
            'game_id': self.game_id,
            'game': game,
            'max_participants': self.max_participants,
            'matches': matches,
            'participants': participants,
            'start_date': self.start_date,
            'start_date_tz': self.start_date_tz
        }
        return match


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
