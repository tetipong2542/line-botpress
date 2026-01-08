"""
Export Service - Export user data to CSV/JSON
"""
import csv
import json
import io
from datetime import datetime
from flask import Response
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.recurring import RecurringRule
from app.models.project import Project
from sqlalchemy import func


class ExportService:
    """Service for exporting user data"""

    @staticmethod
    def export_to_csv(project_id, month_yyyymm=None):
        """Export transactions to CSV format"""
        # Get all transactions for project
        query = Transaction.query.filter_by(project_id=project_id)
        
        if month_yyyymm:
            # Filter by month
            start_date = datetime.strptime(f"{month_yyyymm}-01", '%Y-%m-%d')
            if month_yyyymm.endswith('12'):
                end_date = datetime.strptime(f"{int(month_yyyymm[:4]) + 1}-01-01", '%Y-%m-%d')
            else:
                end_date = datetime.strptime(f"{month_yyyymm[:4]}-{int(month_yyyymm[5:]) + 1:02d}-01", '%Y-%m-%d')
            query = query.filter(Transaction.occurred_at >= start_date, Transaction.occurred_at < end_date)
        
        transactions = query.order_by(Transaction.occurred_at.desc()).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'วันที่เวลา',
            'ประเภท',
            'หมวดหมู่',
            'รายละเอียด',
            'จำนวนเงิน (บาท)',
            'ID'
        ])
        
        # Data rows
        for tx in transactions:
            category = tx.category
            writer.writerow([
                tx.occurred_at.strftime('%Y-%m-%d %H:%M:%S') if tx.occurred_at else '',
                'รายรับ' if tx.type == 'income' else 'รายจ่าย',
                category.name_th if category else 'ไม่ระบุ',
                tx.note or '',
                f"{tx.amount / 100:.2f}",
                tx.id
            ])
        
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def export_to_json(project_id, month_yyyymm=None):
        """Export all project data to JSON format"""
        # Get project
        project = Project.query.get(project_id)
        if not project:
            return None
        
        # Get transactions
        query = Transaction.query.filter_by(project_id=project_id)
        if month_yyyymm:
            start_date = datetime.strptime(f"{month_yyyymm}-01", '%Y-%m-%d')
            if month_yyyymm.endswith('12'):
                end_date = datetime.strptime(f"{int(month_yyyymm[:4]) + 1}-01-01", '%Y-%m-%d')
            else:
                end_date = datetime.strptime(f"{month_yyyymm[:4]}-{int(month_yyyymm[5:]) + 1:02d}-01", '%Y-%m-%d')
            query = query.filter(Transaction.occurred_at >= start_date, Transaction.occurred_at < end_date)
        
        transactions = query.order_by(Transaction.occurred_at.desc()).all()
        
        # Get categories
        categories = Category.query.filter_by(project_id=project_id).order_by(Category.sort_order).all()
        
        # Get budgets
        budgets = Budget.query.filter_by(project_id=project_id).all()
        
        # Get recurring rules
        recurring_rules = RecurringRule.query.filter_by(project_id=project_id).filter_by(is_active=True).all()
        
        # Calculate summary
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expense = sum(t.amount for t in transactions if t.type == 'expense')
        balance = total_income - total_expense
        
        # Build JSON structure
        export_data = {
            'export_info': {
                'project_id': project.id,
                'project_name': project.name,
                'exported_at': datetime.utcnow().isoformat(),
                'month_filter': month_yyyymm,
                'total_transactions': len(transactions)
            },
            'summary': {
                'total_income_satang': total_income,
                'total_income_baht': total_income / 100,
                'total_expense_satang': total_expense,
                'total_expense_baht': total_expense / 100,
                'balance_satang': balance,
                'balance_baht': balance / 100
            },
            'transactions': [
                {
                    'id': tx.id,
                    'type': tx.type,
                    'occurred_at': tx.occurred_at.isoformat() if tx.occurred_at else None,
                    'category_id': tx.category_id,
                    'category_name': tx.category.name_th if tx.category else None,
                    'amount_satang': tx.amount,
                    'amount_baht': tx.amount / 100,
                    'note': tx.note
                }
                for tx in transactions
            ],
            'categories': [
                {
                    'id': cat.id,
                    'type': cat.type,
                    'name_th': cat.name_th,
                    'icon': cat.icon,
                    'color': cat.color,
                    'is_active': cat.is_active,
                    'sort_order': cat.sort_order
                }
                for cat in categories
            ],
            'budgets': [
                {
                    'id': budget.id,
                    'month_yyyymm': budget.month_yyyymm,
                    'category_id': budget.category_id,
                    'category_name': budget.category.name_th if budget.category else None,
                    'limit_amount_satang': budget.limit_amount,
                    'limit_amount_baht': budget.limit_amount / 100,
                    'rollover_policy': budget.rollover_policy
                }
                for budget in budgets
            ],
            'recurring_rules': [
                {
                    'id': rule.id,
                    'category_id': rule.category_id,
                    'category_name': rule.category.name_th if rule.category else None,
                    'amount_satang': rule.amount,
                    'amount_baht': rule.amount / 100,
                    'frequency': rule.frequency,
                    'note': rule.note,
                    'next_run_date': rule.next_run_date.isoformat() if rule.next_run_date else None
                }
                for rule in recurring_rules
            ]
        }
        
        return export_data

    @staticmethod
    def create_csv_response(data, filename):
        """Create Flask CSV response"""
        response = Response(
            data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        return response

    @staticmethod
    def create_json_response(data, filename):
        """Create Flask JSON response"""
        response = Response(
            json.dumps(data, ensure_ascii=False, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        return response

    @staticmethod
    def generate_filename(project_name, format_type, month_yyyymm=None):
        """Generate filename for export"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if month_yyyymm:
            return f"{project_name}_transactions_{month_yyyymm}_{timestamp}.{format_type}"
        else:
            return f"{project_name}_all_data_{timestamp}.{format_type}"

    @staticmethod
    def get_export_summary(project_id):
        """Get summary of export data"""
        total_transactions = Transaction.query.filter_by(project_id=project_id).count()
        total_categories = Category.query.filter_by(project_id=project_id).count()
        total_budgets = Budget.query.filter_by(project_id=project_id).count()
        total_recurring = RecurringRule.query.filter_by(project_id=project_id, is_active=True).count()
        
        # Get oldest and newest transaction
        oldest = Transaction.query.filter_by(project_id=project_id).order_by(Transaction.occurred_at.asc()).first()
        newest = Transaction.query.filter_by(project_id=project_id).order_by(Transaction.occurred_at.desc()).first()
        
        return {
            'total_transactions': total_transactions,
            'total_categories': total_categories,
            'total_budgets': total_budgets,
            'total_recurring': total_recurring,
            'oldest_transaction': oldest.occurred_at.isoformat() if oldest and oldest.occurred_at else None,
            'newest_transaction': newest.occurred_at.isoformat() if newest and newest.occurred_at else None
        }
