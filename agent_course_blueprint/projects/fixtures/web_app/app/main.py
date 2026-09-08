"""Main application module"""

from flask import Flask, render_template, jsonify

app = Flask(__name__)


@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        "status": "ok",
        "version": "1.0.0"
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
