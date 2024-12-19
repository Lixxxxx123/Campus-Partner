from tokenize import group

from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_migrate import Migrate
from sqlalchemy import false

from extensions import db
from flask_login import LoginManager,login_user ,current_user,login_required,logout_user
from models import User,Role,Group,Post,Comment,Like
from functools import wraps
from forms import RegistrationForm,LoginForm,GroupForm,PostForm,CommentForm

#TODO
#1、上传头像功能实现（待定）
#2、修改个人信息，邮箱可能重复
#3、权限功能可能需要管理一下
#4、时间目前都是utc时间，还没进行转换

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
migrate = Migrate(app,db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# mail = Mail(app)
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#权限管理
def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args,**kwargs):
            if current_user.get_role() != role:
                abort(403)
            return func(*args,**kwargs)
        return wrapper
    return decorator

#首页
@app.route('/',methods=['GET','POST'])
def home():
    search_query = request.args.get('search','')
    page = request.args.get('page',1,type=int)
    if search_query:
        posts = Post.query.filter(Post.title.ilike(f"%{search_query}%")).order_by(Post.date_created.desc()).paginate(page=page,per_page=5)
        groups = Group.query.filter(Group.name.ilike(f"%{search_query}%")).paginate(page=page,per_page=5)
    else:
        posts = Post.query.order_by(Post.date_created.desc()).paginate(page=page,per_page=5)
        groups = Group.query.order_by(Group.date_created.desc()).paginate(page=page,per_page=5)
    return render_template('home.html',posts=posts,groups=groups,search_query=search_query)

#用户注册页面
@app.route('/register',methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user =User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('用户名已存在，请选择其他用户名','danger')
            return redirect(url_for('register'))

        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('该邮箱已被注册，请使用其他邮箱','danger')
            return redirect(url_for('register'))

        new_user = User(username=form.username.data,email=form.email.data )
        new_user.set_password(form.password.data)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，欢迎使用！', 'success')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)        
        

#用户登录页面
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('登录成功！','success')
            return redirect(url_for('profile'))
        else:
            flash('登录失败,请检查邮箱和密码','danger')
    return render_template('login.html',form=form)


#编辑个人信息页面
@app.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = RegistrationForm()

    if request.method =='GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('用户名已存在，请选择其他用户名', 'danger')
            return redirect(url_for('edit_profile'))

        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('该邮箱已被注册，请使用其他邮箱', 'danger')
            return redirect(url_for('edit_profile'))

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()

        flash('用户信息更改成功','success')
        return redirect(url_for('profile'))
    

    return render_template('edit_profile.html',form=form)

#个人信息页面
@app.route('/profile',methods=['GET'])
@login_required
def profile():
    return render_template('profile.html',user=current_user)

#我的小组页面
@app.route('/user/groups',methods=['GET','POST'])
@login_required
def my_groups():
    groups = Group.query.filter(Group.members.any(id=current_user.id)).all()
    return render_template('my_groups.html',groups=groups)

#用户登出
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


#创建小组页面
@app.route('/group/create',methods=['GET','POST'])
@login_required
def create_group():
    form = GroupForm()
    if form.validate_on_submit():
        group_name = form.name.data
        description = form.description.data
        new_group = Group(name=group_name,description=description,admin=current_user)
        current_user.groups.append(new_group)
        db.session.add(new_group)
        db.session.commit()
        flash('创建小组成功！','success')
        return redirect(url_for('groups_list'))

    return render_template('create_group.html',form=form)

#小组列表页面
@app.route('/group',methods=['GET','POST'])
def groups_list():
    groups = Group.query.all()
    return render_template('groups_list.html',groups=groups)

#小组详情页面
@app.route('/group/<int:group_id>',methods=['GET','POST'])
def group_detail(group_id):
    group = Group.query.get(group_id)
    if not group:
        flash('该小组不存在','danger')
        return redirect(url_for('groups_list'))

    #判断当前用户是否为小组管理员
    is_admin = group.admin_id == current_user.id if current_user.is_authenticated else False
    posts = Post.query.filter_by(group_id=group.id).order_by(Post.date_created.desc()).all()
    members = group.members
    return render_template('group_detail.html',group=group,posts=posts,members=members,is_admin=is_admin)

#加入小组
@app.route('/group/join/<int:group_id>',methods=['GET','POST'])
@login_required
def join_group(group_id):
    group = Group.query.get(group_id)
    if not group:
        flash('该小组不存在','danger')
        return redirect(url_for('groups_list'))

    if group in current_user.groups:
        flash('你已经是该小组成员了','warning')
        return redirect(url_for('group_detail',group_id=group.id))

    current_user.groups.append(group)
    db.session.commit()
    flash('成功加入小组！','success')
    return redirect(url_for('group_detail',group_id=group.id))


#退出小组
@app.route('/group/leave/<int:group_id>',methods=['POST','GET'])
@login_required
def leave_group(group_id):
    group = Group.query.get(group_id)
    if not group:
        flash('该小组不存在','danger')
        return redirect(url_for('groups_list'))

    if group not in current_user.groups:
        flash('你不在该小组中','warning')
        return redirect(url_for('group_detail',group_id=group.id))

    current_user.groups.remove(group)
    db.session.commit()
    flash('成功退出小组','success')
    return redirect(url_for('groups_list'))


#移除小组成员功能
@app.route('/group/<int:group_id>/remove_member/<int:user_id>',methods=['GET','POST'])
@login_required
def remove_member(group_id,user_id):
    group = Group.query.get(group_id)
    user = User.query.get(user_id)

    if not group or not user or user not in group.members:
        flash('小组或用户不存在','danger')
        return  redirect(url_for('group_detail',group_id=group.id))

    if current_user.id != group.admin_id:
        flash('你没有权限移除该成员','danger')
        return redirect(url_for('group_detail',group_id=group.id))

    group.members.remove(user)
    db.session.commit()
    flash(f'成功移除成员{user.username}','success')
    return redirect(url_for('group_detail',group_id=group.id))



#发布帖子页面
@app.route('/group/<int:group_id>/post',methods=['GET','POST'])
@login_required
def post_in_group(group_id):
    group = Group.query.get(group_id)
    if not group:
        flash('该小组不存在','danger')
        return redirect(url_for('groups_list'))

    form = PostForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_post = Post(title=title,content=content,author=current_user,group=group)

        db.session.add(new_post)
        db.session.commit()
        flash('帖子发布成功','success')
        return redirect(url_for('group_detail',group_id=group.id))

    return  render_template('post_in_group.html',form=form,group=group)

#帖子详情页面及评论功能
@app.route('/group/<int:group_id>/post/<int:post_id>',methods=['GET','POST'])
def post_detail(group_id,post_id):
    group = Group.query.get(group_id)
    post = Post.query.get(post_id)

    if not group or not post or post.group_id != group.id:
        flash('帖子或小组不存在','danger')
        return redirect(url_for('groups_list'))

    form = CommentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        content = form.content.data
        new_comment = Comment(content=content,author=current_user,post=post)

        db.session.add(new_comment)
        db.session.commit()
        flash('评论发表成功','success')
        return redirect(url_for('post_detail',group_id=group.id,post_id=post.id))

    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.date_created.desc()).all()

    #判断当前用户是否已经点赞
    like_by_user = False
    if current_user.is_authenticated:
        like_by_user = current_user.id in [like.user_id for like in post.likes]

    return render_template('post_detail.html',group=group,post=post,form=form,comments=comments,like_by_user=like_by_user)


