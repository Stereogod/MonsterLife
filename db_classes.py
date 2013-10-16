
# top level: each species has key_name containing the url and 'pretty' version of the type
class Species(ndb.Model):
  name = ndb.StringProperty()
  
# next level down:  a single farm, which will always have a Species ancestor.
# this is the reference level for the public face.
class FarmContent(ndb.Model):
  name = ndb.StringProperty()
  ss = ndb.IntegerProperty()
  s = ndb.IntegerProperty()
  aplus = ndb.IntegerProperty()
  a = ndb.IntegerProperty()
  bplus = ndb.IntegerProperty()
  b = ndb.IntegerProperty()
  c = ndb.IntegerProperty()
  expiry = ndb.DateProperty()
  
# an individual update submission: has a FarmContent ancestor.
# this contains a single update to a farm, and can be copied up to
# the FarmContent level in case of integrity checks.
class FarmUpdate(ndb.Model):
  ss = ndb.IntegerProperty()
  s = ndb.IntegerProperty()
  aplus = ndb.IntegerProperty()
  a = ndb.IntegerProperty()
  bplus = ndb.IntegerProperty()
  b = ndb.IntegerProperty()
  c = ndb.IntegerProperty()
  expiry = ndb.DateProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)
  # the spec is annoyingly vague on what format userIDs are.
  # "a str" indeed.  Anyway, good enough to test against a blacklist.
  author = ndb.StringProperty()
  

# special monsters
class Special(ndb.Model):
  name = ndb.StringProperty()
  
class SpecialContent(ndb.Model):
  name = ndb.StringProperty()
  quantity = ndb.IntegerProperty()
  expiry = ndb.DateProperty()
  
class SpecialUpdate(ndb.Model):
  quantity = ndb.IntegerProperty()
  expiry = ndb.DateProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)
  author = ndb.StringProperty()
  