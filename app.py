import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Look for index.html in the root folder instead of /templates
app = Flask(__name__, template_folder=".")
app.config['SECRET_KEY'] = 'orbitron-core-access-99'

# Database Configuration
uri = os.getenv("DATABASE_URL", "sqlite:///orbitron.db")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    playlists = db.relationship('Playlist', backref='owner', lazy=True)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---
@app.route('/')
def index():
    songs = []
    if current_user.is_authenticated:
        songs = Playlist.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', songs=songs)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if User.query.filter_by(username=username).first():
        return redirect(url_for('index')) # Username exists
    
    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
    return redirect(url_for('index'))

@app.route('/add_song', methods=['POST'])
@login_required
def add_song():
    name = request.form.get('song_name')
    if name:
        db.session.add(Playlist(song_name=name, user_id=current_user.id))
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
