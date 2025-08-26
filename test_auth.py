#!/usr/bin/env python3
"""
Test script for user authentication and payment system
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    user_data = {
        'username': 'testuser2',
        'email': 'test2@gmail.com',
        'password': 'testpass123',
        'first_name': 'Jane',
        'last_name': 'Doe',
        'phone': '+1987654321'
    }
    
    response = requests.post(f'{BASE_URL}/api/register', json=user_data)
    result = response.json()
    
    if result['success']:
        print("✓ Registration successful")
        return response.cookies
    else:
        print(f"✗ Registration failed: {result['message']}")
        return None

def test_login(cookies):
    """Test user login"""
    print("Testing user login...")
    
    login_data = {
        'login': 'testuser2',
        'password': 'testpass123'
    }
    
    response = requests.post(f'{BASE_URL}/api/login', json=login_data, cookies=cookies)
    result = response.json()
    
    if result['success']:
        print("✓ Login successful")
        return response.cookies
    else:
        print(f"✗ Login failed: {result['message']}")
        return None

def test_donation(cookies):
    """Test donation with payment tracking"""
    print("Testing donation with payment tracking...")
    
    donation_data = {
        'donorName': 'Jane Doe',
        'donorEmail': 'test2@gmail.com',
        'amount': '100',
        'paymentMethod': 'mpesa',
        'donationType': 'one-time',
        'projectSelection': 'healthcare'
    }
    
    response = requests.post(f'{BASE_URL}/api/donate', json=donation_data, cookies=cookies)
    result = response.json()
    
    if result['success']:
        print(f"✓ Donation successful - Transaction ID: {result.get('transactionId')}")
        return result.get('transactionId')
    else:
        print(f"✗ Donation failed: {result['message']}")
        return None

def test_user_payments(cookies):
    """Test fetching user payments"""
    print("Testing user payments retrieval...")
    
    response = requests.get(f'{BASE_URL}/api/payments', cookies=cookies)
    result = response.json()
    
    if result['success']:
        print(f"✓ Retrieved {len(result['payments'])} payments")
        for payment in result['payments']:
            print(f"  - ${payment['amount']} via {payment['payment_method']} ({payment['payment_status']})")
    else:
        print(f"✗ Failed to retrieve payments: {result['message']}")

def test_user_dashboard(cookies):
    """Test user dashboard"""
    print("Testing user dashboard...")
    
    response = requests.get(f'{BASE_URL}/api/user/dashboard', cookies=cookies)
    result = response.json()
    
    if result['success']:
        dashboard = result['dashboard']
        print("✓ Dashboard retrieved successfully")
        print(f"  - User: {dashboard['user']['first_name']} {dashboard['user']['last_name']}")
        print(f"  - Total donated: ${dashboard['stats']['total_donated']}")
        print(f"  - Donation count: {dashboard['stats']['donation_count']}")
        print(f"  - Recent donations: {len(dashboard['recent_donations'])}")
    else:
        print(f"✗ Dashboard retrieval failed: {result['message']}")

def test_admin_stats():
    """Test admin stats endpoint"""
    print("Testing admin stats...")
    
    response = requests.get(f'{BASE_URL}/api/admin/stats')
    result = response.json()
    
    if 'error' not in result:
        print("✓ Admin stats retrieved")
        print(f"  - Registered users: {result['registered_users']}")
        print(f"  - Total donations: ${result['total_donations']}")
        print(f"  - Total payments: {result['payments']}")
    else:
        print(f"✗ Admin stats failed: {result['error']}")

def main():
    print("🚀 Testing Authentication and Payment System\n")
    
    # Test registration
    cookies = test_registration()
    if not cookies:
        return
    
    # Test login (updates cookies)
    cookies = test_login(cookies)
    if not cookies:
        return
    
    # Test donation
    transaction_id = test_donation(cookies)
    
    # Test payments retrieval
    test_user_payments(cookies)
    
    # Test dashboard
    test_user_dashboard(cookies)
    
    # Test admin stats
    test_admin_stats()
    
    print("\n✅ All tests completed!")

if __name__ == '__main__':
    main()