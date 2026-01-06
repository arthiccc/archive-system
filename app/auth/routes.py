from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import AdminUser
from app.extensions import login_manager
from . import auth
from .forms import LoginForm, SetupForm


@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    first_user = AdminUser.query.count() == 0
    form = SetupForm() if first_user else LoginForm()

    if form.validate_on_submit():
        if first_user:
            user = AdminUser(
                username=form.username.data,
                full_name=form.full_name.data,
                email=form.email.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Admin account created successfully!", "success")
        else:
            user = AdminUser.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                if not user.is_active:
                    flash("Your account has been deactivated.", "danger")
                else:
                    user.last_login = db.func.now()
                    db.session.commit()
                    login_user(user)
                    next_page = request.args.get("next")
                    flash("Logged in successfully!", "success")
                    return (
                        redirect(next_page)
                        if next_page
                        else redirect(url_for("admin.dashboard"))
                    )
            else:
                flash("Invalid username or password.", "danger")

    return render_template("auth/login.html", form=form, first_user=first_user)


@auth.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
