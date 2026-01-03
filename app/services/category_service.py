"""
Category service - Business logic for categories
"""
from app import db
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.project import Project, ProjectMember
from app.utils.validators import validate_transaction_type, validate_category_name, validate_color_hex
from app.utils.helpers import generate_id


class CategoryService:
    """Service for category operations"""

    @staticmethod
    def create_category(project_id, user_id, name_th, type, icon=None, color=None):
        """
        Create a new category

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            name_th: Category name in Thai
            type: Category type ('income' or 'expense')
            icon: Icon (emoji or lucide icon name)
            color: Hex color code

        Returns:
            Category object

        Raises:
            ValueError: If validation fails
            PermissionError: If user doesn't have access
        """
        # Check user has access to project
        if not CategoryService._check_project_access(project_id, user_id):
            raise PermissionError("User doesn't have access to this project")

        # Validate inputs
        name_th = validate_category_name(name_th)
        type = validate_transaction_type(type)

        if color:
            color = validate_color_hex(color)

        # Get max sort_order for this project and type
        max_sort = db.session.query(db.func.max(Category.sort_order)).filter_by(
            project_id=project_id,
            type=type
        ).scalar() or 0

        # Create category
        category = Category(
            project_id=project_id,
            type=type,
            name_th=name_th,
            icon=icon or '📁',
            color=color or '#6B7280',
            sort_order=max_sort + 1
        )

        db.session.add(category)
        db.session.commit()

        return category

    @staticmethod
    def update_category(category_id, user_id, updates):
        """
        Update a category

        Args:
            category_id: Category ID
            user_id: User ID (for permission check)
            updates: Dictionary of fields to update

        Returns:
            Updated Category object
        """
        category = Category.query.get(category_id)

        if not category or not category.is_active:
            raise ValueError("Category not found")

        # Check access
        if not CategoryService._check_project_access(category.project_id, user_id):
            raise PermissionError("User doesn't have access to this category")

        # Update fields
        if 'name_th' in updates:
            category.name_th = validate_category_name(updates['name_th'])

        if 'icon' in updates:
            category.icon = updates['icon']

        if 'color' in updates:
            color = updates['color']
            if color:
                color = validate_color_hex(color)
            category.color = color

        if 'sort_order' in updates:
            category.sort_order = int(updates['sort_order'])

        db.session.commit()

        return category

    @staticmethod
    def delete_category(category_id, user_id):
        """
        Soft delete a category

        Checks if category has transactions and warns user

        Args:
            category_id: Category ID
            user_id: User ID (for permission check)

        Returns:
            dict: Success status and warning if category has transactions
        """
        category = Category.query.get(category_id)

        if not category or not category.is_active:
            raise ValueError("Category not found")

        # Check access
        if not CategoryService._check_project_access(category.project_id, user_id):
            raise PermissionError("User doesn't have access to this category")

        # Check if category has transactions
        transaction_count = Transaction.query.filter_by(
            category_id=category_id,
            deleted_at=None
        ).count()

        # Soft delete
        category.is_active = False
        db.session.commit()

        result = {
            'success': True,
            'transaction_count': transaction_count
        }

        if transaction_count > 0:
            result['warning'] = f'หมวดหมู่นี้มีรายการบันทึก {transaction_count} รายการ แต่ถูกลบเรียบร้อยแล้ว'

        return result

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
