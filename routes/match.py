from flask import Blueprint, request
from models import db, Match, Tournament, User
import random

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
    q = q.filter(Match.is_private == True)
    pagination = q.paginate(page, per_page, max_per_page)  # Paginate result
    return_matches = []
    for match in pagination.items:
        return_matches.append(match.short())
    return return_matches


@match_blueprint.route('/matches', methods=['POST'])
def create_match():
    data = request.json
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
    if 'is_private' in data:
        match.is_private = data['is_private']
    if 'tournament_id' in data:
        tournament = db.session.query(Tournament).filters((Tournament.id == data['tournament_id']) & (Tournament.creator_id == user.id))
    match.insert()
    pass


@match_blueprint.route('/matches/<int:match_id>')
def get_match(match_id):
    pass


@match_blueprint.route('/matches/<int:match_id>', methods=['PATCH'])
def patch_match(match_id):
    pass


@match_blueprint.route('/matches/<int:match_id>', methods=['DELETE'])
def delete_match(match_id):
    pass


def generate_uuid(length):
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    return ''.join(random.choices(chars, k=length))
