import json
import os
import re
import streamlit as st

@st.experimental_dialog('Error!')  
def show_error_dialog(message):

    st.error(message)

    if st.button('Close', use_container_width = True):
        
        st.rerun()

@st.experimental_dialog('Validation Error!')  
def show_validation_dialog(invalid_agent_settings_fields, invalid_task_settings_fields, invalid_crew_settings_fields):

    st.write('The following validation errors have occurred:') 

    with st.container(height = 250, border = True): 

        if len(invalid_agent_settings_fields):

            for agent_settings, missing_agent_settings_fields in invalid_agent_settings_fields:
                
                st.error(f"Agent {(agent_settings['agent_id']).upper()} is missing the following fields: {', '.join(missing_agent_settings_fields)}")

        if len(invalid_task_settings_fields):

            for task_settings, missing_task_settings_fields in invalid_task_settings_fields:
                
                st.error(f"Agent {(task_settings['agent_id']).upper()} Task {task_settings['task_number']} is missing the following fields: {', '.join(missing_task_settings_fields)}")

        if invalid_crew_settings_fields:
            
            st.error(f"Crew is missing the following fields: {', '.join(invalid_crew_settings_fields)}")

    if st.button('Close', use_container_width = True):
        
        st.rerun()       

@st.experimental_dialog('Save Crew') 
def show_save_crew_dialog(files, saved_crews_directory, current_crew_file_name):

    crew_files = [f"📜 {file.replace('.ancr', '')}" for file in files if os.path.isfile(os.path.join(saved_crews_directory, file)) and file.endswith('.ancr')]

    with st.container(height = 150, border = True): 

        for crew_file in crew_files:

            st.write(crew_file)

    file_name = st.text_input('File Name:', 
                              current_crew_file_name,
                              max_chars = 75,
                              key = 'file_name')

    overwrite_existing = st.checkbox('Overwrite Existing',
                                     value = False, 
                                     key = 'overwrite_existing')
  
    if overwrite_existing:
      
        st.warning('Note that you\'ve opted to overwrite any existing crew file of the same name')

    error_message_container = st.empty()

    dialog_buttons_columns =  st.columns((1, 1), gap = 'small')

    with dialog_buttons_columns[0]:

        if st.button('Save', use_container_width = True):

            crew_file_name = format_filename(file_name)

            if crew_file_name == '':

                with error_message_container:

                    st.error('No file name entered!')

            else:

                if crew_file_name in [file.replace('.ancr', '') for file in files if os.path.isfile(os.path.join(saved_crews_directory, file)) and file.endswith('.ancr')] and not overwrite_existing:

                    with error_message_container:

                        st.error('A crew file with the same name already exists! Enter a different file name or check the \'Overwrite Existing\' option')

                else:       

                    agents_tasks_and_crew_settings = {'agents_settings': st.session_state.agents_settings,
                                                      'tasks_settings': st.session_state.tasks_settings,
                                                      'crew_settings': st.session_state.crew_settings}
                    
                    try: 

                        crew_data = json.dumps(agents_tasks_and_crew_settings, indent = 4)

                        with open(os.path.join(st.session_state.saved_crews_directory, str(crew_file_name) + '.ancr'), 'w') as crew_file:

                            crew_file.write(crew_data)

                            st.session_state['current_crew'] = crew_file_name 

                            st.session_state['crew_saved'] = True

                        st.rerun() 

                    except Exception as exception:

                        with error_message_container:
            
                            st.error('There wan an error saving the crew! Check the log for details')

                            st.session_state.logger.error(f'There wan an error saving crew: {str(exception)}')

    with dialog_buttons_columns[1]:    

        if st.button('Cancel', use_container_width = True):

            st.rerun()                           

@st.experimental_dialog('Confirm Remove')  
def show_remove_dialog(remove_type, agent_id, task_number, message):

    st.warning(message)

    dialog_buttons_columns =  st.columns((1, 1), gap = 'small')

    with dialog_buttons_columns[0]:

        if st.button('Yes', type = 'primary', use_container_width = True):

            if remove_type == 'Crew':
               
                st.session_state.agents_settings.clear()

                st.session_state.tasks_settings.clear()

                st.session_state.crew_settings.clear()

                st.session_state['current_crew'] = ''

                st.rerun()

            elif remove_type == 'Agent':

                for agent_settings in st.session_state.agents_settings:

                    for task_settings in st.session_state.tasks_settings:

                        if task_settings['agent_id'] == str(agent_id):

                            st.session_state.tasks_settings.remove(task_settings)

                    if agent_settings['agent_id'] == str(agent_id):

                        if len(st.session_state.agents_settings) == 1:

                            st.session_state.tasks_settings.clear()

                            st.session_state.crew_settings.clear()

                            st.session_state['current_crew'] = ''

                        st.session_state.agents_settings.remove(agent_settings)
            
                st.rerun()

            else:

                for task_settings in st.session_state.tasks_settings:

                    if task_settings['agent_id'] == str(agent_id) and task_settings['task_number'] == int(task_number):

                        st.session_state.tasks_settings.remove(task_settings)
            
                st.rerun()                

    with dialog_buttons_columns[1]:    

        if st.button('No', use_container_width = True):

            st.rerun()

@st.experimental_dialog('Load Crew') 
def show_load_crew_dialog(files, saved_crews_directory):
  
    if len(st.session_state.agents_settings) > 0:
      
        st.warning('Note that the current unsaved crew you\'re working on will be lost when you load an existing crew')  

    st.write('Select the crew file you wish to load:') 

    with st.container(height = 150, border = True):  

        selected_file = st.radio('Select a crew file to load', 
                                 options = [f"📜 {file.replace('.ancr', '')}" for file in files if os.path.isfile(os.path.join(saved_crews_directory, file)) and file.endswith('.ancr')],
                                 index = None,
                                 label_visibility = 'collapsed') 

    error_message_container = st.empty()

    dialog_buttons_columns =  st.columns((1, 1), gap = 'small')

    with dialog_buttons_columns[0]:

        if st.button('Load', use_container_width = True):

            if selected_file:

                crew_file = selected_file.replace('📜 ', '')

                try:

                    with open(os.path.join(saved_crews_directory, str(crew_file) + '.ancr'), 'r') as file:

                        crew_data = json.load(file)

                        st.session_state.agents_settings.clear()

                        st.session_state.tasks_settings.clear()

                        st.session_state.crew_settings.clear()  
                        
                        st.session_state.agents_settings = crew_data['agents_settings']

                        st.session_state.tasks_settings = crew_data['tasks_settings']

                        st.session_state.crew_settings = crew_data['crew_settings']

                        st.session_state['current_crew'] = crew_file  

                    st.rerun()  

                except Exception as exception:

                    with error_message_container:
    
                        st.error('There wan an error loading the crew! Check the log for details')

                        st.session_state.logger.error(f'There wan an error loading crew: {str(exception)}')

            else:

                with error_message_container:

                    st.error('No crew selected!')

    with dialog_buttons_columns[1]:    

        if st.button('Cancel', use_container_width = True):

            st.rerun()

def format_filename(file_name):

    file_name = file_name.strip()
    
    file_name = file_name.replace(' ', '_')

    file_name = file_name.lower()
    
    formatted_file_name = re.sub(r'[^a-z0-9_]', '', file_name)
    
    return formatted_file_name                   
