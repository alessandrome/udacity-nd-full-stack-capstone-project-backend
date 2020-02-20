from flask import Blueprint, request, jsonify
from models import db, Match, Tournament, User, Game
import random
import auth

match_blueprint = Blueprint('match', __name__)


@match_blueprint.route('/matches')
def get_matches():
    max_per_page = 50
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('perPage', 20, type=int)
    q = db.session.query(Match)
    search_term = request.args.get('searchTerm', None, str)
    if search_term:
        q = q.filter((Match.name.ilike('%{}%'.format(search_term)))
                     | (Match.game.name.ilike('%{}%'.format(search_term))))  # Filter by term
    # Retrieve logged user and filter by private matches and by user owned matches
    logged_user =auth.get_logged_user()
    if logged_user:
        q = q.filter((Match.is_private == False) | (Match.creator_id == logged_user.id))
    else:
        q = q.filter((Match.is_private == False))
    pagination = q.paginate(page, per_page, max_per_page)  # Paginate result
    return_matches = []
    for match in pagination.items:
        return_matches.append(match.short())
    return_data = {
        'matches': return_matches,
        'total_matches': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }
    return jsonify(return_data)


@match_blueprint.route('/matches', methods=['POST'])
@auth.requires_auth('create:match')
def create_match(payload):
    data = request.json

    # Prepare game
    game = Game.query.filter(Game.id == data['gameId']).first()
    if not game:
        game = Game.query.filter(Game.name.ilike(data['gameName'].strip())).first()
    if not game:
        game = Game(name=data['gameName'])
        db.session.add(game)

    match = Match(name=data)
    user = db.session.query(User).first()  # TODO: implement a get_user method
    uuid_len = 6
    tries = 0
    max_tries = 10
    match_found = True
    uuid = ''
    while (match_found):
        if tries >= max_tries:
            tries = 0
            uuid_len += 1
        tries += 1
        uuid = generate_uuid(uuid_len)
        match_found = db.session.query(Match).filter(Match.uuid == uuid).first()
    match.uuid = uuid
    match.name = data['name']
    match.max_participants = data['maxParticipants'] if 'maxParticipants' in data else 2
    match.game_id = game.id
    if 'isPrivate' in data:
        match.is_private = data['isPrivate']
    else:
        match.is_private = False
    user = auth.get_logged_user()
    match.creator_id = user.id
    user.matches.append(match)
    db.session.add(match)
    db.session.commit()
    return jsonify(match.long()), 201


@match_blueprint.route('/matches/<string:match_uuid>')
def get_match(match_uuid):
    match = db.session.query(Match).filter(Match.uuid == match_uuid).first()
    if not match:
        return {'error': 'Match not found'}, 404
    return jsonify(match.long())


@match_blueprint.route('/matches/<int:match_id>', methods=['PATCH'])
def patch_match(match_id):
    pass


@match_blueprint.route('/matches/<int:match_id>', methods=['DELETE'])
def delete_match(match_id):
    match = db.session.query(Match).filter(Match.id == match_id).first()
    if not match:
        return {'error': 'Match not found'}, 404
    match.delete()
    return '', 204


def generate_uuid(length):
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    return 'm' + ''.join(random.choices(chars, k=length))
