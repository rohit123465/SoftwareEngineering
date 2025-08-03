from flask_mail import Mail
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from db_schema import db, User, Notification, Article, dbinit, Follows, Company
from flask import Flask, render_template, url_for, session, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug import security
import os
import company as companyClass
import article as articleClass
import requests
import random
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///csEvent.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# required for flask-login (flask-login makes user authentication much easier - e.g. 'is_authenticated' property)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/"

app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
# random new gmail account I made to send verif emails from
app.config['MAIL_USERNAME'] = 'r39288755@gmail.com'
app.config['MAIL_PASSWORD'] = 'lcxu dssl bwnj vkem'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True


# make the mail handler
mail = Mail(app)

db.init_app(app)
app.secret_key = 'anything'

# change this to False to avoid resetting the database every time this app is restarted
resetdb = False
if resetdb:
    with app.app_context():
        # drop everything, create all the tables, then put some data into the tables
        db.drop_all()
        db.create_all()
        dbinit()

# Set this to true to reset and re-populate the DB
# NOTE: This takes a long time ._.
# It may be worth optimising in the future, since all of the articles/companies can be worked on in parallel, and it takes 20 minutes...
# Since it should only be a 1-time thing, I'm electing to not do that and instead let my pc idle it in the background :)
populate: bool = False

with app.app_context(): 
    if populate:
        db.drop_all()
        db.create_all()
        db.session.commit()
    
        with open("companies.txt", "r") as companies:
            articles: list[Article] = []
            s = requests.Session()
            for symbol in companies:
                symbol = symbol.strip()
                print(symbol)
                c: companyClass.Company = companyClass.Company(symbol, s)
                comp = Company(c.name, c.symbol, c.industry, c.country)
                db.session.add(comp)
                db.session.flush()
                db.session.refresh(comp)
                for a in c.articles:
                    articles.append(Article(a.url, a.title, a.author, a.date, a.evaluation, comp.companyID))
            db.session.add_all(articles)
            db.session.commit()
            
    try:
        password_hash = security.generate_password_hash("person")
        u: User = User("person", password_hash, False, "guy@guy.com", True)
        db.session.add(u)
        db.session.commit()
    except:
        print("temp user already in DB")

##################################
### FRONT-END HELPER FUNCTIONS ###
##################################

def companies_following(userID: int) -> list[dict]:
    list = []
    following = Follows.query.filter_by(userID=userID).all()
    for f in following:
        company = Company.query.filter_by(companyID=f.companyID).first()
        if company is not None:
            list.append({"name": company.name, "symbol": company.symbol})          
            
    return list


def recent_notifications(userID: int) -> list[str]:
    list = []
    notifs = Notification.query.filter_by(user_id=userID, read=False).all()
    for n in notifs:
        list.append(n.message)
        n.read = True
        
    db.session.commit()
    
    return list
        

def all_notifications(userID: int) -> list[str]:
    list = []
    notifs = Notification.query.filter_by(user_id=userID).all()
    for n in notifs:
        list.append(n.message)
    
    return list


def user_recommendations(userID: int) -> list[dict]:
    followed = Follows.query.filter_by(userID=userID).all()
    followedIDs = []
    industries = []
    countries = []
    for f in followed:
        followedIDs.append(f.companyID)
        c = Company.query.filter_by(companyID=f.companyID).first()
        industries.append(c.industry)
        countries.append(c.country)
        
    companies = Company.query.all()
    recommendations = []
    for c in companies:
        if (c.companyID not in followedIDs) and ((c.industry in industries) or (c.country in countries)):
            recommendations.append(c)
    
    for r in recommendations:
        companies.remove(r)
    
    while len(recommendations) < 5:
        rand = random.randint(0, len(companies) - 1)
        recommendations.append(companies[rand])
        companies.remove(companies[rand])
        
    while len(recommendations) > 5:
        rand = random.randint(0, len(recommendations) - 1)
        recommendations.remove(recommendations[rand])
        
    return recommendations

