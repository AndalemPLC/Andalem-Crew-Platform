from ansi2html import Ansi2HTMLConverter
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from crewai import Agent, Crew, Process, Task
from crewai_tools import ScrapeWebsiteTool, SeleniumScrapingTool, SerperDevTool, WebsiteSearchTool
from custom_tools.custom_tools import AndalemWebScrapeAndSearchTool, UserInputTool, YouTubeTranscriptionTool
from dotenv import find_dotenv, load_dotenv
from io import StringIO
from langchain_community.llms import ollama
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import ChatOpenAI
import logging
import os
import streamlit as st
from streamlit import _bottom
import sys
from textual_resources.input_field_tooltips import InputFieldTooltips
from textual_resources.openai_exceptions import OpenAIExceptions
from utilities.custom_styles import CustomStyles
import utilities.dialogs as dialogs 
from utilities.streamlit_tweaker import st_tweaker
import uuid

_ = load_dotenv(find_dotenv())
app_name = os.getenv('App_Name')
app_version = os.getenv('App_Version')

os.environ['NVIDIA_API_KEY'] = os.getenv('NVIDIA_API_Key')
os.environ['OPENAI_API_KEY'] = os.getenv('OpenAI_API_Key')

def initialize_app():

  st.session_state.custom_style = CustomStyles.custom_style

  st.session_state.agent_tooltips = InputFieldTooltips.agent_tooltips

  st.session_state.task_tooltips = InputFieldTooltips.task_tooltips

  st.session_state.crew_tooltips = InputFieldTooltips.crew_tooltips

  if 'logger' not in st.session_state:

    st.session_state.logger = logging.getLogger(__name__)
    st.session_state.logger.setLevel(logging.ERROR)
    st.session_state.logger.propagate = False

    logging_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s') 

    logging_file_handler = logging.FileHandler('./logs/platform_log.log')
    logging_file_handler.setLevel(logging.ERROR)
    logging_file_handler.setFormatter(logging_formatter) 

    logging_stdout_handler = logging.StreamHandler(sys.stdout)
    logging_stdout_handler.setLevel(logging.ERROR)
    logging_stdout_handler.setFormatter(logging_formatter)

    if not st.session_state.logger.hasHandlers():

      st.session_state.logger.addHandler(logging_file_handler)
      st.session_state.logger.addHandler(logging_stdout_handler)  

  if 'agents_settings' not in st.session_state:

    st.session_state.agents_settings = []

  if 'tasks_settings' not in st.session_state:

    st.session_state.tasks_settings = []  

  if 'crew_settings' not in st.session_state:

    st.session_state.crew_settings = {}

  st.session_state.saved_crews_directory = './saved_crews'
  
  st.session_state.tools_choices = ['Andalem Web Scrape and Search Tool',
                                    'DuckDuckGo Search Tool',
                                    'Google Serper Search Tool',
                                    'Selenium Scrape Tool',
                                    'User Input Tool',
                                    'Web Page Scrape Tool',
                                    'Website Search Tool',
                                    'YouTube Transcription Tool']
  
  st.session_state.llm_choices = ['DBRX 132B',
                                  'Gemma 7B',
                                  'Llama 3 8B',
                                  'Llama 3 8B Dolphin',
                                  'Mistral 7B',
                                  'Mistral 7B Dolphin',
                                  'Mixtral 8 X 7B',
                                  'Mixtral 8 X 7B Dolphin',
                                  'NVIDIA Llama 3 70B Instruct',
                                  'NVIDIA Mistral Large',
                                  'NVIDIA Mixtral 8 X 22B Instruct',
                                  'NVIDIA Nemotron 4 340B Instruct',
                                  'OpenAI GPT 3.5 Turbo',
                                  'OpenAI GPT 3.5 Turbo 0125',
                                  'OpenAI GPT 4',
                                  'OpenAI GPT 4O',
                                  'Openhermes',
                                  'Phi 3 Mini 3.8B',
                                  'WizardLM 2 7B',
                                  'Zephyr 7B']
  
  if 'show_verbose_output_on_ui' not in st.session_state:

    st.session_state['show_verbose_output_on_ui'] = True

  if 'current_crew' not in st.session_state:

    st.session_state['current_crew'] = ''

  if 'crew_saved' not in st.session_state:

    st.session_state['crew_saved'] = False
        
