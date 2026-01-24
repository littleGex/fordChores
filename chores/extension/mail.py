from flask_mail import Message
from flask import current_app
from chores.extension import mail


def send_payout_email(user_name, total_amount, task_count, chore_details, recipient_email):
    # The parent (admin) who needs to pay
    parent_email = current_app.config.get('MAIL_USERNAME')

    msg = Message(
        subject=f"💰 Payout Request: {user_name}",
        recipients=[parent_email],
        cc=[recipient_email],  # Optional: CC the child for their records
        sender=parent_email
    )

    # HTML Template for a nice "Pay Stub" look
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #e5e7eb; border-radius: 16px; padding: 24px;">
        <h2 style="color: #4f46e5; margin-bottom: 8px;">Payout Request</h2>
        <p style="color: #6b7280; font-size: 16px;"><strong>{user_name}</strong> has completed <strong>{task_count}</strong> chores and is ready for a payout!</p>

        <div style="background-color: #f3f4f6; border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0;">
            <span style="color: #4f46e5; font-size: 14px; font-weight: bold; text-transform: uppercase;">Total Owed</span>
            <h1 style="margin: 0; font-size: 48px; color: #111827;">€{total_amount:.2f}</h1>
        </div>

        <h3 style="font-size: 14px; text-transform: uppercase; color: #9ca3af; letter-spacing: 0.05em;">Chore Details</h3>
        <table style="width: 100%; border-collapse: collapse; margin-top: 12px;">
            <thead>
                <tr style="border-bottom: 2px solid #f3f4f6;">
                    <th style="text-align: left; padding: 12px 0; color: #374151;">Task</th>
                    <th style="text-align: right; padding: 12px 0; color: #374151;">Amount</th>
                </tr>
            </thead>
            <tbody>
    """

    # Loop through the itemized chores
    for chore in chore_details:
        html_body += f"""
            <tr style="border-bottom: 1px solid #f3f4f6;">
                <td style="padding: 12px 0; color: #4b5563;">{chore['name']}</td>
                <td style="padding: 12px 0; text-align: right; font-weight: bold; color: #4f46e5;">€{chore['reward']:.2f}</td>
            </tr>
        """

    html_body += """
            </tbody>
        </table>

        <p style="margin-top: 32px; font-size: 12px; color: #9ca3af; text-align: center;">
            This request was sent from your ChoreTracker App.
        </p>
    </div>
    """

    msg.html = html_body
    msg.body = f"{user_name} is owed €{total_amount:.2f} for {task_count} chores."  # Fallback for non-HTML clients

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Mail failed: {e}")
        return False
