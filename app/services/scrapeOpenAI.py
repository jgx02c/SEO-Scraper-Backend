import openai
import json

openai.api_key = 'your-api-key'  # Add your OpenAI API key here

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

# Function to generate OpenAI response
def stream_openai_response(prompt: str, website_url: str):
    # Create a chat completion request with streaming enabled
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Adjust based on the model you're using
        messages=[
            {"role": "system", "content": f"You are a helpful assistant analyzing the website: {website_url}."},
            {"role": "user", "content": prompt}
        ],
        stream=True,  # Enable streaming
    )

    # Collect the streaming response
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
    print(f"Getting pages for website: {website_url}")
    
    # Get response from OpenAI to list pages for the website
    response = stream_openai_response(prompt, website_url)
    
    # Assuming the response is a comma-separated list of pages
    pages = response.split(',')
    pages = [page.strip() for page in pages]  # Clean up any extra spaces
    
    return pages

# Function to process all prompts for a website overview
def process_overview_for_website(prompts_json, website_url):
    website_output = {}

    # Process each overview prompt for the website
    for key, prompt_data in prompts_json.items():
        prompt = prompt_data["prompt"]
        label = prompt_data["label"]
        
        print(f"Processing overview prompt: {prompt} for website: {website_url}")
        response = stream_openai_response(prompt, website_url)
        
        # Store the result under the correct label
        website_output[label] = response
    
    return website_output

# Function to process prompts for a specific website and its pages
def process_page_level_for_website(prompts_json, website_url, pages):
    page_level_output = {}

    # For each page, process the relevant prompts
    for page_url in pages:
        page_output = {}

        for key, prompt_data in prompts_json.items():
            prompt = prompt_data["prompt"]
            label = prompt_data["label"]
            
            print(f"Processing page-level prompt: {prompt} for page: {page_url}")
            response = stream_openai_response(prompt, page_url)
            
            # Store the result under the correct label
            page_output[label] = response
        
        # Store the page output under the website and page URL
        page_level_output[page_url] = page_output
    
    return page_level_output

# Function to process all websites
def process_websites(prompts_json, websites):
    output = {}

    for website in websites:
        # Step 1: Process overview prompts
        print(f"Processing overview for website: {website}")
        website_overview = process_overview_for_website(prompts_json, website)

        # Step 2: Get the pages of the website using OpenAI
        pages = get_website_pages(website)

        # Step 3: Process page-level prompts for each page
        print(f"Processing page-level prompts for website: {website}")
        website_page_level = process_page_level_for_website(prompts_json, website, pages)

        # Combine both overview and page-level results
        website_data = {
            "overview": website_overview,
            "pages": website_page_level
        }

        # Store results for the website
        output[website] = website_data

    return output

# Run the process and store the results
processed_data = process_websites(prompts_json, websites)

# Print the final output (this would be ready for MongoDB upload)
print(json.dumps(processed_data, indent=2))
