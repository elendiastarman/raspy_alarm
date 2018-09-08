from flask import render_template, redirect, abort, url_for

from . import app


# Create your views here.
@app.route('/', methods=['GET'])
def home_view(**kwargs):
  context = {}
  user = None

  if not user:
    return render_template('home.html', **context)
  else:
    return redirect(url_for('user_view', user=user))


@app.route('/<username>', methods=['GET'])
def new_web_view(**kwargs):
  context = {}

  return render_template('home.html', **context)
