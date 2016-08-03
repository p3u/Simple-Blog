from blog_db import User, Post, Comment, Like
import logging
from google.appengine.ext.db import BadValueError
from google.appengine.ext.db import TransactionFailedError
import hmac
import string
import random


class UserRegistration():
    """A class to help validation and registration of new users"""
    def __init__(self):
        self.secret = "AxzOedEirfL"

    def is_pw_valid(self, pw, pw_conf):
        err_msg = ""
        valid = True
        if (len(pw) < 6):
            err_msg = "Needs to be at least 6 characters long. "
            valid = False
        if (pw != pw_conf):
            err_msg += "Passwords don't match."
            valid = False

        if (valid):
            return True
        else:
            return err_msg.strip()

    def is_username_valid(self, username):
        if (" " in username):
            return "Username can't contain spaces"
        if(username != "".join(
           [i if ord(i) > 44 and ord(i) < 128 else "" for i in username])):
            return "Username can't contain special characters"
        users = User.query(User.username == username.lower())
        if (users.get() is not None):
            return "This username is already taken"
        else:
            return True

    def register_new_user(self, username, pw):
        username = str(username)
        pw = str(pw)
        salt = "".join(random.choice(string.ascii_letters) for x in range(12))
        logging.info("SALT: " + salt)
        hashed_pw = hmac.new(self.secret, pw + salt).hexdigest() + salt
        logging.info("Hashed_pw: " + hashed_pw)
        try:
            new_user = User(username=username.lower(), useralias=username,
                            password=hashed_pw).put()
            return new_user
        except:
            return False

    def is_login_valid(self, username, pw):
        user = User.query(User.username == username.lower()).get()
        if(user is None):
            return (False, "Username doesn't exist")
        db_pw_hash = user.password[0:-12]
        salt = user.password[-12:]
        logging.info("db_salt: " + salt)
        pw_hash = hmac.new(self.secret, pw + salt).hexdigest()
        password_is_valid = pw_hash == db_pw_hash
        if(password_is_valid):
            return (True, username)
        else:
            return (False, "Wrong Password")


class PostRegistration():
    """A class to help validation and registration of new users"""
    def is_post_valid(self, title, body):
        if(title.strip() == "" or body.strip() == ""):
            return "A Title and a Body are required."
        else:
            return True

    def get_valid_path(self, title):
        path = "".join([i if ord(i) < 128 else "" for i in title])
        path = path.replace(" ", "-").lower()
        path = path.replace("?", "")
        same_path = "Maybe"
        i = 0
        while same_path is not None:
            same_path = Post.query(Post.path == path).get()
            if same_path is not None:
                i += 1
                if(i > 1):
                    path = "-".join(path.split("-")[0:-1])
                path = path + "-" + str(i)
            else:
                return path

    def register_new_post(self, title, body, author):
        validation = self.is_post_valid(title, body)
        if (validation is True):
            path = self.get_valid_path(title)
            try:
                new_post = Post(title=title, body=body,
                                path=path, author=author,
                                deleted=False).put()
                return (True, path)
            except BadValueError:
                return (False,
                        "Oops! You are not logged in.")
            except TransactionFailedError:
                return (False,
                        "Oops! Transaction Failed! Try Again.")
        else:
            return (False, validation)


class CommentRegistration():
    def is_comment_valid(self, text):
        if(text.strip() == ""):
            return "A comment is required."
        else:
            return True

    def register_new_comment(self, text, targetpost, author):
        validation = self.is_comment_valid(text)
        logging.info(text)
        logging.info(targetpost)
        logging.info(author)

        if (validation is True):
            try:
                new_comment = Comment(text=text, targetpost=targetpost,
                                      author=author, deleted=False).put()
                return (True, new_comment)
            except BadValueError:
                return (False,
                        "Oops! You are not logged in.")
            except TransactionFailedError:
                return (False,
                        "Oops! Transaction Failed! Try Again.")
        else:
            return (False, validation)


class LikeRegistration():
    def is_like_valid(self, author, targetpost):
        post = Post.query(Post.path == targetpost).get()
        if (post.author == author):
            return (False, "You cannot like your own post")
        nlikes = Like.query(Like.targetpost == targetpost).count()
        author_likes = Like.query(Like.targetpost == targetpost,
                                  Like.author == author).get()
        if (author_likes is None):
            return (True, nlikes + 1)
        else:
            return (False, "You cannot like a post twice")

    def register_new_like(self, author, targetpost):
        validation = self.is_like_valid(author, targetpost)
        if (validation[0] is True):
            try:
                Like(author=author, targetpost=targetpost).put()
                return (True, validation[1])
            except TransactionFailedError:
                return (False, "Oops! Transaction Failed! Try Again.")
        else:
            return (False, validation[1])
