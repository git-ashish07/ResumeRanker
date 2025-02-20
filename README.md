# Resume Ranker API

## Overview
A FastAPI-based service that automates resume evaluation by extracting key criteria from job descriptions and scoring resumes against them. The API uses OpenAI's GPT models to analyze documents and provide objective scoring, making it easier for HR teams and recruiters to process multiple applications efficiently.

## Features
- Extract ranking criteria automatically from job descriptions
- Score multiple resumes against defined criteria
- Support for both PDF and DOCX file formats
- Scoring scale from 0-5 for detailed candidate evaluation
- Export results to CSV for easy analysis
- RESTful API with comprehensive documentation
- Retry mechanism for reliable API responses

## Prerequisites
- Python 3.8 or higher
- OpenAI API key

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/git-ashish07/ResumeRanker.git
   cd ResumeRanker
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory:
   ```bash
   echo OPENAI_API_KEY=your-api-key-here > .env
   ```

## Environment Setup
1. Ensure your `.env` file contains your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

2. Verify all dependencies are installed:
   ```bash
   pip list
   ```

## Running the API
1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. Access the API:
   - Main API: http://localhost:8000
   - Interactive docs/Swagger UI: http://localhost:8000/docs
   - API documentation: http://localhost:8000/redoc

## API Endpoints
### 1. Extract Criteria
- **Endpoint**: `/extract-criteria`
- **Method**: POST
- **Input**: Job description file (PDF/DOCX)

- **Example response**:
  ```json
  {
      "criteria": [
          "5+ years of Python development",
          "Experience with AWS",
          "Strong communication skills"
      ]
  }
  ```

### 2. Score Resumes
- **Endpoint**: `/score-resumes`
- **Method**: POST
- **Input**: 
  - Multiple resume files (PDF/DOCX)
  - Criteria JSON from previous step
- **Output**: Generates "Resume scorer card.csv" with detailed scores

## File Support
- **Supported formats**:
  - PDF (.pdf)
  - Microsoft Word (.docx)
- **File requirements**:
  - Text must be machine-readable
  - Clear formatting recommended

## Output Format
The generated CSV file includes:
- Candidate Name
- Individual scores (0-5) for each criterion
- Total score
- Scoring scale:
  - 5: Exceeds requirement significantly
  - 4: Meets with additional experience
  - 3: Meets basic requirement
  - 2: Partially meets
  - 1: Minimal experience
  - 0: No relevant experience

## Troubleshooting
- **API not starting**: 
  - Check if port 8000 is available
  - Verify Python version compatibility
  - Ensure all dependencies are installed

- **File processing errors**:
  - Verify file format is supported
  - Check if file is corrupted
  - Ensure file is text-searchable

- **Scoring issues**:
  - Validate OpenAI API key
  - Check internet connectivity
  - Verify JSON format of criteria by enabling print statements or setting up logs