# Introduce AI into your file approval workflow by letting an LLM examine your New Unapproved Executed events
import requests, datetime
from openai import OpenAI
import pandas as pd
# Fill in these variable values for your environment:
######################################################
# Language Model settings:
# For use with LM Studio running on this machine:
LLM_server = "http://localhost:1234/v1" 
# default API key for LM Studio:
lm_api_key="lm-studio" 
# LLM model to use. Must be installed and running if using LM Studio:
model_name = "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF"
######################################################
# App Control server settings:
AppC_server = "https://192.168.1.1"
AppC_api_key = "6C491644-9A43-422A-8E78-0A4C03E2D120"
######################################################

# Quick cleanup function to make the LLM messages more readable
def clean_and_format_message(message):
     text = repr(message.content)
     text = text.encode().decode('unicode_escape')
     return text


# Get the New Unapproved Executed events for the last day
AppC_header = { "X-Auth-Token" : AppC_api_key }
AppC_api_endpoint = AppC_server + "/api/bit9platform/v1/event/"
AppC_query = "?q=fileFirstExecutionDate>2000-01-01&fileState:1&subtype:1003&timestamp>-1day"
AppC_uri = AppC_api_endpoint + AppC_query

AppC_response = requests.get(AppC_uri, headers=AppC_header, verify=False)
if AppC_response.status_code != 200:
    print("AppC query unsuccessful")
    exit()
events = AppC_response.json()

# Set up the LLM connection
client = OpenAI(base_url=LLM_server, api_key=lm_api_key)

event_dispositions = []
for file_event in events:
  completion = client.chat.completions.create(
    model=model_name,
    messages=[
      {"role": "system", "content": "You are a Security Operations Center analyst with decades of experience in red teaming, blue teaming, malware detection engineering, intrusion detection and response, edr, xdr, SIEM, and SOAR. You also have extensive experience as an actuary and have published on arxiv.org and lesswrong.com, so you give well-calibrated probabilities for uncertain events. Analyze the following file discovery events from Carbon Black App Control and give a probability that they should be globally approved, with the most valuable indicators supporting your determination."},
      {"role": "user", "content": repr(file_event)}
    ],
    temperature=0.7,
  )
  print(clean_and_format_message(completion.choices[0].message))
  print("----------------------------------------------------------------------------")
  event_dispositions.append(completion.choices[0].message)

event_analyses = pd.DataFrame(events)
event_analyses['LLM Analysis'] = event_dispositions
event_analyses['LLM Analysis'] = event_analyses['LLM Analysis'].apply(clean_and_format_message)


current_date = datetime.now().strftime("%y-%m-%d")
event_analyses.to_csv(f'event_analysis_results_{current_date}.csv' )
