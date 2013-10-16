import cgi
import urllib
import datetime

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

# grab the database class definitions
# Species, FarmContent, FarmUpdate
execfile("db_classes.py")

REQUEST_LIMIT = 70

MAIN_PAGE_FOOTER_TEMPLATE = """\

    <a href="%s">%s</a>

  </body>
</html>
"""
SPECIES_FORM_TEMPLATE = """    <form name="species" action="/admin/species" method="post">
      <div>URL:<input type="text" name="url" rows="1" cols="30"></input></div>
      <div>Type's full name:<input type="text" name="name" rows="1" cols="30"></input></div>
      <div><input type="submit" value="Add Species"></div>
    </form>
    """
    
SPECIAL_FORM_TEMPLATE = """    <form name="special" action="/admin/special" method="post">
      <div>URL:<input type="text" name="url" rows="1" cols="30"></input></div>
      <div>Special's full name:<input type="text" name="name" rows="1" cols="30"></input></div>
      <div><input type="submit" value="Add Special Monster"></div>
    </form>
    """
    
BULK_UPLOAD_TEMPLATE = """
   <form name="bulk" action="/admin/bulk" method="post">
   <div>Paste csv in here.</div>
   <div><textarea cols="80" rows="20" name="tsv"></textarea></div>
   <div>Separator character: <input type="text" name="sep"></input></div>
   <div><input type="submit" value="Send CSV"></div>
   </form>
"""

BULK_SPECIAL_TEMPLATE = """
   <form name="bulk_special" action="/admin/specialbulk" method="post">
   <div>Paste csv in here.</div>
   <div><textarea cols="80" rows="20" name="tsv"></textarea></div>
   <div>Separator character: <input type="text" name="sep"></input></div>
   <div><input type="submit" value="Special CSV"></div>
   </form>
"""

# first arg: concatted species templates
# second arg: today's date, as in 2013-09-22
FARM_FORM_TEMPLATE = """
      <form name="farm" action="/admin/farm" method="post">
      <div>Name:<input type="text" name="name" cols="30"></input></div>
      <div>Monster type:<select name="species">
        %s
      </select></div>
      <div>Expiry:<input name="expiry" type="date" value="%s"></input></div>
      <div><table border=1>
        <tr>
          <th>SS</th>
          <th>S</th>
          <th>A+</th>
          <th>A</th>
          <th>B+</th>
          <th>B</th>
          <th>C</th>
        </tr>
        <tr>
          <td><input type="number" name="ss" size="4" value="0"></input></div></td>
          <td><input type="number" name="s" size="4" value="0"></input></div></td>
          <td><input type="number" name="aplus" size="4" value="0"></input></div></td>
          <td><input type="number" name="a" size="4" value="0"></input></div></td>
          <td><input type="number" name="bplus" size="4" value="0"></input></div></td>
          <td><input type="number" name="b" size="4" value="0"></input></div></td>
          <td><input type="number" name="c" size="4" value="0"></input></div></td>
        </tr>
      </table></div>
      <div><input type="submit" value="Add Farm"></div>
    </form>
    """

# (species key, species print name)
FARM_SPECIES_TEMPLATE = '<option value="%s">%s</option>'

VALUE_ERROR_TEMPLATE = """
<html><head><title>Value Error</title></head>
  <body><h2>Input Error</h2>
    <div>%s</div>
    <div><a href="/admin/">Go back.</a></div>
  </body>
</html>
"""



# for now I can construct this conveniently without a DB lookup
def get_species_key(species_name):
  return ndb.Key('Species', species_name)

def get_farm_key(species_name, farm_name):
  return ndb.Key('Species', species_name, 'FarmContent', farm_name)

# seems to work fine.  
def get_special_key(special_name):
  return ndb.Key('Special', special_name)
  
def get_special_farm_key(special_name, farm_name):
  return ndb.Key('Special', special_name, 'SpecialContent', farm_name)



