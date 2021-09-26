import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
import sys
from werkzeug.exceptions import abort
import logging
from datetime import datetime


COUNT = 0


def hits_counter():
    global COUNT
    COUNT = COUNT + 1

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    hits_counter()
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

def log_msg(message):
    time = datetime.now().strftime('%d-%m-%Y, %H:%M:%S')
    return app.logger.info('%(time)s, %(message)s' %{"time": time, "message": message})

def log_error_msg(message):
    time = datetime.now().strftime('%d-%m-%Y, %H:%M:%S')
    return app.logger.error('%(time)s, %(message)s' %{"time": time, "message": message})

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      log_error_msg('A non-existing article is accessed and a 404 page is returned.')
      return render_template('404.html'), 404
    else:
      title = post['title']
      log_msg('Article "%(title)s" retrieved' % {"title": title})
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    log_msg('The "About Us" page is retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            log_msg('A new article "%(title)s" is created!' % {"title": title})
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthcheck():
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )

    app.logger.info('Status request successful')
    return response


@app.route('/metrics')
def metrics():
    # Total amount of posts in the database
    connection = get_db_connection()
    postCount = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    response = app.response_class(
        response=json.dumps(
            {"db_connection_count": COUNT, "post_count": str(len(postCount))}),
        status=200,
        mimetype='application/json'
    )
    app.logger.info('Metrics request successful')
    return response


@app.errorhandler(404)
def page_not_found(e):
    app.logger.error('Page could not be found')
    return 'This page does not exist', 404


# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(filename='app.log', level=logging.DEBUG)
    app.run(host='0.0.0.0', port='3111')