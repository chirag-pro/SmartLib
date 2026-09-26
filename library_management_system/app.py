from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

from database import (
    init_db, get_all_books, get_book_by_id, add_book, update_book, delete_book,
    get_categories, create_user, get_user_by_username, get_user_by_email,
    get_user_by_id, get_all_users, update_user, update_user_password, toggle_user_status,
    issue_book, return_book, get_user_issued_books, get_user_returned_books, get_user_stats,
    get_library_stats, get_books_by_category, get_monthly_issues, get_monthly_returns,
    get_most_borrowed_books, get_all_issued_books, get_overdue_books,
    get_active_borrowers, get_user_registrations_monthly, calculate_fine
)
from auth import login_required, admin_required, get_current_user

app = Flask(__name__)
app.secret_key = 'xK9#mP2$vL7@nQ4&wR8!yT6^uJ3*'

# ── Context Processor ──────────────────────────────────────────────────────────

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user(), now=datetime.now())

# ── Public Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    stats = get_library_stats()
    featured = get_all_books()[:6]
    return render_template('index.html', stats=stats, featured=featured)

@app.route('/books')
def books():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    availability = request.args.get('availability', '')
    sort = request.args.get('sort', 'title')
    books_list = get_all_books(search=search, category=category, availability=availability, sort=sort)
    categories = get_categories()
    return render_template('books.html', books=books_list, categories=categories,
                           search=search, category=category, availability=availability, sort=sort)

@app.route('/book/<int:book_id>')
def book_details(book_id):
    book = get_book_by_id(book_id)
    if not book:
        return render_template('404.html'), 404
    already_borrowed = False
    if 'user_id' in session:
        from database import get_db
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM issued_books WHERE user_id=? AND book_id=? AND status='Issued'",
                  (session['user_id'], book_id))
        already_borrowed = c.fetchone()[0] > 0
        conn.close()
    return render_template('book_details.html', book=book, already_borrowed=already_borrowed)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ── Auth Routes ────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET','POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        username  = request.form.get('username','').strip()
        email     = request.form.get('email','').strip()
        phone     = request.form.get('phone','').strip()
        password  = request.form.get('password','')
        confirm   = request.form.get('confirm_password','')

        errors = []
        if not all([full_name, username, email, password, confirm]):
            errors.append('All fields are required.')
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors.append('Please enter a valid email address.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if get_user_by_username(username):
            errors.append('Username already exists.')
        if get_user_by_email(email):
            errors.append('Email already registered.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', form=request.form)

        create_user(full_name, username, email, generate_password_hash(password), phone)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form={})

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            if user['status'] != 'Active':
                flash('Your account has been deactivated. Please contact admin.', 'danger')
                return render_template('login.html')
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# ── Student Routes ─────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    user_id = session['user_id']
    stats = get_user_stats(user_id)
    issued = get_user_issued_books(user_id)
    returned = get_user_returned_books(user_id)[:5]
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('dashboard.html', stats=stats, issued=issued,
                           returned=returned, today=today, calculate_fine=calculate_fine)

