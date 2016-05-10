import cgi
import decimal
import logging
import os
import random

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images as imagesapi
from webapp2_extras import i18n
#from webapp2_extras import json
from django.utils import simplejson as json

import model
import paypal
import settings
import util

import urllib

# hack to enable urllib to work with Python 2.6
import os
os.environ['foo_proxy'] = 'bar'

urllib.getproxies_macosx_sysconf = lambda: {}

class RequestHandler(webapp.RequestHandler):
  def error( self, code ):
    webapp.RequestHandler.error( self, code )
    if code >= 500 and code <= 599:
      path = os.path.join(os.path.dirname(__file__), 'templates/50x.htm')
      self.response.out.write(template.render(path, {}))
    if code == 404:
      path = os.path.join(os.path.dirname(__file__), 'templates/404.htm')
      self.response.out.write(template.render(path, {}))
	  
class Home(RequestHandler):
  def get(self):
    data = {
      'items': model.Incident.recent(),
	  'profile': model.Profile.from_user(users.get_current_user()),
    }
    util.add_user( self.request.uri, data )
    path = os.path.join(os.path.dirname(__file__), 'templates/main.htm')
    self.response.out.write(template.render(path, data))

class Incident(RequestHandler):
  def _process(self, message=None):
    data = { 
      'message': message,
      'items': model.Incident.all().filter( 'owner =', users.get_current_user() ).fetch(100),
      'profile': model.Profile.from_user(users.get_current_user())
    }
    util.add_user( self.request.uri, data )
    path = os.path.join(os.path.dirname(__file__), 'templates/incident.htm')
    self.response.out.write(template.render(path, data))

  @login_required
  def get(self, command=None):
    self._process()

  def post(self, command):
    user = users.get_current_user()
    if not user:
      self.redirect( users.create_login_url( "/incident" ) )
    else:
      if command == 'add':
        image = self.request.get("image")
        id = model.Incident.all(keys_only=True).count(1000000)+1
        incident = model.Incident( id=str(id), status='NEW', owner=user, title=self.request.get("title"),description=self.request.get("description"), enabled=True )
        catkeys=self.request.get("catkeys").split(",");
        for key in catkeys:
          keyin=model.Category.get(key)
          incident.categories.append(keyin.key())
        incident.put()   
        nim=0
        for images in incident.images:
          nim=nim+1
        if image and nim < settings.MAXIMAGENUMBER:
          image=imagesapi.resize(image,settings.MAXIMAGEX,settings.MAXIMAGEY)
          image=model.Image(incident=incident,image=db.Blob(image))
          image.put()
        self._process("Incidencia creada.")
      else:
        self._process("Accion no soportada.")
		
class Update(RequestHandler):
  def _process(self, key=None, message=None):
    incident = model.Incident.get(key)
    data = { 
      'message': message,
      'item': incident,
      'profile': model.Profile.from_user(users.get_current_user())
    }
    util.add_user( self.request.uri, data )
    path = os.path.join(os.path.dirname(__file__), 'templates/update.htm')
    self.response.out.write(template.render(path, data))

  @login_required
  def get(self, key=None, message=None):
    incident = model.Incident.get(key)
    data = { 
      'message': message,
      'item': incident,
      'profile': model.Profile.from_user(users.get_current_user())
    }
    util.add_user( self.request.uri, data )
    path = os.path.join(os.path.dirname(__file__), 'templates/update.htm')
    self.response.out.write(template.render(path, data))

  def post(self,key):
    logging.info( "-----image key: %s" % (key) )
    user = users.get_current_user()
    if not user:
      self.redirect( users.create_login_url( "/update" ) )
    elif self.request.get("imagekey"):
      image=model.Image.get( self.request.get("imagekey"))
      if image:
        image.delete()
        self._process(key,"Incidencia actualizado.")
    else:
      incident = model.Incident.get(key)
      image = self.request.get("image")
      incident.title=self.request.get("title")
      incident.description=self.request.get("description")
      incident.enabled=True
      incident.categories=[]
      incident.put()
      # for cat in item.categories:
        # item.categories.remove(cat)
        # item.put()
      catkeys=self.request.get("catkeys").split(",");
      for ckey in catkeys:
        try:
          keyin=model.Category.get(ckey)
          incident.categories.append(keyin.key())
        except:
          logging.info("Excepcion en Update-- Post")
      incident.put()
      nim=0
      for images in incident.images:
        nim=nim+1
      if image and nim < settings.MAXIMAGENUMBER:
        image=imagesapi.resize(image,settings.MAXIMAGEX,settings.MAXIMAGEY)
        image=model.Image(incident=incident,image=db.Blob(image))
        try:
          image.put()
        except:
          self._process(key,"Para mejor funcionalidad pruebe con imagenes pequeñas o de baja calidad menores de 1mb.")
      self._process(key,"Incidencia actualizada.")


