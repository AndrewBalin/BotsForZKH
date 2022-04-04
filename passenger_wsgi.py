import sys, os
sys.path.append('/home/z/zvezda72/serg/main/')
sys.path.append('/home/z/zvezda72/serg/flask_app/lib/python3.6/site-packages')
from main import app as application
from werkzeug.debug import DebuggedApplication
application.wsgi_app = DebuggedApplication(application.wsgi_app, True)
application.debug = True