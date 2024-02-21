from datetime import datetime

import enum

from sqlalchemy import Table, MetaData, Column, String, Integer, Text, Boolean, Date, ForeignKey, Float, DECIMAL, Enum, \
    TIMESTAMP, DATETIME

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


class SubDurationEnum(enum.Enum):
    monthly = 'Monthly',
    yearly = 'Yearly'


class BookDurationEnum(enum.Enum):
    one_hour = '1 Hour',
    two_hours = '2 Hours',
    three_hours = '3 Hours',


class StatusEnum(enum.Enum):
    active = 'Active',
    expired = 'Expired',
    canceled = 'Canceled'


class LanguageEnum(enum.Enum):
    english = 'English',
    russian = 'Russian',
    spanish = 'Spanish',
    french = 'French',
    german = 'German',
    japanese = 'Japanese',
    chinese = 'Chinese',
    korean = 'Korean',
    vietnamese = 'Vietnamese',
    arabic = 'Arabic',
    portuguese = 'Portuguese',


class WeekdaysEnum(enum.Enum):
    monday = 'Monday',
    tuesday = 'Tuesday',
    wednesday = 'Wednesday',
    thursday = 'Thursday',
    friday = 'Friday',
    saturday = 'Saturday',
    sunday = 'Sunday'


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
    Column('gender', Enum(GenderEnum)),
    Column('is_trainer', Boolean, default=False),
    Column('user_role', String)
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
    Column('name', String),
    Column('video_url', String),
    Column('date_added', TIMESTAMP),
    Column('instruction', String)
)

subscription = Table(
    'subscription',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('purchase_name', String),
    Column('monthly_fee', Float),
    Column('yearly_fee', Float)
)


user_subscription = Table(
    'user_subscription',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('purchase_id', Integer, ForeignKey('subscription.id')),
    Column('duration', Enum(SubDurationEnum)),
    Column('created_at', TIMESTAMP, default=datetime.utcnow())
)


user_status = Table(
    'user_status',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('status', Enum(StatusEnum))
)


trainer = Table(
    'trainer',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('full_name',String),
    Column('experience', Integer),
    Column('completed',Integer),
    Column('active_clients', Integer),
    Column('phone_number', String),
    Column('rate', Float),
    Column('description', String)
)


review = Table(
    'review',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('trainer_id', Integer, ForeignKey('trainer.id')),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('rating', Integer),
    Column('comment', Text),
)


saved_cards = Table(
    'cards',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('card_holder_name', String),
    Column('card_number', String),
    Column('expiry_month', Integer),    

)


languages = Table(
    'languages',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('language', Enum(LanguageEnum))
)

booked_trainer = Table(
    'booked_trainer',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('trainer_id', Integer, ForeignKey('trainer.id')),
    Column('date', TIMESTAMP),
    Column('duration', Enum(BookDurationEnum))
)


insights = Table(
    'insights',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('calories', Float),
    Column('steps', Integer),
    Column('time_spent', Float),
    Column('heartbeat', Integer),
    Column('day', Enum(WeekdaysEnum)),
    Column('date', TIMESTAMP)
)

workout_plan = Table(
    'workout_plan',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('exercise', Integer, ForeignKey('exercises.id')),
    Column('minutes', Integer),
    Column('calories', Integer)
)