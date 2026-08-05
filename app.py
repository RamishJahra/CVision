from flask import Flask

from config import Config

from models import db, login_manager, mail
from models.user import User

from routes.public import public
from routes.auth import auth
from models.location import District, Area


app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)

# Flask-Login configuration
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Register Blueprints
app.register_blueprint(public)
app.register_blueprint(auth)


# Create database tables
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)