from flask import Blueprint, request, jsonify
from models import db, Tournament, User, Game
import random
import auth
import errors

tournament_blueprint = Blueprint('tournament', __name__)


@tournament_blueprint.route('/tournaments')
def get_games():
    # Get pagination data
    max_per_page = 100
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('perPage', 50, type=int)
    q = db.session.query(Tournament)
    # Get filter term
    search_term = request.args.get('searchTerm', None, str)
    if search_term:
        q = q.filter((Tournament.name.ilike('%{}%'.format(search_term))))  # Filter by term
    q = q.order_by(Tournament.name.asc())
    pagination = q.paginate(page, per_page, max_per_page)  # Paginate result
    return_tournaments = []
    for tournament in pagination.items:
        return_tournaments.append(tournament.short())
    # Return data and pagination info
    return_data = {
        'tournaments': return_tournaments,
        'total_tournaments': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }
    return jsonify(return_data)


@tournament_blueprint.route('/tournaments', methods=['POST'])
@auth.requires_auth('create:tournament')
def create_tournament(payload):
    data = request.json

    # Prepare game
    game = Game.query.filter(Game.id == data['gameId']).first()
    if not game:
        game = Game.query.filter(Game.name.ilike(data['gameName'].strip())).first()
    if not game:
        game = Game(name=data['gameName'])
        db.session.add(game)
        db.session.flush()

    tournament = Tournament(name=data)
    # Generate the UUID
    uuid_len = 6
    tries = 0
    max_tries = 10
    tournament_found = True
    uuid = ''
    while tournament_found:
        if tries >= max_tries:
            tries = 0
            uuid_len += 1
        tries += 1
        uuid = generate_uuid(uuid_len)
        tournament_found = db.session.query(Tournament).filter(tournament.uuid == uuid).first()
    tournament.uuid = uuid
    tournament.name = data['name']
    tournament.max_participants = data['maxParticipants']
    if 'startDate' in data:
        tournament.start_date = data['startDate']
    if 'startDateTz' in data:
        tournament.start_date_tz = data['startDateTz']
    tournament.game_id = game.id
    user = auth.get_logged_user()
    tournament.creator_id = user.id
    db.session.add(tournament)
    db.session.flush()
    db.session.commit()
    return jsonify(tournament.long()), 201


@auth.requires_auth('delete:tournament')
@tournament_blueprint.route('/tournaments/<int:tournament_id>', methods=['DELETE'])
def delete_tournament(tournament_id):
    tournament = db.session.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        return errors.not_found_error('Tournament not found')
    logged_user = auth.get_logged_user()
    if tournament.creator_id == logged_user.id:
        tournament.delete()
        return '', 204
    errors.forbidden_error('You can\'t delete a not your tournament')


@auth.requires_auth('delete:any-tournament')
@tournament_blueprint.route('/tournaments/<int:tournament_id>', methods=['DELETE'])
def delete_any_tournament(tournament_id):
    tournament = db.session.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        return errors.not_found_error('Tournament not found')
    tournament.delete()
    return '', 204


def generate_uuid(length):
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    return 't' + ''.join(random.choices(chars, k=length))
