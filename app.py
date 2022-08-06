import sqlite3 as sql
import os
from flask import Flask, render_template, request, session, flash
from werkzeug.utils import redirect, secure_filename
from spacy.lang.en import English
import numpy as np
from Summarizer1 import summarize
from Translator import Translator
from newsapi import NewsApiClient
from WebScraper import WebScraper
import pyttsx3
from SentimentAnalysis import isOffensive
newsapi = NewsApiClient(api_key='d9dd88d517c24c7690274e6a34457842')
sources = newsapi.get_sources()
app = Flask(__name__)
app.secret_key = '3d6f45a5fc12445dbac2f59c3b6c7cb1'
app.config['UPLOAD_FOLDER'] = "static/image"
@app.route("/")
def start():
    return redirect('/home')

@app.route("/home")
def home():
    return render_template('homepage.html')


@app.route("/login")
def login():
    return render_template('login.html')


@app.route("/authenticate", methods=['GET', 'POST'])
def authenticate():
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    email = request.form['email']
    password = request.form['password']
    query = f"select uid, name, email, password, blocked from userdetail where email = '{email}' and password = '{password}';"
    rows = cur.execute(query)
    rows = rows.fetchall()
    con.commit()
    con.close()
    if len(rows) == 1 and rows[0][-1] != 1:
        session['uid'] = rows[0][0]
        session['user'] = rows[0][1]
        session['email'] = rows[0][2]
        session['password'] = rows[0][3]
        return redirect('/profile')
    elif len(rows) == 1 and rows[0][-1] == 1:
        flash("You are blocked!")
        return redirect('/login')
    else:
        flash("Invalid Login Credentials")
        return redirect('/login')


@app.route("/registration", methods=['GET', 'POST'])
def registration():
    return render_template('registration.html')


@app.route("/contact")
def contact():
    return render_template('contact.html')


@app.route("/register", methods=['POST'])
def register():
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    verified = 0
    image = 'static/image/default.jpg'
    rid = 0
    email = request.form['e']
    password = request.form['p']
    name = request.form['n']
    mobile = request.form['m']
    address = request.form['address']
    cur.execute("insert into userdetail (Name, Mobile, Email, Password, Image, Verified, RID, Address, blocked) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",(name, mobile, email, password, image, verified, rid, address, 0))
    con.commit()
    con.close()
    return redirect('/login')

@app.route('/profile', methods = ['GET', 'POST'])
def profile():
    if request.method == "POST":
        if 'upload' in request.form.keys():
            con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
            cur = con.cursor()
            uid = session['uid']
            if 'image' in request.files:
                image = request.files['image']
                if(image.filename != ""):
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    filename = app.config['UPLOAD_FOLDER'] + '/' + filename
                    query = f"update userdetail set image = '{filename}' where uid = '{uid}';"
                    cur.execute(query)
                    con.commit()
                    con.close()
                else:
                    flash("Upload an image first!")
        elif 'edit' in request.form.keys():
            return redirect('/edit')
    
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    uid = session['uid']
    query = f"select * from userdetail where uid = '{uid}';"
    rows = cur.execute(query)
    rows = rows.fetchall()
    uid, name, mobile, email, password, image, verified, rid, address = rows[0][0], rows[0][1], rows[0][2], rows[0][3], rows[0][4], rows[0][5], rows[0][6], rows[0][7], rows[0][8] 
    query = f"select rname from role where rid = '{rid}';"
    rows = cur.execute(query)
    rows = rows.fetchall()
    rid = rows[0][0]
    session['role'] = rid
    con.close()
    if rid == "Administrator":
        user = ["admin"]
        return render_template('profile.html', name = name, mobile = mobile, email = email, password = password, image = image, verified = verified, role = rid, address = address, user = user)
    elif rid == "Editor":
        user = ["editor"]
        return render_template('profile.html', name = name, mobile = mobile, email = email, password = password, image = image, verified = verified, role = rid, address = address, user = user)
    else:
        user = ["user"]
        return render_template('profile.html', name = name, mobile = mobile, email = email, password = password, image = image, verified = verified, role = rid, address = address, user = user)
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/home')

