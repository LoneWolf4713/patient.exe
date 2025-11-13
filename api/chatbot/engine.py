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

import asyncio
import redis

# LangGraph Imports:
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver

# Tool Inputs
import pydantic
from pydantic import BaseModel, Field
from typing import Literal


# Trying to import the Gemini API Key
from dotenv import load_dotenv
import os
load_dotenv()
apiKey = os.getenv("GEMINI_API_KEY")

kvURL = os.getenv("REDIS_URL")
checkpointer = None

if kvURL:
    print("Vercel KV URL Found. Using RedisSaver")
    try:
        redisClient = redis.from_url(kvURL)
        checkpointer = RedisSaver(conn=redisClient)
    except Exception as e:
        print(f"Error Connecting To Redis: {e}")
else:
    print("Couldn't Get Vercel KV URL, Can't Procede")
    apiKey = None




if apiKey and checkpointer:
    print("Both API Keys Loaded Nicely")
    model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite", temperature = 0.7, google_api_key = apiKey)

    # The Clipboard
    class patientState(TypedDict):
        patientPersona: str         # To give some personality
        disease: str                # particular disease our AI will have
        symptoms: list[str]         # list of three symptoms

        symptomsRevealed: list[str]
        symptomsRemaining: list[str]

        chatHistory: Annotated[list, operator.add]
        
        prescribedTreatment: str

        last_classification: str

    def routeInitialMessage(state: patientState):

        if "patientPersona" not in state or state["patientPersona"] is None:
            return "initialize"
        else:
            return "continue"
        

    def initializePersona(state: patientState):
        response = json.loads(model.invoke("You are a medical simulator. Generate a common, non-critical disease, a list of 3 progressive symptoms, and a brief one sentence persona for the patient (anxious, stoic, dramatic). Format as a JSON Object with keys: 'disease', 'symptoms' and 'persona'. DONOT OUTPUT IN MARKDOWN, ONLY JSON").content)
        return {
            "patientPersona": response["persona"],
            "disease": response["disease"],
            "symptoms": response["symptoms"],
            "symptomsRemaining": response["symptoms"],
            "symptomsRevealed": []
        }
    
    def generatePatientResponses(state: patientState):
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

        return {"chatHistory": [response]}



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


    

    print("Chatbot is ready. Type 'exit' to quit.")
    
    async def getChatbotResponse(message, sessionId):
        print("Message and Session ID: ", message,sessionId )
        config = {"configurable": {"thread_id": sessionId}}
        async for event in graph.astream({
            "chatHistory": [HumanMessage(content=message)]
        }, config):
            print("event: ", event)

            node_name = next(iter(event))
            node_output = event[node_name]

            if not node_output:
                continue


            if "chatHistory" in node_output:
                print("chatHistory is in event")
                response = node_output["chatHistory"][-1]
                print(response.content)
                if isinstance(response, AIMessage):
                    print("hai bhai instance")
                    for word in response.content.split():
                        yield word
                        await asyncio.sleep(0.1) 
                    

    
else:
    if not apiKey:
        print("API Key Not Present, Cannot Procede")