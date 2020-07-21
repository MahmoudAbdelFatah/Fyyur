#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
import sys
from sqlalchemy import desc
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    #image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.String())
    seeking_description = db.Column(db.String())
    website = db.Column(db.String())
    seeking_talent = db.Column(db.Boolean, default=False)
    genres = db.Column(db.String())

    # Implement many to many relationship
    show = db.relationship('Show', backref='venues', lazy='dynamic')


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    address = db.Column(db.String(120))
    #image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.String())
    seeking_description = db.Column(db.String())
    website = db.Column(db.String())
    seeking_talent = db.Column(db.Boolean, default=False)

    # Implement many to many relationship
    show = db.relationship('Show', backref='artists', lazy='dynamic')



class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'venues.id'), nullable=False)
    beginning_time = db.Column(db.String())

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


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
    data = []
    venues = Venue.query.all()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%S:%M')
    current_state, current_city = '', ''
    for venue in venues:
        # num_shows is aggregated based on number of upcoming shows per venue.
        upcoming_shows = venue.show.filter(
            Show.beginning_time > current_time).all()
        if current_state != venue.state or current_city != venue.city:
            data.append({
                'city': venue.city,
                'state': venue.state,
                'venues': [{
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': len(upcoming_shows)
                }]
            })
        else:
            data[-1]['venues'].append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcoming_shows)
            })

    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    # implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term')
    search_result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))
    response = {
        'count': search_result.count(),
        'data': search_result
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    shows = venue.show.filter(venue_id==venue_id).all()

    upcoming_shows = []
    past_shows = []
    for show in shows:
        artist_data = {
            'artist_id': show.artist_id,
            'artist_name': show.artists.name,
            # 'artist_image_link': show.Artist.image_link,
            'start_time': format_datetime(show.beginning_time)
        }
        time = datetime.strptime(show.beginning_time, '%Y-%m-%d %H:%M:%S')
        if time > datetime.now():
            upcoming_shows.append(artist_data)
        else:
            past_shows.append(artist_data)
    venue_data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        # "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),

    }
    return render_template('pages/show_venue.html', venue=venue_data)
    
#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        genres = request.form['genres']
        #image_link= request.form['image_link']
        facebook_link = request.form['facebook_link']
        #seeking_venue = request.form['seeking_venue']
        #website = request.form['website']
        #seeking_talent = request.form['seeking_talent']
        venue = Venue(name=name, city=city, state=state, phone=phone,
                      genres=genres, facebook_link=facebook_link)
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return redirect(url_for('create_venue_form'))
    except:
        db.session.rollback()
        print(sys.exc_info())
        return render_template('errors/404.html')
    finally:
        return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
        return render_template('errors/404.html')
    finally:
        return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    artists = Artist.query.all()
    data = []
    for artist in artists:
        temp = {
            'id': artist.id,
            'name': artist.name
        }
        data.append(temp)
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term')
    search_result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
    response = {
        'count': search_result.count(),
        'data': search_result
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get(artist_id)
    shows = artist.show.filter(artist_id==artist_id).all()

    upcoming_shows = []
    past_shows = []
    for show in shows:
        artist_data = {
            'artist_id': show.artist_id,
            'artist_name': show.artists.name,
            # 'artist_image_link': show.Artist.image_link,
            'start_time': format_datetime(show.beginning_time)
        }
        time = datetime.strptime(show.beginning_time, '%Y-%m-%d %H:%M:%S')
        if time > datetime.now():
            upcoming_shows.append(artist_data)
        else:
            past_shows.append(artist_data)
    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "address": artist.address,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_talent": artist.seeking_talent,
        "seeking_description": artist.seeking_description,
        # "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),

    }
    return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    returned_artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        # "image_link": artist.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=returned_artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        updated_artist = Artist.query.get(artist_id)
        updated_artist.name = request.form['name']
        updated_artist.city = request.form['city']
        updated_artist.state = request.form['state']
        updated_artist.phone = request.form['phone']
        updated_artist.genres = request.form['genres']
        #updated_artist.image_link = request.form['image_link']
        updated_artist.facebook_link = request.form['facebook_link']
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return redirect(url_for('show_artist', artist_id=artist_id))
    except:
        db.session.rollback()
        print(sys.exc_info())
        return render_template('errors/404.html')


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    returned_venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_venue": venue.seeking_venue,
        "seeking_description": venue.seeking_description,
        # "image_link": venue.image_link
    }

    return render_template('forms/edit_venue.html', form=form, venue=returned_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
        updated_venue = Venue.query.get(venue_id)
        updated_venue.name = request.form['name']
        updated_venue.city = request.form['city']
        updated_venue.state = request.form['state']
        updated_venue.phone = request.form['phone']
        updated_venue.genres = request.form['genres']
        updated_venue.image_link = request.form['image_link']
        updated_venue.facebook_link = request.form['facebook_link']
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return redirect(url_for('show_venue', venue_id=venue_id))

    except:
        db.session.rollback()
        print(sys.exc_info())
        return render_template('errors/404.html')

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # modify data to be the data object returned from db insertion

    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        genres = request.form['genres']
        #image_link= request.form['image_link']
        facebook_link = request.form['facebook_link']
        #seeking_venue = request.form['seeking_venue']
        #website = request.form['website']
        #seeking_talent = request.form['seeking_talent']
        artist = Artist(name=name, city=city, state=state,
                        phone=phone, genres=genres, facebook_link=facebook_link)
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return redirect(url_for('create_artist_form'))
    except:
        db.session.rollback()
        print(sys.exc_info())
        return render_template('errors/404.html')
    finally:
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows = Show.query.order_by(desc(Show.beginning_time))
    show_data = []
    for show in shows:
        temp = {
            'venue_id': show.venue_id,
            'venue_name': show.venues.name,
            'artist_id': show.artist_id,
            'artist_name': show.artists.name,
            # 'artist_image_link': show.Artist.image_link,
            'start_time': show.beginning_time
        }
        show_data.append(temp)
    return render_template('pages/shows.html', shows=show_data)

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    try:
        venue_id = request.form['venue_id']
        artist_id = request.form['artist_id']
        beginning_time = request.form['start_time']
        show = Show(artist_id=artist_id, venue_id=venue_id,
                    beginning_time=beginning_time)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
        return render_template('pages/home.html')
    except:
        db.session.rollback()
        flash('Show was unsuccessfully listed!')
        return render_template('errors/404.html')


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
# if __name__ == '__main__':
#    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
