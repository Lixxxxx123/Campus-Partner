from datetime import datetime

from extensions import db
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin
from sqlalchemy import func,LargeBinary


class Role:
    STUDENT ='student'
    ADMIN = 'admin'
    TEACHER = 'teacher'

#中间表：用户与小组的多对多关系
group_members = db.Table('group_members',
                         db.Column('user_id',db.Integer,db.ForeignKey('user.id'),primary_key=True),
                         db.Column('group_id',db.Integer,db.ForeignKey('group.id'),primary_key=True)
                         )




class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(100),unique=True,nullable=False)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password_hash = db.Column(db.String(255),nullable=False)
    date_created = db.Column(db.DateTime,default=func.now())
    # profile_picture = db.Column(db.String(120),nullable=True)
    role = db.Column(db.String(50),default=Role.STUDENT)

    #与小组的多对多关系
    groups = db.relationship('Group',secondary=group_members,back_populates='members')

    #与帖子和评论的关系
    posts = db.relationship('Post',backref='author',lazy=True)
    comments = db.relationship('Comment',backref='author',lazy=True)

    #用户点赞的帖子
    like_posts = db.relationship('Like',backref='user',lazy=True)

    def like_post_ids(self):
        return [like.post_id for like in self.like_posts]

    def set_password(self,password):
        self.password_hash = generate_password_hash(password,method='pbkdf2:sha256')
        
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

    def set_role(self,role):
        self.role = role

    def get_role(self):
        return self.role
    

class Group(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(255),nullable=False)
    description = db.Column(db.String(512),default='',nullable=True)
    #管理员
    admin_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=True)
    admin = db.relationship('User',backref='managed_groups')
    posts = db.relationship('Post',backref='group',lazy=True)
    # events = db.relationship('Event',backref='group',lazy=True)
    #与成员的多对多关系
    members = db.relationship('User',secondary=group_members,back_populates='groups')
    # avatar = db.Column(LargeBinary,nullable=True)
    date_created = db.Column(db.DateTime, default=func.now())


class Post(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100),nullable=False)
    content = db.Column(db.Text,nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    group_id = db.Column(db.Integer,db.ForeignKey('group.id'),nullable=False)
    date_created = db.Column(db.DateTime,default=func.now())

    comments = db.relationship('Comment',backref='post',lazy=True)
    likes = db.relationship('Like',backref='post',lazy=True)



class Comment(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    content = db.Column(db.String(512),nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    date_created = db.Column(db.DateTime,default=func.now())


class Like(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    date_created = db.Column(db.DateTime,default=func.now())

    #唯一约束，用户只能点赞一次帖子
    __table_args__ = (db.UniqueConstraint('user_id','post_id',name='unique_like'),)


