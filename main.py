import requests, time


ROBLOSECURITY = open("ROBLOSECURITY.txt", "r").read()

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
        todays_date = time.strftime("%Y-%m-%d")
        data = {
            "breakdowns": ["AgeGroup"],
            "granularity": "OneDay",
            "metric":"MonthlyActiveUsers",
            "startTime":todays_date,
            "endTime": todays_date"
        };
        try:
            response = self.session.post(url, headers=headers, data=json.dumps(data))
            response = json.loads(response.text)["values"][0]["datapoints"][0]["value"]
            return int(response)
        except:
            return False


roblox = roblox_api()
total = 0

outputfile = open('output.csv', 'a')

for group in roblox.get_groups():
    groupId = group["id"]
    groupName = group["name"]
    for game_data in roblox.get_games(groupId):
        universeId = game_data["id"]
        expirenceName = game_data["name"]
        MAU = roblox.get_expirence_mau(universeId)
        if MAU == False:
            #print("Failed to get MAU for {}".format(expirenceName))
            continue
        else:
            total += MAU
            print("{} - {}".format(expirenceName, format_number(MAU)))
            decoded_name = expirenceName.encode('ascii', 'ignore').replace(",", "")
            outputfile.write("{},{}\n".format(decoded_name, MAU))

outputfile.close()
print("Total MAU: {}".format(format_number(total)))
