"""A module to query Transport NSW (Australia) departure times."""
from datetime import datetime, timezone
import requests.exceptions
import requests
import logging

ATTR_STOP_ID = 'stop_id'
ATTR_ROUTE = 'route'
ATTR_DUE_IN = 'due'
ATTR_DELAY = 'delay'
ATTR_REALTIME = 'real_time'
ATTR_DESTINATION = 'destination'
ATTR_MODE = 'mode'

logger = logging.getLogger(__name__)

class TransportNSW(object):
    """The Class for handling the data retrieval."""

    # The application requires an API key. You can register for
    # free on the service NSW website for it.

    def __init__(self, api_key, timeout=10):
        """Initialize required parameters."""
        self.api_key = api_key
        self.timeout = timeout

    def get_departures(self, stop_id, route=None, destination=None, excluded_means=[]):
        """Get data about a departure from Transport NSW."""

        # Default return value
        info = {
            ATTR_STOP_ID: 'n/a',
            ATTR_ROUTE: 'n/a',
            ATTR_DUE_IN: 'n/a',
            ATTR_DELAY: 'n/a',
            ATTR_REALTIME: 'n/a',
            ATTR_DESTINATION: 'n/a',
            ATTR_MODE: 'n/a'
            }

        # Build the URL including the STOP_ID and the API key
        url = 'https://api.transport.nsw.gov.au/v1/tp/departure_mon'
        auth = 'apikey ' + self.api_key
        headers = {'Accept': 'application/json', 'Authorization': auth}

        if len(excluded_means) > 0:
            params_excluded_means = {
                "excludedMeans": "checkbox",
                **{"exclMOT_{}".format(x): 1 for x in excluded_means}
            }
        else:
            params_excluded_means = {}

        params = {
            "outputFormat": "rapidJSON",
            "coordOutputFormat": "EPSG:4326",
            "mode": "direct",
            "type_dm": "stop",
            "name_dm": stop_id,
            "nameKey_dm": "$USEPOINT$",
            "departureMonitorMacro": "true",
            "TfNSWDM": "true",
            "version": "10.2.1.42",
            **params_excluded_means,
        }

        # Send the query and return error if something goes wrong
        # Otherwise store the response
        try:
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        except:
            logger.error("Network or Timeout error")
            return info

        # If there is no valid request (e.g. http code 200)
        # log error and return empty object
        if response.status_code != 200:
            logger.warning("Error with the request sent; check api key")
            return info

        # Parse the result as a JSON object
        result = response.json()

        # If there is no stop events for the query
        # log an error and return empty object
        try:
            result['stopEvents']
        except KeyError:
            logger.warning("No stop events for this query")
            return info

        # Set variables
        maxresults = 1
        monitor = []
        if destination != '':
            for i in range(len(result['stopEvents'])):
                result_destination = result['stopEvents'][i]['transportation']['destination']['name']
                if result_destination == destination:
                    event = self.parseEvent(result, i)
                    if event != None:
                        monitor.append(event)
                    if len(monitor) >= maxresults:
                        # We found enough results, lets stop
                        break
        elif route != '':
            # Find the next stop events for a specific route
            for i in range(len(result['stopEvents'])):
                number = result['stopEvents'][i]['transportation']['number']
                if number == route:
                    event = self.parseEvent(result, i)
                    if event != None:
                        monitor.append(event)
                    if len(monitor) >= maxresults:
                        # We found enough results, lets stop
                        break
        else:
            # No route defined, find any route leaving next
            for i in range(0, maxresults):
                event = parseEvent(result, i)
                if event != None:
                    monitor.append(event)

        # If the monitor object is defined, updated the return object with core infos
        if monitor:
            info = {
                ATTR_STOP_ID: stop_id,
                ATTR_ROUTE: monitor[0][0],
                ATTR_DUE_IN: monitor[0][1],
                ATTR_DELAY: monitor[0][2],
                ATTR_REALTIME: monitor[0][5],
                ATTR_DESTINATION: monitor[0][6],
                ATTR_MODE: monitor[0][7]
                }
        return info

    def parseEvent(self, result, i):
        """Parse the current event and extract data."""
        fmt = '%Y-%m-%dT%H:%M:%SZ'
        due = 0
        delay = 0
        real_time = 'n'
        number = result['stopEvents'][i]['transportation']['number']
        planned = datetime.strptime(result['stopEvents'][i]
            ['departureTimePlanned'], fmt)
        destination = result['stopEvents'][i]['transportation']['destination']['name']
        mode = self.get_mode(result['stopEvents'][i]['transportation']['product']['class'])
        # Unless realtime data is available the plannned is equal to estimated time
        estimated = planned
        if 'isRealtimeControlled' in result['stopEvents'][i]:
            real_time = 'y'
            estimated = datetime.strptime(result['stopEvents'][i]
                ['departureTimeEstimated'], fmt)
        # Only deal with future leave times
        if estimated > datetime.utcnow():
            due = self.get_due(estimated)
            delay = self.get_delay(planned, estimated)
            return[
                number,
                due,
                delay,
                planned,
                estimated,
                real_time,
                destination,
                mode
                ]
        else:
            return None

    def get_due(self, estimated):
        """Min till next leave event."""
        due = 0
        due = round((estimated - datetime.utcnow()).seconds / 60)
        return due

    def get_delay(self, planned, estimated):
        """Min of delay on planned departure."""
        delay = 0                   # default is no delay
        if estimated >= planned:    # there is a delay
            delay = round((estimated - planned).seconds / 60)
        else:                       # leaving earlier
            delay = round((planned - estimated).seconds / 60) * -1
        return delay

    def get_mode(self, iconId):
        """Map the iconId to proper modes string."""
        modes = {
            1: "Train",
            4: "Lightrail",
            5: "Bus",
            7: "Coach",
            9: "Ferry",
            11: "Schoolbus"
        }
        return modes.get(iconId, None)


    def get_trip(self, origin_stop_id, destination_stop_id, excluded_means=[]):
        """Get data about a trip from Transport NSW."""

        # Default return value
        info = {
            ATTR_STOP_ID: 'n/a',
            ATTR_ROUTE: 'n/a',
            ATTR_DUE_IN: 'n/a',
            ATTR_DELAY: 'n/a',
            ATTR_REALTIME: 'n/a',
            ATTR_DESTINATION: 'n/a',
            ATTR_MODE: 'n/a'
            }

        # Build the URL including the STOP_ID and the API key
        url = 'https://api.transport.nsw.gov.au/v1/tp/trip'
        auth = 'apikey ' + self.api_key
        headers = {'Accept': 'application/json', 'Authorization': auth}

        if len(excluded_means) > 0:
            params_excluded_means = {
                "excludedMeans": "checkbox",
                **{"exclMOT_{}".format(x): 1 for x in excluded_means}
            }
        else:
            params_excluded_means = {}

        params = {
            "outputFormat": "rapidJSON",
            "coordOutputFormat": "EPSG:4326",
            "depArrMacro": "dep",
            "type_origin": "any",
            "name_origin": origin_stop_id,
            "type_destination": "any",
            "name_destination": destination_stop_id,
            "calcNumberOfTrips": 1,
            **params_excluded_means,
        }

        # Send the query and return error if something goes wrong
        # Otherwise store the response
        try:
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        except:
            logger.warning("Network or Timeout error")
            return info

        # If there is no valid request (e.g. http code 200)
        # log error and return empty object
        if response.status_code != 200:
            logger.warning("Error with the request sent; check api key")
            return info

        # Parse the result as a JSON object
        result = response.json()

        # If there are no journies for the query
        # log an error and return empty object
        try:
            journeys = result['journeys']
        except KeyError:
            logger.warning("No journeys for this query")
            return info

        # Set variables
        maxresults = 1
        monitor = []
        for journey in journeys:
            origin = journey["legs"][0]["origin"]
            time_estimated = datetime.fromisoformat(origin.get("departureTimeEstimated") or origin.get("departureTimePlanned") or origin.get("arrivalTimeEstimated") or origin.get("arrivalTimePlanned"))
            time_planned = datetime.fromisoformat(origin.get("departureTimePlanned") or origin.get("arrivalTimePlanned"))
            time_now = datetime.now(timezone.utc)

            if journey["legs"][0].get("isRealtimeControlled") is not None:
                info[ATTR_REALTIME] = journey["legs"][0]["isRealtimeControlled"]

            info[ATTR_STOP_ID] = origin_stop_id
            info[ATTR_ROUTE] = ",".join([leg["transportation"]["name"] for leg in journey["legs"]])
            info[ATTR_DUE_IN] = round((time_estimated - time_now).seconds / 60)
            info[ATTR_DELAY] = round((time_estimated - time_planned).seconds / 60)
            info[ATTR_DESTINATION] = destination_stop_id
            info[ATTR_MODE] = ",".join(set([self.get_mode(x["transportation"]["product"]["class"]) for x in journey["legs"]]))
            return info
        return info

    def get_mode(self, iconId):
        """Map the iconId to proper modes string."""
        modes = {
            1: "Train",
            4: "Lightrail",
            5: "Bus",
            7: "Coach",
            9: "Ferry",
            11: "Schoolbus"
        }
        return modes.get(iconId, None)
