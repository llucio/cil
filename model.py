import decimal

from google.appengine.ext import db

class Category(db.Model):
  name = db.StringProperty()
  description = db.TextProperty()
  children = db.ListProperty(db.Key)
  @property
  def items(self):
    return Incident.gql("WHERE categories = :1", self.key())
  @staticmethod
  def root():
    return Category.all().filter( "name = ", "root" ).get()
  @staticmethod
  def byName(name):
    return Category.all().filter( "name = ", name).get()
  @property
  def members(self):
    return Incident.gql("WHERE categories = :1", self.key())

class Profile(db.Model):
  '''extra user details'''
  owner = db.UserProperty()
  role = db.StringProperty(choices=( 'USER', 'ADMIN' ))
  name = db.StringProperty()

  @staticmethod
  def from_user( u ):
    return Profile.all().filter( "owner = ", u ).get()

class Incident(db.Model):
  '''an Incident'''
  owner = db.UserProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  title = db.StringProperty()
  description = db.TextProperty()
  enabled = db.BooleanProperty()
  # Group affiliation
  categories = db.ListProperty(db.Key)
  id = db.StringProperty()
  status = db.StringProperty( choices=( 'NEW', 'PROGRESS', 'COMPLETED' ) )
  @staticmethod
  def recent():
    return Incident.all().filter( "enabled =", True ).order('-created').fetch(100)
  @staticmethod
  def by_category(key):
    return Incident.gql("WHERE categories = :1", key)
	
class Image(db.Model):
  incident = db.ReferenceProperty(Incident,collection_name='images')
  image_type = db.StringProperty()
  image = db.BlobProperty()
