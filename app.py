from flask import Flask, render_template, request, redirect, url_for, flash

from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Use environment variable for secret key in production, random for development
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

db_path = os.path.join(os.path.dirname(__file__), 'currency.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



@app.route('/manage_collection', methods=['GET', 'POST'])
def manage_collection():
    places = Place.query.all()
    currencies = Currency.query.all()
    items = Collection.query.all()

    action = request.args.get('action', 'add')  # default action

    if request.method == 'POST':
        # Handle adding new place
        if action == 'add_place':
            place_name = request.form.get('place_name')
            is_country = request.form.get('is_country', 'N')
            if place_name:
                new_place = Place(name=place_name, country=is_country)
                db.session.add(new_place)
                db.session.commit()
                flash(f"Place '{place_name}' added successfully!")
                return redirect(url_for('manage_collection', action=action))
        
        # Handle editing place
        elif action == 'edit_place':
            place_id = request.form.get('place_id')
            place_name = request.form.get('place_name')
            is_country = request.form.get('is_country', 'N')
            if place_id and place_name:
                place = Place.query.get(place_id)
                if place:
                    place.name = place_name
                    place.country = is_country
                    db.session.commit()
                    flash(f"Place '{place_name}' updated successfully!")
                    return redirect(url_for('manage_collection', action=action))
        
        # Handle deleting place
        elif action == 'delete_place':
            place_id = request.form.get('place_id')
            if place_id:
                place = Place.query.get(place_id)
                if place:
                    place_name = place.name
                    db.session.delete(place)
                    db.session.commit()
                    flash(f"Place '{place_name}' deleted successfully!")
                    return redirect(url_for('manage_collection', action=action))
        
        # Handle adding new currency
        elif action == 'add_currency':
            currency_code = request.form.get('currency_code')
            currency_name = request.form.get('currency_name')
            place_ids = request.form.getlist('place_ids')
            
            if currency_code and currency_name and place_ids:
                new_currency = Currency(code=currency_code, name=currency_name)
                db.session.add(new_currency)
                db.session.flush()  # Get the currency_id before commit
                
                # Add place associations
                for place_id in place_ids:
                    place = Place.query.get(place_id)
                    if place:
                        new_currency.countries.append(place)
                
                db.session.commit()
                flash(f"Currency '{currency_name}' added successfully!")
                return redirect(url_for('manage_collection', action=action))
            else:
                flash("Please fill all required fields including at least one place.")
                return redirect(url_for('manage_collection', action=action))
        
        # Handle editing currency
        elif action == 'edit_currency':
            currency_id = request.form.get('currency_id')
            currency_code = request.form.get('currency_code')
            currency_name = request.form.get('currency_name')
            place_ids = request.form.getlist('place_ids')
            
            if currency_id and currency_code and currency_name and place_ids:
                currency = Currency.query.get(currency_id)
                if currency:
                    currency.code = currency_code
                    currency.name = currency_name
                    
                    # Update place associations
                    currency.countries = []
                    for place_id in place_ids:
                        place = Place.query.get(place_id)
                        if place:
                            currency.countries.append(place)
                    
                    db.session.commit()
                    flash(f"Currency '{currency_name}' updated successfully!")
                    return redirect(url_for('manage_collection', action=action))
            else:
                flash("Please fill all required fields including at least one place.")
                return redirect(url_for('manage_collection', action=action))
        
        # Handle deleting currency
        elif action == 'delete_currency':
            currency_id = request.form.get('currency_id')
            if currency_id:
                currency = Currency.query.get(currency_id)
                if currency:
                    currency_name = currency.name
                    db.session.delete(currency)
                    db.session.commit()
                    flash(f"Currency '{currency_name}' deleted successfully!")
                    return redirect(url_for('manage_collection', action=action))
        
        # Handle collection items
        else:
            # Get form data
            selected_item_id = request.form.get('item_id')
            currency_id = request.form.get('currency_id')
            place_id = request.form.get('place_id')
            amount = request.form.get('amount', 0)
            type_ = request.form.get('type')
            source = request.form.get('source', '')
            years = request.form.get('years', '')

            if action == 'add':
                new_item = Collection(
                    currency_id=currency_id,
                    place_id=place_id,
                    amount=amount,
                    type=type_,
                    source=source,
                    years=years
                )
                db.session.add(new_item)
                flash("Item added successfully!")

            elif action == 'edit' and selected_item_id:
                item = Collection.query.get(selected_item_id)
                if item:
                    item.currency_id = currency_id
                    item.place_id = place_id
                    item.amount = amount
                    item.type = type_
                    item.source = source
                    item.years = years
                    flash("Item updated successfully!")

            elif action == 'delete' and selected_item_id:
                item = Collection.query.get(selected_item_id)
                if item:
                    db.session.delete(item)
                    flash("Item deleted successfully!")

            db.session.commit()
            return redirect(url_for('manage_collection', action=action))

    return render_template(
        'manage_collection.html',
        action=action,
        items=items,
        places=places,
        currencies=currencies
    )

class Collection(db.Model):
    __tablename__ = 'collection_item'

    id = db.Column('item_id', db.Integer, primary_key=True)

    currency_id = db.Column(
        db.Integer,
        db.ForeignKey('currency.currency_id'),
        nullable=False
    )

    place_id = db.Column(
        db.Integer,
        db.ForeignKey('place.place_id'), 
        nullable=False
    )

    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(10))
    source = db.Column(db.String)
    years = db.Column(db.String(50))  

    currency = db.relationship('Currency', backref='collections')
    place = db.relationship('Place', backref='collections')


