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
        
        # try:
        location = request.POST.get('autocomplete')
        newLoc='+'.join(location.split(',')[-3].split())
        # except:
        #     return render(request,'setlocation.html',{'default':'Invalid location. Please select from autocomplete.'})

            # return(request,'index.html',request.session['HomePayload'])

        access_token = request.session['access_token']
        artistNames,artistUrls,artistExtLinks, genres, imgURL = services.getArtists(access_token,request.user.spotifyid) #gets top 8 artists in spotify
        request.session['ProfileImg'] = imgURL
        try:
            MySimilarArtistEvents,SimArtistsImgs,SimFoundNames = services.getTicketMaster(genres,newLoc) #gets the ticketmaster suggested artists
            divs = services.renderRecs(SimArtistsImgs,SimFoundNames)
            request.session['Concerts']=MySimilarArtistEvents
        except: 
            divs = '<h2 class="my-4 text-center text-lg-left" style=padding-right: 20px;">No shows found given your location/genre preferences.</h1>'
        
        
        
        locStr, locStr2 = services.locationdropdown(location)#location.split(',')[-3].strip())
        print(locStr)
        print(locStr2)
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

    elif 'HomePayload' not in request.session:
        
        access_token = request.session['access_token']
        artistNames,artistUrls,artistExtLinks, genres, imgURL = services.getArtists(access_token,request.user.spotifyid) #gets top 8 artists in spotify
        request.session['ProfileImg'] = imgURL

        
        try:
            MySimilarArtistEvents,SimArtistsImgs,SimFoundNames = services.getTicketMaster(genres,request.user.location.split(',')[-3].strip()) #gets the ticketmaster suggested artists
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
    
        try:
            location = request.session['PrefLoc']
            locStr, locStr2 = services.locationdropdown(location)
            
            payload['location'] = location
            payload['locationdropdown1'] = locStr
            payload['locationdropdown2'] = locStr2
            request.session['HomePayload']['location'] = location
            request.session['locationdropdown1'] = locStr
            request.session['locationdropdown2'] = locStr2
        except:
            pass
        
    return render(request,'index.html',payload)

def login_view(request):

    if (request.user.is_authenticated):
        return redirect('/home/')

    auth_url = sp_oauth.get_authorize_url()
    payload = {'auth_url':auth_url}
    access_token = "" 
    code = sp_oauth.parse_response_code(request.get_full_path())
    
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
            return redirect('/newuser/')

    else:
        return render(request,'login.html',payload)



def set_location_view(request):
    if (request.method == 'POST'):
        # so they pressed submit on their location
        location = request.POST.get('autocomplete')
        
        
        
        user = CustomUser.objects.get(username=request.user.username,spotifyid=request.user.spotifyid)
        user.location = location#location.split(',')[-3].strip()
        user.save()
        # request.session['HomePayload']['location'] = location
        request.session['PrefLoc'] = location
        # return redirect('/home/')
        return redirect('/home/')
        # return render(request,'index.html',request.session['HomePayload'])

    return render(request,'setlocation.html',{'default':'Enter default location.'})


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
    # try:
    #     print("trying")
    #     img = services.GetSpotifyImage(request.user.spotifyid,request.session['access_token'])
    # except:
    #     img = ''
    # print(img)
    img = request.session['ProfileImg']
    curUser = request.user
    payload={'users':curUser.username,'user':curUser.username,'location':request.session['HomePayload']['location'],'spotifyid':'https://open.spotify.com/user/'+str(curUser.spotifyid),'IMG':img}
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