# pages/views.py
from django.views.generic import TemplateView
from spotipy import oauth2
from django.shortcuts import render
import spotipy
from users.models import CustomUser
from . import services
import requests
from spotipy.oauth2 import SpotifyClientCredentials
import json
from django.core import serializers
from django.shortcuts import redirect
from django.contrib.auth import login, logout , authenticate, get_user


SPOTIPY_CLIENT_ID = '78f584e7e40c41528f1601d32a27d15c'
SPOTIPY_CLIENT_SECRET = 'b284e94507c34fc6b7f17ac0f0fbaca7'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8000/login/'
SCOPE = 'user-top-read'
CACHE = '.spotipyoauthcache'
sp_oauth = oauth2.SpotifyOAuth( SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET,SPOTIPY_REDIRECT_URI,scope=SCOPE,cache_path=CACHE )
client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)


def home_view(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    if request.method=='POST':

        try:
            location = request.POST.get('autocomplete')
            newLoc='+'.join(location.split(',')[-3].split())

        except:
            return(request,'index.html',request.session['HomePayload'])

        access_token = request.session['access_token']
        artistNames,artistUrls,artistExtLinks, genres = services.getArtists(access_token) #gets top 8 artists in spotify

        try:
            MySimilarArtistEvents,SimArtistsImgs,SimFoundNames = services.getTicketMaster(genres,newLoc) #gets the ticketmaster suggested artists
            divs = services.renderRecs(SimArtistsImgs,SimFoundNames)
            request.session['Concerts']=MySimilarArtistEvents
        except: 
            divs = '<h2 class="my-4 text-center text-lg-left" style=padding-right: 20px;">No shows found given your location/genre preferences.</h1>'
        
        
        
        locStr, locStr2 = services.locationdropdown(location.split(',')[-3].strip())

        payload = {       
            'artistimgs': artistUrls,
            'artisturls':artistExtLinks,
            'user':request.user.username,
            'location':location.split(',')[-3].strip(),
            'divs':divs,
            'locationdropdown1':locStr,
            'locationdropdown2':locStr2
        }
        del request.session['HomePayload']
        request.session['HomePayload'] = payload

    if 'HomePayload' not in request.session:
        access_token = request.session['access_token']
        artistNames,artistUrls,artistExtLinks, genres = services.getArtists(access_token) #gets top 8 artists in spotify
        try:
            MySimilarArtistEvents,SimArtistsImgs,SimFoundNames = services.getTicketMaster(genres,request.user.location) #gets the ticketmaster suggested artists
            divs = services.renderRecs(SimArtistsImgs,SimFoundNames)
            request.session['Concerts']=MySimilarArtistEvents
        except:
            divs = '<h2 class="my-4 text-center text-lg-left">No shows found given your location/genre preferences.</h1>'

        locStr, locStr2 = services.locationdropdown(request.user.location)
        payload = {   
            'artistimgs': artistUrls,
            'artisturls':artistExtLinks,
            'user':request.user.username,
            'location':request.user.location,
            'locationdropdown1':locStr,
            'locationdropdown2':locStr2,
            'divs':divs
        }
        request.session['HomePayload'] = payload
    else:
        payload = request.session['HomePayload']

    return render(request,'index.html',payload)

def login_view(request):

    if (request.user.is_authenticated):
        return redirect('/home/')

    auth_url = sp_oauth.get_authorize_url()
    payload = {'auth_url':auth_url}
    access_token = "" 
    code = sp_oauth.parse_response_code(request.get_full_path())
    if request.method == 'POST':
        request.session['PrefLoc'] = location = request.POST.get('preferredCity')

    if code:
        token_info = sp_oauth.get_access_token(code)
        access_token = token_info['access_token']
        request.session['access_token'] = access_token
        sp = spotipy.Spotify(auth=access_token,client_credentials_manager=client_credentials_manager)
        user = sp.current_user()
        
        # dbUser =CustomUser.objects.filter( spotifyid__contains=user['id'] ).first() 
        dbUser = authenticate(spotifyid=str(user['id']))
        if dbUser is not None:
            login(request,dbUser,backend='users.backends.SpotifyAuthBackEnd')
        
            return redirect('/home/')
      
        elif dbUser is None:
            print("didn't find it")
            newUser = CustomUser(username = user['display_name'],location = 'Boston',spotifyid=user['id'])
            newUser.save()
            login(request,newUser,backend='users.backends.SpotifyAuthBackEnd')
            return redirect('/home/')

    else:
        return render(request,'login.html',payload)



def set_location_view(request):
    if (request.method == 'POST'):
        # so they pressed submit on their location
        location = request.POST.get('autocomplete')
        print(location)
        user = CustomUser.objects.get(username=request.user.username,spotifyid=request.user.spotifyid)
        user.location = location.split(',')[-3].strip()
        user.save()
        request.session['PrefLoc'] = location
        # return redirect('/home/')
        return redirect('/success/')

    return render(request,'setlocation.html')


# def login_view(request):

    

    # auth_url = sp_oauth.get_authorize_url()
    # payload = {'auth_url':auth_url}
    
    # access_token = ""

    # # token_info = sp_oauth.get_cached_token()

    # # if token_info:
    # #     print("Found cached token!")
    # #     access_token = token_info['access_token']

    # if 'CurrentUser' in request.session:
    #     pass
      
    # code = sp_oauth.parse_response_code(request.get_full_path())
    # if code:
    #     # print("Found Spotify auth code in Request URL! Trying to get valid access token...")
    #     token_info = sp_oauth.get_access_token(code)
    #     access_token = token_info['access_token']
    #     sp = spotipy.Spotify(auth=access_token,client_credentials_manager=client_credentials_manager)
    #     user = sp.current_user()
        
    #     dbUser =CustomUser.objects.filter( spotifyid__contains=user['id'] ).first() 
    #     # dbUser = authenticate(spotifyid=str(user['id']))
    #     # print(dbUser)
    #     if dbUser is not None:
    #         login(request,dbUser,backend='users.backends.SpotifyAuthBackEnd')
        
    #     # print(request.user.spotifyid)
    #     #LOTS OF COMMENTED STUFF sorry it represents how i made a ruf attempt at searching every similar artist
    #     artistNames,artistUrls,artistExtLinks, genres = services.getArtists(access_token) #gets top 8 artists in spotify

    #     # MyTopArtists, MyTopArtistsId = services.getArtists(access_token)
    #     # print(MyTopArtists)
    #     # print()
    #     # print(MyTopArtistsId)
    #     # MyTopArtistsEvents, TopArtistImgs, FoundTopNames = services.getTicketMaster(MyTopArtists) #returns dict of dicts -> each key is an artist, each value is payload
    #     # print(TopArtistImgs)
    #     # print(MyTopArtistsEvents)
    #     # if requests.session['Concerts'] is None:
    #     #     requests.session['Concerts'] = MyTopArtistsEvents
    #     # else:
    #     # requests.session['Concerts'].update(MyTopArtistsEvents)


    #     # SimilarArtistNames = services.similarArtists(MyTopArtistsId,access_token)
    #     MySimilarArtistEvents,SimArtistsImgs,SimFoundNames = services.getTicketMaster(genres) #gets the ticketmaster suggested artists
    #     #will eventualy accept the genreIDs to make dynamic.
    #     # requests.session['SimilarArtistConcerts']=MySimilarArtistEvents
    #     divs = services.renderRecs(SimArtistsImgs,SimFoundNames)
        
    #     # MyTopArtistsEvents.update(MySimilarArtistEvents)

    #     #so the request.session allows data to be accessed between views per session. I store all the events in the 'Concerts' field
    #     #that i made inthe session, so when i access the /showinfo/ARTIST/ url, it will go in to the request.session['Concerts'][ARTIST] to get 
    #     #the appropriate payload depending on the artist. saves a lot of loading time. kinda like a caching system to hold the data per session.
    
    #     request.session['Concerts']=MySimilarArtistEvents


    #     if dbUser is None:
    #         print("didn't find it")
    #         newUser = CustomUser(username = user['display_name'],location = 'Boston',spotifyid=user['id'])
    #         newUser.save()
    #         login(request,newUser,backend='users.backends.SpotifyAuthBackEnd')
            

    #         #RIGHT NOW HARD CODED TO ASSUME 8 TOP ARTISTS - probably need to make this more general, in the event the user doesn't
    #         #have 8 top artists? need to investigate what spotify api returns in that event.
    #         payload = {
                
    #             'artist1img':artistUrls[0],
    #             'artist2img':artistUrls[1],
    #             'artist3img':artistUrls[2],
    #             'artist4img':artistUrls[3],
    #             'artist5img':artistUrls[4],
    #             'artist6img':artistUrls[5],
    #             'artist7img':artistUrls[6],
    #             'artist8img':artistUrls[7],

    #             'topURL1':artistExtLinks[0],
    #             'topURL2':artistExtLinks[1],
    #             'topURL3':artistExtLinks[2],
    #             'topURL4':artistExtLinks[3],
    #             'topURL5':artistExtLinks[4],
    #             'topURL6':artistExtLinks[5],
    #             'topURL7':artistExtLinks[6],
    #             'topURL8':artistExtLinks[7],

    #             'user':newUser.username,
    #             'location':newUser.location,
    #             'divs':divs
    #         }
    #         request.session['CurrentUser']=json.dumps(json.loads(serializers.serialize('json', [ newUser, ]))[0])
    #         return render(request,'index.html',payload)
    #     else:

    #         payload = {
                
    #             'artist1img':artistUrls[0],
    #             'artist2img':artistUrls[1],
    #             'artist3img':artistUrls[2],
    #             'artist4img':artistUrls[3],
    #             'artist5img':artistUrls[4],
    #             'artist6img':artistUrls[5],
    #             'artist7img':artistUrls[6],
    #             'artist8img':artistUrls[7],
    #             'topURL1':artistExtLinks[0],
    #             'topURL2':artistExtLinks[1],
    #             'topURL3':artistExtLinks[2],
    #             'topURL4':artistExtLinks[3],
    #             'topURL5':artistExtLinks[4],
    #             'topURL6':artistExtLinks[5],
    #             'topURL7':artistExtLinks[6],
    #             'topURL8':artistExtLinks[7],
    #             'user':dbUser.username,
    #             'location':dbUser.location,
    #             'divs':divs
    #         }

    #         # print("found dbUser")
    #         # return render(request,'success.html',{'success':dbUser.spotifyid})
    #         # request.session['user']=user
    #         request.session['CurrentUser']=json.dumps(json.loads(serializers.serialize('json', [ dbUser, ]))[0])

    #         # print(request.session['CurrentUser'])
    #         return render(request,'index.html',payload)


    # if access_token:
    #     # print("Access token available! Trying to get user information...")
    #     sp = spotipy.Spotify(access_token)
    #     results = sp.current_user()
    #     # print(results)
    #     return render(request,'success.html')
    
    
    # else:
    #     return render(request,'login.html',payload)

def success(request):
    # payload = {'success':request.session['user']}
    if request.user.is_authenticated:
        return render(request,'success.html',{'success':request.session['PrefLoc']})
    return render(request,'success.html',{'success':request.session['PrefLoc']})


def showinfo(request,artist):
    
    payload = request.session['Concerts'][artist] #so when i click the show thumbnail - it routes me to something like /showinfo/Drake/
    #then in here artist=Drake, and it will look in my session cache to find the payload for drake, and render the showinfo.html accordingly.
    # curUser = json.loads(request.session['CurrentUser'])
    payload['user']=request.user.username
    payload['location']=request.session['HomePayload']['location']
    return render(request,'showinfo.html',payload)

def profile(request):

    curUser = request.user
    payload={'users':curUser.username,'user':curUser.username,'location':request.session['HomePayload']['location'],'spotifyid':'https://open.spotify.com/user/'+str(curUser.spotifyid)}
    return render(request,'profile.html',payload)

def logout_view(request):
    session_keys = list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    logout(request)
    response = redirect('/login/')
    return response

def redirectit(request):
    return redirect('/login/')