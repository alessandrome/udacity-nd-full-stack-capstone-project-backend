from sqlalchemy import Column, String, create_engine, Integer
from flask_sqlalchemy import SQLAlchemy
import json

database_path = os.environ['DATABASE_URL']

db = SQLAlchemy()


def setup_db(app, database_path=database_path):
    """
    setup_db(app)
        binds a flask application and a SQLAlchemy service
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    db.create_all()


class Person(db.Model):
    """
    Person
    Have title and release year
    """
    __tablename__ = 'People'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    catchphrase = Column(String)

    def __init__(self, name, catchphrase=""):
        self.name = name
        self.catchphrase = catchphrase

    def format(self):
        return {
          'id': self.id,
          'name': self.name,
          'catchphrase': self.catchphrase}