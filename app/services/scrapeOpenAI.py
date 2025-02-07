import openai
import json
import os
from typing import Dict, Any
from datetime import datetime
from pymongo import MongoClient

# MongoDB connection setup
mongo_uri = os.getenv('mongo_uri')
client = MongoClient(mongo_uri)
db = client['Cluster07388']
company_collection = db['company']

openai.api_key = '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'

def load_prompts() -> Dict[str, Dict[str, Dict[str, Dict[str, str]]]]:
    """Load prompts from JSON file"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_path = os.path.join(current_dir, 'prompts.json')
        
        with open(prompts_path, 'r') as file:
            prompts = json.load(file)
            
        # Debug print
        print("Loaded prompts structure:")
        print(json.dumps(prompts, indent=2))
        
        # Validate prompt structure
        if "overview_prompts" not in prompts:
            raise KeyError("Missing 'overview_prompts' in prompts.json")
        if "page_prompts" not in prompts:
            raise KeyError("Missing 'page_prompts' in prompts.json")
            
        return prompts
    except FileNotFoundError:
        print(f"Could not find prompts.json at: {prompts_path}")
        print(f"Current working directory: {os.getcwd()}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing prompts.json: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error loading prompts: {str(e)}")
        raise

def get_gpt_response(prompt: str, website_url: str) -> str:
    """Get response from OpenAI API"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are analyzing the website: {website_url}"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error getting GPT response for {website_url}: {str(e)}")
        return ""

def get_website_pages(website_url: str) -> list:
    """Get all pages from a website"""
    prompt = """List all the product or service pages on this website. 
    Return only the URLs, one per line, with no additional text or formatting."""
    
    response = get_gpt_response(prompt, website_url)
    pages = [page.strip() for page in response.split('\n') if page.strip()]
    return pages

def process_prompts_for_target(prompts: Dict[str, Dict[str, Dict[str, str]]], 
                             target_url: str, 
                             prompt_type: str) -> Dict[str, Any]:
    """Process numbered prompts for a given URL"""
    try:
        results = {}
        
        # Debug print
        print(f"\nProcessing {prompt_type} for {target_url}")
        print(f"Available prompt types: {list(prompts.keys())}")
        
        # Get the specific prompt type (overview_prompts or page_prompts)
        if prompt_type not in prompts:
            raise KeyError(f"Prompt type '{prompt_type}' not found in prompts")
            
        type_prompts = prompts[prompt_type]
        
        # Debug print
        print(f"Found {len(type_prompts)} prompts for {prompt_type}")
        
        # Process each numbered prompt
        for prompt_num in type_prompts:
            prompt_data = type_prompts[prompt_num]
            print(f"Processing prompt {prompt_num}: {prompt_data['label']}")
            
            response = get_gpt_response(prompt_data["prompt"], target_url)
            results[prompt_data["label"]] = {
                "response": response,
                "prompt_number": prompt_num,
                "timestamp": datetime.utcnow()
            }
        
        return results
    except Exception as e:
        print(f"Error processing prompts for {target_url}: {str(e)}")
        raise

def process_website(website_url: str, is_main: bool, prompts: Dict) -> Dict[str, Any]:
    """Process a single website and return its analysis data"""
    # Create base document structure
    website_data = {
        "url": website_url,
        "is_main": is_main,
        "created_at": datetime.utcnow(),
        "last_updated": datetime.utcnow(),
        "sections": {
            "overview": {
                "data": process_prompts_for_target(prompts, website_url, "overview_prompts"),
                "url": website_url,
                "type": "overview"
            }
        }
    }
    
    # Get and process all pages
    pages = get_website_pages(website_url)
    for idx, page in enumerate(pages, 1):
        section_key = f"page_{idx}"
        website_data["sections"][section_key] = {
            "data": process_prompts_for_target(prompts, page, "page_prompts"),
            "url": page,
            "type": "page"
        }
    
    return website_data

def main():
    # Load configuration
    prompts = load_prompts()
    main_website = "https://leapsandrebounds.com/"
    websites = [
        "https://www.bellicon.com",
        "https://www.jumpsport.com",
        # ... rest of your websites list
    ]

    # Process main website
    print(f"Processing main website: {main_website}")
    main_website_data = process_website(main_website, True, prompts)
    
    # Save or update main website data
    company_collection.update_one(
        {"url": main_website},
        {"$set": main_website_data},
        upsert=True
    )

    # Process competitor websites
    for website in websites:
        print(f"Processing competitor website: {website}")
        competitor_data = process_website(website, False, prompts)
        
        # Save or update competitor data
        company_collection.update_one(
            {"url": website},
            {"$set": competitor_data},
            upsert=True
        )

if __name__ == "__main__":
    main()