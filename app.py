from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date
import math
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

#  Configuration 
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#  Setup Flask-Login 
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login if not authenticated

#  Load Event Data 
with open('data/events.json') as f:
    events = json.load(f)

#  Utility Functions 
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth using the Haversine formula.
    """
    R = 6371  # Earth's radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

#  Database Models 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    scores = db.relationship('Score', backref='author', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    score = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes

# Homepage route: displays the game
@app.route("/")
def index():
    today = datetime.now()
    date_number = today.month * 100 + today.day  # e.g., March 22 becomes 322
    game_year = 2025 - date_number

    event = events.get(str(game_year), None)
    if not event:
        event = {
            "name": "Unknown Event",
            "lat": 0,
            "lon": 0,
            "hint": "No known event for this year."
        }
    return render_template("index.html", hint=event["hint"], year=game_year)

# Route to process the guess and calculate the distance
@app.route("/submit_guess", methods=["POST"])
def submit_guess():
    data = request.json
    guess_lat = data["lat"]
    guess_lon = data["lon"]
    year = data["year"]

    event = events.get(str(year))
    if not event:
        return jsonify({"error": "Event not found"})

    actual_lat = event["lat"]
    actual_lon = event["lon"]
    distance = haversine(guess_lat, guess_lon, actual_lat, actual_lon)

    # Record the score for today if the user is logged in
    if current_user.is_authenticated:
        today_date = date.today()
        existing_score = Score.query.filter_by(user_id=current_user.id, date=today_date).first()
        if existing_score:
            # For simplicity, average the new score with the existing score
            existing_score.score = (existing_score.score + distance) / 2
        else:
            new_score = Score(date=today_date, score=distance, user_id=current_user.id)
            db.session.add(new_score)
        db.session.commit()

    return jsonify({
        "event": event["name"],
        "hint": event["hint"],
        "actual_location": {"lat": actual_lat, "lon": actual_lon},
        "distance": round(distance, 2)
    })

# Authentication Routes

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.')
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Account Route
@app.route('/account')
@login_required
def account():
    # Retrieve all score records for the current user
    scores = Score.query.filter_by(user_id=current_user.id).all()
    
    if not scores:
        average_score = None
        best_score = None
        best_score_date = None
    else:
        # Calculate the average score (sum of all scores divided by number of records)
        total = sum(s.score for s in scores)
        average_score = total / len(scores)
        
        # Determine the best score (assuming lower is better) and its date
        best_record = min(scores, key=lambda s: s.score)
        best_score = best_record.score
        best_score_date = best_record.date  # This is a date object

    return render_template("account.html",
                           average_score=average_score,
                           best_score=best_score,
                           best_score_date=best_score_date)

# New endpoint to play the game with a selected year
@app.route("/play")
def play_year():
    year = request.args.get("year")
    if not year:
        return redirect(url_for('index'))
    event = events.get(str(year))
    if not event:
        event = {
            "name": "Unknown Event",
            "lat": 0,
            "lon": 0,
            "hint": "No known event for this year."
        }
    return render_template("index.html", hint=event["hint"], year=year)

# ================== Run the App ==================
if __name__ == "__main__":
    app.run(debug=True)
