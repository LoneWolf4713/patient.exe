# A chatbot that will act as a patient taking presciption from a doctor

# Some Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda


# Other Imports
from typing import List, Annotated
from typing_extensions import TypedDict
import operator
import json
import re

# LangGraph Imports:
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver
from redis import Redis

# Tool Inputs
import pydantic
from pydantic import BaseModel, Field
from typing import Literal

# Logging Imports
import logging

# Env Variable Imports
import os
import sys
from dotenv import load_dotenv

# Logging Setup
logging.basicConfig(
    filename="logs.txt",
    encoding="utf-8",
    filemode="w",
    format="{asctime} - {levelname} : {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.DEBUG,
    force=True
)
logging.info("Engine Module Called and Started")

# Trying to import the Gemini API Key and The Redis URL
load_dotenv()
apiKey = os.getenv("GEMINI_API_KEY")
redisURL = os.getenv('REDIS_URL')


# Global Variable to Better Handle Chatbot Readyness
CHATBOT_READY = False

# Verifying Presence of Gemini API KEY
if  apiKey:
    logging.info("Gemini API Key Loaded")
else:
    logging.debug("Gemini API Key NOT Found")

# Making the Redis Checkpointer 
checkpointer = None
if redisURL:
    logging.info("Redis URL Env Var Loaded, Trying checkpointer now...")
    try:
        redisClient = Redis.from_url(redisURL)
        checkpointer = RedisSaver(redis_client=redisClient)
        checkpointer.setup()
        logging.info("Redis Checkpointer Setup and Ready")

    except Exception as e:
        logging.debug(f"Error Establishing Redis Checkpointer: {e}")

else:
    logging.debug("Couldn't Find Redis URL")


if apiKey and checkpointer:
    CHATBOT_READY = True
    logging.info("Chatbot Ready")
else:
    logging.debug("Chatbot Not Ready")


