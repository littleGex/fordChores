import os
import requests

from flask import Blueprint, jsonify, request
from flask_cors import CORS
from chores.models import User, Completion
from chores.database.payout_manager import run_weekly_payout
from chores.database import db
from chores.extension.mail import send_payout_email


user_v1 = Blueprint('user_v1', __name__, url_prefix='/api/v1/users')
CORS(
    user_v1,
    origins=["https://chores.ford-home-apps.com"],
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)


@user_v1.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(name=data['name'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User added successfully"}), 201


@user_v1.route('/')
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name, "email": u.email} for u in users])


@user_v1.route('/<int:user_id>/balance')
def get_user_balance(user_id):
    # Find all pending completions for this user
    pending = Completion.query.filter_by(user_id=user_id, payout_status='pending').all()

    # Calculate total by reaching through the relationship to the Chore model
    total = sum(item.chore.reward_level for item in pending)

    return jsonify({
        "user_id": user_id,
        "pending_balance": total,
        "task_count": len(pending)
    })


@user_v1.route('/<int:user_id>/history')
def get_user_history(user_id):
    # Returns all completions (paid and unpaid) sorted by date
    history = Completion.query.filter_by(user_id=user_id).order_by(Completion.completed_at.desc()).all()

    return jsonify([{
        "task": h.chore.task_name,
        "reward": h.chore.reward_level,
        "status": h.payout_status,
        "date": h.completed_at.isoformat()
    } for h in history])


@user_v1.route('/<int:user_id>/payout', methods=['POST'])
def payout_user(user_id):
    # This calls your existing payout_manager logic
    total = run_weekly_payout(user_id)
    return jsonify({
        "message": "Payout successful",
        "amount_paid": total,
        "status": "success"
    })


@user_v1.route('/<int:user_id>/request_payout', methods=['POST'])
def request_payout(user_id):
    user = User.query.get_or_404(user_id)
    pending = Completion.query.filter_by(user_id=user_id, payout_status='pending').all()

    if not pending:
        return jsonify({
            "message": "No pending chores",
            "email_status": "none" # Explicitly return a status
        }), 200

    total = sum(c.chore.reward_level for c in pending)

    base_url = os.getenv("PM_BASE_URL")
    try:
        # Call PocketMoney to get user_id
        lookup_res = requests.get(
            f"{base_url}{os.getenv('PM_LOOKUP_PATH')}{user.name}"
        )
        lookup_res.raise_for_status()
        pm_child_id = lookup_res.json().get("id")

        # Add chores money
        payload = {
            "amount": float(total),
            "description": f"Payout for {len(pending)} chores"
        }
        deposit_res = requests.post(
            f"{base_url}{os.getenv('PM_DEPOSIT_PATH')}{pm_child_id}",
            params=payload
        )
        deposit_res.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Pocket Money sync failed",
                        "details": str(e)}), 503

    chore_list = [{"name": c.chore.task_name,
                   "reward": c.chore.reward_level} for c in pending]
    # Trigger the email logic from mail.py
    email_sent = send_payout_email(
        user.name,
        total,
        len(pending),
        chore_details=chore_list,
        recipient_email=user.email
    )

    # Mark as paid in database
    for item in pending:
        item.payout_status = 'paid'
    db.session.commit()

    return jsonify({
        "message": "Payout processed",
        "email_status": "sent" if email_sent else "failed"
    }), 200


@user_v1.route('/test_email')
def test_email():
    # Try sending a dummy email to yourself
    success = send_payout_email(
        user_name="Test Scout",
        total_amount=99.99,
        task_count=1
    )

    if success:
        return "<h3>Success!</h3><p>Check your iCloud inbox (and spam folder).</p>"
    else:
        return "<h3>Failed!</h3><p>Check the terminal/console for the specific error.</p>", 500


@user_v1.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # Note: You may need to handle cascading deletes for completions
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User removed"}), 200


@user_v1.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify({"message": "User updated"}), 200
