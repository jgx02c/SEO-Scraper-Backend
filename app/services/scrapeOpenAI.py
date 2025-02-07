import openai
import json
from pymongo import MongoClient

openai.api_key = 'your-api-key'  # Add your OpenAI API key here

# MongoDB client setup
client = MongoClient('mongodb://localhost:27017/')  # Connect to MongoDB
db = client['website_data']  # Database name
websites_collection = db['websites']  # Collection name

# Load the prompts JSON from an external file
with open('prompts.json', 'r') as file:
    prompts_json = json.load(file)

# Accessing page prompts
page_prompt_5 = prompts_json["page_prompts"]["5"]["prompt"]
page_label_5 = prompts_json["page_prompts"]["5"]["label"]

# Accessing overview prompts
overview_prompt_1 = prompts_json["overview_prompts"]["1"]["prompt"]
overview_label_1 = prompts_json["overview_prompts"]["1"]["label"]

# Example usage of the loaded prompts JSON
print("Page Prompt 5: ", page_prompt_5)
print("Page Label 5: ", page_label_5)

print("Overview Prompt 1: ", overview_prompt_1)
print("Overview Label 1: ", overview_label_1)

main = "https://leapsandrebounds.com/"

# Example list of websites (to start off)
websites = [
    "https://www.bellicon.com",
    "https://www.jumpsport.com",
    "https://www.bcanfitness.com",
    "https://www.acontrampolines.com",
    "https://www.staminaproducts.com",
    "https://www.sunnyhealthfitness.com",
    "https://www.dickssportinggoods.com",
    "https://www.kanchimi.com",
    "https://www.domyos.com",
    "https://www.argos.co.uk",
    "https://www.boogiebounce.com",
    "https://www.ativafit.com",
    "https://www.darchen.com",
    "https://www.theness.com",
    "https://www.sportplus.com",
    "https://www.radicalrebounding.com",
    "https://www.reboundfit.com",
    "https://www.jumpandjacked.com",
    "https://www.reboundercanada.com",
    "https://www.rebounderworld.com",
    "https://www.urbanrebounder.com",
    "https://www.jumpsportfitness.com",
    "https://www.rebounderpro.com",
    "https://www.reboundershop.com",
    "https://www.rebounderdirect.com"
]

# Function to create or get website ID from MongoDB
def get_or_create_website_id(website_url: str):
    # Check if the website already exists in MongoDB
    existing_website = websites_collection.find_one({"url": website_url})
    if existing_website:
        return existing_website["_id"]
    
    # If the website does not exist, insert it and return the new ID
    new_website = {"url": website_url}
    result = websites_collection.insert_one(new_website)
    return result.inserted_id

# Function to generate OpenAI response
def stream_openai_response(prompt: str, website_url: str):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"You are a helpful assistant analyzing the website: {website_url}."},
            {"role": "user", "content": prompt}
        ],
        stream=True,
    )

    result = ''
    for chunk in response:
        if 'choices' in chunk:
            for choice in chunk['choices']:
                if 'message' in choice:
                    result += choice['message']['content']
    return result.strip()

# Function to get all the pages for a website using OpenAI
def get_website_pages(website_url: str):
    prompt = f"List all the product or service pages on the website {website_url}."
    response = stream_openai_response(prompt, website_url)
    
    pages = response.split(',')
    pages = [page.strip() for page in pages]
    
    return pages

# Function to process all prompts for a website overview
def process_overview_for_website(prompts_json, website_url):
    website_output = {}

    for key, prompt_data in prompts_json.items():
        prompt = prompt_data["prompt"]
        label = prompt_data["label"]
        
        response = stream_openai_response(prompt, website_url)
        website_output[label] = response
    
    return website_output

# Function to process prompts for a specific website and its pages
def process_page_level_for_website(prompts_json, website_url, pages):
    page_level_output = {}

    for page_url in pages:
        page_output = {}

        for key, prompt_data in prompts_json.items():
            prompt = prompt_data["prompt"]
            label = prompt_data["label"]
            
            response = stream_openai_response(prompt, page_url)
            page_output[label] = response
        
        page_level_output[page_url] = page_output
    
    return page_level_output

# Function to process all websites
def process_websites(prompts_json, websites):
    output = []
    website_ids = []

    for website in websites:
        website_id = get_or_create_website_id(website)
        website_ids.append({"url": website, "id": str(website_id)})
        
        website_overview = process_overview_for_website(prompts_json, website)
        pages = get_website_pages(website)
        website_page_level = process_page_level_for_website(prompts_json, website, pages)

        website_data = {
            "website_id": str(website_id),
            "overview": website_overview,
            "pages": website_page_level
        }

        output.append(website_data)

    return output, website_ids

# Run the process and store the results
processed_data, website_ids = process_websites(prompts_json, websites)

# Now processed_data contains the OpenAI responses with website IDs, ready for MongoDB upload.
print(json.dumps(processed_data, indent=2))
print("Website IDs:", json.dumps(website_ids, indent=2))

