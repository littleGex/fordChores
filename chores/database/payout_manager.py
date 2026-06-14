from chores.database import db
from chores.models.completion import Completion


def run_weekly_payout(user_id):
    """
    Finds all 'pending' completions for a user, calculates the total,
    marks them 'paid', and could be expanded to create a Payout record.

    This is made safe against concurrent/duplicate calls (e.g. a double
    button press, or two requests racing) by:
      - locking the pending rows for this user (FOR UPDATE) so a second
        concurrent call cannot see the same rows until the first commits
      - immediately flipping status away from 'pending' before doing any
        further work, so a retry/duplicate call finds nothing left to pay
    """
    # Lock the pending rows for this user so concurrent calls serialize.
    # skip_locked means a concurrent duplicate call simply sees an empty
    # result instead of blocking.
    pending_tasks = Completion.query.filter_by(
        user_id=user_id,
        payout_status='pending'
    ).with_for_update(skip_locked=True).all()

    if not pending_tasks:
        return 0.0

    total_payout = sum(task.chore.reward_level for task in pending_tasks)

    # Mark as paid
    for task in pending_tasks:
        task.payout_status = 'paid'
        # task.payout_id = some_new_payout_id (if using a Payout table)

    db.session.commit()

    return total_payout
