# Imports
import time
import random
import string
import re
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, Markup, send_file
from flask_hashing import Hashing
from werkzeug import secure_filename

app = Flask(__name__)            # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

hashing = Hashing(app)
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='#####',
    USERNAME='####',  #SUPERADMIN name
    PASSWORD= hashing.hash_value('####',salt='####'), #SUPERADMIN password
    ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png', 'pdf']), #Allowed extensions to store
    UPLOAD_FOLDER = '/var/www/html/family-sharer/static/home',
    IMAGE_ROOT = '/static/home/'
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

## Generates alert messages
def alert(typemess, message):
  return Markup("<div class=\"container\"><div class=\"alert alert-dismissible alert-"+typemess+ "\"                                                                                                                                         ><button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button><strong>"+ message +                                                                                                                                          "</strong></div></div>")


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
    temp_list = [ f for f in os.listdir(os.getcwd()) if os.path.isfile(os.path.join(os.getcwd(),f))                                                                                                                                          ]


    for filename in temp_list :
      img = 0
      root, ext = os.path.splitext(filename)
      path = os.path.relpath(os.getcwd(), app.config['UPLOAD_FOLDER'])
      if ext == ".jpg" or ext == ".png" or ext == ".jpeg" :
        img = 1
      file_list.append({'name' : root, 'ext' : ext, 'path' : app.config['IMAGE_ROOT'] + path + "/" +                                                                                                                                          filename, 'img' : img})

    print(file_list)
    return render_template('home.html',dir = dir_list, file = file_list)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

####################################################
########## DIRECTORIES AND FILES FUNCTION ##########
####################################################

#### Change directory
#### @param
#### FORM : 'backpath' : location of the directory
@app.route('/#!/switchdir',methods=['GET','POST'])
def switchdir():
  if not session.get('logged_in'):
    abort(401)

  backpath = request.form.get('backpath','')
  if backpath != '':
    os.chdir(backpath)
    return redirect(url_for('home'))

#### Create a new directory
#### @param
#### FORM : 'dirname' : name of the new directory
@app.route('/#!/newdir',methods=['GET','POST'])
def newdir():
  if not session.get('logged_in'):
    abort(401)
  dirname = request.form.get('dirname','')
  dirname = secure_filename(dirname)
  os.mkdir(dirname)
  return redirect(url_for('home'))

#### Download a file
#### @param
#### FORM : 'downfile' : name of file requested
@app.route('/#!/downfile',methods=['POST'])
def downfile():
  if not session.get('logged_in'):
    abort(401)
  downfile = request.form.get('downfile','')
  if(downfile != '') :
    return send_file(os.path.join(os.getcwd(),downfile), as_attachment=True)

#### Delete a file
#### @param
#### FORM : 'delfile' : name of file requested
@app.route('/#!/delfile',methods=['POST'])
def delfile():
  if not session.get('logged_in'):
    abort(401)
  delfile = request.form.get('delfile','')
  if(delfile != '') :
    os.remove(delfile)
    return redirect(url_for('home'))
  return redirect(url_for('home', error = "File doesn't exist"))

#### Delete a directory
#### @param
#### FORM : 'deldir' : name of the directory requested

@app.route('/#!/deldir',methods=['POST'])
def deldir():
  if not session.get('logged_in'):
    abort(401)
  deldir = request.form.get('deldir','')
  if(deldir != '') :
    try:
      os.rmdir(deldir)
    except OSError as error:
      flash(alert("danger","Directory is not empty"))
  return redirect(url_for('home'))

#### Download a directory
#### @param
#### FORM : 'downdir' : name of the directory requested

@app.route('/#!/downdir',methods=['POST'])
def downdir():
  if not session.get('logged_in'):
    abort(401)
  downdir = request.form.get('downdir','')
  if(downdir != '') :
    return send_file(os.path.join(os.getcwd(),downfile), as_attachment=True)


####################################################
########## USER AND INVITE CODE  FUNCTION ##########
####################################################

