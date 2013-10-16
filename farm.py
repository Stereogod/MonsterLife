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

# (" - species")   
MAIN_PAGE_HEADER_TEMPLATE = """<!DOCTYPE HTML>
    <html>
      <head>
        <title>Monster Life Reference%s</title>
        <style media="screen" type="text/css">
          div.fuckoffchrome input[type='number'] { width: 3em }
        </style>
      </head>
      <body>
"""

# (login/out url, word)
MAIN_PAGE_FOOTER_TEMPLATE = """\

    <hr>
    <div class="footer">
    <a href="%s">%s</a>
    </div>
  </body>
</html>
"""

# 'special' or '', type key, display name, home url, word
LOGGED_IN_FOOTER_TEMPLATE = """\
    <hr>
    <div class="footer">
      <div class="update">Update: 
        <a href="/update%s?type=%s&return=true">%s</a> 
        <a href="/update">Regular monster</a> 
        <a href="/updatespecial">Special \
        monster</a>
      </div>
      <a href="%s">%s</a>
    </div>
  </body>
</html>
"""



# (url, name)
MAIN_PAGE_SPECIES_TEMPLATE = """
    <a href="/s/%s">%s</a><br />
    """
    
MAIN_PAGE_SPECIAL_TEMPLATE = """
    <a href="/sp/%s">%s</a><br />
    """

SPECIES_PAGE_TABLE_HEADER_TEMPLATE = """
<table border=1>
        <col />
        <col width="30" />
        <col width="30" />
        <col width="30" />
        <col width="30" />
        <col width="30" />
        <col width="30" />
        <col width="30" />
        <col />
        <tr>
          <th>Farm</th>
          <th>SS</th>
          <th>S</th>
          <th>A+</th>
          <th>A</th>
          <th>B+</th>
          <th>B</th>
          <th>C</th>
          <th>Expiry</th>
        </tr>
"""
SPECIES_PAGE_TABLE_ROW_TEMPLATE = """
        <tr>
          <td><strong>%s</strong></td>
          <td>%s</td>
          <td>%s</td>
          <td>%s</td>
          <td>%s</td>
          <td>%s</td>
          <td>%s</td>
          <td>%s</td>
          <td>%s</td>
        </tr>
"""

# species, farm name, farm name
SPECIES_EDIT_TEMPLATE = """
<a href="/update?type=%s&farm=%s&return=true"><img src="/images/16x16edit.png" /></a>%s
"""


SPECIES_PAGE_TABLE_FOOTER_TEMPLATE = """
</table>
<a href="%s?from=%s">Show another month worth of possibly expired farms.</a>
"""

# (url, name)
SPECIES_PAGE_SPECIES_TEMPLATE = """
    <a href="/s/%s">%s</a>
    """
    

SPECIAL_PAGE_TABLE_HEADER_TEMPLATE = """
<table border=1>
        <col />
        <col width="30" />
        <col />
        <tr>
          <th>Farm</th>
          <th>Quantity</th>
          <th>Expiry</th>
        </tr>
"""
SPECIAL_PAGE_TABLE_ROW_TEMPLATE = """
        <tr>
          <td><strong>%s</strong></td>
          <td>%s</td>
          <td>%s</td>
        </tr>
"""

# species, farm name, farm name
SPECIAL_EDIT_TEMPLATE = """
<a href="/updatespecial?type=%s&farm=%s&return=true"><img src="/images/16x16edit.png" /></a>%s
"""


SPECIAL_PAGE_TABLE_FOOTER_TEMPLATE = """
</table>
"""

# (url, name)
SPECIAL_PAGE_SPECIES_TEMPLATE = """
    <a href="/sp/%s">%s</a>
    """



VALUE_ERROR_TEMPLATE = """
    <h2>Your Update Had A Problem</h2>
    <div>%s</div>
"""

UPDATE_SUCCESS_TEMPLATE = """
    <h3>Your Update Succeeded!</h3>
    <div>You successfully updated %s.</div>
"""