# pass the correctly capitalized farm name.
def validate_farm(species_name, farm_name):
  # request the farm's most recent update, use that to populate
  update_query = FarmUpdate.query(ancestor = get_farm_key(species_name,farm_name.lower())).order(-FarmUpdate.date)
  update = update_query.get()
  if update:
        farm = FarmContent(id=farm_name.lower(), 
                           parent=get_species_key(species_name))
        farm.name = farm_name
        farm.ss = update.ss
        farm.s = update.s
        farm.aplus = update.aplus
        farm.a = update.a
        farm.bplus = update.bplus
        farm.b = update.b
        farm.c = update.c
        farm.expiry = update.expiry
        farm.put()
        
def zint(input):
  if input=='':
    return 0
  else:
    return int(input)

# pass the correctly capitalized farm name.
def validate_special_farm(special_name, farm_name):
  # request the farm's most recent update, use that to populate
  update_query = SpecialUpdate.query(ancestor = get_special_farm_key(special_name,farm_name.lower())).order(-SpecialUpdate.date)
  update = update_query.get()
  if update:
        farm = SpecialContent(id=farm_name.lower(), 
                           parent=get_special_key(special_name))
        farm.name = farm_name
        farm.quantity = update.quantity
        farm.expiry = update.expiry
        farm.put()
        
def oint(input):
  if input=='':
    return 1
  else:
    return int(input)



class MainPage(webapp2.RequestHandler):

    def get(self):
        self.response.write('<html><body>')
        now = datetime.datetime.now()
        
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            
        # block for adding Species to the DB.
        
        self.response.write('<h3>Species</h3>')
        # dump out all existing species, I guess.
        species_query = Species.query() #.order(Species.url)
        specieses = species_query.fetch(REQUEST_LIMIT)
        for species in specieses:
          self.response.write("<b>%s:</b> %s <br />" % (species.key.id(),species.name))
                
        self.response.write(SPECIES_FORM_TEMPLATE)
        
        # block for adding Farms to the DB.
        self.response.write('<h3>Farms</h3>')
        
        formatted_options = map(lambda s: FARM_SPECIES_TEMPLATE % (s.key.id(), s.name), specieses)
        self.response.write(FARM_FORM_TEMPLATE % 
                            ("\n".join(formatted_options), 
                             now.strftime("%Y-%m-%d")
                            )
                           )
        # bulk uploading form
        self.response.write(BULK_UPLOAD_TEMPLATE)
        
        # block for adding Specials to the DB.
         
        self.response.write('<h3>Specials</h3>')
        special_query = Special.query() #.order(Species.url)
        specials = special_query.fetch(REQUEST_LIMIT)
        for special in specials:
          self.response.write("<b>%s:</b> %s <br />" % (special.key.id(),special.name))
        
        self.response.write(SPECIAL_FORM_TEMPLATE)
        # block for adding special farms to the DB.
        
        #bulk upload
        self.response.write(BULK_SPECIAL_TEMPLATE)
        
            
        # finish it off with a logging out button.
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE %
                            (url, url_linktext))
                            
class SpeciesAdd(webapp2.RequestHandler):

    def post(self):
      species = Species(id=self.request.get('url'))
      #species.url = self.request.get('url')
      species.name = self.request.get('name')
      species.put()
      self.redirect('/admin/')
      
class FarmAdd(webapp2.RequestHandler):

    def post(self):
      try: 
        farm = FarmContent(id=self.request.get('name').lower(), 
                           parent=get_species_key(self.request.get('species')))
        if len(self.request.get('name')) == 0:
          raise ValueError("Farm name must be longer than 0.")
        else:
          farm.name = self.request.get('name')
        farm.ss = int(self.request.get('ss'))
        farm.s = int(self.request.get('s'))
        farm.aplus = int(self.request.get('aplus'))
        farm.a = int(self.request.get('a'))
        farm.bplus = int(self.request.get('bplus'))
        farm.b = int(self.request.get('b'))
        farm.c = int(self.request.get('c'))
        farm.expiry = datetime.datetime.strptime(self.request.get('expiry'),"%Y-%m-%d").date()
        farm.put()
        self.redirect('/admin/')
      except ValueError as e:
        self.response.write(VALUE_ERROR_TEMPLATE % str(e))
      
