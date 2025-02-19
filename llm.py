import os
from openai import OpenAI
from dotenv import load_dotenv

# loading API key from .env file
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# function that takes prompt as input and generate the result
def generate_response(query):

    max_retries = 5
    attempt = 1

    system_prompt = """
    You are a world-class AI system, capable of complex reasoning and iterative reflection. For every query, follow this structured process:

    1. Thinking Phase:
    - Analyze the query inside <thinking> tags.
    - Outline your initial reasoning step-by-step, considering all relevant details, constraints, and possible approaches.

    2. Reflection Phase:
    - Review your initial reasoning inside <reflection> tags.
    - Evaluate whether the initial thinking is accurate, complete, and aligned with the query’s requirements.
    - Identify any errors, gaps, or overlooked factors. If any are found, clearly state them here.

    3. Rethinking Phase:
    - Based on your reflection, rethink the query inside <rethinking> tags.
    - Refine or expand upon your initial thinking to correct errors, address gaps, improve the approach and make sure it follows every detail mentioned in the query.
    - Missing any detail from the query and ignoring it can result into a penalty.
    
    4. Final Output:
    - Repeat Thinking, Reflection and Rethinking phase(at least 2 times and at max 3 times) until you are satisifed with the response and it meets every requirement of the query.  
    - Provide your finalized response inside <output> tags, ensuring it is clear, concise, and actionable."""
    
    while attempt <= max_retries:
        try:
            result = client.chat.completions.create(
                    model='gpt-4o',
                    messages=[{"role":"system", "content":system_prompt},
                             {"role":"user", "content":query}],
                    temperature=0, 
                    store= False,
                    max_tokens = 4096,
                    response_format = {"type":"json_object"})

            result = result.choices[0].message.content
            print('\n','#'*20)
            print('Raw response: ', result)
            print('#'*20,'\n')
            return result
    
        except Exception as e:
            print(e)
            attempt += 1
            print('OpenAI Response Error while generating response!!')
            
            
# prompt to extract the criteria from the Job description
def get_ranking_criteria_prompt(content, error_correction_prompt = ""):

    prompt = f"""<context>
You are an expert at analyzing job descriptions and extracting key details. 
Your task is to analyze the provided job description and extract **ranking criteria** that are relevant for evaluating candidates. 
These criteria should be directly based on the job description and may include **skills, certifications, experience, qualifications, etc.** 

The extracted criteria will be used to rank employees and determine the best fit for the job.

Here is the job description:
{content}
</context>

<format>
OUTPUT REQUIREMENTS:
- The output must be in **valid JSON format only**, with no additional text or explanations.
- Example output format:
{{
    "criteria": [
        "Must have certification XYZ",
        "5+ years of experience in Python development",
        "Strong background in Machine Learning"
    ]
}}
</format>

<rules>
- **Only extract information explicitly stated in the job description.** Do not assume or infer any details.  
- **Do not add commentary** or explanations—return only the JSON output.  
- If a category (skills, experience, certifications, qualifications) is not mentioned in the job description, exclude it from the output.  
- Don't make it too extensive that the criteria are too many to analyze on.
- If the role is technical, then give importance to technical criteria and discard non-technical stuff and vice-versa.
</rules>

{error_correction_prompt}
"""

    return prompt

    
# Prompt to get criteria header from extracted criteria
def get_criteria_header_prompt(criteria_list, error_correction_prompt = ""):

    prompt = f"""<context>
You are an expert at generating criteria headers from given criteria which are used to determine how fit a candidate is for a job.
The criteria has been extracted from the job description.

Here's the list of criteria: {criteria_list}
</context>

<format_guidelines>
Technical criteria examples:
- "5+ years of experience in Python development" → "Python Experience"
- "Must have AWS cloud certification" → "AWS Certification"
- "Experience with CI/CD pipelines" → "CI/CD Experience"

Non-technical criteria examples:
- "Strong communication skills" → "Communication Skills"
- "Team leadership experience" → "Team Leadership"
- "Project management background" → "Project Management"
</format_guidelines>

<format>
Response must be valid JSON:
{{
    "Must have certification XYZ": "Certification XYZ",
    "Another criterion": "Its Header"
}}
</format>

<example>
Input criteria: ["Must have certification XYZ", "5+ years of experience in Python development", "Strong background in Machine Learning"]

Response: 
{{
    "criteria_headers": {{
        "Must have certification XYZ": "Certification XYZ",
        "5+ years of experience in Python development": "Python Experience",
        "Strong background in Machine Learning": "Machine Learning"
    }}
}}
</example>

<rules>
- The output must be in **valid JSON format only**, with no additional text or explanations.
- Don't miss out on any criteria. For each criteria, there should be a criteria header.
- The order of the returned criteria headers should also remain the same as the provided criteria.
- Use title casing for the criteria headers, where first letter of every word is uppercase and rest are lower case.
- If the provided criteria is technical, then make sure the criteria headers also look technical and vice-versa for non-technical criteria.
- Make sure the criteria headers are not too lengthy(not more than 3 words). Anything above 3 words is not acceptable.
- Also, the criteria header should convey the same meaning as the criteria, so it should be accurate and not too lengthy.
</rules>

{error_correction_prompt}
"""
    
    return prompt

# prompt to get scores on the resume content based on the criteria
def get_scoring_prompt(content, criteria_headers, error_correction_prompt = ""):

    prompt = f"""<context>
You are an expert at evaluating candidate's resume content based on the provided criteria. 
Your task is given a candidate's resume content and criteria(along with its headers), you need to score the candidate by analyzing the resume content on each criteria out of 10.

Here's the candidate's resume content: {content}

And here's the criteria along with the headers: {criteria_headers}
</context>

<scoring_guidelines>
- 5: Exceeds requirement significantly
- 4: Fully meets requirement with additional relevant experience
- 3: Meets basic requirement
- 2: Partially meets requirement
- 1: Minimal relevant experience
- 0: No relevant experience OR No information available to assess
</scoring_guidelines>

<format>
Response format:
{{
    "Candidate Name": "Extract the name of the candidate from the resume"
    "Criterion 1 Header": score,
    "Criterion 2 Header": score
    // ... for all criteria
}}
</format>

<example>
Resume content: "John Doe - Software Engineer
5 years of Python development experience at Tech Corp
Masters in Computer Science
Implemented ML models for classification"

Criteria headers: {{
    "Must have certification XYZ": "Certification XYZ",
    "5+ years of experience in Python development": "Python Experience",
    "Strong background in Machine Learning": "Machine Learning"
}}

Response:
{{
    "Candidate Name": "John Doe",
    "Certification XYZ": 0,
    "Python Experience": 4,
    "Machine Learning": 3
}}
</example>

<rules>
1. Output must be valid JSON only, with no additional text
2. Evaluate all criteria even if not mentioned in resume
3. Return scores in same order as provided criteria
4. Use consistent key naming:
   - Use title case for first letter of each word
   - Avoid special characters except underscores
5. Scoring rules:
   - Use whole numbers from 0 to 5
   - Don't make assumptions about unstated experience/skills
6. For partial matches:
   - Score proportionally to how well requirement is met
   - Document clear shortfalls with lower scores
</rules>

{error_correction_prompt}
"""
    
    return prompt