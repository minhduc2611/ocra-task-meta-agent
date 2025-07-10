# Fine-Tuning with Google Vertex AI

This document describes the fine-tuning functionality implemented for Google Vertex AI models.

## Overview

The fine-tuning system allows you to:
- Convert conversation data to the required format for Vertex AI fine-tuning
- Convert JSON data to JSONL format
- Start fine-tuning jobs with Google Vertex AI
- Monitor fine-tuning job status
- Validate data formats

## Data Format

### Input Format (Messages from Database)

Messages should have the following structure:
```json
{
  "content": "message content",
  "role": "user" or "assistant",
  "session_id": "session identifier",
  "related_message": {
    "content": "related message content",
    "role": "user" or "assistant"
  }
}
```

### Fine-Tuning Format (Vertex AI)

The system converts messages to this format:
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "user message"}]
    },
    {
      "role": "model",
      "parts": [{"text": "assistant response"}]
    }
  ]
}
```

### JSONL Format

For Vertex AI fine-tuning, data is converted to JSONL format where each line is a valid JSON object:
```jsonl
{"contents":[{"role":"user","parts":[{"text":"What is Buddhism?"}]},{"role":"model","parts":[{"text":"Buddhism is a spiritual tradition..."}]}]}
{"contents":[{"role":"user","parts":[{"text":"How can I be more mindful?"}]},{"role":"model","parts":[{"text":"Practice mindfulness through meditation..."}]}]}
```

## API Endpoints

### 1. Start Fine-Tuning Job

**POST** `/api/v1/fine-tuning/start`

Start a fine-tuning job with selected messages.

**Request Body:**
```json
{
  "message_ids": ["uuid1", "uuid2"],  // Optional: specific message IDs
  "session_id": "session_uuid",       // Optional: all messages from session
  "model_id": "model_uuid",           // Optional: fine-tuning model ID
  "base_model": "gemini-1.5-flash-001", // Optional: base model to fine-tune
  "hyperparameters": {                // Optional: training parameters
    "epoch_count": 3,
    "batch_size": 4,
    "learning_rate": 0.0001
  }
}
```

**Response:**
```json
{
  "message": "Fine-tuning job started successfully",
  "job_info": {
    "job_name": "projects/.../locations/.../trainingPipelines/...",
    "display_name": "fine_tuned_model_20241201_143022",
    "base_model": "gemini-1.5-flash-001",
    "status": "PIPELINE_STATE_PENDING",
    "created_at": "2024-12-01T14:30:22.123456Z",
    "training_data_path": "/path/to/training/data.jsonl",
    "hyperparameters": {
      "epoch_count": 3,
      "batch_size": 4,
      "learning_rate": 0.0001
    }
  },
  "training_pairs_count": 150
}
```

### 2. Convert JSON to JSONL

**POST** `/api/v1/fine-tuning/convert-json`

Convert JSON data to JSONL format.

**Request Body:**
```json
{
  "data": [
    {
      "contents": [
        {"role": "user", "parts": [{"text": "Question?"}]},
        {"role": "model", "parts": [{"text": "Answer."}]}
      ]
    }
  ],
  "filename": "custom_filename.jsonl"  // Optional
}
```

**Response:**
```json
{
  "message": "JSON converted to JSONL successfully",
  "jsonl_content": "{\"contents\":[...]}\n",
  "file_path": "/path/to/file.jsonl",
  "records_count": 1
}
```

### 3. Validate Data Format

**POST** `/api/v1/fine-tuning/validate-data`

Validate that data is in the correct format for fine-tuning.

**Request Body:**
```json
{
  "data": [
    {
      "contents": [
        {"role": "user", "parts": [{"text": "Question?"}]},
        {"role": "model", "parts": [{"text": "Answer."}]}
      ]
    }
  ]
}
```

**Response:**
```json
{
  "message": "Data format is valid",
  "records_count": 1
}
```

### 4. Get Job Status

**GET** `/api/v1/fine-tuning/job-status/<job_name>`

Get the status of a fine-tuning job.

**Response:**
```json
{
  "job_name": "projects/.../locations/.../trainingPipelines/...",
  "display_name": "fine_tuned_model_20241201_143022",
  "status": "PIPELINE_STATE_RUNNING",
  "created_at": "2024-12-01T14:30:22.123456Z",
  "updated_at": "2024-12-01T14:35:15.654321Z",
  "base_model": "gemini-1.5-flash-001",
  "training_data": "gs://bucket/path/to/data.jsonl",
  "tuned_model": "projects/.../locations/.../models/..."  // Available when complete
}
```

### 5. List Fine-Tuning Jobs

**GET** `/api/v1/fine-tuning/jobs`

List all fine-tuning jobs.

**Response:**
```json
{
  "jobs": [
    {
      "job_name": "projects/.../locations/.../trainingPipelines/...",
      "display_name": "fine_tuned_model_20241201_143022",
      "status": "PIPELINE_STATE_SUCCEEDED",
      "created_at": "2024-12-01T14:30:22.123456Z",
      "updated_at": "2024-12-01T16:45:30.123456Z",
      "base_model": "gemini-1.5-flash-001",
      "tuned_model": "projects/.../locations/.../models/..."
    }
  ],
  "count": 1
}
```

## Usage Examples

### Python Code Example

```python
from services.handle_messages import fine_tune_messages
from libs.jsonl_converter import convert_json_to_jsonl, validate_fine_tune_data

