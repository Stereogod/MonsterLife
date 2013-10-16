This is the Google AppEngine code behind the MapleStory Monster Life farm tracker.

To deploy it, follow the Google AppEngine instructions to create an application,
and upload the code to it.  

Once it's running, visit <example.com>/admin/ to get the behind the scenes view. 
It's pretty barebones, but in the upper Species section you can enter a type to 
make it available on the front page.
  Example input:
    - URL:
       aliens
    - Type's full name:
       Aliens & Humanoids
The url version is used to keep web addresses clean, the second version is 
displayed.

The "paste csv here" section can be used to bulk add lines from a spreadsheet.
Separator doesn't matter, but the columns need to be 
Update Date | Farm name | Farm type* | SS | S | A+ | A | B+ | B | C | Expiry date
* farm type should be the same as the URL version above.
  Example input:
   - paste csv:
      2010-07-31 12:30:01, AlienFanatic, aliens, 1, 5, 1, 0, 0, 0, 0, 2010-11-15
      2010-07-31 12:45:13, AlienFanatic, aliens, 1, 6, 0, 0, 0, 0, 0, 2010-11-16
   - separator:
      ,
When you hit 'Send CSV', it'll run through each line and give you diagnostic
information (actually it'll just do a python str(farm_tuple)).  Once it's read
all of the lines, it will go through each farm that had an update and verify the
most recent update.  If any rank's count is empty, it will assume 0.

The Special section works the same way.  The only difference is the columns:
Update date | Farm name | special type* | quantity | expiry date
If "quantity" is blank, it will assume 1.

In general, all you need to do is add the set of types and then it runs itself.
If you run into problematic updates, you'll have to use the appengine's NDB admin
page to find and remove them - I'd like to add a tool for this but have not yet
done so.

NDB/datastore doesn't use traditional rdb tables.  What it does have is a set 
of templates that are arranged hierarchically, so these go as follows:
Species
+ FarmContent
  + FarmUpdate

Special
+ SpecialContent
  + SpecialUpdate

Every update submitted is first turned into a FarmUpdate / SpecialUpdate, then
used to edit the FarmContent / SpecialContent which is its parent.  In order to
verify FarmContent / SpecialContent, you query its children for the one with the
most recent date and set its values to match those.  Normally this isn't necessary
but if it is, see admin.py bulk update for a method (it works on a list of farm 
names + type tuples).

As of this writing there's nothing actually implemented to block users from
submitting updates - if added, it would be an admin tool to delete Updates from
their user ID, fix affected farms, and put them on a blacklist who's not allowed
to use the update pages.