import requests, time, json, sys, pycountry


#Get arg for UniverseId
universeId = sys.argv[1]
expirenceName = sys.argv[2]

ROBLOSECURITY = open("ROBLOSECURITY.txt", "r").read()
game_data_folder = "./GameData/"
breakdowns = ["Country"]
todays_date = time.strftime("%Y-%m-%d")

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
        try:
            return json.loads(response.text)["data"]
        except:
            return False

    def get_expirence_mau(self, universeId):
        url = "https://apis.roblox.com/developer-analytics-aggregations/v1/metrics/engagement/universes/{}".format(universeId)
        headers = {
            'x-csrf-token': self.get_xsrf_token(),
            'Content-Type': 'application/json'
        };
        todays_date = "2024-06-24T00:00:00.000Z"
        data = {
            "breakdowns": ["AgeGroup"], 
            "granularity": "OneDay",
            "metric":"MonthlyActiveUsers",
            "startTime":todays_date,
            "endTime": todays_date
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
            "startTime": "2024-06-24T00:00:00.000Z",
            "endTime": "2024-06-24T00:00:00.000Z"
        };
        response = self.session.post(url, headers=headers, data=json.dumps(data))

        fetched_data = {}

        try:
            for data in json.loads(response.text)["values"]:
                fetched_data[data["breakdowns"][0]["value"]] = data["datapoints"][0]["value"]

            return fetched_data
        except:
            return False


roblox = roblox_api()
total = 0

outputfile = open('BasketData-{}-MAU.csv'.format(todays_date), 'a')
file_prefix = "BasketData-{}".format(todays_date)


if universeId == None:

    for group in roblox.get_groups():
        groupId = group["id"]
        groupName = group["name"]
        print("Group: {}".format(groupName))
        group_games = roblox.get_games(groupId)

        #repeat a few times if we get no group games
        if group_games == False:
            for i in range(5):
                group_games = roblox.get_games(groupId)
                if group_games != False:
                    break
        
        if group_games == False:
            print("Failed to get games for {}".format(groupName))
            continue

        for game_data in group_games:
            universeId = game_data["id"]
            expirenceName = game_data["name"]
            MAU = roblox.get_expirence_mau(universeId)
            if MAU == False:
                #print("Failed to get MAU for {}".format(expirenceName))
                continue
            else:
                total += MAU
                #ascii decode
                decoded_expirence_name = expirenceName.encode('ascii', 'ignore').decode('ascii').replace(",", "").replace("/", "").replace("?","")
                decoded_group_name = groupName.encode('ascii', 'ignore').decode('ascii').replace(",", "").replace("/", "").replace("?","")
                outputfile.write("{},{}\n".format(decoded_expirence_name, MAU))



                for breakdown in breakdowns:
                    data = roblox.get_expirence_demographic(universeId, breakdown)

                    if data == False:
                        print("Failed to get {} data for {}".format(breakdown, expirenceName))
                        continue

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

else:
    decoded_expirence_name = expirenceName
    decoded_group_name = "N/A"
    groupId = "NA"

    for breakdown in breakdowns:
        data = roblox.get_expirence_demographic(universeId, breakdown)

        if data == False:
            print("Failed to get {} data for {}".format(breakdown, expirenceName))
            continue

        for key, value in data.items():
            print("{},{},{},{}".format(decoded_group_name, decoded_expirence_name, key, value))

            #convert key from country code to country name
            if breakdown == "Country":
                try:
                    key = pycountry.countries.get(alpha_2=key).name
                except:
                    pass            


            group_link = "https://www.roblox.com/groups/{}/x".format(groupId)
            
            game_specific_breakdown_file = open("{}/{}-{}.csv".format(game_data_folder, decoded_expirence_name, breakdown), 'a')
            game_specific_breakdown_file.write("{},{}\n".format(key, value))
            game_specific_breakdown_file.close()

            everything_breakdown_file = open("{}-{}.csv".format(file_prefix, breakdown), 'a')
            everything_breakdown_file.write("{},{},{},{},{}\n".format(decoded_group_name, decoded_expirence_name, key, value, group_link))
            everything_breakdown_file.close()
