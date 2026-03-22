from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Resume
from forms import RegistrationForm, LoginForm, ResumeForm
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resumes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.updated_at.desc()).all()
    return render_template('dashboard.html', resumes=resumes)

@app.route('/build_resume', methods=['GET', 'POST'])
@login_required
def build_resume():
    form = ResumeForm()
    if form.validate_on_submit():
        resume = Resume(
            user_id=current_user.id,
            title=form.title.data,
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            summary=form.summary.data,
            education=form.education.data,
            experience=form.experience.data,
            skills=form.skills.data
        )
        db.session.add(resume)
        db.session.commit()
        flash('Resume saved successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('build_resume.html', form=form)

@app.route('/edit_resume/<int:resume_id>', methods=['GET', 'POST'])
@login_required
def edit_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = ResumeForm()
    if form.validate_on_submit():
        resume.title = form.title.data
        resume.full_name = form.full_name.data
        resume.email = form.email.data
        resume.phone = form.phone.data
        resume.address = form.address.data
        resume.summary = form.summary.data
        resume.education = form.education.data
        resume.experience = form.experience.data
        resume.skills = form.skills.data
        db.session.commit()
        flash('Resume updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Populate form with existing data
    form.title.data = resume.title
    form.full_name.data = resume.full_name
    form.email.data = resume.email
    form.phone.data = resume.phone
    form.address.data = resume.address
    form.summary.data = resume.summary
    form.education.data = resume.education
    form.experience.data = resume.experience
    form.skills.data = resume.skills
    
    return render_template('build_resume.html', form=form, edit_mode=True, resume_id=resume_id)

@app.route('/preview_resume/<int:resume_id>')
@login_required
def preview_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Parse education, experience, skills
    education_list = [e.strip() for e in resume.education.split('\n') if e.strip()]
    experience_list = [e.strip() for e in resume.experience.split('\n') if e.strip()]
    skills_list = [s.strip() for s in resume.skills.split(',') if s.strip()]
    
    return render_template('preview_resume.html', resume=resume, 
                         education_list=education_list, 
                         experience_list=experience_list,
                         skills_list=skills_list)

@app.route('/download_resume/<int:resume_id>')
@login_required
def download_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#2c3e50'), spaceAfter=12)
    normal_style = styles['Normal']
    
    # Name and Title
    story.append(Paragraph(resume.full_name, title_style))
    
    # Contact Information
    contact_info = []
    if resume.email:
        contact_info.append(f"Email: {resume.email}")
    if resume.phone:
        contact_info.append(f"Phone: {resume.phone}")
    if resume.address:
        contact_info.append(f"Address: {resume.address}")
    
    contact_text = " | ".join(contact_info)
    story.append(Paragraph(contact_text, normal_style))
    story.append(Spacer(1, 12))
    
    # Professional Summary
    story.append(Paragraph("Professional Summary", heading_style))
    story.append(Paragraph(resume.summary, normal_style))
    story.append(Spacer(1, 12))
    
    # Skills
    story.append(Paragraph("Skills", heading_style))
    skills_list = [s.strip() for s in resume.skills.split(',')]
    skills_text = ", ".join(skills_list)
    story.append(Paragraph(skills_text, normal_style))
    story.append(Spacer(1, 12))
    
    # Experience
    story.append(Paragraph("Work Experience", heading_style))
    experience_items = [e.strip() for e in resume.experience.split('\n') if e.strip()]
    for exp in experience_items:
        story.append(Paragraph(f"• {exp}", normal_style))
    story.append(Spacer(1, 12))
    
    # Education
    story.append(Paragraph("Education", heading_style))
    education_items = [e.strip() for e in resume.education.split('\n') if e.strip()]
    for edu in education_items:
        story.append(Paragraph(f"• {edu}", normal_style))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"{resume.full_name}_resume.pdf", mimetype='application/pdf')

@app.route('/delete_resume/<int:resume_id>')
@login_required
def delete_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(resume)
    db.session.commit()
    flash('Resume deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)