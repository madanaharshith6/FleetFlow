"""Milestone 2 schema enhancements: Trips, tracking number, customer info, route & traffic info, and detailed shipment history.

Revision ID: 004_milestone2_enhancements
Revises: 562efd458346
Create Date: 2026-10-03 16:55:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_milestone2_enhancements'
down_revision: Union[str, Sequence[str], None] = '562efd458346'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    
    # 1. Enhance shipments table
    shipment_cols = [c['name'] for c in insp.get_columns('shipments')]
    
    if 'tracking_number' not in shipment_cols:
        op.add_column('shipments', sa.Column('tracking_number', sa.String(50), nullable=True))
        # Backfill existing shipments with a tracking number
        conn.execute(sa.text("UPDATE shipments SET tracking_number = 'TRK-' || shipment_id WHERE tracking_number IS NULL"))
        op.alter_column('shipments', 'tracking_number', nullable=False)
        op.create_index(op.f('ix_shipments_tracking_number'), 'shipments', ['tracking_number'], unique=True)

    if 'customer_name' not in shipment_cols:
        op.add_column('shipments', sa.Column('customer_name', sa.String(120), nullable=False, server_default='Acme Logistics'))

    if 'customer_phone' not in shipment_cols:
        op.add_column('shipments', sa.Column('customer_phone', sa.String(30), nullable=True, server_default='+91 98765 43210'))

    if 'distance_km' not in shipment_cols:
        op.add_column('shipments', sa.Column('distance_km', sa.Float(), nullable=False, server_default='275.0'))

    if 'estimated_duration' not in shipment_cols:
        op.add_column('shipments', sa.Column('estimated_duration', sa.String(50), nullable=True, server_default='4 hrs 45 mins'))

    if 'route_type' not in shipment_cols:
        op.add_column('shipments', sa.Column('route_type', sa.String(50), nullable=False, server_default='Fastest Route'))

    if 'traffic_level' not in shipment_cols:
        op.add_column('shipments', sa.Column('traffic_level', sa.String(30), nullable=False, server_default='Moderate'))

    if 'scheduled_pickup' not in shipment_cols:
        op.add_column('shipments', sa.Column('scheduled_pickup', sa.DateTime(), nullable=True))

    if 'scheduled_delivery' not in shipment_cols:
        op.add_column('shipments', sa.Column('scheduled_delivery', sa.DateTime(), nullable=True))

    if 'actual_delivery' not in shipment_cols:
        op.add_column('shipments', sa.Column('actual_delivery', sa.DateTime(), nullable=True))

    # 2. Enhance shipment_history table
    history_cols = [c['name'] for c in insp.get_columns('shipment_history')]

    if 'event_type' not in history_cols:
        op.add_column('shipment_history', sa.Column('event_type', sa.String(80), nullable=False, server_default='Status Update'))

    if 'previous_status' not in history_cols:
        op.add_column('shipment_history', sa.Column('previous_status', sa.String(40), nullable=True))

    if 'new_status' not in history_cols:
        op.add_column('shipment_history', sa.Column('new_status', sa.String(40), nullable=True))

    if 'description' not in history_cols:
        op.add_column('shipment_history', sa.Column('description', sa.String(255), nullable=True))

    # 3. Create trips table if not exists
    tables = insp.get_table_names()
    if 'trips' not in tables:
        op.create_table(
            'trips',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('trip_id', sa.String(50), nullable=False),
            sa.Column('shipment_id', sa.Integer(), sa.ForeignKey('shipments.id', ondelete='SET NULL'), nullable=True),
            sa.Column('vehicle_id', sa.Integer(), sa.ForeignKey('vehicles.id'), nullable=False),
            sa.Column('driver_id', sa.Integer(), sa.ForeignKey('drivers.id'), nullable=False),
            sa.Column('origin', sa.String(255), nullable=False),
            sa.Column('destination', sa.String(255), nullable=False),
            sa.Column('trip_status', sa.String(40), nullable=False, server_default='Scheduled'),
            sa.Column('route_type', sa.String(50), nullable=False, server_default='Fastest Route'),
            sa.Column('distance_km', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('scheduled_start', sa.DateTime(), nullable=True),
            sa.Column('scheduled_arrival', sa.DateTime(), nullable=True),
            sa.Column('actual_start', sa.DateTime(), nullable=True),
            sa.Column('actual_arrival', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.String(255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_trips_trip_id'), 'trips', ['trip_id'], unique=True)


def downgrade() -> None:
    op.drop_table('trips')
    op.drop_column('shipment_history', 'description')
    op.drop_column('shipment_history', 'new_status')
    op.drop_column('shipment_history', 'previous_status')
    op.drop_column('shipment_history', 'event_type')
    op.drop_column('shipments', 'actual_delivery')
    op.drop_column('shipments', 'scheduled_delivery')
    op.drop_column('shipments', 'scheduled_pickup')
    op.drop_column('shipments', 'traffic_level')
    op.drop_column('shipments', 'route_type')
    op.drop_column('shipments', 'estimated_duration')
    op.drop_column('shipments', 'distance_km')
    op.drop_column('shipments', 'customer_phone')
    op.drop_column('shipments', 'customer_name')
    op.drop_column('shipments', 'tracking_number')
