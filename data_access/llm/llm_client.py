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
        },
        "gpt-4o-mini": {
            "input": 0.15 / 1e6,
            "output": 0.60 / 1e6
        },
        "gpt-4o-mini-2024-07-18": {
            "input": 0.15 / 1e6,
            "output": 0.60 / 1e6
        },
    }

    def __init__(self):
        self.client = OpenAI()
        self.total_costs = 0

    def generate_paragraph_chunk_information(self, chunk:ParagraphChunk, n_questions:int=3, model="gpt-4o-mini") -> dict:
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

    def answer_question(self, question:str, source_text:str, model="gpt-4o-mini") -> str:
        """
        Ask a question about a source text using OpenAI's LLM.
        """
        # * Format sources as follows: ### {{team}} {{year}}, {{league}} : {{paragraph title}}
        system_role = f"""
You are a helpful and knowledgeable assistant. You will be asked a question from a participant in the RoboCup. The RoboCup is an international scientific initiative aimed at advancing the state of the art of intelligent robots. Teams from all over the world compete in various robot leagues and robot soccer matches. The RoboCup is about sharing knowledge, collaboration, and friendly competition.

Your task:
    * You will be given a question and a list of paragraphs.
    * Answer the question based on the information in the paragraphs.
    * Always cite the team, year, and number of the source paragraph for every piece of information you provide.
    * Your answer should be concise and to the point.
    * Encourage the participant to do their own research by asking follow-up questions or suggesting further reading.
    * Be exhaustive and detailed. Provide as much information as possible.
    * Respond in markdown format. 
    * Add a paragraph ### further research.
    * Add a paragraph ### summary.
    * Respond with at least 7500 characters.

Question: "{question}"

exhaustively answer the following question (ignore paragraphs without relevant data), and end with further research suggestions and a summary.
"""
# For each relevant paragraph given, exhaustively answer the following question (ignore paragraphs without relevant data), and end with further research suggestions and a summary.

        # Prepare the messages for the API call
        messages = [
            {
                'role': 'system',
                'content': system_role
            },
            {
                'role': 'user',
                'content': source_text
            }
        ]

        # Add the question as a separate message to maintain clarity
        messages.append({
            'role': 'user',
            'content': "For each paragraph given, answer the following question (ignore paragraphs without relevant data), and end with a summary: " + question
        })

        # The messages are now ready to be sent to the OpenAI API
        response = self.client.chat.completions.create(
            model=model,
            messages=messages
        )

        if response.model in self.api_costs:
            cost_input = response.usage.prompt_tokens * self.api_costs[response.model]["input"]
            cost_output = response.usage.completion_tokens * self.api_costs[response.model]["output"]
            self.total_costs += cost_input + cost_output
            logger.info(f"Model: {model}, tokens in: {response.usage.prompt_tokens}, tokens out: {response.usage.completion_tokens}, cost in: {cost_input}, cost out: {cost_output}")
        else:
            logger.error(f"Model {response.model} not found in API costs")

        # print(response)

        return response.choices[0].message.content.strip()