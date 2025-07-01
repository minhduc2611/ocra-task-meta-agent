from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from libs.weaviate_lib import (
    get_aggregate, search_non_vector_collection, insert_to_collection, 
    update_collection_object, delete_collection_object, COLLECTION_FINE_TUNING_MODELS
)
from weaviate.classes.query import Filter
from weaviate.collections.classes.grpc import Sort
import uuid
from data_classes.common_classes import FineTuningStatus, Language, UserRole

class FineTuningModelError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def get_fine_tuning_model_by_id(model_id: str) -> Optional[Dict[str, Any]]:
    """Get a fine-tuning model by ID"""
    try:
        models = search_non_vector_collection(
            collection_name=COLLECTION_FINE_TUNING_MODELS,
            filters=Filter.by_id().equal(model_id),
            limit=1,
            properties=["name", "description", "base_model", "status", "language", 
                       "created_at", "updated_at", "author", "training_data_path", 
                       "validation_data_path", "hyperparameters", "training_metrics", 
                       "model_path", "version"]
        )
        if models:
            model = models[0]
            return model
        return None
    except Exception as e:
        print(f"Error getting fine-tuning model by ID: {str(e)}")
        return None

def get_fine_tuning_model_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get a fine-tuning model by name"""
    try:
        filters = Filter.by_property("name").equal(name)
        models = search_non_vector_collection(
            collection_name=COLLECTION_FINE_TUNING_MODELS,
            filters=filters,
            limit=1,
            properties=["name", "description", "base_model", "status", "language", 
                       "created_at", "updated_at", "author", "training_data_path", 
                       "validation_data_path", "hyperparameters", "training_metrics", 
                       "model_path", "version"]
        )
        if models:
            model = models[0]
            return model
        return None
    except Exception as e:
        print(f"Error getting fine-tuning model by name: {str(e)}")
        return None

def get_all_fine_tuning_models(limit: int = 100, offset: int = 0, search: str = "", 
                              status: str = None, language: str = None) -> List[Dict[str, Any]]:
    """Get all fine-tuning models with pagination and filtering"""
    sort = Sort.by_property("created_at", ascending=False)
    filters = None
    
    # Build filters
    filter_conditions = []
    
    if search:
        name_filter = Filter.by_property("name").like(search)
        description_filter = Filter.by_property("description").like(search)
        filter_conditions.append(name_filter | description_filter)
    
    if status:
        status_filter = Filter.by_property("status").equal(status)
        filter_conditions.append(status_filter)
    
    if language:
        language_filter = Filter.by_property("language").equal(language)
        filter_conditions.append(language_filter)
    
    if filter_conditions:
        filters = filter_conditions[0]
        for condition in filter_conditions[1:]:
            filters = filters & condition
    
    try:
        models = search_non_vector_collection(
            collection_name=COLLECTION_FINE_TUNING_MODELS,
            limit=limit,
            offset=offset,
            properties=["name", "description", "base_model", "status", "language", 
                       "created_at", "updated_at", "author", "training_data_path", 
                       "validation_data_path", "hyperparameters", "training_metrics", 
                       "model_path", "version"],
            sort=sort,
            filters=filters
        )
        
        return models
    except Exception as e:
        print(f"Error getting all fine-tuning models: {str(e)}")
        return []

def create_fine_tuning_model(model_data: Dict[str, Any], author_id: str) -> str:
    """Create a new fine-tuning model"""
    try:
        # Check if model with same name already exists
        existing_model = get_fine_tuning_model_by_name(model_data["name"])
        if existing_model:
            raise FineTuningModelError("Model with this name already exists", 400)

        # Validate required fields
        required_fields = ["name", "base_model"]
        for field in required_fields:
            if field not in model_data or not model_data[field]:
                raise FineTuningModelError(f"Field '{field}' is required", 400)

        # Set default values
        model_data["status"] = model_data.get("status", FineTuningStatus.PENDING.value)
        model_data["language"] = model_data.get("language", Language.VI.value)
        model_data["created_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        model_data["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        model_data["author"] = author_id
        model_data["version"] = model_data.get("version", "1.0.0")

        # Validate status
        valid_statuses = [status.value for status in FineTuningStatus]
        if model_data["status"] not in valid_statuses:
            raise FineTuningModelError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}", 400)

        # Validate language
        valid_languages = [lang.value for lang in Language]
        if model_data["language"] not in valid_languages:
            raise FineTuningModelError(f"Invalid language. Must be one of: {', '.join(valid_languages)}", 400)

        # Insert model
        model_id = insert_to_collection(
            collection_name=COLLECTION_FINE_TUNING_MODELS,
            properties=model_data
        )
        
        if isinstance(model_id, uuid.UUID):
            model_id = str(model_id)
        
        if not model_id:
            raise FineTuningModelError("Failed to create fine-tuning model", 500)
        
        return model_id
    except FineTuningModelError:
        raise
    except Exception as e:
        print(f"Error creating fine-tuning model: {str(e)}")
        raise FineTuningModelError("Failed to create fine-tuning model", 500)

def update_fine_tuning_model(model_id: str, model_data: Dict[str, Any]) -> bool:
    """Update an existing fine-tuning model"""
    try:
        # Check if model exists
        existing_model = get_fine_tuning_model_by_id(model_id)
        if not existing_model:
            raise FineTuningModelError("Fine-tuning model not found", 404)

        # Check if name is being changed and if it conflicts
        if "name" in model_data and model_data["name"] != existing_model.get("name"):
            conflicting_model = get_fine_tuning_model_by_name(model_data["name"])
            if conflicting_model:
                raise FineTuningModelError("Model with this name already exists", 400)

        # Update timestamp
        model_data["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Remove fields that shouldn't be updated
        model_data.pop("created_at", None)
        model_data.pop("author", None)  # Author should not be changed

        # Validate status if provided
        if "status" in model_data:
            valid_statuses = [status.value for status in FineTuningStatus]
            if model_data["status"] not in valid_statuses:
                raise FineTuningModelError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}", 400)

        # Validate language if provided
        if "language" in model_data:
            valid_languages = [lang.value for lang in Language]
            if model_data["language"] not in valid_languages:
                raise FineTuningModelError(f"Invalid language. Must be one of: {', '.join(valid_languages)}", 400)

        # Update model
        success = update_collection_object(
            collection_name=COLLECTION_FINE_TUNING_MODELS,
            uuid=model_id,
            properties=model_data
        )
        
        if not success:
            raise FineTuningModelError("Failed to update fine-tuning model", 500)
        
        return True
    except FineTuningModelError:
        raise
    except Exception as e:
        print(f"Error updating fine-tuning model: {str(e)}")
        raise FineTuningModelError("Failed to update fine-tuning model", 500)

def delete_fine_tuning_model(model_id: str) -> bool:
    """Delete a fine-tuning model"""
    try:
        # Check if model exists
        existing_model = get_fine_tuning_model_by_id(model_id)
        if not existing_model:
            raise FineTuningModelError("Fine-tuning model not found", 404)

        # Check if model is in training (should not be deleted)
        if existing_model.get("status") == FineTuningStatus.TRAINING.value:
            raise FineTuningModelError("Cannot delete model while it is training", 400)

        # Delete model
        result = delete_collection_object(
            collection_name=COLLECTION_FINE_TUNING_MODELS,
            uuid=model_id
        )
        
        if not result:
            raise FineTuningModelError("Failed to delete fine-tuning model", 500)
        
        return True
    except FineTuningModelError:
        raise
    except Exception as e:
        print(f"Error deleting fine-tuning model: {str(e)}")
        raise FineTuningModelError("Failed to delete fine-tuning model", 500)

def check_fine_tuning_model_permissions(current_user: Dict[str, Any], target_model_id: str = None, action: str = "read") -> bool:
    """Check if current user has permissions for the action"""
    try:
        if not current_user:
            return False

        # Admin can do everything
        if current_user.get("role", UserRole.VIEWER.value) == UserRole.ADMIN.value:
            return True

        # For non-admin users
        if action == "list":
            # All authenticated users can list models
            return True
        elif action == "create":
            # Contributors and above can create models
            return current_user.get("role") in [UserRole.CONTRIBUTOR.value, UserRole.STUDENT.value]
        elif action in ["read", "update", "delete"]:
            # Users can only access models they created
            if not target_model_id:
                return False
            
            target_model = get_fine_tuning_model_by_id(target_model_id)
            if not target_model:
                return False
            
            return target_model.get("author") == current_user.get("uuid")
        else:
            return False
    except Exception as e:
        print(f"Error checking fine-tuning model permissions: {str(e)}")
        return False

def get_fine_tuning_model_stats():
    """Get statistics about fine-tuning models"""
    try:
        # Get total count
        total_filter = Filter.by_property("status").not_equal("")
        total_count = get_aggregate(COLLECTION_FINE_TUNING_MODELS, total_filter)
        
        # Get counts by status
        status_stats = {}
        for status in FineTuningStatus:
            status_filter = Filter.by_property("status").equal(status.value)
            count = get_aggregate(COLLECTION_FINE_TUNING_MODELS, status_filter)
            status_stats[status.value] = count
        
        # Get counts by language
        language_stats = {}
        for language in Language:
            language_filter = Filter.by_property("language").equal(language.value)
            count = get_aggregate(COLLECTION_FINE_TUNING_MODELS, language_filter)
            language_stats[language.value] = count
        
        return {
            "total": total_count,
            "by_status": status_stats,
            "by_language": language_stats
        }
    except Exception as e:
        print(f"Error getting fine-tuning model stats: {str(e)}")
        return {
            "total": 0,
            "by_status": {},
            "by_language": {}
        } 