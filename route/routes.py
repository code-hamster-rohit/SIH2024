from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from model.models import LoginCreds, ForgetPassword
from config.database import db, fs
from schema.schemas import convert_many_list_files
from bson import ObjectId
import io
import gridfs

router = APIRouter()

# /login?institute_id=123&email_id=abc&password=xyz
@router.get("/login")
async def login(institute_id: str, email_id: str, password: str):
    collection1 = db['MASTER_ADMIN_CREDS']
    if institute_id not in db.list_collection_names():
        admin_cred = collection1.find_one({'institute_id': institute_id})
        if admin_cred is None:
            return {"status": "400", "data": {}, "message": "Institute not found"}
        if email_id.lower() == admin_cred.get('email_id').lower():
            if admin_cred.get('password') == '':
                collection1.update_one({'institute_id': institute_id}, {'$set': {'password': password}})
                db.create_collection(institute_id)
                db.create_collection(institute_id + '_FILES')
                return {"status": "200", "data": {"roles": admin_cred.get('roles')}, "message": "Password set successfully"}
            elif admin_cred.get('password') == password:
                return {"status": "200", "data": {"roles": admin_cred.get('roles')}, "message": "Login successful"}
            else:
                return {"status": "400", "data": {}, "message": "Invalid password"}
        else:
            return {"status": "400", "data": {}, "message": "Invalid email_id"}
    else:
        collection2 = db[institute_id]
        admin_cred = collection1.find_one({'institute_id': institute_id})
        if admin_cred is None:
            return {"status": "400", "data": {}, "message": "Institute not found"}
        if admin_cred.get('email_id').lower() == email_id.lower():
            if admin_cred.get('password') == password:
                return {"status": "200", "data": {"roles": admin_cred.get('roles')}, "message": "Login successful"}
            else:
                return {"status": "400", "data": {}, "message": "Invalid password"}
        user_cred = collection2.find_one({'email_id': email_id.lower()})
        if user_cred is None:
            return {"status": "400", "data": {}, "message": "User not found"}
        if user_cred.get('password') == '':
            collection2.update_one({'email_id': email_id.lower()}, {'$set': {'password': password}})
            return {"status": "200", "data": {"roles": user_cred.get('roles')}, "message": "Password set successfully"}
        elif user_cred.get('password') == password:
            return {"status": "200", "data": {"roles": user_cred.get('roles')}, "message": "Login successful"}
        else:
            return {"status": "400", "data": {}, "message": "Invalid password"}


# /add_user?institute_id=123&email_id=abc&password=xyz&roles=[role1,role2]
@router.post("/add_user")
async def add_user(cred: LoginCreds):
    collection = db[cred.institute_id]
    cred_dict = dict(cred)
    cred_dict.pop('institute_id')
    cred_dict['email_id'] = cred_dict['email_id'].lower()
    cred_dict['_id'] = ObjectId()
    collection.insert_one(cred_dict)
    return {"status": "200", "data": {"id": str(cred_dict['_id']), "roles": cred_dict['roles']}, "message": "User added successfully"}

# /forget_password?institute_id=123&email_id=abc
@router.get("/forget_password")
async def forget_password(cred: ForgetPassword):
    collection = db[cred.institute_id]
    user_cred = collection.find_one({'email_id': cred.email_id.lower()})
    if user_cred is None:
        return {"status": "400", "data": {}, "message": "User not found"}
    collection.update_one({'email_id': cred.email_id.lower()}, {'$set': {'password': ''}})
    return {"status": "200", "data": {}, "message": "Password reset successfully"}

# upload_file?institute_id=123&file_name=abc&file_type=xyz&description=desc&file=abx.pdf&roles=[role1,role2]
@router.post("/upload_file")
async def upload_file(institute_id: str = Form(...), roles: str = Form(...), file_name: str = Form(...), file_type: str = Form(...), description: str = Form(...), file: UploadFile = File(...)):
    try:

        file_dict = {
            'institute_id': institute_id,
            'roles': roles,
            'file_name': file_name.lower(),
            'file_type': file_type,
            'description': description
        }

        collection = db[institute_id + '_FILES']

        existing_file = collection.find_one({'file_name': file_dict['file_name']})
        if existing_file:
            return {'file_id': str(existing_file['_id']), 'file_size': existing_file['file_size'], 'message': 'File already exists.'}
        
        file_id = ObjectId()
        fs.put(file.file, filename=file.filename, _id=file_id, content_type=file.content_type)

        file_size = fs.get(file_id).length

        file_dict['_id'] = file_id
        file_dict['file_id'] = str(file_id)
        file_dict['file_size'] = file_size

        collection.insert_one(file_dict)
        
        return {'file_id': str(file_id), 'file_size': file_size, 'message': 'File uploaded successfully'}
    
    except Exception as e:
        return {'file_id': None, 'message': str(e)}
    
# /list_files?institute_id=123
@router.get("/list_files")
async def list_files(institute_id: str):
    try:
        collection = db[institute_id + '_FILES']
        files = collection.find()
        if files is None:
            return {'files_meta_data': [], 'message': 'No files found'}
        return {'files_meta_data': convert_many_list_files(files), 'message': 'Files listed successfully'}
    except Exception as e:
        return {'files_meta_data': [], 'message': str(e)}

# /download_file?&file_id=abc
@router.get("/download_file")
async def download_file(file_id: str):
    try:
        file = fs.get(ObjectId(file_id))
        headers = {"Content-Disposition": f"attachment; filename={file.filename}"}
        return StreamingResponse(io.BytesIO(file.read()), media_type=file.content_type, headers=headers)
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="File not found")

# /peek_file?file_id=abc[&max_size=1024]
@router.get("/peek_file")
async def peek_file(file_id: str, max_size: int = 1024):
    try:
        file = fs.get(ObjectId(file_id))
        file_content = file.read(max_size)
        content_type = file.content_type
        
        return StreamingResponse(io.BytesIO(file_content), media_type=content_type)
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="File not found")
    
# /create_visualization?files=[abc.pdf, xyz.xlsx,...]&custom_query=pqrst&viz_type=bar_chart
@router.post("/create_visualization")
async def create_visualization(files: list, custom_query: str, viz_type: str):
    pass
