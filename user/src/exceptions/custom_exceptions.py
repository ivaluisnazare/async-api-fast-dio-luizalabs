from fastapi import HTTPException, status

class UserException(HTTPException):
    """Base exception for user-related errors"""
    pass

class UserNotFoundException(UserException):
    def __init__(self, user_id: int = None, username: str = None):
        if user_id is not None:
            detail = f"User with id {user_id} not found"
        elif username is not None:
            detail = f"User with username {username} not found"
        else:
            detail = "User not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class DuplicateUserException(UserException):
    def __init__(self, username: str = None, email: str = None):
        if username:
            detail = f"User with username {username} already exists"
        elif email:
            detail = f"User with email {email} already exists"
        else:
            detail = "User already exists"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class InvalidCredentialsException(UserException):
    def __init__(self):
        detail = "Invalid username or password"
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class InactiveUserException(UserException):
    def __init__(self):
        detail = "Inactive user"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)