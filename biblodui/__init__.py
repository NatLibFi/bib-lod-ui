from flask import Flask

app = Flask(__name__)
from biblodui import views, model
