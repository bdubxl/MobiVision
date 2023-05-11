from django.shortcuts import render
from .models import Trips, Events

# Create your views here.
def home(request):
	trips = Trips.objects.all() # Query all trips from database
	if request.method == 'POST': #Display Events from selected trip
		tripd = request.POST.get('tripdate') # Depending on button press find data returned from form with tripdate value
		events = Events.objects.filter(tripdate=tripd) #Query all events from selected date

		context = {'events': events, 'tripdate' : tripd}
		return render(request, 'events.html', context)
	else: # Display all trips
		context = {'trips': trips}
		return render(request, 'index.html', context)
