from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging

database = SQLAlchemy()
database_name = 'database.sqlite'

# To display logs in the console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    database.create_all()

def create_webapp():
    webapp = Flask(__name__)
    webapp.config['SECRET_KEY'] = 'SecrNor Kayfor webgoher'
    webapp.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_name}'
    
    database.init_app(webapp)

    @webapp.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html')

    login_manager = LoginManager()
    login_manager.init_app(webapp)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    from .views import views
    from .admin import admin
    from .auth import auth
    from .models import User, Cart, Product, Order

    from .recommendation import initialize_engine

    webapp.register_blueprint(views, url_prefix='/')
    webapp.register_blueprint(admin, url_prefix='/') # /admin
    webapp.register_blueprint(auth, url_prefix='/') # /auth/login

    # with webapp.app_context():
    #     create_database()
    
    # Initialize recommendation system
    with webapp.app_context():
        try:
            initialize_engine(webapp)
            logger.info("Recommendation engine initialized successfully")
        except Exception as e:
            logger.warning(f"Recommendation engine initialization failed: {str(e)}")

    return webapp