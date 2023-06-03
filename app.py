import re
import os
import openai
from flask import Flask, request, render_template_string
from pprint import pprint
import hubspot
from hubspot.crm.objects.notes import PublicObjectSearchRequest, ApiException

HAaccesstoken = os.getenv("HATOKEN")
openai.organization = "OPENAI_ORG"
openai.api_key = os.getenv("OPENAIKEY")

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # This is where the form data is processed
        dealID = request.form.get('dealID')
        prompt = request.form.get('prompt')
        print(dealID)
        print(prompt)
        
        # Create HubSpot client
        client = hubspot.Client.create(access_token=HAaccesstoken)
        # Set up a search request to search for notes where the dealId equals the specified deal ID
        public_object_search_request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "propertyName": "associations.contact",
                            "operator": "EQ",
                            "value": dealID
                        }
                    ]
                }],
                properties=['hs_note_body'],
                limit=100  # adjust this value as per your requirement
                )
        try:
            # Perform the search
            api_response = client.crm.objects.notes.search_api.do_search(public_object_search_request=public_object_search_request)
            print(api_response)
            pattern = re.compile(r'<span[^>]*>([^<]+)</span>')
            res = []
            conversation = [
                {"role": "system", "content": "You are a deligent solutions architect taking notes on a customer call"},
                ]
            for i in api_response.results:
                text = i.properties['hs_note_body']
                matches = pattern.findall(text)
                for note in matches:
                    print(note)
                    conversation.append({"role":"assistant", "content":f'{note}'})
        
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=conversation + [
                    {"role": "assistant", "content": f"{prompt}"}
                    ]
                )
            # Extract the generated message
            print(conversation)
            generated_content = response['choices'][0]['message']['content']
            return f'Deal notes: {generated_content}.'

        except ApiException as e:
            print("Exception when calling basic_api->get_page: %s\n" % e)

    # This is the HTML form to be rendered
    form_html = '''
        <form method="POST">
            <label for="text">HubSpot Deal</label><br>
            <input type="text" id="dealID" name="dealID" value=""><br>
            <label for="text">Prompt: </label><br>
            <input type="text" id="prompt" name="prompt" value=""><br>
            <input type="submit" value="Submit">
        </form>
    '''
    return render_template_string(form_html)

if __name__ == '__main__':
    app.run(debug=True, port=5000)