import os
import json
import logging
from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.inspection import inspect
from dotenv import load_dotenv
load_dotenv()


server = Flask(__name__)
auth = HTTPBasicAuth()
server.logger.setLevel(logging.INFO)
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
server.config['SECRET_KEY'] = os.getenv("APP_PASS")
db = SQLAlchemy(server)

users = {
    os.getenv('MANAGEMENT_USER') : generate_password_hash(os.getenv('MANAGEMENT_PASS')),
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

class Serializer(object):

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]

class Card(db.Model):
    UID = db.Column(db.String(8), primary_key=True)

    def __repr__(self) -> str:
        return str(self.UID)

    def serialize(self):
        d = Serializer.serialize(self)
        return d

cards = [os.getenv('CARD1'), os.getenv('CARD2')]

db.create_all()
try:
    for card in cards:
        db.session.add(Card(UID=card))

    db.session.commit()

except Exception as e:
    print(e)

@server.route("/")
def hello():
    return "Get off my property!"

@server.route("/validate", methods=['POST'])
def log():
    server.logger.info(request.json)
    return "OK", 200

@server.route("/sync")
def sync():
    cards = Card.query.all()
    card_list = []
    for card in cards:
        card_list.append(card.serialize())
    return json.dumps(card_list), 200

@server.route("/manage")
@auth.login_required
def manage():
    cards = Card.query.all()
    return render_template("manage.html", len = len(cards), cards = cards)

@server.route("/add", methods=['POST'])
@auth.login_required
def add():
    new_id = request.form.get("uid")
    if len(new_id) == 8:
        try:
            db.session.add(Card(UID=new_id))
            db.session.commit()
            server.logger.info("Added access to: " + new_id)
        except Exception as e:
            server.logger.error(e)

    return redirect("/manage")

@server.route("/delete", methods=['GET'])
@auth.login_required
def delete():
    delete_uid = request.args.get("delete")
    card = Card.query.filter_by(UID=delete_uid).first()
    db.session.delete(card)
    db.session.commit()
    return redirect("/manage")

if __name__ == "__main__":
    server.run(host='0.0.0.0')