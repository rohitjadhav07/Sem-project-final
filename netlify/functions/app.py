"""
Netlify Functions entry point for Flask app
"""
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import create_app

# Create Flask app
app = create_app('production')

def handler(event, context):
    """Netlify Functions handler"""
    try:
        # Convert Netlify event to WSGI environ
        environ = {
            'REQUEST_METHOD': event.get('httpMethod', 'GET'),
            'PATH_INFO': event.get('path', '/'),
            'QUERY_STRING': event.get('queryStringParameters', ''),
            'CONTENT_TYPE': event.get('headers', {}).get('content-type', ''),
            'CONTENT_LENGTH': str(len(event.get('body', ''))),
            'HTTP_HOST': event.get('headers', {}).get('host', 'localhost'),
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'wsgi.input': event.get('body', ''),
            'wsgi.errors': sys.stderr,
        }
        
        # Add headers to environ
        for key, value in event.get('headers', {}).items():
            key = 'HTTP_' + key.upper().replace('-', '_')
            environ[key] = value
        
        # Response data
        response_data = {'body': '', 'headers': {}, 'status': 200}
        
        def start_response(status, headers):
            response_data['status'] = int(status.split()[0])
            for header in headers:
                response_data['headers'][header[0]] = header[1]
        
        # Call Flask app
        response = app(environ, start_response)
        response_data['body'] = ''.join(response)
        
        return {
            'statusCode': response_data['status'],
            'headers': response_data['headers'],
            'body': response_data['body']
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }