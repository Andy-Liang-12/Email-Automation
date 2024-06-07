import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import os.path
import inspect
current_directory = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def initialize_service():
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)
    return service

# load credentials, create gmail api client
def get_credentials():
    creds = None
    """Load or refresh credentials as needed."""
    if os.path.exists(f'{current_directory}/token.json'):
        creds = Credentials.from_authorized_user_file(f'{current_directory}/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                f'{current_directory}/credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open(f'{current_directory}/token.json', "w") as token:
                token.write(creds.to_json())
    return creds

def get_user_profile(service, user_id='me'):
    profile = service.users().getProfile(userId=user_id).execute()
    return profile

'''Creates the raw MIME message'''
def create_MIME_message(Sender, Receiver, Receiver_Name = None, thread_id = None, message_id = None, reply = False,
                   Subject = 'placeholder subject', message_text = 'placeholder email template', append_signature = False, 
                   company_name = 'placeholder company name', client_name = 'placeholder client name'):
    
    signature = get_signature(service)
    if append_signature and signature:
        message = MIMEMultipart('alternative')
        # default_name = '__<span style="color:rgb(255,0,0)">NAME</span>__'
        default_name = ''
        if client_name == 'KnowFully':
            client_link = '<a href="https://www.knowfully.com"">KnowFully</a>'
        elif client_name == 'Alpine':
            client_link = '<a href="https://alpineinvestors.com/"">Alpine Investors</a>'
        else:
            client_link = client_name
        message_text = message_text.replace('__COMPANY__', company_name)
        message_text = message_text.replace('__CLIENT__', client_link)
        # Append additional text to the HTML content
        combined_html = f"Hi {Receiver_Name or default_name},<br><br>{message_text}<br><br>{signature}"
        
        HTML_part = MIMEText(combined_html, 'html')
        message.attach(HTML_part)
    else:
        message = MIMEText(message_text)
    """Create a message for an email."""
    message['To'] = Receiver
    message['From'] = Sender
    message['Subject'] = Subject
    if reply:
        print('Creating Reply')
        message['In-Reply-To'] = message_id
        #TODO: should pass the References to this. Did not have time to fix. Should not be too difficult
        message['References'] = message_id
    else:
        print('New Email')
        
    if thread_id:
        return {
            'raw': base64.urlsafe_b64encode(message.as_bytes()).decode(),
            'threadId': thread_id  # This is needed to keep the message in the same thread
        }
    else:
        return {
            'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()
        }

'''Takes in a list of queries, uses gmail_search function to search for matching messages.
Returns list of messages found in the form [messages: query]'''
            
def handle_query_list(service, query_list: list, quoted = False):
    messages_list = []
    for query in query_list:
        # some companies called COMPANY, LLC --> remove last part
        query = query.split(',')[0]
        
        formatted_query = query
        if quoted:
            formatted_query='"{}"'.format(formatted_query)
        print(f'Searching for {query}')
        #DON'T search attachments for query
        formatted_query += " -has:attachment"
        messages = (gmail_search(service, query=formatted_query)) 
        
        if messages:
            messages_list.append([messages, query])
 
    return messages_list

''''Takes list of messages to reply to. Passes replies to create_MIME_message()
Parameters: 
messages_list: list of messages to reply to
form (draft/send): create draft or send immediately
append_signature(bool): append primary signature to email?'''

def reply_to_messages_list(messages_list: list, form = 'draft', append_signature = False, reply_message = 'This is an automated reply', 
                           client_name = 'placeholder client name'):
    company_name = messages_list[1]
    messages = messages_list[0]
    for message in messages:
        individual_message_id = message.get('id')
        msg = service.users().messages().get(userId='me', id=individual_message_id, format='full').execute()
        #Get 'Hi __NAME__' part of message
        msg_snippet = msg.get('snippet').split(',',1)[0].split()
        POC_name = msg_snippet[1] if len(msg_snippet)>1 else None
        
        headers = msg['payload']['headers']
        #print(f'Headers: {headers}') # Headers are dictionaries, e.g. {'name': 'Subject', 'value': 'query testing'}
        
        Subject = next((header['value'] for header in headers if header['name'] == 'Subject'), None)
        from_email = next((header['value'] for header in headers if header['name'] == 'To'), None)
        # note: the Message-ID is different from the Gmail API id.
        message_id = next((header['value'] for header in headers if header['name'] == 'Message-ID'), None)
        
        thread_id = msg['threadId']
        
        # Often formatted like "Andy Liang <andy.liang@tuckadvisors.com" --> split by <> for email only
        reply_to = from_email.split('<')[-1].split('>')[0] if '<' in from_email else from_email

        # Create reply message
        reply_subject = "Re: " + Subject.removeprefix("Re: ")
        
        reply = create_MIME_message(Sender = Your_Email, Receiver=reply_to, Receiver_Name=POC_name if POC_name is not None else None,
                                    thread_id=thread_id, message_id=message_id, reply = True, Subject = reply_subject, 
                                    message_text=reply_message, append_signature=append_signature,
                                    company_name=company_name, client_name=client_name)
        handle_message(service, raw_msg=reply, form=form)
        

"""Create a draft email/send an email message from raw MIME message
Print the returned message and id.
Returns: Draft/message object, including id

Load pre-authorized user credentials from the environment.
"""
def handle_message(service, raw_msg, form = 'draft'):
    try:
        if form == 'draft':
            # message = {"message": {"raw": encoded_message}}
            draft_message = {'message': raw_msg}
            draft = (
                service.users()
                .drafts()
                .create(userId="me", body=draft_message)
                .execute()
            )
            print(f'Draft id: {draft["id"]}')
            #print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')
            return draft

        elif form == 'send':
            # message = {"raw": encoded_message}
            send_message = (
                service.users()
                .messages()
                .send(userId="me", body=raw_msg)
                .execute()
            )
            print(f'Message Id: {send_message["id"]}')
            return send_message
        
        else:
            print(f'invalid form {form}')
            return
        
    except HttpError as error:
        print(f"An error occurred: {error}")

'''Takes in a search term, returns (maxResults) most recent results. Defaults to only most recent result.'''
def gmail_search(service, query = r'"special test email"', maxResults = 1):
    try:
        # Construct the query
        # query = 'in:outreach is:starred "company"' # sample query
        # messages default format: [{'id': '', 'threadID': ''}]
        results = service.users().messages().list(userId='me', q=query, maxResults=maxResults).execute()
        messages = results.get('messages', [])
        if not messages:
            print(f'No messages found for query: {query}')
        else:
            print(f'Search for {query} returned {messages}')
        return messages
        
    except HttpError as error:
        print(f"An error occurred: {error}")

    raw_messages = []
    for message in messages:
        msg_id = message['id']
        # formats can be minimal, metadata, full, raw
        msg = service.users().messages().get(userId='me', id=msg_id, format='metadata').execute()
        raw_messages.append(msg)
    return raw_messages

def get_signature(service, user_id='me'):
    try:
        # Get the list of send-as aliases
        send_as_response = service.users().settings().sendAs().list(userId=user_id).execute()
        send_as_aliases = send_as_response.get('sendAs', [])
        for alias in send_as_aliases:
            if alias.get('isPrimary', False):
                # Return the signature of the primary alias
                return alias.get('signature', '')
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_service():
    return service

# load credentials, create gmail api client
service = initialize_service()
# Get current user's email
Your_Email = get_user_profile(service)['emailAddress']

if __name__ == "__main__":
    #testing code
    query_list = ['American Online Insurance School', 'Finspire Academy']
    
    queried_messages_list = handle_query_list(service, query_list=query_list, quoted=True)
    print(f'queried messages list: {queried_messages_list}')
    for messages_list in queried_messages_list:
        print(messages_list)
        # company_name = messages_list[1]
        # print(f'company: {company_name}')
        # messages_list = messages_list[0]
        # for message in messages_list:
        #     print(f'message: {message}')
        #     print(f'message id: {message.get('id')}')
        reply_to_messages_list(messages_list=messages_list, form = 'draft', append_signature = True, 
                               reply_message='__CLIENT__', client_name='KnowFully')
    
    # message = create_MIME_message(Sender=Your_Email, Receiver=Your_Email, Subject='testing email', message_text='placeholder email msg', append_signature=False)
    # handle_message(service, raw_msg=message, form='draft')
    