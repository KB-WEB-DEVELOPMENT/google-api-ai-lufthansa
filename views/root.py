# app/views/root.py
# -*- coding: utf-8 -*-

from flask import (
    Blueprint,
    redirect,
    render_template,
    session,
    url_for,
)

import oauth2 as oauth
import urllib

import config

# parse_qsl moved to urlparse module in v2.6
try:
    from urlparse import parse_qsl
except:
    from cgi import parse_qsl

app = Blueprint('root', __name__)

oauth_consumer = oauth.Consumer(key = config.object.LUFTHANSA_OAUTH_CONSUMER_KEY, secret = config.object.LUFTHANSA_OAUTH_CONSUMER_SECRET,)
oauth_client = oauth.Client(oauth_consumer)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    #print("Request:")
    #print(json.dumps(req, indent=4))

    res = process_request(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def get_departure_iata_code(req):
	"""Retrieve the departure airport IATA code based on the city entered by the user."""

    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("departure-city")

	try:
	  r = requests.get('https://api-test.lufthansa.com/airports.json')
	except Exception  as e:
	  print(e, type(e))
	
	for attrs in r.json()['city']:
	    if attrs['city'] == city:			
	      departure_iata = attrs['code']
	      break
	    else:
	      print('Nothing found!')
	
	return departure_iata
	
def get_arrival_iata_code(req):
	"""Retrieve the arrival airport IATA code based on the city entered by the user."""

    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("arrival-city")
	try:
	  r = requests.get('https://api-test.lufthansa.com/airports.json')
	  except Exception  as e:
	  print(e, type(e))
		
	for attrs in r.json()['city']:
	    if attrs['city'] == city: arrival_iata = attrs['code']
	      break
	    else:
	      print('Nothing found!')
	
	return arrival_iata	
		
def process_request(req):
	"""method processing the user query, calls various methods within root.py"""
    if req.get("result").get("action") != "search.bestfares":
        return {}
    baseurl = "https://api-test.lufthansa.com/v1/Offers/"
    best_fares_query = make_lufthansa_best_fares_query(req)
    if best_fares_query is None:
        return {}
     else:		
      login()		
      best_fares_url = baseurl + urllib.urlencode({'q': best_fares_query}) + "&format=json"
      result = urllib.urlopen(best_fares_url).read()
      data = json.loads(result)
      res = make_webhook_result(data)
		
     return res

def make_lufthansa_best_fares_query(req):
	"""the method returns the query used by Luftansa API to return the information searched for"""
	result  = req.get("result")		
	parameters = result.get("parameters")		
	travel-date = parameters.get("travel-date")
	
	if travel-date is None: return None
	
	origin = get_departure_iata_code(req)
	if origin is None:
           return None
		
	cabinclass = parameters.get("cabinclasscode")
    
        if cabinclass is None:
            return None
	
	trip_duration_info = parameters.get("trip-duration") 
	trip_duration = trip_duration_info["amount"]
	
	if trip_duration is None:
           return None
		
	destination = get_arrival_iata_code(req)
	
	if destination is None:
           return None
	
	range = parameters.get("best-fares-range")
	
	if range is None:
           return None
		
	#Example of query required: fares/bestfares?catalogues=LH&travel-date=2016-12-29&origin=FRA&cabin-class=economy&trip-duration=5&country=DE&destination=JNB&range=byday	
	query = "fares/bestfares?catalogues=LH&travel-date=" + travel-date + "&origin=" + origin + "&cabin-class=" + cabinclass + "&trip-duration=" + str(trip_duration) + "&country=DE&destination=" + destination + "&range=" + range	
	   return query
	
@app.route('/webook/login', methods = [ 'GET', 'POST' ])
def login():
	"""this GET method requests a temporary token and sends it to the method auth_authorized() which will check access to Lufthansa API services"""
    res, content = oauth_client.request(
        'https://api.lufthansa.com/v1/oauth/token?%s'
        % urllib.urlencode({
             'oauth_callback': 'http://localhost:5000' + url_for('root.oauth_authorized')
        }).replace('+', '%20'),
        'GET',
    )
    if res['status'] != '200':
        raise Exception(
            "Invalid response %s: %s" % (res['status'], content)
        )

    request_token = dict(parse_qsl(content))
    session['request_token'] = request_token
    url = 'https://api.lufthansa.com/v1/oauth/authorize?%s' % (
        urllib.urlencode({
             'oauth_token': request_token['oauth_token'],
             'oauth_callback': 'http://localhost:5000' + url_for('root.oauth_authorized')
        }).replace('+', '%20'),
    )
	return redirect(url)

@app.route('/webhook/oauth_authorized')
def oauth_authorized():
	"""this POST method both checks the token sent by the method login() and posts a error response if access to Lufthansa API Services is denied"""
    request_token = session['request_token']
    token = oauth.Token(
        request_token['oauth_token'],
        request_token['oauth_token_secret']
    )
    client = oauth.Client(oauth_consumer, token)
    res, content = client.request(
        'https://api.lufthansa.com/v1/oauth/access_token',
        'POST'
    )
    if res['status'] != '200':
        raise Exception(
            "Invalid response %s: %s" % (res['status'], content)
        )
			
	 # the  token has been validated and accepted, back to function 	
	 # access_token = dict(parse_qsl(content)) NOT NEEDED

def make_webhook_result(data):
	""" This method prepares how the results of the query search should be displayed in Slack and Facebook Messenger Bot"""
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    # print(json.dumps(item, indent=4))
	offers_number_string = result.json()["BestFaresResponse"]["AirShoppingRS"]["OffersGroup"]["TotalOfferQuantity"]
	
	offers_number_int = int(offers_number_string)
	
	if offers_number_string = "0":
		speech = "\nSorry, your search did not yield any best fares OFFERS."
	else:	
		speech ="\nTotal number of best fares offers found: " + offers_number_string
		
		count = 1
		for infos_total_price in json()["BestFaresResponse"]:
		   for single_offer_total_price["TotalPrice"]["DetailCurrencyPrice"]["Total"] in infos_total_price["AirShoppingRS"]["OffersGroup"]["AirlineOffers"]["AirlineOffer"]:
		       speech += "\n Offer # " + str(count) + " :" + single_offer_total_price["TotalPrice"]["DetailCurrencyPrice"]["Total"].get("#text") + " EUR"  
		       count += 1
		
		speech  += "\nFLIGHT SEGMENTS LIST FOR ALL OFFERS:  "
		
		for flight_segments in json()["BestFaresResponse"]:
		    for departure_info["Departure"] in flight_segments["AirShoppingRS"]["DataLists"]["FlightSegmentList"]["FlightSegment"]:
		    for arrival_info["Arrival"] in flight_segments["AirShoppingRS"]["DataLists"]["FlightSegmentList"]["FlightSegment"]:
		    for marketing_carrier_info["MarketingCarrier"] in flight_segments["AirShoppingRS"]["DataLists"]["FlightSegmentList"]["FlightSegment"]:
				
		      speech += "\n\nDEPARTURE DATE: " + departure_info["Departure"].get("Date")
		      speech += "\nDEPARTURE AIRPORT CODE:   " +  departure_info["Departure"].get("AirportCode")
		      speech += "\nARRIVAL AIRPORT CODE:   " + arrival_info["Arrival"].get("AirportCode")
		      speech += "\nAIRLINE CARRIER ID: " +  marketing_carrier_info["MarketingCarrier"].get("AirlineID")
		      speech += "\nFLIGHT NUMBER: " +  marketing_carrier_info["MarketingCarrier"].get("FlightNumber")

    #print("Response:")
    print(speech)

    slack_message = {
        "text": speech,
		"title": "YOUR LUFTHANSA BEST FARES QUERY"
		"thumb_url": "URL_PATH_TO_LUFTHANSA_LOGO"
    }

    facebook_message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": {
                        "subtitle": speech,
			"image_url": "URL_PATH_TO_LUFTHANSA_LOGO"
                }              
            }
        }
    }

    #print(json.dumps(slack_message))

    return {
        "speech": speech,
        "displayText": speech,
        "data": {"slack": slack_message, "facebook": facebook_message},
        "contextOut": [],
        "source": "apiai-lufthansa-bestfares-webhook"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=False, port=port, host='0.0.0.0')
