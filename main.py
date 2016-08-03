import os
import jinja2
import webapp2
import logging
from db_reg import UserRegistration, PostRegistration, CommentRegistration
from db_reg import LikeRegistration
from google.appengine.ext import ndb
import blog_db
import encrypt
from google.appengine.api.app_identity import app_identity

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

logging.info("ABC " + app_identity.get_application_id())


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class SignupPage(Handler):

    def get(self):
        useralias = encrypt.check_secure_val(
                    self.request.cookies.get("useralias"))
        if(useralias):
            self.redirect("/")
        self.render("signup.html")

    def post(self):
        ur = UserRegistration()
        username_input = self.request.get("username")
        pw_input = self.request.get("pw")
        pw_conf_input = self.request.get("pw-conf")
        name_check = ur.is_username_valid(username_input)
        pw_check = ur.is_pw_valid(pw_input, pw_conf_input)
        if (pw_check is True and name_check is True):
            user_registered = ur.register_new_user(username_input, pw_input)
            if user_registered:
                self.response.headers.add_header("Set-Cookie", "useralias=%s"
                                                 % encrypt.make_secure_val(
                                                   username_input))
                self.redirect("/")
            else:
                self.render("signup.html", name_err="Oops! Please try again!",
                            name=username_input)
        else:
            if pw_check is True:
                pw_check = ""
            if name_check is True:
                name_check = ""
            self.render("signup.html", pw_err=pw_check, name_err=name_check,
                        name=username_input)


class LandingPage(Handler):

    def get(self):
        useralias = encrypt.check_secure_val(
                    self.request.cookies.get("useralias"))
        posts = blog_db.Post.query().order(-blog_db.Post.created).fetch(5)
        self.render("frontpage.html", posts=posts, loggeduser=useralias)


class WritePage(Handler):

    def get(self):
        useralias = encrypt.check_secure_val(
                    self.request.cookies.get("useralias"))
        if(useralias is None):
            self.redirect("/signup")
        else:
            self.render("write.html", loggeduser=useralias)

    def post(self):
        pr = PostRegistration()
        title_input = self.request.get("title")
        body_input = self.request.get("body")
        author = encrypt.check_secure_val(self.request.cookies.get("useralias"))
        succ, result = pr.register_new_post(title_input, body_input, author)
        if(succ):
            self.redirect("/post/" + result.strip())
        else:
            self.render("write.html", title=title_input, body=body_input,
                        post_err=result, loggeduser=author)


class PostPage(Handler):
    def grabbed_latest_comment(self, comment_key, comments, timeout):
        if (timeout > 25):
            return True
        key_found = len([x for x in comments if x.key == comment_key]) > 0
        if (key_found):
            return True
        else:
            return False

    def get(self, post_path):
        useralias = encrypt.check_secure_val(
                    self.request.cookies.get("useralias"))
        likes = blog_db.Like.query(blog_db.Like.targetpost == post_path).count()
        # Updating number of likes in case the store hasn't updated yet
        expected_likes = self.request.get("nl")
        if(expected_likes):
            if(int(expected_likes) == likes + 1):
                likes += 1
        likes_err = self.request.get("le", "")
        # Getting the latest comment result
        cm_result = self.request.get("cr")
        # Comment was not succesful
        if (cm_result is None or cm_result.isdigit() is False):
            comment_err = cm_result
            comment_key = None
        # Comment was succesful, grab it's id
        else:
            comment_key = cm_result
            comment_err = ""
        comments = []
        timeout = 0
        while (True):
            q = blog_db.Comment.query(blog_db.Comment.targetpost == post_path)
            q = q.order(-blog_db.Comment.created)
            comments = q.fetch()
            timeout += 1
            if (self.grabbed_latest_comment(comment_key, comments, timeout)):
                break
        # Getting the Post...
        post = None
        timeout = 0
        # While it's none, it means the datastore wasn't updated yet
        # So we should keep trying
        while (post is None):
            q = blog_db.Post.query(blog_db.Post.path == post_path)
            post = q.get()
            timeout += 1
            # Give up after 25 tries, so we don't get stuck in a loop
            if(timeout > 25):
                self.write("Boy! We are slow today. Please refresh the page.")
                break
        self.render("post.html", post=post, comments=comments,
                    loggeduser=useralias, likes=likes, comment_err=comment_err,
                    likes_err=likes_err)