class Image (RequestHandler):
  def get(self, id):
    image = db.get(id)
    if image.image:
      self.response.headers['Content-Type'] = "image/png"
      self.response.out.write(image.image)
    else:
      self.error(404)  

class Profile (RequestHandler):
  @login_required
  def get(self):
    profile = model.Profile.from_user( users.get_current_user() )
    message=None
    if profile == None:
      profile = model.Profile( owner = users.get_current_user(), role="ADMIN")
      profile.put()
      message="Es necesario actualizar su nombre completo" 
    data = {
      'profile': profile,
	  'message': message
    }
    logging.info( "------------------ %s" % util.GqlEncoder().encode(profile))
    util.add_user( self.request.uri, data )
    path = os.path.join(os.path.dirname(__file__), 'templates/profile.htm')
    self.response.out.write(template.render(path, data))

  def post(self):
    profile = model.Profile.from_user( users.get_current_user() )
    if profile == None:
      profile = model.Profile( owner = users.get_current_user(), role="ADMIN")
    profile.name = self.request.get('name')
    profile.put()
    data = { 
      'profile': profile, 
      'message': 'Perfil actualizado' }
    util.add_user( self.request.uri, data )
    path = os.path.join(os.path.dirname(__file__), 'templates/profile.htm')
    self.response.out.write(template.render(path, data))


class SellHistory (RequestHandler):
  @login_required
  def get(self):
    data = {
      'items': model.Purchase.all().filter( 'owner =', users.get_current_user() ).order('-created').fetch(1000),
      'profile' : model.Profile.from_user( users.get_current_user() ),
    }
    util.add_user( self.request.uri, data )
    path = os.path.join(os.path.dirname(__file__), 'templates/sellhistory.htm')
    self.response.out.write(template.render(path, data))
	
class Delete (RequestHandler):
  @login_required
  def get(self,key):
    profile = model.Profile.from_user( users.get_current_user() )
    if profile.role=="ADMIN":
      incident=model.Incident.get(key)
      if incident:
        for image in incident.images:
          image.delete()
        incident.delete()
    self.redirect("/")
	  
