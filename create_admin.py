from app import create_app
from app.models import db, User

app = create_app()

with app.app_context():
    email = input("Enter the email of the user to make admin: ").strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user:
        print(f"No user found with email: {email}")
    else:
        user.is_admin = True
        db.session.commit()
        print(f"Success! {user.first_name} {user.last_name} is now an admin.")