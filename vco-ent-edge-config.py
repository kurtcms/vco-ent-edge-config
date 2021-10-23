import time
import datetime
import json
from client import VcoRequestManager
from client import ApiException
from sys import path
from os import mkdir, environ
from dotenv import load_dotenv, find_dotenv

class pccwg_vco():
    INTERVAL_SECS = 300
    '''
    300 seconds i.e. 5 minutes interval as default for API calls
    '''

    INTERVAL_SECS_METRICS = 3600
    '''
    3600 seconds i.e. 60 minutes interval as default for the
    aggregate Edge transport metrics call
    '''

    VCO_THRESHOLD = 600
    '''
    600 seconds i.e. 10 minutes for data is often not reflected in API
    output for up 10 minutes as per the API documentation
    https://code.vmware.com/apis/1045/velocloud-sdwan-vco-api
    '''

    ERR_INVALID_ENV = 'Problem locating the .env file'
    '''
    Error message to display when python-dotenv fails to read
    environment variables
    '''

    ERR_EMPTY_METRICS = 'monitoring/getAggregateEdgeLinkMetrics returns empty'
    '''
    Error message to display when monitoring/getAggregateEdgeLinkMetrics
    returns empty
    '''

    def __init__(self):
        if load_dotenv(find_dotenv()) == False:
            '''
            Raise a system exit on error reading environment variables
            with python-dotenv
            '''
            raise SystemExit(self.ERR_INVALID_ENV)

        try:
            '''
            Read and set the environment variables needed for the VCO
            client authentication
            '''
            hostname = environ['VCO_HOSTNAME']
            username = environ['VCO_USERNAME']
            password = environ['VCO_PASSWORD']
        except KeyError as e:
            '''
            Raise a system exit on error reading the environment variables
            '''
            raise SystemExit(e)

        '''
        Initiate and authenticate the VCO client object
        '''
        self.client = VcoRequestManager(hostname)
        self.client.authenticate(username, password, is_operator=False)

        '''
        Read and initiate the time now
        '''
        self.time_now = self.__update_time()

        '''
        Read and set the enterpriseName and enterpriseId from
        a call to the monitoring/getAggregateEdgeLinkMetrics
        '''
        self.metrics = self._get_aggre_metrics(self.INTERVAL_SECS_METRICS)
        self.ent_name = self._get_ent_name(self.metrics)
        self.ent_id = self._get_ent_id(self.metrics)

        '''
        Read and set the edgeId from a call to the
        enterprise/getEnterpriseEdges
        '''
        self.ent_edge = self._get_ent_edge()
        self.edge_id = self._get_edge_id(self.ent_edge)

    def __update_time(self):
        '''
        Return the time now minus the VCO API delay
        threshold in epoch
        '''
        time_now = int(time.time() - self.VCO_THRESHOLD)
        return time_now

    def __name_sanitised(self, name):
        '''
        Replace non-alphanumeric character in string with a dash
        for sanitisation
        '''
        return ''.join([c if c.isalnum() else '-' for c in name])

    def _get_time_e(self, interval_sec = None):
        '''
        Read the time now minus the VCO API delay threshold and
        set the start and end time accirdingly in epoch and in
        milliseconds with a default 5-minute interval unless
        otherwise specified
        '''
        if interval_sec is None:
            interval_sec = self.INTERVAL_SECS
        self.time_end_e = self.time_now * 1000
        self.time_start_e = (self.time_now - int(interval_sec)) * 1000

    def _get_time(self, interval_sec = None):
        '''
        Read the time now minus the VCO API delay threshold and
        set the start and end time in UTC and in ISO 8601 format
        with a default 5-minute interval unless otherwise specified
        '''
        if interval_sec is None:
            interval_sec = self.INTERVAL_SECS
        self.time_end = datetime.datetime.utcfromtimestamp(
                        self.time_now).isoformat()
        self.time_start = datetime.datetime.utcfromtimestamp(
                            self.time_now - int(interval_sec)).isoformat()

    def _get_aggre_metrics(self, interval_sec):
        '''
        Poll and return the aggregate Edge transport metrics
        of all the Edges given a specified time interval
        '''
        self._get_time_e(interval_sec)
        try:
            metrics = self.client.call_api(
                        'monitoring/getAggregateEdgeLinkMetrics', {
                            'interval': {
                                'start': self.time_start_e,
                                'end': self.time_end_e
                            }
            })
            if metrics:
                return metrics
            else:
                # Raise a system exit on an empty metrics
                raise SystemExit(self.ERR_EMPTY_METRICS)
        except Exception as e:
            # Raise a system exit on exception
            raise SystemExit(e)

    def _get_ent_id(self, metric):
        '''
        Return the enterpriseId
        '''
        try:
            return metric[0]['link']['enterpriseId']
        except KeyError as e:
            # Raise a system exit on error reading the enterpriseId
            raise SystemExit(e)

    def _get_ent_edge(self):
        '''
        Poll and return details of all the Edges given the enterpriseId
        '''
        ent_edge = self.client.call_api(
                    'enterprise/getEnterpriseEdges', {
                        'enterpriseId': self.ent_id,
                    })
        return ent_edge

    def _get_edge_id(self, ent_edge):
        '''
        Return a list of the edgeId for all the Edges given
        '''
        edge_list = []
        for each in ent_edge:
            if isinstance(each['id'], int):
                edge_list.append(each['id'])
        return list(set(edge_list))

    def _get_ent_name(self, metric):
        '''
        Return the enterpriseName
        '''
        try:
            return metric[0]['link']['enterpriseName']
        except KeyError as e:
            # Raise a system exit on error reading the enterpriseName
            raise SystemExit(e)

    def _get_edge_name(self, edge_id, ent_edge):
        '''
        Return the Edge name given its ID
        '''
        for edge in ent_edge:
            if edge['id'] == edge_id:
                return edge['name']
        # Return the Edge ID instead if the name is not found
        return edge_id

    def get_ent_events(self, interval_sec = None):
        '''
        Poll and return events given the enterpriseId and a specified
        time interval
        '''
        self._get_time(interval_sec)
        events = self.client.call_api('event/getEnterpriseEvents',
                    {
                        'enterpriseId': self.ent_id,
                        'interval': {
                            'start': self.time_start,
                            'end': self.time_end
                    }
        })
        return events['data']

    def get_ent_fw_logs(self, interval_sec = None):
        '''
        Poll and return firewall logs given the enterpriseId and a
        specified time interval
        '''
        self._get_time(interval_sec)
        fw_logs = self.client.call_api(
                    'firewall/getEnterpriseFirewallLogs', {
                        'enterpriseId': self.ent_id,
                        'interval': {
                            'start': self.time_start,
                            'end': self.time_end
                    }
        })
        return fw_logs['data']

    def get_ent_edge_config(self):
        '''
        Poll and return the Edge config moodule given the
        enterpriseId and the edgeId
        '''
        edge_configs = {}
        for edge in self.edge_id:
            edge_config = self.client.call_api(
                            'edge/getEdgeConfigurationStack', {
                                'enterpriseId': self.ent_id,
                                'edgeId': edge
                            })
            edge_configs[self._get_edge_name(edge,
                self.ent_edge)] = edge_config
        return edge_configs

    def write_ent_edge_config(self, edge_configs):
        '''
        Write each of the Edge config stacks as JSON files in a
        directory named by the sanitised enterpriseName, and nested
        in a number of subdirectories named respectively by the year,
        the month and the day, and finally by the the full date and
        time now to ease access.
        .
        └── enterpriseName/
            └── Year/
                └── Month/
                    └── Date/
                        └── YYYY-MM-DD-HH-MM-SS/
                            ├── edgeName1.json
                            ├── edgeName2.json
                            ├── edgeName3.json
                            └── edgeName4.json
        '''
        ent_name_sanitised = self.__name_sanitised(self.ent_name)
        time_stamp = time.strftime('%Y-%m-%d-%H-%M-%S',
                        time.gmtime(self.__update_time()))
        date_time = datetime.datetime.strptime(time_stamp,
                    '%Y-%m-%d-%H-%M-%S')

        ent_edge_config_dir_list = [ent_name_sanitised,
                                    date_time.year,
                                    date_time.month,
                                    date_time.day,
                                    time_stamp]

        ent_edge_config_dir = path[0] + '/'

        for i in range(len(ent_edge_config_dir_list)):
            ent_edge_config_dir += str(ent_edge_config_dir_list[i]) + '/'

            try:
                mkdir(ent_edge_config_dir)
            except FileExistsError:
                pass

        for each in edge_configs:
            each_sanitised = self.__name_sanitised(each)
            with open(ent_edge_config_dir + each_sanitised + '.json',
            'w') as f:
                f.write(json.dumps(edge_configs[each]))

    def write_ent_events(self, events):
        '''
        Write each of the event in a JSON file named 'events' in
        a directory by the name of the sanitised enterpriseName.
        Each event will be logged in a new line in the JSON file.
        .
        └── enterpriseName/
            └── events.json
        '''
        if events:
            ent_name_sanitised = self.__name_sanitised(self.ent_name)
            ent_event_dir = path[0] + '/' + ent_name_sanitised + '/'
            ent_event_file_name = 'events'

            try:
                mkdir(ent_event_dir)
            except FileExistsError:
                pass

            event = ''
            for each in events:
                event += json.dumps(each) + '\n'

            with open(ent_event_dir + ent_event_file_name + '.json',
            'a') as f:
                f.write(event)

if __name__ == '__main__':
    '''
    Create the VCO client object, and read and write the Edge
    config stacks by calling the respective functions.
    '''
    conn = pccwg_vco()
    ent_edge_config = conn.get_ent_edge_config()
    conn.write_ent_edge_config(ent_edge_config)
