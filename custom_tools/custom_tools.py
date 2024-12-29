import asyncio
from bs4 import BeautifulSoup
from crewai_tools import BaseTool
import re
import requests
import streamlit as st
from typing import List
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi 
from youtube_transcript_api._errors import VideoUnavailable

class AndalemWebScrapeAndSearchTool(BaseTool): 
 
    name: str = "Web Scraper and Searcher Tool" 
 
    description: str = """ 
    This tool is used to scrape web pages and perform web searches. 
    The input should be a URL string for scraping or a search query string. 
    :param url: str, URL to scrape. 
    :param query: str, search query to perform a web search. 
    """ 
 
    async def _run(self, url: str = None, query: str = None) -> str: 

        try: 

            if url: 

                content = await self.scrape_website(url) 

                return content 
            
            elif query: 

                results = await self.perform_web_search(query)

                return '\n'.join(results) 
            
            else:

                return 'Invalid input: Either a URL or a search query must be provided.' 
            
        except Exception as exception: 

            return f'An error occurred: {exception}' 
 
    async def scrape_website(self, url: str) -> str: 

        try: 

            response = requests.get(url) 

            response.raise_for_status() 
            
            soup = BeautifulSoup(response.content, 'html.parser') 

            return soup.get_text(separator = '\n') 
        
        except requests.RequestException as exception: 

            return f'Failed to scrape the website: {exception}' 
 
    async def perform_web_search(self, query: str) -> List[str]: 

        search_url = f"https://www.google.com/search?q={query}" 

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'} 
 
        try: 

            response = requests.get(search_url, headers = headers) 

            response.raise_for_status() 

            soup = BeautifulSoup(response.content, 'html.parser') 

            results = []

            for content in soup.find_all('div', 'h1', 'h2', 'h3', class_ = 'article'): 

                results.append(content.get_text()) 

            return results 
        
        except requests.RequestException as exception: 

            return f'Failed to perform web search: {exception}'

class UserInputTool(BaseTool):

    name: str = "User Input Tool"

    description: str = "This tool is used to get information or input from the user that is vital for the task the agent has to perform."

    @st.experimental_fragment
    def _run(self, question: str) -> str:

        with st.session_state.user_input_container:

            with st.session_state.user_input_container.expander('User Input', expanded = True):

                if 'messages' not in st.session_state:

                    st.session_state['messages'] = [{'role': 'assistant', 'content': question}]

                for msg in st.session_state.messages:

                    st.chat_message(msg['role']).write(msg['content'])

                if user_input := st.chat_input():

                    st.session_state.messages.append({'role': 'user', 'content': user_input})

                    st.chat_message('user').write(user_input)  

                return user_input        
            
class YouTubeTranscriptionTool(BaseTool):

    name: str = "YouTube Transcription Tool"

    description: str = """
    This tool is used to get transcripts from the given URL.
    The input should be a YouTube URL string.
    :param youtube_url: str, YouTube URL to retrieve transcripts from.
    """

    async def _run(self, youtube_url: str) -> str:

        try:

            video_id = self.get_youtube_video_id(youtube_url)

            if not video_id:

                return 'Invalid YouTube URL'

            transcript = await self.get_transcript_with_retries(video_id)

            combined_transcript = ' '.join([item.get('text', '') for item in transcript])

            return combined_transcript
        
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as exception:

            return f'No transcripts available: {exception}'
        
        except Exception as exception:

            return f'An error occurred while fetching the transcript: {exception}'

    def get_youtube_video_id(self, url: str) -> str:

        """
        This function extracts the video ID from a YouTube URL.
        Args:
            url: The YouTube URL as a string.
        Returns:
            The extracted video ID as a string, or None if the URL is invalid.
        """

        pattern = r'(?:v=|be/|/watch\?v=|\?feature=youtu.be/|/embed/)([\w-]+)'

        match = re.search(pattern, url)

        if match:

            return match.group(1)
        
        else:

            return None

    async def get_transcript_with_retries(self, video_id: str, max_retries: int = 10) -> list:

        """
        This function fetches the transcript with retries and exponential backoff.
        Args:
            video_id: The YouTube video ID.
            max_retries: Maximum number of retries.
        Returns:
            The transcript as a list of dictionaries.
        """

        retries = 0

        backoff = 1

        while retries < max_retries:

            try:

                return YouTubeTranscriptApi.get_transcript(video_id)
            
            except Exception as exception:

                retries += 1

                if retries == max_retries:

                    raise exception
                
                await asyncio.sleep(backoff)

                backoff *= 2           