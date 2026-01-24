from flask import Blueprint, jsonify, request
from chores.models import Chore, Completion, User
from chores.database import db


chore_v1 = Blueprint('chore_v1', __name__, url_prefix='/api/v1/chores')


@chore_v1.route('/', methods=['GET'])
def get_chores():
    chores = Chore.query.all()
    return jsonify([{"id": c.id, "task": c.task_name, "reward": c.reward_level} for c in chores])


@chore_v1.route('/', methods=['POST'])
def add_chore():
    data = request.get_json()

    # Validation
    if not data or 'task_name' not in data or 'reward_level' not in data:
        return jsonify({"error": "Missing task_name or reward_level"}), 400

    new_chore = Chore(
        task_name=data['task_name'],
        reward_level=float(data['reward_level'])
    )

    db.session.add(new_chore)
    db.session.commit()

    return jsonify({"message": "Chore created", "id": new_chore.id}), 201


@chore_v1.route('/complete', methods=['POST'])
def complete_chore():
    data = request.get_json()

    # Required: which user and which chore?
    user_id = data.get('user_id')
    chore_id = data.get('chore_id')

    if not user_id or not chore_id:
        return jsonify({"error": "user_id and chore_id required"}), 400

    # Verify user and chore exist
    user = User.query.get(user_id)
    chore = Chore.query.get(chore_id)

    if not user or not chore:
        return jsonify({"error": "User or Chore not found"}), 404

    # Create the completion record
    new_completion = Completion(
        user_id=user.id,
        chore_id=chore.id,
        payout_status='pending'  # Default status for new completions
    )

    db.session.add(new_completion)
    db.session.commit()

    return jsonify({
        "message": "Chore completion recorded",
        "user": user.name,
        "task": chore.task_name,
        "reward": chore.reward_level
    }), 201


@chore_v1.route('/<int:chore_id>', methods=['DELETE'])
def delete_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    db.session.delete(chore)
    db.session.commit()
    return jsonify({"message": "Chore deleted"}), 200


@chore_v1.route('/<int:chore_id>', methods=['PUT'])
def update_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    data = request.get_json()
    chore.task_name = data.get('task_name', chore.task_name)
    chore.reward_level = data.get('reward_level', chore.reward_level)
    db.session.commit()
    return jsonify({"message": "Chore updated"}), 200

