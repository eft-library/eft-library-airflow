import requests

api_path = 'https://api.tarkov.dev/graphql'

def get_graphql(query):
    """
    graphql api 조회
    """
    headers = {"Content-Type": "application/json"}
    response = requests.post(api_path, headers=headers, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(response.status_code, query))
