import os,sys
sys.path.insert(0,os.path.dirname(__file__))
from flask import Flask,render_template
from db_init import init_db
from controllers.task_controller import task_bp
from controllers.time_controller import time_bp
from controllers.context_controller import ctx_bp
app=Flask(__name__,template_folder='templates',static_folder='static')
app.register_blueprint(task_bp)
app.register_blueprint(time_bp)
app.register_blueprint(ctx_bp)
@app.route('/')
def index(): return render_template('index.html')
if __name__=='__main__':
    init_db()
    print("\n  Tarsck running at http://localhost:5000\n")
    app.run(debug=True,port=5000)