class Logout(Handler):
    def post(self):
        self.response.delete_cookie("useralias")
        self.redirect("/")


class Login(Handler):
    def get(self):
        self.redirect("/signup")

    def post(self):
        ur = UserRegistration()
        username_input = str(self.request.get("username"))
        pw_input = str(self.request.get("pw"))
        success, param = ur.is_login_valid(username_input, pw_input)
        if (success):
            self.response.headers.add_header("Set-Cookie", "useralias=%s"
                                             % encrypt.make_secure_val(
                                               param))
            self.redirect("/")
        else:
            self.render("signup.html", username=username_input,
                        lgn_err=param)


class Like(Handler):
    def post(self):
        author = encrypt.check_secure_val(self.request.cookies.get("useralias"))
        if(author is None):
            self.redirect("/signup")
        else:
            url = self.request.referer
            post_path = url.split("/")[-1]
            post_path = post_path.split("?")[0]
            lr = LikeRegistration()
            success, param = lr.register_new_like(author, post_path)
            if (success):
                self.redirect("/post/" + post_path + "?nl=" + str(param))
            else:
                self.redirect("/post/" + post_path + "?le=" + param)


class Comment(Handler):
    def post(self):
        author = encrypt.check_secure_val(self.request.cookies.get("useralias"))
        if(author is None):
            self.redirect("/signup")
        else:
            url = self.request.referer
            post_path = url.split("/")[-1]
            post_path = post_path.split("?")[0]
            cr = CommentRegistration()
            text_input = self.request.get("text")
            succ, result = cr.register_new_comment(text_input,
                                                   post_path, author)
            if(succ):
                self.redirect("/post/" + post_path + "?cr=" +
                              str(result.id()))
            else:
                self.redirect("/post/" + post_path + "?cr=" + result)


class Delete(Handler):
    def get_path_from_url(self):
        split_url = self.request.referer.split("/")
        path = "/".join(split_url[-2:])
        path = path.split("?")[0]
        logging.info(path)
        return path

    def post(self):
        useralias = encrypt.check_secure_val(self.request.cookies
                                             .get("useralias"))
        if(useralias is None):
            self.redirect("/signup")
        post_path = self.request.get("post-path", self.get_path_from_url())
        key = ndb.Key(urlsafe=self.request.get("btn-delete",
                                               self.request.get("undo-btn")))
        entity = key.get()
        if(entity.author == useralias):
            entity.deleted = (not entity.deleted)
            entity.put()
            if(entity.deleted):
                action = "deleted"
            else:
                action = "restored"

            self.render("confirmation.html", loggeduser=useralias,
                        kind=key.kind(), action=action,
                        key=entity.key.urlsafe(), post_link=post_path)
        else:
            self.redirect(post_path +
                          "?cr=You can't delete other's people comments")


class Edit(Handler):
    get_path_from_url = Delete.__dict__["get_path_from_url"]

    def post(self):
        useralias = encrypt.check_secure_val(self.request.cookies
                                             .get("useralias"))
        if(useralias is None):
            self.redirect("/signup")
        else:
            post_path = self.get_path_from_url()
            key = ndb.Key(urlsafe=self.request.get("btn-edit"))
            post = key.get()
            self.render("edit.html", loggeduser=useralias, post=post)


class Edited(Handler):
    def post(self):
        useralias = encrypt.check_secure_val(self.request.cookies
                                             .get("useralias"))
        key = ndb.Key(urlsafe=self.request.get("key"))
        post = key.get()
        new_title = self.request.get("title")
        new_body = self.request.get("body")
        post.title = new_title
        post.body = new_body
        if(post.author != useralias):
            self.render("edit.html", loggeduser=useralias, post=post,
                        post_err="You are not the author of this post!")
        else:
            pr = PostRegistration()
            validation = pr.is_post_valid(new_title, new_body)
            if(validation is True):
                post.put()
                self.render("success.html", post=post)
            else:
                self.render("edit.html", loggeduser=useralias, post=post,
                            post_err=validation)


app = webapp2.WSGIApplication([
    ("/", LandingPage),
    ("/signup", SignupPage),
    ("/write", WritePage),
    (r"/post/(.*)", PostPage),
    ("/logout", Logout),
    ("/login", Login),
    ("/like", Like),
    ("/comment", Comment),
    ("/confirmation", Delete),
    ("/edit", Edit),
    ("/edited", Edited)
], debug=True)