def normalise_score(score: float) -> float:
    return round(((score + 1) / 2 * 10), 2)


def recent_score(symbol: str) -> dict:
    comp = Company.query.filter_by(symbol = symbol).first()
    
    # if the company doesn't exist in the db
    if comp == None:
        return None
    
    articles = Article.query.filter_by(companyID = comp.companyID).all()
    
    # if the company has no articles
    if len(articles) == 0:
        return None
    
    # calculate the average and most recent scores for this company's articles
    total_score = 0
    recent_score = 0
    recent_date = datetime.min
    for a in articles:
        total_score = total_score + a.score
        if recent_date < a.timeDate:
            recent_score = normalise_score(a.score)
            recent_date = a.timeDate
    average_score = normalise_score(total_score / len(articles))
    percentage_difference = round((recent_score - average_score) / average_score * 100, 2)
    return {"percentage": percentage_difference, "recent": recent_score}

def industry_average(symbol: str) -> dict:
    comp = Company.query.filter_by(symbol = symbol).first()
    
    # if the company doesn't exist in the db
    if comp == None:
        return None
    
    # calculate the industry average score by averaging the average score of each company
    # this avoids biasing the industry average towards companies with more articles present in the db
    industry_companies = Company.query.filter_by(industry = comp.industry).all()
    industry_avgs = []
    for ic in industry_companies:
        articles = Article.query.filter_by(companyID = ic.companyID).all()
        total = 0
        for a in articles:
            total = total + a.score
        if len(articles) > 0:
            industry_avgs.append(total/len(articles))
    
    industry_average = 0
    for item in industry_avgs:
        industry_average = industry_average + item
    industry_average = normalise_score(industry_average / len(industry_avgs))
    
    # calculate the company average score
    total_score = 0
    company_articles = Article.query.filter_by(companyID = comp.companyID).all()
    for ca in company_articles:
        total_score = total_score + ca.score
    
    if len(company_articles) > 0:
        company_average = normalise_score(total_score / len(company_articles))
    else:
        company_average = 0
    
    percentage_difference = round((company_average - industry_average) / industry_average * 100, 2)
    return {"percentage": percentage_difference, "company_average": company_average}


def user_feed(userID: int) -> list[dict]:
    list = []
    following = Follows.query.filter_by(userID=userID).all()
    for f in following:
        company = Company.query.filter_by(companyID=f.companyID).first()
        articles = Article.query.filter_by(companyID=f.companyID).all()
        for a in articles:
            score = normalise_score(a.score)
            list.append({"company_name": company.name, "symbol": company.symbol, "industry": company.industry, "country": company.country, "url": a.url, "title":a.title, "author":a.author, "date": a.timeDate, "score": score})
            
    return list


def company_news(symbol: str) -> list[dict]:
    company = Company.query.filter_by(symbol=symbol).first()
    list = []
    if company is None:
        # company does not exist in DB
        return list
    else:
        articles = Article.query.filter_by(companyID=company.companyID)
        for a in articles:
            score = normalise_score(a.score)
            list.append({"url": a.url, "title":a.title, "author":a.author, "date": a.timeDate, "score": score})
            
    return list


def get_company(symbol: str) -> dict:
    company = Company.query.filter_by(symbol=symbol).first()
    if company is None:
        # company does not exist in DB
        return None
    else:
        return {
            "name": company.name,
            "symbol": company.symbol,
            "industry": company.industry,
            "country": company.country
        }


def follow(symbol: str, userID: int) -> None:
    company = Company.query.filter_by(symbol=symbol).first()
    if company is None:
        return
    else:
        follow = Follows(userID=userID, companyID=company.companyID)
        with app.app_context():
            db.session.add(follow)
            db.session.commit()


