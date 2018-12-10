import requests
import json
import pprint
import pandas as pd
import random
# from .models import Show
import spotipy
from spotipy import oauth2
from constants import *
import datetime 
import time
from constants import GenreHash
def getEventBrite(artist,location):
    
    show = Show.objects.filter(artist__contains=artist.lower(), city__contains=location.lower()).first() 
    if show is not None:
        results = {}
        results['name'] = show.display_artist
        results['address'] = show.location
        results['city'] = show.display_city
        results['zipcode']= show.zipcode
        results['start'] = show.start_time
        results['descript'] = show.description
    else:
        input_city = str(location)
        key = 'ZN6GPC6WGYLKI7IAZSUW' # Brooke's authentication key
        categories = 'music' 
        keywords = str(artist)

        results = {}
        response = requests.get("https://www.eventbriteapi.com/v3/events/search/?location.address="+ input_city +"&expand=organizer,venue,category&q="+keywords+"&categories=103&token=" + key)
        if (response.json()['events']==[]):
            return []
            
        results['name'] = response.json()['events'][0]['name']['text']
        results['address'] = response.json()['events'][0]['venue']['address']['address_1']
        results['city'] = response.json()['events'][0]['venue']['address']['city']
        results['zipcode'] = response.json()['events'][0]['venue']['address']['postal_code']
        results['start'] = response.json()['events'][0]['start']['local']
        results['descript'] = response.json()['events'][0]['description']['text']

        # this is how you create a new entrey in the "SHOW" database
        newShow = Show(artist = results['name'].lower(),city = results['city'].lower(),display_artist=results['name'],display_city=results['city'],start_time = results['start'],description=results['descript'],zipcode = results['zipcode'])
        newShow.save()
        
    return results


# def getTicketMaster(artist,location):
#     endpoint = "https://app.ticketmaster.com/discovery/v2/events.json?keyword="+artist+"&city="+location+"&apikey=O5RiEgAQZrTztqWOwSDjfvCB1jqwm1zj"
#     response = requests.get(endpoint).json()

#     if response['page']['totalElements']==0:
#         return []
#     results = {}
#     results['name']=response['_embedded']['events'][0]['name']
#     results['url']=response['_embedded']['events'][0]['url']
#     results['date']=response['_embedded']['events'][0]['dates']['start']['localDate']
#     results['start']=response['_embedded']['events'][0]['dates']['start']['localTime']
#     results['info']=response['_embedded']['events'][0]['info']

    

def getArtists(bearer):
    #gets users top 8 artists from spotify api, bearer represents access_token from oauth, and returns their image urls.
    url = "https://api.spotify.com/v1/me/top/artists"
    headers = {'content-type': 'application/json', 'Accept': 'application/json',"Authorization":"Authorization: Bearer "+bearer}
    r = requests.get(url, headers=headers,params={'limit':50})
    jsonn=r.json()
    artists=jsonn['items']
    artistLinks=[]
    # artistNames = [a['name'] for a in artists]
    artistNames = ['+'.join(a['name'].split()) for a in artists]
    genres = sum([a['genres'][0:2] for a in artists],[])
    artistImages= []
    for a in artists:
        try:
            img = a['images'][0]['url']
        except:
            img = ''
        artistImages.append(img)
    
    for i in range(len(artistNames)):
        # skURL='https://api.songkick.com/api/3.0/search/artists.json?apikey=zTrWUEWdDa8iaH8v&query='+artistNames[i]
        # rSK = requests.get(skURL)
        
        artistLinks.append(artists[i]['external_urls']['spotify'])    
    return artistNames[0:8],artistImages[0:8],artistLinks,genres

def similarArtists(artistIds,bearer):
    #not used now
    similarArtists = []
    similarArtistImg = []
    for idd in artistIds:
        url="https://api.spotify.com/v1/artists/"+str(idd)+"/related-artists"
        headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Authorization: Bearer "+bearer}

        r2 = requests.get(url,headers=headers,params={'limit':1})
        
        simArtists = r2.json()['artists']
        names = ['+'.join(a['name'].split()) for a in simArtists]
        
        similarArtists+=names
        
    return similarArtists[0:50]


def renderRecs(recArtistsImg,recArtistsNames): 
    #recArtistsImg is the link to the image source, recArtistsNames allows for the routing to the correct url
    allDiv = '<div class="row text-center text-lg-left">'

    for i in range(len(recArtistsImg)):
        
        allDiv += """
        <div class="col-lg-3 col-md-4 col-xs-6">
            <a href="/showinfo/%s/" class="d-block mb-4 h-100">
                <img class="img-fluid img-thumbnail" src="%s" alt="">
            </a>
        </div>
        """%(recArtistsNames[i],recArtistsImg[i])
    allDiv +="""
    </div>
    """
    return allDiv #formats the HTML to fit into the template


