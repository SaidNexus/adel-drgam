import os
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Supabase setup
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

@app.route('/')
@app.route('/index.html')
def home():
    response = supabase.table("books").select("*").execute()
    books = response.data
    return render_template('index.html', books=books)

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/book/<int:book_id>')
def view_book(book_id):
    response = supabase.table("books").select("*").eq('id', book_id).single().execute()
    book = response.data
    if not book:
        return "الكتاب غير موجود", 404
    return render_template('book.html', book=book)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response and response.user:
            session['user'] = response.user.id
            return redirect('/admin')
        else:
            return render_template('login.html', error="بيانات الدخول غير صحيحة")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect('/login')

    response = supabase.table("books").select("*").execute()
    books = response.data
    return render_template('dashboard.html', books=books)

@app.route('/add-book', methods=['POST'])
def add_book():
    if 'user' not in session:
        return redirect('/login')

    title = request.form['title']
    description = request.form['description']
    file = request.files['image']

    image_url = None
    if file:
        upload_result = cloudinary.uploader.upload(file)
        image_url = upload_result['secure_url']

    supabase.table("books").insert({
        "title": title,
        "description": description,
        "image_url": image_url
    }).execute()

    return redirect('/admin')

@app.route('/delete-book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user' not in session:
        return redirect('/login')

    supabase.table("books").delete().eq("id", book_id).execute()
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
