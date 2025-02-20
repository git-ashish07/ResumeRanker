import os
import json
import pandas as pd 
from fastapi import FastAPI, UploadFile, HTTPException, Form
from llm import *
from utils.helpers import *
from typing import List
from models import CriteriaResponse, ErrorResponse, ScoreResponse

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
    response_model=CriteriaResponse,
    responses={
        200: {"model": CriteriaResponse},
        400: {"model": ErrorResponse}
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
    response_model=ScoreResponse,
    responses={
        200: {"model": ScoreResponse},
        400: {"model": ErrorResponse}
    }
)
async def score_resumes(files: List[UploadFile], criteria: str = Form(...)):
    
    print("#"*30)
    
    try:
        # Convert criteria string to list
        criteria_dict = json.loads(criteria)

    except json.JSONDecodeError:
        return ScoreResponse(message = "Invalid input JSON format for criteria!!")
        
    try:
        # get criteria headers from criteria
        criteria_headers = await get_criteria_headers(criteria_dict["criteria"])
        if "Error" in criteria_headers.criteria_headers:
            return ScoreResponse(message="Failed to process due to criteria headers error")

        # dataframe to store results
        header_cols = ['Candidate Name'] + list(criteria_headers.criteria_headers.values())
        score_df = pd.DataFrame(columns=header_cols)

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
            scores_response = await get_candidate_scores(text_content, criteria_headers.criteria_headers)

            if scores_response.Candidate_Name == "Error":
                continue

            # Create a row with the correct column order using model attributes
            row_data = {
                'Candidate Name': scores_response.Candidate_Name,
                **scores_response.scores  # Unpack the scores dictionary
            }

            # in case the returned output is not the right order of columns, lets reorder it
            ordered_row = {col: row_data.get(col, None) for col in score_df.columns}

            # Add the row to DataFrame
            score_df.loc[len(score_df)] = ordered_row

        if len(score_df) == 0:
            return ScoreResponse(message="No valid resumes were processed successfully")

        # getting total score
        score_df["Total Score"] = score_df.iloc[:, 1:].sum(axis=1)

        # sorting the dataframe on total score
        score_df.sort_values(by = 'Total Score', ascending = False, inplace = True, ignore_index = True)

        score_df.to_csv("Resume scorer card.csv", index=False)
        
        return ScoreResponse(message="Scores are successfully generated and saved in csv file.")

    except Exception as e:
        print(f"Error: {str(e)}")
        return ScoreResponse(message="Failed to process resumes due to an error")