import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, setup_db
import routes

def create_app(test_config=None):

    app = Flask(__name__)
    setup_db(app, os.environ['DATABASE_URL'])
    migrate = Migrate(app, db)
    CORS(app)
    app.register_blueprint(routes.game_blueprint)
    app.register_blueprint(routes.match_blueprint)
    app.register_blueprint(routes.tournament_blueprint)

    @app.after_request
    def after_request(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response

    @app.route('/')
    def get_greeting():
        greeting = "Hello"
        return greeting

    return app

app = create_app()

if __name__ == '__main__':
    app.run()