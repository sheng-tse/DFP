from openai import OpenAI
import pandas as pd
import sys
import os

API_KEY = "sk-qfvxszejikiyhxiiddogyyuglhohslrdwxcmjodctfrxwfga"  
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL_NAME = "deepseek-ai/DeepSeek-R1" 
FILE_PATH = '/Users/zedrick/desktop/indeed_jobs.csv' 
DESCRIPTION_COLUMN = 'Description'

try:
    client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )
    print(f"✅ Client initialization successful. Preparing to call the SiliconFlow API.")

except Exception as e:
    print(f"❌ Client initialization failed: {e}")
    sys.exit(1)


def extract_keywords_via_api(file_path: str, column_name: str, num_samples: int = 5):
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found. Please check the path: {file_path}")
        return

    try:
        df = pd.read_csv(file_path)
        if column_name not in df.columns:
            print(f"❌ Error: Column name not found in CSV: '{column_name}'")
            return
        
        descriptions = df[column_name].dropna().head(num_samples).tolist()
        if not descriptions:
            print("❌ Error: The description column does not contain valid data.")
            return

    except Exception as e:
        print(f"❌ Error occurred while reading or preparing data: {e}")
        return

    print(f"\n🚀 Calling the model on the previous {len(descriptions)} records: {MODEL_NAME}...")

    SYSTEM_PROMPT = (
        "You are a professional text analysis and keyword extraction system. Your task is to process the text provided by the user,"
        "Output only the 10 key skills for this job description, using English words or phrases."
        "Please return the results strictly in the format of a Python list: [('Keyword1'), ('Keyword2'), ...]"
    )

    for i, description_text in enumerate(descriptions):
        truncated_text = description_text[:2000] 
        USER_PROMPT = f"Please extract the key skills (10 skills) from the following job description:\n\n--- Description ---\n{truncated_text}"

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT}
                ],
                temperature=0.1, 
                max_tokens=5000 
            )

            result_content = response.choices[0].message.content
            
            original_text = description_text[:50] + "..."
            print(f"\n--- Description {i+1} Extraction Results (Source Text: ){original_text}) ---")
            print(result_content)
            
        except client.APIError as e:
            print(f"❌ Record {i+1} API call error:{e}")
            break 
        except Exception as e:
            print(f"❌ Record {i+1} encountered an unknown error: {e}")
            break

if __name__ == "__main__":
    extract_keywords_via_api(
        file_path=FILE_PATH,
        column_name=DESCRIPTION_COLUMN,
        num_samples= 31 
    )