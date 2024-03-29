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

router = APIRouter()

# Getting OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
if not len(OPENAI_API_KEY):
    print("Please set OPENAI_API_KEY environment variable. Exiting.")
    sys.exit(1)

openai.api_key = OPENAI_API_KEY

# Defining error in case of 503 from OpenAI
error503 = "OpenAI server is busy, try again later"

async def stream_prompt(human_input_str: str) -> Any:
    print(human_input_str)
    cloud_config= {
    'secure_connect_bundle': 'app/secure-connect-ripple-ai.zip'
    }

    with open("app/ripple_ai-token.json") as f:
        secrets = json.load(f)

    CLIENT_ID = secrets["clientId"]
    CLIENT_SECRET = secrets["secret"]
    ASTRA_DB_KEYSPACE = "database"
    # OPENAI_API_KEY = "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"

    auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect()

    # this is creating memory of the story and saving it for 60 mins
    message_history = CassandraChatMessageHistory(
        session_id = "ripplesession",
        session = session,
        keyspace = ASTRA_DB_KEYSPACE,
        ttl_seconds = 3600
    )

    message_history.clear()

    cass_buff_memory = ConversationBufferMemory(
        memory_key = "chat_history",
        chat_memory = message_history
    )

    #template given to AI 
    template = """
    As the storyteller, your role is to guide the user through a unique and engaging story set in the underwater world of the fish mafia, titled "The Codfather." You will create vivid scenes, craft intriguing characters, and present choices that shape the narrative. Your creativity will bring to life the murky depths of this aquatic underworld, where loyalty is as fluid as the water they swim in, and danger lurks in the shadows of the kelp forests. Engage the user with descriptive storytelling, suspenseful plot twists, and interactive decision points that allow them to influence the outcome of their story. Now please give the user an opening. After your opening the user will give you actions they would like to do and you are to incorporate them into your story. Please keep all messages 2 paragraphs long.

    Here is the chat history, use this to understand what to say next: {chat_history}
    Human: {human_input}
    AI:
    """
    try:

        prompt = PromptTemplate(
            input_variables = ["chat_history", "human_input"],
            template = template
        )

        # initializing connection to openai
        llm = OpenAI(openai_api_key=OPENAI_API_KEY)
        llm_chain = LLMChain(
            llm = llm,
            prompt = prompt,
            memory = cass_buff_memory
        )

        response = llm_chain.predict(human_input=human_input_str)
        
    except Exception as e:
        print("Error in creating campaigns from openAI:", str(e))
        raise HTTPException(503, error503)
    
    return StreamingResponse(get_response_openai(response), media_type="text/event-stream")

def get_response_openai(response: str):
    # print(response)
    current_content = response
    try:
        yield current_content
    except Exception as e:
        print("OpenAI Response (Streaming) Error: " + str(e))
        raise HTTPException(503, error503)


