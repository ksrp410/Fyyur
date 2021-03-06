#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
from datetime import *
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show {self.id}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    venue_query = db.session.query(Venue.city, Venue.state).distinct()
    datas = []
    for venue in venue_query:
        venue = dict(zip(('city', 'state'), venue))
        venue['venues'] = []
        tmp = Venue.query.filter_by(city=venue['city'], state=venue['state']).all()
        for venue_data in tmp:
            shows = Show.query.filter_by(venue_id=venue_data.id).all()
            venues_data = {
                'id': venue_data.id,
                'name': venue_data.name,
                'num_upcoming_shows': len(upcoming_shows(shows))
            }
            venue['venues'].append(venues_data)
        datas.append(venue)
    return render_template('pages/venues.html', areas=datas)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response = {
        "datas": []
    }
    search_venues = db.session.query(Venue.name, Venue.id).all()
    for venue in search_venues:
        name = venue[0]
        id = venue[1]
        if name.find(request.form.get('search_term', '')) != -1:
            shows = Show.query.filter_by(venue_id=id).all()
            venue = dict(zip(('name', 'id'), venue))
            venue['num_upcoming_shows'] = len(upcoming_shows(shows))
            response['datas'].append(venue)
    response['count'] = len(response['datas'])
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue_query = Venue.query.filter_by(id=venue_id).first()
    shows = Show.query.filter_by(venue_id=venue_id).all()

    data = {
        "id": venue_query.id,
        "name": venue_query.name,
        "genres": venue_query.genres,
        "address": venue_query.address,
        "city": venue_query.city,
        "state": venue_query.state,
        "phone": venue_query.phone,
        "website": venue_query.website,
        "facebook_link": venue_query.facebook_link,
        "seeking_talent": venue_query.seeking_talent,
        "seeking_description": venue_query.seeking_description,
        "image_link": venue_query.image_link,
        "past_shows": past_shows(shows),
        "upcoming_shows": upcoming_shows(shows),
        "past_shows_count": len(past_shows(shows)),
        "upcoming_shows_count": len(upcoming_shows(shows))
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        venue_form = VenueForm()
        create_venue = Venue(
            name=venue_form.name.data,
            city=venue_form.city.data,
            state=venue_form.state.data,
            address=venue_form.address.data,
            phone=venue_form.phone.data,
            genres=venue_form.genres.data,
            facebook_link=venue_form.facebook_link.data,
            website=venue_form.website.data,
            image_link=venue_form.image_link.data,
            seeking_talent=venue_form.seeking_talent.data,
            seeking_description=venue_form.seeking_description.data,
        )
        db.session.add(create_venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + create_venue.name + ' was successfully listed!')
        return render_template('pages/home.html')
    except Exception as e:
        print(f'Error ==> {e}')
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        db.session.rollback()
        return render_template('pages/home.html')
    finally:
        db.session.close()


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        del_venue = Venue.query.get(venue_id)
        db.session.delete(del_venue)
        db.session.commit()
        return render_template('pages/venues.html')
    except Exception as e:
        print(f'Error ==> {e}')
        flash('An error occurred. Venue could not be deleted.')
        db.session.rollback()
        abort(400)
    finally:
        db.session.close()

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    datas = []
    artists_query = db.session.query(Artist.id, Artist.name).all()
    for artist in artists_query :
        artist = dict(zip(('id', 'name'), artist))
        datas.append(artist)
    return render_template('pages/artists.html', artists=datas)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_response = {
        "data": []
    }
    artists_query = db.session.query(Artist.name, Artist.id).all()
    for artist in artists_query :
        name = artist[0]
        id = artist[1]
        if name.find(request.form.get('search_term', '')) != -1:
            shows = Show.query.filter_by(artist_id=id).all()
            artist = dict(zip(('name', 'id'), artist))
            artist['num_upcoming_shows'] = len(upcoming_shows(shows))
            search_response['data'].append(artist)
    search_response['count'] = len(search_response['data'])
    return render_template('pages/search_artists.html', results=search_response,
                           search_term=request.form.get('search_term', ''))



@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    artist_query = Artist.query.filter_by(id=artist_id).first()
    shows = Show.query.filter_by(artist_id=artist_id).all()

    data = {
        "id": artist_query.id,
        "name": artist_query.name,
        "genres": artist_query.genres,
        "city": artist_query.city,
        "state": artist_query.state,
        "phone": artist_query.phone,
        "website": artist_query.website,
        "facebook_link": artist_query.facebook_link,
        "seeking_venue": artist_query.seeking_venue,
        "seeking_description": artist_query.seeking_description,
        "image_link": artist_query.image_link,
        "past_shows": past_shows(shows),
        "upcoming_shows": upcoming_shows(shows),
        "past_shows_count": len(past_shows(shows)),
        "upcoming_shows_count": len(upcoming_shows(shows))
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist_obj = Artist.query.get(artist_id)
    artist_form = ArtistForm(obj=artist_obj)
    return render_template('forms/edit_artist.html', form=artist_form, artist=artist_obj)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        artist_form = ArtistForm()
        artist_obj = Artist.query.get(artist_id)
        artist_obj.name = artist_form.name.data
        artist_obj.city = artist_form.city.data
        artist_obj.state = artist_form.state.data
        artist_obj.phone = artist_form.phone.data
        artist_obj.genres = artist_form.genres.data
        artist_obj.facebook_link = artist_form.facebook_link.data
        artist_obj.website = artist_form.website.data
        artist_obj.image_link = artist_form.image_link.data
        artist_obj.seeking_venue = artist_form.seeking_venue.data
        artist_obj.seeking_description = artist_form.seeking_description.data
        db.session.commit()
        return redirect(url_for('show_artist', artist_id=artist_id))
    except Exception as e:
        print(f'Error ==> {e}')
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        db.session.rollback()
        return redirect(url_for('show_artist', artist_id=artist_id))
    finally:
        db.session.close()


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # TODO: populate form with values from venue with ID <venue_id>
    venue_query = Venue.query.filter_by(id=venue_id).first()
    venue_form = VenueForm(obj=venue_query)
    return render_template('forms/edit_venue.html', form=venue_form, venue=venue_query)



@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
        venue_form = VenueForm()
        venue_query = Venue.query.get(venue_id)
        venue_query.name = venue_form.name.data
        venue_query.city = venue_form.city.data
        venue_query.state = venue_form.state.data
        venue_query.address = venue_form.address.data
        venue_query.phone = venue_form.phone.data
        venue_query.genres = venue_form.genres.data
        venue_query.facebook_link = venue_form.facebook_link.data
        venue_query.website = venue_form.website.data
        venue_query.image_link = venue_form.image_link.data
        venue_query.seeking_talent = venue_form.seeking_talent.data
        venue_query.seeking_description = venue_form.seeking_description.data
        db.session.commit()
        return redirect(url_for('show_venue', venue_id=venue_id))
    except Exception as e:
        print(f'Error ==> {e}')
        flash('An error occurred. Venue ' + request.venue_form['name'] + ' could not be listed.')
        db.session.rollback()
        return redirect(url_for('show_venue', venue_id=venue_id))
    finally:
        db.session.close()


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        arists_form = ArtistForm()
        create_artist = Artist(
            name=arists_form.name.data,
            city=arists_form.city.data,
            state=arists_form.state.data,
            phone=arists_form.phone.data,
            genres=arists_form.genres.data,
            facebook_link=arists_form.facebook_link.data,
            website=arists_form.website.data,
            image_link=arists_form.image_link.data,
            seeking_venue=arists_form.seeking_venue.data,
            seeking_description=arists_form.seeking_description.data,
        )
        db.session.add(create_artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + create_artist.name + ' was successfully listed!')
        return render_template('pages/home.html')
    except Exception as e:
        flash(f"An error occurred. Artist {request.form['name']} could not be listed. Error: {e}")
        db.session.rollback()
        return render_template('pages/home.html')
    finally:
        db.session.close()



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    shows_query = Show.query.all()
    data = []
    for show in shows_query:
        show = {
            "venue_id": show.venue_id,
            "venue_name": db.session.query(Venue.name).filter_by(id=show.venue_id).first()[0],
            "artist_id": show.artist_id,
            "artist_image_link": db.session.query(Artist.image_link).filter_by(id=show.artist_id).first()[0],
            "start_time": str(show.start_time)
        }
        data.append(show)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    show_form = ShowForm()
    try:
        create_show = Show(
            venue_id=show_form.venue_id.data,
            artist_id=show_form.artist_id.data,
            start_time=show_form.start_time.data,
        )
        db.session.add(create_show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
        return render_template('pages/home.html')
    except Exception as e:
        flash(f'An error occurred. Show could not be listed. Error: {e}')
        db.session.rollback()
        return render_template('forms/new_show.html', form=show_form)
    finally:
        db.session.close()

def upcoming_shows(shows):
    upcoming = []

    for show in shows:
        if show.start_time > datetime.now():
            upcoming.append({
                "artist_id": show.artist_id,
                "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                "start_time": format_datetime(str(show.start_time))
            })
    return upcoming


def past_shows(shows):
    past = []

    for show in shows:
        if show.start_time < datetime.now():
            past.append({
                "artist_id": show.artist_id,
                "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                "start_time": format_datetime(str(show.start_time))
            })
    return past

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