#### Admin Panel
@app.route('/admin_panel')
def admin_panel():
  db = get_db()
  if session['superadmin'] != True :
    cur = db.execute('SELECT level FROM admin WHERE user = ?',(session['user'],))
    level = cur.fetchone()
    if not session.get('logged_in') or level < 100 :
      abort(401)
  cur = db.execute('SELECT user FROM admin')
  user = cur.fetchall()
  cur = db.execute('SELECT key,level FROM invkey')
  code = cur.fetchall()
  return render_template('admin_panel.html', user=user, code = code)

#### Generates invite code
#### @param
#### int : lenght of the invitation code
#### string : salt for random string
def generate_invite(size=6, chars=string.ascii_uppercase + string.digits):
 return ''.join(random.choice(chars) for _ in range(size))

#### Create new invitation code
#### @param
#### FORM : 'lvl' : level of accreditation that the user will have when using this code
@app.route('/#!/newcode',methods=['POST'])
def newcode():
  db = get_db()
  if session['superadmin'] != True :
    cur = db.execute('SELECT level FROM admin WHERE user = ?',(session['user'],))
    level = cur.fetchone()
    if not session.get('logged_in') or level < 100:
      abort(401)

  newlvl = request.form.get('lvl','')
  if newlvl == '' :
    newlvl = 1
  invcode = generate_invite()

  db.execute('INSERT INTO invkey(key,level) values (?, ?)',(invcode,newlvl,))
  db.commit()
  return redirect(url_for('admin_panel'))

#### Create new invitation code
#### @param
#### FORM : 'code' : Code used for creating a new account
#### FORM : 'username' : Name for the new user
#### FORM : 'password' : Password the new user chose
@app.route('/#!/activatecode',methods=['POST'])
def activatecode():
  code     = request.form.get('code','')
  username = request.form.get('username','')
  password = request.form.get('password','')

  if( code != '' and username != '' and password != ''):
    db = get_db()
    cur = db.execute('SELECT level FROM invkey WHERE key = ?',(code,))
    if cur.fetchone() is not None :
      res = cur.fetchall()
      hashed = hashing.hash_value(password,salt='####')
      db.execute('DELETE FROM invkey WHERE key = ?',(code,))
      db.execute('INSERT INTO admin(user, password, level) VALUES (?, ?, ?)',(username, hashed, res[                                                                                                                                         0][0],))
      db.commit()
      return redirect(url_for('home'))

  flash(alert("danger","Invitation code invalid"))
  return redirect(url_for('home'))

#### Deletes user
#### @param
#### FORM : 'username' : name of the account that is going to be deleted
@app.route('/#!/deluser',methods=['POST'])
def deluser():
  db = get_db()
  cur = db.execute('SELECT level FROM admin WHERE user = ?',(session['user'],))
  level = cur.fetchone()
  if not session.get('logged_in') or level < 100 :
    abort(401)

  username = request.form.get('username','')
  if(username != '') :
    db.execute('DELETE FROM admin WHERE user = ?',(username,))
    db.commit()
    flash(alert("warning",username + " has been removed from the user's list"))
    return redirect(url_for('admin_panel'))
  flash(alert("danger","Specified user doesn't exist"))
  return redirect(url_for('admin_panel'))

#### Login
#### @param
#### FORM : 'username' : Username used for login
#### FORM : 'password' : Password used for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
      # Check if it's a SUPER ADMIN login
      if(hashing.check_value(app.config['PASSWORD'],request.form['password'],salt='####') and app.co                                                                                                                                         nfig['USERNAME'] == request.form['username']):
          session['logged_in'] = True
          session['username'] = app.config['USERNAME']
          session['superadmin'] = True
          flash(alert("success","You successfully logged in!"))
          return redirect(url_for('home'))
      # Check if it's a normal login
      db = get_db()
      cur = db.execute('select password from admin where user=?',(request.form['username'],))
      if cur.fetchone() is not None:
        entries = cur.fetchall()
        if(hashing.check_value(entries[0][0],request.form['password'],salt='####')):
          session['logged_in'] = True
          session['user'] = request.form['username']
          session['superadmin'] = False
          flash(alert("success","You successfully logged in!"))
          return redirect(url_for('home'))
      error = 'Invalid credential'
      return render_template('login.html', error=error)

#### Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('superadmin', None)
    flash(alert("success","You successfully logged out!"))
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8083)