def getTicketMaster(genres,location):
    #hard coded for now
    results = {}
    urls = []
    foundArtists=[]
    genreIDstr =''
    subgenre = ''
    for genre in genres:
        if genre == 'pop':
            subgenre = '&subgenreid=KZazBEonSMnZfZ7v6F1'
        if genre in GenreHash:
            genreIDstr+=(GenreHash[genre]+',')
      

    genreIDstr = genreIDstr[0:len(genreIDstr)-1]+subgenre
    #ticketmaster endpoint to find 25 shows in area (hard coded for boston right now) based on genreID (hard coded for dance/electronic right now)
    url = 'https://app.ticketmaster.com/discovery/v2/events.json?size=28&genreId='+genreIDstr+'&segmentId=KZFzniwnSyZfZ7v7nJ&city=' +location+'&apikey=O5RiEgAQZrTztqWOwSDjfvCB1jqwm1zj&radius=100'
    r = requests.get(url).json()
    if (r['page']['totalElements']==0):
        return None
    for i in range(len(r['_embedded']['events'])): #iterate over all the 25 returned shows and parse thru the json accordingly. 
        payload = {}

        payload['eventname'] = r['_embedded']['events'][i]['name']#r['_embedded']['events'][0]['name']
        curArtist = ('+'.join(payload['eventname'].split(' '))).replace('/','')

        if curArtist in results:
            continue

        foundArtists.append( ('+'.join(payload['eventname'].split(' '))).replace('/',''))
        try:
            payload['url'] =r['_embedded']['events'][i]['url']#r['_embedded']['events'][0]['url']
        except:
            pass
        try:
            payload['venueAddr'] = r['_embedded']['events'][i]['_embedded']['venues'][0]['address']['line1']
        except:
            pass
        try:
            payload['venueName'] =  r['_embedded']['events'][i]['_embedded']['venues'][0]['name']
        except:
            pass
        try:
            payload['venueLat'] = r['_embedded']['events'][i]['_embedded']['venues'][0]['location']['latitude']
        except:
            pass
        try:
            payload['venueLng'] = r['_embedded']['events'][i]['_embedded']['venues'][0]['location']['longitude']
        except:
            pass
        try:
            iMax = 0 
            finalI = -1
            for j in range(len(r['_embedded']['events'][i]['images'])):
                nMax = r['_embedded']['events'][i]['images'][j]['height']*r['_embedded']['events'][i]['images'][j]['width']
                if nMax > iMax:
                    iMax = nMax
                    finalI = j
            payload['imgUrl'] = r['_embedded']['events'][i]['images'][finalI]['url']
            urls.append(payload['imgUrl'])
        except:
            urls.append('')
        
        try:
            date=datetime.datetime.strptime(r['_embedded']['events'][i]['dates']['start']['localDate']+'T'+r['_embedded']['events'][0]['dates']['start']['localTime'], '%Y-%m-%dT%H:%M:%S')
            payload['datetime'] =datetime.datetime.strftime(date, '%m/%d/%Y at %H:%M')
        except:
            pass
        try:
            payload['info']=r['_embedded']['events'][i]['info']
        except:
            pass

        #this is hard to visualize - the results dictionary is a dictionary of dictionaries (yikes), but allows data to be upfront
        #loaded rather than having to call the api again once we click a page. so for example if a kanye show is found then
        # results['Kanye'] holds a dictionary of all the information defined above.
        results[curArtist] = payload

    return results,urls,foundArtists #urls and found artists are arrays holding links and names, which allows for html rendering and URL routing


def locationdropdown(location):
    locStr = """
        <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Current Location Set To: <b>"""
    locStr += location
    locStr += """ </b></a>
            <div class="dropdown-menu dropdown-menu-right" aria-labelledby="navbarDropdown">
                <form class="px-4 py-3"  method="post">
                """
    locStr2= """
                    <div class="form-group">
                        <input id="autocomplete" name = "autocomplete" placeholder="Enter new location" type="text" />

                    </div>    
                    <button type="submit" id="find-show" class="btn btn-sm btn-dark btn-block float-right">Set Location</button>

                </form>
            </div>
        </li>
    """

    return locStr,locStr2


def GetSpotifyImage(idd,bearer):
   
    url="https://api.spotify.com/v1/users/"+idd
    headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Authorization: Bearer "+bearer}

    r = requests.get(url,headers=headers).json()
    print(r)
    imgURL = r['images'][0]['url']
    return imgURL
