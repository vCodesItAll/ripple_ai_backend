from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from langchain.memory import CassandraChatMessageHistory, ConversationBufferMemory
from langchain.llms import OpenAI
from langchain import LLMChain, PromptTemplate
import json

cloud_config= {
  'secure_connect_bundle': 'secure-connect-ripple-ai.zip'
}

with open("ripple_ai-token.json") as f:
    secrets = json.load(f)

CLIENT_ID = secrets["clientId"]
CLIENT_SECRET = secrets["secret"]
ASTRA_DB_KEYSPACE = "database"
OPENAI_API_KEY = "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"

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
Setting
In the mystical land of Eldoria, a realm filled with magic, mythical creatures, and ancient secrets. 
The protagonist is a young adventurer seeking the legendary Crystal of Eldoria, said to possess immense power.

Main Objectives
Gather Information: Learn about the Crystal's last known location in the village of Eldor.
Recruit Allies: Find and persuade at least two companions to join the quest.
Cross the Dark Forest: Navigate through a forest filled with dangerous creatures.
Decipher the Ancient Map: Obtain and decipher a map that leads to the Crystal.
Pass the Trial of Elements: Survive trials based on the four natural elements: fire, water, earth, and air.
Retrieve the Silver Key: Obtain a key guarded by a fierce dragon.
Solve the Riddle of the Sphinx: Answer the riddle posed by a mystical sphinx to gain passage.
Traverse the Cavern of Shadows: Safely navigate a treacherous underground cavern.
Confront the Guardian: Battle or outwit the Guardian of the Crystal.
Seize the Crystal of Eldoria: Successfully take the Crystal.

Potential Outcomes Leading to Death
In the Dark Forest: Losing a battle against the forest's beasts or getting lost forever.
During the Trial of Elements: Failing to adapt to and overcome the elemental challenges.
Facing the Dragon: Provoking the dragon without adequate preparation or strategy.
At the Sphinx: Giving a wrong answer to the riddle, leading to a deadly trap.
Within the Cavern of Shadows: Falling into hidden pits or being overwhelmed by shadow creatures.
Against the Guardian: Engaging the Guardian without sufficient strength or wit.

Non-lethal Outcomes
Gaining Allies: Success or failure in recruiting companions affects later challenges.
Deciphering the Map: Incorrect interpretation leads to longer and more dangerous routes.
Obtaining the Silver Key: Choosing stealth or confrontation with the dragon influences future encounters.
Navigating the Cavern: Safe passage reveals secrets and treasures, enhancing capabilities.

Interactivity and Choices
Dialogue Choices: Interact with NPCs to gather information and make allies.
Combat vs Diplomacy: Choose to fight or negotiate in various situations.
Problem-Solving: Solve puzzles and riddles to progress.
Exploration vs Caution: Decide whether to explore risky areas for potential rewards.

Conclusion
Success: Obtaining the Crystal and returning it to a museum or using its power wisely.
Failure: Losing the Crystal or using its power for selfish or destructive purposes.
Death: Various scenarios where poor choices or failed challenges lead to the protagonist's demise.

Some rules to follow:
1. Always start by asking for a name for the protagonist.

Here is the chat history, use this to understand what to say next: {chat_history}
Human: {human_input}
AI:
"""

#setting input variables for ai prompt template
prompt = PromptTemplate(
    input_variables = ["chat_history", "human_input"],
    template = template
)

#initializing connection to openai
llm = OpenAI(openai_api_key=OPENAI_API_KEY)
llm_chain = LLMChain(
    llm = llm,
    prompt = prompt,
    memory = cass_buff_memory
)

response = llm_chain.predict(human_input="Start the adventure!")
print(response)