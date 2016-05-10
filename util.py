import random
import string
import datetime  
import time 

from google.appengine.api import users 
from google.appengine.ext import db 
from django.utils import simplejson  
from google.appengine.api import users

#import simplejson 
import model
import urllib

def is_admin(user):
  admins=['selene.vanegast','luisalberto.lucio','rociopego65','cpedraza7302','alejandro.pedraza.gomez','itzel_chito','josegranciano224','dr.rodriguez']
  if user in admins:
    return True
  else:
    return False

def add_user( url, dict ):
  user = users.get_current_user()
  if user:
    dict['user'] = user
    dict['user_auth_url'] = users.create_logout_url( url )
  else:
    dict['user_auth_url'] = users.create_login_url( url )


def random_alnum( count ):
  chars = string.letters + string.digits
  result = ''
  for i in range(count):
    result += random.choice(chars)
  return result

class GqlEncoder(simplejson.JSONEncoder): 
  def default(self, obj): 
    """Tests the input object, obj, to encode as JSON.""" 
    if hasattr(obj, '__json__'): 
      return getattr(obj, '__json__')() 

    if isinstance(obj, db.GqlQuery): 
      return list(obj) 

    elif isinstance(obj, db.Model): 
      properties = obj.properties().items() 
      output = {} 
      for field, value in properties: 
          output[field] = getattr(obj, field) 
      return output 

    elif isinstance(obj, datetime.datetime): 
      output = {} 
      fields = ['day', 'hour', 'microsecond', 'minute', 'month', 'second', 'year'] 
      methods = ['ctime', 'isocalendar', 'isoformat', 'isoweekday', 'timetuple'] 
      for field in fields: 
          output[field] = getattr(obj, field) 
      for method in methods: 
          output[method] = getattr(obj, method)() 
      output['epoch'] = time.mktime(obj.timetuple()) 
      return output

    elif isinstance(obj, datetime.date): 
      output = {} 
      fields = ['year', 'month', 'day'] 
      methods = ['ctime', 'isocalendar', 'isoformat', 'isoweekday', 'timetuple'] 
      for field in fields: 
          output[field] = getattr(obj, field) 
      for method in methods: 
          output[method] = getattr(obj, method)() 
      output['epoch'] = time.mktime(obj.timetuple()) 
      return output 

    elif isinstance(obj, time.struct_time): 
      return list(obj) 

    elif isinstance(obj, users.User): 
      output = {} 
      methods = ['nickname', 'email', 'auth_domain'] 
      for method in methods: 
          output[method] = getattr(obj, method)() 
      return output 

    return simplejson.JSONEncoder.default(self, obj) 