#删除帖子功能
@app.route('/group/<int:group_id>/post/<int:post_id>/delete',methods=['GET','POST'])
@login_required
def delete_post(group_id,post_id):
    group = Group.query.get(group_id)
    post = Post.query.get(post_id)

    if not group or not post or post.group_id != group_id:
        flash('该帖子不存在','danger')
        return redirect(url_for('groups_list'))

    if current_user.id != post.user_id and current_user.id !=group.admin_id and current_user.role != Role.ADMIN:
        flash('你没有权限删除该帖子','danger')
        return redirect(url_for('group_detail',group_id=group.id))

    db.session.delete(post)
    db.session.commit()
    flash('帖子删除成功','success')
    return redirect(url_for('group_detail',group_id=group.id))


#删除评论功能
@app.route('/delete_comment/<int:comment_id>',methods=['GET','POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        flash('评论不存在','danger')
        return redirect(request.referrer)

    post = comment.post
    group = post.group

    #仅可以由评论作者，帖子作者，小组管理员，最高管理员删除评论
    can_delete = (comment.author == current_user
        or post.author == current_user
        or group.admin == current_user
        or current_user.role == Role.ADMIN )
    if  can_delete:
        db.session.delete(comment)
        db.session.commit()
        flash('评论已删除','success')
    else:
        flash('没有权限删除该评论','danger')

    return redirect(url_for('post_detail',group_id=group.id,post_id=post.id))


#点赞功能
@app.route('/group/<int:group_id>/post/<int:post_id>/like',methods=['GET','POST'])
@login_required
def like_post(group_id,post_id):
    post =Post.query.get(post_id)

    if not post or post.group_id != group_id:
        flash('帖子不存在','danger')
        return redirect(url_for('groups_list'))

    #检查用户是否点赞
    existing_like = Like.query.filter_by(user_id=current_user.id,post_id=post.id).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        flash('取消点赞成功','success')
    else:
        new_like = Like(user_id=current_user.id,post_id=post.id)
        db.session.add(new_like)
        db.session.commit()
        flash('点赞成功','success')

    return redirect(url_for('post_detail',group_id=group_id,post_id=post_id))

if __name__ == '__main__':

    app.run(host='0.0.0.0',port=5000,debug=True)