def initialize_page():

  st.set_page_config(page_title = app_name, 
                     page_icon = './app_images/andalem-icon.png', 
                     layout = 'wide', 
                     initial_sidebar_state = 'auto')

  st.markdown(st.session_state.custom_style, unsafe_allow_html = True)

  st_tweaker.image('./app_images/andalem-logo-with-motto.png', cls = 'app-logo', width = 245)

  st.write(f'<span class="app-name">{app_name} {app_version}</span>', unsafe_allow_html = True)

  if st.session_state['crew_saved']:

    st.toast('Your crew has been saved!') 

    st.session_state['crew_saved'] = False

  top_section_columns =  st.columns((1, 1, 1, 1), gap = 'small')

  with top_section_columns[0]:

    st.button('Add Agent',
              use_container_width = True, 
              on_click = add_agent,
              key = 'add_agent_button')

  if len(st.session_state.agents_settings) > 0:

    st.write(f'<span class="number-of-agents">Number of Agents in Crew: {len(st.session_state.agents_settings)}</span>', unsafe_allow_html = True)

  for agent_settings in st.session_state.agents_settings:

    agent_tasks_settings = []

    for task_settings in st.session_state.tasks_settings:

      if task_settings['agent_id'] == agent_settings['agent_id']:

        agent_tasks_settings.append(task_settings)

    load_agent_settings(agent_settings, agent_tasks_settings)

  if len(st.session_state.agents_settings) > 0: 

    load_crew_settings(st.session_state.crew_settings)

    output_preference_section_columns =  st.columns((1, 1, 1, 1), gap = 'small')

    with output_preference_section_columns[0]:

      st.checkbox('Show Verbose Output on UI',
                  value = True,
                  key = 'show_verbose_output_on_ui')

  st.session_state.work_process_container = st.empty() 

  st.session_state.user_input_container = st.empty()

  st.session_state.output_container = st.empty()

  bottom_section_columns = _bottom.columns((1, 1, 1, 1), gap = 'small')
  
  with bottom_section_columns[0]:

    if st.button('Run Crew', 
                 use_container_width = True, 
                 key = 'run_crew_button'):
      
      if len(st.session_state.agents_settings) > 0:
        
        validate()

      else:

        dialogs.show_error_dialog('There is no crew to run! Add at least one agent.')

  with bottom_section_columns[1]:

    if st.button('Save Crew', 
                 use_container_width = True, 
                 key = 'save_crew_button'): 
      
      if len(st.session_state.agents_settings) > 0:

        try:

          os.makedirs(st.session_state.saved_crews_directory, exist_ok = True)

          saved_crews_directory_files = os.listdir(st.session_state.saved_crews_directory)
    
        except Exception as exception:

          dialogs.show_error_dialog('There wan an error reading saved crews directory! Check the log for details')

          st.session_state.logger.error(f'There wan an error reading saved crews directory: {str(exception)}') 

        dialogs.show_save_crew_dialog(saved_crews_directory_files, st.session_state.saved_crews_directory, st.session_state['current_crew'])        

      else:

        dialogs.show_error_dialog('There is no crew to save! Add at least one agent.')

  with bottom_section_columns[2]:

    if st.button('Remove Crew',
                 type = 'primary',
                 use_container_width = True, 
                 key = 'remove_crew_button'):

      if len(st.session_state.agents_settings) > 0:

        dialogs.show_remove_dialog('Crew', None, None, 'Are you sure you wish to remove this crew?')

      else:

        dialogs.show_error_dialog('There is no crew to remove!') 

  with bottom_section_columns[3]:

    if st.button('Load Crew', 
                 use_container_width = True,
                 key = 'load_crew_button'):
      
      try:

        os.makedirs(st.session_state.saved_crews_directory, exist_ok = True)

        saved_crews_directory_files = os.listdir(st.session_state.saved_crews_directory)
  
      except Exception as exception:

        dialogs.show_error_dialog('There wan an error reading saved crews directory! Check the log for details')

        st.session_state.logger.error(f'There wan an error reading saved crews directory: {str(exception)}') 

      dialogs.show_load_crew_dialog(saved_crews_directory_files, st.session_state.saved_crews_directory) 

def add_agent():

  agent_id = generate_unique_agent_id()

  agent_settings = {'agent_id': agent_id, 
                    'agent_name': """""", 
                    'agent_role': """""", 
                    'agent_goal': """""", 
                    'agent_backstory': """""", 
                    'agent_verbosity': 'True',
                    'agent_delegation': 'False', 
                    'agent_tools': [], 
                    'agent_llm': 'Llama 3 8B',
                    'agent_llm_temperature': 0.50, 
                    'agent_max_rpm': 50,
                    'agent_max_iter': 15,
                    'agent_memory': 'False'}
  
  if len(st.session_state.agents_settings) == 0:

    crew_settings = {'crew_name': """""",
                     'crew_description': """""",
                     'crew_verbosity': 'True',  
                     'crew_max_rpm': 50,
                     'crew_memory': 'False',
                     'crew_full_output': 'True',
                     'crew_process': 'Sequential',
                     'crew_manager_llm': '',
                     'crew_manager_llm_temperature': 0.50,} 
    
    st.session_state.crew_settings = crew_settings 

  st.session_state.agents_settings.append(agent_settings)

  add_task(agent_id)

