from datetime import datetime, timedelta

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


class LevelEnum(enum.Enum):
    beginner = 'Beginner',
    intermediate = 'Intermediate',
    advanced = 'Advanced',


class SubDurationEnum(enum.Enum):
    monthly = 'Monthly',
    yearly = 'Yearly'


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
    Column('language',Enum(LanguageEnum), default=LanguageEnum.english),
    Column('is_trainer', Boolean, default=False),
    Column('is_admin', Boolean, default=False),
    Column('notifications', Integer, ForeignKey('user_news.id'))
)

user_goal = Table(
    'user_goal',
    metadata,
    Column('id', Integer, primary_key=True, index=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('goal', Enum(GoalEnum)),
    Column('activity', Enum(ActivityEnum))
)

trainer = Table(
    'trainer',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('experience', Integer),
    Column('completed', Integer),
    Column('active_clients', Integer),
    Column('cost',Float),
    Column('phone_number', String),
    Column('rate', Float),
    Column('description', String),
)

booked_trainer = Table(
    'booked_trainer',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('trainer_id', Integer, ForeignKey('trainer.id')),
    Column('date', TIMESTAMP, default=datetime.utcnow()+timedelta(hours=5)),
)

level = Table(
    'levels',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', Enum(LevelEnum))
)
category = Table(
    'category',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('level_id', Integer, ForeignKey('levels.id')),
    Column('name', String),
    Column('photo_url', String)
)


workout_categories = Table(
    'user_level',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('level_id', Integer, ForeignKey('levels.id'))
)


exercises = Table(
    'exercises',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('category_id', Integer, ForeignKey('category.id')),
    Column('name', String),
    Column('video_url', String),
    Column('video_hash', String),
    Column('date_added', TIMESTAMP, default=datetime.utcnow()+timedelta(hours=5)),
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
    Column('created_at', TIMESTAMP, default=datetime.utcnow()++timedelta(hours=5))
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
    Column('trainer_id', Integer, ForeignKey('trainer.id')),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('rating', Float),
    Column('comment', Text),
)

saved_cards = Table(
    'cards',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('card_holder_name', String),
    Column('card_number', String),
    Column('balance', Integer, default=1000),
    Column('expiry_month', Integer),

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
    Column('date', TIMESTAMP, default=datetime.utcnow()+timedelta(hours=5))
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

user_payment = Table(
    'user_payment',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('card_id', Integer, ForeignKey('cards.id')),
    Column('trainer_id', Integer, ForeignKey('trainer.id')),
    Column('amount', Float),
    Column('payment_method', String),
    Column('created_at', TIMESTAMP, default=datetime.utcnow()+timedelta(hours=5))
)

news = Table(
    'news',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('title', String),
    Column('news', String),
    Column('created_at', TIMESTAMP, default=datetime.utcnow()+timedelta(hours=5))
)

events = Table(
    'events',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String),
    Column('event', String),
    Column('created_at', TIMESTAMP, default=datetime.utcnow())
)

All = Table(
    'all',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('news_id', Integer, ForeignKey('news.id')),
    Column('events_id', Integer,ForeignKey('events.id'))

)

user_news = Table(
    'user_news',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('news_id', Integer, ForeignKey('news.id'))
)