if CHATBOT_READY:
    model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite",  top_p=0.95,
    top_k=40, temperature = 1.0, google_api_key = apiKey)
    
    # The Clipboard
    class patientState(TypedDict):
        patientPersona: str         # To give some personality
        disease: str                # particular disease our AI will have
        symptoms: list[str]         # list of three symptoms

        symptomsRevealed: list[str] # Added these variables to implement
        symptomsRemaining: list[str] # Progressive Symptom Reveal

        chatHistory: Annotated[list, operator.add]
    
        last_classification: str

    def routeInitialMessage(state: patientState):
        """
        This node decides whether the user is a new one or a previously talked one
        and routes the graph based on that.
        """

        if "patientPersona" not in state or state["patientPersona"] is None:
            return "initialize"
        else:
            return "continue"
        

    def initializePersona(state: patientState):
        """
        This ndoe initializes the Persona, Disease and Symptoms of the chatbot on each run.
        On each run, a new, dynamic and unique persona, disease and symptoms are generated
        so the chatbot doesn't feel repetitive.

        Also added a randomTag to make sure the AI Returns different outputs on each run,
        because previously it was returning the same and same personas ignoring the prompt,
        (maybe caching?).
        The randomTag helps keeping the novelty of the prompt.

        """
        randomTag = str(os.urandom(8).hex())
        response = model.invoke(f"""
                                RANDOM TAG: {randomTag}
                                You are a medical simulator.
                                            Generate a realistic but varied non-critical condition can range from mild allergies to digestive issues to viral infections to muscular issues to dermatological issues to stress related issues,
                                            Geneate a list of 3 progressive symptoms that increase in severity or clarity and must not repeat frequently used symptom sets, 
                                            Generate a one-sentence patient persona with emotional style AND Communication quirks
                                            Format as a JSON Object with keys: 'disease', 'symptoms' and 'persona'.

                                            Make the disease and diverse as diverse as possible

                                            Return ONLY JSON, NO MARKDOWN:
                                            {{ "disease": "", "symptoms": [], "persona": "" }}""").content.strip()
        
        # model was still returning markdown, so just to make sure. 
        if response.startswith("```"):
            response = response.strip("`")
            response = response.replace("json", "").strip()
        
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            logging.error("Model Didn't Return JSON in Initialize Persona")

        response =match.group(0)
        try:
            response = json.loads(response)
            return {
                "patientPersona": response["persona"],
                "disease": response["disease"],
                "symptoms": response["symptoms"],
                "symptomsRemaining": response["symptoms"],
                "symptomsRevealed": []
            }
        except Exception as e:
            logging.error(f"Error While Parsing :InitializePersona Output: {e}")
            logging.error(f"Model's Response Was: {response}")

    
    def generatePatientResponses(state: patientState):
        """
        This is the main node that generates the AI Response on each message.
        The prompt gives it's persona, disease and symptoms along with the chatHistory"""
        patientPrompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
                You are {patientPersona}. You have {disease}. Your Symptoms are {symptoms}.
                 Your goal is
                          to describe progressively. Do NOT reveal all symptoms at once. Only
                          answer the doctor's questions based on your persona.
                          Respond to last message.
                          You are already revealed the {symptomsRevealed} Symptoms. Reveal the remaining one, that is: {symptomsRemaining}.
            """),
            MessagesPlaceholder(variable_name="chatHistory")
        ])

        patientChain = patientPrompt | model 

        response = patientChain.invoke(
            state
        )

        # Adding Truncating History to last 5 messages.
        updatedHistory = state["chatHistory"] + [response]

        return {"chatHistory": updatedHistory[-5:]}



    # Function Calling Implemented as to determine the user's message intent
    # the thing is, I ran into t a problem where I tried to do this manually by detecting question marks but it was so prone to failing
    # so now our LLM model will do the job for us

    class ClassifyInput(BaseModel):
        classification: Literal["questioning", "prescribingTreatment"] = Field(
            description = "The classification of the user's last message"
        )

    modelWithTool = model.bind_tools(
        [ClassifyInput],
        tool_choice="ClassifyInput"
    )

    def evaluateUserInput_Node(state: patientState):

        """
        This node evaluates the user (Doctor's) input to decide whether the doctor is giving
        a prescription or whether he's asking more info about the disease.

        Tried to implement manually but this is a much better way.
        """

        lastUserMessage = state["chatHistory"][-1].content
        
        evaluateUserPrompt = ChatPromptTemplate.from_messages([
            SystemMessage("You need to classify the user message. It is part of a medical conversation"),
            HumanMessagePromptTemplate.from_template("User Message: {input}")
        ])
        evaludateUserChain = evaluateUserPrompt | modelWithTool
        response = evaludateUserChain.invoke({
            "input": lastUserMessage
        })

        if not response.tool_calls:
            return {"last_classification": "questioning"} # Default FallBack if the AI gave lunatic answers
        
        toolCall = response.tool_calls[0]
        classification = toolCall["args"]["classification"]

        return {"last_classification": classification}
    
    def evaluateUserInput_condition(state: patientState):
        return state["last_classification"]
    

    # Function Calling to Evaluate LLM Output as to which symptoms are revealed and which are not
    class SymptomReport(BaseModel):
        symptomsMentioned: List[str] = Field(description="A list of symptoms")

    modelWithSymptomTool = model.bind_tools(
        [SymptomReport],
        tool_choice="SymptomReport"
    )

    def evaluateLLMResponse(state: patientState):

        """
        This node's job is to analyze the AI Output to see which symptoms it has revealed and mark those as such.
        Why? because LLM Reveals the symptoms in a conversation flow, so it is very hard to detect the revealed symptoms manually.
        Hence this node uses the LLM to classify it's own output.
        """
        lastMessage = state["chatHistory"][-1].content

        remainingSymptoms = state["symptomsRemaining"]
        if not remainingSymptoms:
            return {}

        evaluateLLMPrompt = ChatPromptTemplate.from_messages([
            SystemMessage("You need to analyze the given patient message for the symptoms that are mentioned in it that are also among the Symptom List: {symptomsRemaining}. You *must* use the 'SymptomReport' tool to list the symptoms that were mentioned. If no symptoms from the list were mentioned, use the tool and pass an empty list."),
            HumanMessagePromptTemplate.from_template("User Message: {input}")
        ])

        evaluateLLMChain = evaluateLLMPrompt | modelWithSymptomTool
        response = evaluateLLMChain.invoke({
            "input": lastMessage,
            "symptomsRemaining": ",".join(remainingSymptoms)
        })

        if not response.tool_calls:
            return {}
        
        tool_call = response.tool_calls[0]
        symptomMentioned = tool_call['args']["symptomsMentioned"]

        if not symptomMentioned:
            return {}
        
        return {
            "symptomsRevealed": list(
                set(state["symptomsRevealed"]).union(set(symptomMentioned))
            ),
            "symptomsRemaining": list(
                set(state["symptomsRemaining"]).difference(set(symptomMentioned))
            ),
            
        }

        
        



    def acceptTreatment(state: patientState):
        """
        This node is simple, when a prescription has been given, it directs the LLM to generate a 
        response corresponding to Doctor's Last Message.
        """
        lastUserMessage = state["chatHistory"][-1].content
        acceptTreatmentPrompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="You are {patientPersona}. You have been given a correct treatment. Thank the doctor and end the conversation"
            
            ),
            HumanMessagePromptTemplate.from_template("{input}")
        ])
        acceptTreatmentChain = acceptTreatmentPrompt | model 
        response = acceptTreatmentChain.invoke({"patientPersona": state["patientPersona"], "input":lastUserMessage})

        return {"chatHistory": [response]}
    




    # LangGraph Code

    workflow = StateGraph(patientState)

    workflow.add_node("initializePersona", initializePersona)
    workflow.add_node("evaluateUserInput", evaluateUserInput_Node)
    workflow.add_node("evaluateLLMResponse", evaluateLLMResponse)
    workflow.add_node("generatePatientResponses", generatePatientResponses)
    workflow.add_node("acceptTreatment", acceptTreatment)

    workflow.set_conditional_entry_point(
        routeInitialMessage,
        {
       "initialize": "initializePersona",
       "continue": "evaluateUserInput"
    }
    )

    workflow.add_edge("initializePersona", "evaluateUserInput")
    workflow.add_edge("generatePatientResponses", "evaluateLLMResponse")
    workflow.add_edge("evaluateLLMResponse", END)

    workflow.add_edge("acceptTreatment", END)

    workflow.add_conditional_edges(
    "evaluateUserInput",
    evaluateUserInput_condition,
    {
        "questioning": "generatePatientResponses",
        "prescribingTreatment": "acceptTreatment"
    }
)
    graph = workflow.compile(checkpointer=checkpointer)


# This is the main chatbot function that will be imported by the FastAPI
def getChatbotResponse(message, sessionId):

    if not CHATBOT_READY:
        yield "Internal Server Error: 500, Please Try Again Later"
        return
    
    if len(message) > 300:
        yield "Message too long. Please send a shorter message."
        logging.debug(f"Message Length Was More Than 300 Chars, sessionId: { sessionId} ")
        return
    
    try:
        logging.info(f"Message Received, Sesssion ID: { sessionId}")

        config = {"configurable": {"thread_id": sessionId}}
        for event in graph.stream({
            "chatHistory": [HumanMessage(content=message)]
        }, config):
            
            nodeName = next(iter(event))
            logging.info(f"{sessionId} EVENT: node={nodeName}")
            nodeOutput = event[nodeName]

            if not nodeOutput:
                continue

            if "chatHistory" in nodeOutput:
                response = nodeOutput["chatHistory"][-1]
                if isinstance(response, AIMessage):
                    yield response.content

    except Exception as e:
        logging.debug(f"Error Inside Graph: {e}")
        yield "Internal Server Error: 500, Please Try Again Later"
                        