# args: query options, farm name, option list, expiry time, quantity of each rank
FARM_FORM_TEMPLATE = """
      <form name="farmupdate" action="/update%s" method="post">
      <div class="fuckoffchrome"><table border=0>
        <tr>
          <th>Farm Name</th>
          <th>Type</th>
          <th>Expiry</th>
          <th>SS</th>
          <th>S</th>
          <th>A+</th>
          <th>A</th>
          <th>B+</th>
          <th>B</th>
          <th>C</th>
          <th>&nbsp;</th>
        </tr>
        <tr>
          <td><input type="text" name="name" cols="30" value="%s"></input></td>
          <td><select name="species">
                %s
              </select></td>
          <td><input name="expiry" type="date" value="%s"></input></td>
          <td><input type="number" name="ss" size="4" value="%s"></input></div></td>
          <td><input type="number" name="s" size="4" value="%s"></input></div></td>
          <td><input type="number" name="aplus" size="4" value="%s"></input></div></td>
          <td><input type="number" name="a" size="4" value="%s"></input></div></td>
          <td><input type="number" name="bplus" size="4" value="%s"></input></div></td>
          <td><input type="number" name="b" size="4" value="%s"></input></div></td>
          <td><input type="number" name="c" size="4" value="%s"></input></div></td>
          <td><input type="submit" value="Submit Update"></td>
        </tr>
      </table></div>
      <div></div>
    </form>
    """

# (species key, species print name)
FARM_SPECIES_TEMPLATE = '<option value="%s">%s</option>'

# args: query options, farm name, option list, expiry time, quantity of each rank
SPECIAL_FORM_TEMPLATE = """
      <form name="farmspecialupdate" action="/updatespecial%s" method="post">
      <div class="fuckoffchrome"><table border=0>
        <tr>
          <th>Farm Name</th>
          <th>Type</th>
          <th>Expiry</th>
          <th>Quantity</th>
          <th>&nbsp;</th>
        </tr>
        <tr>
          <td><input type="text" name="name" cols="30" value="%s"></input></td>
          <td><select name="special">
                %s
              </select></td>
          <td><input name="expiry" type="date" value="%s"></input></td>
          <td><input type="number" name="quantity" size="4" value="%s"></input></div></td>
          <td><input type="submit" value="Submit Update"></td>
        </tr>
      </table></div>
      <div></div>
    </form>
    """


def remove_zeroes(list):
  return tuple(["&nbsp;" if x==0 else x for x in list])
  
def get_species_key(species_name):
  return ndb.Key('Species', species_name)
  
def get_farm_key(species_name, farm_name):
  return ndb.Key('Species', species_name, 'FarmContent', farm_name)
  
# seems to work fine.  
def get_special_key(special_name):
  return ndb.Key('Special', special_name)
  
def get_special_farm_key(special_name, farm_name):
  return ndb.Key('Special', special_name, 'SpecialContent', farm_name)


  
def count(input):
  r = int(input)
  if r < 0 or r > 50:
    raise ValueError("Number of monsters must be between 0 and 20.")
  return r
  

class MainPage(webapp2.RequestHandler):

    def get(self):
        self.response.write(MAIN_PAGE_HEADER_TEMPLATE % "")
        
        # list the types of regular monsters
        self.response.write('<div class="species"><h3>Monster Types</h3>\n')
        species_query = Species.query() #.order(Species.url)
        species_keys = species_query.fetch(REQUEST_LIMIT,keys_only=True)
        specieses = ndb.get_multi(species_keys)
        for species in specieses:
          self.response.write(MAIN_PAGE_SPECIES_TEMPLATE % (species.key.id(),species.name))
                
        self.response.write('</div>')
        # list the types of special monsters
        self.response.write('<div class="special"><h3>Special Types</h3>\n')
        special_query = Special.query()
        special_keys = special_query.fetch(REQUEST_LIMIT, keys_only=True) # find out if 50 is enough
        specials = ndb.get_multi(special_keys)
        for sp in specials:
          self.response.write(MAIN_PAGE_SPECIAL_TEMPLATE % (sp.key.id(),sp.name))
        self.response.write('</div>')
        
        # link to update form, I guess?
        
        if users.get_current_user():
            self.response.write('<div class="update">\
              <h3>Update</h3><a href="/update">Submit \
              a regular monster update.</a> <br />\
              <a href="/updatespecial">Submit a special \
              monster update.</a></div>')
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
	    url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            
        # finish it off with a logging out button.
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE %
                            (url, url_linktext))
                            

