
PANDORA_PLUGIN_PREFIX = "/music/pandora"
NAMESPACES = {'pandora':'http://www.pandora.com/rss/1.0/modules/pandora/','sy':'http://purl.org/rss/1.0/modules/syndication/','content':'http://purl.org/rss/1.0/modules/content/','dc':'http://purl.org/dc/elements/1.1/','mm':'http://musicbrainz.org/mm/mm-2.1#','fh':'http://purl.org/syndication/history/1.0','itms':'http://phobos.apple.com/rss/1.0/modules/itms/','az':'http://www.amazon.com/gp/aws/landing.html','xsi':'http://www.w3.org/2001/XMLSchema-instance'}
####################################################################################################
def Start():
  # Current artwork.jpg free for personal use only - http://squaresailor.deviantart.com/art/Apple-Desktop-52188810
    Plugin.AddPrefixHandler(PANDORA_PLUGIN_PREFIX, MainMenu, "Pandora", "icon-default.jpg", "art-default.jpg")
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    MediaContainer.art        =R("art-default.jpg")
    DirectoryItem.thumb       =R("icon-default.jpg")
####################################################################################################

def performLogin():
    values =  {'loginform': '',
            'login_username': Prefs['pan_user'],
            'login_password': Prefs['pan_pass']}
    jsonUrl = "http://feeds.pandora.com/services/ajax/?method=authenticate.emailToWebname&email=" + Prefs['pan_user']
    
    headers=HTTP.Request(jsonUrl).headers
    Log(headers)
    dict = JSON.ObjectFromURL(jsonUrl, values=values)
    if dict["stat"] == "ok":
        return dict["result"]["webname"]
    else:
        return "WEBNAME_LOOKUP_ERROR" #need to handle this error
####################################################################################################  
def MainMenu():
    
    dir= MediaContainer(viewGroup="List")
    useremail = Prefs['pan_user']
    password = Prefs['pan_pass']
    webname = pandoraWebNameFromEmail(useremail)
    webname=performLogin()
    Log(webname)
    if useremail == None or password == None or webname=="WEBNAME_LOOKUP_ERROR":
        dir.Append(PrefsItem("Set your Pandora Preferences","" , "", ""))
    else:
        dir.Append(Function(DirectoryItem(Stations, "Your Stations", ""), webname=webname))
        #dir.Append(Function(DirectoryItem(Friends, "Your Friends", ""), webname=webname))
        dir.Append(Function(DirectoryItem(Bookmarks, "Your Bookmarked Songs", ""), webname=webname))
        dir.Append(Function(DirectoryItem(BookmarkedArtists, "Your Bookmarked Artists", ""), webname=webname))
        dir.Append(Function(InputDirectoryItem(ArtistSearch, "Search/Add Station by Artist", "Search/Add Station by Artist", thumb=R("search.jpg"))))
        dir.Append(Function(InputDirectoryItem(EmailSearch, "Search for User Stations by Email", "Search for User Stations by Email", thumb=R("search.jpg"))))
        dir.Append(Function(InputDirectoryItem(WebnameSearch, "Search for User Stations by ID", "Search for User Stations by Email", thumb=R("search.jpg"))))
        
        dir.Append(PrefsItem("Change your Pandora Preferences","" , "", ""))
    
    return dir
    
 ####################################################################################################  
def Stations(sender,webname):
    dir= MediaContainer(viewGroup="List")
    url='http://feeds.pandora.com/feeds/people/'+webname+'/stations.xml'
    content=XML.ElementFromURL(url).xpath('//item',isHTML="False")
    
    for item in content:
        title = item.xpath('.//title')[0].text
        link=item.xpath('.//link')[0].text
        desc=item.xpath('.//description')[0].text
        thumb=item.xpath('./pandora:stationAlbumArtImageUrl',namespaces=NAMESPACES)[0].text
        Log(thumb)
        dir.Append(WebVideoItem(link,title=title,summary=desc,thumb=thumb))
    return dir
        
 ####################################################################################################  
#def Friends(sender,webname):
#    dir= MediaContainer(viewGroup="List")
#   url="http://www.pandora.com/favorites/profile_tablerows_listener.vm?webname="+webname
#    page=HTML.ElementFromURL(url,headers={'Referer':'http://www.pandora.com'})
#    Log(page)
#    Log(XML.StringFromElement(page))
#    return dir
   
 ####################################################################################################  
