from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests

db = SQLAlchemy()

app = Flask(__name__)
app.app_context().push()

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(500), unique=True, nullable=True)
    img_url = db.Column(db.String(500), unique=True, nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


db.create_all()

app.config['SECRET_KEY'] = 'the-very-secret-key'
Bootstrap(app)

# new_movie = Movie(
#     title="Star Wars: Episode I - The Phantom Menace",
#     year=1999,
#     description="Two Jedi escape a hostile blockade to find allies and come across a young boy who may bring balance "
#                 "to the Force, but the long dormant Sith resurface to claim their original glory.",
#     rating=7.7,
#     ranking=9,
#     review="Great introduction to the Republic and a great start to the prequel trilogy",
#     img_url="https://m.media-amazon.com/images/I/81gzXmcpM6L._AC_SY879_.jpg"
# )

# db.session.add(new_movie)
# db.session.commit()

all_movies = db.session.query(Movie).all()


class RateMovieForm(FlaskForm):
    rating = FloatField(label='Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField(label='Your Review', validators=[DataRequired()])
    submit = SubmitField(label='Done', validators=[DataRequired()])


class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    updated_all_movies = db.session.query(Movie).all()
    all_movie_ratings = {}
    for movie in updated_all_movies:
        rating = movie.rating
        if rating not in all_movie_ratings:
            all_movie_ratings[rating] = [movie]
        else:
            all_movie_ratings[rating].append(movie)

    keys = list(all_movie_ratings.keys())
    keys.sort()
    sorted_all_movie_ratings = {i: all_movie_ratings[i] for i in keys}
    sorted_all_movies = []
    for movie in sorted_all_movie_ratings.values():
        for current_movie in movie:
            sorted_all_movies.append(current_movie)
    reverse_keys = list(all_movie_ratings.keys())
    reverse_keys.sort(reverse=True)
    print(reverse_keys)
    reversed_sorted_all_movie_ratings = {i: all_movie_ratings[i] for i in reverse_keys}
    print(reversed_sorted_all_movie_ratings)
    reversed_sorted_all_movies = []
    for movie in reversed_sorted_all_movie_ratings.values():
        for current_movie in movie:
            reversed_sorted_all_movies.append(current_movie)
    count = 1
    for movie in reversed_sorted_all_movies:
        movie.ranking = count
        count += 1
    return render_template("index.html", movies=sorted_all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = FindMovieForm()
    if form.validate_on_submit():
        movie_title = request.form["title"]
        url = f"https://api.themoviedb.org/3/search/movie?query={movie_title}&language=en-US&page=1"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5OTYwZTAxNzFhMTE5MDM3MGJkOTBiNjcxMTIyZGQ5ZSIsIn"
                             "N1YiI6IjY0Nzc3OWI2ZTMyM2YzMDE0ODE0ZDQ0NyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjox"
                             "fQ.l0U0WkCOExqsF_iVONwaMgZauHgl9H58OvBDrUjmNwI"
        }
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        data = response.json()['results']
        print(data)

        return render_template('select.html', options=data)
    return render_template('add.html', form=form)


@app.route("/find", methods=["GET", "POST"])
def find_movie():
    movie_id = request.args.get('id')
    url = url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5OTYwZTAxNzFhMTE5MDM3MGJkOTBiNjcxMTIyZGQ5ZSIsIn"
                         "N1YiI6IjY0Nzc3OWI2ZTMyM2YzMDE0ODE0ZDQ0NyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjox"
                         "fQ.l0U0WkCOExqsF_iVONwaMgZauHgl9H58OvBDrUjmNwI"
    }
    response = requests.get(url=url, headers=headers)
    response.raise_for_status()
    data = response.json()
    print(data)
    year = int(data['release_date'].split("-")[0])
    new_movie = Movie(
        title=data['title'],
        year=year,
        description=data["overview"],
        rating=None,
        ranking=None,
        review=None,
        img_url=f"https://image.tmdb.org/t/p/w1280{data['poster_path']}"
    )

    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
