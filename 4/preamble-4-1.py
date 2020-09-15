# NOTE: The authoritative original source of this snippet is in
# https://github.com/UTokyo-IPP/utpython/preamble.py.

import getpass

#@title Submission snippet
#@markdown Please [login to server](https://utpython-autograder-v6gvzmyosa-an.a.run.app/login) to get a JWT token, run this cell and paste the JWT token.
SERVER_URL = 'https://utpython-autograder-v6gvzmyosa-an.a.run.app'
JWT_TOKEN = getpass.getpass('Enter JWT token:')

import json
import requests

from google.colab import _message as google_message
from IPython.core import display

def Submit(exercise_id=None):
  if JWT_TOKEN == "":
    display.display(display.HTML("Please get JWT_TOKEN by visiting " +
                                 "<a href='" + SERVER_URL + "/login'>Login page</a>"))
    raise Exception("Please set JWT_TOKEN")
  notebook = google_message.blocking_request(
    "get_ipynb", request="", timeout_sec=120)["ipynb"]
  ids = []
  for cell in notebook['cells']:
        if 'metadata' not in cell:
          continue
        m = cell['metadata']
        if m and 'exercise_id' in m:
            cell_id = m['exercise_id']
            if cell_id:
                ids.append(cell_id)
  params = {}
  if exercise_id:
    if exercise_id not in ids:
        raise Exception('Not valid exercise ID: ' + exercise_id + ". Valid ids: " + ", ".join(ids))
    params["exercise_id"] = exercise_id
  data = json.dumps(notebook)
  r = requests.post(SERVER_URL + "/upload", files={"notebook": data},
                    headers={"Authorization": "Bearer " + JWT_TOKEN},
                    params=params)
  if r.status_code == 401:
    display.display(display.HTML("Not authorized: is your JWT_TOKEN correct? " +
                                 "Please get JWT_TOKEN by visiting " +
                                 "<a target='_blank' href='" + SERVER_URL + "/login'>Login page</a>" +
                                 "in a new browser tab."))  
  display.display(display.HTML(r.content.decode('utf-8')))
  
if JWT_TOKEN == "":
  display.display(display.HTML("Please get JWT_TOKEN by visiting " +
                                 "<a href='" + SERVER_URL + "/login'>Login page</a>"))
  raise Exception("Please set JWT_TOKEN")

# Create the sample text.
import os
with open('sample.txt', 'w') as f:
    f.write('''Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.''')
