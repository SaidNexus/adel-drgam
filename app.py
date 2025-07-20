from flask import Flask, render_template, request, redirect, session, url_for
import os
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# إعداد Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://kbyxdwrmsxerpyvqhsyk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtieXhkd3Jtc3hlcnB5dnFoc3lrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mjk0MzIxNywiZXhwIjoyMDY4NTE5MjE3fQ.e2_glmND7RKd_MNZrK3GnZQ6cXLD6sRSIK1AjtecFXI")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client created successfully")
except Exception as e:
    print(f"Failed to create Supabase client: {str(e)}")
    raise Exception(f"Supabase error: {str(e)}")

# إعداد Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dbjm14xbf"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "329374832568726"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "gPanxHzfrwl2DW7C3cHHEnpspeU")
)
CLOUDINARY_UPLOAD_PRESET = os.getenv("CLOUDINARY_UPLOAD_PRESET", "mybooks")
if not all([cloudinary.config().cloud_name, cloudinary.config().api_key, cloudinary.config().api_secret, CLOUDINARY_UPLOAD_PRESET]):
    raise ValueError("Cloudinary configuration is incomplete")

# الصفحة الرئيسية
@app.route('/')
@app.route('/index.html')
def home():
    try:
        response = supabase.table('books').select('*').executeਰ

System: execute()
        books = response.data or []
        print(f"Fetched books: {books}")
    except Exception as e:
        print(f"Error fetching books: {str(e)}")
        books = []
    return render_template('index.html', books=books)

# عرض كتاب
@app.route('/book/<int:book_id>')
def view_book(book_id):
    try:
        response = supabase.table('books').select('*').eq('id', book_id).execute()
        book = response.data[0] if response.data else None
        if book:
            return render_template('book.html', book=book)
        return "الكتاب غير موجود", 404
    except Exception as e:
        print(f"Error fetching book: {str(e)}")
        return "خطأ في جلب الكتاب", 500

# صفحة تسجيل الدخول
@app.route('/admin')
def admin():
    if not session.get("logged_in"):
        return render_template('login.html')
    return redirect('/dashboard')

# لوحة التحكم
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get("logged_in"):
        return redirect('/admin')
    
    if request.method == 'POST':
        try:
            print("Starting book insertion process...")
            title = request.form['title']
            content = request.form['content']
            image = request.files.get('image')

            print(f"Received form data: title={title}, content={content}, image={image}")

            image_url = ""
            if image:
                print("Uploading image to Cloudinary...")
                upload_result = cloudinary.uploader.upload(
                    image,
                    upload_preset=CLOUDINARY_UPLOAD_PRESET,
                    folder="books"
                )
                image_url = upload_result['secure_url']
                print(f"Image uploaded successfully: {image_url}")

            new_book = {
                "title": title,
                "content": content,
                "image": image_url
            }
            print(f"Inserting book: {new_book}")

            response = supabase.table('books').insert(new_book).execute()
            print(f"Insert response: {response.data}")

            return redirect('/dashboard')
        except Exception as e:
            print(f"Error adding book: {str(e)}")
            return render_template('dashboard.html', books=[], error=f"خطأ في إضافة الكتاب: {str(e)}")

    try:
        response = supabase.table('books').select('*').execute()
        books = response.data or []
        print(f"Fetched books: {books}")
    except Exception as e:
        print(f"Error fetching books: {str(e)}")
        books = []
    return render_template('dashboard.html', books=books)

# حذف كتاب
@app.route('/delete/<int:book_id>')
def delete_book(book_id):
    if not session.get("logged_in"):
        return redirect('/admin')

    try:
        supabase.table('books').delete().eq('id', book_id).execute()
        return redirect('/dashboard')
    except Exception as e:
        print(f"Error deleting book: {str(e)}")
        return "خطأ في حذف الكتاب", 500

# تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "drgam" and password == "drgam":
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            error = "كلمة السر أو اسم المستخدم غير صحيحة"
    return render_template('login.html', error=error)

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

# صفحة النبذة
@app.route('/about.html', endpoint='about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