@app.route('/edit', methods = ['POST', 'GET'])
def edit():
    uid = session['uid']
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    uid = session['uid']
    query = f"select * from userdetail where uid = '{uid}';"
    rows = cur.execute(query)
    rows = rows.fetchall()
    uid, name, mobile, email, password, image, verified, rid, address = rows[0][0], rows[0][1], rows[0][2], rows[0][3], rows[0][4], rows[0][5], rows[0][6], rows[0][7], rows[0][8]
    if request.method == 'POST':
         name = request.form['n']
         email = request.form['e']
         password = request.form['p']
         address = request.form['a']
         query = f"update userdetail set name = '{name}', email = '{email}', password = '{password}', address = '{address}' where uid = '{uid}';"
         cur.execute(query)
         con.commit()
         con.close()
         return redirect('/profile')
    con.close()
    return render_template('edit.html', name = name, email = email, password = password, address = address, mobile = mobile)

@app.route('/sports', methods = ['GET', 'POST'])
def sports():
    category = 'Sports'
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    query = f"select heading, category, image, descript, date, uid, aid from articles where category = '{category}' ORDER BY date DESC;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    for i in range(len(rows)):
        query = f"select name,email from userdetail where uid = '{rows[i][5]}';"
        name = cur.execute(query)
        name = name.fetchall()
        if name:
            rows[i] = list(rows[i])
            rows[i][5] = name[0]
            rows[i] = tuple(rows[i])
    if session['role'] == "Administrator":
        user = ["admin"]
        return render_template('news.html', news = 'Sports', posts=rows, user = user)
    elif session['role'] == "Editor":
        user = ["editor"]
        return render_template('news.html', news = 'Sports', posts=rows, user = user)
    else:
        user = ["user"]
        return render_template('news.html', news = 'Sports', posts=rows, user = user)

@app.route('/politics', methods = ['GET', 'POST'])
def politics():
    category = 'Politics'
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    query = f"select heading, category, image, descript, date, uid, aid from articles where category = '{category}' ORDER BY date DESC;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    for i in range(len(rows)):
        query = f"select name,email from userdetail where uid = '{rows[i][5]}';"
        name = cur.execute(query)
        name = name.fetchall()
        if name:
            rows[i] = list(rows[i])
            rows[i][5] = name[0]
            rows[i] = tuple(rows[i])
    if session['role'] == "Administrator":
        user = ["admin"]
        return render_template('news.html', news = 'Politics', posts=rows, user = user)
    elif session['role'] == "Editor":
        user = ["editor"]
        return render_template('news.html', news = 'Politics', posts=rows, user = user)
    else:
        user = ["user"]
        return render_template('news.html', news = 'Politics', posts=rows, user = user)

@app.route('/tech', methods = ['GET', 'POST'])
def tech():
    category = 'Tech'
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    query = f"select heading, category, image, descript, date, uid, aid from articles where category = '{category}' ORDER BY date DESC;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    for i in range(len(rows)):
        query = f"select name,email from userdetail where uid = '{rows[i][5]}';"
        name = cur.execute(query)
        name = name.fetchall()
        if name:
            rows[i] = list(rows[i])
            rows[i][5] = name[0]
            rows[i] = tuple(rows[i])
    if session['role'] == "Administrator":
        user = ["admin"]
        return render_template('news.html', news = 'Technology', posts=rows, user = user)
    elif session['role'] == "Editor":
        user = ["editor"]
        return render_template('news.html', news = 'Technology', posts=rows, user = user)
    else:
        user = ["user"]
        return render_template('news.html', news = 'Technology', posts=rows, user = user)

@app.route('/film', methods = ['GET', 'POST'])
def film():
    category = 'Film'
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    query = f"select heading, category, image, descript, date, uid, aid from articles where category = '{category}' ORDER BY date DESC;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    for i in range(len(rows)):
        query = f"select name,email from userdetail where uid = '{rows[i][5]}';"
        name = cur.execute(query)
        name = name.fetchall()
        if name:
            rows[i] = list(rows[i])
            rows[i][5] = name[0]
            rows[i] = tuple(rows[i])
    if session['role'] == "Administrator":
        user = ["admin"]
        return render_template('news.html', news = 'Film', posts=rows, user = user)
    elif session['role'] == "Editor":
        user = ["editor"]
        return render_template('news.html', news = 'Film', posts=rows, user = user)
    else:
        user = ["user"]
        return render_template('news.html', news = 'Film', posts=rows, user = user)

