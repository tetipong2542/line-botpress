"""
Member service - Business logic for project members and invitations
"""
from datetime import datetime
import secrets
from app import db
from app.models.project import Project, ProjectMember, ProjectInvite
from app.models.user import User
from app.utils.validators import validate_email, validate_role


class MemberService:
    """Service for member management operations"""

    @staticmethod
    def invite_member(project_id, inviter_user_id, invitee_email, role='member'):
        """
        Send invitation to new member

        Args:
            project_id: Project ID
            inviter_user_id: User ID of inviter (must be owner/admin)
            invitee_email: Email of person to invite
            role: Role to assign ('member' or 'admin')

        Returns:
            ProjectInvite object

        Raises:
            ValueError: If validation fails
            PermissionError: If inviter doesn't have permission
        """
        # Check inviter has admin access
        if not MemberService._check_admin_access(project_id, inviter_user_id):
            raise PermissionError("Only project owner or admin can invite members")

        # Validate email and role
        invitee_email = validate_email(invitee_email)
        role = validate_role(role)

        # Check if user already member
        invitee_user = User.query.filter_by(email=invitee_email).first()
        if invitee_user:
            existing_member = ProjectMember.query.filter_by(
                project_id=project_id,
                user_id=invitee_user.id
            ).first()
            if existing_member:
                raise ValueError("User is already a member of this project")

        # Check if invitation already exists
        existing_invite = ProjectInvite.query.filter_by(
            project_id=project_id,
            email=invitee_email,
            status='pending'
        ).first()
        if existing_invite:
            raise ValueError("Invitation already sent to this email")

        # Generate invite token
        token = secrets.token_urlsafe(32)

        # Create invitation
        invite = ProjectInvite(
            project_id=project_id,
            email=invitee_email,
            role=role,
            token=token,
            invited_by=inviter_user_id
        )

        db.session.add(invite)
        db.session.commit()

        # TODO: Send email/LINE notification

        return invite

    @staticmethod
    def get_project_members(project_id, user_id):
        """
        List all members of project

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)

        Returns:
            List of ProjectMember objects with user info
        """
        # Check access
        if not MemberService._check_project_access(project_id, user_id):
            raise PermissionError("User doesn't have access to this project")

        members = ProjectMember.query.filter_by(project_id=project_id).all()

        return members

    @staticmethod
    def update_member_role(member_id, user_id, new_role):
        """
        Update member role

        Args:
            member_id: ProjectMember ID
            user_id: User ID (must be owner)
            new_role: New role ('admin' or 'member')

        Returns:
            Updated ProjectMember object
        """
        member = ProjectMember.query.get(member_id)

        if not member:
            raise ValueError("Member not found")

        # Only owner can change roles
        project = Project.query.get(member.project_id)
        if not project or project.owner_user_id != user_id:
            raise PermissionError("Only project owner can change member roles")

        # Cannot change owner role
        if member.role == 'owner':
            raise ValueError("Cannot change owner role")

        # Validate new role
        new_role = validate_role(new_role)
        if new_role == 'owner':
            raise ValueError("Cannot assign owner role to member")

        member.role = new_role
        db.session.commit()

        return member

    @staticmethod
    def remove_member(member_id, user_id):
        """
        Remove member from project

        Args:
            member_id: ProjectMember ID
            user_id: User ID (must be owner or admin)

        Returns:
            True if successful
        """
        member = ProjectMember.query.get(member_id)

        if not member:
            raise ValueError("Member not found")

        # Check permission (owner or admin)
        if not MemberService._check_admin_access(member.project_id, user_id):
            raise PermissionError("Only project owner or admin can remove members")

        # Cannot remove owner
        if member.role == 'owner':
            raise ValueError("Cannot remove project owner")

        db.session.delete(member)
        db.session.commit()

        return True

    @staticmethod
    def list_pending_invites(project_id, user_id):
        """
        List pending invitations

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)

        Returns:
            List of ProjectInvite objects
        """
        # Check access
        if not MemberService._check_project_access(project_id, user_id):
            raise PermissionError("User doesn't have access to this project")

        invites = ProjectInvite.query.filter_by(
            project_id=project_id,
            status='pending'
        ).order_by(ProjectInvite.created_at.desc()).all()

        return invites

    @staticmethod
    def cancel_invite(invite_id, user_id):
        """
        Cancel pending invitation

        Args:
            invite_id: ProjectInvite ID
            user_id: User ID (must have admin access)

        Returns:
            True if successful
        """
        invite = ProjectInvite.query.get(invite_id)

        if not invite or invite.status != 'pending':
            raise ValueError("Invitation not found or already processed")

        # Check permission
        if not MemberService._check_admin_access(invite.project_id, user_id):
            raise PermissionError("Only project owner or admin can cancel invitations")

        invite.status = 'cancelled'
        db.session.commit()

        return True

    @staticmethod
    def accept_invite(token, user_id):
        """
        Accept invitation (user accepts invite)

        Args:
            token: Invitation token
            user_id: User ID accepting the invite

        Returns:
            ProjectMember object
        """
        invite = ProjectInvite.query.filter_by(token=token, status='pending').first()

        if not invite:
            raise ValueError("Invalid or expired invitation")

        # Check if user email matches invite
        user = User.query.get(user_id)
        if not user or user.email != invite.email:
            raise ValueError("This invitation is for a different email address")

        # Check if already a member
        existing_member = ProjectMember.query.filter_by(
            project_id=invite.project_id,
            user_id=user_id
        ).first()
        if existing_member:
            raise ValueError("You are already a member of this project")

        # Create member
        from app.utils.helpers import generate_id
        member = ProjectMember(
            project_id=invite.project_id,
            user_id=user_id,
            role=invite.role
        )
        member.id = generate_id('mem')

        db.session.add(member)

        # Update invite status
        invite.status = 'accepted'

        db.session.commit()

        return member

    @staticmethod
    def _check_project_access(project_id, user_id):
        """Check if user has access to project"""
        project = Project.query.get(project_id)
        if project and project.owner_user_id == user_id:
            return True

        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()

        return member is not None

    @staticmethod
    def _check_admin_access(project_id, user_id):
        """Check if user has admin access (owner or admin role)"""
        project = Project.query.get(project_id)
        if project and project.owner_user_id == user_id:
            return True

        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()

        return member and member.role in ['owner', 'admin']