# Example 1: Fine-tune messages from database
messages = [
    {
        "content": "What is Buddhism?",
        "role": "user",
        "related_message": {
            "content": "Buddhism is a spiritual tradition...",
            "role": "assistant"
        }
    }
]

result = fine_tune_messages(messages)
print(result)

# Example 2: Convert custom data to JSONL
custom_data = [
    {
        "contents": [
            {"role": "user", "parts": [{"text": "Hello"}]},
            {"role": "model", "parts": [{"text": "Hi there!"}]}
        ]
    }
]

# Validate first
validate_fine_tune_data(custom_data)

# Convert to JSONL
jsonl_content = convert_json_to_jsonl(custom_data)
print(jsonl_content)
```

### cURL Examples

```bash
# Start fine-tuning with session messages
curl -X POST http://localhost:5000/api/v1/fine-tuning/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_uuid",
    "base_model": "gemini-1.5-flash-001"
  }'

# Convert JSON to JSONL
curl -X POST http://localhost:5000/api/v1/fine-tuning/convert-json \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "contents": [
          {"role": "user", "parts": [{"text": "Question?"}]},
          {"role": "model", "parts": [{"text": "Answer."}]}
        ]
      }
    ]
  }'

# Get job status
curl -X GET http://localhost:5000/api/v1/fine-tuning/job-status/JOB_NAME \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

### Google Cloud Setup

1. Ensure you have the Google Cloud SDK installed
2. Set up authentication:
   ```bash
   gcloud auth application-default login
   ```
3. Set the project ID:
   ```bash
   gcloud config set project llm-project-2d719
   ```

### Environment Variables

Make sure these are set in your `.env` file:
```
GOOGLE_CLOUD_PROJECT=llm-project-2d719
GOOGLE_CLOUD_LOCATION=us-central1
```

## Testing

Run the test script to verify functionality:

```bash
python test_fine_tuning.py
```

This will test:
- JSON to JSONL conversion
- Message format conversion
- Data validation
- File saving

## Error Handling

The system includes comprehensive error handling:

- **Validation Errors**: Invalid data format
- **Authentication Errors**: Missing or invalid tokens
- **Google Cloud Errors**: API failures, quota limits
- **File System Errors**: Permission issues, disk space

## Best Practices

1. **Data Quality**: Ensure conversation pairs are high-quality and relevant
2. **Data Size**: Aim for at least 100-500 conversation pairs for effective fine-tuning
3. **Validation**: Always validate data before starting fine-tuning
4. **Monitoring**: Check job status regularly during training
5. **Backup**: Keep copies of your training data
6. **Testing**: Test fine-tuned models thoroughly before deployment

## Limitations

- Vertex AI fine-tuning is currently in preview
- Supported base models: `gemini-1.5-flash-001`
- Training data must be in JSONL format
- Maximum file size: 100MB
- Training time varies based on data size and model complexity

## Troubleshooting

### Common Issues

1. **Authentication Error**: Ensure Google Cloud credentials are properly set up
2. **Invalid Data Format**: Use the validation endpoint to check data structure
3. **Job Fails**: Check Google Cloud Console for detailed error messages
4. **File Not Found**: Ensure training data file exists and is accessible

### Getting Help

- Check Google Cloud Console for job logs
- Review the application logs for detailed error messages
- Use the validation endpoints to debug data format issues 