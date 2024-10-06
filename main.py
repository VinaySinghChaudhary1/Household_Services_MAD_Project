from flask import Flask, render_template

from db import db

app = Flask(__name__)

#.....connect app and db.........
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about/<user_name>')
def about(user_name):
    return render_template('about.html', name=user_name)

# @app.route('/contact')

@app.route('/base')
def base():
    return render_template('base.html')

@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register_customer')
def register_customer():
    return render_template('register_customer.html')


@app.route('/register_supplier')
def register_supplier():
    return render_template('register_supplier.html')
        
if __name__ == '__main__':
    with app.app_context():   #to connect app and db
        db.create_all()       #to create db
    app.run(debug=True)