def Bookmarks(sender,webname):
    dir= MediaContainer(viewGroup="List")
    url='http://feeds.pandora.com/feeds/people/'+webname+'/favorites.xml'
    content=XML.ElementFromURL(url).xpath('//item',isHTML="False")
    
    for item in content:
        title = item.xpath('.//title')[0].text
        link=item.xpath('.//link')[0].text
        desc=item.xpath('.//description')[0].text
        thumb=item.xpath('./pandora:albumArtUrl',namespaces=NAMESPACES)[0].text
        Log(thumb)
        dir.Append(WebVideoItem(link,title=title,summary=desc,thumb=thumb))
    return dir
   
 #################################################################################################### 
def BookmarkedArtists(sender,webname):
    webname=webname
    dir= MediaContainer(viewGroup="List")
    url='http://feeds.pandora.com/feeds/people/'+webname+'/favoriteartists.xml'
    content=XML.ElementFromURL(url).xpath('//item',isHTML="False")
    Log(content)
    for item in content:
        title = item.xpath('.//title')[0].text
        link=item.xpath('.//link')[0].text
        desc=item.xpath('.//description')[0].text
        thumb=item.xpath('./pandora:artistPhotoUrl',namespaces=NAMESPACES)[0].text
        Log(thumb)
        dir.Append(WebVideoItem(link,title=title,summary=desc,thumb=thumb))
    return dir
####################################################################################################  
def ArtistSearch(sender,query):
    
    dir= MediaContainer(viewGroup="List")
    content=HTML.ElementFromURL("http://www.pandora.com/backstage?type=all&q="+query).xpath("//table[@id='tbl_artist_search_results']/tbody/tr")
    Log(content)
    for r in content:
        thumb = r.xpath("td/a/img")[0].get("src")
        a = r.xpath("td/a")
        href = a[1].get("href")
        id = "http://www.pandora.com/?search=" + href[href.rfind("/")+1:]
        title = a[1].text
        duration=""
        dir.Append(WebVideoItem(id, title, thumb=thumb))
    return dir
 ####################################################################################################  
def EmailSearch(sender,query):
    tmpwebname=pandoraWebNameFromEmail(query)
    dir= MediaContainer(viewGroup="List")
    if tmpwebname != "WEBNAME_LOOKUP_ERROR":
        url="http://feeds.pandora.com/feeds/people/" + tmpwebname  + "/stations.xml"
        content=XML.ElementFromURL(url).xpath('//item',isHTML="False")
        for item in content:
            title = item.xpath('.//title')[0].text
            link=item.xpath('.//link')[0].text
            desc=item.xpath('.//description')[0].text
            thumb=item.xpath('./pandora:stationAlbumArtImageUrl',namespaces=NAMESPACES)[0].text
            Log(thumb)
            dir.Append(WebVideoItem(link,title=title,summary=desc,thumb=thumb))
    else:
        dir.Append(Function(InputDirectoryItem(EmailSearch, "Invalid Email", "Search for User Stations by Email", "search.png")))
    return dir
 ####################################################################################################  
def WebnameSearch(sender,query):
    tmpwebname=query
    dir= MediaContainer(viewGroup="List")
    if tmpwebname != "WEBNAME_LOOKUP_ERROR":
        url="http://feeds.pandora.com/feeds/people/" + tmpwebname  + "/stations.xml"
        content=XML.ElementFromURL(url).xpath('//item',isHTML="False")
        for item in content:
            title = item.xpath('.//title')[0].text
            link=item.xpath('.//link')[0].text
            desc=item.xpath('.//description')[0].text
            thumb=item.xpath('./pandora:stationAlbumArtImageUrl',namespaces=NAMESPACES)[0].text
            Log(thumb)
            dir.Append(WebVideoItem(link,title=title,summary=desc,thumb=thumb))
    else:
        dir.Append(Function(InputDirectoryItem(EmailSearch, "Invalid Email", "Search for User Stations by Email", "search.png")))
    return dir

 ####################################################################################################  
def pandoraWebNameFromEmail(email):
  jsonUrl = "http://feeds.pandora.com/services/ajax/?method=authenticate.emailToWebname&email=" + email
  dict = JSON.ObjectFromURL(jsonUrl)
  if dict["stat"] == "ok":
    return dict["result"]["webname"]
  else:
    return "WEBNAME_LOOKUP_ERROR" #need to handle this error

####################################################################################################   
def populateFromFeed(url, dir):
  feed = RSS.Parse(url)
  for entry in feed["items"]:
    id = entry.link
    title = entry.description
    thumb = ""
    duration = ""
    dir.AppendItem(WebVideoItem(id, title, helptext, duration, thumb))
  return dir

####################################################################################################   
      