from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, URL
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash


# WTForms
class CafeForm(FlaskForm):
    name = StringField("Name of Cafe:", validators=[DataRequired()])
    map_url = StringField("Map URL:", validators=[DataRequired(), URL()])
    img_url = StringField("Image URL:", validators=[DataRequired(), URL()])
    location = StringField("Locality:", validators=[DataRequired()])
    has_sockets = BooleanField("Has Sockets?:")
    has_toilet = BooleanField("Has Toilets?:")
    has_wifi = BooleanField("Has Wifi?:")
    can_take_calls = BooleanField("Can Take Calls?:")
    seats = StringField("No of Seats:", validators=[DataRequired()])
    coffee_price = StringField("Coffee Price:", validators=[DataRequired()])
    submit = SubmitField("Submit Cafe")


class LoginForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Log Me In")


class RegisterForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])
    repeat_password = PasswordField("Repeat Password:", validators=[DataRequired()])
    submit = SubmitField("Register Me")


# Flask App Initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Flask is good. Python is King'
bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# DB creation
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///cafes.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Table creation
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    has_sockets = db.Column(db.Boolean(250), nullable=False)
    has_toilet = db.Column(db.Boolean(250), nullable=False)
    has_wifi = db.Column(db.Boolean(250), nullable=False)
    can_take_calls = db.Column(db.Boolean(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    coffee_price = db.Column(db.String(250), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    poster = relationship("User", back_populates="cafes")


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    cafes = relationship("Cafe", back_populates="poster")


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    all_cafes = db.session.query(Cafe).all()[::-1]
    return render_template("index.html", cafe_list=all_cafes, current_user=current_user)


@app.route('/details')
def details():
    the_cafe = Cafe.query.get(request.args.get('cafe_id'))
    return render_template("details.html", cafe=the_cafe, current_user=current_user)


@app.route("/edit/<int:cafe_id>", methods=["GET", "POST"])
def edit(cafe_id):
    the_cafe = Cafe.query.get(cafe_id)
    edit_form = CafeForm(
        name=the_cafe.name,
        map_url=the_cafe.map_url,
        img_url=the_cafe.img_url,
        location=the_cafe.location,
        has_sockets=the_cafe.has_sockets,
        has_toilet=the_cafe.has_toilet,
        has_wifi=the_cafe.has_wifi,
        can_take_calls=the_cafe.can_take_calls,
        seats=the_cafe.seats,
        coffee_price=the_cafe.coffee_price
    )

    if edit_form.validate_on_submit():
        the_cafe.name = edit_form.name.data
        the_cafe.map_url = edit_form.map_url.data
        the_cafe.img_url = edit_form.img_url.data
        the_cafe.location = edit_form.location.data
        the_cafe.has_sockets = edit_form.has_sockets.data
        the_cafe.has_toilet = edit_form.has_toilet.data
        the_cafe.has_wifi = edit_form.has_wifi.data
        the_cafe.can_take_calls = edit_form.can_take_calls.data
        the_cafe.seats = edit_form.seats.data
        the_cafe.coffee_price = edit_form.coffee_price.data
        db.session.commit()

        return render_template("details.html", cafe=the_cafe)

    if the_cafe.poster_id != current_user.id:
        flash("You can only edit cafes that you posted!")
        return render_template("details.html", cafe=the_cafe)


    return render_template("edit.html", form=edit_form, cafe=the_cafe, current_user=current_user)


@app.route('/add', methods=["GET", "POST"])
def add():
    add_form = CafeForm()
    if add_form.validate_on_submit():
        new_cafe = Cafe(
            name=add_form.name.data,
            map_url=add_form.map_url.data,
            img_url=add_form.img_url.data,
            location=add_form.location.data,
            has_sockets=add_form.has_sockets.data,
            has_toilet=add_form.has_toilet.data,
            has_wifi=add_form.has_wifi.data,
            can_take_calls=add_form.can_take_calls.data,
            seats=add_form.seats.data,
            coffee_price=add_form.coffee_price.data,
            poster = current_user
        )

        db.session.add(new_cafe)
        db.session.commit()

        return render_template("details.html", cafe=new_cafe)

    return render_template("add.html", form=add_form)


@app.route('/login' , methods=["GET", "POST"])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data

        user = User.query.filter_by(username=username).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That username does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=login_form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():

        if User.query.filter_by(username=register_form.username.data).first():
            # User already exists
            flash("You've already signed up with that username, log in instead!")
            return redirect(url_for('login'))

        if register_form.password.data != register_form.repeat_password.data:
            flash("Your passwords do not match! Try again")
            return redirect(url_for('register'))

        hash_and_salted_password = generate_password_hash(
            register_form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            username=register_form.username.data,
            password=hash_and_salted_password,
            status=0
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", form=register_form, current_user=current_user)


if __name__ == "__main__":
    app.run(debug=True)
