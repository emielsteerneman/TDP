# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from abc import ABC, abstractmethod
import json
# Third party libraries
from dotenv import load_dotenv
load_dotenv()
import numpy as np
from openai import OpenAI
# Local libraries
from data_structures.TDPName import TDPName
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from MyLogger import logger


class LLMClient(ABC):
    @abstractmethod
    def generate_paragraph_chunk_information(self, chunk:ParagraphChunk, text:str=None, n_questions:int=3) -> dict:
        pass

class OpenAIClient(LLMClient):

    # Costs per token
    api_costs = {
        "gpt-3.5-turbo-0125": {
            "input": 0.50 / 1e6,
            "output": 1.50 / 1e6
        },
        "gpt-4o": {
            "input": 5.00 / 1e6,
            "output": 15.00 / 1e6
        },
        "gpt-4o-2024-05-13": {
            "input": 5.00 / 1e6,
            "output": 15.00 / 1e6
        }
    }

    def __init__(self):
        self.client = OpenAI()
        self.total_costs = 0

    def generate_paragraph_chunk_information(self, chunk:ParagraphChunk, n_questions:int=3, model="gpt-3.5-turbo-0125") -> dict:
        """
        Generate information about a paragraph using OpenAI's LLM.
        """
        
        prompt = (
            f"Analyze the following paragraph and provide a response in JSON format with two fields: "
            # f"'summary' (a brief summary of the paragraph), "
            f"'questions_specific' (a list of {n_questions} questions or less that the paragraph would answer, specifically for this league team year). "
            f"'questions_generic' (a list of {n_questions} questions or less that the paragraph would answer, without referencing team specifics or source specifics). "
            # f"'keywords' (a list of important keywords from the paragraph), "
            # f"'domain_specific' (a list of domain-specific words from the paragraph, that could be unknown to any reader or dictionary). "
            f"Keep in mind that the questions should be useful. Ensure that questions are specific. For example, say 'ball sensor' instead of 'sensor', or 'dribbler motor' instead of 'motor'."
            f"It is better to have fewer questions that are more useful than more questions that are less useful or too obvious. "
            f"The source of the following paragraph is as follows: league={chunk.tdp_name.league.name_pretty}, team={chunk.tdp_name.team_name.name_pretty}, year={chunk.tdp_name.year}."
            f"\n\n"
            f"Paragraph: {chunk.text}"
        )

        response = self.client.chat.completions.create(
            model=model,
            messages=[{
                'role': 'user',
                'content': prompt
            }]
        )

        self.total_costs += response.usage.prompt_tokens * self.api_costs[response.model]["input"]
        self.total_costs += response.usage.completion_tokens * self.api_costs[response.model]["output"]

        response_text = response.choices[0].message.content.strip()
        # if response_text.startswith("json"): response_text = response_text[4:]
        # response_text = response_text.replace("```", "")
        # Trim from first '{' to last '}'
        response_text = response_text[response_text.find("{"):response_text.rfind("}")+1]

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode response from OpenAI: {response_text}")
            return {}

    def answer_question(self, question:str, source_text:str, model="gpt-3.5-turbo-0125") -> str:
        """
        Ask a question about a source text using OpenAI's LLM.
        """
        system_role = f"You are a helpful and knowledgeable assistant. You will be asked a question from a participant in "
        f"the Robocup. The RoboCup is an international scientific initiative with the goal to advance the state of the art of intelligent robots. "
        f"Every year, teams from all over the world compete in various robot leagues and robot soccer matches. The Robocup is all about "
        f"sharing knowledge, collaboration, and friendly competition. You are a helpful and knowledgeable assistant. "
        f"You will be given a question and a list of paragraphs. Answer the question based on the information in the paragraphs. "
        f"Always cite the team and year and number of the source paragraph for every piece of information you provide. "
        f"Your answer should be concise and to the point. If you don't know the answer, you can say 'I don't know'."
        f"The answer should encourage the participant to do its own research. Maybe ask a question back to the participant or suggest follow-up research. "
        f"Again, it is absolutely important to always cite the source of your information. Always provide the paragraph title."

        messages = [
            {
                'role': 'system',
                'content': system_role
            },
            {
                'role': 'user',
                'content': "For each paragraph given, answer the following question (ignore paragraphs without relevant data): " + question
            },
            {
                'role': 'user',
                'content': source_text
            }
        ]

        response = self.client.chat.completions.create(
            model=model,
            messages=messages
        )

        if response.model in self.api_costs:
            cost_input = response.usage.prompt_tokens * self.api_costs[response.model]["input"]
            cost_output = response.usage.completion_tokens * self.api_costs[response.model]["output"]
            self.total_costs += cost_input + cost_output
            logger.info(f"tokens in: {response.usage.prompt_tokens}, tokens out: {response.usage.completion_tokens}, cost in: {cost_input}, cost out: {cost_output}")
        else:
            logger.error(f"Model {response.model} not found in API costs")

        # print(response)

        return response.choices[0].message.content.strip()


def main():
    """
    Main interaction loop for the chatbot.
    """
    print("Welcome to Chatbot! Type 'quit' to exit.")
    
    # Initialize the conversation history with a system message
    conversation_history = [
        {
            'role': 'system',
            'content': 'You are a helpful and knowledgeable assistant. When given a paragraph, you will provide a summary, a list of questions the paragraph would answer, and a list of keywords in JSON format.'
        }
    ]

    user_input = ""
    while user_input.lower() != "quit":
        user_input = input("You: ")

        if user_input.lower() != "quit":
            response = chat_with_openai(user_input, conversation_history)
            print(f"Chatbot: {response}")

def chat_with_openai(prompt, conversation_history):
    """
    Sends the prompt to OpenAI API using the chat interface and gets the model's response.
    Maintains conversation history for context.
    """
    # Add the user message to the conversation history
    conversation_history.append({
        'role': 'user',
        'content': prompt
    })

    # Create the prompt for the specific task
    specific_task_prompt = (
        f"The source of the following paragraph is as follows: league='soccer smallsize', team='GreenTea', year='2023'."
        f"Analyze the following paragraph and provide a response in JSON format with five fields: "
        f"'summary' (a brief summary of the paragraph), "
        f"'questions_specific' (a list of questions that the paragraph would answer, specifically for this team), "
        f"'questions_generic' (a list of questions that the paragraph would answer, without referencing team specifics), "
        f"'keywords' (a list of important keywords from the paragraph), "
        f"'domain_specific' (a list of domain-specific words from the paragraph)."
        f"\n\n"
        f"Paragraph: {prompt}"
    )

    conversation_history.append({
        'role': 'user',
        'content': specific_task_prompt
    })

    response = openai_client.chat.completions.create(
        model=model_name,
        messages=conversation_history
    )

    # Extract the chatbot's message from the response.
    chatbot_response = response.choices[0].message.content.strip()
    
    # Add the chatbot's response to the conversation history
    conversation_history.append({
        'role': 'assistant',
        'content': chatbot_response
    })

    return chatbot_response

if __name__ == "__main__":
    model_name = "gpt-3.5-turbo-0125"
    openai_client = OpenAI()
    main()