def add_task(agent_id):

  task_number = generate_task_number(agent_id)

  task_settings = {'agent_id': agent_id,
                   'task_number': task_number,
                   'task_human_input': 'False',
                   'task_description': """""",
                   'task_expected_output': """"""} 
  
  st.session_state.tasks_settings.append(task_settings)

def generate_unique_agent_id():

  unique_id = uuid.uuid4()

  agent_id = ((str(unique_id).replace('-', '')))[:4]

  existing_agent_ids = []

  for agent_settings in st.session_state.agents_settings:

    existing_agent_ids.append(agent_settings['agent_id'])

  if agent_id in existing_agent_ids:

    generate_unique_agent_id()

  else:

    return agent_id
  
def generate_task_number(agent_id):

  agent_tasks = []

  for task_settings in st.session_state.tasks_settings:

    if task_settings['agent_id'] == agent_id:

      agent_tasks.append(task_settings)

  return len(agent_tasks) + 1    

def load_agent_settings(agent_settings, agent_tasks_settings):

  agent_id = agent_settings['agent_id']

  number_of_tasks = len(agent_tasks_settings)

  agent_settings_container = st.empty()

  with agent_settings_container.expander(f'Agent {agent_id.upper()} Settings', expanded = False):

    agent, task = st.tabs(['Agent', f'Tasks ({number_of_tasks})' if number_of_tasks > 1 else f'Task ({number_of_tasks})'])

    with agent:

      with st.container(border = True):

        row_1_columns =  st.columns((1, 1), gap = 'small')

        with row_1_columns[0]:

          agent_settings['agent_name'] = st.text_input('Name: *', 
                                                       agent_settings['agent_name'],
                                                       max_chars = 75,
                                                       help = st.session_state.agent_tooltips['agent_name'],
                                                       key = f'agent_{agent_id}_name')

        row_2_columns =  st.columns((1, 1), gap = 'small')

        with row_2_columns[0]: 

          agent_settings['agent_role'] = st.text_area('Role: *',
                                                      agent_settings['agent_role'],
                                                      height = 50,
                                                      help = st.session_state.agent_tooltips['agent_role'],
                                                      key = f'agent_{agent_id}_role')

        with row_2_columns[1]:      

          agent_settings['agent_goal'] = st.text_area('Goal: *',
                                                      agent_settings['agent_goal'],
                                                      height = 50,
                                                      help = st.session_state.agent_tooltips['agent_goal'],
                                                      key = f'agent_{agent_id}_goal')

        agent_settings['agent_backstory'] = st.text_area('Backstory: *', 
                                                         agent_settings['agent_backstory'],
                                                         height = 150, 
                                                         help = st.session_state.agent_tooltips['agent_backstory'],
                                                         key = f'agent_{agent_id}_backstory')
        
        row_4_columns =  st.columns((1, 1), gap = 'small')

        with row_4_columns[0]:

          agent_settings['agent_verbosity'] = st.selectbox('Verbose: *',
                                                           options = ('False', 'True'), 
                                                           index = ('False', 'True').index(agent_settings['agent_verbosity']),
                                                           help = st.session_state.agent_tooltips['agent_verbosity'],
                                                           key = f'agent_{agent_id}_verbosity')
          
        with row_4_columns[1]:

          if len(st.session_state.agents_settings) == 1: 

            for agent in st.session_state.agents_settings:
                    
              if agent['agent_id'] == str(agent_id):

                agent['agent_delegation'] = 'False'

            agent_settings['agent_delegation'] = 'False'
        
            agent_settings['agent_delegation'] = st.selectbox('Allow Delegation: *', 
                                                              options = ('False', 'True'), 
                                                              index = ('False', 'True').index(agent_settings['agent_delegation']),
                                                              help = st.session_state.agent_tooltips['agent_delegation'],
                                                              disabled = True,
                                                              key = f'agent_{agent_id}_delegation')
            
          else:

            agent_settings['agent_delegation'] = st.selectbox('Allow Delegation: *', 
                                                              options = ('False', 'True'), 
                                                              index = ('False', 'True').index(agent_settings['agent_delegation']),
                                                              help = st.session_state.agent_tooltips['agent_delegation'],
                                                              disabled = False,
                                                              key = f'agent_{agent_id}_delegation')

        agent_settings['agent_tools'] = st.multiselect('Tools:', 
                                                       options = st.session_state.tools_choices, 
                                                       default = agent_settings['agent_tools'],
                                                       placeholder = 'Select Tools . . .', 
                                                       help = st.session_state.agent_tooltips['agent_tools'],
                                                       key = f'agent_{agent_id}_tools')
        
        row_6_columns =  st.columns((1, 1), gap = 'small')

        with row_6_columns[0]:
        
          agent_settings['agent_llm'] = st.selectbox('LLM: *', 
                                                     options = st.session_state.llm_choices, 
                                                     index = st.session_state.llm_choices.index(agent_settings['agent_llm']),
                                                     help = st.session_state.agent_tooltips['agent_llm'],
                                                     key = f'agent_{agent_id}_llm')

        with row_6_columns[1]:

          agent_settings['agent_llm_temperature'] = st.slider('Temperature: *', 
                                                              min_value = 0.00,
                                                              max_value = 1.00, 
                                                              value = agent_settings['agent_llm_temperature'],
                                                              step = 0.01,
                                                              help = st.session_state.agent_tooltips['agent_llm_temperature'],
                                                              key = f'agent_{agent_id}_llm_temperature') 

        row_7_columns =  st.columns((1, 1, 1), gap = 'small') 

        with row_7_columns[0]:

          agent_settings['agent_max_rpm'] = st.number_input('Maximum Requests Per Minute: *', 
                                                            min_value = 0,
                                                            max_value = 100, 
                                                            value = agent_settings['agent_max_rpm'],
                                                            step = 1,
                                                            help = st.session_state.agent_tooltips['agent_max_rpm'],
                                                            key = f'agent_{agent_id}_max_rpm') 

        with row_7_columns[1]: 

          agent_settings['agent_max_iter'] = st.number_input('Maximum Iterations: *', 
                                                             min_value = 1,
                                                             max_value = 100, 
                                                             value = agent_settings['agent_max_iter'],
                                                             step = 1,
                                                             help = st.session_state.agent_tooltips['agent_max_iter'],
                                                             key = f'agent_{agent_id}_max_iter')

        with row_7_columns[2]:

          agent_settings['agent_memory'] = st.selectbox('Memory: *', 
                                                        options = ('False', 'True'), 
                                                        index = ('False', 'True').index(agent_settings['agent_memory']), 
                                                        help = st.session_state.agent_tooltips['agent_memory'],
                                                        key = f'agent_{agent_id}_memory') 

    with task:

      agent_task_control_columns =  st.columns((1, 1, 2, 2), gap = 'small')

      with agent_task_control_columns[0]:

        st.button('Add Task',
                  use_container_width = True,
                  on_click = add_task,
                  args = [agent_id],
                  key = f'add_task_{agent_id}')

      for agent_task_settings in agent_tasks_settings:

        task_number = agent_task_settings['task_number']

        with st.container(border = True):

          st.write(f'Task {task_number}')

          row_1_columns =  st.columns((1, 1), gap = 'small') 

          with row_1_columns[0]:

            agent_task_settings['task_human_input'] = st.selectbox('Human Input: *', 
                                                                   options = ('False', 'True'), 
                                                                   index = ('False', 'True').index(agent_task_settings['task_human_input']), 
                                                                   help = st.session_state.task_tooltips['task_human_input'],
                                                                   key = f'agent_{agent_id}_task_{task_number}_human_input')      
          
          agent_task_settings['task_description'] = st.text_area('Task Description: *',
                                                                 agent_task_settings['task_description'], 
                                                                 height = 150, 
                                                                 help = st.session_state.task_tooltips['task_description'],
                                                                 key = f'agent_{agent_id}_task_{task_number}_task_description')
          
          agent_task_settings['task_expected_output'] = st.text_area('Expected Output: *',
                                                                     agent_task_settings['task_expected_output'],
                                                                     height = 25,
                                                                     help = st.session_state.task_tooltips['task_expected_output'],
                                                                     key = f'agent_{agent_id}_task_{task_number}_expected_output')
          
          if task_number != 1:
      
            task_control_columns =  st.columns((1, 1, 2, 2), gap = 'small') 

            with task_control_columns[0]:

              if st.button('Remove Task',
                           type = 'primary',
                           use_container_width = True,
                           key =f'remove_{agent_id}_task_{task_number}'):
                
                dialogs.show_remove_dialog('Task', agent_id, task_number, 'Are you sure you wish to remove this task?')

    agent_control_columns =  st.columns((1, 1, 2, 2), gap = 'small')      

    with agent_control_columns[0]:

      if st.button('Remove Agent',
                   type = 'primary', 
                   use_container_width = True,
                   key = f'remove_{agent_id}'):
        
        dialogs.show_remove_dialog('Agent', agent_id, None, 'Are you sure you wish to remove this agent?')   

