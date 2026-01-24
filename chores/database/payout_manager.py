from chores.database import db
from chores.models.completion import Completion


def run_weekly_payout(user_id):
    """
    Finds all 'pending' completions for a user, calculates the total,
    marks them 'paid', and could be expanded to create a Payout record.
    """
    # Fetch all unpaid chores for this specific user
    pending_tasks = Completion.query.filter_by(
        user_id=user_id,
        payout_status='pending'
    ).all()

    if not pending_tasks:
        return 0.0

    total_payout = sum(task.chore.reward_level for task in pending_tasks)

    # Mark as paid
    for task in pending_tasks:
        task.payout_status = 'paid'
        # task.payout_id = some_new_payout_id (if using a Payout table)

    db.session.commit()

    return total_payout