@app.route('/world', methods = ['GET', 'POST'])
def world():
    category = 'World'
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    query = f"select heading, category, image, descript, date, uid, aid from articles where category = '{category}' ORDER BY date DESC;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    for i in range(len(rows)):
        query = f"select name,email from userdetail where uid = '{rows[i][5]}';"
        name = cur.execute(query)
        name = name.fetchall()
        if name:
            rows[i] = list(rows[i])
            rows[i][5] = name[0]
            rows[i] = tuple(rows[i])
    if session['role'] == "Administrator":
        user = ["admin"]
        return render_template('news.html', news = 'World', posts=rows, user = user)
    elif session['role'] == "Editor":
        user = ["editor"]
        return render_template('news.html', news = 'World', posts=rows, user = user)
    else:
        user = ["user"]
        return render_template('news.html', news = 'World', posts=rows, user = user)

@app.route('/business', methods = ['GET', 'POST'])
def business():
    category = 'Business'
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    query = f"select heading, category, image, descript, date, uid, aid from articles where category = '{category}' ORDER BY date DESC;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    for i in range(len(rows)):
        query = f"select name,email from userdetail where uid = '{rows[i][5]}';"
        name = cur.execute(query)
        name = name.fetchall()
        if name:
            rows[i] = list(rows[i])
            rows[i][5] = name[0]
            rows[i] = tuple(rows[i])
    if session['role'] == "Administrator":
        user = ["admin"]
        return render_template('news.html', news = 'Business', posts=rows, user = user)
    elif session['role'] == "Editor":
        user = ["editor"]
        return render_template('news.html', news = 'Business', posts=rows, user = user)
    else:
        user = ["user"]
        return render_template('news.html', news = 'Business', posts=rows, user = user)


@app.route("/newpost")
def NewPost():
    return render_template('AddNewPost.html')

@app.route("/addnewpost", methods = ['GET', 'POST'])
def AddNewPost():
    heading = request.form['head']
    category = request.form['cat']
    description = request.form['descri']
    rating = isOffensive(description)[0]
    if rating['label'] == '1 star':
        flash('Your post could be found offensive to some readers')
        return render_template('AddNewPost.html')
    image = request.files['image']
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    if(image.filename != ""):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filename = app.config['UPLOAD_FOLDER'] + '/' + filename
        query = f"select datetime('now', 'localtime');"
        date = cur.execute(query)
        date = cur.fetchone()
        query = f"insert into articles (Heading, Category, Image, Descript, Date, UID) VALUES ('{heading}', '{category}', '{filename}', '{description}', '{date[0]}', '{session['uid']}');"
        cur.execute(query)
        con.commit()
        flash("Post added successfully")
    return render_template('AddNewPost.html')

@app.route("/verifiedUsers", methods = ['GET', 'POST'])
def verifiedUsers():
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    if request.method == 'POST':
        if request.form['submit_button'] == 'block':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set blocked = 1 where uid ='{i}';"
                cur.execute(query)
                con.commit()
        
        if request.form['submit_button'] == 'unblock':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set blocked = 0 where uid ='{i}';"
                cur.execute(query)
                con.commit()
        
        if request.form['submit_button'] == 'mkeditor':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set rid = 2 where uid = '{i}';"
                cur.execute(query)
                con.commit()
        
        if request.form['submit_button'] == 'mkuser':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set rid = 1 where uid = '{i}';"
                cur.execute(query)
                con.commit()
        
        if request.form['submit_button'] == 'rmver':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set verified = 0 where uid = '{i}';"
                cur.execute(query)
                con.commit()
        
    
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    query = f"select uid, name, email, password from userdetail where verified = 1;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    query = f"select rid from userdetail where verified = 1;"
    rid = cur.execute(query)
    rid = rid.fetchall()
    for i in range(len(rid)):
        rows[i] = list(rows[i])
        role = cur.execute(f"select rname from role where rid = '{rid[i][0]}'")
        role = role.fetchone()
        rows[i].append(role[0])
        rows[i] = tuple(rows[i])
    con.close()
    return render_template('verifiedUsers.html', rows = rows)

@app.route("/non-verifiedUsers", methods = ['GET', 'POST'])
def nonVerifiedUsers():
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    if request.method == 'POST':
        if request.form['submit_button'] == 'block':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set blocked = 1 where uid ='{i}';"
                cur.execute(query)
                con.commit()
        
        if request.form['submit_button'] == 'unblock':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set blocked = 0 where uid ='{i}';"
                cur.execute(query)
                con.commit()
        
        if request.form['submit_button'] == 'mkeditor':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set rid = 2 where uid = '{i}';"
                cur.execute(query)
                con.commit()
        
        if request.form['submit_button'] == 'mkuser':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set rid = 1 where uid = '{i}';"
                cur.execute(query)
                con.commit()
        
        if request.form['submit_button'] == 'rmver':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"update userdetail set verified = 1 where uid = '{i}';"
                cur.execute(query)
                con.commit()
        
    
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    query = f"select uid, name, email, password from userdetail where verified = 0;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    query = f"select rid from userdetail where verified = 0;"
    rid = cur.execute(query)
    rid = rid.fetchall()
    for i in range(len(rid)):
        rows[i] = list(rows[i])
        role = cur.execute(f"select rname from role where rid = '{rid[i][0]}'")
        role = role.fetchone()
        rows[i].append(role[0])
        rows[i] = tuple(rows[i])
    con.close()
    return render_template('nonVerifiedUsers.html', rows = rows)