def load_crew_settings(crew_settings):

  crew_settings_container = st.empty()

  with crew_settings_container.expander('Crew Settings', expanded = False):

    row_1_columns =  st.columns((1, 1), gap = 'small')

    with row_1_columns[0]:

      crew_settings['crew_name'] = st.text_input('Crew Name: *', 
                                                 crew_settings['crew_name'],
                                                 max_chars = 75,
                                                 help = st.session_state.crew_tooltips['crew_name'],
                                                 key = 'crew_name')
      
    crew_settings['crew_description'] = st.text_area('Crew Description: *',
                                                     crew_settings['crew_description'],
                                                     height = 25,
                                                     help = st.session_state.crew_tooltips['crew_description'],
                                                     key = 'crew_description') 

    row_3_columns =  st.columns((1, 1), gap = 'small') 

    with row_3_columns[0]:

      crew_settings['crew_verbosity'] = st.selectbox('Verbose: *', 
                                                     options = ('False', 'True'), 
                                                     index = ('False', 'True').index(crew_settings['crew_verbosity']), 
                                                     help = st.session_state.crew_tooltips['crew_verbosity'],
                                                     key = 'crew_verbosity') 

    with row_3_columns[1]:

      crew_settings['crew_max_rpm'] = st.number_input('Maximum Requests Per Minute: *', 
                                                      min_value = 0,
                                                      max_value = 100, 
                                                      value = crew_settings['crew_max_rpm'],
                                                      step = 1,
                                                      help = st.session_state.crew_tooltips['crew_max_rpm'],
                                                      key = 'crew_max_rpm')
      
    row_4_columns =  st.columns((1, 1), gap = 'small')

    with row_4_columns[0]:

      crew_settings['crew_memory'] = st.selectbox('Memory: *', 
                                                  options = ('False', 'True'), 
                                                  index = ('False', 'True').index(crew_settings['crew_memory']), 
                                                  help = st.session_state.crew_tooltips['crew_memory'],
                                                  key = 'crew_memory')

    with row_4_columns[1]:

      crew_settings['crew_full_output'] = st.selectbox('Full Output: *', 
                                                       options = ('False', 'True'), 
                                                       index = ('False', 'True').index(crew_settings['crew_full_output']), 
                                                       help = st.session_state.crew_tooltips['crew_full_output'],
                                                       key = 'crew_full_output')

    row_5_columns =  st.columns((1, 1, 1), gap = 'small')

    with row_5_columns[0]:

      crew_settings['crew_process'] = st.selectbox('Process: *', 
                                                  options = ('Hierarchical', 'Sequential'), 
                                                  index = ('Hierarchical', 'Sequential').index(crew_settings['crew_process']), 
                                                  help = st.session_state.crew_tooltips['crew_process'],
                                                  key = 'crew_process')

    with row_5_columns[1]:

      if crew_settings['crew_process'] == 'Hierarchical':

        crew_settings['crew_manager_llm'] = st.selectbox('Manager LLM: *', 
                                                         options = st.session_state.llm_choices, 
                                                         index = st.session_state.llm_choices.index(crew_settings['crew_manager_llm']) if crew_settings['crew_manager_llm'] else None, 
                                                         placeholder = 'Select Manager LLM . . .',
                                                         help = st.session_state.crew_tooltips['crew_manager_llm'],
                                                         disabled = False,
                                                         key = 'crew_manager_llm')

      else:

        st.session_state.crew_settings['crew_manager_llm'] = None

        crew_settings['crew_manager_llm'] = None

        crew_settings['crew_manager_llm'] = st.selectbox('Manager LLM: *', 
                                                         options = st.session_state.llm_choices, 
                                                         index = st.session_state.llm_choices.index(crew_settings['crew_manager_llm']) if crew_settings['crew_manager_llm'] else None, 
                                                         placeholder = 'Select Manager LLM . . .',
                                                         help = st.session_state.crew_tooltips['crew_manager_llm'],
                                                         disabled = True,
                                                         key = 'crew_manager_llm_disabled') 

    with row_5_columns[2]:

      if crew_settings['crew_process'] == 'Hierarchical':

        crew_settings['crew_manager_llm_temperature'] = st.slider('Temperature: *', 
                                                                  min_value = 0.00,
                                                                  max_value = 1.00, 
                                                                  value = crew_settings['crew_manager_llm_temperature'],
                                                                  step = 0.01,
                                                                  help = st.session_state.crew_tooltips['crew_manager_llm_temperature'],
                                                                  disabled = False,
                                                                  key = 'crew_manager_llm_temperature') 

      else:

        st.session_state.crew_settings['crew_manager_llm_temperature'] = 0.50

        crew_settings['crew_manager_llm_temperature'] = 0.50

        crew_settings['crew_manager_llm_temperature'] = st.slider('Temperature: *', 
                                                                  min_value = 0.00,
                                                                  max_value = 1.00, 
                                                                  value = crew_settings['crew_manager_llm_temperature'],
                                                                  step = 0.01,
                                                                  help = st.session_state.crew_tooltips['crew_manager_llm_temperature'],
                                                                  disabled = True,
                                                                  key = 'crew_manager_llm_temperature')                       

