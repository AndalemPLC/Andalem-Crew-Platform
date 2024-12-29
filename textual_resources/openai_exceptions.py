import openai

class OpenAIExceptions:

    error_messages = {openai.APITimeoutError: 'Request time out error! Check the log for details',
                      openai.APIConnectionError: 'Connection error! Check the log for details',
                      openai.AuthenticationError: 'Authentication error! Check the log for details',
                      openai.BadRequestError: 'Bad request error! Check the log for details',
                      openai.ConflictError: 'Conflict error! Check the log for details',
                      openai.InternalServerError: 'Internal server error! Check the log for details',
                      openai.NotFoundError: 'Resource not found error! Check the log for details',
                      openai.PermissionDeniedError: 'Permission denied error! Check the log for details',
                      openai.RateLimitError: 'Rate limit error! Check the log for details',
                      openai.UnprocessableEntityError: 'Unable to process request error! Check the log for details',
                      openai.APIError: 'API error! Check the log for details'}    