class PlaceCurrency(db.Model):
    __tablename__ = 'place_currency'

    place_id = db.Column(
        db.Integer,
        db.ForeignKey('place.place_id'),
        primary_key=True
    )

    currency_id = db.Column(
        db.Integer,
        db.ForeignKey('currency.currency_id'),
        primary_key=True
    )


class Place(db.Model):
    __tablename__ = 'place'

    place_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    country = db.Column(db.String(5))  # Y/N

    currencies = db.relationship(
        'Currency',
        secondary='place_currency',
        backref='countries'
    )

    def __repr__(self):
        return f"<Place {self.name}>"


class Currency(db.Model):
    __tablename__ = 'currency'

    currency_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10))
    name = db.Column(db.String(120))

    def __repr__(self):
        return f"<Currency {self.code}>"



@app.route('/')
def home():
    total_collections = Collection.query.count()
    total_countries = Place.query.filter_by(country='Y').count()
    collected_countries = Place.query.filter_by(country='Y').filter(Place.collections.any()).count()
    
    # Use func.lower to make case-insensitive comparison
    from sqlalchemy import func
    collected_countries_coins = Place.query.filter_by(country='Y').filter(
        Place.collections.any(func.lower(Collection.type) == 'coin')
    ).count()
    collected_countries_notes = Place.query.filter_by(country='Y').filter(
        Place.collections.any(func.lower(Collection.type) == 'note')
    ).count()
    
    # Calculate currency statistics
    total_currencies = Currency.query.count()
    collected_currencies = Currency.query.filter(Currency.collections.any()).count()
    
    return render_template('index.html', 
                         total_collections=total_collections,
                         collected_countries=collected_countries,
                         total_countries=total_countries,
                         collected_countries_coins=collected_countries_coins,
                         collected_countries_notes=collected_countries_notes,
                         total_currencies=total_currencies,
                         collected_currencies=collected_currencies)

@app.route('/collection')
def collection():
    # Get type from query param, default to 'note'
    filter_type = request.args.get('type', 'note').lower()  # always lowercase

    # Only allow 'coin' or 'note'
    if filter_type not in ['coin', 'note']:
        filter_type = 'note'

    # Query filtered by type (case-insensitive)
    items = Collection.query.filter(Collection.type.ilike(filter_type)).all()

    return render_template('collection.html', items=items, filter_type=filter_type)


@app.route('/countries')
def countries():
    try:
        # Only places where country='Y'
        countries_list = Place.query.filter_by(country='Y').all()
    except Exception as e:
        print('DB query error:', e)
        countries_list = []

    return render_template('countries.html', countries=countries_list)


@app.route('/currency/<int:currency_id>')
def currency_detail(currency_id):
    from sqlalchemy import func
    
    currency = Currency.query.get_or_404(currency_id)
    
    # Get all countries that use this currency
    countries_using = currency.countries
    
    # Check if we have collected coins for this currency
    has_coins = Collection.query.filter(
        Collection.currency_id == currency_id,
        func.lower(Collection.type) == 'coin'
    ).count() > 0
    
    # Check if we have collected notes for this currency
    has_notes = Collection.query.filter(
        Collection.currency_id == currency_id,
        func.lower(Collection.type) == 'note'
    ).count() > 0
    
    # Get all collection items for this currency
    collected_items = Collection.query.filter_by(currency_id=currency_id).all()
    
    return render_template('currency_detail.html',
                         currency=currency,
                         countries=countries_using,
                         has_coins=has_coins,
                         has_notes=has_notes,
                         collected_items=collected_items)


if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Only use debug mode locally
    app.run(debug=True, port=5000)