def validate():

  required_agent_settings_fields = ['agent_name', 'agent_role', 'agent_goal', 'agent_backstory'] 

  required_task_settings_fields = ['task_description', 'task_expected_output']
  
  required_crew_settings_fields = ['crew_name', 'crew_description']
  
  if st.session_state.crew_settings['crew_process'] == 'Hierarchical':

    required_crew_settings_fields.append('crew_manager_llm')

  invalid_agent_settings_fields = []

  for agent_settings in st.session_state.agents_settings:

    missing_agent_settings_fields = [((field.replace('_', ' ')).title()).replace('Llm', 'LLM') for field in required_agent_settings_fields if not agent_settings.get(field)]

    if missing_agent_settings_fields:
          
      invalid_agent_settings_fields.append((agent_settings, missing_agent_settings_fields))

  invalid_task_settings_fields = []

  for task_settings in st.session_state.tasks_settings:

    missing_task_settings_fields = [((field.replace('_', ' ')).title()).replace('Llm', 'LLM') for field in required_task_settings_fields if not task_settings.get(field)]

    if missing_task_settings_fields:
          
      invalid_task_settings_fields.append((task_settings, missing_task_settings_fields))

  invalid_crew_settings_fields = [((field.replace('_', ' ')).title()).replace('Llm', 'LLM') for field in required_crew_settings_fields if not st.session_state.crew_settings.get(field)]

  if len(invalid_agent_settings_fields) > 0 or len(invalid_task_settings_fields) > 0 or len(invalid_crew_settings_fields) > 0:

    dialogs.show_validation_dialog(invalid_agent_settings_fields, invalid_task_settings_fields, invalid_crew_settings_fields) 

  else:

    run_crew()   

