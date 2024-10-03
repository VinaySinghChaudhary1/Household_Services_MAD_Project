from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/about/<user_name')
def about(user_name):
    return render_template('about.html', name=user_name)


if __name__ == '__main__':
    app.run(debug=True)
