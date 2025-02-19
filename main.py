import os
import json
import pandas as pd 
import numpy as np
from fastapi import FastAPI, UploadFile, HTTPException, Form
from llm import *
from utils.helpers import *
from pydantic import BaseModel
from typing import List

allowed_extensions = [".pdf", ".docx"]

app = FastAPI(
    title="Resume Ranker",
    description="""
    An API for ranking resumes based on job criteria. The system performs two main functions:
    1. Extracting ranking criteria from job descriptions
    2. Scoring resumes against the extracted criteria
    """
)

@app.get("/",
    summary="Root endpoint",
    description="Returns a welcome message to confirm the API is running.",
    response_description="Welcome message"
)
def root():
    return {"message":"Welcome to Resume Ranker"}

# End point to extract criteria from Job descriptions
@app.post("/extract-criteria",
    summary="Extract ranking criteria from job description",
    description="""
    Extracts key ranking criteria from an uploaded job description file.
    Supports PDF and DOCX file formats.
    """,
    response_description="JSON object containing extracted ranking criteria",
    responses={
        200: {
            "description": "Successfully extracted criteria",
            "content": {
                "application/json": {
                    "example": {
                        "criteria": [
                            "5+ years of Python development",
                            "Experience with AWS",
                            "Strong communication skills"
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Invalid file format or processing error",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid file extension. Only .pdf, .docx are allowed!"}
                }
            }
        }
    }
)
async def extract_criteria(file: UploadFile):
    file_ext = os.path.splitext(file.filename)[1].lower()

    # checking if the uploaded files are valid through extracted extensions
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code = 400,
            detail = f"{file.filename} has invalid extension. Only {', '.join(allowed_extensions)} are allowed!"
        )
    
    # read the content if the files are valid
    content = await file.read()
    
    # Extract text based on file type
    text_content = await extract_content(file_ext, content)

    # extract key ranking criteria from job description
    attempt = 1
    max_retries = 3
    error = False
    error_correction_prompt = ""

    # attempting retry in case of OPENAI error or json error
    while attempt <= max_retries:
    
        try:
            criteria_response = generate_response(get_ranking_criteria_prompt(text_content, error_correction_prompt))
            ranking_criteria = json.loads(criteria_response)
            print(ranking_criteria)
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
        ranking_criteria = {"Error": "Failed to generate a response, please try again!!"}

    return ranking_criteria

# Endpoint to score the resumes using the extracted criteria
@app.post("/score-resumes",
    summary="Score resumes against criteria",
    description="""
    Scores multiple resumes against provided ranking criteria.
    Supports PDF and DOCX resume files.
    Returns scores for each candidate across all criteria and saves results to CSV.
    
    The scoring is done on a scale of 0-5:
    - 5: Exceeds requirement significantly
    - 4: Fully meets requirement with additional relevant experience
    - 3: Meets basic requirement
    - 2: Partially meets requirement
    - 1: Minimal relevant experience
    - 0: No relevant experience OR No information available to assess
    """,
    response_description="Success message or error details",
    responses={
        200: {
            "description": "Successfully scored resumes",
            "content": {
                "application/json": {
                    "example": {
                        "Success": "Scores are successfully generated and saved in csv file."
                    }
                }
            }
        },
        400: {
            "description": "Invalid input or processing error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid JSON format for criteria"
                    }
                }
            }
        }
    }
)
async def score_resumes(files: List[UploadFile], criteria: str = Form(...)):
    
    print("#"*30)
    error = False

    # Convert criteria string to list
    try:
        criteria_dict = json.loads(criteria)  # Parse JSON string into Python list
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for criteria")

    try:
        # get criteria headers from criteria
        criteria_headers = await get_criteria_headers(criteria_dict["criteria"])

        # dataframe to store results
        header_cols = ['Candidate Name'] + [header for header in list(criteria_headers.values())]
        score_df = pd.DataFrame(columns = header_cols)
        print("\n",score_df)

        # iterating over each resume and storing the content
        for file in files:
        
            file_ext = os.path.splitext(file.filename)[1].lower()

            # checking if the uploaded files are valid through extracted extensions
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code = 400,
                    detail = f"{file.filename} has invalid extension. Only {', '.join(allowed_extensions)} are allowed!"
                )
            
            # read the content if the files are valid
            content = await file.read()
            
            # Extract text based on file type
            text_content = await extract_content(file_ext, content)

            # send the extracted resume content along with criteria to generate scores
            scores_response = await get_candidate_scores(text_content, criteria_headers)

            # in case the returned output is not the right order of columns, lets reorder it
            ordered_row = {col: scores_response.get(col, None) for col in score_df.columns}

            # Add the row to DataFrame
            score_df.loc[len(score_df)] = ordered_row
            
    
    except Exception as e:
        print(f"Error : {str(e)}")
        error = True

    if error:
        return {"Error": "Error in either extracting content from resumes or generating scores!!"}

    else:
        # getting total score
        score_df["Total Score"] = score_df.iloc[:, 1:].sum(axis=1)

        score_df.to_csv("Resume scorer card.csv", index = False)

        return {"Success": "Scores are successfully generated and saved in csv file."}