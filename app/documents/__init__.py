from flask import Blueprint

documents = Blueprint("documents", __name__, template_folder="templates")

from . import routes
