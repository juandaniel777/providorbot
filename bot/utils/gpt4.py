import openai
import json

def gpt_response(prompt):
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt
    )
    return response.choices[0].text

def get_user_rating(user_rating):
    # """Get the user rating from the user message, extra a numerical rating from 0 to 10"""
    # user_rating = gpt_response(f"""
    #     The following is a user feedback about a dish. Please analyse and extract a numerical rating from 0 to 10.
    #     with 0 being the worst and 10 being the best. Without returning anything else other than an integer.
    #     User feedback: {user_rating}
    # """
    # )
    rating = {
        "rating": int(user_rating),
    }
    return rating

def provide_recommendations(user_previous_ratings, all_dishes):
    pass


def intention_classification(user_message):
    messages = [{"role": "user", "content": user_message}]
    functions = [
        {
            "name": "get_user_rating",
            "description": """
                Get the user feedback about an order or a dish from the user message, 
                extra a numerical rating from 0 to 10, with 0 being the worst and 10 being the best.
                Make sure you don't return anything else other than an integer. If you think the user
                didn't provide a rating, or not intended to provide a rating, return None.
                """,
            "parameters": {
                "type": "object",
                "properties": {
                    "user_rating": {
                        "type": "integer",
                        "description": """
                            Feedback from the user, e.g. 'I like it', 'It's good', 'It's bad',
                            'I don't like it', 'I hate it', 'I love it', 'I don't like it',
                            'I'll give it a 8', 'I'll give it a 9', 'I'll give it a 10',
                            '1/10', '10/10', '0/10', '10 out of 10', '9 out of 10',
                            'This dish is fantastic', 'This dish is great', 'This dish is good',
                            'This dish is bad', 'This dish is terrible', 'This dish is horrible',
                            'This dish is amazing', 'This dish is awesome', 'This dish is awful',
                        """,
                    },
                },
                "required": ["user_rating"],
            },
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call={"name": "get_user_rating"}  # auto is default, but we'll be explicit
    )
    response_message = response["choices"][0]["message"]
    # Step 2: check if GPT wanted to call a function
    if response_message.get("function_call"):
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_user_rating": get_user_rating,
        }  # only one function in this example, but you can have multiple
        function_name = response_message["function_call"]["name"]
        function_to_call = available_functions[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = function_to_call(
            user_rating=function_args.get("user_rating")
        )
        return {
            "response": function_response,
            "function_name": function_name,
        }