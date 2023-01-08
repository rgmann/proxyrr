# ProxyRR

This module provides a framework receiving and responding to proxy resource REST API requests.

## Usage

```python
import proxyrr

def lambda_handler(event, context):

    start_time = time.time()

    environment_variables = {
        'POLLY_OUTPUT_BUCKET' : {
            'required' : True
        },
        'POLLY_SNS_TOPIC_ARN' : {
            'required' : True
        },
        'MONGODB_USERNAME' : {
            'required' : True
        },
        'MONGODB_PASSWORD' : {
            'required' : True
        }
    }

    handler_context = proxyrr.request_handler.RequestHandlerContext(event, context, start_time)

    logging.info('Validating expected environment variables')
    try:
        handler_context.validate_environment(environment_variables)

    except Exception as error:
        handler_context.error_response(500, str(error))
        return handler_context.response

    username = handler_context.environ('MONGODB_USERNAME')
    password = handler_context.environ('MONGODB_PASSWORD')

    request_mapper = proxyrr.request_handler.RequestMapper()

    logging.info('Processing request for resource \'{}\' with method \'{}\''.format(
        handler_context.resource(),
        handler_context.method()
    ))

    handler = request_mapper.get_handler(handler_context.resource(), handler_context.method())
    if handler:
        handler.process_request(handler_context)

    else:
        handler_context.error_response(404, 'No handler registered for resource=\'{}\', method=\'{}\''.format(
            handler_context.resource(),
            handler_context.method().name
        ))

    return handler_context.response
```