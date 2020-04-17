import logging
import inspect
import json
from httplib2 import Http
import re
from lxml import html 


import azure.functions as func

################################################################################
bot_url = 'URL'
################################################################################


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    logging.info(f"BEGIN-----------------------------------------------------")        
    for k,v  in req.headers.items():
        logging.info(f"request header {k}:{v}")    
    logging.info(f"request params are: {req.params}")
    logging.info(f"request body is: {req.get_body()}")
    logging.info(f"END-----------------------------------------------------")
    try:
        parsed_body = json.loads(req.get_body())
        alert_context = parsed_body['alertContext']
        final_message = ""
        alert_type = alert_context['AlertType']
        if alert_type=='SSH User Login in VM':
            final_message = final_message + "\n⚠ *SSH user has logged in to a VM* ⚠\n "
            search_results = alert_context['SearchResults']
            tables = search_results['tables']
            columns = tables[0]['columns']
            for column in columns:
                if column['name']=='TimeGenerated':
                    final_message = final_message + "\n*Generated at:* "+ column['type']
                if column['name']=='Computer':
                    final_message = final_message + "\n*Virtual Machine:* "+ column['type']
                if column['name']=='SeverityLevel':
                    final_message = final_message + "\n*Severity level:* "+ column['type']
                if column['name']=='SyslogMessage':
                    final_message = final_message + "\n*Message:* "+ column['type']
            
        logging.info(f"extracted message: {final_message}")

        if (len(final_message)>0):
            http_obj = Http()
            
            bot_message = {
                'text': final_message
            }
            message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
 
            bot_response = http_obj.request(
                uri = bot_url,
                method='POST',
                headers=message_headers,
                body = json.dumps(bot_message)
            )
            logging.info(f"bot response is: {bot_response}")

            return func.HttpResponse(f"Completed successfully", status_code=200)
        else:
            return func.HttpResponse(f"Error occurred", status_code=404)
    except Exception as e:
        logging.error(f"Error {e}")
        return func.HttpResponse(f"Error occurred", status_code=500)