import pandas as pd
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import OpenAI
import time
import requests
import os
from datetime import datetime
from src.models import ManagerCommand, State, ResearchState, AnalyticsState, SynthersizerState
from dotenv import load_dotenv
load_dotenv()

# --------------------------------------------
#              Manager Agent
# --------------------------------------------


def get_data_summary(data_path):

    file_name, file_extension = os.path.splitext(data_path)
    if file_extension == ".xlsx":
        df = pd.read_excel(data_path)
    elif file_extension == ".csv":
        df = pd.read_csv(data_path)
    else:
        raise ValueError("Unsupported file extension")

    with open('info_output.txt','w') as file_out:
        df.info(buf=file_out)

    with open('info_output.txt','r') as file_in:
        summary = file_in.read()

    return summary


def manager_command(state: State):

    manager = ChatOpenAI(model='gpt-4o-mini', temperature=0.0).with_structured_output(ManagerCommand)

    business_profile = state["business_profile"]
    data_path = state["data_path"]
    data_summary = get_data_summary(data_path)

    sys_prompt = "You are the manager of business consulting team. You have at your command research specialist \
               that can look up industry standards and practices and a data analytics expert that can analyze data and draw valuable insights. \
               You must give them the instructions on what to do. Each one needs a task and a standard so they know what the task needs to be accomplished \
               and a certain focus or emphasis to take into account while accomplishing the tasks.\
               The client will provide you with information about their business and you must use that to create the appropriate instructions for \
               your team in order to get valuable and actionable insights for the client. Keep the instructions simple, concise and to the point."

    user_prompt = f"The client specified having the following business profile: {state['business_profile']} \n \
              His goal while using our consulting services is the following: {state['goal']} \
              He also uploaded tabular data with the path {state['data_path']}. This is a summary of it: {data_summary}"

    manager_command = manager.invoke(
        [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt)
        ]
    )

    return {"research_instructions": manager_command.research_instructions, "analytics_instructions": manager_command.analytics_instructions}


# --------------------------------------------
#              Research Agent
# --------------------------------------------

def simplify_prompt(prompt, client):

    input_text = f"""I'll provide you with a prompt that caused the OpenAI's o3-deep-research model to have a Rate Limit 
    Error for exceeding the 200k token limit. Your goal is to simplify the task in the prompt such that it makes it less 
    likely to have the model performing so many actions that it exceeds the rate limit. You need to do this without 
    compromising the quality of the prompt, the essence of the task or the main goal of the prompt.
    Return ONLY the modified prompt for the model with no additional comments.
    Here's the prompt you need to simplify:
    {prompt}"""

    response = client.responses.create(
            model="gpt-4o-mini",
            input=input_text,
        )
    return response.output_text

def research(state: ResearchState):

    client = OpenAI(timeout=3600)

    def get_research_data(input_text):

        #You should consider these standards for the tasks to be accomplished: {state["research_instructions"].standards}
        response = client.responses.create(
            model="o3-deep-research",
            #model="o4-mini-deep-research",
            input=input_text,
            background=False,
            tools=[
                {"type": "web_search"},
                {
                    "type": "code_interpreter",
                    "container": {"type": "auto"}
                },
            ],
        )

        return response

    response = None
    max_attempts = 3
    attempt = 0
    input_text = f"""You have this task: {state["research_instructions"].tasks}
            You should accomplish it while mainting this focus: {state["research_instructions"].focus}
            """
    # When given complex tasks, the model is likely to do so much it runs out of tokens
    # Therefore, we write a retry system that simplifies the prompt/task for the model on each attempt
    while response is None and attempt < max_attempts:
        print(f"Attempt {attempt}")
        try:
            print(f"Trying prompt: {input_text}")
            start = datetime.now()
            response = get_research_data(input_text)
            print("Research Latency:", datetime.now() - start)
        except Exception as e:
            print(f"Error: {e}; Trying again")
            response = None
            input_text = simplify_prompt(input_text, client)
            attempt += 1
            time.sleep(2)

    return {"research_report": response.output_text}


