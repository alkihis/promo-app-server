import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

def get_service():
  """
  Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.pickle stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists('gmail_token.pickle'):
    with open('gmail_token.pickle', 'rb') as token:
      creds = pickle.load(token)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('gmail_token.pickle', 'wb') as token:
      pickle.dump(creds, token)

  return build('gmail', 'v1', credentials=creds)
    

def create_message(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEText(message_text, 'html')
  msg = MIMEMultipart('alternative')
  msg['to'] = to
  msg['from'] = sender
  msg['subject'] = subject
  msg.attach(message)

  return {'raw': str(
    base64.urlsafe_b64encode(
      bytes(msg.as_string(), encoding="utf-8")
    ), 
    encoding="utf-8"
  )}


def send_message(service, user_id: str, message):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print('Message Id: %s' % message['id'])
    return message
  except Exception as error:
    print('An error occurred: %s' % error)


GMAIL_SERVICE = get_service()
MASTER_ADDRESS = "masterbioinformatiquelyon@gmail.com"

if __name__ == '__main__':
  send_message(GMAIL_SERVICE, MASTER_ADDRESS, create_message(MASTER_ADDRESS, MASTER_ADDRESS, "Hello", """
  <html>
    <body>
      <p>Hello !</p>
    </body>
  </html>

  """))