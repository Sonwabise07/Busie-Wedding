import os
import csv
import io
import re
import secrets
import qrcode
from datetime import datetime
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_file)
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///wedding.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class Guest(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False)
    token      = db.Column(db.String(64), unique=True, nullable=False)
    used       = db.Column(db.Boolean, default=False)          # RSVP submitted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rsvp       = db.relationship('RSVP', backref='guest', uselist=False)

class RSVP(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    guest_token  = db.Column(db.String(64), db.ForeignKey('guest.token'), nullable=True)
    full_name    = db.Column(db.String(200), nullable=False)
    phone        = db.Column(db.String(30), nullable=False)
    attending    = db.Column(db.Boolean, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class GiftClaim(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    gift_id      = db.Column(db.String(50), nullable=False)
    claimer_name = db.Column(db.String(200), nullable=False)
    claimer_phone = db.Column(db.String(30), nullable=False)
    claimed_at   = db.Column(db.DateTime, default=datetime.utcnow)

GIFTS = [
    {"id": "cutlery", "name": "Cutlery Set", "description": "16–24 piece stainless steel cutlery set", "icon": "🍴",
     "options": [{"label": "Option A", "url": "https://www.mrphome.com/en_za/16-piece-2-tone-stainless-steel-cutlery-set-106767467"},
                 {"label": "Option B", "url": "https://www.takealot.com/24-piece-stainless-steel-cutlery-set/PLID71884328"}]},
    {"id": "chopping-board", "name": "Chopping Board", "description": "Bamboo or marble chopping board", "icon": "🪵",
     "options": [{"label": "Bamboo Board", "url": "https://bash.com/amazon-tray-rect-marble-white-153003aaea0/p"}]},
    {"id": "toaster", "name": "Toaster", "description": "2-slice stainless steel toaster", "icon": "🍞",
     "options": [{"label": "Russell Hobbs Nexus", "url": "https://bash.com/russell-hobbs-nexus-2-slice-toaster-silver-153301abgo5/p"},
                 {"label": "Morphy Richards", "url": "https://www.checkers.co.za"}]},
    {"id": "stand-mixer", "name": "Electric Stand Mixer", "description": "6-speed tilt-head kitchen mixer, 1000–1500W", "icon": "🥣",
     "options": [{"label": "BezosMax 6.5Qt", "url": "https://www.makro.co.za/bezosmax-3-1-smart-display-stand-mixer-automatic-6-speed-tilt-head-food-dough-6-5-qt-kitchen-electric-mixer-bread-cake-baking-1500-w/p/itm7680f89832269"},
                 {"label": "Kambrook Aspire", "url": "https://clicks.co.za/kambrook_aspire-stand-mixer-with-stainless-steel-bowl-1000w/p/380678"}]},
    {"id": "waffle-maker", "name": "Waffle Maker", "description": "Classic round or square waffle maker", "icon": "🧇",
     "options": [{"label": "Sunbeam", "url": "https://www.takealot.com/sunbeam-waffle-maker/PLID73716549"},
                 {"label": "Cloud Market Round", "url": "https://www.amazon.co.za/Cloud-Market-Round-Classic-Waffle/dp/B0G2SNMHXY"}]},
    {"id": "bakeware", "name": "Bakeware Set", "description": "Non-stick stackable bakeware set (10 piece)", "icon": "🎂",
     "options": [{"label": "10-piece Stackable", "url": "https://www.takealot.com/best-10-piece-nonstick-stackable-bakeware-set/PLID100928532"},
                 {"label": "ALANES Non-Stick", "url": "https://www.amazon.co.za/ALANES-Non-Stick-Pan-Bakeware/dp/B0FP1X35F"}]},
    {"id": "coffee-maker", "name": "Coffee Maker", "description": "Espresso or Nespresso machine", "icon": "☕",
     "options": [{"label": "Nespresso Vertuo Pop", "url": "https://www.checkers.co.za"},
                 {"label": "Platinum Espresso 1100W", "url": "https://www.checkers.co.za"}]},
    {"id": "juicer", "name": "Juicer", "description": "Electric centrifugal juicer 1000W", "icon": "🍊",
     "options": [{"label": "Kuvings Auto6 Cold Press Juicer", "url": "https://premierhomeware.co.za/products/kuvings-auto6-cold-press-juicer?variant=43563110826035&country=ZA&currency=ZAR&utm_medium=product_sync&utm_source=google&utm_content=sag_organic&utm_campaign=sag_organic&utm_source=google&utm_medium=cpc&utm_term=&utm_adtype=pla&utm_campaign=&gad_source=1&gad_campaignid=22781206019&gbraid=0AAAAA-KQ-wZPtuiGw7d2DSyXqOPoCbiMS&gclid=CjwKCAjwwJzPBhBREiwAJfHRnfaiNOXUDsAwwDO2smbovFYR1BlUjYVU83zDRNOqVCcPSQpyBzQOExoClw8QAvD_BwE"}]},
    {"id": "dinnerware", "name": "Dinnerware Set", "description": "12-piece porcelain dinnerware set", "icon": "🍽️",
     "options": [{"label": "Ella 12-Piece Porcelain", "url": "https://bash.com/ella-12-piece-porcelain-dinnerware-white-153001aacz2/p"},
                 {"label": "Famiware 12-Piece", "url": "https://www.amazon.co.za/Famiware-Dinnerware-Pieces-Plates-Dishes/dp/B0BDL6F2RV"}]},
    {"id": "steamer", "name": "Clothes Steamer", "description": "Handheld or standing garment steamer", "icon": "👔",
     "options": [{"label": "Philips Handheld", "url": "https://www.checkers.co.za"},
                 {"label": "Standing Steam Iron", "url": "https://www.amazon.co.za/Standing-Steam-Iron-Garment-Electric/dp/B0G1SYX2M6"}]},
    {"id": "heater", "name": "Electric Heater", "description": "Infrared or ceramic fan heater", "icon": "🔥",
     "options": [{"label": "Infrared Radiant Heater", "url": "https://www.amazon.co.za/Infrared-Radiant-Electric-Certified-Warranty/dp/B0CVMYRNZ1"},
                 {"label": "DeLonghi Ceramic Fan", "url": "https://bash.com/delonghi-ceramic-fan-heater-hfx30c-18-ag-153301aadk1/p"}]},
    {"id": "fan", "name": "Pedestal Fan", "description": "40cm stand fan", "icon": "💨",
     "options": [{"label": "Alva Matt Black 40cm", "url": "https://bash.com/alva-pedestal-fan-matt-black-40cm-153301aaaz3/p"},
                 {"label": "Elektra Stand Fan", "url": "https://www.amazon.co.za/Elektra-Stand-Fan-Length-Black/dp/B0CMTZ26Y8"}]},
    {"id": "vacuum", "name": "Vacuum Cleaner", "description": "Bagless or drum vacuum cleaner", "icon": "🧹",
     "options": [{"label": "Philips 1800W Bagless", "url": "https://www.amazon.co.za/Philips-1800W-Bagless-Vacuum-Cleaner/dp/B0CSYY9KB4"},
                 {"label": "Hoover Drum Vacuum", "url": "https://www.amazon.co.za/Hoover-Stainless-Steel-Drum-Vacuum/dp/B0F1DD3955"}]},
]

MAX_PER_GIFT = 2

# ─────────────────────────────────────────
# HELPER: South African phone validation
# ─────────────────────────────────────────

def validate_sa_phone(phone):
    """Return True if phone is exactly 10 digits starting with 0."""
    cleaned = re.sub(r'\D', '', phone)   # remove spaces, dashes, etc.
    return bool(re.fullmatch(r'0\d{9}', cleaned))

# ─────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    token = request.args.get('token')
    guest = None
    if token:
        guest = Guest.query.filter_by(token=token).first()

    if request.method == 'POST':
        full_name  = request.form.get('full_name', '').strip()
        phone      = request.form.get('phone', '').strip()
        attending  = request.form.get('attending') == 'yes'
        form_token = request.form.get('token')

        # Validation
        if not full_name or not phone:
            flash('Please fill in your name and phone number.', 'error')
            return redirect(url_for('rsvp', token=form_token))

        if not validate_sa_phone(phone):
            flash('Please enter a valid South African cellphone number (10 digits, starting with 0).', 'error')
            return redirect(url_for('rsvp', token=form_token))

        # Prevent duplicate RSVP
        if form_token:
            guest_record = Guest.query.filter_by(token=form_token).first()
            if guest_record and guest_record.used:
                flash('You have already submitted your RSVP.', 'error')
                return redirect(url_for('rsvp', token=form_token))
        else:
            # For public RSVP (no token), check if phone number already used
            existing = RSVP.query.filter_by(phone=phone).first()
            if existing:
                flash('This phone number has already submitted an RSVP.', 'error')
                return redirect(url_for('rsvp'))

        # Mark guest as used if token exists
        if form_token:
            g = Guest.query.filter_by(token=form_token).first()
            if g:
                g.used = True

        new_rsvp = RSVP(
            guest_token=form_token or None,
            full_name=full_name,
            phone=phone,
            attending=attending
        )
        db.session.add(new_rsvp)
        db.session.commit()
        return redirect(url_for('thank_you', attending='yes' if attending else 'no'))

    return render_template('rsvp.html', guest=guest, token=token)

@app.route('/thank-you')
def thank_you():
    attending = request.args.get('attending', 'yes')
    return render_template('thank_you.html', attending=attending)

@app.route('/venue')
def venue():
    return render_template('venue.html')

@app.route('/stay')
def stay():
    return render_template('stay.html')

@app.route('/gifts')
def gifts():
    claims = {}
    for gift in GIFTS:
        count = GiftClaim.query.filter_by(gift_id=gift['id']).count()
        claims[gift['id']] = count
    return render_template('gifts.html', gifts=GIFTS, claims=claims, max_per=MAX_PER_GIFT)

@app.route('/gifts/claim', methods=['POST'])
def claim_gift():
    gift_id      = request.form.get('gift_id', '').strip()
    claimer_name = request.form.get('claimer_name', '').strip()
    claimer_phone = request.form.get('claimer_phone', '').strip()

    if not gift_id or not claimer_name or not claimer_phone:
        flash('Please fill in your name and phone number to claim a gift.', 'error')
        return redirect(url_for('gifts'))

    if not validate_sa_phone(claimer_phone):
        flash('Please enter a valid South African cellphone number (10 digits, starting with 0).', 'error')
        return redirect(url_for('gifts'))

    gift = next((g for g in GIFTS if g['id'] == gift_id), None)
    if not gift:
        flash('Gift not found.', 'error')
        return redirect(url_for('gifts'))

    # Check total availability (max 2 per gift)
    total_claimed = GiftClaim.query.filter_by(gift_id=gift_id).count()
    if total_claimed >= MAX_PER_GIFT:
        flash(f'Sorry, the {gift["name"]} has already been fully claimed.', 'error')
        return redirect(url_for('gifts'))

    # Prevent same person claiming same gift twice
    already_claimed = GiftClaim.query.filter_by(
        gift_id=gift_id,
        claimer_name=claimer_name,
        claimer_phone=claimer_phone
    ).first()
    if already_claimed:
        flash(f'You have already claimed the {gift["name"]}.', 'error')
        return redirect(url_for('gifts'))

    claim = GiftClaim(
        gift_id=gift_id,
        claimer_name=claimer_name,
        claimer_phone=claimer_phone
    )
    db.session.add(claim)
    db.session.commit()
    flash(f'Thank you, {claimer_name}! You have claimed the {gift["name"]}. 🎁', 'success')
    return redirect(url_for('gifts'))

@app.route('/invite/<token>')
def personalized_invite(token):
    guest = Guest.query.filter_by(token=token).first_or_404()
    if guest.used:
        return render_template('already_rsvpd.html', guest=guest)
    return render_template('invite.html', guest=guest)

# ─────────────────────────────────────────
# ADMIN ROUTES
# ─────────────────────────────────────────

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'busieian2026')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Incorrect password.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    rsvps    = RSVP.query.order_by(RSVP.submitted_at.desc()).all()
    guests   = Guest.query.order_by(Guest.created_at.desc()).all()
    claims   = GiftClaim.query.order_by(GiftClaim.claimed_at.desc()).all()
    total    = len(rsvps)
    attending= sum(1 for r in rsvps if r.attending)
    declined = sum(1 for r in rsvps if not r.attending)

    gift_summary = []
    for gift in GIFTS:
        count = GiftClaim.query.filter_by(gift_id=gift['id']).count()
        gift_summary.append({
            'name': gift['name'],
            'id': gift['id'],
            'claimed': count,
            'remaining': MAX_PER_GIFT - count
        })

    return render_template('admin/dashboard.html',
                           rsvps=rsvps, guests=guests, claims=claims,
                           total=total, attending=attending, declined=declined,
                           gift_summary=gift_summary)

@app.route('/admin/create-invite', methods=['POST'])
@admin_required
def create_invite():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Guest name is required.', 'error')
        return redirect(url_for('admin_dashboard'))

    token = secrets.token_urlsafe(8)
    guest = Guest(name=name, token=token)
    db.session.add(guest)
    db.session.commit()

    invite_url = url_for('personalized_invite', token=token, _external=True)
    qr = qrcode.make(invite_url)
    os.makedirs(os.path.join(app.root_path, 'static', 'qrcodes'), exist_ok=True)
    qr_path = os.path.join(app.root_path, 'static', 'qrcodes', f'{token}.png')
    qr.save(qr_path)

    flash(f'Invite created for {name}. Token: {token}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/qr/<token>')
@admin_required
def download_qr(token):
    from flask import abort
    path = os.path.join(app.root_path, 'static', 'qrcodes', f'{token}.png')
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name=f'invite-{token}.png')

@app.route('/admin/export')
@admin_required
def export_csv():
    rsvps = RSVP.query.order_by(RSVP.submitted_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Phone', 'Attending', 'Submitted'])
    for r in rsvps:
        writer.writerow([
            r.full_name, r.phone,
            'Yes' if r.attending else 'No',
            r.submitted_at.strftime('%d %b %Y %H:%M')
        ])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='rsvps.csv')

@app.route('/admin/export-gifts')
@admin_required
def export_gifts_csv():
    claims = GiftClaim.query.order_by(GiftClaim.claimed_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Gift', 'Claimer Name', 'Claimer Phone', 'Claimed At'])
    for c in claims:
        gift = next((g for g in GIFTS if g['id'] == c.gift_id), None)
        writer.writerow([
            gift['name'] if gift else c.gift_id,
            c.claimer_name, c.claimer_phone,
            c.claimed_at.strftime('%d %b %Y %H:%M')
        ])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='gift-claims.csv')

# ─────────────────────────────────────────
# INIT DATABASE
# ─────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)