from flask import Blueprint, render_template, request, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/gallery')
def gallery():
    return render_template('gallery.html')

@main_bp.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == 'POST':
        # Placeholder — will save to DB later when we add reservations table
        return jsonify({"success": True})
    return render_template('reservations.html')