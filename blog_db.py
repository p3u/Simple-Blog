from google.appengine.ext import ndb


class User(ndb.Model):
    username = ndb.StringProperty(required=True)  # Ignores case sensitivity
    useralias = ndb.StringProperty(required=True)  # Preserve case sensitivity
    password = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)


class Post(ndb.Model):
    title = ndb.StringProperty(required=True)
    body = ndb.TextProperty(required=True)
    path = ndb.StringProperty(required=True)
    author = ndb.StringProperty(required=True)
    deleted = ndb.BooleanProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)


class Comment(ndb.Model):
    author = ndb.StringProperty(required=True)
    text = ndb.TextProperty(required=True)
    targetpost = ndb.StringProperty(required=True)
    deleted = ndb.BooleanProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)


class Like(ndb.Model):
    author = ndb.StringProperty(required=True)
    targetpost = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
