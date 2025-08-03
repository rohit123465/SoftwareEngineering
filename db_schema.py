from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date
from datetime import time

db = SQLAlchemy()



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(20))
    email = db.Column(db.String())
    notifications = db.relationship('Notification', backref='user', cascade='all, delete')
    verified = db.Column(db.Boolean())

    def __init__(self, username, password_hash, is_organiser, email, verified):  
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.verified = verified
   
    def get_id(self):
        return str(self.id)
    
class Follows(db.Model):
    userID=db.Column(db.Integer, primary_key=True)
    companyID=db.Column(db.Integer,primary_key=True)
    def __init__(self, userID , companyID):
        self.userID = userID
        self.companyID = companyID

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    read = db.Column(db.Boolean())

    def __init__(self, message, user_id, read):
        self.message = message
        self.user_id = user_id
        self.read = read

class Company(db.Model):
    companyID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    symbol = db.Column(db.String())
    industry = db.Column(db.String())
    country = db.Column(db.String())

    def __init__(self , name , symbol , industry , country):
        self.name=name
        self.symbol=symbol
        self.industry=industry
        self.country=country

class Article(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String())
    title = db.Column(db.String())
    author = db.Column(db.String())
    timeDate=db.Column(db.DateTime())
    score=db.Column(db.Integer())
    companyID=db.Column(db.Integer(),db.ForeignKey(Company.companyID))
    def __init__(self , url , title, author,  timeDate , score , companyID):
        self.url=url
        self.title=title
        self.author=author
        self.timeDate=timeDate
        self.score=score
        self.companyID=companyID




    

def dbinit():
    """users_list = [
        USER('Do even more stuff', date(2000, 12, 7), time(12, 00, 00), 2, 200)
    ]
    db.session.add_all(events_list)
        """
    print("init")