def run_crew():

  with st.session_state.output_container:

    with st.session_state.output_container.expander('Output', expanded = True):

      with st.spinner('Configuring crew. Please wait . . .'):

        agents = []

        tasks = []

        for agent_settings in st.session_state.agents_settings:

          agent_id = agent_settings['agent_id'] 
          agent_name = agent_settings['agent_name']
          agent_role = agent_settings['agent_role']
          agent_goal = agent_settings['agent_goal'] 
          agent_backstory = agent_settings['agent_backstory'] 
          agent_verbosity = get_selected_boolean(agent_settings['agent_verbosity'])
          agent_delegation = get_selected_boolean(agent_settings['agent_delegation'])
          agent_tools = [] if not agent_settings['agent_tools'] else get_selected_tools(agent_settings['agent_tools'])
          agent_llm_temperature = agent_settings['agent_llm_temperature'] 
          agent_llm = get_selected_llm(agent_settings['agent_llm'], agent_llm_temperature, 'Agent')
          agent_max_rpm = get_max_rpm(agent_settings['agent_max_rpm'])
          agent_max_iter = agent_settings['agent_max_iter']
          agent_memory = get_selected_boolean(agent_settings['agent_memory'])

          globals()['agent_' + str(agent_id)] = Agent(role = agent_role,
                                                      goal = agent_goal,
                                                      backstory = agent_backstory,
                                                      verbose = agent_verbosity,
                                                      allow_delegation = agent_delegation,
                                                      tools = agent_tools,
                                                      llm = agent_llm,
                                                      max_rpm = agent_max_rpm,
                                                      max_iter = agent_max_iter,
                                                      memory = agent_memory)
          
          agents.append(globals()['agent_' + str(agent_id)])

        for task_settings in st.session_state.tasks_settings:

          task_agent_id = task_settings['agent_id']
          task_number = task_settings['task_number']
          task_human_input = get_selected_boolean(task_settings['task_human_input'])
          task_description = task_settings['task_description']
          task_expected_output = task_settings['task_expected_output'] 

          globals()['agent_' + str(task_agent_id) + '_task_' + str(task_number)] = Task(human_input = task_human_input,
                                                                                        description = task_description,
                                                                                        agent = globals()['agent_' + str(task_agent_id)],
                                                                                        expected_output = task_expected_output)
          
          tasks.append(globals()['agent_' + str(task_agent_id) + '_task_' + str(task_number)])

        crew_name = st.session_state.crew_settings['crew_name']
        crew_description = st.session_state.crew_settings['crew_description']
        crew_verbosity = get_selected_boolean(st.session_state.crew_settings['crew_verbosity'])
        crew_max_rpm = get_max_rpm(st.session_state.crew_settings['crew_max_rpm'])
        crew_memory = get_selected_boolean(st.session_state.crew_settings['crew_memory'])
        crew_full_output = get_selected_boolean(st.session_state.crew_settings['crew_full_output']) 
        crew_process = get_selected_process(st.session_state.crew_settings['crew_process'])        
        crew_manager_llm_temperature = st.session_state.crew_settings['crew_manager_llm_temperature']
        crew_manager_llm = get_selected_llm(st.session_state.crew_settings['crew_manager_llm'], crew_manager_llm_temperature, 'Manager') 

        crew = Crew(agents = agents,
                    tasks = tasks,
                    verbose = crew_verbosity,
                    max_rpm = crew_max_rpm,
                    memory = crew_memory,
                    full_output = crew_full_output,
                    process = crew_process,
                    manager_llm = crew_manager_llm)
        
      with st.spinner('Running crew. Please wait . . .'):

        try:

          if st.session_state['show_verbose_output_on_ui']:

            with st.session_state.work_process_container:

              with st.expander('Work Process', expanded = True):

                with capture_verbose_output(lambda output: display_verbose_output(output)):

                  output = crew.kickoff()

            if crew_full_output == True:      

              for task in tasks:

                st.markdown(get_final_output(task.output.description), unsafe_allow_html = True)

                st.markdown(get_final_output(task.output.raw_output), unsafe_allow_html = True)

            else:

              st.markdown(get_final_output(output), unsafe_allow_html = True)

          else:

            output = crew.kickoff()

            if crew_full_output == True:      

              for task in tasks:

                st.markdown(get_final_output(task.output.description), unsafe_allow_html = True)

                st.markdown(get_final_output(task.output.raw_output), unsafe_allow_html = True)

            else:

              st.markdown(get_final_output(output), unsafe_allow_html = True)

        except Exception as exception:

          error_message = None

          for error_type, message in OpenAIExceptions.error_messages.items():
              
            if isinstance(exception, error_type):
                
              error_message = message

              break
              
          if error_message:

            dialogs.show_error_dialog(error_message)

            st.session_state.logger.error(f'There wan an error running crew: {str(exception)}')

          else:
              
            dialogs.show_error_dialog('There wan an error running the crew! Check the log for details')

            st.session_state.logger.error(f'There wan an error running crew: {str(exception)}') 

          output = None             

