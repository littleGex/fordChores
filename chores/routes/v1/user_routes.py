import os
import requests

from flask import Blueprint, jsonify, request
from chores.models import User, Completion
from chores.database.payout_manager import run_weekly_payout
from chores.database import db
from chores.extension.mail import send_payout_email


user_v1 = Blueprint('user_v1', __name__, url_prefix='/api/v1/users')


@user_v1.route('/add_user',
               methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(name=data['name'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User added successfully"}), 201


@user_v1.route('/',
               methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id,
                     "name": u.name,
                     "email": u.email} for u in users])


@user_v1.route('/<int:user_id>/balance',
               methods=['GET'])
def get_user_balance(user_id):
    # Find all pending completions for this user
    pending = Completion.query.filter_by(
        user_id=user_id,
        payout_status='pending').all()

    # Calculate total by reaching through the relationship to the Chore model
    total = sum(item.chore.reward_level for item in pending)

    return jsonify({
        "user_id": user_id,
        "pending_balance": total,
        "task_count": len(pending)
    })


@user_v1.route('/<int:user_id>/history',
               methods=['GET'])
def get_user_history(user_id):
    # Returns all completions (paid and unpaid) sorted by date
    history = Completion.query.filter_by(
        user_id=user_id).order_by(
        Completion.completed_at.desc()).all()

    return jsonify([{
        "task": h.chore.task_name,
        "reward": h.chore.reward_level,
        "status": h.payout_status,
        "date": h.completed_at.isoformat()
    } for h in history])


@user_v1.route('/<int:user_id>/payout',
               methods=['POST'])
def payout_user(user_id):
    User.query.get_or_404(user_id)

    # This calls your existing payout_manager logic. run_weekly_payout
    # now locks pending rows and marks them 'paid' atomically, so a
    # duplicate/concurrent call to this route returns 0.0 instead of
    # paying out twice.
    total = run_weekly_payout(user_id)

    if total <= 0:
        return jsonify({
            "message": "No pending chores to pay out",
            "amount_paid": 0.0,
            "status": "noop"
        }), 200

    return jsonify({
        "message": "Payout successful",
        "amount_paid": total,
        "status": "success"
    })


@user_v1.route('/<int:user_id>/request_payout',
               methods=['POST'])
def request_payout(user_id):
    user = User.query.get_or_404(user_id)

    # Lock the pending rows for this user so concurrent requests serialize
    pending = Completion.query.filter_by(
        user_id=user_id,
        payout_status='pending'
    ).with_for_update(skip_locked=True).all()

    if not pending:
        return jsonify({
            "message": "No pending chores",
            "email_status": "none"
        }), 200

    total = sum(c.chore.reward_level for c in pending)
    chore_list = [{"name": c.chore.task_name,
                   "reward": c.chore.reward_level} for c in pending]

    # Claim these completions immediately, before the slow external call.
    # If a second request arrives, the rows are already 'processing' /
    # no longer 'pending', so it will find nothing and exit above.
    for item in pending:
        item.payout_status = 'processing'
    db.session.commit()

    base_url = os.getenv("PM_BASE_URL")
    try:
        lookup_res = requests.get(
            f"{base_url}{os.getenv('PM_LOOKUP_PATH')}{user.name}"
        )
        lookup_res.raise_for_status()
        pm_child_id = lookup_res.json().get("id")

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
        # Roll back the claim so the chores can be retried/paid later
        for item in pending:
            item.payout_status = 'pending'
        db.session.commit()
        return jsonify({"error": "Pocket Money sync failed",
                        "details": str(e)}), 503

    email_sent = send_payout_email(
        user.name,
        total,
        len(pending),
        chore_details=chore_list,
        recipient_email=user.email
    )

    # Finalize as paid (already claimed, just confirming final state)
    for item in pending:
        item.payout_status = 'paid'
    db.session.commit()

    return jsonify({
        "message": "Payout processed",
        "email_status": "sent" if email_sent else "failed"
    }), 200


@user_v1.route('/test_email',
               methods=['GET'])
def test_email():
    # Try sending a dummy email to yourself
    success = send_payout_email(
        user_name="Test Scout",
        total_amount=99.99,
        task_count=1
    )

    if success:
        return ("<h3>Success!</h3><p>Check your iCloud inbox "
                "(and spam folder).</p>")
    else:
        return ("<h3>Failed!</h3><p>Check the terminal/console for"
                " the specific error.</p>"), 500


@user_v1.route('/<int:user_id>',
               methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # Note: You may need to handle cascading deletes for completions
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User removed"}), 200


@user_v1.route('/<int:user_id>',
               methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify({"message": "User updated"}), 200
