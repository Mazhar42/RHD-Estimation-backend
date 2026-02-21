from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from .. import crud, schemas, models
from ..security import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    is_superadmin,
    get_db
)
import logging

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.Token)
def register(user: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        logger.info(f"Registration attempt for username: {user.username}, email: {user.email}")
        
        # Check if username already exists
        existing_user = crud.get_user_by_username(db, user.username)
        if existing_user:
            logger.warning(f"Username already exists: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        existing_email = crud.get_user_by_email(db, user.email)
        if existing_email:
            logger.warning(f"Email already exists: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        is_first_user = crud.get_user_count(db) == 0

        # Create the user
        db_user = crud.create_user(db, user)
        logger.info(f"User created successfully: {db_user.username} (ID: {db_user.user_id})")
        
        role_name = "superadmin" if is_first_user else "user"
        role_description = f"System {role_name} role"

        user_role = crud.get_role_by_name(db, role_name)
        if not user_role:
            user_role = crud.create_role(
                db,
                schemas.RoleCreate(name=role_name, description=role_description),
                is_system_role=True
            )
            logger.info(f"Created default '{role_name}' role")
        
        crud.assign_role_to_user(db, db_user.user_id, user_role.role_id)
        logger.info(f"Assigned '{role_name}' role to {db_user.username}")
        
        # Refresh to get roles
        db.refresh(db_user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.username, "user_id": db_user.user_id},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Registration successful for {db_user.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": db_user
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Registration error: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

from fastapi.security import OAuth2PasswordRequestForm

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    try:
        logger.info(f"Login attempt for: {form_data.username}")
        
        # Try to find user by username
        db_user = crud.get_user_by_username(db, form_data.username)
        
        # If not found by username, try by email
        if not db_user:
            db_user = crud.get_user_by_email(db, form_data.username)
        
        if not db_user:
            logger.warning(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(form_data.password, db_user.hashed_password):
            logger.warning(f"Password verification failed for user: {db_user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not db_user.is_active:
            logger.warning(f"Inactive user login attempt: {db_user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.username, "user_id": db_user.user_id},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Login successful for user: {db_user.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": db_user
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Login error: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=schemas.User)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user

@router.post("/change-password")
def change_password(
    password_change: schemas.UserPasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    # Verify old password
    if not verify_password(password_change.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid current password"
        )
    
    # Update password
    update_data = schemas.UserUpdate(password=password_change.new_password)
    crud.update_user(db, current_user.user_id, update_data)
    
    return {"message": "Password changed successfully"}

# =============== Admin Endpoints ===============

@router.post("/users", response_model=schemas.User)
def create_new_user(
    user: schemas.UserCreate,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Create a new user (superadmin only)."""
    # Check if username already exists
    existing_user = crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing_email = crud.get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create user
    db_user = crud.create_user(db, user)
    
    # Assign default user role
    user_role = crud.get_role_by_name(db, "user")
    if not user_role:
        user_role = crud.create_role(db, schemas.RoleCreate(name="user", description="Default user role"))
    
    crud.assign_role_to_user(db, db_user.user_id, user_role.role_id)
    db.refresh(db_user)
    
    return db_user

@router.get("/users", response_model=list[schemas.User])
def list_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """List all users (superadmin only)."""
    return crud.get_all_users(db, skip=skip, limit=limit)

@router.get("/users/{user_id}", response_model=schemas.User)
def get_user(
    user_id: int,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Get a specific user (superadmin only)."""
    db_user = crud.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/users/{user_id}", response_model=schemas.User)
def update_user_info(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Update a user (superadmin only)."""
    db_user = crud.update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.post("/users/{user_id}/deactivate", response_model=schemas.User)
def deactivate_user_endpoint(
    user_id: int,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Deactivate a user (superadmin only)."""
    db_user = crud.deactivate_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.post("/users/{user_id}/activate", response_model=schemas.User)
def activate_user_endpoint(
    user_id: int,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Activate a user (superadmin only)."""
    db_user = crud.activate_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

# =============== Role Endpoints ===============

@router.post("/roles", response_model=schemas.Role)
def create_new_role(
    role: schemas.RoleCreate,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Create a new role (superadmin only)."""
    existing_role = crud.get_role_by_name(db, role.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already exists"
        )
    
    db_role = crud.create_role(db, role, is_system_role=False)
    return db_role

@router.get("/roles", response_model=list[schemas.Role])
def list_all_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """List all roles (superadmin only)."""
    return crud.get_all_roles(db, skip=skip, limit=limit)

@router.get("/roles/{role_id}", response_model=schemas.Role)
def get_role(
    role_id: int,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Get a specific role (superadmin only)."""
    db_role = crud.get_role_by_id(db, role_id)
    if not db_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return db_role

@router.put("/roles/{role_id}", response_model=schemas.Role)
def update_role_info(
    role_id: int,
    role_update: schemas.RoleUpdate,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Update a role (superadmin only)."""
    db_role = crud.get_role_by_id(db, role_id)
    if not db_role or db_role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles"
        )
    
    db_role = crud.update_role(db, role_id, role_update)
    if not db_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return db_role

@router.delete("/roles/{role_id}")
def delete_role_endpoint(
    role_id: int,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Delete a role (superadmin only)."""
    success = crud.delete_role(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role or role not found"
        )
    return {"message": "Role deleted successfully"}

@router.post("/users/{user_id}/roles/{role_id}")
def assign_role_to_user_endpoint(
    user_id: int,
    role_id: int,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Assign a role to a user (superadmin only)."""
    success = crud.assign_role_to_user(db, user_id, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User or role not found"
        )
    return {"message": "Role assigned successfully"}

@router.delete("/users/{user_id}/roles/{role_id}")
def remove_role_from_user_endpoint(
    user_id: int,
    role_id: int,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Remove a role from a user (superadmin only)."""
    success = crud.remove_role_from_user(db, user_id, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User or role not found"
        )
    return {"message": "Role removed successfully"}

# =============== Permission Endpoints ===============

@router.post("/permissions", response_model=schemas.Permission)
def create_new_permission(
    permission: schemas.PermissionCreate,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Create a new permission (superadmin only)."""
    existing_permission = crud.get_permission_by_name(db, permission.name)
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already exists"
        )
    
    db_permission = crud.create_permission(db, permission)
    return db_permission

@router.get("/permissions", response_model=list[schemas.Permission])
def list_all_permissions(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """List all permissions (superadmin only)."""
    return crud.get_all_permissions(db, skip=skip, limit=limit)

@router.post("/roles/{role_id}/permissions/{permission_id}")
def assign_permission_to_role_endpoint(
    role_id: int,
    permission_id: int,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Assign a permission to a role (superadmin only)."""
    success = crud.assign_permission_to_role(db, role_id, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role or permission not found"
        )
    return {"message": "Permission assigned successfully"}

@router.delete("/roles/{role_id}/permissions/{permission_id}")
def remove_permission_from_role_endpoint(
    role_id: int,
    permission_id: int,
    current_user: models.User = Depends(is_superadmin),
    db: Session = Depends(get_db)
):
    """Remove a permission from a role (superadmin only)."""
    success = crud.remove_permission_from_role(db, role_id, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role or permission not found"
        )
    return {"message": "Permission removed successfully"}
