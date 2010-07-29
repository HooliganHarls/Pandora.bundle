from PMS import Plugin, Log, XML, HTTP, JSON, Prefs, RSS, Utils
from PMS.MediaXML import MediaContainer, DirectoryItem, WebVideoItem, SearchDirectoryItem, VideoItem
from PMS.FileTypes import PLS
from PMS.Shorthand import _L
  
useremail = ""
password = ""
helptext = "You must log into your Pandora account using Safari prior to using Pandora in Plex. The up and down arrows will let you thumbs up/down a song. Right arrow lets you skip a track."

PANDORA_PLUGIN_PREFIX = "/music/pandora"

####################################################################################################
def Start():
  # Current artwork.jpg free for personal use only - http://squaresailor.deviantart.com/art/Apple-Desktop-52188810
  Plugin.AddRequestHandler(PANDORA_PLUGIN_PREFIX, HandleVideosRequest, "Pandora", "icon-default.jpg", "art-default.jpg")
  Prefs.Expose("loginemail", "Login Email Address")
  Prefs.Expose("password", "Password")
####################################################################################################

def performLogin():
  values =  {'loginform': '',
            'login_username': useremail,
            'login_password': password}
  HTTP.Post('https://www.pandora.com/login.vm', values)
  
def pandoraWebNameFromEmail(email):
  jsonUrl = "http://feeds.pandora.com/services/ajax/?method=authenticate.emailToWebname&email=" + HTTP.Quote(email)
  dict = JSON.DictFromURL(jsonUrl)
  if dict["stat"] == "ok":
    return dict["result"]["webname"]
  else:
    return "WEBNAME_LOOKUP_ERROR" #need to handle this error
  
def populateFromFeed(url, dir):
  feed = RSS.Parse(url)
  for entry in feed["items"]:
    id = entry.link
    title = entry.description
    thumb = ""
    duration = ""
    dir.AppendItem(WebVideoItem(id, title, helptext, duration, thumb))
  return dir
  
def HandleVideosRequest(pathNouns, count):
  try:
    (pathNouns[count-1], title2) = pathNouns[count-1].split("||")
    title2 = _D(title2).encode("utf-8")
  except:
    title2 = ""
    
  dir = MediaContainer("art-default.jpg",None,title1="Pandora",title2=title2)
  if count == 0:
    useremail = Prefs.Get("loginemail")
    password = Prefs.Get("password")
    if useremail != None and password != None:
      webname = pandoraWebNameFromEmail(useremail)
      performLogin()
      if not webname == "WEBNAME_LOOKUP_ERROR":
        dir.AppendItem(DirectoryItem("stations^"+webname+"||Your Stations", "Your Stations", ""))
        dir.AppendItem(DirectoryItem("friends^"+webname+"||Your Friends", "Your Friends", ""))
        #dir.AppendItem(DirectoryItem("songs_"+webname, "Your Bookmarked Songs", ""))
        #dir.AppendItem(DirectoryItem("artists_"+webname, "Your Bookmarked Artists", ""))
        dir.AppendItem(SearchDirectoryItem("artistsearch", "Search/Add Station by Artist", "Search/Add Station by Artist", "search.png"))
        dir.AppendItem(SearchDirectoryItem("search^email", "Search for User Stations by Email", "Search for User Stations by Email", "search.png"))
        dir.AppendItem(SearchDirectoryItem("search^webname", "Search for User Stations by ID", "Search for User Stations by Email", "search.png"))
      else:
        dir.SetMessage(_L("InvalidEmail"), "Email address not found on Pandora.") #the plex pref email is no good
    
    if useremail != None:
      dir.AppendItem(SearchDirectoryItem("pref^loginemail", "Change Pandora email login [" + useremail + "]", "Set your Pandora email login.", ""))  
    else:
      dir.AppendItem(SearchDirectoryItem("pref^loginemail", "Set your Pandora email login", "Set your Pandora email login", ""))
    if password != None:
      dir.AppendItem(SearchDirectoryItem("pref^password", "Change your Pandora password", "Change your Pandora password", ""))
    else:
      dir.AppendItem(SearchDirectoryItem("pref^password", "Set your Pandora password", "Set your Pandora password", ""))
      
    dir.AppendItem(VideoItem("http://www.plexapp.com/screencasts/using/pandora.mov", "Pandora Help Screencast", "", "", "http://www.plexapp.com/screencasts/help.png"))
    
  elif pathNouns[0].startswith("stations"):
    if count == 1:
      dir = populateFromFeed("http://feeds.pandora.com/feeds/people/" + pathNouns[0].split("^")[1] + "/stations.xml", dir)
  #elif pathNouns[0][:6] == "songs_":
  #  if count == 1:
  #    return populateFromFeed("http://feeds.pandora.com/feeds/people/" + pathNouns[0][6:] + "/favorites.xml?max=100")
  #elif pathNouns[0][:8] == "artists_":
  #  if count == 1:
  #    return populateFromFeed("http://feeds.pandora.com/feeds/people/" + pathNouns[0][8:] + "/favoriteartists.xml?max=100")
  elif pathNouns[0].startswith("friends"):
    if count == 1:
      Log.Add(XML.ElementToString(XML.ElementFromURL("http://www.pandora.com/people/"+pathNouns[0].split("^")[1],True)))
      for f in XML.ElementFromURL("http://www.pandora.com/people/"+pathNouns[0].split("^")[1],True).xpath("//table[@id='tbl_friends_table']/tbody/tr/td/div/a"):
        dir.AppendItem(DirectoryItem(f.text, f.text, ""))
    if count == 2:
      dir = populateFromFeed("http://feeds.pandora.com/feeds/people/" + pathNouns[1] + "/stations.xml", dir)
      
  elif pathNouns[0].startswith("search"):
    if count > 1:
      query = pathNouns[1]  
      if count > 2:
        for i in range(2, len(pathNouns)): query += "/%s" % pathNouns[i]
      if pathNouns[0].split("^")[1] == "email":
        tmpWebName = pandoraWebNameFromEmail(query)
      else: 
        tmpWebName = query
      if not tmpWebName == "WEBNAME_LOOKUP_ERROR":
        dir = populateFromFeed("http://feeds.pandora.com/feeds/people/" + tmpWebName  + "/stations.xml", dir)
      else:
        dir.SetMessage(_L("InvalidEmail"), "Email address not found on Pandora.")

  elif pathNouns[0] == "artistsearch":
    if count == 2:
      query = pathNouns[1]
      #if count > 2:
      #  for i in range(2, len(pathNouns)): query += "/%s" % pathNouns[i]
      for r in XML.ElementFromURL("http://www.pandora.com/backstage?type=all&q="+query,True).xpath("//table[@id='tbl_artist_search_results']/tbody/tr"):
        thumb = r.xpath("td/a/img")[0].get("src")
        a = r.xpath("td/a")
        href = a[1].get("href")
        id = "http://www.pandora.com/?search=" + href[href.rfind("/")+1:]
        title = a[1].text
        duration=""
        dir.AppendItem(WebVideoItem(id, title, helptext, duration, thumb))
    
  elif pathNouns[0].startswith("pref"):
    if count == 2:
      field = pathNouns[0].split("^")[1]
      Prefs.Set(field,pathNouns[1])
      if field == "loginemail":
        dir.SetMessage("Pandora login", "Pandora email set.")
      else:
        dir.SetMessage("Pandora login", "Pandora password set.")
      
  return dir.ToXML()        