import fitz
import json
from typing import List, Tuple
from docx import Document
from io import BytesIO
from llm import get_criteria_prompt, generate_response, get_scoring_prompt

async def extract_content(file_ext: str, content: bytes) -> str:
    
    if file_ext==".pdf":
        # Create a BytesIO object from the content
        pdf_stream = BytesIO(content)
        # Open the PDF using PyMuPDF
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        text = ""
        # Iterate through pages and extract text
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    
    elif file_ext==".docx":
        docx_file = BytesIO(content)
        doc = Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    

async def get_criteria_headers(criteria_list: List):

    error_correction_prompt = ""
    attempt = 1
    max_retires = 2
    error = False

    while attempt <= max_retires:

        try:
            prompt = get_criteria_prompt(criteria_list, error_correction_prompt = "")
            response = generate_response(prompt)
            # original_criteria_headers = json.loads(response)
            criteria_headers = json.loads(response)["criteria_headers"]
            print("Criteria headers: ",criteria_headers,"\n")

            if len(criteria_list)!=len(criteria_headers.keys()):
                print("One or more criteria are missing from the response!!")
                error = True
                error_correction_prompt = "In the previous iteration, you missed out on some of the criteria from the output. Make sure that doesn't happen. All provided criteria should have a header."
                attempt += 1
                continue

            else:
                if sorted(criteria_list)!=sorted(list(criteria_headers.keys())):
                    print("Original criteria doesn't match the returned criteria!!")
                    error = True
                    error_correction_prompt = "In the previous iteration, you gave out the headers for every criteria but some of the criteria didn't matched the original criteria. Make sure the criteria in the returned output are same as you got in the input."
                    attempt += 1
                    continue
                
                else:
                    pass

            error = False
            break

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {str(e)}")
            error_correction_prompt = "In the previous iteration, you failed to return a valid JSON response, please make sure the response is in the JSON format as mentioned."
            attempt += 1
            error = True
            continue

        except Exception as e:
            print(f"Error in generating response : {str(e)}")
            attempt += 1
            error = True
            continue

    if error:
        criteria_headers = {"Error": "Failed to generate criteria headers, please try again!!"}

    return criteria_headers


async def get_candidate_scores(content : str, criteria_headers: dict):

    error_correction_prompt = ""
    attempt = 1
    max_retires = 2
    error = False

    while attempt <= max_retires:

        try:
            prompt = get_scoring_prompt(content, criteria_headers, error_correction_prompt = "")
            response = generate_response(prompt)
            candidate_scores = json.loads(response)

            print("Scores: ",candidate_scores,"\n")

            # checking if the number of items returned are same as input
            if len(candidate_scores)-1!=len(criteria_headers.values()): # excluding name count from check
                print("One or more criteria are missing from the response!!")
                error = True
                error_correction_prompt = "In the previous iteration, you missed out on some of the criteria from the output. Make sure that doesn't happen. A candidate needs to be evaluated on all the criteria, no matter what. Please make sure you follow the rules."
                attempt += 1
                continue

            else:
                if sorted([key for key in candidate_scores.keys() if key != "Candidate Name"]) != sorted(list(criteria_headers.values())):
                    print("Criteria headers doesn't match the original headers provided!!")
                    error = True
                    error_correction_prompt = "In the previous iteration, you returned the scores for each criteria header but some of the criteria headers didn't matched the original criteria headers. Make sure the criteria headers in the returned output are same as you got in the input."
                    attempt += 1
                    continue
                
                else:
                    pass

            error = False
            break

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {str(e)}")
            error_correction_prompt = "In the previous iteration, you failed to return a valid JSON response, please make sure the response is in the JSON format as mentioned."
            attempt += 1
            error = True
            continue

        except Exception as e:
            print(f"Error in generating response : {str(e)}")
            attempt += 1
            error = True
            continue

    if error:
        candidate_scores = {"Error": "Failed to generate scores, please try again!!"}

    return candidate_scores