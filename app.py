from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import flask_login
import bleach

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret'
db = SQLAlchemy(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# Dummy users for login
users = {'admin': {'password': 'admin'}}

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return
    
    user = User()
    user.id = username
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in users:
        return
    
    user = User()
    user.id = username
    return user

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    username = request.form['username']
    password = request.form['password']
    if username in users and users[username]['password'] == password:
        user = User()
        user.id = username
        flask_login.login_user(user)
        return redirect(url_for('index'))
    
    return 'Bad login'

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized', 401

@app.route('/')
@flask_login.login_required
def index():
    # RAW Query
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)

@app.route('/add', methods=['POST'])
@flask_login.login_required
def add_student():
    name = request.form['name']
    age = request.form['age']
    grade = request.form['grade']

    # Sanitize input
    name = bleach.clean(name)
    age = bleach.clean(age)
    grade = bleach.clean(grade)
    
    # RAW Query
    db.session.execute(
        text("INSERT INTO student (name, age, grade) VALUES (:name, :age, :grade)"),
        {'name': name, 'age': age, 'grade': grade}
    )
    db.session.commit()
    return redirect(url_for('index'))


# @app.route('/delete/<string:id>') 
# def delete_student(id):
#     # RAW Query
#     db.session.execute(text(f"DELETE FROM student WHERE id={id}"))
#     db.session.commit()
#     return redirect(url_for('index'))

@app.route('/delete/<string:id>')
@flask_login.login_required
def delete_student(id):
    db.session.execute(
        text("DELETE FROM student WHERE id = :id"),
        {'id': id}
    )
    db.session.commit()
    return redirect(url_for('index'))



@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@flask_login.login_required
def edit_student(id):
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']
        
        # RAW Query
        # db.session.execute(text(f"UPDATE student SET name='{name}', age={age}, grade='{grade}' WHERE id={id}"))
        db.session.execute(
            text("UPDATE student SET name = :name, age = :age, grade = :grade WHERE id = :id"),
            {'name': name, 'age': age, 'grade': grade, 'id': id}
        )

        db.session.commit()
        return redirect(url_for('index'))
    else:
        # RAW Query
        # student = db.session.execute(text(f"SELECT * FROM student WHERE id={id}")).fetchone()
        student = db.session.execute(
            text("SELECT * FROM student WHERE id = :id"),
            {'id': id}
        ).fetchone()
        return render_template('edit.html', student=student)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

