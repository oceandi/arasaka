#!/usr/bin/env python3
"""
Initial user and region setup script
"""

from app import app, db, User, Region
from datetime import datetime

def create_initial_data():
    """Create initial users and regions"""
    
    with app.app_context():
        # Create regions
        regions_data = [
            {'name': 'Bursa', 'code': 'BURSA'},
            {'name': 'Kocaeli', 'code': 'KOCAELI'},
            {'name': 'İstanbul', 'code': 'ISTANBUL'},
            {'name': 'Ankara', 'code': 'ANKARA'},
            {'name': 'İzmir', 'code': 'IZMIR'}
        ]
        
        for region_data in regions_data:
            existing_region = Region.query.filter_by(code=region_data['code']).first()
            if not existing_region:
                region = Region(
                    name=region_data['name'],
                    code=region_data['code'],
                    active=True
                )
                db.session.add(region)
                print(f"✓ Bölge eklendi: {region_data['name']}")
        
        # Create initial users
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@karel.com.tr',
                'password': 'Karel2024!',
                'role': 'super_admin',
                'region': None  # Super admin can access all regions
            },
            {
                'username': 'karel_bursa',
                'email': 'karel.bursa@karel.com.tr',
                'password': 'Karel2024!',
                'role': 'karel_user',
                'region': 'Bursa'
            },
            {
                'username': 'karel_kocaeli',
                'email': 'karel.kocaeli@karel.com.tr',
                'password': 'Karel2024!',
                'role': 'karel_user',
                'region': 'Kocaeli'
            },
            {
                'username': 'bayi_bursa',
                'email': 'bayi.bursa@example.com',
                'password': 'Bayi2024!',
                'role': 'bayi_user',
                'region': 'Bursa'
            },
            {
                'username': 'admin_bursa',
                'email': 'admin.bursa@turkcell.com.tr',
                'password': 'Admin2024!',
                'role': 'admin',
                'region': 'Bursa'
            },
            {
                'username': 'onur',
                'email': 'onur@karel.com.tr',
                'password': 'Onur2024!',
                'role': 'super_admin',
                'region': None  # Developer access
            }
        ]
        
        for user_data in users_data:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role'],
                    region=user_data['region'],
                    active=True,
                    created_at=datetime.utcnow()
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                print(f"✓ Kullanıcı eklendi: {user_data['username']} ({user_data['role']})")
        
        db.session.commit()
        print("\n✅ Initial data created successfully!")
        
        # Print login credentials
        print("\n📋 Login Credentials:")
        print("=" * 50)
        for user_data in users_data:
            print(f"Username: {user_data['username']}")
            print(f"Password: {user_data['password']}")
            print(f"Role: {user_data['role']}")
            print(f"Region: {user_data['region'] or 'All'}")
            print("-" * 30)

if __name__ == '__main__':
    create_initial_data()