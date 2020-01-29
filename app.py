import os
from flask import Flask
from flask_cors import CORS
from models import setup_db
import routes

def create_app(test_config=None):

    app = Flask(__name__)
    setup_db(app, os.environ['DATABASE_URL'])
    CORS(app)
    app.register_blueprint(routes.match_blueprint)
    app.register_blueprint(routes.tournament_blueprint)

    @app.route('/')
    def get_greeting():
        greeting = "Hello"
        return greeting

    return app

app = create_app()

if __name__ == '__main__':
    app.run()