def unfollow(symbol: str, userID: int) -> None:
    company = Company.query.filter_by(symbol=symbol).first()
    if company is None:
        return
    else:
        follow = Follows.query.filter_by(userID=userID, companyID=company.companyID).first()
        with app.app_context():
            current_db = db.session.object_session(follow)
            current_db.delete(follow)
            current_db.commit()


def search(query: str) -> list[dict]:
    list = []
    companies = Company.query.all()
    for company in companies:
        if (str(company.name).lower().find(query.lower()) != -1) or (str(company.symbol).lower().find(query.lower()) != -1):
            list.append({"name": company.name, "symbol": company.symbol})

    return list


def scoresort(e: dict):
    return e["score"]


def datesort(e: dict):
    return e["date"]

######################################
### FRONT-END HELPER FUNCTIONS END ###
######################################

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


@app.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return render_template("index.html")
    feed = user_feed(current_user.id)
    recommendations = user_recommendations(current_user.id)
    recent_notifs = recent_notifications(current_user.id)
    for n in recent_notifs:
        flash(n)
    
    # the following code was written at 5am on a deadline.
    # it does not need to be fast.
    # please ignore how terribly written it is.
    # i hate remove items from the construct i am iterating on,
    # and i am too tired to bother to write a nicer solution to that problem.
    finalfeed = feed.copy()
    
    if request.method == "POST":
        if request.form.to_dict()["filter-order"] == "score":
            finalfeed.sort(key=scoresort, reverse=True)
        else:
            finalfeed.sort(key=datesort, reverse=True)
        if request.form.to_dict()["filter-industry"] != "All":
            for item in feed:
                if item["industry"] != request.form.to_dict()["filter-industry"]:
                    finalfeed.remove(item)
        feed = finalfeed.copy()
        try:
            if int(request.form.to_dict()["filter-score"]) > 0:
                for item in feed:
                    if item["score"] < int(request.form.to_dict()["filter-score"]):
                        finalfeed.remove(item)
        except Exception as e:
            print(f"FILTER-SCORE WAS NOT SET TO AN INTEGER VALUE: {e}")
        feed = finalfeed.copy()
        if request.form.to_dict()["filter-symbol"] != "":
            for item in feed:
                if str(item["symbol"]).lower() != request.form.to_dict()["filter-symbol"].lower():
                    finalfeed.remove(item)
        feed = finalfeed.copy()
        if request.form.to_dict()["filter-date"] != "":
            date_format = "%Y-%m-%d"
            date = datetime.strptime(request.form.to_dict()["filter-date"], date_format)
            for item in feed:
                if item["date"].year != date.year or item["date"].month != date.month or item["date"].day != date.day:
                    finalfeed.remove(item)
        feed = finalfeed.copy()
        if request.form.to_dict()["filter-location"] != "all":
            for item in feed:
                if request.form.to_dict()["filter-location"] == "United States":
                    if item["country"] != "United States":
                        finalfeed.remove(item)
                if request.form.to_dict()["filter-location"] == "Ireland":
                    if item["country"] != "Ireland":
                        finalfeed.remove(item)
                if request.form.to_dict()["filter-location"] == "India":
                    if item["country"] != "India":
                        finalfeed.remove(item)
    return render_template("index.html", feed=finalfeed, recommendations=recommendations, recent_notifs=recent_notifs)


@app.route('/follow', methods=['POST'])
@login_required
def follow_company():
    symbol = request.json['symbol']
    follow(symbol, current_user.id)
    return "success"


@app.route('/unfollow', methods=['POST'])
@login_required
def unfollow_company():
    symbol = request.json['symbol']
    unfollow(symbol, current_user.id)
    return "success"


