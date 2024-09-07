from pydantic import BaseModel

class LoginCreds(BaseModel):
    institute_id: str
    email_id: str
    password: str = ''
    roles: list = ['student']

class ForgetPassword(BaseModel):
    institute_id: str
    email_id: str

class FileMetaData(BaseModel):
    institute_id: str
    roles: list = ['student']
    file_name: str
    file_type: str
    description: str