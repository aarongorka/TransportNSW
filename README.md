# TransportNSW
Python lib to access Transport NSW information.

## How to Use

### Get an API Key
An OpenData account and API key is required to request the data. More information on how to create the free account can be found here:
https://opendata.transport.nsw.gov.au/user-guide .

### Get the stop and line
The libary will expect at least stop id to request the next leave events. The easieste way to get the ID is using Google Maps and clicking on one of the bus, train or ferry stops. The information pane one the left will show the relevant stop ID.

Another source for the stop ID and line is  https://transportnsw.info/stops#/. It provides the option to search for a stop and the corresponding lines leaving from there. 

### Sample Code
The following example will request the next leave event for the bus route/line *199* from stop ID *209516*.

### API Documentation
The source API details can be found here: https://opendata.transport.nsw.gov.au/node/601/exploreapi

**Code:**
```python
from TransportNSW import TransportNSW
ptnsw1 = TransportNSW.TransportNSW()
journey = tnsw.get_departures('209516', '199', '', 'YOUR_API_KEY')
print(journey)
```
**Result:**
```
{'stop_id': '209516', 'route': '199', 'due': 4, 'delay': 0, 'real_time': 'n', 'destination': 'Palm Beach'}
```
* route: bus, train, ferry number
* due: minutes till next leave
* real_time: flag if the leave event has real_time information
* delay: delay in minutes from the scheduled leave time
* destination: end point of the route

Leaving the line field empty will return any bus/train/ferry leaving next from a given stop.
**Code:**
```python
journey = tnsw.get_departures('209516', '', '', 'YOUR_API_KEY')
```

Setting a destination will return all lines going there from the stop_id. Example for ferries leaving Balmain Warf towards Circular Quay 
**Code:**
```python
journey = tnsw.get_departures('10102008', '', 'Circular Quay', 'YOUR_API_KEY')
```

Alternatively, destination can be set to a stop ID if the name is ambiguous or difficult to match against. For example, Central can be named e.g. "Emu Plains via Central", "Hornsby via Central", etc. depending on the "route" (train line). This will show all departures from Chatswood to Central, regardless of route:
**Code:**
```python
journey = tnsw.get_departures('206710', '', '10101100', 'YOUR_API_KEY')
```

Optionally, methods of transport can also be ignored by passing a list of one or more methods (1 = train, 2 = metro, 4 = light rail, 5 = bus, 7 = coach, 9 = ferry, 11 = school bus). For example, to ignore buses going from Chatswood to Central:
**Code:**
```python
journey = tnsw.get_departures('206710', '', '10101100', 'YOUR_API_KEY', ["5"])
```

Optionally, a timeout (specified in seconds) can be passed if you're having issues with the default timeout of 10 seconds. For example, to set the timeout to 20 seconds:
**Code:**
```python
journey = tnsw.get_departures('206710', '', '10101100', 'YOUR_API_KEY', ["5"], 20)
```

### Errors
No leave event with wrong stop ID or not matching route.
```
{'stop_id': 'n/a', 'route': 'n/a', 'due': 'n/a', 'delay': 'n/a', 'real_time': 'n/a', destination: 'n/a'}
```
