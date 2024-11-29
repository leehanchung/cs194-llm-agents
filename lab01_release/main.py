from typing import Dict, List
from autogen import ConversableAgent
import sys
import os


def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # TODO
    # This function takes in a restaurant name and returns the reviews for that restaurant. 
    # The output should be a dictionary with the key being the restaurant name and the value being a list of reviews for that restaurant.
    # The "data fetch agent" should have access to this function signature, and it should be able to suggest this as a function call. 
    # Example:
    # > fetch_restaurant_data("Applebee's")
    # {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}

    reviews = []
    with open('./restaurant-data.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.lower().startswith(restaurant_name.lower() + '. ') or line.lower().startswith(restaurant_name.lower().replace(' ', '-') + '. '):
                reviews.append(line[len(restaurant_name)+2:])
    return {restaurant_name: reviews}


def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    # TODO
    # This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    # The output should be a score between 0 and 10, which is computed as the following:
    # SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    # The above formula is a geometric mean of the scores, which penalizes food quality more than customer service. 
    # Example:
    # > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    # {"Applebee's": 5.048}
    # NOTE: be sure to that the score includes AT LEAST 3  decimal places. The public tests will only read scores that have 
    # at least 3 decimal places.
    from math import sqrt

    scores = [sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(len(food_scores) * sqrt(125) + 1e-8) for i in range(len(food_scores))]
    score = round(sum(scores) * 10, 3)
    return {restaurant_name: score}


def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    # TODO
    # It may help to organize messages/prompts within a function which returns a string. 
    # For example, you could use this function to return a prompt for the data fetch agent 
    # to use to fetch reviews for a specific restaurant.
    return  f"""You are a specialized data fetch agent focused on fetching restaurant reviews.

Task: Analyze and fetch review data for {restaurant_query}

Please follow these steps:
1. Get the restaurant name from the {restaurant_query}. Remember to capitalize the name.
1. Call the fetch_restaurant_data function with restaurant name as the argument
2. Verify the data was retrieved successfully
3. Return the fetched review data

Use this function:
fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]
- Input: Restaurant name (string)
- Output: Dictionary with restaurant name as key and list of reviews as values

IMPORTANT: Always use the function call format to fetch data, do not try to provide or generate reviews yourself."""


# TODO: feel free to write as many additional functions as you'd like.
def data_fetch_agent(user_query: str) -> Dict[str, List[str]]:

    from openai import OpenAI
    from pydantic import BaseModel

    class RestaurantExtraction(BaseModel):
        restaurant_name: str

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    messages = [
        {
            'role': 'user',
            'content': f"""You are a specialized data fetch agent focused on fetching restaurant reviews. Please get the restuarant name from {user_query}."""
        },
    ]
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=messages,
        response_format=RestaurantExtraction,
    )
    restaurnt_name = response.choices[0].message.parsed.restaurant_name
    print(f"\n\ndata_fetch_agent:\nrestaurant name: {restaurnt_name}\n")
    reviews = fetch_restaurant_data(restaurnt_name)
    print(f"reviews:\n {reviews}")
    return reviews


def review_analysis_agent(reviews: Dict[str, List[str]]):
    """returns  Tuple[str, List[int], List[int]]:
    """
    print("\n\nreview_analysis_agent:\n")
    restaurnt_name = list(reviews.keys())[0]
    reviews = reviews[restaurnt_name]
    food_scores, customer_service_scores = [], []

    def score_review(review: str):
        from openai import OpenAI
        from pydantic import BaseModel

        class ReviewExtraction(BaseModel):
            food_score: int
            customer_service_score: int

        prompt = f"""You are a review analysis agent. Your task is to analyze the reviews for a restaurant and provide scores for both food quality score and customer service score.

Here's the scoring criteria:
Score 1/5 has one of these adjectives: awful, horrible, or disgusting.
Score 2/5 has one of these adjectives: bad, unpleasant, or offensive.
Score 3/5 has one of these adjectives: average, uninspiring, or forgettable.
Score 4/5 has one of these adjectives: good, enjoyable, or satisfying.
Score 5/5 has one of these adjectives: awesome, incredible, or amazing.

Example:
review: The food at McDonald's was average, but the customer service was unpleasant. The uninspiring menu options were served quickly, but the staff seemed disinterested and unhelpful.
food score: 3
customer service score: 2

review: {review}
"""

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        messages = [

            {
                'role': 'user',
                'content': prompt,
            },
        ]
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format = ReviewExtraction,
        )
        review = response.choices[0].message.parsed
        return review.food_score, review.customer_service_score

    for review in reviews:
        food_score, customer_service_score = score_review(review)
        print(f"review: {review}food_score: {food_score}\ncustomer_service_score: {customer_service_score}\n")
        food_scores.append(food_score)
        customer_service_scores.append(customer_service_score)
    
    print(f"restaurant_name{restaurnt_name}\nfood_scores: {food_scores}\ncustomer_service_scores: {customer_service_scores}")
    return restaurnt_name, food_scores, customer_service_scores


# Do not modify the signature of the "main" function.
def main(user_query: str):
    # entrypoint_agent_system_message = """NO WAY JOSE."""  # TODO

    # example LLM config for the entrypoint agent
    # llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}

    # the main entrypoint/supervisor agent
    # entrypoint_agent = ConversableAgent(
    #     name="entrypoint_agent",
    #     system_message=entrypoint_agent_system_message,
    #     human_input_mode="NEVER",
    #     llm_config=llm_config,
    # )

    # entrypoint_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    # entrypoint_agent.register_for_llm(name="calculate_overall_score", description="Calculates overall score.")(calculate_overall_score)

    # NOTE: autogen sucks. doing this manually


    # TODO
    # Create more agents here.
    reviews = data_fetch_agent(user_query)
    restaurant_name, food_scores, customer_service_scores = review_analysis_agent(reviews)
    overall_score = calculate_overall_score(restaurant_name, food_scores, customer_service_scores)
    print(f"Overall score for {restaurant_name}: {overall_score[restaurant_name]:.3f}")

    # # TODO
    # # Fill in the argument to `initiate_chats` below, calling the correct agents sequentially.
    # # If you decide to use another conversation pattern, feel free to disregard this code.
    
    # # Uncomment once you initiate the chat with at least one agent.
    # chat_results = entrypoint_agent.initiate_chats()


# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])