@app.route("/verifiedArticles", methods = ['GET', 'POST'])
def verifiedArticles():
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()

    if request.method == 'POST':
        if request.form['delete'] == 'delete':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"delete from articles where aid = '{i}';"
                cur.execute(query)
                con.commit()

    query = f"select heading, image, descript, date, uid, aid from articles where uid in (select uid from userdetail where verified = 1);"
    rows = cur.execute(query)
    rows = rows.fetchall()
    for i in range(len(rows)):
        rows[i] = list(rows[i])
        name = cur.execute(f"select name from userdetail where uid = '{rows[i][4]}'").fetchone()
        rows[i][4] = name[0]
        nlp = English()
        nlp.add_pipe('sentencizer')
        rows[i][2] = summarize(text = rows[i][2], per=0.5)
        rows[i] = tuple(rows[i])
    con.close()
    return render_template('verifiedArticles.html', rows = rows)


@app.route("/non-verifiedArticles", methods = ['GET', 'POST'])
def nonVerifiedArticles():
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()

    if request.method == 'POST':
        if request.form['delete'] == 'delete':
            checkedList = request.form.getlist('check[]')
            for i in checkedList:
                query = f"delete from articles where aid = '{i}';"
                cur.execute(query)
                con.commit()

    query = f"select heading, image, descript, date, uid, aid from articles where uid in (select uid from userdetail where verified = 0);"
    rows = cur.execute(query)
    rows = rows.fetchall()
    for i in range(len(rows)):
        rows[i] = list(rows[i])
        name = cur.execute(f"select name from userdetail where uid = '{rows[i][4]}'").fetchone()
        rows[i][4] = name[0]
        nlp = English()
        nlp.add_pipe('sentencizer')
        rows[i][2] = summarize(text = rows[i][2], per=0.5)
        rows[i] = tuple(rows[i])
    con.close()
    return render_template('verifiedArticles.html', rows = rows)

@app.route('/ReadPost<aid>', methods = ['GET', 'POST'])
def ReadPost(aid):
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    query = f"select heading, category, image, descript, date, uid from articles where aid = '{aid}' ORDER BY date DESC;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    query = f"select name,email from userdetail where uid = '{rows[0][5]}';"
    name = cur.execute(query)
    name = name.fetchall()
    if name:
        rows[0] = list(rows[0])
        rows[0][5] = name[0]
        rows[0] = tuple(rows[0])
    if request.method == "POST":
        if request.form['submit_button'] == 'Summarize':
            rows[0] = list(rows[0])
            rows[0][3] = summarize(text = rows[0][3], per=0.5)
            rows[0] = tuple(rows[0])
        elif request.form['submit_button'] == 'Translate':
            language = request.form.get('language')
            print(language)
            languages = {
                'Hindi' : 'hi',
                'Telugu' : 'te',
                'Tamil' : 'ta',
                'Kannada' : 'kn',
            }
            language = languages[language]
            rows[0] = list(rows[0])
            rows[0][3] = Translator(rows[0][3], language)
            rows[0] = tuple(rows[0])
        elif request.form['submit_button'] == 'Audio':
            description = rows[0][3]
            pyobj = pyttsx3.init()
            pyobj.say(description)
            pyobj.runAndWait()
    if session['role'] == "Administrator":
        user = ["admin"]
        return render_template('ReadPost.html', heading = rows[0][0], category = rows[0][1], name = rows[0][5][0], email = rows[0][5][1], date = rows[0][4], source = rows[0][2], description = rows[0][3], aid = aid, user = user)
    elif session['role'] == "Editor":
        user = ["editor"]
        return render_template('ReadPost.html', heading = rows[0][0], category = rows[0][1], name = rows[0][5][0], email = rows[0][5][1], date = rows[0][4], source = rows[0][2], description = rows[0][3], aid = aid, user=user)
    else:
        user = ["user"]
        return render_template('ReadPost.html', heading = rows[0][0], category = rows[0][1], name = rows[0][5][0], email = rows[0][5][1], date = rows[0][4], source = rows[0][2], description = rows[0][3], aid = aid, user=user)

    
