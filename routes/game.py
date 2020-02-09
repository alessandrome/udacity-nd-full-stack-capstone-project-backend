from flask import Blueprint, request, jsonify, redirect, Response
from models import db, Match, Tournament, User, Game
import random

game_blueprint = Blueprint('game', __name__)


@game_blueprint.route('/games')
def get_games():
    max_per_page = 100
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('perPage', 50, type=int)
    q = db.session.query(Game)
    search_term = request.args.get('searchTerm', None, str)
    if search_term:
        q = q.filter((Game.name.ilike('%{}%'.format(search_term))))  # Filter by term
    pagination = q.paginate(page, per_page, max_per_page)  # Paginate result
    return_games = []
    for game in pagination.items:
        return_games.append(game.short())
    return_data = {
        'games': return_games,
        'total_games': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }
    return jsonify(return_data)


@game_blueprint.route('/games', methods=['POST'])
def create_game():
    data = request.json
    # TODO: check for name field existence + string not empty
    game = db.session.query(Game).filter(Game.name.ilike(data['name'].strip())).first()
    if game:
        resp = jsonify(game.long())
        resp.status_code = 303
        resp.headers['Location'] = '/games/{}'.format(game.id)
        return resp
    game = Game(name=data['name'])
    game.insert()
    return jsonify(game.long()), 201


@game_blueprint.route('/games/<int:game_id>')
def get_game(game_id):
    game = db.session.query(Game).filter(Game.id == game_id).first()
    if not game:
        return {'error': 'Game not found'}, 404
    return jsonify(game.long())


@game_blueprint.route('/games/<int:game_id>', methods=['PATCH'])
def patch_game(game_id):
    game = db.session.query(Game).filter(Game.id == game_id).first()
    if not game:
        return {'error': 'Game not found'}, 404
    data = request.json
    if 'name' in data:
        game.name = data['name']
    db.session.commit()
    return jsonify(game.long())


@game_blueprint.route('/games/<int:game_id>', methods=['DELETE'])
def delete_game(game_id):
    game = db.session.query(Game).filter(Game.id == game_id).first()
    if not game:
        return {'error': 'Game not found'}, 404
    game.delete()
    return '', 204


def generate_uuid(length):
    """
    Generate a uuid starting with 'm'
    :param length: Length of UUID plus a starting 'm'
    :return string: A string starting with 'm' plus length - 1 random chars (Base62)
    """
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    return 'm' + ''.join(random.choices(chars, k=length - 1))
