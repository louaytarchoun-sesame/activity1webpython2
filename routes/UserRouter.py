from flask import Blueprint, jsonify, request
from extensions import db
from models.User import User

UserRouter = Blueprint('UserRouter', __name__, url_prefix='/users')

@UserRouter.route('/add', methods=['POST'])
def add_user():
    data = request.get_json()
    
    user = User(
        username = data['username'],
        email = data['email'],
        password = data['password']
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message' : 'Utilisateur ajouté avec success',
        'username' : user.username,
        'email' : user.email
    }) , 201