# When the 'submit' button on the login form is pressed, get the POSTed values and
# call the 'try_to_log_user_in()' function
# NOTE: I decided to use POST rather than get when dealing with sensitive data, as if
# I used 'GET' the user's password would be visible in the URL, unlike POST. Therefore,
# using 'POST' makes the database more secure.


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')

    if request.method == "GET":
        return render_template('/login.html')

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        # After the user enters their username and password when logging in -
        # log them in if the details are correct; otherwise redirect them back
        # to the login page with an error message
        # returns the User row in the database with the given id as a parameter.
        # (required for flask-login to work)

        if user is None:
            return render_template('/login.html', login_fail=True)
        elif not security.check_password_hash(user.password_hash, password):
            return render_template('/login.html', login_fail=True)
        elif not bool(user.verified):
            print("User not verified")
            return render_template('/login.html', login_fail=True)
        else:
            print("LOGIN")
            login_user(user)
            return redirect("/")


# When the submit button on the 'register_new_user' form is pressed, get the POSTed values,
# generate a new row in the 'USER' table with the given information, then call the 'send_verification_email'
# function

@app.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('/register.html')

@app.route('/companies-following')
@login_required
def companies_following_page():
    companies = companies_following(current_user.id)
    return render_template('/companies-following.html', companies=companies)

@app.route('/notifications')
@login_required
def notifications():
    notifications = all_notifications(current_user.id)
    return render_template('/notifications.html', notifications=notifications)

@app.route('/company/<company_symbol>')
@login_required
def company(company_symbol):
    articles = company_news(company_symbol)
    company = get_company(company_symbol)
    recent_score_data = recent_score(company_symbol)
    industry_average_data = industry_average(company_symbol)
    is_following = False
    sentiment_analysis = {"positive": 0, "neutral": 0, "negative": 0}
    for a in articles:
        if a["score"] > 7:
            sentiment_analysis["positive"] = sentiment_analysis["positive"] + 1
        elif a["score"] > 4:
            sentiment_analysis["neutral"] = sentiment_analysis["neutral"] + 1
        else:
            sentiment_analysis["negative"] = sentiment_analysis["negative"] + 1
    # check if the user is following the company
    if Follows.query.filter_by(userID=current_user.id).filter_by(companyID=Company.query.filter_by(symbol=company_symbol).first().companyID).first() is not None:
        is_following = True
    return render_template('/company.html', company_symbol=company_symbol, articles=articles,
                            company=company, is_following=is_following, sentiment_analysis=sentiment_analysis,
                            recent_score=recent_score_data, industry_average=industry_average_data)

@app.route('/search')
@login_required
def realtime_search():
    query = request.args.get('query')
    results = search(query)
    return results


@app.route('/register_new_user', methods=['POST'])
def register_new_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')

        if password != confirm_password:
            return render_template('/register.html', confirm_password_fail=True)
        

        special_chars = '[@_!#$%^&*()<>?/\|}{~:]' 
        digits = '1234567890'
        has_special_char = False
        has_number = False
        for letter in password:
                if letter in special_chars:
                    has_special_char = True
                elif letter in digits:
                    has_number = True
                if has_special_char and has_number:
                    break

        if len(password) < 8 or password.upper() == password or password.lower() == password or has_special_char == False or has_number == False:
            return render_template('/register.html', password_strength_fail=True)
        
        user_in_database_by_username = User.query.filter_by(
            username=username).first()

        if user_in_database_by_username is not None:
             # delete unverified users with same username from database
            User.query.filter_by(username=username, verified = False).delete()

            db.session.commit()

            user_in_database_by_username = User.query.filter_by(
            username=username).first()

            # If there exists a verfied user with the same username, display fail message
            if user_in_database_by_username is not None:
                return render_template('/register.html', username_not_unique=True)

        user_in_database_by_email = User.query.filter_by(email=email).first()
        if user_in_database_by_email is not None:
           
            # delete unverified users with same email from db
            User.query.filter_by(email=email, verified = False).delete()

            db.session.commit()

            user_in_database_by_email= User.query.filter_by(
            email=email).first()

            # If there exists a verfied user with the same email, display fail message
            if user_in_database_by_email is not None:
                 return render_template('/register.html', email_not_unique=True)
        


        # password is hashed, so if database is accessed, hackers can't
        # access user's accounts as a hash of the password is stored in the database
        # return render_template('/index.html', login_fail=True, login_page=True)
        password_hash = security.generate_password_hash(password)
        new_user = User(username=username, password_hash=password_hash,
                        is_organiser=False, email=email, verified=False)

        db.session.add(new_user)
        db.session.commit()

        return send_verification_email(email, username)


