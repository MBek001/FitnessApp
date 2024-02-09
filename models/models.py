from datetime import datetime

import enum

from sqlalchemy import Table, MetaData, Column, String, Integer, Text, Boolean, Date, ForeignKey, Float, DECIMAL, Enum, \
    TIMESTAMP

metadata = MetaData()


class GenderEnum(enum.Enum):
    male = 'male'
    female = 'female'


class GoalEnum(enum.Enum):
    gain = 'Gain weight',
    lose = 'Lose weight',
    fit = 'Get fitter',
    flexible = 'Get more flexible',
    basic = 'Learn the basic'


class ActivityEnum(enum.Enum):
    rookie = 'Rookie',
    beginner = 'Beginner',
    intermediate = 'Intermediate',
    advanced = 'Advanced',
    beast = 'True Beast'


class CategoryEnum(enum.Enum):
    beginner = 'Beginner',
    intermediate = 'Intermediate',
    advanced = 'Advanced',


class DurationEnum(enum.Enum):
    monthly = 'Monthly',
    yearly = 'Yearly'


class StatusEnum(enum.Enum):
    active = 'Active',
    expired = 'Expired',
    canceled = 'Canceled'


users = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True, index=True, autoincrement=True),
    Column('name', String),
    Column('photo_url', String),
    Column('password', String),
    Column('email', String),
    Column('age', Integer),
    Column('weight', Integer),
    Column('height', Integer),
    Column('gender', Enum(GenderEnum))
)

user_goal = Table(
    'user_goal',
    metadata,
    Column('id', Integer, primary_key=True, index=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('goal', Enum(GoalEnum)),
    Column('activity', Enum(ActivityEnum))
)


workout_categories = Table(
    'workout_category',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('category', Enum(CategoryEnum))
)

exercises = Table(
    'exercises',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('workout_category_id', Integer, ForeignKey('workout_category.id')),
    Column('name', String)
)

user_purchase = Table(
    'user_purchase',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('purchase_name', String),
    Column('monthly_fee', Float),
    Column('yearly_fee', Float)
)


user_payment = Table(
    'user_payment',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('purchase_id', Integer, ForeignKey('user_purchase.id')),
    Column('duration', Enum(DurationEnum)),
    Column('created_at', TIMESTAMP, default=datetime.utcnow()),
)


user_status = Table(
    'user_status',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('status', Enum(StatusEnum))
)


review = Table(
    'review',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('exercises_id', Integer, ForeignKey('exercises.id')),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('rating', Integer),
    Column('comment', Text),
)
