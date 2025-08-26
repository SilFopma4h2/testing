#!/usr/bin/env python3
"""
Sample data seeder for Hope Foundation Financial Features
"""
from app import app, db, Expense, Budget, Campaign, FinancialReport
from datetime import datetime, timedelta
import json

def seed_sample_data():
    """Add sample financial data"""
    with app.app_context():
        # Clear existing data
        print("Clearing existing financial data...")
        Expense.query.delete()
        Budget.query.delete()
        Campaign.query.delete()
        FinancialReport.query.delete()
        
        # Add sample expenses
        print("Adding sample expenses...")
        sample_expenses = [
            {
                'description': 'Water well construction in Kenya',
                'amount': 15000,
                'category': 'program',
                'project': 'water-access',
                'status': 'approved',
                'date': datetime.now() - timedelta(days=30)
            },
            {
                'description': 'School supplies for Uganda project',
                'amount': 5000,
                'category': 'program',
                'project': 'education-support',
                'status': 'approved',
                'date': datetime.now() - timedelta(days=15)
            },
            {
                'description': 'Medical clinic equipment',
                'amount': 8000,
                'category': 'program',
                'project': 'healthcare-access',
                'status': 'approved',
                'date': datetime.now() - timedelta(days=10)
            },
            {
                'description': 'Office rent and utilities',
                'amount': 2500,
                'category': 'admin',
                'status': 'approved',
                'date': datetime.now() - timedelta(days=5)
            },
            {
                'description': 'Staff salaries',
                'amount': 12000,
                'category': 'admin',
                'status': 'approved',
                'date': datetime.now() - timedelta(days=3)
            },
            {
                'description': 'Marketing and outreach materials',
                'amount': 1500,
                'category': 'fundraising',
                'status': 'approved',
                'date': datetime.now() - timedelta(days=1)
            }
        ]
        
        for expense_data in sample_expenses:
            expense = Expense(**expense_data)
            db.session.add(expense)
        
        # Add sample budgets
        print("Adding sample budgets...")
        current_year = datetime.now().year
        sample_budgets = [
            {
                'name': f'Water Access Program {current_year}',
                'year': current_year,
                'category': 'program',
                'allocated_amount': 50000,
                'spent_amount': 15000,
                'project': 'water-access'
            },
            {
                'name': f'Education Support {current_year}',
                'year': current_year,
                'category': 'program',
                'allocated_amount': 30000,
                'spent_amount': 5000,
                'project': 'education-support'
            },
            {
                'name': f'Healthcare Access {current_year}',
                'year': current_year,
                'category': 'program',
                'allocated_amount': 40000,
                'spent_amount': 8000,
                'project': 'healthcare-access'
            },
            {
                'name': f'Administrative Costs {current_year}',
                'year': current_year,
                'category': 'admin',
                'allocated_amount': 18000,
                'spent_amount': 14500
            },
            {
                'name': f'Fundraising {current_year}',
                'year': current_year,
                'category': 'fundraising',
                'allocated_amount': 6000,
                'spent_amount': 1500
            }
        ]
        
        for budget_data in sample_budgets:
            budget = Budget(**budget_data)
            db.session.add(budget)
        
        # Add sample campaigns
        print("Adding sample campaigns...")
        sample_campaigns = [
            {
                'name': 'Clean Water for Kenya Villages',
                'description': 'Help us build 5 new water wells in rural Kenya to provide clean, safe drinking water for over 2,000 families.',
                'goal_amount': 75000,
                'raised_amount': 42800,
                'project_category': 'water-access',
                'end_date': datetime.now() + timedelta(days=60)
            },
            {
                'name': 'School Lunch Program Expansion',
                'description': 'Expand our nutritious school meal program to reach 1,000 more children in Uganda and Tanzania.',
                'goal_amount': 25000,
                'raised_amount': 18200,
                'project_category': 'education-support',
                'end_date': datetime.now() + timedelta(days=45)
            },
            {
                'name': 'Mobile Health Clinic Initiative',
                'description': 'Launch a mobile health clinic to bring medical care to remote communities in Ghana.',
                'goal_amount': 50000,
                'raised_amount': 28500,
                'project_category': 'healthcare-access',
                'end_date': datetime.now() + timedelta(days=90)
            }
        ]
        
        for campaign_data in sample_campaigns:
            campaign = Campaign(**campaign_data)
            db.session.add(campaign)
        
        # Add a sample financial report
        print("Adding sample financial report...")
        report_data = {
            'income_breakdown': {
                'donations': 85000,
                'grants': 25000,
                'fundraising_events': 12000
            },
            'expense_breakdown': {
                'program': 44000,
                'admin': 14500,
                'fundraising': 1500
            },
            'program_impact': {
                'families_served': 850,
                'children_educated': 450,
                'medical_treatments': 320
            }
        }
        
        financial_report = FinancialReport(
            title=f'Annual Financial Report {current_year}',
            report_type='annual',
            year=current_year,
            total_income=122000,
            total_expenses=60000,
            program_expenses=44000,
            admin_expenses=14500,
            fundraising_expenses=1500,
            net_result=62000,
            report_data=json.dumps(report_data)
        )
        db.session.add(financial_report)
        
        # Commit all changes
        db.session.commit()
        print("✅ Sample financial data added successfully!")
        
        # Print summary
        print("\n📊 Financial Data Summary:")
        print(f"- Expenses: {Expense.query.count()}")
        print(f"- Budgets: {Budget.query.count()}")
        print(f"- Campaigns: {Campaign.query.count()}")
        print(f"- Reports: {FinancialReport.query.count()}")

if __name__ == '__main__':
    seed_sample_data()