"""
Transaction service - Business logic for transactions
"""
from datetime import datetime
from app import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.project import Project, ProjectMember
from app.utils.validators import validate_transaction_type, validate_amount
from app.utils.helpers import baht_to_satang


class TransactionService:
    """Service for transaction operations"""

    @staticmethod
    def create_transaction(project_id, user_id, type, category_id, amount,
                          occurred_at=None, note=None, member_id=None):
        """
        Create a new transaction

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            type: Transaction type ('income' or 'expense')
            category_id: Category ID
            amount: Amount (in satang or baht - will be converted)
            occurred_at: DateTime when transaction occurred (default: now)
            note: Optional note
            member_id: Optional member ID

        Returns:
            Transaction object

        Raises:
            ValueError: If validation fails
            PermissionError: If user doesn't have access
        """
        # Check user has access to project
        if not TransactionService._check_project_access(project_id, user_id):
            raise PermissionError("User doesn't have access to this project")

        # Validate inputs
        type = validate_transaction_type(type)

        # Check category exists and belongs to project
        category = Category.query.get(category_id)
        if not category or category.project_id != project_id:
            raise ValueError("Invalid category for this project")

        # Validate category type matches transaction type
        if category.type != type:
            raise ValueError(f"Category type mismatch: category is {category.type}, transaction is {type}")

        # Convert amount to satang if needed
        if isinstance(amount, float):
            amount = baht_to_satang(amount)
        amount = validate_amount(amount)

        # Parse occurred_at
        if occurred_at and isinstance(occurred_at, str):
            occurred_at = datetime.fromisoformat(occurred_at.replace('Z', '+00:00'))

        # Create transaction
        transaction = Transaction(
            project_id=project_id,
            type=type,
            category_id=category_id,
            amount=amount,
            occurred_at=occurred_at,
            note=note,
            member_id=member_id
        )

        db.session.add(transaction)
        db.session.commit()

        return transaction

    @staticmethod
    def get_transactions(project_id, user_id, filters=None):
        """
        Get transactions with filters

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            filters: Dictionary of filters (type, category_id, from_date, to_date, etc.)

        Returns:
            List of Transaction objects
        """
        # Check access
        if not TransactionService._check_project_access(project_id, user_id):
            raise PermissionError("User doesn't have access to this project")

        query = Transaction.query.filter_by(
            project_id=project_id,
            deleted_at=None
        )

        # Apply filters
        if filters:
            if filters.get('type'):
                query = query.filter_by(type=filters['type'])

            if filters.get('category_id'):
                query = query.filter_by(category_id=filters['category_id'])

            if filters.get('from_date'):
                from_date = datetime.fromisoformat(filters['from_date'].replace('Z', '+00:00'))
                query = query.filter(Transaction.occurred_at >= from_date)

            if filters.get('to_date'):
                to_date = datetime.fromisoformat(filters['to_date'].replace('Z', '+00:00'))
                query = query.filter(Transaction.occurred_at <= to_date)

            if filters.get('member_id'):
                query = query.filter_by(member_id=filters['member_id'])

        # Order by occurred_at descending
        query = query.order_by(Transaction.occurred_at.desc())

        # Pagination
        page = filters.get('page', 1) if filters else 1
        per_page = filters.get('per_page', 50) if filters else 50

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def update_transaction(transaction_id, user_id, updates):
        """
        Update a transaction

        Args:
            transaction_id: Transaction ID
            user_id: User ID (for permission check)
            updates: Dictionary of fields to update

        Returns:
            Updated Transaction object
        """
        transaction = Transaction.query.get(transaction_id)

        if not transaction or transaction.deleted_at:
            raise ValueError("Transaction not found")

        # Check access
        if not TransactionService._check_project_access(transaction.project_id, user_id):
            raise PermissionError("User doesn't have access to this transaction")

        # Update fields
        if 'amount' in updates:
            amount = updates['amount']
            if isinstance(amount, float):
                amount = baht_to_satang(amount)
            transaction.amount = validate_amount(amount)

        if 'type' in updates:
            transaction.type = validate_transaction_type(updates['type'])

        if 'category_id' in updates:
            category = Category.query.get(updates['category_id'])
            if not category or category.project_id != transaction.project_id:
                raise ValueError("Invalid category for this project")
            transaction.category_id = updates['category_id']

        if 'occurred_at' in updates:
            occurred_at = updates['occurred_at']
            if isinstance(occurred_at, str):
                occurred_at = datetime.fromisoformat(occurred_at.replace('Z', '+00:00'))
            transaction.occurred_at = occurred_at

        if 'note' in updates:
            transaction.note = updates['note']

        if 'member_id' in updates:
            transaction.member_id = updates['member_id']

        db.session.commit()

        return transaction

    @staticmethod
    def delete_transaction(transaction_id, user_id):
        """
        Soft delete a transaction

        Args:
            transaction_id: Transaction ID
            user_id: User ID (for permission check)

        Returns:
            True if successful
        """
        transaction = Transaction.query.get(transaction_id)

        if not transaction or transaction.deleted_at:
            raise ValueError("Transaction not found")

        # Check access
        if not TransactionService._check_project_access(transaction.project_id, user_id):
            raise PermissionError("User doesn't have access to this transaction")

        # Soft delete
        transaction.deleted_at = datetime.utcnow()
        db.session.commit()

        return True

    @staticmethod
    def _check_project_access(project_id, user_id):
        """
        Check if user has access to project

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            bool: True if user has access
        """
        # Check if user is owner
        project = Project.query.get(project_id)
        if project and project.owner_user_id == user_id:
            return True

        # Check if user is member
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()

        return member is not None
