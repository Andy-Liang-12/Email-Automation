import requests
import datetime 
import logging
import re
import draft_send_reply_PD as DSR

# Configure logging
logging.basicConfig(level=logging.INFO)

def fetch_tasks_for_day(api_key, app_key, owner_id, date):
    url = "https://api.pipelinecrm.com/api/v3/calendar_entries"
    headers = {
        "Content-Type": "application/json",
    }
    
    '''person_id --> tasks associated to person (different from assigned)
    owner_id --> who the task is assigned to
    '''
    params = {
        'conditions[incomplete]': 'true',
        'conditions[today]': 'true',
        'conditions[owner_id]': owner_id,
        
        "api_key": api_key,
        "app_key": app_key
    }
    
    try: 
        response = requests.get(url, headers=headers, params=params)
         # Log the URL of the request
        logging.info(f"Requested URL: {response.request.url}")
        
        response.raise_for_status()  # Raises a HTTPError for bad responses
        # logging.info(f"Request successful: {response.text}")
        logging.info(f'Request successful')
        
        return response.json()
    
    except requests.exceptions.HTTPError as errh:
        logging.error(f"HTTP error occurred: {errh}")
    except requests.exceptions.ConnectionError as errc:
        logging.error(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        logging.error(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        logging.error(f"Error: {err}")

def find_user(email):
    url = "https://api.pipelinecrm.com/api/v3/profile"
    headers = {
        "Content-Type": "application/json",
    }
    
    params = {
        'conditions[email]': email,
        "api_key": api_key,
        "app_key": app_key
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json()
    except requests.exceptions.RequestException as e:
        return e

'''takes in user dictionary, parses for id'''
def parse_user_id(user_info: dict):
    return user_info.get('id')

if __name__ == "__main__":
    api_key = 'YOUR API KEY HERE'
    app_key = 'YOUR APP KEY HERE'
    email = 'YOUR_EMAIL@tuckadvisors.com'
    
    today = datetime.date.today()
    user_info = find_user(email=email)
    owner_id = parse_user_id(user_info=user_info)
    
    task_list = fetch_tasks_for_day(api_key, app_key, owner_id, today).get('entries')
    
    follow_up_task_list = []
    
    for task in task_list:
        task_name = task.get('name')
        if 'f/u' in task_name or 'keep reaching out' in task_name:
            # Some Companies formated like "Sample Long Company (SLC)"
            # only pass along real name
            company_name = task.get('association').get('name')
            symbol = "("
            company_name = re.split(f'(?={re.escape(symbol)})', company_name)[0]
            follow_up_task_list.append(company_name)
    
    print(follow_up_task_list)
    
    templates = ['I wanted to touch base regarding the M&A opportunity with __CLIENT__. If __COMPANY__ is interested in exploring this further, please let me know, and we can schedule a call at your convenience. If not, just let me know, and I can remove you from our list. Thank you!',
                 'I’m following up on my previous email about a potential M&A opportunity with __CLIENT__. If __COMPANY__ is open to discussing this further, I’d be glad to arrange a call to provide more details. If this isn’t of interest at the moment, please let me know, and I will update our records accordingly.',
                 'I wanted to reach out again to see if __COMPANY__ might be interested in an M&A opportunity with __CLIENT__. I’m happy to schedule a call to go over the details at a time that works for you. Alternatively, if now isn’t a good time, please let me know, and I will remove you from our list. Thank you!',
                 '__POSITIONING__STATEMENT__. Would __COMPANY__ be interested in an M&A opportunity with __CLIENT__? Please let me know if you have any questions or would like to schedule a call. Thanks!']
    current_template = templates[2]
    client = 'Alpine'
    service = DSR.get_service()
    
    queried_messages_list = DSR.handle_query_list(service, query_list=follow_up_task_list, quoted=True)
    for messages_list in queried_messages_list:
        print(messages_list)
        DSR.reply_to_messages_list(messages_list=messages_list, form = 'draft', append_signature = True, reply_message=current_template, client_name=client)