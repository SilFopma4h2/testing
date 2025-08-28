#!/usr/bin/env python3
"""
Flask backend for Patte Conservation website
Provides API endpoints for financial data, campaigns, and crypto addresses
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Sample data - in a real application, this would come from a database
FINANCIAL_DATA = {
    "year": 2024,
    "total_donations": 285000,
    "program_expenses": 228000,
    "admin_expenses": 34200,
    "fundraising_expenses": 22800,
    "total_expenses": 285000,
    "active_campaigns": [
        {"id": 1, "name": "Coral Restoration"},
        {"id": 2, "name": "Marine Education"},
        {"id": 3, "name": "Sustainable Fishing"}
    ]
}

TRANSPARENCY_DATA = {
    "program_percentage": 80,
    "admin_percentage": 12,
    "fundraising_percentage": 8,
    "efficiency_rating": "A+"
}

CAMPAIGNS_DATA = [
    {
        "id": 1,
        "name": "Coral Restoration Project",
        "description": "Restoring damaged coral reefs through community-based conservation efforts",
        "goal_amount": 50000,
        "raised_amount": 35000,
        "progress": 70
    },
    {
        "id": 2,
        "name": "Marine Education Program",
        "description": "Teaching local communities sustainable fishing practices and marine conservation",
        "goal_amount": 30000,
        "raised_amount": 22500,
        "progress": 75
    },
    {
        "id": 3,
        "name": "Sustainable Fishing Initiative",
        "description": "Supporting local fishermen with sustainable equipment and training",
        "goal_amount": 40000,
        "raised_amount": 16000,
        "progress": 40
    }
]

CRYPTO_ADDRESSES = {
    "bitcoin": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "ethereum": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
}

# Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# API Endpoints
@app.route('/api/financial/overview')
def financial_overview():
    """Get financial overview data"""
    return jsonify(FINANCIAL_DATA)

@app.route('/api/financial/transparency')
def financial_transparency():
    """Get financial transparency data"""
    return jsonify(TRANSPARENCY_DATA)

@app.route('/api/financial/campaigns')
def financial_campaigns():
    """Get active campaigns data"""
    return jsonify(CAMPAIGNS_DATA)

@app.route('/api/financial/impact-calculator', methods=['POST'])
def impact_calculator():
    """Calculate impact of a donation amount"""
    data = request.get_json()
    amount = float(data.get('amount', 0))
    
    # Calculate impact based on donation amount
    # These are example ratios - adjust based on real impact metrics
    families_helped = int(amount // 45)  # $45 per family on average
    meals_provided = int(amount * 4)     # 4 meals per dollar
    clean_water_days = int(amount * 2)   # 2 days of clean water per dollar
    education_hours = int(amount / 5)    # 1 hour of education per $5
    
    impact = {
        "families_helped": families_helped,
        "meals_provided": meals_provided,
        "clean_water_days": clean_water_days,
        "education_hours": education_hours
    }
    
    return jsonify({"impact": impact})

@app.route('/api/crypto-addresses')
def crypto_addresses():
    """Get cryptocurrency addresses for donations"""
    return jsonify({
        "success": True,
        "addresses": CRYPTO_ADDRESSES
    })

# Health check endpoint
@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Patte Conservation Backend Server on port {port}")
    print(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)