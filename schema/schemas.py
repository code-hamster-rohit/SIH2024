def convert_one_login_creds(cred):
    return {
        "id": str(cred['_id']),
        "institute_id": cred['institute_id'],
        "email_id": cred['email_id'],
        "password": cred['password'],
        "roles": cred['roles']
    }

def convert_many_login_creds(creds):
    return [convert_one_login_creds(cred) for cred in creds]

def convert_one_list_file(file):
    return {
        "institute_id": file['institute_id'],
        "roles": file['roles'],
        "file_id": file['file_id'],
        "file_name": file['file_name'],
        "file_type": file['file_type'],
        "description": file['description']
    }

def convert_many_list_files(files):
    return [convert_one_list_file(file) for file in files]