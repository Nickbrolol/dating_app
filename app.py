from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating.db'
db = SQLAlchemy(app)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.String(300))
    likes = db.relationship('Like', backref='user', lazy=True)
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

# Лайки
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    liked_user_id = db.Column(db.Integer, nullable=False)

# Сообщения
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.String(500))

with app.app_context():
    db.create_all()

# Главная
@app.route('/')
def index():
    return render_template('index.html')

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('profile'))
        return "Неверные данные"
    return render_template('login.html')

# Профиль
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

# Просмотр всех пользователей
@app.route('/users')
def users():
    all_users = User.query.filter(User.id != session.get('user_id')).all()
    return render_template('users.html', users=all_users)

# Лайк пользователя
@app.route('/like/<int:user_id>')
def like(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    new_like = Like(user_id=session['user_id'], liked_user_id=user_id)
    db.session.add(new_like)
    db.session.commit()
    return redirect(url_for('users'))

# Отправка сообщения
@app.route('/message/<int:user_id>', methods=['GET', 'POST'])
def message(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        content = request.form['content']
        msg = Message(sender_id=session['user_id'], receiver_id=user_id, content=content)
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('messages'))
    receiver = User.query.get(user_id)
    return render_template('messages.html', receiver=receiver)

# Просмотр сообщений
@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    received_msgs = user.messages_received
    return render_template('messages.html', messages=received_msgs)

# Выход
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

