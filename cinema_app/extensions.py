from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS

# Ініціалізація розширень
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()
csrf = CSRFProtect()
cache = Cache()
compress = Compress()
migrate = Migrate()
cors = CORS()
