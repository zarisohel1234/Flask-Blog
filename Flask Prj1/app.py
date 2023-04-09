import os
from werkzeug.utils import secure_filename
from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import date, datetime
import json

app=Flask(__name__)
app.secret_key='super-key'
with open('config.json','r') as c:
    params=json.load(c)['params']

local_server=params['local_server']  #local server true for checking condition

# Configuring mail with app
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
mail=Mail(app)               #For initializing Flask mail services

#Configuring with File Uploader
app.config['UPLOAD_FOLDER']= params['upload_location']

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']     #Choosing server as local or production from config.json
else:
    app.config['SQLALCHEMY_DATABASE_URI'] =params['prod_uri']       #Choosing server as production or production from config.json

db = SQLAlchemy(app)

class Contacts(db.Model):          #Creating Database models take variables in database tables for Contacts.
    ysrno = db.Column(db.Integer,primary_key=True,nullable=False)
    yname = db.Column(db.String(80), unique=True, nullable=True)
    yemail = db.Column(db.String(120), unique=True, nullable=False)
    yphone_num = db.Column(db.String(12), unique=True, nullable=True)
    ymessage = db.Column(db.String(120), unique=True, nullable=True)
    ydate = db.Column(db.String(12), unique=False, nullable=False)

class Posts(db.Model):          #Creating Database models take variables in database tables for posts.
    srno = db.Column(db.Integer,primary_key=True,nullable=False)
    title = db.Column(db.String(80), unique=True, nullable=True)
    slug = db.Column(db.String(20), unique=True, nullable=False)
    content = db.Column(db.String(12), unique=True, nullable=True)
    date = db.Column(db.String(12), unique=False, nullable=False)
    img_url=db.Column(db.String(20),unique=False,nullable=True)
    tag_line=db.Column(db.String(20),unique=False,nullable=True)

# Index page Web-Service
@app.route('/')
def index():
    posts=Posts.query.filter_by().all()[0:params['texts']]
    return render_template('index.html',params=params,posts=posts)        # --> render template gives file present in templates folder

# about page Web-service
@app.route('/about')
def about():
    return render_template('about.html',params=params)

@app.route('/uploader',methods=['GET','POST'])
def uploader():
    if('user' in session and session['user']==params['admin_user']):
        if request.method =='POST':
            file=request.files['f1']
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
            return "File Uploaded Successfully"

#Web service for Edit web pages
@app.route('/edit/<string:srno>',methods=['GET','POST'])
def edit(srno):
    if('user' in session and session['user']==params['admin_user']):
        if request.method =='POST':
            title=request.form.get('title')
            slug=request.form.get('slug')
            content=request.form.get('content')
            tag_line=request.form.get('tag_line')
            img_url=request.form.get('img_url')

            if srno == '0':
                post=Posts(title=title,slug=slug,content=content,tag_line=tag_line,img_url=img_url,date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(srno=srno).first()
                post.title=title
                post.slug=slug
                post.content=content
                post.tag_line=tag_line
                post.img_url=img_url
                db.session.commit()
                return redirect('/edit/'+srno)

        post=Posts.query.filter_by(srno=srno).first()
        return render_template('edit.html',params=params,srno=srno,post=post)

# Dashboard page web Service
@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    #If User alraedy logged in
    if('user' in session and session['user']==params['admin_user']):
        posts=Posts.query.filter_by().all()
        return render_template('dashboard.html',params=params,posts=posts)

    #If user tries to log in
    if request.method=='POST':
        email=request.form.get('email')
        password=request.form.get('password')
        if(email==params['admin_user'] and password==params['admin_pass']):
            session['user']=email
            posts=Posts.query.filter_by().all()
            return render_template('dashboard.html',params=params,posts=posts)

    return render_template('login.html',params=params)

# Post page web Service
@app.route('/post/<string:post_slug>',methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()    # -->For fetching and displaying posts at post.html page from database
    return render_template('post.html',params=params,post=post)


#  Contact page web-services
@app.route('/contact',methods=['GET','POST'])
def contact():
    if request.method == "POST":     # Setting method Used   &    Using it to get response in form field in Website
        name=request.form.get('name')  #variable name is for getting data form in website & make it name
        srno=request.form.get('srno')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        #Entry variable is used for assigning class elements or database attributes  with the user response
        entry=Contacts(ysrno=srno,yname=name,yemail=email,yphone_num=phone,ymessage=message,ydate=datetime.now())

        db.session.add(entry)        #db.session.add() used for add
        db.session.commit()          #db.sessioncommit() is for commit it
        mail.send_message('New Message',
                            sender=email ,
                            recipients=[params['gmail_user']],
                            body=message + '/n' + phone)          #Use for Sending Mail in contacts registration

    return render_template('contact.html',params=params)   #Passing parameters in config.json file as params=params

# Web-service for Deleting posts from dashboard
@app.route('/delete/<string:sno>',methods=['GET','POST'])
def delete(sno):
    if('user' in session and session['user']==params['admin_user']):
        post=Posts.query.filter_by(srno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')

#Web Service for Log-Out
@app.route('/logout/')
def logout():
    session.pop('user')
    return redirect('/dashboard')


if __name__ =="__main__":
    app.run(debug=True)