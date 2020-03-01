from flask import Blueprint, request, jsonify
from models import db, Match, Tournament, User, Game, MatchParticipants
import random
import auth
import errors

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
        return errors.not_found_error('Match not found')
    return jsonify(match.long())


@match_blueprint.route('/matches/<int:match_id>', methods=['PATCH'])
@auth.requires_auth()
def patch_match(payload, match_id):
    data = request.json
    if not 'action' in data:
        return errors.bad_request_error('Passed data must contain "action" value')
    action = data['action']
    # Get Match
    match = db.session.query(Match).filter(Match.id == match_id).first()
    if not match:
        return errors.not_found_error('Match not found')

    logged_user = auth.get_logged_user()
    if action == 'join':
        if len(match.participants) < match.max_participants:
            for participant in match.participants:
                if participant.id == logged_user.id:
                    return errors.bad_request_error('You can\'t join an already joined match')
            match.participants.append(logged_user)
            match.update()
            return '', 204
        else:
            return errors.bad_request_error('You can\'t join on a full match')
    elif action == 'disjoin':
        MatchParticipants.query.filter((MatchParticipants.match_id == match_id) & (MatchParticipants.user_id == logged_user.id)).delete()
        db.session.commit()
        return '', 204
    elif action == 'edit':
        if match.creator_id != logged_user.id:
            return errors.forbidden_error('You can edit only you\'re matches')
        if 'maxParticipants' in data:
            match.max_participants = data['maxParticipants']
        if 'name' in data:
            match.name = data['name']
        if 'isPrivate' in data:
            match.is_private = data['isPrivate']
        if 'join' in data:
            for user_id in data['join']:
                user = User.query.filter(User.id == user_id).first()
                if user:
                    match.participants.append(user)
        if 'remove' in data:
            match.participants.filter(User.id.in_(data['remove'])).clear()
            MatchParticipants.query.filter(
                (MatchParticipants.match_id == match_id) & (MatchParticipants.user_id.in_(data['remove']))).delete()
        if 'gameId' in data:
            print('gameId is', data['gameId'])
            if data['gameId'] is None:
                match.game_id = None
            else:
                game = Game.query.filter(Game.id == data['gameId']).first()
                if not game:
                    game = Game.query.filter(Game.name.ilike(data['gameName'].strip())).first()
                    if not game:
                        if 'gameName' in data:
                            game = Game(name=data['gameName'])
                            db.session.add(game)
                            db.session.flush()
                            match.game_id = game.id
                    else:
                        match.game_id = game.id
                else:
                    match.game_id = game.id
        db.session.commit()
        return jsonify(match.long())
    return errors.bad_request_error('"{}" action is not supported'.format(action))


@auth.requires_auth('delete:match')
@match_blueprint.route('/matches/<int:match_id>', methods=['DELETE'])
def delete_match(match_id):
    match = db.session.query(Match).filter(Match.id == match_id).first()
    if not match:
        return errors.not_found_error('Match not found')
    logged_user = auth.get_logged_user()
    if match.creator_id != logged_user.id:
        return errors.forbidden_error('You can\'t delete a not your own match')
    match.delete()
    return '', 204


@auth.requires_auth('delete:any-match')
@match_blueprint.route('/matches/<int:match_id>', methods=['DELETE'])
def delete_any_match(match_id):
    match = db.session.query(Match).filter(Match.id == match_id).first()
    if not match:
        return errors.not_found_error('Match not found')
    match.delete()
    return '', 204


@match_blueprint.route('/matches/<int:match_id>/users')
def match_users(match_id):
    match = db.session.query(Match).filter(Match.id == match_id).first()
    if not match:
        return errors.not_found_error('Match not found')
    max_per_page = 50
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('perPage', 20, type=int)
    q = db.session.query(User)
    search_term = request.args.get('searchTerm', None, str)
    if search_term:
        q = q.filter((User.name.ilike('%{}%'.format(search_term))))  # Filter by term
    user_joined = request.args.get('joined', 1, int)
    if user_joined:
        q = q.filter(User.matches.any(Match.id == match_id))
    else:
        q = q.filter(~ (User.matches.any(Match.id == match_id)))
    pagination = q.paginate(page, per_page, max_per_page)  # Paginate result
    return_users = []
    for user in pagination.items:
        return_users.append(user.short())
    return_data = {
        'users': return_users,
        'total_users': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }
    return jsonify(return_data)


def generate_uuid(length):
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    return 'm' + ''.join(random.choices(chars, k=length))
