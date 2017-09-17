# Imports
import time
import re
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, Markup
from flask_hashing import Hashing
from werkzeug import secure_filename

app = Flask(__name__)		 # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

hashing = Hashing(app)
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='#####',
    USERNAME='####',  #SUPERADMIN name
    PASSWORD= hashing.hash_value('####',salt='####'), #SUPERADMIN password
    ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png', '*']), #Allowed extensions to store
    UPLOAD_FOLDER = '####'
))


app.config.from_envvar('FLASKR_SETTINGS', silent=True)
os.chdir(app.config['UPLOAD_FOLDER'])

## Database function ##

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

## Data injected in all templates ##

@app.context_processor
def inject_dict_for_all_templates():
  path = os.path.relpath(os.getcwd(), app.config['UPLOAD_FOLDER'])
  backpath = os.path.relpath(app.config['UPLOAD_FOLDER'],os.getcwd())

  path_array = []

  path = path.split('/')
  path = ['home'] + path

  backpath = backpath.split('/')
  if len(backpath) - 1 != 0 :
    for i in range(len(backpath) - 1) :
      backpath[i] = backpath[i] + '/' +backpath[i + 1] 
  backpath = backpath + ['']

  for i in range(len(path)):
    path_array.append({'path' : path[i], 'backpath' : backpath[i]})

  return dict(path=path_array)		


## template function


@app.route('/',methods=['GET','POST'])
def home():
  if not session.get('logged_in'):
    error = None
    return render_template('login.html',error=error)
  else :
    if( request.method == 'POST') :
      status  = request.form.get('status','###')
      print status
      if status == 'OK':
        print request.files['file']
        file = request.files['file']
        if file and allowed_file(file.filename):
          filename = secure_filename(file.filename)
          file.save(os.path.join(os.getcwd(), filename ))  

    ## Switching directory (breadcrumb) ##
    directory = request.form.get('dir','')
    if directory != '' :
      os.chdir(directory)


    file_list = []
    dir_list = [ f for f in os.listdir(os.getcwd()) if os.path.isdir(os.path.join(os.getcwd(),f)) ]
    temp_list = [ f for f in os.listdir(os.getcwd()) if os.path.isfile(os.path.join(os.getcwd(),f)) ]
 
    for filename in temp_list :
      root, ext = os.path.splitext(filename)
      file_list.append({'name' : root, 'ext' : ext})

    print(file_list)
    return render_template('home.html',dir = dir_list, file = file_list)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/#switchdir',methods=['GET','POST'])
def switchdir():
  directory = request.form.get('backpath','')
  if directory != '':
    os.chdir(directory)
    return redirect(url_for('home'))


@app.route('/#newdir',methods=['GET','POST'])
def newdir():
  dirname = request.form.get('dirname','')
  dirname = secure_filename(dirname)  
  os.mkdir(dirname)
  return redirect(url_for('home'))

@app.route('/newfile',methods=['POST'])
def newfile():
  if( request.method == 'POST') :
    status  = request.form.get('status','###')
    print status
    if status == 'OK':
      print request.files['file']
      file = request.files['file']
      if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(os.getcwd(), filename ))  
        return redirect(url_for('home'))

@app.route('/admin_panel')
def admin_panel():
    if not session.get('logged_in'):
        abort(401)
    return render_template('admin_panel.html')



    ####################
    #insert web-console#
    ####################

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
      if(hashing.check_value(app.config['PASSWORD'],request.form['password'],salt='####') and app.config['USERNAME'] == request.form['username']):
          session['logged_in'] = True
          message= Markup("<div class=\"container\"><div class=\"alert alert-dismissible alert-success\"><button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button><strong>Alert : You successfully logged in</strong></div></div>")
	  flash(message)
	  return redirect(url_for('home'))
      db = get_db()
      cur = db.execute('select password from admin where user=?',(request.form['username'],))
      if cur.fetchone() is not None: 
        entries = cur.fetchall()
        print entries
        if(hashing.check_value(entries[0][0],request.form['password'],salt='####')):
          session['logged_in'] = True
          message= Markup("<div class=\"container\"><div class=\"alert alert-dismissible alert-success\"><button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button><strong>Alert : You successfully logged in</strong></div></div>")
	  flash(message)
	  return redirect(url_for('home'))
      error = 'Invalid credential'
      return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    message= Markup("<div class=\"container\"><div class=\"alert alert-dismissible alert-success\"><button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button><strong>Alert : You successfully logged out</strong></div></div>")
    flash(message)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8083)