class SpeciesPage(webapp2.RequestHandler):
      
      def get(self, species):
        today = datetime.datetime.now().date()
        #self.response.write("Placeholder for %s" % species)
        try:
          species_key = ndb.Key('Species', species)
          species_descr = species_key.get()
          self.response.write(MAIN_PAGE_HEADER_TEMPLATE % " ".join([" -", species_descr.name]))
          self.response.write("<h3>%s</h3>" % species_descr.name)
          
          # add the top bit of the table.
          self.response.write(SPECIES_PAGE_TABLE_HEADER_TEMPLATE)
          
          # check for a page option to get all
          if self.request.get("from"):
            time = datetime.datetime.strptime(self.request.get('from'),"%Y-%m-%d").date()
          else:
            time = today
          # pull all the responses from the DB
          farm_query = FarmContent.query(FarmContent.expiry >= time, ancestor=species_key)
          farm_keys = farm_query.fetch(REQUEST_LIMIT,keys_only=True)
          farms = ndb.get_multi(farm_keys)
          farms.sort(key = lambda f: (f.ss,f.s,f.aplus,f.a,f.bplus,f.b,f.c), reverse=True)

          for f in farms:
            if users.get_current_user():
              farm_name_string = SPECIES_EDIT_TEMPLATE % (species, f.name, f.name)
              
            else:
              farm_name_string = f.name
            self.response.write(SPECIES_PAGE_TABLE_ROW_TEMPLATE % remove_zeroes([farm_name_string,f.ss,f.s,f.aplus,f.a,f.bplus,f.b,f.c,f.expiry]))
             
          # calculate the 'back a month'
          month = datetime.timedelta(days=30)
          time = time - month
          self.response.write(SPECIES_PAGE_TABLE_FOOTER_TEMPLATE % (species, time.strftime("%Y-%m-%d")))
          
          # plus monster types, at the bottom.
          self.response.write('<hr><div class="species">\n')
          species_query = Species.query() #.order(Species.url)
          species_keys = species_query.fetch(REQUEST_LIMIT,keys_only=True)
          specieses = ndb.get_multi(species_keys)
          for species in specieses:
            self.response.write(SPECIES_PAGE_SPECIES_TEMPLATE % (species.key.id(),species.name))

          self.response.write('</div>')
          if users.get_current_user():
            self.response.write(LOGGED_IN_FOOTER_TEMPLATE % ('',species_descr.key.id(), species_descr.name,"/","Home"))
          else:
            self.response.write(MAIN_PAGE_FOOTER_TEMPLATE % ("/","Home"))
        except AttributeError:
          # display an error of the "type not known" sort.
          self.response.write(MAIN_PAGE_HEADER_TEMPLATE % " - Unknown Type")
          self.response.write('<h3>Type Error</h3><div>Unknown type "%s".</div>' % species)
          self.response.write(MAIN_PAGE_FOOTER_TEMPLATE % ("/","Home"))

class SpecialPage(webapp2.RequestHandler):
      
      def get(self, special):
        today = datetime.datetime.now().date()
        #self.response.write("Placeholder for %s" % special)
        try:
          special_key = ndb.Key('Special', special)
          special_descr = special_key.get()
          self.response.write(MAIN_PAGE_HEADER_TEMPLATE % " ".join([" -", special_descr.name]))
          self.response.write("<h3>%s</h3>" % special_descr.name)
          
          # add the top bit of the table.
          self.response.write(SPECIAL_PAGE_TABLE_HEADER_TEMPLATE)

          # pull all the responses from the DB
          farm_query = SpecialContent.query(SpecialContent.quantity > 0, ancestor=special_key).order(-SpecialContent.quantity, -SpecialContent.expiry)
          farm_keys = farm_query.fetch(REQUEST_LIMIT,keys_only=True)
          # try it unsorted?
          #farms.sort(key = lambda f: (f.quantity, f.expiry), reverse=True)
          farms = ndb.get_multi(farm_keys)
          for f in farms:
            if users.get_current_user():
              farm_name_string = SPECIAL_EDIT_TEMPLATE % (special, f.name, f.name)
              
            else:
              farm_name_string = f.name
            self.response.write(SPECIAL_PAGE_TABLE_ROW_TEMPLATE % remove_zeroes([farm_name_string,f.quantity,f.expiry]))
             
          self.response.write(SPECIAL_PAGE_TABLE_FOOTER_TEMPLATE)
          
          # plus monster types, at the bottom.
          self.response.write('<hr><div class="special">\n')
          special_query = Special.query() #.order(Special.url)
          specials = special_query.fetch(REQUEST_LIMIT,keys_only=True)
          speciales = ndb.get_multi(specials)
          for special in speciales:
            self.response.write(SPECIAL_PAGE_SPECIES_TEMPLATE % (special.key.id(),special.name))

          self.response.write('</div>')
          
          if users.get_current_user():
            self.response.write(LOGGED_IN_FOOTER_TEMPLATE % ('special',special_descr.key.id(), special_descr.name,"/","Home"))
          else:
            self.response.write(MAIN_PAGE_FOOTER_TEMPLATE % ("/","Home"))
        except AttributeError:
          # display an error of the "type not known" sort.
          self.response.write(MAIN_PAGE_HEADER_TEMPLATE % " - Unknown Type")
          self.response.write('<h3>Type Error</h3><div>Unknown type "%s".</div>' % special)
          self.response.write(MAIN_PAGE_FOOTER_TEMPLATE % ("/","Home"))




