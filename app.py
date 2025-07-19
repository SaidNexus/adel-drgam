import os
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")

# Supabase setup
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Cloudinary setup
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Home page
@app.route('/')
def index():
    books = supabase.table("books").select("*").execute().data
    return render_template("index.html", books=books)

# Book details
@app.route('/book/<int:id>')
def book(id):
    book = supabase.table("books").select("*").eq("id", id).single().execute().data
    return render_template("book.html", book=book)

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="بيانات خاطئة")
    return render_template("login.html")

# Logout
@app.route('/logout')
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))

# Dashboard
@app.route('/dashboard')
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))
    books = supabase.table("books").select("*").execute().data
    return render_template("dashboard.html", books=books)

# Add book
@app.route('/add', methods=['POST'])
def add():
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    title = request.form["title"]
    summary = request.form["summary"]
    file = request.files["image"]
    
    if file:
        upload_result = cloudinary.uploader.upload(file)
        image_url = upload_result["secure_url"]
    else:
        image_url = ""

    supabase.table("books").insert({
        "title": title,
        "summary": summary,
        "image": image_url
    }).execute()

    return redirect(url_for("dashboard"))

# Delete book
@app.route('/delete/<int:id>')
def delete(id):
    if not session.get("admin"):
        return redirect(url_for("login"))
    supabase.table("books").delete().eq("id", id).execute()
    return redirect(url_for("dashboard"))

if __name__ == '__main__':
    app.run(debug=True)
