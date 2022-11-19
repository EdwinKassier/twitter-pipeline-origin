import tweepy
import pandas as pd
from google.cloud import storage
import os
import json
from datetime import datetime

major_population_centers = [{"CITY":"CPT","WOEID":1591691},{"CITY":"DUR","WOEID":1580913}
,{"CITY":"JHB","WOEID":1582504},{"CITY":"PRY","WOEID":1586638},{"CITY":"ZEV","WOEID":1587677}]

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "gcp_credentials.json"

with open('twitter_credentials.json') as file:
    data = json.load(file)
    Bearer_Token = data["Bearer_Token"]

auth = tweepy.OAuth2BearerHandler(Bearer_Token)
api = tweepy.API(auth)


def create_result_df():

    """Query the Twitter API and retrieve the trending topics around the top five major population centers in South Africa"""

    retrieval_time = datetime.now().strftime("%m/%d/%Y")

    full_set  = []

    for item in major_population_centers:
        WOEID = item["WOEID"]
        CITY = item["CITY"]
        top_trends = api.get_place_trends(WOEID)[0]["trends"]

        result = [dict(item, city=CITY) for item in top_trends]
        result = [dict(item, retrieval_time=retrieval_time) for item in result]
        #print(top_trends[0]["trends"])
        #full_set.append(result)

        full_set += result


    dfItem = pd.DataFrame.from_records(full_set)

    print(dfItem.head())

    return dfItem



def upload_df_to_datalake(df):
    
    """Upload the provided df to the data lake (cloud storage, to be used by the next block of code in the Transform and Load step)"""

    retrieval_time = datetime.now().strftime("%m_%d_%Y")

    local_filename = f"{retrieval_time}_daily_raw_twitter_data.csv"

    #Save data as a .csv locally
    df.to_csv('daily_data.csv', encoding='utf-8')

    #Initiate a storage client
    storage_client = storage.Client()

    # The name for bucket where the data is to be stored
    bucket_name = "edwin_portfolio_twitter_data_lake"

    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(local_filename)

    blob.upload_from_filename('daily_data.csv')

    os.remove('daily_data.csv')


'''
Entry point for cloud function
'''


def Exract_Twitter_Data(request):
    """HTTP Cloud Function.
    Args:
            request (flask.Request): The request object.
            <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
            The response text, or any set of values that can be turned into a
            Response object using `make_response`
            <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    try:
        request_json = request.get_json(silent=True)
        request_args = request.args

        # validation function
        print(request_args)

        result = create_result_df()
        upload_df_to_datalake(result)

        return 'Success'
    except Exception as exc:
        print(exc)
        return 'Failure'

    


