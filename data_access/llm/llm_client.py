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
    def __init__(self):
        self.client = OpenAI()

    def generate_paragraph_chunk_information(self, chunk:ParagraphChunk, n_questions:int=3) -> dict:
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
            model="gpt-3.5-turbo-0125",
            messages=[{
                'role': 'user',
                'content': prompt
            }]
        )

        response_text = response.choices[0].message.content.strip()
        response_obj = json.loads(response_text)
        return response_obj




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