# Send a code based on a hash of a given email address as a parameter to a user.
# This code is used to verify the user's email. Then, direct them to a page where they
# are asked to verify their email.
def send_verification_email(email, username):
    recipients = [email]

    email_hash = security.generate_password_hash(email)
    # The code for a 6-character slice of the hash.
    session['code'] = email_hash[21:28]
    # allows me to use it in the next f-string (body)
    local_code = session['code']

    mail.send_message(sender='noreply@demo.com', subject="Email Verification",
                      body=f'Enter this code to verify your email: {local_code}', recipients=recipients)

    return redirect(url_for('verify_message', username=username))


# After registering for an account, take user to page where they need to
# enter the verify code send via email.
@app.route('/verify_message', methods=['GET'])
def verify_message():
    username = request.args.get('username')
    session['username'] = username
    user = User.query.filter_by(username=username).first()
    email = user.email
    return render_template('/verify_message.html', email=email)

# Get POSTed values from verification form, and check it against the
# code sent via email. If correct, log the user in; if not, send user
# to login page.


@app.route('/check_email_code', methods=['POST'])
def check_email_code():
    email = request.form.get('email')
    entered_code = request.form.get('code')

    if session['code'] == entered_code:
        session.pop('code', default=None)
        user = User.query.filter_by(username=session['username']).first()
        session.pop('username', default=None)
        user.verified = True
        db.session.commit()

        return try_to_log_just_registered_user_in(user.username)
    else:
        return render_template('/register.html', verification_fail=True)

# After a user enters the code to verify their email, log the user in if the code is correct,
# otherwise redirect them to the login page


def try_to_log_just_registered_user_in(username):
    user = User.query.filter_by(username=username).first()
    if not user.verified:
        print("User not verified")
        return render_template('/index.html', login_fail=True, login_page=True)
    else:
        print("User verified")
        login_user(user)
        return redirect("/")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)

data = list()
def data_company_refresh():
    print("SCHEDULED COMPANY REFRESH RUNNING")
    with app.app_context():
        try:
            # pre-processing to get/update all the updated company/article data before interfering with the DB
            if len(data) == 0:
                with open("companies.txt","r") as file_companies:
                    articles=[]
                    s = requests.Session()
                    for symbol in file_companies:
                        symbol=symbol.strip() # removes the trailing whitespaces
                        print(symbol)
                        c=companyClass.Company(symbol,s)
                        data.append(c)
            # if all of the companies and articles have already been instantiated, just check for updates using the company class built in method
            else:
                s = requests.Session()
                for c in data:
                    c.update(s)
            
            new_data = []
            
            # differentiate new articles from ones already in DB
            for c in data:
                for a in c.articles:
                    if (Article.query.filter_by(url=a.url).first()) is None:
                        comp = Company.query.filter_by(symbol=c.symbol).first()
                        new_data.append(Article(a.url, a.title, a.author, a.date, a.evaluation, comp.companyID))
            
            # creates notifications
            for nd in new_data:
                users = Follows.query.filter_by(companyID=nd.companyID).all()
                print(users)
                comp = Company.query.filter_by(companyID=nd.companyID).first()
                for u in users:
                    msg = "A new article has been published regarding " + comp.name
                    db.session.add(Notification(msg, u.userID, False))
            db.session.add_all(new_data)
            db.session.commit()
            print("DONE")
            
        except Exception as e:
            print(f"Error during scheduled refresh: {e.with_traceback()}")
            
# Setup the APScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(data_company_refresh, 'interval', minutes=30)  # Run every 30 minutes
scheduler.start()