class UpdatePage(webapp2.RequestHandler):
      
      # plain old hitting the url
      def get(self):
        if users.get_current_user():
          self.header()
          self.response.write("Farm name should follow the original \
             capitalization.  Expiry time should be set to the last \
             expiry - that is, the date when all of the monsters \
             have expired.")
          self.page()
        else:
          url = users.create_login_url(self.request.uri)
          url_linktext = 'Login'
          self.redirect(url)
        
      # it posts to itself, so it should handle those
      def post(self):
        self.header()
        try: 
          # todo: check user credentials
          user = users.get_current_user()
          if not user:
            raise ValueError("You need to be signed in to add updates.")
          # primary FarmContent edit
          farm = FarmContent(id=self.request.get('name').lower(), 
                             parent=get_species_key(self.request.get('species')))
          if len(self.request.get('name')) == 0 or len(self.request.get('name')) > 12:
            raise ValueError("Farm name must be 1 to 12 characters.")
          else:
            farm.name = self.request.get('name')
          farm.ss = count(self.request.get('ss'))
          farm.s = count(self.request.get('s'))
          farm.aplus = count(self.request.get('aplus'))
          farm.a = count(self.request.get('a'))
          farm.bplus = count(self.request.get('bplus'))
          farm.b = count(self.request.get('b'))
          farm.c = count(self.request.get('c'))
          farm.expiry = datetime.datetime.strptime(self.request.get('expiry'),"%Y-%m-%d").date()
          farm.put()
          # add FarmUpdate info.
          update = FarmUpdate(parent=farm.key)
          update.ss = count(self.request.get('ss'))
          update.s = count(self.request.get('s'))
          update.aplus = count(self.request.get('aplus'))
          update.a = count(self.request.get('a'))
          update.bplus = count(self.request.get('bplus'))
          update.b = count(self.request.get('b'))
          update.c = count(self.request.get('c'))
          update.expiry = datetime.datetime.strptime(self.request.get('expiry'),"%Y-%m-%d").date()
          update.author = user.user_id()
          update.put()
          
          self.response.write(UPDATE_SUCCESS_TEMPLATE % farm.name)
          # or, if return=true and we just did a successful submission
          if self.request.get("return") == 'true':
            self.redirect(str("s/%s" % self.request.get("species")))
        except ValueError as e:
          self.response.write(VALUE_ERROR_TEMPLATE % str(e))
        self.page()
        
      def header(self):
        # write the page header
        self.response.write(MAIN_PAGE_HEADER_TEMPLATE % " - Update")
      
      def page(self):
        now = datetime.datetime.now()
        # write out the page as usual.
        self.response.write('<h3>Update Farm</h3>')
        # retrieve all the species names
        species_query = Species.query() #.order(Species.url)
        specieses = species_query.fetch(REQUEST_LIMIT)
        # fill in the select box template
        if self.request.get("type"):
          type = self.request.get("type")
          species = next(s for s in specieses if s.key.id() == type)
          formatted_options = [FARM_SPECIES_TEMPLATE % (type, species.name)]
          if self.request.get("farm"):
            species_key = get_farm_key(type,self.request.get("farm").lower())
            f = species_key.get()
            quantities = (f.ss,f.s,f.aplus,f.a,f.bplus,f.b,f.c,)
            expiry_time = f.expiry
          else:
            quantities = (0,0,0,0,0,0,0,)
            expiry_time = now
        else:
          formatted_options = map(lambda s: FARM_SPECIES_TEMPLATE % (s.key.id(), s.name), specieses)
          quantities = (0,0,0,0,0,0,0,)
          expiry_time = now
        if self.request.get("return")=='true':
          options = '?return=true'
        else:
          options = ''
        # and stick it into the table.
        self.response.write(FARM_FORM_TEMPLATE % 
                            ((options, self.request.get("farm"), "\n".join(formatted_options), 
                             expiry_time.strftime("%Y-%m-%d"),
                            ) + quantities)
                           )        
        
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE % ("/","Home"))


