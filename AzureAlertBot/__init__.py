import logging
import inspect
import json
from httplib2 import Http
import re
from lxml import html 
import traceback


import azure.functions as func

################################################################################
bot_url = 'Webhook URL'
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
        final_message = ""
        parsed_body = json.loads(req.get_body())
        signal_type = parsed_body['data']['essentials']['signalType']
        alert_status = parsed_body['data']['essentials']['monitorCondition']
        context = parsed_body['data']['alertContext']
        
        #For query log alerts
        if signal_type == "Log":
            alert_rule = parsed_body['data']['essentials']['alertRule']
            final_message = final_message + "\n⚠ *"+ alert_rule + "* ⚠\n"
            columns = [c['name'] for c in parsed_body['data']['alertContext']['SearchResults']['tables'][0]['columns']]
            rows = parsed_body['data']['alertContext']['SearchResults']['tables'][0]['rows']
            # results = {name: value for name, value in zip(columns, row) for row in rows}
            time_generated = ""
            computer = ""
            message = ""

            for row in rows:
                for name, value in zip(columns, row):
                    if name == 'TimeGenerated':
                        time_generated = value
                    if name == 'Computer':
                        computer = value
                    if name == 'SyslogMessage':
                        message = value
                    
            final_message = final_message + "\n*Generated at:* " + time_generated 
            final_message = final_message + "\n*Resource:* " + computer
            final_message = final_message + "\n*Message:* " + message

        #For metrics alert
        if signal_type == "Metric":
            conditions = context['condition']['allOf']
            operator_name = ""
            threshold = ""
            metric_name = ""
            for key, value in conditions[0].items():
                if key == "metricName":
                    metric_name = value
                if key == "threshold":
                    threshold = value
                if key == "operator":
                    operator = value

            r = parsed_body['data']['essentials']['alertTargetIDs']  
            final_message = final_message + "\n⚠ *" + metric_name + " is " + operator +  " " + threshold + "* ⚠\n "
            final_message = final_message + "\n*Resources:* " + '\n\n'.join(r)    
        
        final_message = final_message + "\n*Status*: " + str(parsed_body['data']['essentials']['monitorCondition']) 
        if (alert_status == "Resolved"):
            final_message = final_message + " ✔️"
        elif (alert_status == "Fired"):
            final_message = final_message + " ❌" 

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