# --------------------------------------------
#              Analytics Agent
# --------------------------------------------

def get_graph_from_agent(response):


    container_id = ""
    container_file_id = ""
    container_filename = "no.no"
    for item in response.output:
      try:
        container_id = item.content[0].annotations[0].container_id
        container_file_id = item.content[0].annotations[0].file_id
        container_filename = item.content[0].annotations[0].filename
        print("Succesful Item")
        print(item)
      except Exception as e:
        pass

    _, file_extension = os.path.splitext(container_filename)
    is_image = file_extension in [".png", ".jpg", ".jpeg"]
    if container_id and container_file_id and is_image:

        OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

        url = f"https://api.openai.com/v1/containers/{container_id}/files/{container_file_id}/content"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        response = requests.get(url, headers=headers)

        binary_data = response.content

        # Example: save to disk
        local_file_path = "graph.png"
        with open(local_file_path, "wb") as f:
            f.write(binary_data)

        return local_file_path

    else:

        return None
    
def analytics(state: AnalyticsState):

    data_path = state["data_path"]
    client = OpenAI()

    upload_file = client.files.create(file=open(data_path, "rb"), purpose="user_data",
        expires_after={"anchor": "created_at", "seconds": 43200})

    file_id = upload_file.id

    instructions = f"""You have these tasks: {state["analytics_instructions"].tasks}
    You should accomplish them while mainting this focus: {state["analytics_instructions"].focus}
    
    If you generate in image like a histogram, do NOT use plt.show(), you NEED to use plt.savefig()
    and return the image as an output file. Rmember, you NEED TO SAVE the image.
    """

    #You should consider these standards for the tasks to be accomplished: {state["analytics_instructions"].standards}

    response = client.responses.create(
      model="gpt-4.1",
      tools=[{"type":"code_interpreter", "container": {"type":"auto", "file_ids":[file_id]}}],
      input=instructions
    )

    graph_file_path = get_graph_from_agent(response)

    return {"analytics_report": response.output_text, "graph_file_path": graph_file_path}


# --------------------------------------------
#              Synthesizer Agent
# --------------------------------------------

def synthesizer(state: State):

    business_profile = state["business_profile"]
    goal = state["goal"]
    research_report = state["research_report"]
    analytics_report = state["analytics_report"]
    graph_file_path = state["graph_file_path"]

    client = OpenAI()

    information_prompt = f"""You are a business advisor/consultant. Your client has the followwing busines profile:
        {business_profile}
        He has hired you to accomplish the following goal: {goal}
        In your team you have a research specialist and an analytics specialist
        The research specialist has produced this report: {research_report} \n ---------------
        The analytics specialist has produced, based on tabular data provided by the client, this report: {analytics_report}
        """

    command_prompt = """You need to use all this information to produce a report with valuable and actionable insights for the client. 
        Remember, the report needs to effectively communicate insights about the clients business and state action items that can 
        help the client accomplish his goal. Do NOT include any additional suggestions or questions in your answer. Only produce the 
        report wihtout anything else, as if it was ready to be officially printed."""

    if graph_file_path:

        # Function to create a file with the Files API
        with open(graph_file_path, "rb") as file_content:
            result = client.files.create(
                file=file_content,
                purpose="vision",
            )
        file_id = result.id

        information_prompt += "The anlytics specialist has produced a graph that'll be provided for you."
        user_prompt = information_prompt + command_prompt

        inputs = [{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_prompt},
                    {
                        "type": "input_image",
                        "file_id": file_id,
                    },
                ],
            }]
        
    else:

        inputs = information_prompt + command_prompt

    response = client.responses.create(
        model="gpt-5",
        input=inputs
    )
    
    return {"final_report": response.output_text, "graph_file_path": graph_file_path}