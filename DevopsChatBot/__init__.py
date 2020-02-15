import logging
import inspect
import json
from httplib2 import Http
import re
from lxml import html 


import azure.functions as func


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
        event_type = parsed_body['eventType']
        final_message = ""
        if event_type=='git.pullrequest.created':
            logging.info(f"parsed body is {parsed_body}")            
            resource = parsed_body['resource']
            title = resource['title']
            if 'description' in resource.keys():
                description = resource['description'] 
            else: 
                description = None
            author = resource['createdBy']['displayName']
            link_to_pr = resource['_links']['web']['href']
            if description is None:
                final_message = f"Hello dear friends!\n{author} created <{link_to_pr}|pull request>\nTitle: *{title}*\nPull request has no description - shame on you {author} :)"
            else:
                final_message = f"Hello dear friends!\n{author} created <{link_to_pr}|pull request>\nTitle: *{title}*\nDescription:\n{description}"
        elif event_type=='ms.vss-code.git-pullrequest-comment-event':
            resource = parsed_body['resource']
            author = resource['author']['displayName']
            if 'content' in resource.keys():
                content = resource['content']
            else:
                return func.HttpResponse(f"Comment is not PTAL", status_code=200)
            html_message = parsed_body['message']['html']
            string_document = html.fromstring(html_message) 
            link_to_pr = ""
            link = list(string_document.iterlinks()) 
            if len(link):                
                (element, attribute, link_to_pr, pos) = link[0]             
            if re.match("^PTAL$",content):
                final_message = f"Hello dear friends!\n{author} wants us to take another look <{link_to_pr}|at this pull request>"
            elif re.match("^PTAL ASAP$",content):
                final_message = f"Hello dear friends!\n\n\n\n\n{author} *really really really* wants you to take another look <{link_to_pr}|at this pull request>"
            elif re.match("^PTAL KURWA$",content):
                final_message = f"Hello lazy buttheads!\n\n\n\n\nNow everyone !!! Put away what you are doing and go <{link_to_pr}|here> to finish reviewing this PR because otherwise author ->{author}<- starts throwing stones at you if you wont do it ASAP!!!\n\n\nNow move!!!!"
            else:
                return func.HttpResponse(f"Comment is not PTAL", status_code=200)
        else:
            final_message = f"unable to process event {event_type} - tell Konrad to debug ;P"

        logging.info(f"extracted message: {final_message}")

        if (len(final_message)>0):
            http_obj = Http()
            ################################################################################
            bot_url = here goes googleapis link to your room
            ################################################################################
            
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