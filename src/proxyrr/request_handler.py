import json
import re
import os
import logging
import urllib
import jsonschema
from enum import Enum
from proxy_error import ProxyError

class MethodType(Enum):
    UNSUPPORTED = 0
    GET = 1
    POST = 2


class RequestHandlerContext:

    def __init__(self, request, context, start_time):
        self.request = request
        self.context = context
        self.response = {
            'statusCode' : 404,
            'body' : {
                'status' : 'error',
                'message' : 'Request not supported'
            },
            'headers' : {
                'Access-Control-Allow-Origin': '*',
            }
        }
        self.environment_variables = {}

        self.configure_logging_context()

        self.request_params = self.parse_request_params()

        self.start_time = start_time

    def resource(self):
        # The resource is everything after /api, but before the '?'
        parse_result = urllib.parse.urlparse(self.request['path'])
        matches = re.search(r'(?<=\/api\/).+', parse_result.path)
        return matches.group(0)

    def method(self):
        if self.request['httpMethod'] == 'GET':
            return MethodType.GET
        elif self.request['httpMethod'] == 'POST':
            return MethodType.POST
        else:
            return MethodType.UNSUPPORTED

    def parse_request_params(self):
        params = {}
        if self.method() is MethodType.POST:
            if 'body' in self.request.keys() and self.request['body']:
                try:
                    params = json.loads(self.request['body'])
                except json.JSONDecodeError as err:
                    logging.info('No request body detected.')

        elif self.method() is MethodType.GET:
            params = self.request['queryStringParameters']
            params = params if type(params) is dict else {}
        
        else:
            raise 'Unsupported request type'

        return params

    def params(self):
        return self.request_params

    def validate_environment(self, environment_variables:dict):
        for key in environment_variables.keys():
            required = False
            if 'required' in environment_variables.get(key).keys():
                required = environment_variables.get(key)['required']

            if key in os.environ:
                self.environment_variables.update({key : os.environ.get(key)})

            elif required:
                raise 'FATAL: Environment variable \'{}\' not set'.format(key)

    def configure_logging_context(self):
        logging.basicConfig(level=logging.DEBUG)

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))

        logging.getLogger().addHandler(console)


    def environ(self, key):
        if not key in self.environment_variables.keys():
            return None
        return self.environment_variables.get(key)

    def is_authenticated(self):
        if not 'authorizer' in self.request['requestContext'].keys():
            return False
        return True

    def authenticated_sub(self):
        if not self.is_authenticated():
            return None
        if 'cognito:username' in self.request['requestContext']['authorizer']['claims'].keys():
            return self.request['requestContext']['authorizer']['claims']['cognito:username']
        return None

    def success_response(self, data):
        self.response = {
            'statusCode' : 200,
            'body' : json.dumps({
                'status' : 'success',
                'message' : '',
                'data' : data
            }, default=str),
            'headers' : {
                'Access-Control-Allow-Origin': '*',
            }
        }

    def error_response(self, error_code, message, error_type=''):
        logging.error(message)
        self.response = {
            'statusCode' : error_code,
            'body' : json.dumps({
                'status' : 'error',
                'type' : error_type,
                'message' : message
            }, default=str),
            'headers' : {
                'Access-Control-Allow-Origin': '*',
            }
        }

    def exception_response(self, error_message, aws_request_id):
        logging.error(error_message)
        self.response = {
            'statusCode': 500,
            'body': json.dumps({
                'Error': error_message,
                'Reference': aws_request_id,
            }),
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
        }


class RequestHandler:

    def __init__(self, name : str, resource : str, method : MethodType, auth_required:bool=True, validation_schema=None):
        self.name = name
        self.resource = resource
        self.method_type = method
        self.auth_required = auth_required
        self.validation_schema = validation_schema

    def execute(self, context : RequestHandlerContext):
        raise 'Execute method must be overriden by subclass'

    def process_request(self, context : RequestHandlerContext):

        if self.auth_required and not context.is_authenticated():
            context.error_response(500, 'Authorization not configured')

        else:

            if self.validation_schema:
                try:
                    jsonschema.validate(instance=context.params(), schema=self.validation_schema)
                
                except jsonschema.ValidationError as err:
                    context.error_response(400, err.message)
                    return

                except jsonschema.SchemaError as err:
                    context.error_response(500, err.message)
                    return

            try:
                self.execute(context)

            except ProxyError as err:
                context.error_response(err.code, err.message, error_type=err.type)

            except Exception as err:
                context.error_response(500, str(err))