class Categories(RequestHandler):
  def get(self):
    user = users.get_current_user()
    profile=None
    message=None
    if not user:
      self.redirect(users.create_login_url( "/shoppingCart/" ))
    else:
      profile=model.Profile.from_user( user )
    if not profile:
      self.redirect(users.create_login_url( "/profile"))
    data={
      'profile': model.Profile.from_user(users.get_current_user()),
	}
    path = os.path.join(os.path.dirname(__file__), 'templates/categories.htm')	
    util.add_user( self.request.uri, data )
    self.response.out.write(template.render(path, data))
	
  def post(self):
    if self.request.get('mainpage'):
      data=[]
      if model.Category.all(keys_only=True).count(10)<1:
        cat=model.Category(name="root", description="Categoria raiz esta categoria solo sirve como punto de partida")
        cat.put()
      root=model.Category.root()
      data.insert(0,self.fillchildren(root,None))
    else:
      user = users.get_current_user()
      data = {}
      profile=None
      if not user:
        data['redirect'] = users.create_login_url( "/" )
      else:
        profile=model.Profile.from_user( user )
        if profile==None:
          data['redirect'] = users.create_login_url( "/profile")
        else:
          if self.request.get('command'):	
            command=self.request.get('command')
            if command=="delete":
              try:
                parent=model.Category.get(self.request.get('parentKey'))
                cat=model.Category.get(self.request.get('Key'))
                parent.children.remove(cat.key())
                cat.delete()
                parent.put()
              except:
                logging.info("Se intento eliminar la categoria raiz")
            if command=="create":
              parent=model.Category.get(self.request.get('parentKey'))
              cat=model.Category(name=self.request.get('name'),parent=parent,description="")
              cat.put()
              parent.children.append(cat.key())
              parent.put()
            if command=="rename":
              cat=model.Category.get(self.request.get('Key'))
              cat.name=self.request.get('name')
              cat.put()
            #self.redirect("/categories")
            data['success'] = True
          else:
            data=[]
            if model.Category.all(keys_only=True).count(10)<1:
              cat=model.Category(name="root", description="Categoria raiz esta categoria solo sirve como punto de partida")
              cat.put()
            root=model.Category.root()
            item=None
            if self.request.get("itemkey"):
              item=model.Incident.get(self.request.get("itemkey"))
            data.insert(0,self.fillchildren(root,item))
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(data))
	
  def fillchildren(self,cat,item=None):
    if len(cat.children)==0:
      if item:
        if cat.key() in item.categories:
          return {'id': '%s'%(cat.key()),'text':cat.name,'state':{ 'opened' : True, 'selected' : True, 'checked' : True},'children':[]}
        else:
          return {'id': '%s'%(cat.key()),'text':cat.name,'state':{ 'opened' : True, 'selected' : False, 'checked' : False},'children':[]}
      else:
        return {'id': '%s'%(cat.key()),'text':cat.name,'state':{ 'opened' : True, 'selected' : False },'children':[]}
    else:
      chdata=[]
      for child in cat.children:
        child=model.Category.get(child)
        chdata.insert(0,self.fillchildren(child,item))
      if item:
        if cat.key() in item.categories:
          return {'id': '%s'%(cat.key()),'text':cat.name,'state':{ 'opened' : True, 'selected' : True , 'checked' : True},'children':chdata}
        else:
          return {'id': '%s'%(cat.key()),'text':cat.name,'state':{ 'opened' : True, 'selected' : False , 'checked' : False},'children':chdata}
      else:
        return {'id': '%s'%(cat.key()),'text':cat.name,'state':{ 'opened' : True, 'selected' : False },'children':chdata}

class Items(RequestHandler):
  def post(self,key):
    category=model.Category.get(key)
    if category:
      data={}
      if category.name=="root":
        data={'items':model.Item.recent()}
      else:
        data={'items':category.members}
      path = os.path.join(os.path.dirname(__file__), 'templates/items.htm')	
      user=users.get_current_user()
      util.add_user( self.request.uri, data )
      data['profile']=model.Profile.from_user(user)
      self.response.out.write(template.render(path, data))
	  
class Item(RequestHandler):
  def get(self,key):
    data={}
    item=model.Item.get(key)
    data['item']=item
    path = os.path.join(os.path.dirname(__file__), 'templates/item.htm')	
    user=users.get_current_user()
    util.add_user( self.request.uri, data )
    data['profile']=model.Profile.from_user(user)
    self.response.out.write(template.render(path, data))

class NotFound (RequestHandler):
  def get(self):
    self.error(404)
	

app = webapp.WSGIApplication( [
    ('/', Home),
    ('/item/(.*)/', Item),
    ('/items/(.*)/', Items),
    ('/incident', Incident),
    ('/incident/(.*)/', Incident),
    ('/update', Update),
    ('/update/(.*)/', Update),
    ('/delete/(.*)/', Delete),
    ('/image/(.*)/', Image),
    ('/profile', Profile),
    ('/categories', Categories),
    ('/.*', NotFound)
  ],
  debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(app)

if __name__ == "__main__":
  main()
