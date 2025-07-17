"""
Fine-tuning controller for handling fine-tuning requests.
"""

from flask import request, jsonify, g
from __init__ import app, login_required
from services.handle_messages import fine_tune_messages, get_messages_list
from services.handle_fine_tuning_models import get_fine_tuning_model_by_id, update_fine_tuning_model, FineTuningModelError
from data_classes.common_classes import FineTuningStatus, ApprovalStatus
from libs.jsonl_converter import convert_json_to_jsonl, save_jsonl_to_file, validate_fine_tune_data
import logging
from libs.google_vertex import get_fine_tuning_job_list, upload_to_gcs
logger = logging.getLogger(__name__)

@app.route('/api/v1/fine-tuning/start', methods=['POST'])
@login_required
def start_fine_tuning():
    """Start a fine-tuning job with selected messages"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get parameters
        # message_ids = data.get("message_ids", [])
        model_id = data.get("model_id")
        base_model = data.get("base_model", "gemini-2.5-flash")
        modes = data.get("mode")
        
        if not modes:
            return jsonify({"error": "mode must be provided"}), 400
        
        # if not message_ids:
        #     return jsonify({"error": "message_ids must be provided"}), 400

        result = get_messages_list(
            limit=1000,
            include_related=True,
            approval_status=ApprovalStatus.APPROVED.value
        )
        if "error" in result:
            return jsonify({"error": f"Failed to get messages: {result['error']}"}), 400
        messages = result.get("messages", [])
        
        if not messages:
            return jsonify({"error": "No messages found for fine-tuning"}), 400
        
        
        # Start fine-tuning
        result = fine_tune_messages(messages, base_model)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        # Update model status if model_id is provided
        if model_id:
            try:
                update_fine_tuning_model(model_id, {
                    "status": FineTuningStatus.TRAINING.value,
                    "training_data_path": result.get("training_data_path"),
                    "hyperparameters": result.get("job_info", {}).get("hyperparameters")
                })
            except FineTuningModelError as e:
                logger.warning(f"Failed to update model status: {e.message}")
        
        return jsonify({
            "message": "Fine-tuning job started successfully",
            "job_info": result.get("job_info"),
            "training_pairs_count": result.get("training_pairs_count")
        }), 200
        
    except Exception as e:
        logger.error(f"Error in start_fine_tuning: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# @app.route('/api/v1/fine-tuning/job-status/<job_name>', methods=['GET'])
# @login_required
# def get_fine_tuning_job_status(job_name):
#     """Get the status of a fine-tuning job"""
#     try:
#         from google.cloud import aiplatform
#         from vertexai.preview.fine_tuning import FineTuningJob
        
#         # Initialize Vertex AI
#         project_id = "llm-project-2d719"
#         location = "us-central1"
#         aiplatform.init(project=project_id, location=location)
        
#         # Get job status
#         job = FineTuningJob.get(job_name)
        
#         return jsonify({
#             "job_name": job.name,
#             "display_name": job.display_name,
#             "status": job.state.name,
#             "created_at": job.create_time.isoformat(),
#             "updated_at": job.update_time.isoformat() if job.update_time else None,
#             "base_model": job.base_model,
#             "training_data": job.training_data,
#             "tuned_model": job.tuned_model.name if job.tuned_model else None
#         }), 200
        
#     except Exception as e:
#         logger.error(f"Error in get_fine_tuning_job_status: {str(e)}")
#         return jsonify({"error": f"Failed to get job status: {str(e)}"}), 500



@app.route('/api/v1/fine-tuning/jobs', methods=['GET'])
@login_required
def list_fine_tuning_jobs():
    """List all fine-tuning jobs"""
    try:
        
        # List jobs
        jobs = get_fine_tuning_job_list()
        job_list = []
        for job in jobs:
            job_list.append({
                "job_name": job["name"],
                "display_name": job["tunedModelDisplayName"],
                "status": job["state"],
                "created_at": job["createTime"],
                "updated_at": job["updateTime"] if job["updateTime"] else None,
                "base_model": job["baseModel"],
                "tuned_model": job["tunedModelDisplayName"] if job["tunedModelDisplayName"] else None
            })
        
        return jsonify({
            "jobs": job_list,
            "count": len(job_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in list_fine_tuning_jobs: {str(e)}")
        return jsonify({"error": f"Failed to list jobs: {str(e)}"}), 500 