class UpdateSpecialPage(webapp2.RequestHandler):
      
      # plain old hitting the url
      def get(self):
        if users.get_current_user():
          self.header()
          self.response.write("Farm name should follow the original \
             capitalization.  Expiry time should be set to the final \
             expiry - that is, the date when all of the monsters \
             have expired.  If a farm no longer has the monster, \
             enter a quantity of 0 and the current date.  Now that \
             monsters can be revived, leave the listing alone if \
             the monster's still on the farm and expired, so it \
             can be located and revived if necessary.")
          self.page()
        else:
          url = users.create_login_url(self.request.uri)
          url_linktext = 'Login'
          self.redirect(url)
      
      
      def header(self):
        # write the page header
        self.response.write(MAIN_PAGE_HEADER_TEMPLATE % " - Special Update")
      
      def post(self):
        self.header()
        try: 
          # todo: check user credentials
          user = users.get_current_user()
          if not user:
            raise ValueError("You need to be signed in to add updates.")
          # primary SpecialContent edit
          farm = SpecialContent(id=self.request.get('name').lower(), 
                             parent=get_special_key(self.request.get('special')))
          if len(self.request.get('name')) == 0 or len(self.request.get('name')) > 12:
            raise ValueError("Farm name must be 1 to 12 characters.")
          else:
            farm.name = self.request.get('name')
          farm.quantity = count(self.request.get('quantity'))
          farm.expiry = datetime.datetime.strptime(self.request.get('expiry'),"%Y-%m-%d").date()
          farm.put()
          # add SpecialUpdate info.
          update = SpecialUpdate(parent=farm.key)
          update.ss = count(self.request.get('quantity'))
          update.expiry = datetime.datetime.strptime(self.request.get('expiry'),"%Y-%m-%d").date()
          update.author = user.user_id()
          update.put()
          
          self.response.write(UPDATE_SUCCESS_TEMPLATE % farm.name)
          # or, if return=true and we just did a successful submission
          if self.request.get("return") == 'true':
            self.redirect(str("/sp/%s" % self.request.get("special")))
        except ValueError as e:
          self.response.write(VALUE_ERROR_TEMPLATE % str(e))
        self.page()

      def page(self):
        now = datetime.datetime.now()
        # write out the page as usual.
        self.response.write("<h3>Update Farm's Special</h3>")
        # retrieve all the species names
        special_query = Special.query() #.order(Special.url)
        speciales = special_query.fetch(REQUEST_LIMIT)
        # fill in the select box template
        if self.request.get("type"):
          type = self.request.get("type")
          special = next(s for s in speciales if s.key.id() == type)
          formatted_options = [FARM_SPECIES_TEMPLATE % (type, special.name)]
          if self.request.get("farm"):
            special_key = get_special_farm_key(type,self.request.get("farm").lower())
            f = special_key.get()
            quantity = f.quantity
            expiry_time = f.expiry
          else:
            quantity = 1
            expiry_time = now
        else:
          formatted_options = map(lambda s: FARM_SPECIES_TEMPLATE % (s.key.id(), s.name), speciales)
          quantity = 1
          expiry_time = now
        if self.request.get("return")=='true':
          options = '?return=true'
        else:
          options = ''
        # and stick it into the table.
        self.response.write(SPECIAL_FORM_TEMPLATE % 
                            (options, self.request.get("farm"), "\n".join(formatted_options), 
                             expiry_time.strftime("%Y-%m-%d"),
                            quantity,)
                           )        
        
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE % ("/","Home"))




application = webapp2.WSGIApplication([
    ('/', MainPage),
    (r'/s/(\w+)',SpeciesPage),
    (r'/sp/(\w+)',SpecialPage),
    ('/update', UpdatePage),
    ('/updatespecial',UpdateSpecialPage),
], debug=True)