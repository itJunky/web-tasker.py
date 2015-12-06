# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, send_from_directory
from flask_bootstrap import Bootstrap

def create_app():
  app = Flask(__name__, static_url_path='/static/')
  Bootstrap(app)
  return app

app = create_app()


@app.route("/")
def index():
    # getting referer
    user_from='some-site.ru'
    return render_template('index.html', title='Hi', user_from=user_from) 

@app.route("/task")
@app.route("/task/<number>")
def task(number=None):
    return render_template('task.html', tittle='Задачи', number=number)

@app.route("/profile")
def profile(user=None):
	return render_template('profile.html', user=user)

@app.route("/about")
def about():
    return render_template('about.html', tittle='О сайте')

@app.route("/login")
def login(user):
    return render_template('login.html', user=user)

@app.route("/logout")
def logout(user):
    return render_template('logout.html', user=user)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
