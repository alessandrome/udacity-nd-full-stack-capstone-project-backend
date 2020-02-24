from flask import jsonify
from werkzeug.exceptions import NotFound


def bad_request_error(error='Bad request'):
    return jsonify({'success': False, 'error': 400, 'message': error}), 400


def unauthorized_error(error='Unauthorized'):
    if isinstance(error, NotFound):
        return jsonify({'success': False, 'error': 401, 'message': str(error)}), 401
    return jsonify({'success': False, 'error': 401, 'message': error}), 401


def forbidden_error(error='Forbidden'):
    if isinstance(error, NotFound):
        return jsonify({'success': False, 'error': 403, 'message': str(error)}), 403
    return jsonify({'success': False, 'error': 403, 'message': error}), 403


def not_found_error(error='Resource not found'):
    if isinstance(error, NotFound):
        return jsonify({'success': False, 'error': 404, 'message': str(error)}), 404
    return jsonify({'success': False, 'error': 404, 'message': error}), 404


def server_error(error='Server Error'):
    return jsonify({'success': False, 'error': 500, 'message': error}), 500
