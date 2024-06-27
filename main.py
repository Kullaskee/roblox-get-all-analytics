import requests, time, json


ROBLOSECURITY = open("ROBLOSECURITY.txt", "r").read()
game_data_folder = "./GameData/"
breakdowns = ["AgeGroup", "Country", "Gender"]
todays_date = time.strftime("%Y-%m-%d")
todays_date_string = "2024-06-24T00:00:00.000Z" #edit this to be a few days behind current day!!!!!

def format_number(number):
    return "{:,}".format(number)

class roblox_api:
    def __init__(self):
        global ROBLOSECURITY
        self.session = requests.Session()
        self.session.cookies['.ROBLOSECURITY'] = ROBLOSECURITY


    def get_xsrf_token(self):
        url = "https://auth.roblox.com/v2/logout"
        response = self.session.post(url)
        return response.headers['x-csrf-token']

    def get_groups(self):
        url = "https://apis.roblox.com/creator-home-api/v1/groups"
        response = self.session.get(url)
        return json.loads(response.text)["groups"]

    def get_games(self, groupId):
        url = "https://apis.roblox.com/universes/v1/search?CreatorType=Group&CreatorTargetId={}&IsArchived=false&PageSize=50&SortParam=LastUpdated&SortOrder=Desc".format(groupId)
        response = self.session.get(url)
        return json.loads(response.text)["data"]

    def get_expirence_mau(self, universeId):
        url = "https://apis.roblox.com/developer-analytics-aggregations/v1/metrics/engagement/universes/{}".format(universeId)
        headers = {
            'x-csrf-token': self.get_xsrf_token(),
            'Content-Type': 'application/json'
        };
        data = {
            "breakdowns": ["AgeGroup"], 
            "granularity": "OneDay",
            "metric":"MonthlyActiveUsers",
            "startTime":todays_date_string,
            "endTime": todays_date_string
        };
        try:
            response = self.session.post(url, headers=headers, data=json.dumps(data))
            response = json.loads(response.text)["values"][0]["datapoints"][0]["value"]
            return int(response)
        except:
            return False

    def get_expirence_demographic(self, universeId, breakdown):
        url = "https://apis.roblox.com/developer-analytics-aggregations/v1/metrics/engagement/universes/{}".format(universeId)
        headers = {
            'x-csrf-token': self.get_xsrf_token(),
            'Content-Type': 'application/json'
        };
        data = {
            "breakdown": ["{}".format(breakdown)], 
            "granularity": "OneDay",
            "metric":"MonthlyActiveUsers",
            "startTime": todays_date_string,
            "endTime": todays_date_string
        };
        response = self.session.post(url, headers=headers, data=json.dumps(data))

        fetched_data = {}

        for data in json.loads(response.text)["values"]:
            fetched_data[data["breakdowns"][0]["value"]] = data["datapoints"][0]["value"]

        return fetched_data




roblox = roblox_api()
total = 0

outputfile = open('Data-{}-MAU.csv'.format(todays_date), 'a')
file_prefix = "Data-{}".format(todays_date)

for group in roblox.get_groups():
    groupId = group["id"]
    groupName = group["name"]
    print("Group: {}".format(groupName))
    for game_data in roblox.get_games(groupId):
        universeId = game_data["id"]
        expirenceName = game_data["name"]
        MAU = roblox.get_expirence_mau(universeId)
        if MAU == False:
            #print("Failed to get MAU for {}".format(expirenceName))
            continue
        else:
            total += MAU
            #ascii decode
            decoded_expirence_name = expirenceName.encode('ascii', 'ignore').decode('ascii').replace(",", "").replace("/", "")
            decoded_group_name = groupName.encode('ascii', 'ignore').decode('ascii').replace(",", "").replace("/", "")
            outputfile.write("{},{}\n".format(decoded_expirence_name, MAU))



            for breakdown in breakdowns:
                data = roblox.get_expirence_demographic(universeId, breakdown)
                for key, value in data.items():
                    print("{},{},{},{}".format(decoded_group_name, decoded_expirence_name, key, value))

                    group_link = "https://www.roblox.com/groups/{}/x".format(groupId)
                    
                    game_specific_breakdown_file = open("{}/{}-{}.csv".format(game_data_folder, decoded_expirence_name, breakdown), 'a')
                    game_specific_breakdown_file.write("{},{}\n".format(key, value))
                    game_specific_breakdown_file.close()

                    everything_breakdown_file = open("{}-{}.csv".format(file_prefix, breakdown), 'a')
                    everything_breakdown_file.write("{},{},{},{},{}\n".format(decoded_group_name, decoded_expirence_name, key, value, group_link))
                    everything_breakdown_file.close()
            
            print("{} - {}".format(expirenceName, format_number(MAU)))
