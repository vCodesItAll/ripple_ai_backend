from datetime import timedelta
from typing import Any
from fastapi import FastAPI, APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from langchain.memory import CassandraChatMessageHistory, ConversationBufferMemory
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import json
import openai
import time
import os
import sys

"""
changed stream_prompt into 2 functions generate_response and update_chat_history.

generate_response now takes in the origanal template as well as the human input. 
this allows us to add alot more templets to the websight without changeing the back end.

i cant get my requirements working on my computor so i am 100% sure there will need to be more changes and fixes before this works but so far so good.
"""

router = APIRouter()

# Getting OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
if not len(OPENAI_API_KEY):
    print("Please set OPENAI_API_KEY environment variable. Exiting.")
    sys.exit(1)

openai.api_key = OPENAI_API_KEY


async def generate_response(human_input_str: str, original_template: str) -> Any:
    try:
        # makeing templete
        template = f"""
        {original_template}
        
        Some rules to follow:
        1. Always start by asking for a name for the protagonist.

        Here is the chat history, use this to understand what to say next: {{chat_history}}
        Human: {{human_input}}
        AI:
        """
        # calling function that talks to cassandra
        chat_history = await update_chat_history()

        # making the prompt an object
        prompt = PromptTemplate(
            input_variables=["chat_history", "human_input"],
            template=template
        )
        llm = OpenAI(openai_api_key=OPENAI_API_KEY)
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            memory=chat_history
        )

        # getting response
        response = llm_chain.predict(human_input=human_input_str)
        
        # checking for errors
    except Exception as e:
        print("Error in creating campaigns from OpenAI:", str(e))
        raise HTTPException(503, "OpenAI server is busy, try again later")
    
    # returning responce
    return StreamingResponse(get_response_openai(response), media_type="text/event-stream")

async def update_chat_history():
    # most of the cassandra code unchanged
    cloud_config = {
        'secure_connect_bundle': 'app/secure-connect-ripple-ai.zip'
    }
    with open("app/ripple_ai-token.json") as f:
        secrets = json.load(f)

    CLIENT_ID = secrets["clientId"]
    CLIENT_SECRET = secrets["secret"]
    ASTRA_DB_KEYSPACE = "database"

    auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect()

    message_history = CassandraChatMessageHistory(
        session_id="ripplesession",
        session=session,
        keyspace=ASTRA_DB_KEYSPACE,
        ttl_seconds=3600
    )
    message_history.clear()

    cass_buff_memory = ConversationBufferMemory(
        memory_key="chat_history",
        chat_memory=message_history
    )

    return cass_buff_memory

def get_response_openai(response: str):
    # print(response)
    current_content = response
    try:
        yield current_content
    except Exception as e:
        print("OpenAI Response (Streaming) Error: " + str(e))
        raise HTTPException(503, "OpenAI server is busy, try again later")


