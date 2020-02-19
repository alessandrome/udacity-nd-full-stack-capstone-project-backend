import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, setup_db
import routes
import auth

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
        response.headers['Access-Control-Allow-Methods'] = '*'
        return response

    @app.route('/')
    def get_greeting():
        greeting = "Wow! This API server works ;)"
        return greeting

    @app.route('/user-auth0')
    def get_user_info():
        user = auth.get_logged_user()
        if user:
            user = user.base_info()
        return jsonify(user)

    return app

app = create_app()

if __name__ == '__main__':
    app.run()