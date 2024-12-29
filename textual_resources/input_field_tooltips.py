class InputFieldTooltips:

   agent_tooltips = {'agent_name': 'The name of the agent so it can easily be differentiated form other agents', 
                     'agent_role': 'The agent\'s function within the crew. It determines the kinds of tasks the agent is best suited for', 
                     'agent_goal': 'The individual objective that the agent aims to achieve. It guides the agent\'s decision-making process', 
                     'agent_backstory': 'The context to the agent\'s role and goal to enrich the interaction and collaboration dynamics', 
                     'agent_verbosity': 'The internal logger configuration to provide detailed execution logs',
                     'agent_delegation': 'The configuration of the agent to delegate tasks or questions to other agents', 
                     'agent_tools': 'The set of capabilities or functions that the agent can use to perform tasks', 
                     'agent_llm': 'The Large Language Model that will run the agent',
                     'agent_llm_temperature': 'The agent Large Language Model\'s configuration to determine whether the output is more random and creative or more predictable', 
                     'agent_max_rpm': 'The maximum number of requests per minute the agent can perform. \'0\' means no limit',
                     'agent_max_iter': 'The maximum number of iterations the agent can perform before giving its best answer',
                     'agent_memory': 'The configuration for storing execution memories (Entity, Long-Term and Short-Term memory)'}
   
   task_tooltips = {'task_human_input': 'The configuration to indicate if the task requires human feedback at the end',
                    'task_description': 'A clear and concise statement of what the specific task entails',
                    'task_expected_output': 'A detailed description of what the task\'s completed output looks like'}   
   
   crew_tooltips = {'crew_name': 'The name of the crew',
                    'crew_description': 'A clear and concise statement of what the crew does',
                    'crew_verbosity': 'The internal logger configuration to provide detailed execution logs',  
                    'crew_max_rpm': 'The maximum number of requests per minute the crew can perform. \'0\' means no limit',
                    'crew_memory': 'The configuration for storing execution memories (Entity, Long-Term and Short-Term memory)',
                    'crew_full_output': 'The configuration to set whether the crew should return the full output of all tasks or just the final output',
                    'crew_process': 'The process flow (Hierarchical or Sequential) the crew follows',
                    'crew_manager_llm': 'The Large Language Model used by the manager agent in a hierarchical process (Only required when using a hierarchical process)',
                    'crew_manager_llm_temperature': 'The manager Large Language Model\'s configuration to determine whether the output is more random and creative or more predictable (Only required when using a hierarchical process)'}