def get_selected_boolean(selected_boolean):

  if selected_boolean == 'True':

    return True

  else:

    return False 
  
def get_selected_tools(selected_tools):

  try:

    tools = {'Andalem Web Scrape and Search Tool': AndalemWebScrapeAndSearchTool(),
             'DuckDuckGo Search Tool': DuckDuckGoSearchRun(),
             'Google Serper Search Tool': SerperDevTool(),
             'Selenium Scrape Tool': SeleniumScrapingTool(),
             'User Input Tool': UserInputTool(),
             'Web Page Scrape Tool': ScrapeWebsiteTool(),
             'Website Search Tool': WebsiteSearchTool(),
             'YouTube Transcription Tool': YouTubeTranscriptionTool()}

    agent_tools = []

    if selected_tools:

      for tool in selected_tools:

        agent_tools.append(tools[tool])

    return agent_tools
  
  except Exception as exception:

    dialogs.show_error_dialog('There wan an error loading tool! Check the log for details')

    st.session_state.logger.error(f'There wan an error loading tool: {str(exception)}')

def get_selected_llm(selected_llm, selected_temperature, type):

  nvidia_base_url = 'https://integrate.api.nvidia.com/v1'

  try:

    llms = {'DBRX 132B': ollama.Ollama(model = 'dbrx', temperature = selected_temperature),
            'Gemma 7B': ollama.Ollama(model = 'gemma', temperature = selected_temperature),
            'Llama 3 8B': ollama.Ollama(model = 'llama3', temperature = selected_temperature),
            'Llama 3 8B Dolphin': ollama.Ollama(model = 'dolphin-llama3', temperature = selected_temperature),
            'Mistral 7B': ollama.Ollama(model = 'mistral', temperature = selected_temperature),
            'Mistral 7B Dolphin': ollama.Ollama(model = 'dolphin-mistral', temperature = selected_temperature),
            'Mixtral 8 X 7B': ollama.Ollama(model = 'mixtral', temperature = selected_temperature),
            'Mixtral 8 X 7B Dolphin': ollama.Ollama(model = 'dolphin-mixtral', temperature = selected_temperature),
            'NVIDIA Llama 3 70B Instruct': ChatNVIDIA(model = 'meta/llama3-70b-instruct', temperature = selected_temperature, base_url = nvidia_base_url),
            'NVIDIA Mistral Large': ChatNVIDIA(model = 'mistralai/mistral-large', temperature = selected_temperature, base_url = nvidia_base_url),
            'NVIDIA Mixtral 8 X 22B Instruct': ChatNVIDIA(model = 'mistralai/mixtral-8x22b-instruct-v0.1', temperature = selected_temperature, base_url = nvidia_base_url),
            'NVIDIA Nemotron 4 340B Instruct': ChatNVIDIA(model = 'nvidia/nemotron-4-340b-instruct', temperature = selected_temperature, base_url = nvidia_base_url),
            'OpenAI GPT 3.5 Turbo': ChatOpenAI(model_name = 'gpt-3.5-turbo', temperature = selected_temperature),
            'OpenAI GPT 3.5 Turbo 0125': ChatOpenAI(model_name = 'gpt-3.5-turbo-0125', temperature = selected_temperature),
            'OpenAI GPT 4': ChatOpenAI(model_name = 'gpt-4', temperature = selected_temperature),
            'OpenAI GPT 4O': ChatOpenAI(model_name = 'gpt-4o', temperature = selected_temperature), 
            'Openhermes': ollama.Ollama(model = 'openhermes', temperature = selected_temperature),                
            'Phi 3 Mini 3.8B': ollama.Ollama(model = 'phi3', temperature = selected_temperature),
            'WizardLM 2 7B': ollama.Ollama(model = 'wizardlm2', temperature = selected_temperature),
            'Zephyr 7B': ollama.Ollama(model = 'zephyr', temperature = selected_temperature)}
    
    if type == 'Agent':

      llm_type = 'agent'
 
      agent_llm = llms[selected_llm]

      return agent_llm
    
    else:

      llm_type = 'manager'

      if st.session_state.crew_settings['crew_process'] == 'Sequential' or selected_llm == '' or None:

        return None

      else:  
 
        manager_llm = llms[selected_llm]

        return manager_llm
  
  except Exception as exception:

    dialogs.show_error_dialog(f'There wan an error loading {llm_type} LLM! Check the log for details')

    st.session_state.logger.error(f'There wan an error loading {llm_type} LLM: {str(exception)}')

def get_max_rpm(max_rpm):

  if max_rpm == 0:

    return None
  
  else:

    return max_rpm
  
def get_selected_process(selected_process):

  if selected_process == 'Hierarchical':

    return Process.hierarchical
  
  else:

    return Process.sequential

@contextmanager
def capture_verbose_output(output_function):

  with StringIO() as stdout, StringIO() as stderr, redirect_stdout(stdout), redirect_stderr(stderr):
        
    original_stdout_write = stdout.write

    original_stderr_write = stderr.write
    
    def redirect_output(string):
        
      redirected_output = original_stdout_write(string)

      output_function(string)

      return redirected_output
    
    def redirect_error_output(string):
        
      redirected_output = original_stderr_write(string)

      output_function(string)

      return redirected_output
    
    stdout.write = redirect_output

    stderr.write = redirect_error_output
    
    yield

def display_verbose_output(output):

  original_output = Ansi2HTMLConverter()

  converted_output = original_output.convert(output, full = True)

  st.markdown(converted_output, unsafe_allow_html = True)

def get_final_output(output):

  original_output = Ansi2HTMLConverter()

  converted_output = original_output.convert(output, full = True)

  return converted_output

if __name__ == '__main__': 

  initialize_app()

  initialize_page()