@app.route('/news', methods = ['GET', 'POST'])
def gnews():
    if request.method == 'POST':
        query = request.form.get('searchbar')
        from_date = request.form.get('from')
        to_date = request.form.get('to')
        top_headlines = ""
        if(from_date == "" or to_date == ""):
            top_headlines = newsapi.get_everything(q=query,language="en")
        else:
            top_headlines = newsapi.get_everything(q=query,language="en", from_param=from_date, to=to_date)
        articles = top_headlines['articles']
        if session['role'] == "Administrator":
            user = ["admin"]
            return render_template('gnews.html', articles = articles)
        elif session['role'] == "Editor":
            user = ["editor"]
            return render_template('gnews.html', articles = articles, user=user)
        else:
            user = ["user"]
            return render_template('gnews.html', articles = articles, user=user)
    else:
        return render_template('gnews.html')

@app.route('/readURL', methods = ['GET', 'POST'])
def webscrape():
    if request.method == 'POST':
        name = request.form['author']
        heading = request.form['title']
        URL = request.form['URL']
        date = request.form['date']
        content = request.form['content']
        source = request.form['source']
        i = -7
        chars = ""
        while content[i] != '+':
            chars += content[i]
            i -= 1
        chars = int(chars[::-1])
        starting = content[:25]
        description = WebScraper(URL)
        while not description.startswith(starting):
            description = description[1:]
        description = description[:chars+18]
        if session['role'] == "Administrator":
            user = ["admin"]
            return render_template('ReadPostURL.html', heading = heading, name = name, date = date, description = description, source = source, sourceURL = URL,user=user)
        elif session['role'] == "Editor":
            user = ["editor"]
            return render_template('ReadPostURL.html', heading = heading, name = name, date = date, description = description, source = source, sourceURL = URL,user=user)
        else:
            user = ["user"]
            return render_template('ReadPostURL.html', heading = heading, name = name, date = date, description = description, source = source, sourceURL = URL,user=user)

@app.route('/ReadPostURL', methods = ['GET', 'POST'])
def readPostURL():
    if request.method == 'POST':
        description = request.form.get('description')
        heading = request.form.get('heading')
        name = request.form.get('name')
        date = request.form.get('date')
        source = request.form.get('source')
        if request.form['submit_button'] == 'Translate':
            language = request.form.get('language')
            print(language)
            languages = {
                'Hindi' : 'hi',
                'Telugu' : 'te',
                'Tamil' : 'ta',
                'Kannada' : 'kn',
            }
            language = languages[language]
            description = Translator(description, language)
        
        elif request.form['submit_button'] == 'Audio':
            description = request.form.get('description')
            pyobj = pyttsx3.init()
            pyobj.say(description)
            pyobj.runAndWait()
        
        if session['role'] == "Administrator":
            user = ["admin"]
            return render_template('ReadPostURL.html', heading = heading, name = name, date = date, description = description, source = source,user=user)
        elif session['role'] == "Editor":
            user = ["editor"]
            return render_template('ReadPostURL.html', heading = heading, name = name, date = date, description = description, source = source, user=user)
        else:
            user = ["user"]
            return render_template('ReadPostURL.html', heading = heading, name = name, date = date, description = description, source = source, user=user)

@app.route('/viewposts', methods = ['GET', 'POST'])
def viewposts():
    con = sql.connect(r'''D:\NewsPortal_DB\sqlite\newspaperx.db''')
    cur = con.cursor()
    if request.method == 'POST':
        aid = request.form.get('aid')
        query = f"delete from articles where aid = '{aid}'"
        cur.execute(query)
        con.commit()
    uid = session['uid']
    query = f"select heading, category, image, descript, date, uid, aid from articles where uid = '{uid}' ORDER BY date DESC;"
    rows = cur.execute(query)
    rows = rows.fetchall()
    for i in range(len(rows)):
        query = f"select name,email from userdetail where uid = '{rows[i][5]}';"
        name = cur.execute(query)
        name = name.fetchall()
        if name:
            rows[i] = list(rows[i])
            rows[i][5] = name[0]
            rows[i] = tuple(rows[i])
    user = ["editor"]
    return render_template('ViewMyPosts.html', news = 'Business', posts=rows, user = user)

if __name__ == "__main__":
    app.run(debug=True)