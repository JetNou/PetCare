"""Create DB

Revision ID: 57fdd21306c4

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '57fdd21306c4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema"""
    op.create_table('medical_histories',
    sa.Column('medical_history_id', sa.Integer(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('medical_history_id')
    )
    op.create_index(op.f('ix_medical_histories_medical_history_id'), 'medical_histories', ['medical_history_id'], unique=False)
    op.create_table('roles',
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('role_name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('role_id')
    )
    op.create_table('medical_actions',
    sa.Column('medical_action_id', sa.Integer(), nullable=False),
    sa.Column('medical_history_id', sa.Integer(), nullable=False),
    sa.Column('type_action', sa.Enum('INSPECTION', 'TESTS', 'DIAGNOSTICS', 'COMPLEX', 'PARASITE_TREATMENT', 'SURGERY', 'TREATMENT_COURSE', 'DENTISTRY', 'GROOMING', 'OTHER', name='typeaction'), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('interval_period', sa.Integer(), nullable=True),
    sa.Column('date', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('status', sa.Enum('PLANNED', 'OVERDUE', 'COMPLETED', name='medicalhistorystatus'), nullable=False),
    sa.Column('notes', sa.String(length=1000), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['medical_history_id'], ['medical_histories.medical_history_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('medical_action_id')
    )
    op.create_index(op.f('ix_medical_actions_medical_action_id'), 'medical_actions', ['medical_action_id'], unique=False)
    op.create_index(op.f('ix_medical_actions_medical_history_id'), 'medical_actions', ['medical_history_id'], unique=False)
    op.create_table('users',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('user_full_name', sa.String(length=100), nullable=False),
    sa.Column('user_login', sa.String(length=50), nullable=False),
    sa.Column('user_email', sa.String(length=100), nullable=False),
    sa.Column('user_password_hash', sa.String(length=255), nullable=False),
    sa.Column('user_avatar', sa.String(length=255), nullable=True),
    sa.Column('registered_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('REGISTERED', 'ACTIVE', 'BANNED', name='userstatus'), nullable=False),
    sa.Column('banned_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('ban_reason', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('user_id'),
    sa.UniqueConstraint('user_email'),
    sa.UniqueConstraint('user_login')
    )
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=False)
    op.create_table('actions',
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('notes', sa.String(length=1000), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('action_id')
    )
    op.create_index(op.f('ix_actions_action_id'), 'actions', ['action_id'], unique=False)
    op.create_index(op.f('ix_actions_user_id'), 'actions', ['user_id'], unique=False)
    op.create_table('pets',
    sa.Column('pet_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('breed', sa.String(length=100), nullable=True),
    sa.Column('color', sa.String(length=50), nullable=True),
    sa.Column('gender', sa.String(length=20), nullable=True),
    sa.Column('date_birth', sa.Date(), nullable=True),
    sa.Column('chip', sa.String(length=25), nullable=True),
    sa.Column('photo', sa.String(length=255), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('medical_history_id', sa.Integer(), nullable=True),
    sa.Column('weight', sa.Float(precision=2), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['medical_history_id'], ['medical_histories.medical_history_id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('pet_id')
    )
    op.create_index(op.f('ix_pets_medical_history_id'), 'pets', ['medical_history_id'], unique=False)
    op.create_index(op.f('ix_pets_pet_id'), 'pets', ['pet_id'], unique=False)
    op.create_index(op.f('ix_pets_user_id'), 'pets', ['user_id'], unique=False)
    op.create_table('user_tokens',
    sa.Column('token_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('token_type', sa.String(length=32), nullable=False),
    sa.Column('requested_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('consumed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('token_id')
    )
    op.create_index(op.f('ix_user_tokens_token_hash'), 'user_tokens', ['token_hash'], unique=False)
    op.create_index(op.f('ix_user_tokens_user_id'), 'user_tokens', ['user_id'], unique=False)

def downgrade() -> None:
    """Downgrade schema"""
    op.drop_index(op.f('ix_user_tokens_user_id'), table_name='user_tokens')
    op.drop_index(op.f('ix_user_tokens_token_hash'), table_name='user_tokens')
    op.drop_table('user_tokens')
    op.drop_index(op.f('ix_pets_user_id'), table_name='pets')
    op.drop_index(op.f('ix_pets_pet_id'), table_name='pets')
    op.drop_index(op.f('ix_pets_medical_history_id'), table_name='pets')
    op.drop_table('pets')
    op.drop_index(op.f('ix_actions_user_id'), table_name='actions')
    op.drop_index(op.f('ix_actions_action_id'), table_name='actions')
    op.drop_table('actions')
    op.drop_index(op.f('ix_users_user_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_medical_actions_medical_history_id'), table_name='medical_actions')
    op.drop_index(op.f('ix_medical_actions_medical_action_id'), table_name='medical_actions')
    op.drop_table('medical_actions')
    op.drop_table('roles')
    op.drop_index(op.f('ix_medical_histories_medical_history_id'), table_name='medical_histories')
    op.drop_table('medical_histories')