@app.route('/my-books')
@login_required
def my_books():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    user_id = session['user_id']
    issued = get_user_issued_books(user_id)
    returned = get_user_returned_books(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('my_books.html', issued=issued, returned=returned,
                           today=today, calculate_fine=calculate_fine)

@app.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    if session.get('role') == 'admin':
        flash('Admins cannot borrow books.', 'warning')
        return redirect(url_for('book_details', book_id=book_id))
    success, msg = issue_book(session['user_id'], book_id)
    if success:
        flash(f'Book borrowed successfully! Due date: {msg}', 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('book_details', book_id=book_id))

@app.route('/return/<int:issue_id>', methods=['POST'])
@login_required
def return_book_route(issue_id):
    success, fine = return_book(issue_id, session['user_id'])
    if success:
        if fine > 0:
            flash(f'Book returned successfully. Fine: ₹{fine}', 'warning')
        else:
            flash('Book returned successfully. No fine.', 'success')
    else:
        flash('Unable to process return. Please try again.', 'danger')
    return redirect(url_for('my_books'))

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    user = get_user_by_id(session['user_id'])
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            full_name = request.form.get('full_name','').strip()
            email     = request.form.get('email','').strip()
            phone     = request.form.get('phone','').strip()
            if not full_name or not email:
                flash('Name and email are required.', 'danger')
            elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                flash('Invalid email address.', 'danger')
            else:
                existing = get_user_by_email(email)
                if existing and existing['id'] != session['user_id']:
                    flash('Email already in use.', 'danger')
                else:
                    update_user(session['user_id'], {'full_name':full_name,'email':email,'phone':phone})
                    session['full_name'] = full_name
                    flash('Profile updated successfully.', 'success')
        elif action == 'change_password':
            current  = request.form.get('current_password','')
            new_pw   = request.form.get('new_password','')
            confirm  = request.form.get('confirm_password','')
            if not check_password_hash(user['password_hash'], current):
                flash('Current password is incorrect.', 'danger')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters.', 'danger')
            elif new_pw != confirm:
                flash('Passwords do not match.', 'danger')
            else:
                update_user_password(session['user_id'], generate_password_hash(new_pw))
                flash('Password changed successfully.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

# ── Admin Routes ───────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = get_library_stats()
    cat_data = get_books_by_category()
    monthly_issues = get_monthly_issues()
    monthly_returns = get_monthly_returns()
    most_borrowed = get_most_borrowed_books()
    user_regs = get_user_registrations_monthly()
    return render_template('admin/dashboard.html', stats=stats,
                           cat_data=cat_data, monthly_issues=monthly_issues,
                           monthly_returns=monthly_returns, most_borrowed=most_borrowed,
                           user_regs=user_regs)

@app.route('/admin/books')
@admin_required
def admin_books():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    books_list = get_all_books(search=search, category=category)
    categories = get_categories()
    return render_template('admin/books.html', books=books_list, categories=categories,
                           search=search, category=category)

@app.route('/admin/books/add', methods=['GET','POST'])
@admin_required
def admin_add_book():
    if request.method == 'POST':
        data = {
            'title':            request.form.get('title','').strip(),
            'author':           request.form.get('author','').strip(),
            'category':         request.form.get('category','').strip(),
            'isbn':             request.form.get('isbn','').strip(),
            'publisher':        request.form.get('publisher','').strip(),
            'publication_year': request.form.get('publication_year', 0),
            'quantity':         request.form.get('quantity', 1),
            'shelf':            request.form.get('shelf','').strip(),
            'description':      request.form.get('description','').strip(),
            'cover_image':      request.form.get('cover_image','default.jpg').strip(),
        }
        if not data['title'] or not data['author'] or not data['category']:
            flash('Title, Author, and Category are required.', 'danger')
            return render_template('admin/add_book.html', form=request.form)
        try:
            qty = int(data['quantity'])
            if qty < 1:
                raise ValueError
        except ValueError:
            flash('Quantity must be a positive number.', 'danger')
            return render_template('admin/add_book.html', form=request.form)
        add_book(data)
        flash('Book added successfully!', 'success')
        return redirect(url_for('admin_books'))
    return render_template('admin/add_book.html', form={})

@app.route('/admin/books/edit/<int:book_id>', methods=['GET','POST'])
@admin_required
def admin_edit_book(book_id):
    book = get_book_by_id(book_id)
    if not book:
        return render_template('404.html'), 404
    if request.method == 'POST':
        data = {
            'title':            request.form.get('title','').strip(),
            'author':           request.form.get('author','').strip(),
            'category':         request.form.get('category','').strip(),
            'isbn':             request.form.get('isbn','').strip(),
            'publisher':        request.form.get('publisher','').strip(),
            'publication_year': request.form.get('publication_year', 0),
            'quantity':         request.form.get('quantity', 1),
            'shelf':            request.form.get('shelf','').strip(),
            'description':      request.form.get('description','').strip(),
            'cover_image':      request.form.get('cover_image','default.jpg').strip(),
        }
        if not data['title'] or not data['author'] or not data['category']:
            flash('Title, Author, and Category are required.', 'danger')
            return render_template('admin/edit_book.html', book=book, form=request.form)
        update_book(book_id, data)
        flash('Book updated successfully!', 'success')
        return redirect(url_for('admin_books'))
    return render_template('admin/edit_book.html', book=book, form=book)

@app.route('/admin/books/delete/<int:book_id>', methods=['POST'])
@admin_required
def admin_delete_book(book_id):
    success = delete_book(book_id)
    if success:
        flash('Book deleted successfully.', 'success')
    else:
        flash('Cannot delete: this book has active issues.', 'danger')
    return redirect(url_for('admin_books'))

@app.route('/admin/users')
@admin_required
def admin_users():
    search = request.args.get('search', '')
    users = get_all_users(search=search)
    return render_template('admin/users.html', users=users, search=search)

@app.route('/admin/users/toggle/<int:user_id>', methods=['POST'])
@admin_required
def admin_toggle_user(user_id):
    toggle_user_status(user_id)
    flash('User status updated.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/issued-books')
@admin_required
def admin_issued():
    status_filter = request.args.get('status', '')
    issues = get_all_issued_books(status_filter)
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('admin/issued_books.html', issues=issues,
                           status_filter=status_filter, today=today,
                           calculate_fine=calculate_fine)

@app.route('/admin/returns')
@admin_required
def admin_returns():
    issues = get_all_issued_books('Returned')
    return render_template('admin/returns.html', issues=issues)

@app.route('/admin/overdue')
@admin_required
def admin_overdue():
    overdues = get_overdue_books()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('admin/overdue.html', overdues=overdues,
                           today=today, calculate_fine=calculate_fine)

@app.route('/admin/reports')
@admin_required
def admin_reports():
    stats = get_library_stats()
    cat_data = get_books_by_category()
    most_borrowed = get_most_borrowed_books()
    active_borrowers = get_active_borrowers()
    monthly_issues = get_monthly_issues()
    monthly_returns = get_monthly_returns()
    return render_template('admin/reports.html', stats=stats, cat_data=cat_data,
                           most_borrowed=most_borrowed, active_borrowers=active_borrowers,
                           monthly_issues=monthly_issues, monthly_returns=monthly_returns)

# ── Error Handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=False)