class BulkAdd(webapp2.RequestHandler):
    
    def post(self):
       self.response.write('<html><body><div>Parsing...</div>')
       user = users.get_current_user()
       # start by splitting it into rows
       bulk_rows = self.request.get('tsv').splitlines()
       farms = set()
       for r in bulk_rows:
         try:
           info = r.split(self.request.get('sep'))
           update = FarmUpdate(parent=get_farm_key(info[2], info[1].lower()))
           update.ss = zint(info[3])
           update.s = zint(info[4])
           update.aplus = zint(info[5])
           update.a = zint(info[6])
           update.bplus = zint(info[7])
           update.b = zint(info[8])
           update.c = zint(info[9])
           update.expiry = datetime.datetime.strptime(info[10],"%Y-%m-%d").date()
           update.date = datetime.datetime.strptime(info[0],"%Y-%m-%d %H:%M:%S")
           update.author = user.user_id()
           update.put()
           self.response.write('<div>%s</div>\n' % str(info))
           if info[1].lower() not in farms:
             farms.add((info[2],info[1]))
         except ValueError as e:
           self.response.write('<div>Failed: %s</div>\n' % str(e))
       self.response.write('<div>Added updates.</div>')
       # now update the farms 
       for f in farms:
         validate_farm(f[0],f[1])
         self.response.write('<div>Validated %s for %s.</div>\n' % f)
       self.response.write('<div>Done.</div></body></html>')
       
class SpecialAdd(webapp2.RequestHandler):

    def post(self):
      special = Special(id=self.request.get('url'))
      special.name = self.request.get('name')
      special.put()
      self.redirect('/admin/')
      
class SpecialFarmAdd(webapp2.RequestHandler):

    def post(self):
      try: 
        farm = SpecialContent(id=self.request.get('name').lower(), 
                           parent=get_special_key(self.request.get('special')))
        if len(self.request.get('name')) == 0:
          raise ValueError("Farm name must be longer than 0.")
        else:
          farm.name = self.request.get('name')
        farm.ss = int(self.request.get('ss'))
        farm.s = int(self.request.get('s'))
        farm.aplus = int(self.request.get('aplus'))
        farm.a = int(self.request.get('a'))
        farm.bplus = int(self.request.get('bplus'))
        farm.b = int(self.request.get('b'))
        farm.c = int(self.request.get('c'))
        farm.expiry = datetime.datetime.strptime(self.request.get('expiry'),"%Y-%m-%d").date()
        farm.put()
        self.redirect('/admin/')
      except ValueError as e:
        self.response.write(VALUE_ERROR_TEMPLATE % str(e))
      
class BulkSpecialAdd(webapp2.RequestHandler):
    
    def post(self):
       self.response.write('<html><body><div>Parsing...</div>')
       user = users.get_current_user()
       # start by splitting it into rows
       bulk_rows = self.request.get('tsv').splitlines()
       farms = set()
       for r in bulk_rows:
         try:
           info = r.split(self.request.get('sep'))
           update = SpecialUpdate(parent=get_special_farm_key(info[2], info[1].lower()))
           update.quantity = oint(info[3])
           update.expiry = datetime.datetime.strptime(info[4],"%Y-%m-%d").date()
           update.date = datetime.datetime.strptime(info[0],"%Y-%m-%d %H:%M:%S")
           update.author = user.user_id()
           update.put()
           self.response.write('<div>%s</div>\n' % str(info))
           if info[1].lower() not in farms:
             farms.add((info[2],info[1]))
         except ValueError as e:
           self.response.write('<div>Failed: %s</div>\n' % str(e))
       self.response.write('<div>Added updates.</div>')
       # now update the farms 
       for f in farms:
         validate_special_farm(f[0],f[1])
         self.response.write('<div>Validated %s for %s.</div>\n' % f)
       self.response.write('<div><a href="/admin/">Done.</a></div></body></html>')


application = webapp2.WSGIApplication([
    ('/admin/', MainPage),
    ('/admin/species', SpeciesAdd),
    ('/admin/farm', FarmAdd),
    ('/admin/bulk',BulkAdd),
    ('/admin/special', SpecialAdd),
    ('/admin/specialfarm', SpecialFarmAdd),
    ('/admin/specialbulk', BulkSpecialAdd),
], debug=True)