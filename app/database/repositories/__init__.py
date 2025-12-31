from .user_document import (
    user_uploads, update_document, add_supporting_doc, delete_document,
    list_user_documents, get_document
    )
# from .permission import require_admin, require_superadmin
from .document_parser import parse_cv_task
from .user import get_user_by_email, create_user, update_user, get_country_from_ip, get_client_ip
from .user_otp import create_otp, get_otp_by_type, delete_otp, delete_otp_by_type
from .permission import (
    require_admin, require_superadmin, 
    require_authenticated, require_permission, get_or_create_admin_role
    )
from .auth import get_current_user, get_user_by_email, authenticate_user, require_authenticated, get_user_by_id
# from .scraped_jobs import save_scraped_jobs