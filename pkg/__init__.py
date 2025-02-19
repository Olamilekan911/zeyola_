from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from pkg import config, forms
from pkg.models import db,Customer





# csrf =CSRFProtect()
# mail = Mail()



def create_app():
    from pkg import models
            
    app = Flask(__name__,instance_relative_config=True)

    app.config.from_pyfile("config.py")
    app.config.from_object(config.BaseConfig)
    
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('user/404.html')


    #db = SQLAlchemy(app)
    db.init_app(app)
    migrate = Migrate(app,db)
    # csrf.init_app(app)




    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'user_login'
    login_manager.login_message = 'Please log in to access this page'

    @login_manager.user_loader
    def load_user(cus_id):
        return Customer.query.get(int(cus_id))


    return app



app=create_app()

from pkg import user,admin