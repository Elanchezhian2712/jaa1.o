from collections import defaultdict
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from src import report, totaltime
from . import models, schemas
from fastapi import UploadFile,HTTPException
import pandas as pd
import json
from datetime import date,datetime, time,timedelta
import os
from zipfile import ZipFile
import tracemalloc
import shutil
from sqlalchemy import cast, or_,and_,func,Date
import csv
from io import BytesIO
from sqlalchemy.exc import IntegrityError
import pendulum
from datetime import datetime, timedelta
import time
#-------------------------------------------------------------------------------------------

#Function to convert time string to timedelta
# def time_str_to_timedelta(time_str):
#     (h, m, s) = map(int, time_str.split(':'))
#     return timedelta(hours=h, minutes=m, seconds=s)

from datetime import timedelta

def time_str_to_timedelta(time_str):
    # Check if the string contains "day" and handle accordingly
    if "day" in time_str:
        day_part, time_part = time_str.split(", ")
        days = int(day_part.split()[0])  # Extract the number of days
        (h, m, s) = map(int, time_part.split(':'))  # Extract hours, minutes, seconds
        return timedelta(days=days, hours=h, minutes=m, seconds=s)
    else:
        (h, m, s) = map(int, time_str.split(':'))
        return timedelta(hours=h, minutes=m, seconds=s)


#-------------------------------------------------------------------------------------------

def insert_nature_of_work(db:Session,work_name_str:str):
   db_nature_of_work = models.Nature_Of_Work(work_name = work_name_str)
   db.add(db_nature_of_work)
   try:
        db.commit()
        return "Success"
   except :
       db.rollback()
       return "Failure"

def get_nature_of_work(db:Session):
    return db.query(models.Nature_Of_Work).filter(models.Nature_Of_Work.work_status==1).all()

def delete_nature_of_work(db:Session,work_id:int):
    db_res = db.query(models.Nature_Of_Work).filter(models.Nature_Of_Work.work_id==work_id).first()
    db_res.work_status = 0
    try:
        db.commit()
        return "Success"
    except:
        return "Failure"

def update_nature_of_work(db:Session,work_name:str,work_id:int):
    db_res = db.query(models.Nature_Of_Work).filter(models.Nature_Of_Work.work_id==work_id).first()
    db_res.work_name = work_name
    try:
        db.commit()
        return "Success"
    except:
        return "Failure"
    
#-------------------------------------------------------------------------------------------

def insert_user(db:Session,username:str,role:str,firstname:str,lastname:str,location:str):
   db_insert_user = models.User_table(username = username,role=role,firstname = firstname,lastname = lastname,location=location)
   db.add(db_insert_user)
   
   try:
        db.commit()
        return "Success"
   except :
       db.rollback()
       return "Failure"

# def insert_user(db: Session, username: str, role: str, firstname: str, lastname: str, location: str):
#     db_insert_user = models.User_table(username=username, role=role, firstname=firstname, lastname=lastname, location=location)
#     db.add(db_insert_user)
#     
#     try:
#         db.commit()
#         return "Success"
#     except IntegrityError:
#         db.rollback()
#         return "Failure: Username already exists"
#     except Exception as e:
#         db.rollback()
#         return f"Failure: {str(e)}"
   
def get_user(db:Session):
    return db.query(models.User_table).filter(models.User_table.user_status==1).all()

def delete_user(db:Session,user_id:int):
    db_res = db.query(models.User_table).filter(models.User_table.user_id==user_id).first()
    db_res.user_status = 0
    try:
        db.commit()
        return "Success"
    except:
        return "Failure"
    
def update_user(db:Session,user_id:int,username:str,user_role:str):
    db_res = db.query(models.User_table).filter(models.User_table.user_id==user_id).first()
    db_res.username = username
    db_res.role = user_role
    try:
        db.commit()
        return "Success"
    except:
        return "Failure"

#-------------------------------------------------------------------------------------------

def login_check(db:Session,username:str,password:str):
    db_count = db.query(models.User_table).filter(models.User_table.username==username,models.User_table.password==password,models.User_table.user_status==1).count()
    if db_count > 0:
        return db.query(models.User_table).filter(models.User_table.username==username,models.User_table.password==password,models.User_table.user_status==1).all()
    else:
        return []
    
#-------------------------------------------------------------------------------------------

def tl_insert(db:Session,name_of_entity:str,gst_or_tan:str,gst_tan:str,client_grade:str,Priority:str,Assigned_By:int,estimated_d_o_d:str,estimated_time:str,Assigned_To:int,Scope:int,nature_of_work:int,From:int,Actual_d_o_d:str):
    entity_name = name_of_entity
    entity_name_upper = entity_name.upper()
    # 
    db_insert_tl = models.TL(name_of_entity=entity_name_upper,gst_or_tan=gst_or_tan,gst_tan=gst_tan,client_grade=client_grade,Priority=Priority,Assigned_By=Assigned_By,estimated_d_o_d=estimated_d_o_d,estimated_time=estimated_time,Assigned_To=Assigned_To,Scope=Scope,nature_of_work=nature_of_work,From=From,Actual_d_o_d=Actual_d_o_d)
    db.add(db_insert_tl)
    try:
        db.commit()
        return "Success"
    except :
       db.rollback()
       return "Failure"
    
#-------------------------------------------------------------------------------------------

def tl_insert_bulk(db:Session,file1:UploadFile):
    tracemalloc.start()
    if file1.filename.endswith('.csv'):
        df1 = pd.read_csv(file1.file)
        
    else:
        raise HTTPException(status_code=400, detail="File format not supported. Please upload CSV (.csv) files.")
    
    for index,row1 in df1.iterrows():

        nature_of_work = row1['nature_of_work']
        assigned_by = row1['Assigned_By']
        assigned_to = row1['Assigned_To']
        db_res_count = db.query(models.Nature_Of_Work).filter(models.Nature_Of_Work.work_name==nature_of_work,models.Nature_Of_Work.work_status==1).count()
        
        

        if db_res_count>0:
            db_res = db.query(models.Nature_Of_Work).filter(models.Nature_Of_Work.work_name==nature_of_work,models.Nature_Of_Work.work_status==1).first()
            nature_of_work_id = db_res.work_id
            db_res_count1 = db.query(models.User_table).filter(models.User_table.username==assigned_by,models.User_table.user_status==1).count()
            if db_res_count1>0:
                db_res = db.query(models.User_table).filter(models.User_table.username==assigned_by,models.User_table.user_status==1).first()
                assigned_by_id = db_res.user_id
                db_res_count2 = db.query(models.User_table).filter(models.User_table.username==assigned_to,models.User_table.user_status==1).count()
                if db_res_count2>0:
                    db_res = db.query(models.User_table).filter(models.User_table.username==assigned_to,models.User_table.user_status==1).first()
                    assigned_to_id = db_res.user_id
                    entity = row1['name_of_entity']
                    entity_name_upper = entity.upper()
                    db_insert_tl = models.TL(name_of_entity=entity_name_upper,gst_or_tan=row1['gst_or_tan'],gst_tan=row1['gst_tan'],client_grade=row1['client_grade'],Priority=row1['Priority'],Assigned_By=int(assigned_by_id),estimated_d_o_d=row1['estimated_d_o_d'],estimated_time=row1['estimated_time'],Assigned_To=int(assigned_to_id),Scope=row1['Scope'],nature_of_work=int(nature_of_work_id),From=row1['From'],Actual_d_o_d=row1['Actual_d_o_d'])
                    db.add(db_insert_tl)
                    try:
                        db.commit()
                    except :
                        db.rollback()
                else:
                    return "Failure"
            else:
                return "Failure"
        else:
            return "Failure"
    return "Success"
        
#-------------------------------------------------------------------------------------------

def get_work(db:Session,user_id:int):
    task_list = []
    db_res = db.query(models.TL).filter(models.TL.Assigned_To==user_id,models.TL.status==1,models.TL.work_status != "Re-allocated",models.TL.work_status != "Completed").all()
    
    for row in db_res:
        data = {}
        data['service_id'] = row.Service_ID
        data['name_of_entity'] = row.name_of_entity
        data['gst_or_tan'] = row.gst_or_tan
        data['gst_tan'] = row.gst_tan
        data['client_grade'] = row.client_grade   
        data['Priority'] = row.Priority
        data['Scope'] = row.scope.scope
       
        # Fetch Assigned_By details
        db_user = db.query(models.User_table).filter(models.User_table.user_id==row.Assigned_By).first()
        if db_user:
            data['Assigned_By'] = db_user.username
            data['Assigned_By_Id'] = db_user.user_id
        else:
            data['Assigned_By'] = '-'
            data['Assigned_By_Id'] = None

        data['Assigned_Date'] = row.Assigned_Date.strftime("%d-%m-%Y %H:%M:%S")
        data['estimated_d_o_d'] = row.estimated_d_o_d
        data['estimated_time'] = row.estimated_time

        # Fetch Assigned_To details
        db_user = db.query(models.User_table).filter(models.User_table.user_id==row.Assigned_To).first()
        if db_user:
            data['Assigned_To'] = db_user.username
            data['Assigned_To_Id'] = db_user.user_id
        else:
            data['Assigned_To'] = '-'
            data['Assigned_To_Id'] = None

        data['nature_of_work'] = row._nature_of_work.work_name
        data['nature_of_work_id'] = row.nature_of_work
        data['From'] = row.sub_scope.sub_scope
        data['Actual_d_o_d'] = row.Actual_d_o_d
        data['created_on'] = row.created_on.strftime("%d-%m-%Y ")
        data['type_of_activity'] = row.type_of_activity
        data['work_status'] = row.work_status
        data['no_of_items'] = row.no_of_items
        data['remarks'] = row.remarks
        data['working_time'] = row.working_time
        data['completed_time'] = row.completed_time
        data['reallocated_time'] = row.reallocated_time
        task_list.append(data)
    json_data = json.dumps(task_list)
    return json.loads(json_data)

def commonfunction_get_work_tl(db, db_res):
    task_list = []
    for row in db_res:
        data = {}
        data['service_id'] = row.Service_ID
        data['name_of_entity'] = row.name_of_entity
        data['gst_or_tan'] = row.gst_or_tan
        data['gst_tan'] = row.gst_tan
        data['client_grade'] = row.client_grade
        data['Priority'] = row.Priority
        data['Scope'] = row.scope.scope    
        # data['created_on'] = row.created_on
        # 
       
        # data['created_on'] = row.created_on.date()
       
        # Fetch Assigned_By details
        db_user = db.query(models.User_table).filter(models.User_table.user_id==row.Assigned_By).first()
        if db_user:
            data['Assigned_By'] = db_user.firstname + ' ' + db_user.lastname
            data['Assigned_By_Id'] = db_user.user_id
        else:
            data['Assigned_By'] = '-'
            data['Assigned_By_Id'] = None

        data['Assigned_Date'] = row.Assigned_Date.strftime("%d-%m-%Y %H:%M:%S")
        data['estimated_d_o_d'] = row.estimated_d_o_d
        data['estimated_time'] = row.estimated_time

        # Fetch Assigned_To details
        db_user = db.query(models.User_table).filter(models.User_table.user_id==row.Assigned_To).first()
        if db_user:
            data['Assigned_To'] =  db_user.firstname + ' ' + db_user.lastname
            data['Assigned_To_Id'] = db_user.user_id
        else:
            data['Assigned_To'] = '-'
            data['Assigned_To_Id'] = None

        data['nature_of_work'] = row._nature_of_work.work_name
        data['nature_of_work_id'] = row.nature_of_work
        data['From'] = row.sub_scope.sub_scope
        data['Actual_d_o_d'] = row.Actual_d_o_d
        data['created_on'] = row.created_on.strftime("%d-%m-%Y ")
        data['type_of_activity'] = row.type_of_activity
        data['work_status'] = row.work_status
        data['no_of_items'] = row.no_of_items
        data['remarks'] = row.remarks
        data['working_time'] = row.working_time
        data['completed_time'] = row.completed_time
        data['reallocated_time'] = row.reallocated_time

        task_list.append(data)

    return json.dumps(task_list)

# def get_work_tl(db:Session,user_id:int):
#     user_roles = db.query(models.User_table).filter(models.User_table.user_id==user_id,models.User_table.user_status==1).all()
#     role = [role.role for role in user_roles]
#     if 'TL' in role:
#         db_res = db.query(models.TL).filter(models.TL.Assigned_By==user_id,models.TL.status==1).all()
#         json_data = commonfunction_get_work_tl(db, db_res)
#         return json.loads(json_data)
#     else:
#         db_res = db.query(models.TL).filter(models.TL.status==1).all()
#         json_data = commonfunction_get_work_tl(db, db_res)
#         return json.loads(json_data)



def get_work_tl(picked_date, to_date, db: Session, user_id: int):
    start_date = datetime.strptime(picked_date, "%Y-%m-%d")
    end_date = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    user_roles = db.query(models.User_table).filter(models.User_table.user_id == user_id, models.User_table.user_status == 1).all()
    role = [role.role for role in user_roles]

    if 'TL' in role:
        db_res = db.query(models.TL).filter(
            and_(
                models.TL.Assigned_By == user_id,
                models.TL.status == 1,
                models.TL.created_on >= start_date,
                models.TL.created_on <= end_date
            )
        ).all()
        json_data = commonfunction_get_work_tl(db, db_res)
        return json.loads(json_data)
    else:
        db_res = db.query(models.TL).filter(
            and_(
                models.TL.status == 1,
                models.TL.created_on >= start_date,
                models.TL.created_on <= end_date
            )
        ).all()
        json_data = commonfunction_get_work_tl(db, db_res)
        return json.loads(json_data)


def commonfunction_get_work_tl(db, db_res):
    task_list = []

    for item in db_res:
        task = {
            'Service_ID': item.Service_ID,
            'name_of_entity': item.name_of_entity,
            'gst_or_tan': item.gst_or_tan,
            'gst_tan': item.gst_tan,
            'client_grade': item.client_grade,
            'Priority': item.Priority,
            'Assigned_By': item.Assigned_By,
            'Assigned_Date': item.Assigned_Date.isoformat() if item.Assigned_Date else None,
            'estimated_d_o_d': item.estimated_d_o_d,
            'estimated_time': item.estimated_time,
            'Assigned_To': item.Assigned_To,
            'Scope': item.scope.scope,
            'nature_of_work': item._nature_of_work.work_name,
            'From': item.sub_scope.sub_scope,
            'Actual_d_o_d': item.Actual_d_o_d,
            'remarks': item.remarks,
            'status': item.status,
            'created_on': item.created_on.isoformat() if item.created_on else None,
            'type_of_activity': item.type_of_activity,
            'work_status': item.work_status,
            'no_of_items': item.no_of_items,
            'working_time': item.working_time,
            'completed_time': item.completed_time.isoformat() if item.completed_time else None,
            'reallocated_time': item.reallocated_time,
        }
        task_list.append(task)

    return json.dumps(task_list)

#-------------------------------------------------------------------------------------------

# def start(db:Session,service_id:int,type_of_activity:str,no_of_items:str):
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.type_of_activity = type_of_activity
#     db_res.no_of_items = no_of_items
#     db_res.work_status = "Work in Progress"
#     if db_res.working_time == '':
#         current_datetime = datetime.now()
#         current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
#         db_res.working_time = current_datetime_str
#     db.commit()
#     return "Success"



#-------------------------------------------------------------------------------------------

def reallocated(db:Session,service_id:int,remarks:str,user_id:int):
    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    db_res.work_status = "Re-allocated"
    db_res.remarks = remarks
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    db_res.reallocated_time = current_datetime_str
    db.commit()


    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    
    if db_res:
        # Update the record's fields
        # db_res.work_status = "Re-allocated"
        # db_res.Assigned_To = None
        db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id,models.TL.status==1).all()
        
        for row in db_res:
            
            # data['service_id'] = row.Service_ID
            name_of_entity = row.name_of_entity
            gst_or_tan = row.gst_or_tan
            gst_tan = row.gst_tan
            client_grade = row.client_grade   
            Priority = row.Priority
            Scope = row.Scope
            nature_of_work = row._nature_of_work.work_name
            nature_of_work_id = row.nature_of_work
            From = row.From
            Actual_d_o_d = row.Actual_d_o_d
            created_on = row.created_on.strftime("%d-%m-%Y ")
            type_of_activity = row.type_of_activity
            work_status = "Not Picked"
            no_of_items = row.no_of_items
            remarks_new = row.remarks
            working_time = row.working_time
            completed_time = row.completed_time
            reallocated_time = row.reallocated_time
            Assigned_By = row.Assigned_By
            estimated_d_o_d = row.estimated_d_o_d
            estimated_time = row.estimated_time
            # 
            db_insert = models.TL(name_of_entity=name_of_entity,gst_or_tan=gst_or_tan,gst_tan=gst_tan,client_grade=client_grade,Priority=Priority,Assigned_By=Assigned_By,estimated_d_o_d=estimated_d_o_d,work_status = work_status ,estimated_time=estimated_time,Assigned_To=user_id,Scope=Scope,nature_of_work=nature_of_work_id,From=From,Actual_d_o_d=Actual_d_o_d)

            db.add(db_insert)
            db.commit()
            current_datetime = datetime.now()
            current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            db_insert = models.REALLOCATED(Service_ID = service_id,user_id=user_id,re_time_start = current_datetime_str,remarks=remarks)
            db.add(db_insert)
            db.commit()

        return "Success"


def reallocated_end(db:Session,service_id:int,user_id:int):
    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    db_res.work_status = "Not Picked"
    db_res.Assigned_To = user_id
    
    db.commit()
    # current_datetime = datetime.now()
    # current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    # db_res2 = db.query(models.REALLOCATED).filter(
    #     models.REALLOCATED.Service_ID == service_id,
    #     models.REALLOCATED.user_id == user_id
    # ).order_by(
    #     models.REALLOCATED.id.desc()
    # ).first()
    # db_res2.re_time_end = current_datetime_str
    # db.commit()
    return "Success"

#-------------------------------------------------------------------------------------------

def get_count(db:Session,user_id:int):
    count_list = []
    data = {}
    db_completed_count = db.query(models.TL).filter(models.TL.Assigned_To==user_id,models.TL.work_status=="Completed",models.TL.status==1).count()
    data['completed_count'] = db_completed_count

    db_reallocated_count = db.query(models.TL).filter(models.TL.Assigned_To==user_id,models.TL.work_status=="Reallocated",models.TL.status==1).count()
    data['reallocated_count'] = db_reallocated_count

    db_not_picked_count = db.query(models.TL).filter(models.TL.Assigned_To==user_id,models.TL.work_status=="Not Picked",models.TL.status==1).count()
    data['not_picked_count'] = db_not_picked_count

    db_wip_count = db.query(models.TL).filter(models.TL.Assigned_To==user_id,models.TL.work_status=="Work in Progress",models.TL.status==1).count()
    data['wip_count'] = db_wip_count

    db_chargable_count = db.query(models.TL).filter(models.TL.Assigned_To==user_id,models.TL.type_of_activity=="CHARGABLE",models.TL.status==1).count()
    data['chargable_count'] = db_chargable_count

    db_non_chargable_count = db.query(models.TL).filter(models.TL.Assigned_To==user_id,models.TL.type_of_activity=="Non-Charchable",models.TL.status==1).count()
    data['non_chargable_count'] = db_non_chargable_count

    db_hold_count = db.query(models.TL).filter(models.TL.Assigned_To==user_id,models.TL.work_status=="Hold",models.TL.status==1).count()
    data['hold'] = db_hold_count

    db_training = db.query(models.TL).filter(models.TL.Assigned_To==user_id,models.TL.work_status=="End Of Day",models.TL.status==1).count()
    data['Training'] = db_training

    count_list.append(data)
    return count_list

def get_count_tl(db:Session,user_id:int):
    count_list = []
    data = {}
    get_role = db.query(models.User_table).filter(models.User_table.user_id==user_id).all()
    user_role = ''
    if get_role:
        user_role = get_role[0].role
    else:
        None
    if (user_role == "TL"):
        db_completed_count = db.query(models.TL).filter(models.TL.Assigned_By==user_id,models.TL.work_status=="Completed",models.TL.status==1).count()
        data['completed_count'] = db_completed_count

        db_reallocated_count = db.query(models.TL).filter(models.TL.Assigned_By==user_id,models.TL.work_status=="Reallocated",models.TL.status==1).count()
        data['reallocated_count'] = db_reallocated_count

        db_not_picked_count = db.query(models.TL).filter(models.TL.Assigned_By==user_id,models.TL.work_status=="Not Picked",models.TL.status==1).count()
        data['not_picked_count'] = db_not_picked_count

        db_wip_count = db.query(models.TL).filter(models.TL.Assigned_By==user_id,models.TL.work_status=="Work in Progress",models.TL.status==1).count()
        data['wip_count'] = db_wip_count

        db_chargable_count = db.query(models.TL).filter(models.TL.Assigned_By==user_id,models.TL.type_of_activity=="CHARGABLE",models.TL.status==1).count()
        data['chargable_count'] = db_chargable_count

        db_non_chargable_count = db.query(models.TL).filter(models.TL.Assigned_By==user_id,models.TL.type_of_activity=="Non-Charchable",models.TL.status==1).count()
        data['non_chargable_count'] = db_non_chargable_count

        db_hold_count = db.query(models.TL).filter(models.TL.Assigned_By==user_id,models.TL.work_status=="Hold",models.TL.status==1).count()
        data['hold'] = db_hold_count

        db_training = db.query(models.TL).filter(models.TL.Assigned_By==user_id,models.TL.work_status=="End Of Day",models.TL.status==1).count()
        data['Training'] = db_training

        count_list.append(data)
        return count_list
    elif (user_role == "Admin"):
        db_completed_count = db.query(models.TL).filter(models.TL.work_status=="Completed",models.TL.status==1).count()
        data['completed_count'] = db_completed_count

        db_reallocated_count = db.query(models.TL).filter(models.TL.work_status=="Reallocated",models.TL.status==1).count()
        data['reallocated_count'] = db_reallocated_count

        db_not_picked_count = db.query(models.TL).filter(models.TL.work_status=="Not Picked",models.TL.status==1).count()
        data['not_picked_count'] = db_not_picked_count

        db_wip_count = db.query(models.TL).filter(models.TL.work_status=="Work in Progress",models.TL.status==1).count()
        data['wip_count'] = db_wip_count

        db_chargable_count = db.query(models.TL).filter(models.TL.type_of_activity=="CHARGABLE",models.TL.status==1).count()
        data['chargable_count'] = db_chargable_count

        db_non_chargable_count = db.query(models.TL).filter(models.TL.type_of_activity=="Non-Charchable",models.TL.status==1).count()
        data['non_chargable_count'] = db_non_chargable_count

        db_hold_count = db.query(models.TL).filter(models.TL.work_status=="Hold",models.TL.status==1).count()
        data['hold'] = db_hold_count

        db_training = db.query(models.TL).filter(models.TL.work_status=="End Of Day",models.TL.status==1).count()
        data['Training'] = db_training

        count_list.append(data)
        return count_list

#-------------------------------------------------------------------------------------------

def get_break_time_info(db:Session):
    db_res = db.query(models.TL).all()
    user_list = []
    for row in db_res:
        data = {}
        time_format = "%Y-%m-%d %H:%M:%S"
        time = datetime.strptime(row.break_time_str, time_format) 
        if time.hour > 1:
            data['user_name'] = row._user_table1.username
            data['user_id']=row.Assigned_To
            data['break_time'] = row.break_time_str
            user_list.append(data)
            return user_list
        elif time.hour ==1:
            if time.minute>0:
                data['user_name'] = row._user_table1.username
                data['user_id']=row.Assigned_To
                data['break_time'] = row.break_time_str
                user_list.append(data)
                return user_list
            else:
                return []         
        else:
            return user_list
#-------------------------------------------------------------------------------------------

async def get_reports(db:Session,fields:str):
    column_set = fields.split(",")
    db_res = db.query(models.TL).all()
    df = pd.DataFrame([r.__dict__ for r in db_res])
    new_df = df[column_set]
    return new_df

#-------------------------------------------------------------------------------------------

# def break_start(db:Session,service_id:int,remarks:str,user_id:int):
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Break"
#     db.commit()
#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
#     db_insert = models.BREAK(Service_ID = service_id,user_id=user_id,break_time_start = current_datetime_str,remarks=remarks)
#     db.add(db_insert)
#     db.commit()
#     return "Success"

# def break_end(db:Session,service_id:int,user_id:int):
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Work in Progress"
#     db.commit()
#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
#     db_res2 = db.query(models.BREAK).filter(
#         models.BREAK.Service_ID == service_id,
#         models.BREAK.user_id == user_id
#     ).order_by(
#         models.BREAK.id.desc()
#     ).first()
#     db_res2.break_time_end = current_datetime_str
#     db.commit()
#     return "Success"


# def call_start(db:Session,service_id:int,remarks:str,user_id:int):
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Clarification Call"
#     db.commit()
#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
#     db_insert = models.CALL(Service_ID = service_id,user_id=user_id,call_time_start = current_datetime_str,remarks=remarks)
#     db.add(db_insert)
#     db.commit()
#     return "Success"

# def call_end(db:Session,service_id:int,user_id:int):
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Work in Progress"
#     db.commit()
#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
#     db_res2 = db.query(models.CALL).filter(
#         models.CALL.Service_ID == service_id,
#         models.CALL.user_id == user_id
#     ).order_by(
#         models.CALL.id.desc()
#     ).first()
#     db_res2.call_time_end = current_datetime_str
#     db.commit()
#     return "Success"


# def end_of_day_start(db:Session,service_id:int,remarks:str,user_id:int):
    
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "End Of Day"
#     db.commit()

#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
#     db_insert = models.END_OF_DAY(Service_ID = service_id,user_id=user_id,end_time_start = current_datetime_str,remarks=remarks)
#     db.add(db_insert)
#     db.commit()
    
#     return "Success"

# def end_of_day_end(db:Session,service_id:int,user_id:int):
    
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Work in Progress"
#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
#     db_res.reallocated_time = current_datetime_str
#     db.commit()
    
#     db_res2 = db.query(models.END_OF_DAY).filter(
#         models.END_OF_DAY.Service_ID == service_id,
#         models.END_OF_DAY.user_id == user_id
#     ).order_by(
#         models.END_OF_DAY.id.desc()
#     ).first()
#     db_res2.end_time_end = current_datetime_str
#     db.commit()
#     return "Success"


# def hold_start(db:Session,service_id:int,remarks:str,user_id:int):
    
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Hold"
#     db.commit()

#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
#     db_insert = models.HOLD(Service_ID = service_id,user_id=user_id,hold_time_start=current_datetime_str,remarks=remarks)
#     db.add(db_insert)
#     db.commit()
    
#     return "Success"

# def hold_end(db:Session,service_id:int,user_id:int):
    
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Work in Progress"
#     db.commit()
    
#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
#     db_res2 = db.query(models.HOLD).filter(
#         models.HOLD.Service_ID == service_id,
#         models.HOLD.user_id == user_id
#     ).order_by(
#         models.HOLD.id.desc()
#     ).first()
#     db_res2.hold_time_end = current_datetime_str
#     db.commit()
#     return "Success"


# def meeting_start(db:Session,service_id:int,remarks:str,user_id:int):
    
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Meeting"
#     db.commit()

#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
#     db_insert = models.MEETING(Service_ID = service_id,user_id=user_id,meeting_time_start=current_datetime_str,remarks=remarks)
#     db.add(db_insert)
#     db.commit()
    
#     return "Success"

# def meeting_end(db:Session,service_id:int,user_id:int):
    
#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Work in Progress"
#     db.commit()
    
#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
#     db_res2 = db.query(models.MEETING).filter(
#         models.MEETING.Service_ID == service_id,
#         models.MEETING.user_id == user_id
#     ).order_by(
#         models.MEETING.id.desc()
#     ).first()
#     db_res2.meeting_time_end = current_datetime_str
#     db.commit()
#     return "Success"

# def Completed(db:Session,service_id:int,remarks:str,count:str):
    
#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Completed"
#     db_res.no_of_items = count
#     db_res.completed_time = current_datetime_str
#     db_res.remarks = remarks
#     db.commit()
    
#     return "Success"


#----------------------------------------------------------------------------
def User_Wise_Day_Wise_Part_1(db: Session, picked_date: str, to_date: str):
    date_time_formate_string = '%Y-%m-%d %H:%M:%S'
    list_data = []

    date_time1 = datetime.now()
    todatedd = datetime.strptime(to_date, "%Y-%m-%d")

    db_res = db.query(models.TL).filter(models.TL.status == 1,
        or_(
            models.TL.working_time.between(picked_date, to_date),
            models.TL.reallocated_time.between(picked_date, to_date),
            
        )
    ).all()

    for row in db_res:
        data = {}
        data["date"] = datetime.strptime(row.working_time, date_time_formate_string).date()
        data["user"] = row._user_table1.username
        data["Service_ID"] = row.Service_ID
        data["scope"] = row.Scope
        data["subscopes"] = row.From
        data["entity"] = row.name_of_entity
        data["status"] = row.work_status
        data["type_of_activity"] = row.type_of_activity
        data["Nature_of_Work"] = row._nature_of_work.work_name
        data["gst_tan"] = row.gst_tan
        data["estimated_d_o_d"] =  row.estimated_d_o_d
        data["estimated_time"] =  row.estimated_time
        # username = db.query(User_table).filter(User.user_id == row.Assigned_To).first()
        data["member_name"] = row._user_table1.firstname +' '+ row._user_table1.lastname
        
        date_time2 = datetime.strptime(row.working_time, date_time_formate_string)
        time_diff = date_time1 - date_time2
        work_hour_hours_diff = time_diff


        # -----end of the day
        # db_res2 = db.query(models.END_OF_DAY).filter(
        #     models.END_OF_DAY.Service_ID == row.Service_ID,
        #     cast(models.END_OF_DAY.end_time_start, Date) >= todatedd
        # ).all()

        
        
        
        # end_hour_diff = timedelta(hours=0)
        # date_time_format_string = '%Y-%m-%d %H:%M:%S'
        # for row2 in db_res2:
        #     if row2.end_time_end and row2.end_time_start:

        #         
                

        #         datetime_obj1 = datetime.strptime(row2.end_time_start, "%Y-%m-%d %H:%M:%S")
        #         datetime_obj2 = datetime.strptime(row2.end_time_end, "%Y-%m-%d %H:%M:%S")

        #         # Calculate the difference
        #         time_difference = datetime_obj2 - datetime_obj1

        #         
        #         current_datetime = datetime.now()
        #         current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")


        #         date_time11 = datetime.strptime(row2.end_time_end, date_time_format_string)
        #         date_time22 = datetime.strptime(row2.end_time_start, date_time_format_string)
        #         time_diff = date_time11 - date_time22
        #         end_hour_diff += time_diff
        #         
        #     else:
        #         if not (row.work_status == "Completed" or (row.work_status == "in_progress" or row.work_status == "End Of Day")):
        #             
                    

        #             datetime_obj1 = datetime.strptime(row2.end_time_start, "%Y-%m-%d %H:%M:%S")
        #             datetime_obj2 = datetime.strptime(row2.end_time_end, "%Y-%m-%d %H:%M:%S")

        #             # Calculate the difference
        #             time_difference = datetime_obj2 - datetime_obj1

        #             
        #             current_datetime = datetime.now()
        #             current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        #             

        #             

        #             datetime_obj1 = datetime.strptime(row2.end_time_start, "%Y-%m-%d %H:%M:%S")
        #             minus = datetime.now()
        #             minus_datetime_str = minus.strftime("%Y-%m-%d %H:%M:%S")

        #             time_difference =  datetime_obj1 - minus_datetime_str


        #             end_hour_diff += time_difference


       
        a = timedelta(hours=0)
        b = timedelta(hours=0)
        if row.work_status == "Reallocated":
            db_res2 = db.query(models.REALLOCATED).filter(
                models.REALLOCATED.Service_ID == row.Service_ID,
                models.REALLOCATED.re_time_start >= picked_date,
                models.REALLOCATED.re_time_end <= to_date
            ).all()

            re_hour_diff = timedelta(hours=0)

            for row2 in db_res2:
                if row2.re_time_start and row2.re_time_end:
                    date_time2r = datetime.strptime(row2.re_time_start, date_time_formate_string)
                    re_time_diff = date_time1 - date_time2r
                    re_hour_diff += re_time_diff
                    data["reallocated"] = re_hour_diff
            a = work_hour_hours_diff
        if row.work_status == "Completed":
            a = work_hour_hours_diff
        else:
            b = work_hour_hours_diff

        # ----- Hold Hour ------
        db_res2 = db.query(models.HOLD).filter(
            models.HOLD.Service_ID == row.Service_ID,
            models.HOLD.hold_time_start >= picked_date,
            models.HOLD.hold_time_end <= to_date
        ).all()

        hold_hour_diff = timedelta(hours=0)

        for row2 in db_res2:
            if row2.hold_time_end and row2.hold_time_start:
                date_time11 = datetime.strptime(row2.hold_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.hold_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                hold_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.hold_time_start, date_time_formate_string)
                    hold_hour_diff +=  time1

        data["hold"] = hold_hour_diff

        # ----- Meeting Hour ------
        db_res2 = db.query(models.MEETING).filter(
            models.MEETING.Service_ID == row.Service_ID,
            models.MEETING.meeting_time_start >= picked_date,
            models.MEETING.meeting_time_end <= to_date
        ).all()

        meet_hour_diff = timedelta(hours=0)

        for row2 in db_res2:
            if row2.meeting_time_end and row2.meeting_time_start:
                date_time11 = datetime.strptime(row2.meeting_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                meet_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                    meet_hour_diff +=   time1



        data["meeting"] = meet_hour_diff

        # ----- Break Hour ------
        db_res2 = db.query(models.BREAK).filter(
            models.BREAK.Service_ID == row.Service_ID,
            models.BREAK.break_time_start >= picked_date,
            models.BREAK.break_time_end <= to_date
        ).all()

        break_hour_diff = timedelta(hours=0)

        for row2 in db_res2:
            if row2.break_time_end and row2.break_time_start:
                date_time11 = datetime.strptime(row2.break_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.break_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                break_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.break_time_start, date_time_formate_string)
                 
                    break_hour_diff += time1

        data["break"] = break_hour_diff

        # ----- Call Hour ------
        db_res2 = db.query(models.CALL).filter(
            models.CALL.Service_ID == row.Service_ID,
            models.CALL.call_time_start >= picked_date,
            models.CALL.call_time_end <= to_date
        ).all()

        call_hour_diff = timedelta(hours=0)

        for row2 in db_res2:
            if row2.call_time_end and row2.call_time_start:
                date_time11 = datetime.strptime(row2.call_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.call_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                call_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.call_time_start, date_time_formate_string)
                   
                    call_hour_diff += time1

        data["call"] = call_hour_diff


        # -----end of the day
        temp = ''
        
        db_res2 = db.query(models.END_OF_DAY).filter(
            models.END_OF_DAY.Service_ID == row.Service_ID,
            models.END_OF_DAY.end_time_start>=picked_date,
            models.END_OF_DAY.end_time_start<=to_date
        ).all()

        count = db.query(models.END_OF_DAY).filter(
            models.END_OF_DAY.Service_ID == row.Service_ID,
            models.END_OF_DAY.end_time_start>=picked_date
        ).count()

        time_diff = timedelta(hours=0)
        if count >= 1 :
            for rom in db_res2:
                if rom.end_time_end == "":
                    temp = rom.end_time_start
                    parsed_date = datetime.strptime(str(temp), '%Y-%m-%d %H:%M:%S')
                    date_time22 = date_time1
                    time_diff += date_time22 - parsed_date
                else:
                    temp = rom.end_time_start
                    parsed_date = datetime.strptime(str(temp), '%Y-%m-%d %H:%M:%S')
                    date_time11 = datetime.strptime(rom.end_time_end, date_time_formate_string)
                    time_diff += date_time11 - parsed_date
        data["end_of_day"] = time_diff
        
        if row.work_status == "Completed":
            e_o_d = data["end_of_day"]
            data["in_progress"] = timedelta(hours=0)
            data["completed"] = (datetime.strptime(row.completed_time, date_time_formate_string) - datetime.strptime(row.working_time, date_time_formate_string)) - (call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + e_o_d)
            # data["completed"] = (a + b) - (call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + e_o_d)
        else:
            e_o_d = data["end_of_day"]
            data["completed"] = timedelta(hours=0)
            if row.work_status != "End Of Day":
                data["in_progress"] = (a + b) - (call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + e_o_d)
            else:
                data["in_progress"] = (a + b) - (call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + e_o_d)
            

        # data["total_time_taken"] = call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + data["completed"] + data["in_progress"]

        data["total_time_taken"] =  (data["in_progress"] + data["completed"] )
        # data["second_report_data"] = call_hour_diff + hold_hour_diff + data["completed"] + data["in_progress"]
        data["second_report_data"] =  data["completed"] + data["in_progress"]

        
#--------------------------------------------------------------------------------------------------------------------------------------
        # ----- HOLD Hour ------
        holdchargable = db.query(models.HOLD).join(
            models.TL, models.HOLD.Service_ID == models.TL.Service_ID
        ).filter(
            models.HOLD.Service_ID == row.Service_ID,
            models.HOLD.hold_time_start >= picked_date,
            models.HOLD.hold_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        holdchargable_hour_diff = timedelta(hours=0)

        for row2 in holdchargable:
            if row2.hold_time_end and row2.hold_time_start:
                date_time11 = datetime.strptime(row2.hold_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.hold_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                holdchargable_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.hold_time_start, date_time_formate_string)
                   
                    holdchargable_hour_diff += time1


        
        
        # ----- Meeting Hour ------
        Meetingchargable = db.query(models.MEETING).join(
            models.TL, models.MEETING.Service_ID == models.TL.Service_ID
        ).filter(
            models.MEETING.Service_ID == row.Service_ID,
            models.MEETING.meeting_time_start >= picked_date,
            models.MEETING.meeting_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        meetch_hour_diff = timedelta(hours=0)

        for row2 in Meetingchargable:
            if row2.meeting_time_end and row2.meeting_time_start:
                date_time11 = datetime.strptime(row2.meeting_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                meetch_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                    
                    meetch_hour_diff += time1


        
        
        # ----- Break Hour ------
        Breakchargable = db.query(models.BREAK).join(
            models.TL, models.BREAK.Service_ID == models.TL.Service_ID
        ).filter(
            models.BREAK.Service_ID == row.Service_ID,
            models.BREAK.break_time_start >= picked_date,
            models.BREAK.break_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        breakch_hour_diff = timedelta(hours=0)

        for row2 in Breakchargable:
            if row2.break_time_end and row2.break_time_start:
                date_time11 = datetime.strptime(row2.break_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.break_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                breakch_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.break_time_start, date_time_formate_string)
                  
                    breakch_hour_diff += time1


        
        
        # ----- Call Hour ------
        Callchargable = db.query(models.CALL).join(
            models.TL, models.CALL.Service_ID == models.TL.Service_ID
        ).filter(
            models.CALL.Service_ID == row.Service_ID,
            models.CALL.call_time_start >= picked_date,
            models.CALL.call_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        callch_hour_diff = timedelta(hours=0)

        for row2 in Callchargable:
            if row2.call_time_end and row2.call_time_start:
                date_time11 = datetime.strptime(row2.call_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.call_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                callch_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.call_time_start, date_time_formate_string)
                 
                    callch_hour_diff += time1

        # -----end of the day
        endch = db.query(models.END_OF_DAY).join(
            models.TL, models.END_OF_DAY.Service_ID == models.TL.Service_ID
        ).filter(
            models.END_OF_DAY.Service_ID == row.Service_ID,
            models.END_OF_DAY.end_time_start >= picked_date,
            models.END_OF_DAY.end_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        endch_hour_diff = timedelta(hours=0)

        for row2 in endch:
            if row2.end_time_end and row2.end_time_start:
                date_time11 = datetime.strptime(row2.end_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.end_time_start, date_time_formate_string)
                time_diff = date_time22 - date_time11
                endch_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.end_time_start, date_time_formate_string)
                   
                    endch_hour_diff += time1

        data["endch_hour_diff"] = endch_hour_diff
        if row.type_of_activity == "CHARGABLE":
            data["chargable_time"] = data["in_progress"] + data["completed"]
        else:
            data["chargable_time"] = timedelta(hours=0)

        parsed_time = datetime.strptime(data["estimated_time"], '%H:%M')
        time_delta = timedelta(hours=parsed_time.hour, minutes=parsed_time.minute)

        data["difference_a_b"] = time_delta - data["chargable_time"]
#--------------------------------------------------------------------------------------------------------------------------------------	



#--------------------------------------------------------------------------------------------------------------------------------------
        # ----- HOLD Hour ------
        holdchargable = db.query(models.HOLD).join(
            models.TL, models.HOLD.Service_ID == models.TL.Service_ID
        ).filter(
            models.HOLD.Service_ID == row.Service_ID,
            models.HOLD.hold_time_start >= picked_date,
            models.HOLD.hold_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        holdchargable_hour_diff = timedelta(hours=0)

        for row2 in holdchargable:
            if row2.hold_time_end and row2.hold_time_start:
                date_time11 = datetime.strptime(row2.hold_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.hold_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                holdchargable_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.hold_time_start, date_time_formate_string)
                   
                    holdchargable_hour_diff += time1

        
        
        # ----- Meeting Hour ------
        Meetingchargable = db.query(models.MEETING).join(
            models.TL, models.MEETING.Service_ID == models.TL.Service_ID
        ).filter(
            models.MEETING.Service_ID == row.Service_ID,
            models.MEETING.meeting_time_start >= picked_date,
            models.MEETING.meeting_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        meetch_hour_diff = timedelta(hours=0)

        for row2 in Meetingchargable:
            if row2.meeting_time_end and row2.meeting_time_start:
                date_time11 = datetime.strptime(row2.meeting_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                meetch_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                   
                    meetch_hour_diff += time1

        
        
        # ----- Break Hour ------
        Breakchargable = db.query(models.BREAK).join(
            models.TL, models.BREAK.Service_ID == models.TL.Service_ID
        ).filter(
            models.BREAK.Service_ID == row.Service_ID,
            models.BREAK.break_time_start >= picked_date,
            models.BREAK.break_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        breakch_hour_diff = timedelta(hours=0)

        for row2 in Breakchargable:
            if row2.break_time_end and row2.break_time_start:
                date_time11 = datetime.strptime(row2.break_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.break_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                breakch_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.break_time_start, date_time_formate_string)
                    
                    breakch_hour_diff += time1


        
        
        # ----- Call Hour ------
        Callchargable = db.query(models.CALL).join(
            models.TL, models.CALL.Service_ID == models.TL.Service_ID
        ).filter(
            models.CALL.Service_ID == row.Service_ID,
            models.CALL.call_time_start >= picked_date,
            models.CALL.call_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        callch_hour_diff = timedelta(hours=0)

        for row2 in Callchargable:
            if row2.call_time_end and row2.call_time_start:
                date_time11 = datetime.strptime(row2.call_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.call_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                callch_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.call_time_start, date_time_formate_string)
                  
                    callch_hour_diff += time1

        # -----end of the day
        endch = db.query(models.END_OF_DAY).join(
            models.TL, models.END_OF_DAY.Service_ID == models.TL.Service_ID
        ).filter(
            models.END_OF_DAY.Service_ID == row.Service_ID,
            models.END_OF_DAY.end_time_start >= picked_date,
            models.END_OF_DAY.end_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        endch_hour_diff = timedelta(hours=0)

        for row2 in endch:
            if row2.end_time_end and row2.end_time_start:
                date_time11 = datetime.strptime(row2.end_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.end_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                endch_hour_diff += time_diff
            else :
                if not(row.work_status == "Completed" or row.work_status == "in_progress"):
                    time1 =  datetime.now() - datetime.strptime(row2.end_time_start, date_time_formate_string)
                    endch_hour_diff += time1
	    

        data["endch_hour_diff"] = endch_hour_diff
        if row.type_of_activity == "Non-Charchable":
            data["Non_Charchable_time"] = endch_hour_diff 
        else:
            data["Non_Charchable_time"] = timedelta(hours=0)
        data["chargable_and_non_chargable"] = data["Non_Charchable_time"] + data["chargable_time"]
#--------------------------------------------------------------------------------------------------------------------------------------	



        str_temp = ""
        str_temper = ""

        if row.work_status == "Work in Progress":

            data["third_report_data"] = ""

        elif row.work_status == "Hold":

            db_res3 = db.query(models.HOLD).filter(
                models.HOLD.Service_ID == row.Service_ID,
            ).all()
            for hold_obj in db_res3:
                data["third_report_data"] = hold_obj.remarks
                str_temper = hold_obj.remarks

        elif row.work_status == "Meeting":

            db_res3 = db.query(models.MEETING).filter(
                models.MEETING.Service_ID == row.Service_ID,
            ).all()
            for meet_obj in db_res3:
                data["third_report_data"] = meet_obj.remarks


        elif row.work_status == "Break":
            db_res3 = db.query(models.BREAK).filter(
                models.BREAK.Service_ID == row.Service_ID,
            ).all()
            for break_obj in db_res3:
                
                data["third_report_data"] = break_obj.remarks
                
        elif row.work_status == "Clarification Call":
            db_res3 = db.query(models.CALL).filter(
                models.CALL.Service_ID == row.Service_ID,
            ).all()
            for call_obj in db_res3:
                
                data["third_report_data"] = call_obj.remarks

        elif row.work_status == "Completed":
            data["third_report_data"] = row.remarks

        if row.work_status == "Completed":
            try:
                db_res3 = db.query(models.HOLD).filter(
                    models.HOLD.Service_ID == row.Service_ID,
                ).all()
                for hold_obj in db_res3:
                    str_temp = str_temp + hold_obj.remarks + ","
            except:
                str_temp = ""
            try:
                db_res3 = db.query(models.MEETING).filter(
                    models.MEETING.Service_ID == row.Service_ID,
                ).all()
                for meet_obj in db_res3:

                    str_temp = str_temp + meet_obj.remarks + ","

            except:
                str_temp = ""
            try:
                db_res3 = db.query(models.BREAK).filter(
                    models.BREAK.Service_ID == row.Service_ID,
                ).all()
                for break_obj in db_res3:
                    str_temp = str_temp + break_obj.remarks + ","
            except:
                str_temp = ""
            try:
                db_res3 = db.query(models.CALL).filter(
                    models.CALL.Service_ID == row.Service_ID,
                ).all()
                for call_obj in db_res3:
                    str_temp = str_temp + call_obj.remarks + ","
                str_temp = str_temp + row.remarks + ","
            except:
                str_temp = ""

        data["fourth_report"] = row.no_of_items
        data["fourth_report2"] = str_temp
        data["fifth_report"] = str_temper        
        list_data.append(data)
    def convert_values(d):
        return dict(map(lambda item: (item[0], str(item[1]).split('.')[0] if not isinstance(item[1], (dict, list)) else item[1]), d.items()))

    converted_list_of_dicts = [convert_values(d) for d in list_data]
    return converted_list_of_dicts

#-------------------------------------------------------------------------------------------

def insert_tds(db:Session,tds_str:str):
   db_tds = models.tds(tds = tds_str)
   db.add(db_tds)
   try:
        db.commit()
        return "Success"
   except :
       db.rollback()
       return "Failure"

def get_tds(db:Session):
    return db.query(models.tds).filter(models.tds.tds_status==1).all()

def delete_tds(db:Session,tds_id:int):
    db_res = db.query(models.tds).filter(models.tds.tds_id==tds_id).first()
    db_res.tds_status = 0
    try:
        db.commit()
        return "Success"
    except:
        return "Failure"

def update_tds(db:Session,tds_name:str,tds_id:int):
    db_res = db.query(models.tds).filter(models.tds.tds_id==tds_id).first()
    db_res.tds = tds_name
    try:
        db.commit()
        return "Success"
    except:
        return "Failure"
    
#-------------------------------------------------------------------------------------------

def insert_gst(db:Session,gst_str:str):
   db_gst = models.gst(gst = gst_str)
   db.add(db_gst)
   try:
        db.commit()
        return "Success"
   except :
       db.rollback()
       return "Failure"

def get_gst(db:Session):
    return db.query(models.gst).filter(models.gst.gst_status==1).all()

def delete_gst(db:Session,gst_id:int):
    db_res = db.query(models.gst).filter(models.gst.gst_id==gst_id).first()
    db_res.gst_status = 0
    try:
        db.commit()
        return "Success"
    except:
        return "Failure"

def update_gst(db:Session,gst:str,gst_id:int):
    db_res = db.query(models.gst).filter(models.gst.gst_id==gst_id).first()
    db_res.gst = gst
    try:
        db.commit()
        return "Success"
    except:
        return "Failure"
    
#-------------------------------------------------------------------------------------------


def delete_entity(db:Session,record_service_id:int):
    db_res = db.query(models.TL).filter(models.TL.Service_ID==record_service_id).first()
    db_res.status = 0
    try:
        db.commit()
        return "Success"
    except:
        return "Failure"
    
#-------------------------------------------------------------------------------------------

def lastfivereports(db: Session, picked_date: str, to_date: str, reportoptions: str ):
    date_time_formate_string = '%Y-%m-%d %H:%M:%S'
    list_data = []

    # fetch_hold_data(db)

    d1 = picked_date
    d2 = to_date

    # Convert strings to datetime objects
    start_date = datetime.strptime(d1, '%Y-%m-%d')
    end_date = datetime.strptime(d2, '%Y-%m-%d')

    # Generate all dates in between and store as strings
    dates_list = []
    current_date = start_date

    while current_date <= end_date:
        
        dates_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

#     # dates_list contains all dates as strings
    # 

    for item in dates_list:
        # 
        list_data.append(report.user_wise_report(db,item,reportoptions))
        
    list_data = [item for item in list_data if item]
    return list_data

#----------------------------------------------------------------------------
def Hold_Wise_Day_Wise_Part(db: Session, picked_date: str, to_date: str):
    date_time_formate_string = '%Y-%m-%d %H:%M:%S'
    list_data = []

    # fetch_hold_data(db)

    date_time1 = datetime.now()
    # todatedd = datetime.strptime(to_date, "%Y-%m-%d")

    # db_res = db.query(models.TL).filter(models.TL.status == 1,
    #     or_(
    #         models.TL.working_time.between(picked_date, to_date),
    #         models.TL.reallocated_time.between(picked_date, to_date),
            
    #     )
    # ).all()

    list_data = []
    list_ddata1 = set()


    db_res2 = db.query(models.TL).filter(
        models.TL.status == 1,
        models.TL.working_time.between(picked_date, to_date)    
    )

    for row2 in db_res2:
        list_ddata1.add(row2.Service_ID)

    db_res2 = db.query(models.TL).filter(
        models.TL.status == 1,
        models.TL.Service_ID == models.HOLD.Service_ID,
        or_(
            models.HOLD.hold_time_end.between(picked_date, to_date),
            models.TL.working_time.between(picked_date, to_date)
        )
        
    )

    for row2 in db_res2:
        list_ddata1.add(row2.Service_ID)
    
    db_res2 = db.query(models.TL).filter(
        models.TL.status == 1,
        models.TL.Service_ID == models.END_OF_DAY.Service_ID,
        or_(
            models.END_OF_DAY.end_time_end.between(picked_date, to_date),
            models.TL.working_time.between(picked_date, to_date)
        )
    )

    for row2 in db_res2:
        list_ddata1.add(row2.Service_ID)
        

# final query
    db_res =  db.query(models.TL).filter(
        models.TL.status == 1,
        models.TL.Service_ID.in_(list_ddata1)
    ).all()


    for row in db_res:
        data = {}
        data["date"] = datetime.strptime(row.working_time, date_time_formate_string).date()
        data["user"] = row._user_table1.username
        data["Service_ID"] = row.Service_ID
        data["scope"] = row.Scope
        data["subscopes"] = row.From
        data["entity"] = row.name_of_entity
        data["status"] = row.work_status
        data["type_of_activity"] = row.type_of_activity
        data["Nature_of_Work"] = row._nature_of_work.work_name
        data["gst_tan"] = row.gst_tan
        data["estimated_d_o_d"] =  row.estimated_d_o_d
        data["estimated_time"] =  row.estimated_time
        # username = db.query(User_table).filter(User.user_id == row.Assigned_To).first()
        data["member_name"] = row._user_table1.firstname +' '+ row._user_table1.lastname
        
        date_time2 = datetime.strptime(row.working_time, date_time_formate_string)
        time_diff = date_time1 - date_time2
        work_hour_hours_diff = time_diff


        # -----end of the day
        # db_res2 = db.query(models.END_OF_DAY).filter(
        #     models.END_OF_DAY.Service_ID == row.Service_ID,
        #     cast(models.END_OF_DAY.end_time_start, Date) >= todatedd
        # ).all()

        
        
        
        # end_hour_diff = timedelta(hours=0)
        # date_time_format_string = '%Y-%m-%d %H:%M:%S'
        # for row2 in db_res2:
        #     if row2.end_time_end and row2.end_time_start:

        #         
                

        #         datetime_obj1 = datetime.strptime(row2.end_time_start, "%Y-%m-%d %H:%M:%S")
        #         datetime_obj2 = datetime.strptime(row2.end_time_end, "%Y-%m-%d %H:%M:%S")

        #         # Calculate the difference
        #         time_difference = datetime_obj2 - datetime_obj1

        #         
        #         current_datetime = datetime.now()
        #         current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")


        #         date_time11 = datetime.strptime(row2.end_time_end, date_time_format_string)
        #         date_time22 = datetime.strptime(row2.end_time_start, date_time_format_string)
        #         time_diff = date_time11 - date_time22
        #         end_hour_diff += time_diff
        #         
        #     else:
        #         if not (row.work_status == "Completed" or (row.work_status == "in_progress" or row.work_status == "End Of Day")):
        #             
                    

        #             datetime_obj1 = datetime.strptime(row2.end_time_start, "%Y-%m-%d %H:%M:%S")
        #             datetime_obj2 = datetime.strptime(row2.end_time_end, "%Y-%m-%d %H:%M:%S")

        #             # Calculate the difference
        #             time_difference = datetime_obj2 - datetime_obj1

        #             
        #             current_datetime = datetime.now()
        #             current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        #             

        #             

        #             datetime_obj1 = datetime.strptime(row2.end_time_start, "%Y-%m-%d %H:%M:%S")
        #             minus = datetime.now()
        #             minus_datetime_str = minus.strftime("%Y-%m-%d %H:%M:%S")

        #             time_difference =  datetime_obj1 - minus_datetime_str


        #             end_hour_diff += time_difference


       
        a = timedelta(hours=0)
        b = timedelta(hours=0)
        if row.work_status == "Reallocated":
            db_res2 = db.query(models.REALLOCATED).filter(
                models.REALLOCATED.Service_ID == row.Service_ID,
                models.REALLOCATED.re_time_start >= picked_date,
                models.REALLOCATED.re_time_end <= to_date
            ).all()

            re_hour_diff = timedelta(hours=0)

            for row2 in db_res2:
                if row2.re_time_start and row2.re_time_end and (datetime.strptime(row2.re_time_start, date_time_formate_string).date()==datetime.strptime(row2.re_time_end, date_time_formate_string).date()):
                    date_time2r = datetime.strptime(row2.re_time_start, date_time_formate_string)
                    re_time_diff = date_time1 - date_time2r
                    re_hour_diff += re_time_diff
                    data["reallocated"] = re_hour_diff
            a = work_hour_hours_diff
        if row.work_status == "Completed":
            a = work_hour_hours_diff
        else:
            b = work_hour_hours_diff

        # ----- Hold Hour ------
        db_res2 = db.query(models.HOLD).filter(
            models.HOLD.Service_ID == row.Service_ID,
            models.HOLD.hold_time_start >= picked_date,
            models.HOLD.hold_time_end <= to_date
        ).all()

        hold_hour_diff = timedelta(hours=0)

        for row2 in db_res2:
            if (row2.hold_time_end and row2.hold_time_start) and (datetime.strptime(row2.hold_time_end, date_time_formate_string).date()==datetime.strptime(row2.hold_time_start, date_time_formate_string).date()):
                
                date_time11 = datetime.strptime(row2.hold_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.hold_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                # 
                hold_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress") :
            #         time1 =  datetime.now() - datetime.strptime(row2.hold_time_start, date_time_formate_string)
            #         hold_hour_diff +=  time1

        data["hold"] = hold_hour_diff


        # 

        # ----- Meeting Hour ------
        db_res2 = db.query(models.MEETING).filter(
            models.MEETING.Service_ID == row.Service_ID,
            models.MEETING.meeting_time_start >= picked_date,
            models.MEETING.meeting_time_end <= to_date
        ).all()

        meet_hour_diff = timedelta(hours=0)

        for row2 in db_res2:
            if row2.meeting_time_end and row2.meeting_time_start  and (datetime.strptime(row2.meeting_time_end, date_time_formate_string).date()==datetime.strptime(row2.meeting_time_start, date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.meeting_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                meet_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.meeting_time_start, date_time_formate_string)
            #         meet_hour_diff +=   time1



        data["meeting"] = meet_hour_diff

        # ----- Break Hour ------
        db_res2 = db.query(models.BREAK).filter(
            models.BREAK.Service_ID == row.Service_ID,
            models.BREAK.break_time_start >= picked_date,
            models.BREAK.break_time_end <= to_date
        ).all()

        break_hour_diff = timedelta(hours=0)

        for row2 in db_res2:
            if row2.break_time_end and row2.break_time_start   and (datetime.strptime(row2.break_time_end, date_time_formate_string).date()==datetime.strptime(row2.break_time_start , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.break_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.break_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                break_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.break_time_start, date_time_formate_string)
                 
            #         break_hour_diff += time1

        data["break"] = break_hour_diff

        # ----- Call Hour ------
        db_res2 = db.query(models.CALL).filter(
            models.CALL.Service_ID == row.Service_ID,
            models.CALL.call_time_start >= picked_date,
            models.CALL.call_time_end <= to_date
        ).all()

        call_hour_diff = timedelta(hours=0)

        for row2 in db_res2:
            if row2.call_time_end and row2.call_time_start    and (datetime.strptime(row2.call_time_end, date_time_formate_string).date()==datetime.strptime(row2.call_time_start  , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.call_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.call_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                call_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.call_time_start, date_time_formate_string)
                   
            #         call_hour_diff += time1

        data["call"] = call_hour_diff


        # -----end of the day
        temp = ''
        
        db_res2 = db.query(models.END_OF_DAY).filter(
            models.END_OF_DAY.Service_ID == row.Service_ID,
            models.END_OF_DAY.end_time_start>=picked_date,
            models.END_OF_DAY.end_time_start<=to_date
        ).all()

        count = db.query(models.END_OF_DAY).filter(
            models.END_OF_DAY.Service_ID == row.Service_ID,
            models.END_OF_DAY.end_time_start>=picked_date
        ).count()

        time_diff = timedelta(hours=0)
        if count >= 1 :
            for rom in db_res2:
                if rom.end_time_end == "":
                    temp = rom.end_time_start
                    parsed_date = datetime.strptime(str(temp), '%Y-%m-%d %H:%M:%S')
                    date_time22 = date_time1
                    time_diff += date_time22 - parsed_date
                else:
                    temp = rom.end_time_start
                    parsed_date = datetime.strptime(str(temp), '%Y-%m-%d %H:%M:%S')
                    date_time11 = datetime.strptime(rom.end_time_end, date_time_formate_string)
                    time_diff += date_time11 - parsed_date
        data["end_of_day"] = time_diff
        
        if row.work_status == "Completed":
            e_o_d = data["end_of_day"]
            data["in_progress"] = timedelta(hours=0)
            data["completed"] = (datetime.strptime(row.completed_time, date_time_formate_string) - datetime.strptime(row.working_time, date_time_formate_string)) - (call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + e_o_d)
            # data["completed"] = (a + b) - (call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + e_o_d)
        else:
            e_o_d = data["end_of_day"]
            data["completed"] = timedelta(hours=0)
            if row.work_status != "End Of Day":
                data["in_progress"] = (a + b) - (call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + e_o_d)
            else:
                data["in_progress"] = (a + b) - (call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + e_o_d)
            

        # data["total_time_taken"] = call_hour_diff + break_hour_diff + meet_hour_diff + hold_hour_diff + data["completed"] + data["in_progress"]

        data["total_time_taken"] =  (data["in_progress"] + data["completed"] )
        # data["second_report_data"] = call_hour_diff + hold_hour_diff + data["completed"] + data["in_progress"]
        data["second_report_data"] =  data["completed"] + data["in_progress"]

        
#--------------------------------------------------------------------------------------------------------------------------------------
        # ----- HOLD Hour ------
        holdchargable = db.query(models.HOLD).join(
            models.TL, models.HOLD.Service_ID == models.TL.Service_ID
        ).filter(
            models.HOLD.Service_ID == row.Service_ID,
            models.HOLD.hold_time_start >= picked_date,
            models.HOLD.hold_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        holdchargable_hour_diff = timedelta(hours=0)

        for row2 in holdchargable:
            if row2.hold_time_end and row2.hold_time_start   and (datetime.strptime(row2.hold_time_end, date_time_formate_string).date()==datetime.strptime(row2.hold_time_start  , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.hold_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.hold_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                holdchargable_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.hold_time_start, date_time_formate_string)
                   
            #         holdchargable_hour_diff += time1


        
        
        # ----- Meeting Hour ------
        Meetingchargable = db.query(models.MEETING).join(
            models.TL, models.MEETING.Service_ID == models.TL.Service_ID
        ).filter(
            models.MEETING.Service_ID == row.Service_ID,
            models.MEETING.meeting_time_start >= picked_date,
            models.MEETING.meeting_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        meetch_hour_diff = timedelta(hours=0)

        for row2 in Meetingchargable:
            if row2.meeting_time_end and row2.meeting_time_start   and (datetime.strptime(row2.meeting_time_end, date_time_formate_string).date()==datetime.strptime(row2.meeting_time_start  , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.meeting_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                meetch_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                    
            #         meetch_hour_diff += time1


        
        
        # ----- Break Hour ------
        Breakchargable = db.query(models.BREAK).join(
            models.TL, models.BREAK.Service_ID == models.TL.Service_ID
        ).filter(
            models.BREAK.Service_ID == row.Service_ID,
            models.BREAK.break_time_start >= picked_date,
            models.BREAK.break_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        breakch_hour_diff = timedelta(hours=0)

        for row2 in Breakchargable:
            if row2.break_time_end and row2.break_time_start   and (datetime.strptime( row2.break_time_end, date_time_formate_string).date()==datetime.strptime(row2.break_time_start , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.break_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.break_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                breakch_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.break_time_start, date_time_formate_string)
                  
            #         breakch_hour_diff += time1


        
        
        # ----- Call Hour ------
        Callchargable = db.query(models.CALL).join(
            models.TL, models.CALL.Service_ID == models.TL.Service_ID
        ).filter(
            models.CALL.Service_ID == row.Service_ID,
            models.CALL.call_time_start >= picked_date,
            models.CALL.call_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        callch_hour_diff = timedelta(hours=0)

        for row2 in Callchargable:
            if row2.call_time_end and row2.call_time_start   and (datetime.strptime( row2.call_time_end, date_time_formate_string).date()==datetime.strptime(row2.call_time_start  , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.call_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.call_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                callch_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.call_time_start, date_time_formate_string)
                 
            #         callch_hour_diff += time1

        # -----end of the day
        endch = db.query(models.END_OF_DAY).join(
            models.TL, models.END_OF_DAY.Service_ID == models.TL.Service_ID
        ).filter(
            models.END_OF_DAY.Service_ID == row.Service_ID,
            models.END_OF_DAY.end_time_start >= picked_date,
            models.END_OF_DAY.end_time_end <= to_date,
            models.TL.type_of_activity == 'CHARGABLE'
        ).all()

        endch_hour_diff = timedelta(hours=0)

        for row2 in endch:
            if row2.end_time_end and row2.end_time_start and (datetime.strptime( row2.end_time_end , date_time_formate_string).date()==datetime.strptime(row2.end_time_start  , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.end_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.end_time_start, date_time_formate_string)
                time_diff = date_time22 - date_time11
                endch_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.end_time_start, date_time_formate_string)
                   
            #         endch_hour_diff += time1

        data["endch_hour_diff"] = endch_hour_diff
        if row.type_of_activity == "CHARGABLE":
            data["chargable_time"] = data["in_progress"] + data["completed"]
        else:
            data["chargable_time"] = timedelta(hours=0)

        parsed_time = datetime.strptime(data["estimated_time"], '%H:%M')
        time_delta = timedelta(hours=parsed_time.hour, minutes=parsed_time.minute)

        data["difference_a_b"] = time_delta - data["chargable_time"]
#--------------------------------------------------------------------------------------------------------------------------------------	



#--------------------------------------------------------------------------------------------------------------------------------------
        # ----- HOLD Hour ------
        holdchargable = db.query(models.HOLD).join(
            models.TL, models.HOLD.Service_ID == models.TL.Service_ID
        ).filter(
            models.HOLD.Service_ID == row.Service_ID,
            models.HOLD.hold_time_start >= picked_date,
            models.HOLD.hold_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        holdchargable_hour_diff = timedelta(hours=0)

        for row2 in holdchargable:
            if row2.hold_time_end and row2.hold_time_start    and (datetime.strptime(row2.hold_time_end, date_time_formate_string).date()==datetime.strptime(row2.hold_time_start  , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.hold_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.hold_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                holdchargable_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.hold_time_start, date_time_formate_string)
                   
            #         holdchargable_hour_diff += time1

        
        
        # ----- Meeting Hour ------
        Meetingchargable = db.query(models.MEETING).join(
            models.TL, models.MEETING.Service_ID == models.TL.Service_ID
        ).filter(
            models.MEETING.Service_ID == row.Service_ID,
            models.MEETING.meeting_time_start >= picked_date,
            models.MEETING.meeting_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        meetch_hour_diff = timedelta(hours=0)

        for row2 in Meetingchargable:
            if row2.meeting_time_end and row2.meeting_time_start    and (datetime.strptime(row2.meeting_time_end, date_time_formate_string).date()==datetime.strptime(row2.meeting_time_start  , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.meeting_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                meetch_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.meeting_time_start, date_time_formate_string)
                   
            #         meetch_hour_diff += time1

        
        
        # ----- Break Hour ------
        Breakchargable = db.query(models.BREAK).join(
            models.TL, models.BREAK.Service_ID == models.TL.Service_ID
        ).filter(
            models.BREAK.Service_ID == row.Service_ID,
            models.BREAK.break_time_start >= picked_date,
            models.BREAK.break_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        breakch_hour_diff = timedelta(hours=0)

        for row2 in Breakchargable:
            if row2.break_time_end and row2.break_time_start    and (datetime.strptime(row2.break_time_end, date_time_formate_string).date()==datetime.strptime(row2.break_time_start , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.break_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.break_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                breakch_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.break_time_start, date_time_formate_string)
                    
            #         breakch_hour_diff += time1


        
        
        # ----- Call Hour ------
        Callchargable = db.query(models.CALL).join(
            models.TL, models.CALL.Service_ID == models.TL.Service_ID
        ).filter(
            models.CALL.Service_ID == row.Service_ID,
            models.CALL.call_time_start >= picked_date,
            models.CALL.call_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        callch_hour_diff = timedelta(hours=0)

        for row2 in Callchargable:
            if row2.call_time_end and row2.call_time_start    and (datetime.strptime( row2.call_time_end, date_time_formate_string).date()==datetime.strptime(row2.call_time_start  , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.call_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.call_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                callch_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.call_time_start, date_time_formate_string)
                  
            #         callch_hour_diff += time1

        # -----end of the day
        endch = db.query(models.END_OF_DAY).join(
            models.TL, models.END_OF_DAY.Service_ID == models.TL.Service_ID
        ).filter(
            models.END_OF_DAY.Service_ID == row.Service_ID,
            models.END_OF_DAY.end_time_start >= picked_date,
            models.END_OF_DAY.end_time_end <= to_date,
            models.TL.type_of_activity == 'Non-Charchable'
        ).all()

        endch_hour_diff = timedelta(hours=0)

        for row2 in endch:
            if row2.end_time_end and row2.end_time_start  and (datetime.strptime( row2.end_time_end , date_time_formate_string).date()==datetime.strptime(row2.end_time_start  , date_time_formate_string).date()):
                date_time11 = datetime.strptime(row2.end_time_end, date_time_formate_string)
                date_time22 = datetime.strptime(row2.end_time_start, date_time_formate_string)
                time_diff = date_time11 - date_time22
                endch_hour_diff += time_diff
            # else :
            #     if not(row.work_status == "Completed" or row.work_status == "in_progress"):
            #         time1 =  datetime.now() - datetime.strptime(row2.end_time_start, date_time_formate_string)
            #         endch_hour_diff += time1
	    

        data["endch_hour_diff"] = endch_hour_diff
        if row.type_of_activity == "Non-Charchable":
            data["Non_Charchable_time"] = endch_hour_diff 
        else:
            data["Non_Charchable_time"] = timedelta(hours=0)
        data["chargable_and_non_chargable"] = data["Non_Charchable_time"] + data["chargable_time"]
#--------------------------------------------------------------------------------------------------------------------------------------	



        str_temp = ""
        str_temper = ""

        if row.work_status == "Work in Progress":

            data["third_report_data"] = ""

        elif row.work_status == "Hold":

            db_res3 = db.query(models.HOLD).filter(
                models.HOLD.Service_ID == row.Service_ID,
            ).all()
            for hold_obj in db_res3:
                data["third_report_data"] = hold_obj.remarks
                str_temper = hold_obj.remarks

        elif row.work_status == "Meeting":

            db_res3 = db.query(models.MEETING).filter(
                models.MEETING.Service_ID == row.Service_ID,
            ).all()
            for meet_obj in db_res3:
                data["third_report_data"] = meet_obj.remarks


        elif row.work_status == "Break":
            db_res3 = db.query(models.BREAK).filter(
                models.BREAK.Service_ID == row.Service_ID,
            ).all()
            for break_obj in db_res3:
                
                data["third_report_data"] = break_obj.remarks
                
        elif row.work_status == "Clarification Call":
            db_res3 = db.query(models.CALL).filter(
                models.CALL.Service_ID == row.Service_ID,
            ).all()
            for call_obj in db_res3:
                
                data["third_report_data"] = call_obj.remarks

        elif row.work_status == "Completed":
            data["third_report_data"] = row.remarks

        if row.work_status == "Completed":
            try:
                db_res3 = db.query(models.HOLD).filter(
                    models.HOLD.Service_ID == row.Service_ID,
                ).all()
                for hold_obj in db_res3:
                    str_temp = str_temp + hold_obj.remarks + ","
            except:
                str_temp = ""
            try:
                db_res3 = db.query(models.MEETING).filter(
                    models.MEETING.Service_ID == row.Service_ID,
                ).all()
                for meet_obj in db_res3:

                    str_temp = str_temp + meet_obj.remarks + ","

            except:
                str_temp = ""
            try:
                db_res3 = db.query(models.BREAK).filter(
                    models.BREAK.Service_ID == row.Service_ID,
                ).all()
                for break_obj in db_res3:
                    str_temp = str_temp + break_obj.remarks + ","
            except:
                str_temp = ""
            try:
                db_res3 = db.query(models.CALL).filter(
                    models.CALL.Service_ID == row.Service_ID,
                ).all()
                for call_obj in db_res3:
                    str_temp = str_temp + call_obj.remarks + ","
                str_temp = str_temp + row.remarks + ","
            except:
                str_temp = ""

        data["fourth_report"] = row.no_of_items
        data["fourth_report2"] = str_temp
        data["fifth_report"] = str_temper        
        list_data.append(data)
    def convert_values(d):
        return dict(map(lambda item: (item[0], str(item[1]).split('.')[0] if not isinstance(item[1], (dict, list)) else item[1]), d.items()))

    converted_list_of_dicts = [convert_values(d) for d in list_data]
    return converted_list_of_dicts




def convert_to_duration(value):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_duration = f"{hours}:{minutes}:{seconds}"
        
        return formatted_duration


def totalfivereports(db: Session, picked_date: str, to_date: str, reportoptions: str ):
    
    
    # fetch_hold_data(db)
    
    if reportoptions == "userlist":
        

            finalre = {
                'estimated_time_with_add' : pendulum.duration(),
                'date': set(),
                'user': set(),
                'Service_ID': set(),
                'created_at' : set(),
                'Completed_date' : set(),
                'scope': set(),
                'subscopes': set(),
                'entity': set(),
                'status': set(),
                'type_of_activity': set(),
                'Nature_of_Work': set(),
                'gst_tan': set(),
                'estimated_d_o_d': set(),
                'estimated_time': set(),
                'member_name': set(),
                'end_time': pendulum.duration(),
                'hold': pendulum.duration(),
                'break': pendulum.duration(),
                'time_diff_work': pendulum.duration(),
                'call': pendulum.duration(),
                'meeting': pendulum.duration(),
                'in_progress': pendulum.duration(),
                'completed': pendulum.duration(),
                'third_report_data' : set(),
                'fourth_report' :  set(),
                'fourth_report2' : set(),
                'fifth_report' : set(),
                'no_of_items' : set(),
                'chargable' : set(),
                'non-chargable' : set(),
                'total-time' : set(),
                'idealname' : pendulum.duration()
            }

            date_time_formate_string = '%Y-%m-%d %H:%M:%S'
            list_data = []
            result_data = []
            


            d1 = picked_date
            d2 = to_date

            # Convert strings to datetime objects
            start_date = datetime.strptime(d1, '%Y-%m-%d')
            end_date = datetime.strptime(d2, '%Y-%m-%d')

            # Generate all dates in between and store as strings
            dates_list = []
            current_date = start_date

            while current_date <= end_date:
                
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

        #     # dates_list contains all dates as strings
            # 

            for item in dates_list:
                # 
                list_data.append(totaltime.user_wise_report(db,item,reportoptions))
                
            list_data = [item for item in list_data if item]

            common =  set()

            for report_list in list_data:
                for entry in report_list:
                        my_set = {str(x) for x in entry['user']} 
                        common.add(my_set.pop())
            
            for finalitems in common:
                for report_list in list_data:
                    
                    for entry in report_list:
                        
                        if entry['user']=={finalitems}:
                            # 

                            
                            for key in finalre.keys():
                                                                             
                                        if key == 'end_time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'estimated_time_with_add':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'hold':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'break':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'time_diff_work':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'call':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'meeting':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'in_progress':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'idealname':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'completed':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'no_of_items':
                                        
                                            try:
                                                
                                                if len(finalre[key]) == 0:
                                                    finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                else:
                                                    finalre[key] = entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'non-chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'total-time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        else:
                                            finalre[key] = entry[key].union(finalre[key])


                result = {
                    'estimated_time_with_add' : set(),
                    'work_started_date' : set(),
                    'work_ended_date' : set(),
                    'number_of_days_taken' : set(),
                    'number_of_days_delayed' : set(),
                    'actual_date_of_delivery' : set(),
                    'estimated_date_of_delivery' : set(),
                    'number_of_entity' : set(),
                    'estimated_time_minus_chargable_time' : set(),
                    'date': set(),
                    'user': set(),
                    'Service_ID': set(),
                    'created_at' : set(),
                    'Completed_date' : set(),
                    'scope': set(),
                    'subscopes': set(),
                    'entity': set(),
                    'status': set(),
                    'type_of_activity': set(),
                    'Nature_of_Work': set(),
                    'gst_tan': set(),
                    'estimated_d_o_d': set(),
                    'estimated_time': set(),
                    'member_name': set(),
                    'end_time': set(),
                    'hold': set(),
                    'break': set(),
                    'time_diff_work': set(),
                    'call': set(),
                    'meeting': set(),
                    'in_progress': set(),
                    'completed': set(),
                    'third_report_data' : set(),
                    'fourth_report' :  set(),
                    'fourth_report2' : set(),
                    'fifth_report' : set(),
                    'no_of_items' : set(),
                    'chargable' : set(),
                    'non-chargable' : set(),
                    'total-time' : set(),
                    'idealname' : set()
                }
                
                for key in finalre:
                    if isinstance(finalre[key], set):

                            cpof = finalre[key]
                            result[key]= cpof
                           
                            finalre[key] = set()

                    else:
                    
                        result[key].add(convert_to_duration(finalre[key]))
                        finalre[key] = pendulum.duration()
                


#--------------------------- last calculation


                
                
                
                # Define the set of date strings
                date_strings = result['date']

                # Convert the date strings to datetime objects
                dateslast = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find the maximum date
                max_date = max(dateslast)

                min_date = min(dateslast)

                
                


                
                # Define the set of date strings
                date_strings_date = result['estimated_d_o_d']

                # Convert the date strings to datetime objects
                dateslast_date = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings_date}

                # Find the maximum date
                max_date_in_dates = max(dateslast_date)

                


#--------------------------- last calculation


                dateesti =  max_date_in_dates.strftime("%Y-%m-%d")

                # Define the set of date strings
                date_strings = result['date']

                # Convert dateesti to a datetime object
                dateesti_dt = datetime.strptime(dateesti, "%Y-%m-%d").date()

                # Convert the set of date strings to a set of datetime objects
                dates = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find and count the dates that are greater than dateesti_dt
                greater_dates = {date for date in dates if date > dateesti_dt}
                count_greater_dates = len(greater_dates)

                # Print the count
                


#-----------------------------getting estimate time
                

                estichar = result['estimated_time_with_add'].pop()
                hourses, minuteses, secondses = map(int, estichar.split(':'))

                # Create a pendulum Duration object
                durationes = pendulum.duration(hours=hourses, minutes=minuteses, seconds=secondses)

#----------------------------------------- chargable time


                nchar = result['chargable'].pop()

                hours, minutes, seconds = map(int, nchar.split(':'))

                # Create a pendulum Duration object
                duration = pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
                
#------------------------ late of date estimated
                result['chargable'] = nchar
                result['estimated_time_with_add'] = estichar
                result['work_started_date'] =  min_date
                result['work_ended_date'] = max_date
                result['number_of_days_taken'] = len(result['date'])
                result['number_of_days_delayed'] = count_greater_dates
                result['actual_date_of_delivery'] = max_date_in_dates 
                result['estimated_date_of_delivery'] = max_date_in_dates
                result['number_of_entity'] = len(result['entity'])
                result['estimated_time_minus_chargable_time'] = convert_to_duration(durationes-duration)

#------------------------------ code end

                result_data.append(result)
                result = {}


            return result_data

        

    elif reportoptions == "entitylist":

            finalre = {
                'estimated_time_with_add' : pendulum.duration(),
                'date': set(),
                'user': set(),
                'Service_ID': set(),
                'created_at' : set(),
                'Completed_date' : set(),
                'scope': set(),
                'subscopes': set(),
                'entity': set(),
                'status': set(),
                'type_of_activity': set(),
                'Nature_of_Work': set(),
                'gst_tan': set(),
                'estimated_d_o_d': set(),
                'estimated_time': set(),
                'member_name': set(),
                'end_time': pendulum.duration(),
                'hold': pendulum.duration(),
                'break': pendulum.duration(),
                'time_diff_work': pendulum.duration(),
                'call': pendulum.duration(),
                'meeting': pendulum.duration(),
                'in_progress': pendulum.duration(),
                'completed': pendulum.duration(),
                'third_report_data' : set(),
                'fourth_report' :  set(),
                'fourth_report2' : set(),
                'fifth_report' : set(),
                'no_of_items' : set(),
                'chargable' : set(),
                'non-chargable' : set(),
                'total-time' : set(),
                'idealname' : pendulum.duration()
            }

            date_time_formate_string = '%Y-%m-%d %H:%M:%S'
            list_data = []
            result_data = []
            


            d1 = picked_date
            d2 = to_date

            # Convert strings to datetime objects
            start_date = datetime.strptime(d1, '%Y-%m-%d')
            end_date = datetime.strptime(d2, '%Y-%m-%d')

            # Generate all dates in between and store as strings
            dates_list = []
            current_date = start_date

            while current_date <= end_date:
                
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

        #     # dates_list contains all dates as strings
            # 

            for item in dates_list:
                # 
                list_data.append(totaltime.user_wise_report(db,item,reportoptions))
                
            list_data = [item for item in list_data if item]

            common =  set()

            for report_list in list_data:
                for entry in report_list:
                        my_set = {str(x) for x in entry['entity']} 
                        common.add(my_set.pop())
            
            for finalitems in common:
                for report_list in list_data:
                    
                    for entry in report_list:
                        
                        if entry['entity']=={finalitems}:
                            # 

                            
                            for key in finalre.keys():

                                        if key == 'end_time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'estimated_time_with_add':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'hold':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'break':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'time_diff_work':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'call':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'meeting':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'in_progress':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'completed':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'idealname':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'no_of_items':
                                            try:
                                                
                                                if len(finalre[key]) == 0:
                                                    finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                else:
                                                    finalre[key] = entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'non-chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'total-time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        else:
                                            finalre[key] = entry[key].union(finalre[key])

                result = {
                    'estimated_time_with_add' : set(),
                    'work_started_date' : set(),
                    'work_ended_date' : set(),
                    'number_of_days_taken' : set(),
                    'number_of_days_delayed' : set(),
                    'actual_date_of_delivery' : set(),
                    'estimated_date_of_delivery' : set(),
                    'number_of_entity' : set(),
                    'estimated_time_minus_chargable_time' : set(),
                    'date': set(),
                    'user': set(),
                    'Service_ID': set(),
                    'created_at' : set(),
                    'Completed_date' : set(),
                    'scope': set(),
                    'subscopes': set(),
                    'entity': set(),
                    'status': set(),
                    'type_of_activity': set(),
                    'Nature_of_Work': set(),
                    'gst_tan': set(),
                    'estimated_d_o_d': set(),
                    'estimated_time': set(),
                    'member_name': set(),
                    'end_time': set(),
                    'hold': set(),
                    'break': set(),
                    'time_diff_work': set(),
                    'call': set(),
                    'meeting': set(),
                    'in_progress': set(),
                    'completed': set(),
                    'third_report_data' : set(),
                    'fourth_report' :  set(),
                    'fourth_report2' : set(),
                    'fifth_report' : set(),
                    'no_of_items' : set(),
                    'chargable' : set(),
                    'non-chargable' : set(),
                    'total-time' : set(),
                    'idealname' : set()
                }
                for key in finalre:
                    if isinstance(finalre[key], set):

                            cpof = finalre[key]
                            result[key]= cpof
                           
                            finalre[key] = set()

                    elif isinstance(finalre[key], int):
                          result[key] = finalre[key]
                        #   
                    else:
                    
                        result[key].add(convert_to_duration(finalre[key]))
                        finalre[key] = pendulum.duration()
                


#--------------------------- last calculation


                
                
                
                # Define the set of date strings
                date_strings = result['date']

                # Convert the date strings to datetime objects
                dateslast = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find the maximum date
                max_date = max(dateslast)

                min_date = min(dateslast)

                
                


                
                # Define the set of date strings
                date_strings_date = result['estimated_d_o_d']

                # Convert the date strings to datetime objects
                dateslast_date = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings_date}

                # Find the maximum date
                max_date_in_dates = max(dateslast_date)

                


#--------------------------- last calculation


                dateesti =  max_date_in_dates.strftime("%Y-%m-%d")

                # Define the set of date strings
                date_strings = result['date']

                # Convert dateesti to a datetime object
                dateesti_dt = datetime.strptime(dateesti, "%Y-%m-%d").date()

                # Convert the set of date strings to a set of datetime objects
                dates = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find and count the dates that are greater than dateesti_dt
                greater_dates = {date for date in dates if date > dateesti_dt}
                count_greater_dates = len(greater_dates)

                # Print the count
                


#-----------------------------getting estimate time
                

                estichar = result['estimated_time_with_add'].pop()
                hourses, minuteses, secondses = map(int, estichar.split(':'))

                # Create a pendulum Duration object
                durationes = pendulum.duration(hours=hourses, minutes=minuteses, seconds=secondses)

#----------------------------------------- chargable time


                nchar = result['chargable'].pop()

                hours, minutes, seconds = map(int, nchar.split(':'))

                # Create a pendulum Duration object
                duration = pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
                
#------------------------ late of date estimated
                result['chargable'] = nchar
                result['estimated_time_with_add'] = estichar
                result['work_started_date'] =  min_date
                result['work_ended_date'] = max_date
                result['number_of_days_taken'] = len(result['date'])
                result['number_of_days_delayed'] = count_greater_dates
                result['actual_date_of_delivery'] = max_date_in_dates 
                result['estimated_date_of_delivery'] = max_date_in_dates
                result['number_of_entity'] = len(result['entity'])
                result['estimated_time_minus_chargable_time'] = convert_to_duration(durationes-duration)

#------------------------------ code end
                result_data.append(result)
                result = {}


            return result_data

    elif reportoptions == "scopelist":
        
        

            finalre = {
                'estimated_time_with_add' : pendulum.duration(),
                'date': set(),
                'user': set(),
                'Service_ID': set(),
                'created_at' : set(),
                'Completed_date' : set(),
                'scope': set(),
                'subscopes': set(),
                'entity': set(),
                'status': set(),
                'type_of_activity': set(),
                'Nature_of_Work': set(),
                'gst_tan': set(),
                'estimated_d_o_d': set(),
                'estimated_time': set(),
                'member_name': set(),
                'end_time': pendulum.duration(),
                'hold': pendulum.duration(),
                'break': pendulum.duration(),
                'time_diff_work': pendulum.duration(),
                'call': pendulum.duration(),
                'meeting': pendulum.duration(),
                'in_progress': pendulum.duration(),
                'completed': pendulum.duration(),
                'third_report_data' : set(),
                'fourth_report' :  set(),
                'fourth_report2' : set(),
                'fifth_report' : set(),
                'no_of_items' : set(),
                'chargable' : set(),
                'non-chargable' : set(),
                'total-time' : set(),
                'idealname' : pendulum.duration()
            }

            date_time_formate_string = '%Y-%m-%d %H:%M:%S'
            list_data = []
            result_data = []
            


            d1 = picked_date
            d2 = to_date

            # Convert strings to datetime objects
            start_date = datetime.strptime(d1, '%Y-%m-%d')
            end_date = datetime.strptime(d2, '%Y-%m-%d')

            # Generate all dates in between and store as strings
            dates_list = []
            current_date = start_date

            while current_date <= end_date:
                
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

        #     # dates_list contains all dates as strings
            # 

            for item in dates_list:
                # 
                list_data.append(totaltime.user_wise_report(db,item,reportoptions))
                
            list_data = [item for item in list_data if item]

            common =  set()

            for report_list in list_data:
                for entry in report_list:
                        my_set = {str(x) for x in entry['scope']} 
                        common.add(my_set.pop())
            
            
            for finalitems in common:
                for report_list in list_data:
                    
                    for entry in report_list:
                        
                        if entry['scope']=={finalitems}:
                            # 

                            
                            for key in finalre.keys():

                                        if key == 'end_time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'estimated_time_with_add':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'hold':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'break':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'time_diff_work':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'call':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'meeting':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'in_progress':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'completed':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'idealname':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'no_of_items':
                                        
                                            try:
                                                
                                                if len(finalre[key]) == 0:
                                                    finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                else:
                                                    finalre[key] = entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'non-chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'total-time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        else:
                                            finalre[key] = entry[key].union(finalre[key])

                result = {
                    'estimated_time_with_add' : set(),
                    'date': set(),
                    'user': set(),
                    'Service_ID': set(),
                    'created_at' : set(),
                    'Completed_date' : set(),
                    'scope': set(),
                    'subscopes': set(),
                    'entity': set(),
                    'status': set(),
                    'type_of_activity': set(),
                    'Nature_of_Work': set(),
                    'gst_tan': set(),
                    'estimated_d_o_d': set(),
                    'estimated_time': set(),
                    'member_name': set(),
                    'end_time': set(),
                    'hold': set(),
                    'break': set(),
                    'time_diff_work': set(),
                    'call': set(),
                    'meeting': set(),
                    'in_progress': set(),
                    'completed': set(),
                    'third_report_data' : set(),
                    'fourth_report' :  set(),
                    'fourth_report2' : set(),
                    'fifth_report' : set(),
                    'no_of_items' : set(),
                    'chargable' : set(),
                    'non-chargable' : set(),
                    'total-time' : set(),
                    'idealname' : set()
                }
                for key in finalre:
                    if isinstance(finalre[key], set):

                            cpof = finalre[key]
                            result[key]= cpof
                           
                            finalre[key] = set()

                    else:
                    
                        result[key].add(convert_to_duration(finalre[key]))
                        finalre[key] = pendulum.duration()
                
                result_data.append(result)
                result = {}


            return result_data

    elif reportoptions == "subscope":
        
            
        

            finalre = {
                'estimated_time_with_add' : pendulum.duration(),
                'date': set(),
                'user': set(),
                'Service_ID': set(),
                'created_at' : set(),
                'Completed_date' : set(),
                'scope': set(),
                'subscopes': set(),
                'entity': set(),
                'status': set(),
                'type_of_activity': set(),
                'Nature_of_Work': set(),
                'gst_tan': set(),
                'estimated_d_o_d': set(),
                'estimated_time': set(),
                'member_name': set(),
                'end_time': pendulum.duration(),
                'hold': pendulum.duration(),
                'break': pendulum.duration(),
                'time_diff_work': pendulum.duration(),
                'call': pendulum.duration(),
                'meeting': pendulum.duration(),
                'in_progress': pendulum.duration(),
                'completed': pendulum.duration(),
                'third_report_data' : set(),
                'fourth_report' :  set(),
                'fourth_report2' : set(),
                'fifth_report' : set(),
                'no_of_items' : set(),
                'chargable' : set(),
                'non-chargable' : set(),
                'total-time' : set(),
                'idealname' : pendulum.duration()
            }

            date_time_formate_string = '%Y-%m-%d %H:%M:%S'
            list_data = []
            result_data = []
            


            d1 = picked_date
            d2 = to_date

            # Convert strings to datetime objects
            start_date = datetime.strptime(d1, '%Y-%m-%d')
            end_date = datetime.strptime(d2, '%Y-%m-%d')

            # Generate all dates in between and store as strings
            dates_list = []
            current_date = start_date

            while current_date <= end_date:
                
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

        #     # dates_list contains all dates as strings
            # 

            for item in dates_list:
                # 
                list_data.append(totaltime.user_wise_report(db,item,reportoptions))
                
            list_data = [item for item in list_data if item]

            common =  set()

            for report_list in list_data:
                for entry in report_list:
                        my_set = {str(x) for x in entry['subscopes']} 
                        common.add(my_set.pop())
            
            
            for finalitems in common:
                for report_list in list_data:
                    
                    for entry in report_list:
                        
                        if entry['subscopes']=={finalitems}:
                            # 

                            
                            for key in finalre.keys():

                                        if key == 'end_time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'estimated_time_with_add':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'hold':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'break':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'time_diff_work':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'call':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'meeting':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'in_progress':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'completed':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'no_of_items':
                                        
                                            try:
                                                
                                                if len(finalre[key]) == 0:
                                                    finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                else:
                                                    finalre[key] = entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'idealname':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'non-chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'total-time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        else:
                                            finalre[key] = entry[key].union(finalre[key])

                result = {
                    'estimated_time_with_add' : set(),
                    'date': set(),
                    'user': set(),
                    'Service_ID': set(),
                    'created_at' : set(),
                    'Completed_date' : set(),
                    'scope': set(),
                    'subscopes': set(),
                    'entity': set(),
                    'status': set(),
                    'type_of_activity': set(),
                    'Nature_of_Work': set(),
                    'gst_tan': set(),
                    'estimated_d_o_d': set(),
                    'estimated_time': set(),
                    'member_name': set(),
                    'end_time': set(),
                    'hold': set(),
                    'break': set(),
                    'time_diff_work': set(),
                    'call': set(),
                    'meeting': set(),
                    'in_progress': set(),
                    'completed': set(),
                    'third_report_data' : set(),
                    'fourth_report' :  set(),
                    'fourth_report2' : set(),
                    'fifth_report' : set(),
                    'no_of_items' : set(),
                    'chargable' : set(),
                    'non-chargable' : set(),
                    'total-time' : set(),
                    'idealname' : set()
                }
                for key in finalre:
                    if isinstance(finalre[key], set):

                            cpof = finalre[key]
                            result[key]= cpof
                           
                            finalre[key] = set()

                    else:
                    
                        result[key].add(convert_to_duration(finalre[key]))
                        finalre[key] = pendulum.duration()
                
                result_data.append(result)
                result = {}


            return result_data
    
    elif reportoptions == "nature":
        

        

            finalre = {
                'estimated_time_with_add' : pendulum.duration(),
                'date': set(),
                'user': set(),
                'Service_ID': set(),
                'created_at' : set(),
                'Completed_date' : set(),
                'scope': set(),
                'subscopes': set(),
                'entity': set(),
                'status': set(),
                'type_of_activity': set(),
                'Nature_of_Work': set(),
                'gst_tan': set(),
                'estimated_d_o_d': set(),
                'estimated_time': set(),
                'member_name': set(),
                'end_time': pendulum.duration(),
                'hold': pendulum.duration(),
                'break': pendulum.duration(),
                'time_diff_work': pendulum.duration(),
                'call': pendulum.duration(),
                'meeting': pendulum.duration(),
                'in_progress': pendulum.duration(),
                'completed': pendulum.duration(),
                'third_report_data' : set(),
                'fourth_report' :  set(),
                'fourth_report2' : set(),
                'fifth_report' : set(),
                'no_of_items' : set(),
                'chargable' : set(),
                'non-chargable' : set(),
                'total-time' : set(),
                'idealname' : pendulum.duration()
            }

            date_time_formate_string = '%Y-%m-%d %H:%M:%S'
            list_data = []
            result_data = []
            


            d1 = picked_date
            d2 = to_date

            # Convert strings to datetime objects
            start_date = datetime.strptime(d1, '%Y-%m-%d')
            end_date = datetime.strptime(d2, '%Y-%m-%d')

            # Generate all dates in between and store as strings
            dates_list = []
            current_date = start_date

            while current_date <= end_date:
                
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

        #     # dates_list contains all dates as strings
            # 

            for item in dates_list:
                # 
                list_data.append(totaltime.user_wise_report(db,item,reportoptions))
                
            list_data = [item for item in list_data if item]

            common =  set()

            for report_list in list_data:
                for entry in report_list:
                        my_set = {str(x) for x in entry['Nature_of_Work']} 
                        common.add(my_set.pop())
            
            
            for finalitems in common:
                for report_list in list_data:
                    
                    for entry in report_list:
                        
                        if entry['Nature_of_Work']=={finalitems}:
                            

                            
                            for key in finalre.keys():

                                        if key == 'end_time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'estimated_time_with_add':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'hold':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'break':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'time_diff_work':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'call':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'meeting':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'in_progress':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'completed':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'idealname':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'no_of_items':
                                        
                                            try:
                                                
                                                if len(finalre[key]) == 0:
                                                    finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                else:
                                                    finalre[key] = entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'non-chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'total-time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        else:
                                            finalre[key] = entry[key].union(finalre[key])

                result = {
                    'estimated_time_with_add' : set(),
                    'date': set(),
                    'user': set(),
                    'Service_ID': set(),
                    'created_at' : set(),
                    'Completed_date' : set(),
                    'scope': set(),
                    'subscopes': set(),
                    'entity': set(),
                    'status': set(),
                    'type_of_activity': set(),
                    'Nature_of_Work': set(),
                    'gst_tan': set(),
                    'estimated_d_o_d': set(),
                    'estimated_time': set(),
                    'member_name': set(),
                    'end_time': set(),
                    'hold': set(),
                    'break': set(),
                    'time_diff_work': set(),
                    'call': set(),
                    'meeting': set(),
                    'in_progress': set(),
                    'completed': set(),
                    'third_report_data' : set(),
                    'fourth_report' :  set(),
                    'fourth_report2' : set(),
                    'fifth_report' : set(),
                    'no_of_items' : set(),
                    'chargable' : set(),
                    'non-chargable' : set(),
                    'total-time' : set(),
                    'idealname' : set()
                }
                for key in finalre:
                    if isinstance(finalre[key], set):

                            cpof = finalre[key]
                            result[key]= cpof
                           
                            finalre[key] = set()

                    else:
                    
                        result[key].add(convert_to_duration(finalre[key]))
                        finalre[key] = pendulum.duration()
                
                result_data.append(result)
                result = {}


            return result_data


    elif reportoptions == "twenty":

            finalre = {
                'estimated_time_with_add' : pendulum.duration(),
                'date': set(),
                'user': set(),
                'Service_ID': set(),
                'scope': set(),
                'created_at' : set(),
                'Completed_date' : set(),
                'subscopes': set(),
                'entity': set(),
                'status': set(),
                'type_of_activity': set(),
                'Nature_of_Work': set(),
                'gst_tan': set(),
                'estimated_d_o_d': set(),
                'estimated_time': set(),
                'member_name': set(),
                'end_time': pendulum.duration(),
                'hold': pendulum.duration(),
                'break': pendulum.duration(),
                'time_diff_work': pendulum.duration(),
                'call': pendulum.duration(),
                'meeting': pendulum.duration(),
                'in_progress': pendulum.duration(),
                'completed': pendulum.duration(),
                'third_report_data' : set(),
                'fourth_report' :  set(),
                'fourth_report2' : set(),
                'fifth_report' : set(),
                'no_of_items' : set(),
                'chargable' : set(),
                'non-chargable' : set(),
                'total-time' : set(),
                'idealname' : pendulum.duration()
            }

            date_time_formate_string = '%Y-%m-%d %H:%M:%S'
            list_data = []
            result_data = []
            


            d1 = picked_date
            d2 = to_date

            # Convert strings to datetime objects
            start_date = datetime.strptime(d1, '%Y-%m-%d')
            end_date = datetime.strptime(d2, '%Y-%m-%d')

            # Generate all dates in between and store as strings
            dates_list = []
            current_date = start_date

            while current_date <= end_date:
                
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)

        #     # dates_list contains all dates as strings
            # 

            for item in dates_list:
                # 
                list_data.append(totaltime.user_wise_report(db,item,reportoptions))
                
            list_data = [item for item in list_data if item]

            common =  set()

            for report_list in list_data:
                for entry in report_list:
                        my_set = {str(x) for x in entry['Service_ID']} 
                        
                        common.add(my_set.pop())

            
            
            for finalitems in common:
                for report_list in list_data:
                    
                    for entry in report_list:

                        if int(finalitems) in entry['Service_ID']:
                            
                            
                            for key in finalre.keys():

                                        if key == 'end_time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'estimated_time_with_add':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'hold':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'break':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'time_diff_work':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'call':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'meeting':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'in_progress':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'completed':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'idealname':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'no_of_items':
                                            
                                            try:
                                                
                                                if len(finalre[key]) == 0:
                                                    finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                else:
                                                    finalre[key] = entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'non-chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'total-time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        else:
                                            finalre[key] = entry[key].union(finalre[key])

                result = {
                    'estimated_time_with_add' : set(),
                    'work_started_date' : set(),
                    'work_ended_date' : set(),
                    'number_of_days_taken' : set(),
                    'number_of_days_delayed' : set(),
                    'actual_date_of_delivery' : set(),
                    'estimated_date_of_delivery' : set(),
                    'number_of_entity' : set(),
                    'estimated_time_minus_chargable_time' : set(),
                    'date': set(),
                    'user': set(),
                    'Service_ID': set(),
                    'created_at' : set(),
                    'Completed_date' : set(),
                    'scope': set(),
                    'subscopes': set(),
                    'entity': set(),
                    'status': set(),
                    'type_of_activity': set(),
                    'Nature_of_Work': set(),
                    'gst_tan': set(),
                    'estimated_d_o_d': set(),
                    'estimated_time': set(),
                    'member_name': set(),
                    'end_time': set(),
                    'hold': set(),
                    'break': set(),
                    'time_diff_work': set(),
                    'call': set(),
                    'meeting': set(),
                    'in_progress': set(),
                    'completed': set(),
                    'third_report_data' : set(),
                    'fourth_report' :  set(),
                    'fourth_report2' : set(),
                    'fifth_report' : set(),
                    'no_of_items' : set(),
                    'chargable' : set(),
                    'non-chargable' : set(),
                    'total-time' : set(),
                    'idealname' : set()
                }
                for key in finalre:
                    if isinstance(finalre[key], set):

                            cpof = finalre[key]
                            result[key]= cpof
                           
                            finalre[key] = set()

                    elif isinstance(finalre[key], int):
                          result[key] = finalre[key]
                        #   
                    else:
                    
                        result[key].add(convert_to_duration(finalre[key]))
                        finalre[key] = pendulum.duration()
                


#--------------------------- last calculation


                

                # Define the set of date strings
                date_strings = result['date']
               
                # Convert the date strings to datetime objects
                dateslast = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find the maximum date
                max_date = max(dateslast)

                min_date = min(dateslast)




                # Define the set of date strings
                date_strings_date = result['estimated_d_o_d']

                # Convert the date strings to datetime objects
                dateslast_date = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings_date}

                # Find the maximum date
                max_date_in_dates = max(dateslast_date)

                


#--------------------------- last calculation


                dateesti =  max_date_in_dates.strftime("%Y-%m-%d")

                # Define the set of date strings
                date_strings = result['date']

                # Convert dateesti to a datetime object
                dateesti_dt = datetime.strptime(dateesti, "%Y-%m-%d").date()

                # Convert the set of date strings to a set of datetime objects
                dates = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find and count the dates that are greater than dateesti_dt
                greater_dates = {date for date in dates if date > dateesti_dt}
                count_greater_dates = len(greater_dates)

               

#-----------------------------getting estimate time
                

                estichar = result['estimated_time_with_add'].pop()
                hourses, minuteses, secondses = map(int, estichar.split(':'))

                # Create a pendulum Duration object
                durationes = pendulum.duration(hours=hourses, minutes=minuteses, seconds=secondses)

#----------------------------------------- chargable time


                nchar = result['chargable'].pop()

                hours, minutes, seconds = map(int, nchar.split(':'))

                # Create a pendulum Duration object
                duration = pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
                # 
#------------------------ late of date estimated
                result['chargable'] = nchar
                result['estimated_time_with_add'] = estichar
                result['work_started_date'] =  min_date
                result['work_ended_date'] = max_date
                result['number_of_days_taken'] = len(result['date'])
                result['number_of_days_delayed'] = count_greater_dates
                result['actual_date_of_delivery'] = max_date_in_dates 
                result['estimated_date_of_delivery'] = max_date_in_dates
                result['number_of_entity'] = len(result['entity'])
                result['estimated_time_minus_chargable_time'] = convert_to_duration(durationes-duration)

#------------------------------ code end
                result_data.append(result)
                result = {}


            return result_data
    

#------------------------------------------------------------------------------------ Pasupathi



    elif reportoptions == "scope_subscope_natureofwork":

                    finalre = {
                        'estimated_time_with_add' : pendulum.duration(),
                        'date': set(),
                        'user': set(),
                        'Service_ID': set(),
                        'scope': set(),
                        'created_at' : set(),
                        'Completed_date' : set(),
                        'subscopes': set(),
                        'entity': set(),
                        # 'no_of_entity' : set(),
                        'status': set(),
                        'type_of_activity': set(),
                        'Nature_of_Work': set(),
                        'gst_tan': set(),
                        'estimated_d_o_d': set(),
                        'estimated_time': set(),
                        'member_name': set(),
                        'end_time': pendulum.duration(),
                        'hold': pendulum.duration(),
                        'break': pendulum.duration(),
                        'time_diff_work': pendulum.duration(),
                        'call': pendulum.duration(),
                        'meeting': pendulum.duration(),
                        'in_progress': pendulum.duration(),
                        'completed': pendulum.duration(),
                        'third_report_data' : set(),
                        'fourth_report' :  set(),
                        'fourth_report2' : set(),
                        'fifth_report' : set(),
                        'no_of_items' : set(),
                        'chargable' : set(),
                        'non-chargable' : set(),
                        'total-time' : set(),
                        'idealname' : pendulum.duration()
                    }

                    date_time_formate_string = '%Y-%m-%d %H:%M:%S'
                    list_data = []
                    result_data = []
                    


                    d1 = picked_date
                    d2 = to_date

                    # Convert strings to datetime objects
                    start_date = datetime.strptime(d1, '%Y-%m-%d')
                    end_date = datetime.strptime(d2, '%Y-%m-%d')

                    # Generate all dates in between and store as strings
                    dates_list = []
                    current_date = start_date

                    while current_date <= end_date:
                        
                        dates_list.append(current_date.strftime('%Y-%m-%d'))
                        current_date += timedelta(days=1)
                        

                #     # dates_list contains all dates as strings
                    # 
                    for item in dates_list:
                        # 
                        
                        
                        
                        
                        
                        
                        reportoptions="twenty"
                        list_data.append(totaltime.user_wise_report(db,item,reportoptions))

                                    
                    list_data = [item for item in list_data if item]

                    common =  set()
                    
                    
                    for report_list in list_data:
                        for entry in report_list:
                                my_set = {str(x) for x in entry['Service_ID']} 
                                
                                common.add(my_set.pop())

                                
                    for finalitems in common:
                        for report_list in list_data:
                            for entry in report_list:
                                if int(finalitems) in entry['Service_ID']:
                                    for key in finalre.keys():
                                                if key == 'end_time':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'estimated_time_with_add':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'hold':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'break':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'time_diff_work':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'call':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'meeting':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'in_progress':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'completed':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'idealname':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'no_of_items':
                                                    try:
                                                        
                                                    
                                                        finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                        
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'chargable':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'non-chargable':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'total-time':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                else:
                                                    finalre[key] = entry[key].union(finalre[key])

                        result = {
                            'estimated_time_with_add' : set(),
                            'work_started_date' : set(),
                            'work_ended_date' : set(),
                            'number_of_days_taken' : set(),
                            'number_of_days_delayed' : set(),
                            'actual_date_of_delivery' : set(),
                            'estimated_date_of_delivery' : set(),
                            'number_of_entity' : set(),
                            'estimated_time_minus_chargable_time' : set(),
                            'date': set(),
                            'user': set(),
                            'Service_ID': set(),
                            'created_at' : set(),
                            'Completed_date' : set(),
                            'scope': set(),
                            'subscopes': set(),
                            'entity': set(),
                            # 'no_of_entity' : set(),
                            'status': set(),
                            'type_of_activity': set(),
                            'Nature_of_Work': set(),
                            'gst_tan': set(),
                            'estimated_d_o_d': set(),
                            'estimated_time': set(),
                            'member_name': set(),
                            'end_time': set(),
                            'hold': set(),
                            'break': set(),
                            'time_diff_work': set(),
                            'call': set(),
                            'meeting': set(),
                            'in_progress': set(),
                            'completed': set(),
                            'third_report_data' : set(),
                            'fourth_report' :  set(),
                            'fourth_report2' : set(),
                            'fifth_report' : set(),
                            'no_of_items' : set(),
                            'chargable' : set(),
                            'non-chargable' : set(),
                            'total-time' : set(),
                            'idealname' : set()
                        }
                        for key in finalre:
                            if isinstance(finalre[key], set):

                                    cpof = finalre[key]
                                    result[key]= cpof
                                
                                    finalre[key] = set()

                            elif isinstance(finalre[key], int):
                                result[key] = finalre[key]
                                #   
                            else:
                            
                                result[key].add(convert_to_duration(finalre[key]))
                                finalre[key] = pendulum.duration()
                        


        #--------------------------- last calculation


                        

                        # Define the set of date strings
                        date_strings = result['date']
                    
                        # Convert the date strings to datetime objects
                        dateslast = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                        # Find the maximum date
                        max_date = max(dateslast)

                        min_date = min(dateslast)




                        # Define the set of date strings
                        date_strings_date = result['estimated_d_o_d']

                        # Convert the date strings to datetime objects
                        dateslast_date = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings_date}

                        # Find the maximum date
                        max_date_in_dates = max(dateslast_date)

                        


        #--------------------------- last calculation


                        dateesti =  max_date_in_dates.strftime("%Y-%m-%d")

                        # Define the set of date strings
                        date_strings = result['date']

                        # Convert dateesti to a datetime object
                        dateesti_dt = datetime.strptime(dateesti, "%Y-%m-%d").date()

                        # Convert the set of date strings to a set of datetime objects
                        dates = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                        # Find and count the dates that are greater than dateesti_dt
                        greater_dates = {date for date in dates if date > dateesti_dt}
                        count_greater_dates = len(greater_dates)

                    

        #-----------------------------getting estimate time
                        

                        estichar = result['estimated_time_with_add'].pop()
                        hourses, minuteses, secondses = map(int, estichar.split(':'))

                        # Create a pendulum Duration object
                        durationes = pendulum.duration(hours=hourses, minutes=minuteses, seconds=secondses)

        #----------------------------------------- chargable time


                        nchar = result['chargable'].pop()

                        hours, minutes, seconds = map(int, nchar.split(':'))

                        # Create a pendulum Duration object
                        duration = pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
                        # 
        #------------------------ late of date estimated
                        result['chargable'] = nchar
                        result['estimated_time_with_add'] = estichar
                        result['work_started_date'] =  min_date
                        result['work_ended_date'] = max_date
                        result['number_of_days_taken'] = len(result['date'])
                        result['number_of_days_delayed'] = count_greater_dates
                        result['actual_date_of_delivery'] = max_date_in_dates 
                        result['estimated_date_of_delivery'] = max_date_in_dates
                        result['number_of_entity'] = len(result['entity'])
                        result['estimated_time_minus_chargable_time'] = convert_to_duration(durationes-duration)

        #------------------------------ code end
                        result_data.append(result)
                        result = {}
                        # 
                        # 
                        # 
                    # CODE FOR COMBINING TOTAL-TIME STARTS HERE
                    newObj1 = {}

                    # 
                    # 
                    
                    for item in result_data: 
                        #

                        # 

                        # 

                        # 
                        tempGroup = ''
                        
                        for scope in item['scope']:
                            tempGroup+=scope

                        for subscopes in item['subscopes']:
                            tempGroup+=subscopes

                        for Nature_of_Work in item['Nature_of_Work']:
                            tempGroup+=Nature_of_Work

                        key_to_check = tempGroup

                        if key_to_check in newObj1:
                            if isinstance(item['user'], set):   
                                newObj1[tempGroup]['user'].update(item['user'])  # Update with a set of users
                            else:
                                newObj1[tempGroup]['user'].add(item['user'])  # Add a single user

                            oldETWA = newObj1[tempGroup]['estimated_time_with_add']
                            currentETWA = item['estimated_time_with_add']

                            oldendtime = newObj1[tempGroup]['end_time']
                            currentendtime = item['end_time']

                            oldhold = newObj1[tempGroup]['hold']
                            currenthold = item['hold']

                            oldbreak = newObj1[tempGroup]['break']
                            currentbreak = item['break']

                            oldTDW = newObj1[tempGroup]['time_diff_work']
                            currentTDW = item['time_diff_work']

                            oldcall = newObj1[tempGroup]['call']
                            currentcall = item['call']

                            oldmeeting = newObj1[tempGroup]['meeting']
                            currentmeeting = item['meeting']

                            oldInProgress = newObj1[tempGroup]['in_progress']
                            currentInProgress = item['in_progress']

                            oldcompleted = newObj1[tempGroup]['completed']
                            currentcompleted = item['completed']

                            oldchargable = newObj1[tempGroup]['chargable']
                            curentchargable = item['chargable']
                            
                            oldnonchargable = newObj1[tempGroup]['non-chargable']
                            curentnonchargable = item['non-chargable']

                            oldTime = newObj1[tempGroup]['total-time']
                            curentTime = item['total-time']
        #--------------------------------------------------------------------------------------
        #--------------------------Total-estimated_time_with_add-------------------------------
                            ETWAToAdd = {
                                'oldETWA': oldETWA,
                                'currentETWA' : currentETWA
                            }
                            
                            

                            total_ETWA = timedelta()

                            for times in ETWAToAdd:
                                time_value = ETWAToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_ETWA += time_str_to_timedelta(time_value)

                            total_ETWA_str1 = str(total_ETWA)

                            newObj1[tempGroup]['estimated_time_with_add'] = total_ETWA_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-end_time---------------------------------------------------
                            endtimeToAdd = {
                                'oldendtime': oldendtime,
                                'currentendtime' : currentendtime
                            }

                            
                            

                            total_endtime = timedelta()

                            for times in endtimeToAdd:
                                time_value = endtimeToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_endtime += time_str_to_timedelta(time_value)

                            total_endtime_str1 = str(total_endtime)

                            newObj1[tempGroup]['end_time'] = total_endtime_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-hold---------------------------------------------------
                            holdToAdd = {
                                'oldhold': oldhold,
                                'currenthold' : currenthold
                            }

                            
                            

                            total_hold = timedelta()

                            for times in holdToAdd:
                                time_value = holdToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_hold += time_str_to_timedelta(time_value)

                            total_hold_str1 = str(total_hold)

                            newObj1[tempGroup]['hold'] = total_hold_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-break------------------------------------------------------

                            breakToAdd = {
                                'oldbreak': oldbreak,
                                
                                'currentbreak' : currentbreak
                            }

                            
                            

                            total_break = timedelta()

                            for times in breakToAdd:
                                time_value = breakToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_break += time_str_to_timedelta(time_value)

                            total_break_str1 = str(total_break)

                            newObj1[tempGroup]['break'] = total_break_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-time_diff_work------------------------------------------------------

                            TDWToAdd = {
                                'oldTDW': oldTDW,
                                'currentTDW' : currentTDW
                            }

                            
                            

                            total_TDW = timedelta()

                            for times in TDWToAdd:
                                time_value = TDWToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_TDW += time_str_to_timedelta(time_value)

                            total_TDW_str1 = str(total_TDW)

                            newObj1[tempGroup]['time_diff_work'] = total_TDW_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-call------------------------------------------------------

                            callToAdd = {
                                'oldcall': oldcall,
                                'currentcall' : currentcall
                            }

                            
                            

                            total_call = timedelta()

                            for times in callToAdd:
                                time_value = callToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_call += time_str_to_timedelta(time_value)

                            total_call_str1 = str(total_call)

                            newObj1[tempGroup]['call'] = total_call_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-meeting------------------------------------------------------
                            meetingToAdd = {
                                'oldmeeting': oldmeeting,
                                'currentmeeting' : currentmeeting
                            }

                            
                            

                            total_meeting = timedelta()

                            for times in meetingToAdd:
                                time_value = meetingToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_meeting += time_str_to_timedelta(time_value)

                            total_meeting_str1 = str(total_meeting)

                            newObj1[tempGroup]['meeting'] =  total_meeting_str1
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-in_progress------------------------------------------------------

                            Inprogresstoadd = {
                                'oldInProgress': oldInProgress,
                                'currentInProgress' : currentInProgress
                            }

                            
                            

                            total_Inprogresstime = timedelta()

                            for times in Inprogresstoadd:
                                time_value = Inprogresstoadd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_Inprogresstime += time_str_to_timedelta(time_value)

                            total_time_str1 = str(total_Inprogresstime)

                            newObj1[tempGroup]['in_progress'] = total_time_str1 
                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-completed------------------------------------------------------
                            completedToAdd = {
                                'oldcompleted': oldcompleted,
                                'currentcompleted' : currentcompleted

                            }

                            
                            

                            total_completed = timedelta()

                            for times in completedToAdd:
                                time_value = completedToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time1 in time_value:
                                        time_value = ""
                                        time_value += time1
                                else:
                                    time_values = time_value
                                
                                total_completed += time_str_to_timedelta(time_value)

                            total_completed_str1 = str(total_completed)

                            newObj1[tempGroup]['estimated_time_with_add'] = total_completed_str1 


                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-chargable------------------------------------------------------
                            # oldchargable = newObj1[tempGroup]['chargable']
                            # curentchargable = item['chargable']

                            chargableToAdd = {
                                'oldchargable': oldchargable,
                                'curentchargable' : curentchargable

                            }

                            total_chargable = timedelta()

                            for times in chargableToAdd:
                                time_value = chargableToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time1 in time_value:
                                        time_value = ""
                                        time_value += time1
                                else:
                                    time_values = time_value
                                
                                total_chargable += time_str_to_timedelta(time_value)

                            total_chargable_str1 = str(total_chargable)

                            newObj1[tempGroup]['chargable'] = total_chargable_str1 

                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-non-chargable------------------------------------------------------

                            # oldnonchargable = newObj1[tempGroup]['non-chargable']
                            # curentnonchargable = item['non-chargable']

                            nonchargableToAdd = {
                                'oldnonchargable': oldnonchargable,
                                'curentnonchargable' : curentnonchargable

                            }

                            total_nonchargable = timedelta()

                            for times in nonchargableToAdd:
                                time_value = nonchargableToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time1 in time_value:
                                        time_value = ""
                                        time_value += time1
                                else:
                                    time_values = time_value
                                
                                total_nonchargable += time_str_to_timedelta(time_value)

                            total_nonchargable_str1 = str(total_nonchargable)

                            newObj1[tempGroup]['non-chargable'] = total_nonchargable_str1 

                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-total_time------------------------------------------------------

                            timesToAdd = {
                                'oldTime': oldTime,
                                'curentTime': curentTime
                            }
                            
                            
                            # Initialize a timedelta object to store the total time
                            total_time = timedelta()

                            # Iterate through the keys to add the time
                            for times in timesToAdd:                        
                                #time_value = next(iter(timesToAdd[times]))  # Extract the single item from the set                        
                                time_value = timesToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_values += time
                                else:
                                    time_values = time_value
                                
                                total_time += time_str_to_timedelta(time_values)

                            # Convert total_time back to a string in HH:MM:SS format
                            total_time_str = str(total_time)  

                            # newObj[tempGroup] = item     #-----(THIS LINE UPDATE THE RECENT RECORD TO THE RESPONSE)

                            newObj1[tempGroup]['total-time'] = total_time_str                    
                        else:
                            if not isinstance(item['user'], set):
                                    item['user'] = {item['user']}  # Convert the user to a set
                                    newObj1[tempGroup] = item  
                            newObj1[tempGroup] = item               
                        
                    combinedArr = []

                    for key, value in newObj1.items():
                        combinedArr.append(value)

                    result_data = combinedArr
                    # CODE FOR COMBINING TOTAL-TIME ENDS HERE
                    
                    

                    
                    


                    return result_data
        
    elif reportoptions == "scope_subscope":
                    print('ddddddddddddddddddddddddddddddddddddddddddddddddd')
                    finalre = {
                        'estimated_time_with_add' : pendulum.duration(),
                        'date': set(),
                        'user': set(),
                        'Service_ID': set(),
                        'scope': set(),
                        'created_at' : set(),
                        'Completed_date' : set(),
                        'subscopes': set(),
                        'entity': set(),
                        # 'no_of_entity' : set(),
                        'status': set(),
                        'type_of_activity': set(),
                        'Nature_of_Work': set(),
                        'gst_tan': set(),
                        'estimated_d_o_d': set(),
                        'estimated_time': set(),
                        'member_name': set(),
                        'end_time': pendulum.duration(),
                        'hold': pendulum.duration(),
                        'break': pendulum.duration(),
                        'time_diff_work': pendulum.duration(),
                        'call': pendulum.duration(),
                        'meeting': pendulum.duration(),
                        'in_progress': pendulum.duration(),
                        'completed': pendulum.duration(),
                        'third_report_data' : set(),
                        'fourth_report' :  set(),
                        'fourth_report2' : set(),
                        'fifth_report' : set(),
                        'no_of_items' : set(),
                        'chargable' : set(),
                        'non-chargable' : set(),
                        'total-time' : set(),
                        'idealname' : pendulum.duration()
                    }

                    date_time_formate_string = '%Y-%m-%d %H:%M:%S'
                    list_data = []
                    result_data = []
                    


                    d1 = picked_date
                    d2 = to_date

                    # Convert strings to datetime objects
                    start_date = datetime.strptime(d1, '%Y-%m-%d')
                    end_date = datetime.strptime(d2, '%Y-%m-%d')

                    # Generate all dates in between and store as strings
                    dates_list = []
                    current_date = start_date

                    while current_date <= end_date:
                        
                        dates_list.append(current_date.strftime('%Y-%m-%d'))
                        current_date += timedelta(days=1)
                        

                #     # dates_list contains all dates as strings
                    # 
                    for item in dates_list:
                        reportoptions="twenty"
                        list_data.append(totaltime.user_wise_report(db,item,reportoptions))

                        
                    list_data = [item for item in list_data if item]

                    common =  set()
                    # 
                    # 
                    for report_list in list_data:
                        for entry in report_list:
                                my_set = {str(x) for x in entry['Service_ID']} 
                                
                                common.add(my_set.pop())

                                
                    for finalitems in common:
                        for report_list in list_data:
                            for entry in report_list:
                                if int(finalitems) in entry['Service_ID']:
                                    for key in finalre.keys():
                                                if key == 'end_time':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'estimated_time_with_add':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'hold':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'break':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'time_diff_work':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'call':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'meeting':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'in_progress':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'completed':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'idealname':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'no_of_items':
                                                    try:
                                                
                                            
                                                        finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                        
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'chargable':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'non-chargable':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'total-time':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                else:
                                                    finalre[key] = entry[key].union(finalre[key])

                        result = {
                            'estimated_time_with_add' : set(),
                            'work_started_date' : set(),
                            'work_ended_date' : set(),
                            'number_of_days_taken' : set(),
                            'number_of_days_delayed' : set(),
                            'actual_date_of_delivery' : set(),
                            'estimated_date_of_delivery' : set(),
                            'number_of_entity' : set(),
                            'estimated_time_minus_chargable_time' : set(),
                            'date': set(),
                            'user': set(),
                            'Service_ID': set(),
                            'created_at' : set(),
                            'Completed_date' : set(),
                            'scope': set(),
                            'subscopes': set(),
                            'entity': set(),
                            # 'no_of_entity' : set(),
                            'status': set(),
                            'type_of_activity': set(),
                            'Nature_of_Work': set(),
                            'gst_tan': set(),
                            'estimated_d_o_d': set(),
                            'estimated_time': set(),
                            'member_name': set(),
                            'end_time': set(),
                            'hold': set(),
                            'break': set(),
                            'time_diff_work': set(),
                            'call': set(),
                            'meeting': set(),
                            'in_progress': set(),
                            'completed': set(),
                            'third_report_data' : set(),
                            'fourth_report' :  set(),
                            'fourth_report2' : set(),
                            'fifth_report' : set(),
                            'no_of_items' : set(),
                            'chargable' : set(),
                            'non-chargable' : set(),
                            'total-time' : set(),
                            'idealname' : set()
                        }
                        

                        for key in finalre:
                            if isinstance(finalre[key], set):

                                    cpof = finalre[key]
                                    result[key]= cpof
                                
                                    finalre[key] = set()

                            elif isinstance(finalre[key], int):
                                result[key] = finalre[key]
                                #   
                            else:
                            
                                result[key].add(convert_to_duration(finalre[key]))
                                finalre[key] = pendulum.duration()
                        

                        
        #--------------------------- last calculation


                        

                        # Define the set of date strings
                        date_strings = result['date']
                    
                        # Convert the date strings to datetime objects
                        dateslast = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                        # Find the maximum date
                        max_date = max(dateslast)

                        min_date = min(dateslast)




                        # Define the set of date strings
                        date_strings_date = result['estimated_d_o_d']

                        # Convert the date strings to datetime objects
                        dateslast_date = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings_date}

                        # Find the maximum date
                        max_date_in_dates = max(dateslast_date)

                        


        #--------------------------- last calculation


                        dateesti =  max_date_in_dates.strftime("%Y-%m-%d")

                        # Define the set of date strings
                        date_strings = result['date']

                        # Convert dateesti to a datetime object
                        dateesti_dt = datetime.strptime(dateesti, "%Y-%m-%d").date()

                        # Convert the set of date strings to a set of datetime objects
                        dates = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                        # Find and count the dates that are greater than dateesti_dt
                        greater_dates = {date for date in dates if date > dateesti_dt}
                        count_greater_dates = len(greater_dates)

                    

        #-----------------------------getting estimate time
                        

                        estichar = result['estimated_time_with_add'].pop()
                        hourses, minuteses, secondses = map(int, estichar.split(':'))

                        # Create a pendulum Duration object
                        durationes = pendulum.duration(hours=hourses, minutes=minuteses, seconds=secondses)

        #----------------------------------------- chargable time


                        nchar = result['chargable'].pop()

                        hours, minutes, seconds = map(int, nchar.split(':'))

                        # Create a pendulum Duration object
                        duration = pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
                        # 

        #------------------------ late of date estimated
                        result['chargable'] = nchar
                        result['estimated_time_with_add'] = estichar
                        result['work_started_date'] =  min_date
                        result['work_ended_date'] = max_date
                        result['number_of_days_taken'] = len(result['date'])
                        result['number_of_days_delayed'] = count_greater_dates
                        result['actual_date_of_delivery'] = max_date_in_dates 
                        result['estimated_date_of_delivery'] = max_date_in_dates
                        result['number_of_entity'] = len(result['entity'])
                        result['estimated_time_minus_chargable_time'] = convert_to_duration(durationes-duration)
                        print(result,'ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww')

        #------------------------------ code end
                        result_data.append(result)
                        result = {}
                        # 
                        # 
                        # 
                    # CODE FOR COMBINING TOTAL-TIME STARTS HERE
                    newObj1 = {}
                   
                    
                    for item in result_data: 
                        #

                        # 

                        # 

                        # 
                        tempGroup = ''
                        
                        for scope in item['scope']:
                            tempGroup+=scope

                        for subscopes in item['subscopes']:
                            tempGroup+=subscopes

                        key_to_check = tempGroup

                        if key_to_check in newObj1:
                            if isinstance(item['user'], set):   
                                newObj1[tempGroup]['user'].update(item['user'])  # Update with a set of users
                            else:
                                newObj1[tempGroup]['user'].add(item['user'])  # Add a single user

                            oldETWA = newObj1[tempGroup]['estimated_time_with_add']
                            currentETWA = item['estimated_time_with_add']

                            oldendtime = newObj1[tempGroup]['end_time']
                            currentendtime = item['end_time']

                            oldhold = newObj1[tempGroup]['hold']
                            currenthold = item['hold']

                            oldbreak = newObj1[tempGroup]['break']
                            currentbreak = item['break']

                            oldTDW = newObj1[tempGroup]['time_diff_work']
                            currentTDW = item['time_diff_work']

                            oldcall = newObj1[tempGroup]['call']
                            currentcall = item['call']

                            oldmeeting = newObj1[tempGroup]['meeting']
                            currentmeeting = item['meeting']

                            oldInProgress = newObj1[tempGroup]['in_progress']
                            currentInProgress = item['in_progress']

                            oldcompleted = newObj1[tempGroup]['completed']
                            currentcompleted = item['completed']

                            oldchargable = newObj1[tempGroup]['chargable']
                            curentchargable = item['chargable']
                            
                            oldnonchargable = newObj1[tempGroup]['non-chargable']
                            curentnonchargable = item['non-chargable']

                            oldTime = newObj1[tempGroup]['total-time']
                            curentTime = item['total-time']


        #--------------------------------------------------------------------------------------
        #--------------------------Total-estimated_time_with_add-------------------------------
                            ETWAToAdd = {
                                'oldETWA': oldETWA,
                                'currentETWA' : currentETWA
                            }
                            
                            

                            total_ETWA = timedelta()

                            for times in ETWAToAdd:
                                time_value = ETWAToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_ETWA += time_str_to_timedelta(time_value)

                            total_ETWA_str1 = str(total_ETWA)

                            newObj1[tempGroup]['estimated_time_with_add'] = total_ETWA_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-end_time---------------------------------------------------
                            endtimeToAdd = {
                                'oldendtime': oldendtime,
                                'currentendtime' : currentendtime
                            }

                            
                            

                            total_endtime = timedelta()

                            for times in endtimeToAdd:
                                time_value = endtimeToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_endtime += time_str_to_timedelta(time_value)

                            total_endtime_str1 = str(total_endtime)

                            newObj1[tempGroup]['end_time'] = total_endtime_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-hold---------------------------------------------------
                            holdToAdd = {
                                'oldhold': oldhold,
                                'currenthold' : currenthold
                            }

                            
                            

                            total_hold = timedelta()

                            for times in holdToAdd:
                                time_value = holdToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_hold += time_str_to_timedelta(time_value)

                            total_hold_str1 = str(total_hold)

                            newObj1[tempGroup]['hold'] = total_hold_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-break------------------------------------------------------

                            breakToAdd = {
                                'oldbreak': oldbreak,
                                
                                'currentbreak' : currentbreak
                            }

                            
                            

                            total_break = timedelta()

                            for times in breakToAdd:
                                time_value = breakToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_break += time_str_to_timedelta(time_value)

                            total_break_str1 = str(total_break)

                            newObj1[tempGroup]['break'] = total_break_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-time_diff_work------------------------------------------------------

                            TDWToAdd = {
                                'oldTDW': oldTDW,
                                'currentTDW' : currentTDW
                            }

                            
                            

                            total_TDW = timedelta()

                            for times in TDWToAdd:
                                time_value = TDWToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_TDW += time_str_to_timedelta(time_value)

                            total_TDW_str1 = str(total_TDW)

                            newObj1[tempGroup]['time_diff_work'] = total_TDW_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-call------------------------------------------------------

                            callToAdd = {
                                'oldcall': oldcall,
                                'currentcall' : currentcall
                            }

                            
                            

                            total_call = timedelta()

                            for times in callToAdd:
                                time_value = callToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_call += time_str_to_timedelta(time_value)

                            total_call_str1 = str(total_call)

                            newObj1[tempGroup]['call'] = total_call_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-meeting------------------------------------------------------
                            meetingToAdd = {
                                'oldmeeting': oldmeeting,
                                'currentmeeting' : currentmeeting
                            }

                            
                            

                            total_meeting = timedelta()

                            for times in meetingToAdd:
                                time_value = meetingToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_meeting += time_str_to_timedelta(time_value)

                            total_meeting_str1 = str(total_meeting)

                            newObj1[tempGroup]['meeting'] =  total_meeting_str1
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-in_progress------------------------------------------------------

                            Inprogresstoadd = {
                                'oldInProgress': oldInProgress,
                                'currentInProgress' : currentInProgress
                            }

                            
                            

                            total_Inprogresstime = timedelta()

                            for times in Inprogresstoadd:
                                time_value = Inprogresstoadd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_Inprogresstime += time_str_to_timedelta(time_value)

                            total_time_str1 = str(total_Inprogresstime)

                            newObj1[tempGroup]['in_progress'] = total_time_str1 
                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-completed------------------------------------------------------
                            completedToAdd = {
                                'oldcompleted': oldcompleted,
                                'currentcompleted' : currentcompleted

                            }

                            total_completed = timedelta()

                            for times in completedToAdd:
                                time_value = completedToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time1 in time_value:
                                        time_value = ""
                                        time_value += time1
                                else:
                                    time_values = time_value
                                
                                total_completed += time_str_to_timedelta(time_value)

                            total_completed_str1 = str(total_completed)

                            newObj1[tempGroup]['completed'] = total_completed_str1 

                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-chargable------------------------------------------------------
                            # oldchargable = newObj1[tempGroup]['chargable']
                            # curentchargable = item['chargable']

                            chargableToAdd = {
                                'oldchargable': oldchargable,
                                'curentchargable' : curentchargable

                            }

                            total_chargable = timedelta()

                            for times in chargableToAdd:
                                time_value = chargableToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time1 in time_value:
                                        time_value = ""
                                        time_value += time1
                                else:
                                    time_values = time_value
                                
                                total_chargable += time_str_to_timedelta(time_value)

                            total_chargable_str1 = str(total_chargable)

                            newObj1[tempGroup]['chargable'] = total_chargable_str1 

                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-non-chargable------------------------------------------------------

                            # oldnonchargable = newObj1[tempGroup]['non-chargable']
                            # curentnonchargable = item['non-chargable']

                            nonchargableToAdd = {
                                'oldnonchargable': oldnonchargable,
                                'curentnonchargable' : curentnonchargable

                            }

                            total_nonchargable = timedelta()

                            for times in nonchargableToAdd:
                                time_value = nonchargableToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time1 in time_value:
                                        time_value = ""
                                        time_value += time1
                                else:
                                    time_values = time_value
                                
                                total_nonchargable += time_str_to_timedelta(time_value)

                            total_nonchargable_str1 = str(total_nonchargable)

                            newObj1[tempGroup]['non-chargable'] = total_nonchargable_str1 

                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-total_time------------------------------------------------------

                            timesToAdd = {
                                'oldTime': oldTime,
                                'curentTime': curentTime
                            }
                            
                            
                            # Initialize a timedelta object to store the total time
                            total_time = timedelta()

                            # Iterate through the keys to add the time
                            for times in timesToAdd:                        
                                #time_value = next(iter(timesToAdd[times]))  # Extract the single item from the set                        
                                time_value = timesToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_values += time
                                else:
                                    time_values = time_value
                                
                                total_time += time_str_to_timedelta(time_values)

                            # Convert total_time back to a string in HH:MM:SS format
                            total_time_str = str(total_time)  

                            # newObj[tempGroup] = item     #-----(THIS LINE UPDATE THE RECENT RECORD TO THE RESPONSE)

                            newObj1[tempGroup]['total-time'] = total_time_str                    
                        else:
                            if not isinstance(item['user'], set):
                                    item['user'] = {item['user']}  # Convert the user to a set
                                    newObj1[tempGroup] = item  
                            newObj1[tempGroup] = item               
                        
                    combinedArr = []

                    for key, value in newObj1.items():
                        combinedArr.append(value)

                    result_data = combinedArr
                    # CODE FOR COMBINING TOTAL-TIME ENDS HERE
                    
                    
                    


                    
                    


                    return result_data
        
    elif reportoptions == "natureofwork_membername":

                    finalre = {
                        'estimated_time_with_add' : pendulum.duration(),
                        'date': set(),
                        'user': set(),
                        'Service_ID': set(),
                        'scope': set(),
                        'created_at' : set(),
                        'Completed_date' : set(),
                        'subscopes': set(),
                        'entity': set(),
                        # 'no_of_entity' : set(),
                        'status': set(),
                        'type_of_activity': set(),
                        'Nature_of_Work': set(),
                        'gst_tan': set(),
                        'estimated_d_o_d': set(),
                        'estimated_time': set(),
                        'member_name': set(),
                        'end_time': pendulum.duration(),
                        'hold': pendulum.duration(),
                        'break': pendulum.duration(),
                        'time_diff_work': pendulum.duration(),
                        'call': pendulum.duration(),
                        'meeting': pendulum.duration(),
                        'in_progress': pendulum.duration(),
                        'completed': pendulum.duration(),
                        'third_report_data' : set(),
                        'fourth_report' :  set(),
                        'fourth_report2' : set(),
                        'fifth_report' : set(),
                        'no_of_items' : set(),
                        'chargable' : set(),
                        'non-chargable' : set(),
                        'total-time' : set(),
                        'idealname' : pendulum.duration()
                    }

                    date_time_formate_string = '%Y-%m-%d %H:%M:%S'
                    list_data = []
                    result_data = []
                    


                    d1 = picked_date
                    d2 = to_date

                    # Convert strings to datetime objects
                    start_date = datetime.strptime(d1, '%Y-%m-%d')
                    end_date = datetime.strptime(d2, '%Y-%m-%d')

                    # Generate all dates in between and store as strings
                    dates_list = []
                    current_date = start_date

                    while current_date <= end_date:
                        
                        dates_list.append(current_date.strftime('%Y-%m-%d'))
                        current_date += timedelta(days=1)
                        

                #     # dates_list contains all dates as strings
                    # 
                    for item in dates_list:
                        reportoptions="twenty"
                        list_data.append(totaltime.user_wise_report(db,item,reportoptions))

                        
                    list_data = [item for item in list_data if item]

                    common =  set()
                    # 
                    # 
                    for report_list in list_data:
                        for entry in report_list:
                                my_set = {str(x) for x in entry['Service_ID']} 
                                
                                common.add(my_set.pop())

                                
                    for finalitems in common:
                        for report_list in list_data:
                            for entry in report_list:
                                if int(finalitems) in entry['Service_ID']:
                                    for key in finalre.keys():
                                                if key == 'end_time':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'estimated_time_with_add':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'hold':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'break':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'time_diff_work':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'call':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'meeting':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'in_progress':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'completed':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'idealname':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'no_of_items':
                                                
                                                    try:
                                                        
                                                    
                                                        finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                        
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'chargable':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'non-chargable':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                elif key == 'total-time':
                                                    try:

                                                        finalre[key] = finalre[key]+entry[key]
                                                    except:
                                                        finalre[key] = entry[key]
                                                else:
                                                    finalre[key] = entry[key].union(finalre[key])

                        result = {
                            'estimated_time_with_add' : set(),
                            'work_started_date' : set(),
                            'work_ended_date' : set(),
                            'number_of_days_taken' : set(),
                            'number_of_days_delayed' : set(),
                            'actual_date_of_delivery' : set(),
                            'estimated_date_of_delivery' : set(),
                            'number_of_entity' : set(),
                            'estimated_time_minus_chargable_time' : set(),
                            'date': set(),
                            'user': set(),
                            'Service_ID': set(),
                            'created_at' : set(),
                            'Completed_date' : set(),
                            'scope': set(),
                            'subscopes': set(),
                            'entity': set(),
                            # 'no_of_entity' : set(),
                            'status': set(),
                            'type_of_activity': set(),
                            'Nature_of_Work': set(),
                            'gst_tan': set(),
                            'estimated_d_o_d': set(),
                            'estimated_time': set(),
                            'member_name': set(),
                            'end_time': set(),
                            'hold': set(),
                            'break': set(),
                            'time_diff_work': set(),
                            'call': set(),
                            'meeting': set(),
                            'in_progress': set(),
                            'completed': set(),
                            'third_report_data' : set(),
                            'fourth_report' :  set(),
                            'fourth_report2' : set(),
                            'fifth_report' : set(),
                            'no_of_items' : set(),
                            'chargable' : set(),
                            'non-chargable' : set(),
                            'total-time' : set(),
                            'idealname' : set()
                        }
                        for key in finalre:
                            if isinstance(finalre[key], set):

                                    cpof = finalre[key]
                                    result[key]= cpof
                                
                                    finalre[key] = set()

                            elif isinstance(finalre[key], int):
                                result[key] = finalre[key]
                                #   
                            else:
                            
                                result[key].add(convert_to_duration(finalre[key]))
                                finalre[key] = pendulum.duration()
                        


        #--------------------------- last calculation


                        

                        # Define the set of date strings
                        date_strings = result['date']
                    
                        # Convert the date strings to datetime objects
                        dateslast = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                        # Find the maximum date
                        max_date = max(dateslast)

                        min_date = min(dateslast)




                        # Define the set of date strings
                        date_strings_date = result['estimated_d_o_d']

                        # Convert the date strings to datetime objects
                        dateslast_date = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings_date}

                        # Find the maximum date
                        max_date_in_dates = max(dateslast_date)

                        


        #--------------------------- last calculation


                        dateesti =  max_date_in_dates.strftime("%Y-%m-%d")

                        # Define the set of date strings
                        date_strings = result['date']

                        # Convert dateesti to a datetime object
                        dateesti_dt = datetime.strptime(dateesti, "%Y-%m-%d").date()

                        # Convert the set of date strings to a set of datetime objects
                        dates = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                        # Find and count the dates that are greater than dateesti_dt
                        greater_dates = {date for date in dates if date > dateesti_dt}
                        count_greater_dates = len(greater_dates)

                    

        #-----------------------------getting estimate time
                        

                        estichar = result['estimated_time_with_add'].pop()
                        hourses, minuteses, secondses = map(int, estichar.split(':'))

                        # Create a pendulum Duration object
                        durationes = pendulum.duration(hours=hourses, minutes=minuteses, seconds=secondses)

        #----------------------------------------- chargable time


                        nchar = result['chargable'].pop()

                        hours, minutes, seconds = map(int, nchar.split(':'))

                        # Create a pendulum Duration object
                        duration = pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
                        # 
        #------------------------ late of date estimated
                        result['chargable'] = nchar
                        result['estimated_time_with_add'] = estichar
                        result['work_started_date'] =  min_date
                        result['work_ended_date'] = max_date
                        result['number_of_days_taken'] = len(result['date'])
                        result['number_of_days_delayed'] = count_greater_dates
                        result['actual_date_of_delivery'] = max_date_in_dates 
                        result['estimated_date_of_delivery'] = max_date_in_dates
                        result['number_of_entity'] = len(result['entity'])
                        result['estimated_time_minus_chargable_time'] = convert_to_duration(durationes-duration)

        #------------------------------ code end
                        result_data.append(result)
                        result = {}
                        # 
                        # 
                        # 
                    # CODE FOR COMBINING TOTAL-TIME STARTS HERE
                    newObj1 = {}
                    
                    for item in result_data: 
                        #

                        # 

                        # 

                        # 
                        tempGroup = ''
                        
                        for Nature_of_Work in item['Nature_of_Work']:
                            tempGroup+=Nature_of_Work

                        for member_name in item['member_name']:
                            tempGroup+=member_name

                        key_to_check = tempGroup

                    
                        if key_to_check in newObj1:
                            if isinstance(item['user'], set):   
                                newObj1[tempGroup]['user'].update(item['user'])  # Update with a set of users
                            else:
                                newObj1[tempGroup]['user'].add(item['user'])  # Add a single user

                            oldETWA = newObj1[tempGroup]['estimated_time_with_add']
                            currentETWA = item['estimated_time_with_add']

                            oldendtime = newObj1[tempGroup]['end_time']
                            currentendtime = item['end_time']

                            oldhold = newObj1[tempGroup]['hold']
                            currenthold = item['hold']

                            oldbreak = newObj1[tempGroup]['break']
                            currentbreak = item['break']

                            oldTDW = newObj1[tempGroup]['time_diff_work']
                            currentTDW = item['time_diff_work']

                            oldcall = newObj1[tempGroup]['call']
                            currentcall = item['call']

                            oldmeeting = newObj1[tempGroup]['meeting']
                            currentmeeting = item['meeting']

                            oldInProgress = newObj1[tempGroup]['in_progress']
                            currentInProgress = item['in_progress']

                            oldcompleted = newObj1[tempGroup]['completed']
                            currentcompleted = item['completed']

                            oldTime = newObj1[tempGroup]['total-time']
                            curentTime = item['total-time']
        #--------------------------------------------------------------------------------------
        #--------------------------Total-estimated_time_with_add-------------------------------
                            ETWAToAdd = {
                                'oldETWA': oldETWA,
                                'currentETWA' : currentETWA
                            }
                            
                            

                            total_ETWA = timedelta()

                            for times in ETWAToAdd:
                                time_value = ETWAToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_ETWA += time_str_to_timedelta(time_value)

                            total_ETWA_str1 = str(total_ETWA)

                            newObj1[tempGroup]['estimated_time_with_add'] = total_ETWA_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-end_time---------------------------------------------------
                            endtimeToAdd = {
                                'oldendtime': oldendtime,
                                'currentendtime' : currentendtime
                            }

                            
                            

                            total_endtime = timedelta()

                            for times in endtimeToAdd:
                                time_value = endtimeToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_endtime += time_str_to_timedelta(time_value)

                            total_endtime_str1 = str(total_endtime)

                            newObj1[tempGroup]['end_time'] = total_endtime_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-hold---------------------------------------------------
                            holdToAdd = {
                                'oldhold': oldhold,
                                'currenthold' : currenthold
                            }

                            
                            

                            total_hold = timedelta()

                            for times in holdToAdd:
                                time_value = holdToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_hold += time_str_to_timedelta(time_value)

                            total_hold_str1 = str(total_hold)

                            newObj1[tempGroup]['hold'] = total_hold_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-break------------------------------------------------------

                            breakToAdd = {
                                'oldbreak': oldbreak,
                                
                                'currentbreak' : currentbreak
                            }

                            
                            

                            total_break = timedelta()

                            for times in breakToAdd:
                                time_value = breakToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_break += time_str_to_timedelta(time_value)

                            total_break_str1 = str(total_break)

                            newObj1[tempGroup]['break'] = total_break_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-time_diff_work------------------------------------------------------

                            TDWToAdd = {
                                'oldTDW': oldTDW,
                                'currentTDW' : currentTDW
                            }

                            
                            

                            total_TDW = timedelta()

                            for times in TDWToAdd:
                                time_value = TDWToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_TDW += time_str_to_timedelta(time_value)

                            total_TDW_str1 = str(total_TDW)

                            newObj1[tempGroup]['time_diff_work'] = total_TDW_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-call------------------------------------------------------

                            callToAdd = {
                                'oldcall': oldcall,
                                'currentcall' : currentcall
                            }

                            
                            

                            total_call = timedelta()

                            for times in callToAdd:
                                time_value = callToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_call += time_str_to_timedelta(time_value)

                            total_call_str1 = str(total_call)

                            newObj1[tempGroup]['call'] = total_call_str1 
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-meeting------------------------------------------------------
                            meetingToAdd = {
                                'oldmeeting': oldmeeting,
                                'currentmeeting' : currentmeeting
                            }

                            
                            

                            total_meeting = timedelta()

                            for times in meetingToAdd:
                                time_value = meetingToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_meeting += time_str_to_timedelta(time_value)

                            total_meeting_str1 = str(total_meeting)

                            newObj1[tempGroup]['meeting'] =  total_meeting_str1
                            #------------------------------------------------------------------------------------------
                            #-------------------------Total-in_progress------------------------------------------------------

                            # Inprogresstoadd = {
                            #     'oldInProgress': oldInProgress,
                            #     'currentInProgress' : currentInProgress
                            # }

                            # 
                            # 

                            # total_Inprogresstime = timedelta()

                            # for times in Inprogresstoadd:
                            #     time_value = Inprogresstoadd[times]
                            #     time_values = ''

                            #     if isinstance(time_value, set):
                            #         for time in time_value:
                            #             time_value = ""
                            #             time_value += time
                            #     else:
                            #         time_values = time_value
                                
                            #     total_Inprogresstime += time_str_to_timedelta(time_value)

                            # total_time_str1 = str(total_Inprogresstime)

                            # newObj1[tempGroup]['in_progress'] = total_time_str1 

                            Inprogresstoadd = {
                                'oldInProgress': oldInProgress,
                                'currentInProgress' : currentInProgress
                            }

                            
                            

                            total_Inprogresstime = timedelta()

                            for times in Inprogresstoadd:
                                time_value = Inprogresstoadd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_value = ""
                                        time_value += time
                                else:
                                    time_values = time_value
                                
                                total_Inprogresstime += time_str_to_timedelta(time_value)

                            total_time_str1 = str(total_Inprogresstime)

                            newObj1[tempGroup]['in_progress'] = total_time_str1 
                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-completed------------------------------------------------------
                            completedToAdd = {
                                'oldcompleted': oldcompleted,
                                'currentcompleted' : currentcompleted

                            }

                            
                            

                            total_completed = timedelta()

                            for times in completedToAdd:
                                time_value = completedToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time1 in time_value:
                                        time_value = ""
                                        time_value += time1
                                else:
                                    time_values = time_value
                                
                                total_completed += time_str_to_timedelta(time_value)

                            total_completed_str1 = str(total_completed)

                            newObj1[tempGroup]['estimated_time_with_add'] = total_completed_str1 
                            #---------------------------------------------------------------------------------------
                            #-------------------------Total-total_time------------------------------------------------------

                            timesToAdd = {
                                'oldTime': oldTime,
                                'curentTime': curentTime
                            }
                            
                            
                            # Initialize a timedelta object to store the total time
                            total_time = timedelta()

                            # Iterate through the keys to add the time
                            for times in timesToAdd:                        
                                #time_value = next(iter(timesToAdd[times]))  # Extract the single item from the set                        
                                time_value = timesToAdd[times]
                                time_values = ''

                                if isinstance(time_value, set):
                                    for time in time_value:
                                        time_values += time
                                else:
                                    time_values = time_value
                                
                                total_time += time_str_to_timedelta(time_values)

                            # Convert total_time back to a string in HH:MM:SS format
                            total_time_str = str(total_time)  

                            # newObj[tempGroup] = item     #-----(THIS LINE UPDATE THE RECENT RECORD TO THE RESPONSE)

                            newObj1[tempGroup]['total-time'] = total_time_str                    
                        else:
                            if not isinstance(item['user'], set):
                                    item['user'] = {item['user']}  # Convert the user to a set
                                    newObj1[tempGroup] = item  
                            newObj1[tempGroup] = item               
                        
                    combinedArr = []

                    for key, value in newObj1.items():
                        combinedArr.append(value)

                    result_data = combinedArr
                    # CODE FOR COMBINING TOTAL-TIME ENDS HERE

                    
                    

                    
                    


                    return result_data


    elif reportoptions == "scope_subscope_natureofwork":

            finalre = {
                'estimated_time_with_add' : pendulum.duration(),
                'date': set(),
                'user': set(),
                'Service_ID': set(),
                'scope': set(),
                'created_at' : set(),
                'Completed_date' : set(),
                'subscopes': set(),
                'entity': set(),
                # 'no_of_entity' : set(),
                'status': set(),
                'type_of_activity': set(),
                'Nature_of_Work': set(),
                'gst_tan': set(),
                'estimated_d_o_d': set(),
                'estimated_time': set(),
                'member_name': set(),
                'end_time': pendulum.duration(),
                'hold': pendulum.duration(),
                'break': pendulum.duration(),
                'time_diff_work': pendulum.duration(),
                'call': pendulum.duration(),
                'meeting': pendulum.duration(),
                'in_progress': pendulum.duration(),
                'completed': pendulum.duration(),
                'third_report_data' : set(),
                'fourth_report' :  set(),
                'fourth_report2' : set(),
                'fifth_report' : set(),
                'no_of_items' : set(),
                'chargable' : set(),
                'non-chargable' : set(),
                'total-time' : set(),
                'idealname' : pendulum.duration()
            }

            date_time_formate_string = '%Y-%m-%d %H:%M:%S'
            list_data = []
            result_data = []
            


            d1 = picked_date
            d2 = to_date

            # Convert strings to datetime objects
            start_date = datetime.strptime(d1, '%Y-%m-%d')
            end_date = datetime.strptime(d2, '%Y-%m-%d')

            # Generate all dates in between and store as strings
            dates_list = []
            current_date = start_date

            while current_date <= end_date:
                
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
                

            # dates_list contains all dates as strings
            # 
            for item in dates_list:
                # 
                
                
                
                
                
                
                reportoptions="twenty"
                list_data.append(totaltime.user_wise_report(db,item,reportoptions))

                            
            list_data = [item for item in list_data if item]

            common =  set()
            
            
            for report_list in list_data:
                for entry in report_list:
                        my_set = {str(x) for x in entry['Service_ID']} 
                        
                        common.add(my_set.pop())

                                
            for finalitems in common:
                for report_list in list_data:
                    for entry in report_list:
                        if int(finalitems) in entry['Service_ID']:
                            for key in finalre.keys():
                                        if key == 'end_time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'estimated_time_with_add':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'hold':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'break':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'time_diff_work':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'call':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'meeting':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'in_progress':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'completed':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'idealname':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'no_of_items':
                                            try:
                                                
                                                if len(finalre[key]) == 0:
                                                    finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                else:
                                                    finalre[key] = entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'non-chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'total-time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        else:
                                            finalre[key] = entry[key].union(finalre[key])

                result = {
                    'estimated_time_with_add' : set(),
                    'work_started_date' : set(),
                    'work_ended_date' : set(),
                    'number_of_days_taken' : set(),
                    'number_of_days_delayed' : set(),
                    'actual_date_of_delivery' : set(),
                    'estimated_date_of_delivery' : set(),
                    'number_of_entity' : set(),
                    'estimated_time_minus_chargable_time' : set(),
                    'date': set(),
                    'user': set(),
                    'Service_ID': set(),
                    'created_at' : set(),
                    'Completed_date' : set(),
                    'scope': set(),
                    'subscopes': set(),
                    'entity': set(),
                    # 'no_of_entity' : set(),
                    'status': set(),
                    'type_of_activity': set(),
                    'Nature_of_Work': set(),
                    'gst_tan': set(),
                    'estimated_d_o_d': set(),
                    'estimated_time': set(),
                    'member_name': set(),
                    'end_time': set(),
                    'hold': set(),
                    'break': set(),
                    'time_diff_work': set(),
                    'call': set(),
                    'meeting': set(),
                    'in_progress': set(),
                    'completed': set(),
                    'third_report_data' : set(),
                    'fourth_report' :  set(),
                    'fourth_report2' : set(),
                    'fifth_report' : set(),
                    'no_of_items' : set(),
                    'chargable' : set(),
                    'non-chargable' : set(),
                    'total-time' : set(),
                    'idealname' : set()
                }
                for key in finalre:
                    if isinstance(finalre[key], set):

                            cpof = finalre[key]
                            result[key]= cpof
                        
                            finalre[key] = set()

                    elif isinstance(finalre[key], int):
                        result[key] = finalre[key]
                        #   
                    else:
                    
                        result[key].add(convert_to_duration(finalre[key]))
                        finalre[key] = pendulum.duration()
                


        #--------------------------- last calculation


                        

                # Define the set of date strings
                date_strings = result['date']
            
                # Convert the date strings to datetime objects
                dateslast = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find the maximum date
                max_date = max(dateslast)

                min_date = min(dateslast)




                # Define the set of date strings
                date_strings_date = result['estimated_d_o_d']

                # Convert the date strings to datetime objects
                dateslast_date = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings_date}

                # Find the maximum date
                max_date_in_dates = max(dateslast_date)

                        


        #--------------------------- last calculation


                dateesti =  max_date_in_dates.strftime("%Y-%m-%d")

                # Define the set of date strings
                date_strings = result['date']

                # Convert dateesti to a datetime object
                dateesti_dt = datetime.strptime(dateesti, "%Y-%m-%d").date()

                # Convert the set of date strings to a set of datetime objects
                dates = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find and count the dates that are greater than dateesti_dt
                greater_dates = {date for date in dates if date > dateesti_dt}
                count_greater_dates = len(greater_dates)

                    

        #-----------------------------getting estimate time
                        

                estichar = result['estimated_time_with_add'].pop()
                hourses, minuteses, secondses = map(int, estichar.split(':'))

                # Create a pendulum Duration object
                durationes = pendulum.duration(hours=hourses, minutes=minuteses, seconds=secondses)

        #----------------------------------------- chargable time


                nchar = result['chargable'].pop()

                hours, minutes, seconds = map(int, nchar.split(':'))

                # Create a pendulum Duration object
                duration = pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
                # 
#------------------------ late of date estimated
                result['chargable'] = nchar
                result['estimated_time_with_add'] = estichar
                result['work_started_date'] =  min_date
                result['work_ended_date'] = max_date
                result['number_of_days_taken'] = len(result['date'])
                result['number_of_days_delayed'] = count_greater_dates
                result['actual_date_of_delivery'] = max_date_in_dates 
                result['estimated_date_of_delivery'] = max_date_in_dates
                result['number_of_entity'] = len(result['entity'])
                result['estimated_time_minus_chargable_time'] = convert_to_duration(durationes-duration)

        #------------------------------ code end
                result_data.append(result)
                result = {}
                # 
                # 
                # 
            # CODE FOR COMBINING TOTAL-TIME STARTS HERE
            newObj1 = {}

            # 
            # 
            
            for item in result_data: 
                #

                # 

                # 

                # 
                tempGroup = ''
                
                for scope in item['scope']:
                    tempGroup+=scope

                for subscopes in item['subscopes']:
                    tempGroup+=subscopes

                for Nature_of_Work in item['Nature_of_Work']:
                    tempGroup+=Nature_of_Work

                key_to_check = tempGroup

                if key_to_check in newObj1:
                    if isinstance(item['user'], set):   
                        newObj1[tempGroup]['user'].update(item['user'])  # Update with a set of users
                    else:
                        newObj1[tempGroup]['user'].add(item['user'])  # Add a single user

                    oldETWA = newObj1[tempGroup]['estimated_time_with_add']
                    currentETWA = item['estimated_time_with_add']

                    oldendtime = newObj1[tempGroup]['end_time']
                    currentendtime = item['end_time']

                    oldhold = newObj1[tempGroup]['hold']
                    currenthold = item['hold']

                    oldbreak = newObj1[tempGroup]['break']
                    currentbreak = item['break']

                    oldTDW = newObj1[tempGroup]['time_diff_work']
                    currentTDW = item['time_diff_work']

                    oldcall = newObj1[tempGroup]['call']
                    currentcall = item['call']

                    oldmeeting = newObj1[tempGroup]['meeting']
                    currentmeeting = item['meeting']

                    oldInProgress = newObj1[tempGroup]['in_progress']
                    currentInProgress = item['in_progress']

                    oldcompleted = newObj1[tempGroup]['completed']
                    currentcompleted = item['completed']

                    oldnoofitems = newObj1[tempGroup]['no_of_items']
                    currentnoofitems = item['no_of_items']

                    oldTime = newObj1[tempGroup]['total-time']
                    curentTime = item['total-time']
                    #--------------------------------------------------------------------------------------
                    #--------------------------Total-estimated_time_with_add-------------------------------
                    ETWAToAdd = {
                        'oldETWA': oldETWA,
                        'currentETWA' : currentETWA
                    }
                    
                    

                    total_ETWA = timedelta()

                    for times in ETWAToAdd:
                        time_value = ETWAToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value = ""
                                # time_value += time
                        else:
                            time_values = time_value
                        
                    total_ETWA += time_str_to_timedelta(time_values)

                    total_ETWA_str1 = str(total_ETWA)

                    newObj1[tempGroup]['estimated_time_with_add'] = total_ETWA_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-end_time---------------------------------------------------
                    endtimeToAdd = {
                        'oldendtime': oldendtime,
                        'currentendtime' : currentendtime
                    }

                    
                    

                    total_endtime = timedelta()

                    for times in endtimeToAdd:
                        time_value = endtimeToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value = ""
                                # time_value += time
                        else:
                            time_values = time_value
                        
                    total_endtime += time_str_to_timedelta(time_values)

                    total_endtime_str1 = str(total_endtime)

                    newObj1[tempGroup]['end_time'] = total_endtime_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-hold---------------------------------------------------
                    holdToAdd = {
                        'oldhold': oldhold,
                        'currenthold' : currenthold
                    }

                    
                    

                    total_hold = timedelta()

                    for times in holdToAdd:
                        time_value = holdToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value = ""
                                # time_value += time
                        else:
                            time_values = time_value
                        
                    total_hold += time_str_to_timedelta(time_values)

                    total_hold_str1 = str(total_hold)

                    newObj1[tempGroup]['hold'] = total_hold_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-break------------------------------------------------------

                    breakToAdd = {
                        'oldbreak': oldbreak,
                        
                        'currentbreak' : currentbreak
                    }

                    
                    

                    total_break = timedelta()

                    for times in breakToAdd:
                        time_value = breakToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value = ""
                                # time_value += time
                        else:
                            time_values = time_value
                        
                    total_break += time_str_to_timedelta(time_values)

                    total_break_str1 = str(total_break)

                    newObj1[tempGroup]['break'] = total_break_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-time_diff_work------------------------------------------------------

                    TDWToAdd = {
                        'oldTDW': oldTDW,
                        'currentTDW' : currentTDW
                    }

                    
                    

                    total_TDW = timedelta()

                    for times in TDWToAdd:
                        time_value = TDWToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value = ""
                                # time_value += time
                        else:
                            time_values = time_value
                        
                    total_TDW += time_str_to_timedelta(time_values)

                    total_TDW_str1 = str(total_TDW)

                    newObj1[tempGroup]['time_diff_work'] = total_TDW_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-call------------------------------------------------------

                    callToAdd = {
                        'oldcall': oldcall,
                        'currentcall' : currentcall
                    }

                    
                    

                    total_call = timedelta()

                    for times in callToAdd:
                        time_value = callToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value = ""
                                # time_value += time
                        else:
                            time_values = time_value

                        
                    total_call += time_str_to_timedelta(time_values)

                    total_call_str1 = str(total_call)

                    newObj1[tempGroup]['call'] = total_call_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-meeting------------------------------------------------------
                    meetingToAdd = {
                        'oldmeeting': oldmeeting,
                        'currentmeeting' : currentmeeting
                    }

                    
                    

                    total_meeting = timedelta()

                    for times in meetingToAdd:
                        time_value = meetingToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value = ""
                                # time_value += time
                        else:
                            time_values = time_value
                        
                    total_meeting += time_str_to_timedelta(time_values)

                    total_meeting_str1 = str(total_meeting)

                    newObj1[tempGroup]['meeting'] =  total_meeting_str1
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-in_progress------------------------------------------------------

                    Inprogresstoadd = {
                        'oldInProgress': oldInProgress,
                        'currentInProgress' : currentInProgress
                    }

                    
                    

                    total_Inprogresstime = timedelta()

                    for times in Inprogresstoadd:
                        time_value = Inprogresstoadd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value = ""
                                # time_value += time
                        else:
                            time_values = time_value
                        
                    total_Inprogresstime += time_str_to_timedelta(time_values)

                    total_time_str1 = str(total_Inprogresstime)

                    newObj1[tempGroup]['in_progress'] = total_time_str1 
                    #---------------------------------------------------------------------------------------
                    #-------------------------Total-completed------------------------------------------------------
                    completedToAdd = {
                        'oldcompleted': oldcompleted,
                        'currentcompleted' : currentcompleted

                    }

                    
                    

                    total_completed = timedelta()

                    for times in completedToAdd:
                        time_value = completedToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value = ""
                                # time_value += time1
                        else:
                            time_values = time_value
                        
                    total_completed += time_str_to_timedelta(time_values)

                    total_completed_str1 = str(total_completed)

                    newObj1[tempGroup]['completed'] = total_completed_str1 

                    #------------------------------------------------------------------------------------
                    #-------------------------Total-no_of_items------------------------------------------------------
                    noofitemsdToAdd = {
                        'oldnoofitems': oldnoofitems,
                        'currentnoofitems' : currentnoofitems
                    }
                 
                    
                    

                    total_noofitems = 0

                    for num in noofitemsdToAdd:
                        num_value = noofitemsdToAdd[num]

                        if isinstance(num_value, set):  # If the value is a set, extract the single element
                            total_noofitems += sum(num_value)
                        elif isinstance(num_value, int):  # If the value is an integer, add it directly
                            total_noofitems += num_value

                    total_noofitems_str1 = str(total_noofitems)

                    # Print the results
                    

                    #---------------------------------------------------------------------------------------
                    #-------------------------Total-total_time------------------------------------------------------

                    timesToAdd = {
                        'oldTime': oldTime,
                        'curentTime': curentTime
                    }
                    
                    
                    # Initialize a timedelta object to store the total time
                    total_time = timedelta()

                    # Iterate through the keys to add the time
                    for times in timesToAdd:                        
                        #time_value = next(iter(timesToAdd[times]))  # Extract the single item from the set                        
                        time_value = timesToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)  # Add time to the set

                                # time_value += time
                        else:
                            time_values = time_value
                        
                    total_time += time_str_to_timedelta(time_values)

                    # Convert total_time back to a string in HH:MM:SS format
                    total_time_str = str(total_time)  

                    # newObj[tempGroup] = item     #-----(THIS LINE UPDATE THE RECENT RECORD TO THE RESPONSE)

                    newObj1[tempGroup]['total-time'] = total_time_str                    
                else:
                    if not isinstance(item['user'], set):
                            item['user'] = {item['user']}  # Convert the user to a set
                            newObj1[tempGroup] = item  
                    newObj1[tempGroup] = item               
                
            combinedArr = []

            for key, value in newObj1.items():
                combinedArr.append(value)

            result_data = combinedArr
            # CODE FOR COMBINING TOTAL-TIME ENDS HERE
            
            

            
            


            return result_data
        
    elif reportoptions == "scope_subscope":
            print('dddddddddddddddddddddddddddddddddddddddddddddd')
            finalre = {
                'estimated_time_with_add' : pendulum.duration(),
                'date': set(),
                'user': set(),
                'Service_ID': set(),
                'scope': set(),
                'created_at' : set(),
                'Completed_date' : set(),
                'subscopes': set(),
                'entity': set(),
                # 'no_of_entity' : set(),
                'status': set(),
                'type_of_activity': set(),
                'Nature_of_Work': set(),
                'gst_tan': set(),
                'estimated_d_o_d': set(),
                'estimated_time': set(),
                'member_name': set(),
                'end_time': pendulum.duration(),
                'hold': pendulum.duration(),
                'break': pendulum.duration(),
                'time_diff_work': pendulum.duration(),
                'call': pendulum.duration(),
                'meeting': pendulum.duration(),
                'in_progress': pendulum.duration(),
                'completed': pendulum.duration(),
                'third_report_data' : set(),
                'fourth_report' :  set(),
                'fourth_report2' : set(),
                'fifth_report' : set(),
                'no_of_items' : set(),
                'chargable' : set(),
                'non-chargable' : set(),
                'total-time' : set(),
                'idealname' : pendulum.duration()
            }

            date_time_formate_string = '%Y-%m-%d %H:%M:%S'
            list_data = []
            result_data = []
            


            d1 = picked_date
            d2 = to_date

            # Convert strings to datetime objects
            start_date = datetime.strptime(d1, '%Y-%m-%d')
            end_date = datetime.strptime(d2, '%Y-%m-%d')

            # Generate all dates in between and store as strings
            dates_list = []
            current_date = start_date

            while current_date <= end_date:
                
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
                

        #     # dates_list contains all dates as strings
            # 
            for item in dates_list:
                reportoptions="twenty"
                list_data.append(totaltime.user_wise_report(db,item,reportoptions))

                
            list_data = [item for item in list_data if item]

            common =  set()
            # 
            # 
            for report_list in list_data:
                for entry in report_list:
                        my_set = {str(x) for x in entry['Service_ID']} 
                        
                        common.add(my_set.pop())

                                
            for finalitems in common:
                for report_list in list_data:
                    for entry in report_list:
                        if int(finalitems) in entry['Service_ID']:
                            for key in finalre.keys():
                                        if key == 'end_time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'estimated_time_with_add':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'hold':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'break':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'time_diff_work':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'call':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'meeting':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'in_progress':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'completed':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'idealname':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'no_of_items':
                                            try:
                                                
                                                if len(finalre[key]) == 0:
                                                    finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                else:
                                                    finalre[key] = entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'non-chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'total-time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        else:
                                            finalre[key] = entry[key].union(finalre[key])

                result = {
                    'estimated_time_with_add' : set(),
                    'work_started_date' : set(),
                    'work_ended_date' : set(),
                    'number_of_days_taken' : set(),
                    'number_of_days_delayed' : set(),
                    'actual_date_of_delivery' : set(),
                    'estimated_date_of_delivery' : set(),
                    'number_of_entity' : set(),
                    'estimated_time_minus_chargable_time' : set(),
                    'date': set(),
                    'user': set(),
                    'Service_ID': set(),
                    'created_at' : set(),
                    'Completed_date' : set(),
                    'scope': set(),
                    'subscopes': set(),
                    'entity': set(),
                    # 'no_of_entity' : set(),
                    'status': set(),
                    'type_of_activity': set(),
                    'Nature_of_Work': set(),
                    'gst_tan': set(),
                    'estimated_d_o_d': set(),
                    'estimated_time': set(),
                    'member_name': set(),
                    'end_time': set(),
                    'hold': set(),
                    'break': set(),
                    'time_diff_work': set(),
                    'call': set(),
                    'meeting': set(),
                    'in_progress': set(),
                    'completed': set(),
                    'third_report_data' : set(),
                    'fourth_report' :  set(),
                    'fourth_report2' : set(),
                    'fifth_report' : set(),
                    'no_of_items' : set(),
                    'chargable' : set(),
                    'non-chargable' : set(),
                    'total-time' : set(),
                    'idealname' : set()
                }
                for key in finalre:
                    if isinstance(finalre[key], set):

                            cpof = finalre[key]
                            result[key]= cpof
                        
                            finalre[key] = set()

                    elif isinstance(finalre[key], int):
                        result[key] = finalre[key]
                        #   
                    else:
                    
                        result[key].add(convert_to_duration(finalre[key]))
                        finalre[key] = pendulum.duration()
                        

                
        #--------------------------- last calculation


                        

                # Define the set of date strings
                date_strings = result['date']
            
                # Convert the date strings to datetime objects
                dateslast = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find the maximum date
                max_date = max(dateslast)

                min_date = min(dateslast)




                # Define the set of date strings
                date_strings_date = result['estimated_d_o_d']

                # Convert the date strings to datetime objects
                dateslast_date = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings_date}

                # Find the maximum date
                max_date_in_dates = max(dateslast_date)

                        


        #--------------------------- last calculation


                dateesti =  max_date_in_dates.strftime("%Y-%m-%d")

                # Define the set of date strings
                date_strings = result['date']

                # Convert dateesti to a datetime object
                dateesti_dt = datetime.strptime(dateesti, "%Y-%m-%d").date()

                # Convert the set of date strings to a set of datetime objects
                dates = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find and count the dates that are greater than dateesti_dt
                greater_dates = {date for date in dates if date > dateesti_dt}
                count_greater_dates = len(greater_dates)

                    

        #-----------------------------getting estimate time
                        

                estichar = result['estimated_time_with_add'].pop()
                hourses, minuteses, secondses = map(int, estichar.split(':'))

                # Create a pendulum Duration object
                durationes = pendulum.duration(hours=hourses, minutes=minuteses, seconds=secondses)

        #----------------------------------------- chargable time
               


                nchar = result['chargable'].pop()
                

                hours, minutes, seconds = map(int, nchar.split(':'))

                # Create a pendulum Duration object
                duration = pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
                # 
#------------------------ late of date estimated
                result['chargable'] = nchar
                result['estimated_time_with_add'] = estichar
                result['work_started_date'] =  min_date
                result['work_ended_date'] = max_date
                result['number_of_days_taken'] = len(result['date'])
                result['number_of_days_delayed'] = count_greater_dates
                result['actual_date_of_delivery'] = max_date_in_dates 
                result['estimated_date_of_delivery'] = max_date_in_dates
                result['number_of_entity'] = len(result['entity'])
                result['estimated_time_minus_chargable_time'] = convert_to_duration(durationes-duration)
          
        #------------------------------ code end
                result_data.append(result)
                result = {}
                
                
                
                # 
                # 
                # 
            # CODE FOR COMBINING TOTAL-TIME STARTS HERE
            newObj1 = {}
            
            for item in result_data: 
                #

                # 

                # 

                # 
                tempGroup = ''
                
                for scope in item['scope']:
                    tempGroup+=scope

                for subscopes in item['subscopes']:
                    tempGroup+=subscopes

                key_to_check = tempGroup

                if key_to_check in newObj1:
                    if isinstance(item['user'], set):   
                        newObj1[tempGroup]['user'].update(item['user'])  # Update with a set of users
                    else:
                        newObj1[tempGroup]['user'].add(item['user'])  # Add a single user

                    oldETWA = newObj1[tempGroup]['estimated_time_with_add']
                    currentETWA = item['estimated_time_with_add']

                    oldendtime = newObj1[tempGroup]['end_time']
                    currentendtime = item['end_time']

                    oldhold = newObj1[tempGroup]['hold']
                    currenthold = item['hold']

                    oldbreak = newObj1[tempGroup]['break']
                    currentbreak = item['break']

                    oldTDW = newObj1[tempGroup]['time_diff_work']
                    currentTDW = item['time_diff_work']

                    oldcall = newObj1[tempGroup]['call']
                    currentcall = item['call']

                    oldmeeting = newObj1[tempGroup]['meeting']
                    currentmeeting = item['meeting']

                    oldInProgress = newObj1[tempGroup]['in_progress']
                    currentInProgress = item['in_progress']

                    oldcompleted = newObj1[tempGroup]['completed']
                    currentcompleted = item['completed']

                    oldnoofitems = newObj1[tempGroup]['no_of_items']
                    currentnoofitems = item['no_of_items']

                    oldTime = newObj1[tempGroup]['total-time']
                    curentTime = item['total-time']
#--------------------------------------------------------------------------------------
#--------------------------Total-estimated_time_with_add-------------------------------
                    ETWAToAdd = {
                        'oldETWA': oldETWA,
                        'currentETWA' : currentETWA
                    }
                    
                    

                    total_ETWA = timedelta()

                    for times in ETWAToAdd:
                        time_value = ETWAToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time) 
                        else:
                            time_values = time_value
                        
                    total_ETWA += time_str_to_timedelta(time_values)

                    total_ETWA_str1 = str(total_ETWA)

                    newObj1[tempGroup]['estimated_time_with_add'] = total_ETWA_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-end_time---------------------------------------------------
                    endtimeToAdd = {
                        'oldendtime': oldendtime,
                        'currentendtime' : currentendtime
                    }

                    
                    

                    total_endtime = timedelta()

                    for times in endtimeToAdd:
                        time_value = endtimeToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_endtime += time_str_to_timedelta(time_values)

                    total_endtime_str1 = str(total_endtime)

                    newObj1[tempGroup]['end_time'] = total_endtime_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-hold---------------------------------------------------
                    holdToAdd = {
                        'oldhold': oldhold,
                        'currenthold' : currenthold
                    }

                    
                    

                    total_hold = timedelta()

                    for times in holdToAdd:
                        time_value = holdToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time) 
                        else:
                            time_values = time_value
                        
                    total_hold += time_str_to_timedelta(time_values)

                    total_hold_str1 = str(total_hold)

                    newObj1[tempGroup]['hold'] = total_hold_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-break------------------------------------------------------

                    breakToAdd = {
                        'oldbreak': oldbreak,
                        
                        'currentbreak' : currentbreak
                    }

                    
                    

                    total_break = timedelta()

                    for times in breakToAdd:
                        time_value = breakToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = ""
                                time_value += time
                        else:
                            time_values = time_value
                        
                    total_break += time_str_to_timedelta(time_values)

                    total_break_str1 = str(total_break)

                    newObj1[tempGroup]['break'] = total_break_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-time_diff_work------------------------------------------------------

                    TDWToAdd = {
                        'oldTDW': oldTDW,
                        'currentTDW' : currentTDW
                    }

                    
                    

                    total_TDW = timedelta()

                    for times in TDWToAdd:
                        time_value = TDWToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time) 
                        else:
                            time_values = time_value
                        
                    total_TDW += time_str_to_timedelta(time_values)

                    total_TDW_str1 = str(total_TDW)

                    newObj1[tempGroup]['time_diff_work'] = total_TDW_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-call------------------------------------------------------

                    callToAdd = {
                        'oldcall': oldcall,
                        'currentcall' : currentcall
                    }

                    
                    

                    total_call = timedelta()

                    for times in callToAdd:
                        time_value = callToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time) 
                        else:
                            time_values = time_value
                        
                    total_call += time_str_to_timedelta(time_values)

                    total_call_str1 = str(total_call)

                    newObj1[tempGroup]['call'] = total_call_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-meeting------------------------------------------------------
                    meetingToAdd = {
                        'oldmeeting': oldmeeting,
                        'currentmeeting' : currentmeeting
                    }

                    
                    

                    total_meeting = timedelta()

                    for times in meetingToAdd:
                        time_value = meetingToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time) 
                        else:
                            time_values = time_value
                        
                    total_meeting += time_str_to_timedelta(time_values)

                    total_meeting_str1 = str(total_meeting)

                    newObj1[tempGroup]['meeting'] =  total_meeting_str1
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-in_progress------------------------------------------------------

                    Inprogresstoadd = {
                        'oldInProgress': oldInProgress,
                        'currentInProgress' : currentInProgress
                    }

                    
                    

                    total_Inprogresstime = timedelta()

                    for times in Inprogresstoadd:
                        time_value = Inprogresstoadd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time) 
                        else:
                            time_values = time_value
                        
                    total_Inprogresstime += time_str_to_timedelta(time_values)

                    total_time_str1 = str(total_Inprogresstime)

                    newObj1[tempGroup]['in_progress'] = total_time_str1 
                    #---------------------------------------------------------------------------------------
                    #-------------------------Total-completed------------------------------------------------------
                    completedToAdd = {
                        'oldcompleted': oldcompleted,
                        'currentcompleted' : currentcompleted

                    }

                    
                    

                    total_completed = timedelta()

                    for times in completedToAdd:
                        time_value = completedToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time1 in time_value:
                                time_value = set()
                                time_value.add(time) 
                        else:
                            time_values = time_value
                        
                    total_completed += time_str_to_timedelta(time_values)

                    total_completed_str1 = str(total_completed)

                    newObj1[tempGroup]['completed'] = total_completed_str1 

                    #------------------------------------------------------------------------------------
                    #-------------------------Total-no_of_items------------------------------------------------------
                    noofitemsdToAdd = {
                        'oldnoofitems': oldnoofitems,
                        'currentnoofitems' : currentnoofitems
                    }
                    
                    

                    total_noofitems = 0

                    for num in noofitemsdToAdd:
                        num_value = noofitemsdToAdd[num]

                        if isinstance(num_value, set):  # If the value is a list, sum its elements
                            total_noofitems += sum(num_value)
                        elif isinstance(num_value, int):  # If the value is an integer, add it directly
                            total_noofitems += num_value

                    total_noofitems_str1 = str(total_noofitems)

                    newObj1[tempGroup]['no_of_items'] = total_noofitems_str1 

                    

                    #---------------------------------------------------------------------------------------
                    #-------------------------Total-total_time------------------------------------------------------

                    timesToAdd = {
                        'oldTime': oldTime,
                        'curentTime': curentTime
                    }
                    
                    
                    # Initialize a timedelta object to store the total time
                    total_time = timedelta()

                    # Iterate through the keys to add the time
                    for times in timesToAdd:                        
                        #time_value = next(iter(timesToAdd[times]))  # Extract the single item from the set                        
                        time_value = timesToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_time += time_str_to_timedelta(time_values)

                    # Convert total_time back to a string in HH:MM:SS format
                    total_time_str = str(total_time)  

                    # newObj[tempGroup] = item     #-----(THIS LINE UPDATE THE RECENT RECORD TO THE RESPONSE)

                    newObj1[tempGroup]['total-time'] = total_time_str                    
                else:
                    if not isinstance(item['user'], set):
                            item['user'] = {item['user']}  # Convert the user to a set
                            newObj1[tempGroup] = item  
                    newObj1[tempGroup] = item               
                
            combinedArr = []

            for key, value in newObj1.items():
                combinedArr.append(value)

            result_data = combinedArr
            # CODE FOR COMBINING TOTAL-TIME ENDS HERE

            
            

            
            


            return result_data
        
    elif reportoptions == "natureofwork_membername":

            finalre = {
                'estimated_time_with_add' : pendulum.duration(),
                'date': set(),
                'user': set(),
                'Service_ID': set(),
                'scope': set(),
                'created_at' : set(),
                'Completed_date' : set(),
                'subscopes': set(),
                'entity': set(),
                # 'no_of_entity' : set(),
                'status': set(),
                'type_of_activity': set(),
                'Nature_of_Work': set(),
                'gst_tan': set(),
                'estimated_d_o_d': set(),
                'estimated_time': set(),
                'member_name': set(),
                'end_time': pendulum.duration(),
                'hold': pendulum.duration(),
                'break': pendulum.duration(),
                'time_diff_work': pendulum.duration(),
                'call': pendulum.duration(),
                'meeting': pendulum.duration(),
                'in_progress': pendulum.duration(),
                'completed': pendulum.duration(),
                'third_report_data' : set(),
                'fourth_report' :  set(),
                'fourth_report2' : set(),
                'fifth_report' : set(),
                'no_of_items' : set(),
                'chargable' : set(),
                'non-chargable' : set(),
                'total-time' : set(),
                'idealname' : pendulum.duration()
            }

            date_time_formate_string = '%Y-%m-%d %H:%M:%S'
            list_data = []
            result_data = []
            


            d1 = picked_date
            d2 = to_date

            # Convert strings to datetime objects
            start_date = datetime.strptime(d1, '%Y-%m-%d')
            end_date = datetime.strptime(d2, '%Y-%m-%d')

            # Generate all dates in between and store as strings
            dates_list = []
            current_date = start_date

            while current_date <= end_date:
                
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
                

        #     # dates_list contains all dates as strings
            # 
            for item in dates_list:
                reportoptions="twenty"
                list_data.append(totaltime.user_wise_report(db,item,reportoptions))

                
            list_data = [item for item in list_data if item]

            common =  set()
            # 
            # 
            for report_list in list_data:
                for entry in report_list:
                        my_set = {str(x) for x in entry['Service_ID']} 
                        
                        common.add(my_set.pop())

                                
            for finalitems in common:
                for report_list in list_data:
                    for entry in report_list:
                        if int(finalitems) in entry['Service_ID']:
                            for key in finalre.keys():
                                        if key == 'end_time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'estimated_time_with_add':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'hold':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'break':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'time_diff_work':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'call':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'meeting':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'in_progress':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'completed':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'idealname':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'no_of_items':
                                        
                                            try:
                                                
                                                if len(finalre[key]) == 0:
                                                    finalre[key] = [finalre[key].pop()]+int(entry[key].pop())
                                                else:
                                                    finalre[key] = entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'non-chargable':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        elif key == 'total-time':
                                            try:

                                                finalre[key] = finalre[key]+entry[key]
                                            except:
                                                finalre[key] = entry[key]
                                        else:
                                            finalre[key] = entry[key].union(finalre[key])

                result = {
                    'estimated_time_with_add' : set(),
                    'work_started_date' : set(),
                    'work_ended_date' : set(),
                    'number_of_days_taken' : set(),
                    'number_of_days_delayed' : set(),
                    'actual_date_of_delivery' : set(),
                    'estimated_date_of_delivery' : set(),
                    'number_of_entity' : set(),
                    'estimated_time_minus_chargable_time' : set(),
                    'date': set(),
                    'user': set(),
                    'Service_ID': set(),
                    'created_at' : set(),
                    'Completed_date' : set(),
                    'scope': set(),
                    'subscopes': set(),
                    'entity': set(),
                    # 'no_of_entity' : set(),
                    'status': set(),
                    'type_of_activity': set(),
                    'Nature_of_Work': set(),
                    'gst_tan': set(),
                    'estimated_d_o_d': set(),
                    'estimated_time': set(),
                    'member_name': set(),
                    'end_time': set(),
                    'hold': set(),
                    'break': set(),
                    'time_diff_work': set(),
                    'call': set(),
                    'meeting': set(),
                    'in_progress': set(),
                    'completed': set(),
                    'third_report_data' : set(),
                    'fourth_report' :  set(),
                    'fourth_report2' : set(),
                    'fifth_report' : set(),
                    'no_of_items' : set(),
                    'chargable' : set(),
                    'non-chargable' : set(),
                    'total-time' : set(),
                    'idealname' : set()
                }
                for key in finalre:
                    if isinstance(finalre[key], set):

                            cpof = finalre[key]
                            result[key]= cpof
                        
                            finalre[key] = set()

                    elif isinstance(finalre[key], int):
                        result[key] = finalre[key]
                        #   
                    else:
                    
                        result[key].add(convert_to_duration(finalre[key]))
                        finalre[key] = pendulum.duration()
                


        #--------------------------- last calculation


                        

                # Define the set of date strings
                date_strings = result['date']
            
                # Convert the date strings to datetime objects
                dateslast = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find the maximum date
                max_date = max(dateslast)

                min_date = min(dateslast)




                # Define the set of date strings
                date_strings_date = result['estimated_d_o_d']

                # Convert the date strings to datetime objects
                dateslast_date = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings_date}

                # Find the maximum date
                max_date_in_dates = max(dateslast_date)

                        


        #--------------------------- last calculation


                dateesti =  max_date_in_dates.strftime("%Y-%m-%d")

                # Define the set of date strings
                date_strings = result['date']

                # Convert dateesti to a datetime object
                dateesti_dt = datetime.strptime(dateesti, "%Y-%m-%d").date()

                # Convert the set of date strings to a set of datetime objects
                dates = {datetime.strptime(date, "%Y-%m-%d").date() for date in date_strings}

                # Find and count the dates that are greater than dateesti_dt
                greater_dates = {date for date in dates if date > dateesti_dt}
                count_greater_dates = len(greater_dates)

                    

        #-----------------------------getting estimate time
                        

                estichar = result['estimated_time_with_add'].pop()
                hourses, minuteses, secondses = map(int, estichar.split(':'))

                # Create a pendulum Duration object
                durationes = pendulum.duration(hours=hourses, minutes=minuteses, seconds=secondses)

        #----------------------------------------- chargable time


                nchar = result['chargable'].pop()

                hours, minutes, seconds = map(int, nchar.split(':'))

                # Create a pendulum Duration object
                duration = pendulum.duration(hours=hours, minutes=minutes, seconds=seconds)
                # 
#------------------------ late of date estimated
                result['chargable'] = nchar
                result['estimated_time_with_add'] = estichar
                result['work_started_date'] =  min_date
                result['work_ended_date'] = max_date
                result['number_of_days_taken'] = len(result['date'])
                result['number_of_days_delayed'] = count_greater_dates
                result['actual_date_of_delivery'] = max_date_in_dates 
                result['estimated_date_of_delivery'] = max_date_in_dates
                result['number_of_entity'] = len(result['entity'])
                result['estimated_time_minus_chargable_time'] = convert_to_duration(durationes-duration)

        #------------------------------ code end
                result_data.append(result)
                result = {}
                # 
                # 
                # 
            # CODE FOR COMBINING TOTAL-TIME STARTS HERE
            newObj1 = {}
            
            for item in result_data: 
                #

                # 

                # 

                # 
                tempGroup = ''
                
                for Nature_of_Work in item['Nature_of_Work']:
                    tempGroup+=Nature_of_Work

                for member_name in item['member_name']:
                    tempGroup+=member_name

                key_to_check = tempGroup

            
                if key_to_check in newObj1:
                    if isinstance(item['user'], set):   
                        newObj1[tempGroup]['user'].update(item['user'])  # Update with a set of users
                    else:
                        newObj1[tempGroup]['user'].add(item['user'])  # Add a single user

                    oldETWA = newObj1[tempGroup]['estimated_time_with_add']
                    currentETWA = item['estimated_time_with_add']

                    oldendtime = newObj1[tempGroup]['end_time']
                    currentendtime = item['end_time']

                    oldhold = newObj1[tempGroup]['hold']
                    currenthold = item['hold']

                    oldbreak = newObj1[tempGroup]['break']
                    currentbreak = item['break']

                    oldTDW = newObj1[tempGroup]['time_diff_work']
                    currentTDW = item['time_diff_work']

                    oldcall = newObj1[tempGroup]['call']
                    currentcall = item['call']

                    oldmeeting = newObj1[tempGroup]['meeting']
                    currentmeeting = item['meeting']

                    oldInProgress = newObj1[tempGroup]['in_progress']
                    currentInProgress = item['in_progress']

                    oldcompleted = newObj1[tempGroup]['completed']
                    currentcompleted = item['completed']

                    oldnoofitems = newObj1[tempGroup]['no_of_items']
                    currentnoofitems = item['no_of_items']

                    oldTime = newObj1[tempGroup]['total-time']
                    curentTime = item['total-time']
#--------------------------------------------------------------------------------------
#--------------------------Total-estimated_time_with_add-------------------------------
                    ETWAToAdd = {
                        'oldETWA': oldETWA,
                        'currentETWA' : currentETWA
                    }
                    
                    

                    total_ETWA = timedelta()

                    for times in ETWAToAdd:
                        time_value = ETWAToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_ETWA += time_str_to_timedelta(time_values)

                    total_ETWA_str1 = str(total_ETWA)

                    newObj1[tempGroup]['estimated_time_with_add'] = total_ETWA_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-end_time---------------------------------------------------
                    endtimeToAdd = {
                        'oldendtime': oldendtime,
                        'currentendtime' : currentendtime
                    }

                    
                    

                    total_endtime = timedelta()

                    for times in endtimeToAdd:
                        time_value = endtimeToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_endtime += time_str_to_timedelta(time_values)

                    total_endtime_str1 = str(total_endtime)

                    newObj1[tempGroup]['end_time'] = total_endtime_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-hold---------------------------------------------------
                    holdToAdd = {
                        'oldhold': oldhold,
                        'currenthold' : currenthold
                    }

                    
                    

                    total_hold = timedelta()

                    for times in holdToAdd:
                        time_value = holdToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_hold += time_str_to_timedelta(time_values)

                    total_hold_str1 = str(total_hold)

                    newObj1[tempGroup]['hold'] = total_hold_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-break------------------------------------------------------

                    breakToAdd = {
                        'oldbreak': oldbreak,
                        'currentbreak' : currentbreak
                    }

                    
                    

                    total_break = timedelta()

                    for times in breakToAdd:
                        time_value = breakToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_break += time_str_to_timedelta(time_values)

                    total_break_str1 = str(total_break)

                    newObj1[tempGroup]['break'] = total_break_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-time_diff_work------------------------------------------------------

                    TDWToAdd = {
                        'oldTDW': oldTDW,
                        'currentTDW' : currentTDW
                    }

                    
                    

                    total_TDW = timedelta()

                    for times in TDWToAdd:
                        time_value = TDWToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_TDW += time_str_to_timedelta(time_values)

                    total_TDW_str1 = str(total_TDW)

                    newObj1[tempGroup]['time_diff_work'] = total_TDW_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-call------------------------------------------------------

                    callToAdd = {
                        'oldcall': oldcall,
                        'currentcall' : currentcall
                    }

                    
                    

                    total_call = timedelta()

                    for times in callToAdd:
                        time_value = callToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_call += time_str_to_timedelta(time_values)

                    total_call_str1 = str(total_call)

                    newObj1[tempGroup]['call'] = total_call_str1 
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-meeting------------------------------------------------------
                    meetingToAdd = {
                        'oldmeeting': oldmeeting,
                        'currentmeeting' : currentmeeting
                    }

                    
                    

                    total_meeting = timedelta()

                    for times in meetingToAdd:
                        time_value = meetingToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_meeting += time_str_to_timedelta(time_values)

                    total_meeting_str1 = str(total_meeting)

                    newObj1[tempGroup]['meeting'] =  total_meeting_str1
                    #------------------------------------------------------------------------------------------
                    #-------------------------Total-in_progress------------------------------------------------------

                    # Inprogresstoadd = {
                    #     'oldInProgress': oldInProgress,
                    #     'currentInProgress' : currentInProgress
                    # }

                    # 
                    # 

                    # total_Inprogresstime = timedelta()

                    # for times in Inprogresstoadd:
                    #     time_value = Inprogresstoadd[times]
                    #     time_values = ''

                    #     if isinstance(time_value, set):
                    #         for time in time_value:
                    #             time_value = ""
                    #             time_value += time
                    #     else:
                    #         time_values = time_value
                        
                    #     total_Inprogresstime += time_str_to_timedelta(time_value)

                    # total_time_str1 = str(total_Inprogresstime)

                    # newObj1[tempGroup]['in_progress'] = total_time_str1 

                    Inprogresstoadd = {
                        'oldInProgress': oldInProgress,
                        'currentInProgress' : currentInProgress
                    }

                    
                    

                    total_Inprogresstime = timedelta()

                    for times in Inprogresstoadd:
                        time_value = Inprogresstoadd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_Inprogresstime += time_str_to_timedelta(time_values)

                    total_time_str1 = str(total_Inprogresstime)

                    newObj1[tempGroup]['in_progress'] = total_time_str1 
                    #---------------------------------------------------------------------------------------
                    #-------------------------Total-completed------------------------------------------------------
                    completedToAdd = {
                        'oldcompleted': oldcompleted,
                        'currentcompleted' : currentcompleted

                    }

                    
                    

                    total_completed = timedelta()

                    for times in completedToAdd:
                        time_value = completedToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time)
                        else:
                            time_values = time_value
                        
                    total_completed += time_str_to_timedelta(time_values)

                    total_completed_str1 = str(total_completed)

                    newObj1[tempGroup]['completed'] = total_completed_str1 

                    #------------------------------------------------------------------------------------
                    #-------------------------Total-no_of_items------------------------------------------------------

                    noofitemsdToAdd = {
                        'oldnoofitems': oldnoofitems,
                        'currentnoofitems' : currentnoofitems
                    }
                    
                    

                    total_noofitems = 0

                    for num in noofitemsdToAdd:
                        num_value = noofitemsdToAdd[num]

                        if isinstance(num_value, set):  # If the value is a list, sum its elements
                            total_noofitems += sum(num_value)
                        elif isinstance(num_value, int):  # If the value is an integer, add it directly
                            total_noofitems += num_value

                    total_noofitems_str1 = str(total_noofitems)

                    newObj1[tempGroup]['no_of_items'] = total_noofitems_str1 


                    #---------------------------------------------------------------------------------------
                    #-------------------------Total-total_time------------------------------------------------------

                    timesToAdd = {
                        'oldTime': oldTime,
                        'curentTime': curentTime
                    }
                    
                    
                    # Initialize a timedelta object to store the total time
                    total_time = timedelta()

                    # Iterate through the keys to add the time
                    for times in timesToAdd:                        
                        #time_value = next(iter(timesToAdd[times]))  # Extract the single item from the set                        
                        time_value = timesToAdd[times]
                        time_values = ''

                        if isinstance(time_value, set):
                            for time in time_value:
                                time_value = set()
                                time_value.add(time) 
                        else:
                            time_values = time_value
                        
                    total_time += time_str_to_timedelta(time_values)

                    # Convert total_time back to a string in HH:MM:SS format
                    total_time_str = str(total_time)  

                    # newObj[tempGroup] = item     #-----(THIS LINE UPDATE THE RECENT RECORD TO THE RESPONSE)

                    newObj1[tempGroup]['total-time'] = total_time_str                    
                else:
                    if not isinstance(item['user'], set):
                            item['user'] = {item['user']}  # Convert the user to a set
                            newObj1[tempGroup] = item  
                    newObj1[tempGroup] = item               
                
            combinedArr = []

            for key, value in newObj1.items():
                combinedArr.append(value)

            result_data = combinedArr
            # CODE FOR COMBINING TOTAL-TIME ENDS HERE

            
            

            
            


            return result_data
#--------------------------------------------------------------------------- Paupathi


def scope_add(scope: str,db :Session):
   db_tds = models.scope(scope = scope)
   db.add(db_tds)
   try:
        db.commit()
        return "Success"
   except :
       db.rollback()
       return "Failure"

def get_scope(db:Session):
    return db.query(models.scope).all()

def scope_delete(scope_id: int, db: Session):
    
    db_scope = db.query(models.scope).filter(models.scope.scope_id == scope_id).first()
    
    
    if db_scope is None:
        return "Scope not found"

    
    db.delete(db_scope)
    
    try:
        db.commit()
        return "Success"
    except:
        db.rollback()
        return "Failure"
    
def scope_update(scope_id: int, new_scope: str, db: Session):
    
    db_scope = db.query(models.scope).filter(models.scope.scope_id == scope_id).first()
    
    
    if db_scope is None:
        return "Scope not found"

    
    db_scope.scope = new_scope
    
    try:
        db.commit()
        return "Success"
    except:
        db.rollback()
        return "Failure"


def sub_scope_add(scope_id: int, sub_scope: str, db: Session):
    # Create a new sub_scope instance
    db_sub_scope = models.sub_scope(scope_id=scope_id, sub_scope=sub_scope)
    db.add(db_sub_scope)
    
    try:
        db.commit()
        db.refresh(db_sub_scope)
        return "Success"
    except:
        db.rollback()
        return "Failure"

def sub_scope_delete(sub_scope_id: int, db: Session):
    # Fetch the sub_scope to delete
    db_sub_scope = db.query(models.sub_scope).filter(models.sub_scope.sub_scope_id == sub_scope_id).first()
    
    # If the sub_scope is not found, return an error message
    if db_sub_scope is None:
        return "Sub-scope not found"

    # Delete the sub_scope
    db.delete(db_sub_scope)
    
    try:
        db.commit()
        return "Success"
    except:
        db.rollback()
        return "Failure"

def sub_scope_update(sub_scope_id: int, new_scope_id: int, new_sub_scope: str, db: Session):
    
    db_sub_scope = db.query(models.sub_scope).filter(models.sub_scope.sub_scope_id == sub_scope_id).first()
    
    
    if db_sub_scope is None:
        return "Sub-scope not found"

    
    db_sub_scope.scope_id = new_scope_id
    db_sub_scope.sub_scope = new_sub_scope
    
    try:
        db.commit()
        db.refresh(db_sub_scope)
        return "Success"
    except:
        db.rollback()
        return None

def get_sub_scope(scope_id,db:Session):

    return db.query(models.sub_scope).filter(models.sub_scope.scope_id == scope_id).all()

def logintime_add(logtime: str,userid: int,db :Session):
   db_logintime = models.login_time(userid = userid, login_time = logtime)
   db.add(db_logintime)
   try:
        db.commit()
        return "Success"
   except :
       db.rollback()
       return "Failure"
   
# def logout_time_add(logouttime: str,userid: int,db :Session):

#     db_res2 = db.query(models.login_time).filter(models.login_time.userid == userid).order_by(models.login_time.login_id.desc()).first()
    
    
    
#     db_res2.logout_time = logouttime
#     db.commit()
#     return "Success"

def entityadd(entityname: str,tanorgst: str,tanvalue: str,db :Session):
    entity_name_upper = entityname.upper()
   
    db_logintime = models.entityadd(entityname = entity_name_upper, gstortan = tanorgst,tanvalue = tanvalue)
    db.add(db_logintime)
    try:
            db.commit()
            return "Success"
    except :
            db.rollback()
            return "Failure"
   
def get_entity_data(db:Session):

    return db.query(models.entityadd).all()

def get_filter_entitydata(id,db:Session):

    return db.query(models.entityadd).filter(models.entityadd.id == id).all()




# --------------------------------elan code start------------------------------------- 
# --------------------------------logout auto start 

import pytz
def calculate_work_hours(userid: int, specific_date: str, db: Session):
    

    timezone = pytz.timezone('Asia/Kolkata')

    # Parse the specific date
    date_object = datetime.strptime(specific_date, '%Y-%m-%d')

    # Start and end of the day
    start_of_day = timezone.localize(date_object.replace(hour=0, minute=0, second=0, microsecond=0))
    end_of_day = timezone.localize(date_object.replace(hour=23, minute=59, second=59, microsecond=999999))

    # Query the login/logout data for the specific user and date
    login_logout_data = db.query(models.login_time).filter(
        and_(
            models.login_time.userid == userid,
            models.login_time.login_time >= start_of_day.strftime('%Y-%m-%d %H:%M:%S'),
            models.login_time.login_time <= end_of_day.strftime('%Y-%m-%d %H:%M:%S')
        )
    ).all()

    total_seconds_worked = 0
    current_time = datetime.now(timezone)

    for record in login_logout_data:
        # Parse login time
        login_dt = timezone.localize(datetime.strptime(record.login_time, '%Y-%m-%d %H:%M:%S'))

        # Parse logout time, or use current time if logout time is None
        if record.logout_time:
            logout_dt = timezone.localize(datetime.strptime(record.logout_time, '%Y-%m-%d %H:%M:%S'))
        else:
            logout_dt = current_time

        # Ensure logout time is after login time
        if logout_dt < login_dt:
            
            continue

        # Calculate seconds worked for this session
        seconds_worked = (logout_dt - login_dt).total_seconds()
        total_seconds_worked += seconds_worked

    # Convert total seconds to hours, minutes, and seconds
    total_hours = int(total_seconds_worked // 3600)
    remaining_minutes = int((total_seconds_worked % 3600) // 60)
    remaining_seconds = int(total_seconds_worked % 60)

    

    return f"{total_hours}:{remaining_minutes:02d}:{remaining_seconds:02d}"

# =======================================logout time auto update===================================


def time_check_logout(db: Session):
    try:
        current_time = datetime.now()
        current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')

        # Fetch records where logout_time is empty or None
        records_to_update = db.query(models.login_time).filter(
            or_(models.login_time.logout_time == '', models.login_time.logout_time.is_(None))
        ).all()

        if records_to_update:
            # Update logout_time for those records
            db.query(models.login_time).filter(
                or_(models.login_time.logout_time == '', models.login_time.logout_time.is_(None))
            ).update({models.login_time.logout_time: current_time_str}, synchronize_session=False)

            db.commit()

            # Query the records that were updated
            records_updated = db.query(models.login_time).filter(
                models.login_time.logout_time == current_time_str
            ).all()

            # Update WorkSession's end_time with the updated logout_time
            # Update WorkSession's end_time with the updated logout_time
            for record in records_updated:
                assigned_tasks = db.query(models.TL).filter(models.TL.Assigned_To == record.userid).all()

                for task in assigned_tasks:
                    work_sessions = db.query(models.WorkSession).filter(
                        and_(
                            models.WorkSession.user_id == record.userid,  # Use the correct user ID
                            models.WorkSession.end_time.is_(None)
                        )
                    ).all()

                    for work_session in work_sessions:
                        work_session.end_time = current_time_str
                        total_worked = calculate_total_times(work_session.start_time, work_session.end_time)
                        work_session.total_time_worked = total_worked  
                        db.add(work_session)

                db.commit()  # Commit after processing all work sessions


    except Exception as e:
        
        None

# --------------------------------logout auto end



            
#-------------------------------Change the Wrok statuses to Break, Call, Metting and Work in Progress--------------------------------------------


# def check_and_update_work_status(db: Session):
#     current_datetime = datetime.now()

#     # Query all relevant records
#     all_records = db.query(models.TL).filter(models.TL.work_status.in_(
#         ["Break", "Clarification Call", "Meeting", "Work in Progress"]
#     )).all()

    

#     for db_res in all_records:
#         # Get the current time for the record update
#         current_time_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

#         # Update work status and corresponding records
#         if db_res.work_status == "Break":
#             db_res.work_status = "End Of Day"
#             break_record = db.query(models.BREAK).filter(
#                 models.BREAK.Service_ID == db_res.Service_ID).first()
#             if break_record:
#                 break_record.break_time_end = current_time_str
#                 db.add(break_record)

#         elif db_res.work_status == "Clarification Call":
#             db_res.work_status = "End Of Day"
#             call_record = db.query(models.CALL).filter(
#                 models.CALL.Service_ID == db_res.Service_ID).first()
#             if call_record:
#                 call_record.call_time_end = current_time_str
#                 db.add(call_record)

#         elif db_res.work_status == "Meeting":
#             db_res.work_status = "End Of Day"
#             meeting_record = db.query(models.MEETING).filter(
#                 models.MEETING.Service_ID == db_res.Service_ID).first()
#             if meeting_record:
#                 meeting_record.meeting_time_end = current_time_str
#                 db.add(meeting_record)

#         elif db_res.work_status == "Work in Progress":
#             db_res.work_status = "End Of Day"
#             work_in_progress_record = db.query(models.TL).filter(
#                 models.I.Service_ID == db_res.Service_ID).first()
#             if work_in_progress_record:
#                 db_res.working_time = current_time_str
#                 db.add(work_in_progress_record)

#         # Insert a new End Of Day (EOD) record
#         end_of_day_record = models.END_OF_DAY(
#             Service_ID=db_res.Service_ID,
#             user_id=db_res.Assigned_To,
#             end_time_start=current_time_str,
#             remarks="Auto EOD"
#         )
#         db.add(end_of_day_record)

#         # Insert a new Work Session record when automict
#         work_session_record = models.WorkSession(
#             user_id=db_res.Assigned_To,
#             start_time=current_time_str  
#         )
#         db.add(work_session_record)

#     try:
#         db.commit()
        
#     except Exception as e:
#         None


from datetime import datetime

def check_and_update_work_status(db: Session):
    current_datetime = datetime.now()

    # Query all relevant records
    all_records = db.query(models.TL).filter(models.TL.work_status.in_(
        ["Break", "Clarification Call", "Meeting", "Work in Progress"]
    )).all()

    

    for db_res in all_records:
        # Get the current time for the record update
        current_time_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

        # Update work status and corresponding records
        if db_res.work_status == "Break":
            db_res.work_status = "End Of Day"
            break_record = db.query(models.BREAK).filter(
                models.BREAK.user_id == db_res.Assigned_To,
                models.BREAK.Service_ID == db_res.Service_ID
                ).first()
            if break_record:
                break_record.break_time_end = current_datetime  # Store as datetime
                db.add(break_record)

                # Calculate total break time
                if break_record.break_time_start and break_record.break_time_end:
                    total_break_time = break_record.break_time_end - break_record.break_time_start
                    
                    # Convert total time to seconds
                    total_seconds = total_break_time.total_seconds()
                    
                    # Format as HH:MM:SS
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    break_record.break_total_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        elif db_res.work_status == "Clarification Call":
            db_res.work_status = "End Of Day"
            call_record = db.query(models.CALL).filter(
                models.CALL.user_id == db_res.Assigned_To,
                models.CALL.Service_ID == db_res.Service_ID
                ).first()
            if call_record:
                call_record.call_time_end = current_datetime  # Store as datetime
                db.add(call_record)

                # Calculate total break time
                if call_record.call_time_start and call_record.call_time_end:
                    total_call_time = call_record.call_time_end - call_record.call_time_start
                    
                    # Convert total time to seconds
                    total_seconds = total_call_time.total_seconds()
                    
                    # Format as HH:MM:SS
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    call_record.call_total_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


        elif db_res.work_status == "Meeting":
            db_res.work_status = "End Of Day"
            meet_record = db.query(models.MEETING).filter(
                models.MEETING.user_id == db_res.Assigned_To,
                models.MEETING.Service_ID == db_res.Service_ID
                ).first()
            if meet_record:
                meet_record.meeting_time_end = current_datetime  # Store as datetime
                db.add(meet_record)

                # Calculate total break time
                if meet_record.meeting_time_start and meet_record.meeting_time_end:
                    total_meet_time = meet_record.meeting_time_end - meet_record.meeting_time_start
                    
                    # Convert total time to seconds
                    total_seconds = total_meet_time.total_seconds()
                    
                    # Format as HH:MM:SS
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    meet_record.meet_total_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        
        elif db_res.work_status == "Work in Progress":
            db_res.work_status = "End Of Day"
            work_record = db.query(models.INPROGRESS).filter(
                models.INPROGRESS.user_id == db_res.Assigned_To,
                models.INPROGRESS.Service_ID == db_res.Service_ID,
                models.INPROGRESS.end_time.is_(None)
            ).first()

            if work_record:
                work_record.end_time = current_datetime  # Store as datetime
                db.add(work_record)

                if work_record.start_time and work_record.end_time:
                    total_work_time = work_record.end_time - work_record.start_time
                    
                    # Convert to HH:MM:SS
                    total_seconds = total_work_time.total_seconds()
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    work_record.total_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"




        # Insert a new End Of Day (EOD) record
        end_of_day_record = models.END_OF_DAY(
            Service_ID=db_res.Service_ID,
            user_id=db_res.Assigned_To,
            end_time_start=current_time_str
        )
        db.add(end_of_day_record)

        # Insert a new Work Session record
        work_session_record = models.WorkSession(
            user_id=db_res.Assigned_To,
            start_time=current_time_str  
        )
        db.add(work_session_record)

    try:
        db.commit()
    except Exception as e:
        None  # Consider logging the error for debugging

# --------------------------------end     


# ------------------------------------------NEW IDEAL TIME and login satuts change CODE START

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

def idealtime(userid: int, check_status: str, db: Session):
    current_time = datetime.now()

    # Fetch the current work session for the user
    work_session = db.query(models.WorkSession).filter(
        models.WorkSession.user_id == userid
    ).order_by(models.WorkSession.id.desc()).first()

    # Check work status in TL table
    tl_records = db.query(models.TL).filter(models.TL.Assigned_To == userid).order_by(models.TL.Service_ID.desc()).all()
    
    new_session_created = False  # Track if a new session was created

    for tl_record in tl_records:
        if check_status == "Login":
            if tl_record.work_status == "Work in Progress":
                tl_record.work_status = "Hold"
                db.commit()
                

                 # Find the last INPROGRESS entry for the user
                in_progress_entry = (
                    db.query(models.INPROGRESS)
                    .filter(models.INPROGRESS.user_id == userid, models.INPROGRESS.Service_ID == tl_record.Service_ID, models.INPROGRESS.end_time.is_(None))
                    .order_by(models.INPROGRESS.id.desc())
                    .first()
                )

                if in_progress_entry:
                    # Update end_time in INPROGRESS table
                    in_progress_entry.end_time = datetime.now()  # Set end time to current time
                    db.commit()
                    logging.info(f"End time updated for INPROGRESS for user {userid}.")

                    # Calculate the total working time (end_time - start_time)
                    total_worked_time = calculate_total_times(in_progress_entry.start_time, in_progress_entry.end_time)
                    in_progress_entry.total_time = total_worked_time  # Assuming total_time is stored as a string
                    db.commit()
                    logging.info(f"Total working time updated for INPROGRESS for user {userid}.")

                hold_entry = models.HOLD(
                    Service_ID=tl_record.Service_ID,
                    user_id=userid,
                    hold_time_start=current_time,
                    remarks="Work to H"
                )
                db.add(hold_entry)

                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                
            elif tl_record.work_status == "Hold":
                if work_session and (work_session.end_time is None):
                    work_session.end_time = current_time
                    db.commit()

                    total_time = work_session.end_time - work_session.start_time
                    work_session.total_time_worked = format_timedelta(total_time)  # Format to HH:MM:SS
                    db.commit()

                if not new_session_created:
                    new_session = models.WorkSession(user_id=userid, start_time=current_time)
                    db.add(new_session)
                    db.commit()
                    
                    new_session_created = True  # Mark that a new session has been created

            elif check_status == "Login" and tl_record.work_status == "Break":
                tl_record.work_status = "Hold"
                db.commit()
                
                break_record = db.query(models.BREAK).filter(
                    models.BREAK.user_id == userid,
                    models.BREAK.break_time_end == None
                ).first()

                if break_record:
                    break_record.break_time_end = current_time
                    total_seconds = (break_record.break_time_end - break_record.break_time_start).total_seconds()
                    break_record.break_total_time = str(timedelta(seconds=int(total_seconds))).split('.')[0]
                    db.commit()
                    
                hold_entry = models.HOLD(
                    Service_ID=tl_record.Service_ID,
                    user_id=userid,
                    hold_time_start=current_time,
                    remarks="Break to Hold"
                )
                db.add(hold_entry)
                db.commit()

            elif check_status == "Login" and tl_record.work_status == "Meeting":  
                tl_record.work_status = "Hold"
                db.commit()
                
                meet_record = db.query(models.MEETING).filter(
                    models.MEETING.user_id == userid,
                    models.MEETING.meeting_time_end == None
                ).first()

                if meet_record:
                    meet_record.meeting_time_end = current_time
                    total_seconds = (meet_record.meeting_time_end - meet_record.meeting_time_start).total_seconds()
                    meet_record.meet_total_time = str(timedelta(seconds=int(total_seconds))).split('.')[0]
                    db.commit()
                    
                hold_entry = models.HOLD(
                    Service_ID=tl_record.Service_ID,
                    user_id=userid,
                    hold_time_start=current_time,
                    remarks="Meeting to Hold"
                )
                db.add(hold_entry)
                db.commit()

            elif check_status == "Login" and tl_record.work_status == "Clarification Call":  
                tl_record.work_status = "Hold"
                db.commit()
                
                call_record = db.query(models.CALL).filter(
                    models.CALL.user_id == userid,
                    models.CALL.call_time_end == None
                ).first()

                if call_record:
                    call_record.call_time_end = current_time
                    total_seconds = (call_record.call_time_end - call_record.call_time_start).total_seconds()
                    call_record.call_total_time = str(timedelta(seconds=int(total_seconds))).split('.')[0]
                    db.commit()
                
                hold_entry = models.HOLD(
                    Service_ID=tl_record.Service_ID,
                    user_id=userid,
                    hold_time_start=current_time,
                    remarks="Call to Hold"
                )
                db.add(hold_entry)
                db.commit()


            elif check_status == "Login" and tl_record.work_status == "End Of Day":  
                new_session = models.WorkSession(user_id=userid, start_time=current_time)
                db.add(new_session)
                db.commit()

    
    if not new_session_created:
        # If all TL records are End Of Day, create a new session
        if tl_records and all(tl_record.work_status == "End Of Day" for tl_record in tl_records):
            if work_session and work_session.end_time is None:
                work_session.end_time = current_time
                db.commit()

                total_time = work_session.end_time - work_session.start_time
                work_session.total_time_worked = format_timedelta(total_time)  # Format to HH:MM:SS
                db.commit()

            

    
        # Handle other statuses (if necessary)
        elif check_status in ["Login", "Hold", "Completed"]:
            if work_session and (work_session.end_time is None):
                work_session.end_time = current_time
                db.commit()

                total_time = work_session.end_time - work_session.start_time
                work_session.total_time_worked = format_timedelta(total_time)  # Format to HH:MM:SS
                db.commit()

            new_session = models.WorkSession(user_id=userid, start_time=current_time)
            db.add(new_session)
            db.commit()

        # Handle Work in Progress
        elif check_status == "Work in Progress":
            if work_session and (work_session.end_time is None):
                work_session.end_time = current_time
                db.commit()

                total_time = work_session.end_time - work_session.start_time
                work_session.total_time_worked = format_timedelta(total_time)  # Format to HH:MM:SS
                db.commit()
            else:
                None
            return userid

        # Handle Logout or Completed
        elif check_status == "Logout":
            if work_session and (work_session.end_time is None):
                work_session.end_time = current_time
                db.commit()

                total_time = work_session.end_time - work_session.start_time
                work_session.total_time_worked = format_timedelta(total_time)  # Format to HH:MM:SS
                db.commit()

            return userid
        
    # Handle End of Day
    if check_status == "End Of Day":
        if work_session and (work_session.end_time is None):
            work_session.end_time = current_time

            total_time = work_session.end_time - work_session.start_time
            work_session.total_time_worked = format_timedelta(total_time)  # Format to HH:MM:SS
            db.commit()
        else:
            new_session = models.WorkSession(user_id=userid, start_time=current_time)
            db.add(new_session)
            db.commit()

        return userid



def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"



def add_ideal_time(data_list: List[Dict], dict2: Dict[str, str]) -> List[Dict]:
    # Iterate over each dictionary in the list
    for data in data_list:
        # Extract the user from the current dictionary
        user = next(iter(data['user']), None)
        if user and user in dict2:
            # Add 'idealtime' to the dictionary if the user exists in dict2
            data['idealtime'] = dict2[user]
    
    return data_list

# def calculate_total_time(picked_date: str, to_date: str, db: Session) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     current_time = datetime.now()

#     # Initialize user times for each activity
#     user_times = {
#         'idealtime': defaultdict(timedelta),
#         'in_progress': defaultdict(timedelta),
#         'break': defaultdict(timedelta),
#         'meeting': defaultdict(timedelta),
#         'call': defaultdict(timedelta)
#     }

#     # Function to process records and calculate total time
#     def process_records(records, start_time_field, end_time_field, activity):
#         for record in records:
#             start_time = getattr(record, start_time_field)
#             end_time = getattr(record, end_time_field)

#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time as end_time for ongoing activities
#                 else:
#                     continue  # Ignore records that are not ongoing or not on the current date
            
#             # Get the username from the user table
#             user = db.query(models.User_table).filter(models.User_table.user_id == record.user_id).first()
#             member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'  # Safe fallback

#             user_times[activity][member_name] += (end_time - start_time)

#     # Fetch and process records for different activities
#     process_records(db.query(models.BREAK).filter(
#         models.BREAK.break_time_start >= picked_date_start,
#         models.BREAK.break_time_start <= to_date_end
#     ).all(), 'break_time_start', 'break_time_end', 'break')

#     process_records(db.query(models.MEETING).filter(
#         models.MEETING.meeting_time_start >= picked_date_start,
#         models.MEETING.meeting_time_start <= to_date_end
#     ).all(), 'meeting_time_start', 'meeting_time_end', 'meeting')

#     process_records(db.query(models.CALL).filter(
#         models.CALL.call_time_start >= picked_date_start,
#         models.CALL.call_time_start <= to_date_end
#     ).all(), 'call_time_start', 'call_time_end', 'call')

#     process_records(db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.start_time >= picked_date_start,
#         models.INPROGRESS.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'in_progress')

#     process_records(db.query(models.WorkSession).filter(
#         models.WorkSession.start_time >= picked_date_start,
#         models.WorkSession.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'idealtime')

#     # Format the total time for each activity and user
#     formatted_total_time = {
#         member_name: {
#             'member_name': member_name,  # Include the member name in the response
#             'idealtime': str(user_times['idealtime'][member_name]).split('.')[0],
#             'in_progress': str(user_times['in_progress'][member_name]).split('.')[0],
#             'break': str(user_times['break'][member_name]).split('.')[0],
#             'call': str(user_times['call'][member_name]).split('.')[0],
#             'meeting': str(user_times['meeting'][member_name]).split('.')[0],
#             'completed': str(user_times['in_progress'][member_name]).split('.')[0],
#             'Total Time Take': str(
#                 user_times['idealtime'][member_name] +
#                 user_times['in_progress'][member_name] +
#                 user_times['break'][member_name] +
#                 user_times['call'][member_name] +
#                 user_times['meeting'][member_name]
#             ).split('.')[0]  # Sum of all activities
#         }
#         for member_name in set(user_times['break'].keys()).union(
#             user_times['meeting'].keys(), user_times['call'].keys(),
#             user_times['in_progress'].keys(), user_times['idealtime'].keys()
#         )
#     }

#     return formatted_total_time



# from datetime import datetime, timedelta
# from collections import defaultdict
# from sqlalchemy.orm import Session

# def calculate_total_time(picked_date: str, to_date: str, db: Session) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     current_time = datetime.now()

#     # Initialize user times for each activity
#     user_times = {
#         'idealtime': defaultdict(timedelta),
#         'in_progress': defaultdict(timedelta),
#         'break': defaultdict(timedelta),
#         'meeting': defaultdict(timedelta),
#         'call': defaultdict(timedelta),
#         'completed': defaultdict(timedelta)
#     }

#     def get_completed_time(member_name: str, picked_date_start: datetime, to_date_end: datetime) -> timedelta:
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()
        
#         if user:
#             user_id = user.user_id  # Ensure this is an integer ID
#             in_progress_records = db.query(models.INPROGRESS).filter(
#                 models.INPROGRESS.user_id == user_id,
#                 models.INPROGRESS.start_time >= picked_date_start,
#                 models.INPROGRESS.start_time <= to_date_end
#             ).all()

#             total_completed_time = timedelta()
#             for record in in_progress_records:
#                 # Convert the total_time string to timedelta
#                 if record.total_time:
#                     try:
#                         hours, minutes, seconds = map(int, record.total_time.split(':'))
#                         total_completed_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                     except ValueError as e:
#                         print(f"Error parsing total_time for record {record.id}: {e}")

#             return total_completed_time
#         else:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()  # Return zero time if user not found

#     # Function to process records and calculate total time
#     def process_records(records, start_time_field, end_time_field, activity):
#         for record in records:
#             start_time = getattr(record, start_time_field)
#             end_time = getattr(record, end_time_field)

#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time as end_time for ongoing activities
#                 else:
#                     continue  # Ignore records that are not ongoing or not on the current date
            
#             # Get the username from the user table
#             user = db.query(models.User_table).filter(models.User_table.user_id == record.user_id).first()
#             member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'  # Safe fallback

#             # Calculate the time difference
#             time_diff = end_time - start_time
            
#             # Accumulate time per user and activity
#             user_times[activity][member_name] += time_diff

#     # Fetch and process records for different activities
#     process_records(db.query(models.BREAK).filter(
#         models.BREAK.break_time_start >= picked_date_start,
#         models.BREAK.break_time_start <= to_date_end
#     ).all(), 'break_time_start', 'break_time_end', 'break')

#     process_records(db.query(models.MEETING).filter(
#         models.MEETING.meeting_time_start >= picked_date_start,
#         models.MEETING.meeting_time_start <= to_date_end
#     ).all(), 'meeting_time_start', 'meeting_time_end', 'meeting')

#     process_records(db.query(models.CALL).filter(
#         models.CALL.call_time_start >= picked_date_start,
#         models.CALL.call_time_start <= to_date_end
#     ).all(), 'call_time_start', 'call_time_end', 'call')

#     process_records(db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.start_time >= picked_date_start,
#         models.INPROGRESS.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'in_progress')

#     process_records(db.query(models.WorkSession).filter(
#         models.WorkSession.start_time >= picked_date_start,
#         models.WorkSession.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'idealtime')

#     # Calculate completed time after processing all records
#     for member_name in user_times['in_progress'].keys():
#         user_times['completed'][member_name] += get_completed_time(member_name, picked_date_start, to_date_end)

#     # Format the total time for each activity and user
#     formatted_total_time = {
#         member_name: {
#             'member_name': member_name,
#             'idealtime': str(user_times['idealtime'][member_name]).split('.')[0],
#             'in_progress': str(user_times['in_progress'][member_name]).split('.')[0],
#             'break': str(user_times['break'][member_name]).split('.')[0],
#             'call': str(user_times['call'][member_name]).split('.')[0],
#             'meeting': str(user_times['meeting'][member_name]).split('.')[0],
#             'completed': str(user_times['completed'][member_name]).split('.')[0],  # Use completed time
#             'Total Time Take': str(
#                 user_times['idealtime'][member_name] +
#                 user_times['in_progress'][member_name] +
#                 user_times['break'][member_name] +
#                 user_times['call'][member_name] +
#                 user_times['meeting'][member_name] +
#                 user_times['completed'][member_name]
#             ).split('.')[0]  # Sum of all activities
#         }
#         for member_name in set(user_times['break'].keys()).union(
#             user_times['meeting'].keys(), user_times['call'].keys(),
#             user_times['in_progress'].keys(), user_times['idealtime'].keys()
#         )
#     }

#     return formatted_total_time
# -----------------WOKING ON OCT18 18:26



# def calculate_total_time(picked_date: str, to_date: str, db: Session) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     current_time = datetime.now()

#     # Initialize user times for each activity
#     user_times = {
#         'idealtime': defaultdict(timedelta),
#         'in_progress': defaultdict(timedelta),
#         'break': defaultdict(timedelta),
#         'meeting': defaultdict(timedelta),
#         'call': defaultdict(timedelta),
#         'completed': defaultdict(timedelta),
#         'chargeable': defaultdict(timedelta)  # Add chargeable time
#     }

#     def get_completed_time(member_name: str, picked_date_start: datetime, to_date_end: datetime) -> timedelta:
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()
        
#         if user:
#             user_id = user.user_id  # Ensure this is an integer ID
#             in_progress_records = db.query(models.INPROGRESS).filter(
#                 models.INPROGRESS.user_id == user_id,
#                 models.INPROGRESS.start_time >= picked_date_start,
#                 models.INPROGRESS.start_time <= to_date_end
#             ).all()

#             total_completed_time = timedelta()
#             for record in in_progress_records:
#                 # Convert the total_time string to timedelta
#                 if record.total_time:
#                     try:
#                         hours, minutes, seconds = map(int, record.total_time.split(':'))
#                         total_completed_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                     except ValueError as e:
#                         print(f"Error parsing total_time for record {record.id}: {e}")

#             return total_completed_time
#         else:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()  # Return zero time if user not found

#     def get_chargeable_time(member_name, picked_date_start, to_date_end):
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()
        
#         if user:
#             user_id = user.user_id  # Ensure this is an integer ID
#             in_progress_records = db.query(models.INPROGRESS).filter(
#                 models.INPROGRESS.user_id == user_id,
#                 models.INPROGRESS.start_time >= picked_date_start,
#                 or_(
#                     models.INPROGRESS.end_time <= to_date_end,
#                     models.INPROGRESS.end_time == None  # This includes ongoing activities
#                 )
#             ).all()

#             total_chargeable_time = timedelta()  # Initialize the total chargeable time

#             for record in in_progress_records:
#                 # Convert the total_time string to timedelta
#                 if record.total_time:
#                     try:
#                         hours, minutes, seconds = map(int, record.total_time.split(':'))
#                         total_chargeable_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                     except ValueError as e:
#                         print(f"Error parsing total_time for record {record.id}: {e}")

#             return total_chargeable_time
#         else:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()  # Return zero time if user not found





#     # Function to process records and calculate total time
#     def process_records(records, start_time_field, end_time_field, activity):
#         for record in records:
#             start_time = getattr(record, start_time_field)
#             end_time = getattr(record, end_time_field)

#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time as end_time for ongoing activities
#                 else:
#                     continue  # Ignore records that are not ongoing or not on the current date
            
#             # Get the username from the user table
#             user = db.query(models.User_table).filter(models.User_table.user_id == record.user_id).first()
#             member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'  # Safe fallback

#             # Calculate the time difference
#             time_diff = end_time - start_time
            
#             # Accumulate time per user and activity
#             user_times[activity][member_name] += time_diff

#     # Fetch and process records for different activities
#     process_records(db.query(models.BREAK).filter(
#         models.BREAK.break_time_start >= picked_date_start,
#         models.BREAK.break_time_start <= to_date_end
#     ).all(), 'break_time_start', 'break_time_end', 'break')

#     process_records(db.query(models.MEETING).filter(
#         models.MEETING.meeting_time_start >= picked_date_start,
#         models.MEETING.meeting_time_start <= to_date_end
#     ).all(), 'meeting_time_start', 'meeting_time_end', 'meeting')

#     process_records(db.query(models.CALL).filter(
#         models.CALL.call_time_start >= picked_date_start,
#         models.CALL.call_time_start <= to_date_end
#     ).all(), 'call_time_start', 'call_time_end', 'call')

#     process_records(db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.start_time >= picked_date_start,
#         models.INPROGRESS.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'in_progress')

#     process_records(db.query(models.WorkSession).filter(
#         models.WorkSession.start_time >= picked_date_start,
#         models.WorkSession.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'idealtime')

#     # Calculate completed and chargeable time after processing all records
#     for member_name in user_times['in_progress'].keys():
#         user_times['completed'][member_name] += get_completed_time(member_name, picked_date_start, to_date_end)
#         user_times['chargeable'][member_name] += get_chargeable_time(member_name, picked_date_start, to_date_end)

#     # Format the total time for each activity and user
#     formatted_total_time = {
#         member_name: {
#             'member_name': member_name,
#             'idealtime': str(user_times['idealtime'][member_name]).split('.')[0],
#             'in_progress': str(user_times['in_progress'][member_name]).split('.')[0],
#             'break': str(user_times['break'][member_name]).split('.')[0],
#             'call': str(user_times['call'][member_name]).split('.')[0],
#             'meeting': str(user_times['meeting'][member_name]).split('.')[0],
#             'completed': str(user_times['completed'][member_name]).split('.')[0],  # Use completed time
#             'chargeable': str(user_times['chargeable'][member_name]).split('.')[0],  # Use chargeable time
#             'Total Time Taken': str(
#                 user_times['idealtime'][member_name] +
#                 user_times['in_progress'][member_name] +
#                 user_times['break'][member_name] +
#                 user_times['call'][member_name] +
#                 user_times['meeting'][member_name] +
#                 user_times['completed'][member_name]
#             ).split('.')[0]  # Sum of all activities
#         }
#         for member_name in set(user_times['break'].keys()).union(
#             user_times['meeting'].keys(), user_times['call'].keys(),
#             user_times['in_progress'].keys(), user_times['idealtime'].keys()
#         )
#     }

#     return formatted_total_time
# -------------------------work on oct21

# from datetime import datetime, timedelta
# from collections import defaultdict
# from sqlalchemy.orm import Session, aliased
# from sqlalchemy import or_

# def calculate_total_time(picked_date: str, to_date: str, db: Session) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     current_time = datetime.now()

#     # Initialize user times for each activity
#     user_times = {
#         'idealtime': defaultdict(timedelta),
#         'in_progress': defaultdict(timedelta),
#         'break': defaultdict(timedelta),
#         'meeting': defaultdict(timedelta),
#         'call': defaultdict(timedelta),
#         'completed': defaultdict(timedelta),
#         'chargeable': defaultdict(timedelta),
#         'non-chargeable': defaultdict(timedelta),
#     }

#     def get_completed_time(member_name: str, picked_date_start: datetime, to_date_end: datetime) -> timedelta:
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()

#         if user:
#             user_id = user.user_id  # Ensure this is an integer ID
#             in_progress_records = db.query(models.INPROGRESS).filter(
#                 models.INPROGRESS.user_id == user_id,
#                 models.INPROGRESS.start_time >= picked_date_start,
#                 models.INPROGRESS.start_time <= to_date_end
#             ).all()

#             total_completed_time = timedelta()
#             for record in in_progress_records:
#                 # Convert the total_time string to timedelta
#                 if record.total_time:
#                     try:
#                         hours, minutes, seconds = map(int, record.total_time.split(':'))
#                         total_completed_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                     except ValueError as e:
#                         print(f"Error parsing total_time for record {record.id}: {e}")

#             return total_completed_time
#         else:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()  # Return zero time if user not found

#     def get_chargeable_time(member_name, picked_date_start, to_date_end):
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()

#         if not user:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()  # Return zero if user not found

#         user_id = user.user_id
#         TL_alias = aliased(models.TL)

#         in_progress_records = db.query(models.INPROGRESS).join(
#             TL_alias, TL_alias.Assigned_To == models.INPROGRESS.user_id
#         ).filter(
#             models.INPROGRESS.user_id == user_id,
#             models.INPROGRESS.start_time >= picked_date_start,
#             or_(
#                 models.INPROGRESS.end_time <= to_date_end,
#                 models.INPROGRESS.end_time.is_(None)  # Correct NULL check
#             ),
#             TL_alias.Assigned_To == user_id,  # Ensure correct assignment
#             TL_alias.type_of_activity == "CHARGABLE",
#             TL_alias.status == 1
#         ).all()

#         total_chargeable_time = timedelta()

#         for record in in_progress_records:
#             if record.total_time:
#                 try:
#                     hours, minutes, seconds = map(int, record.total_time.split(':'))
#                     total_chargeable_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                 except ValueError as e:
#                     print(f"Error parsing total_time for record {record.id}: {e}")

#         return total_chargeable_time

#     def get_nonchargeable_time(member_name, picked_date_start, to_date_end):
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()

#         if not user:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()

#         user_id = user.user_id
#         TL_alias = aliased(models.TL)

#         in_progress_records = db.query(models.INPROGRESS).join(
#             TL_alias, TL_alias.Assigned_To == models.INPROGRESS.user_id
#         ).filter(
#             models.INPROGRESS.user_id == user_id,
#             models.INPROGRESS.start_time >= picked_date_start,
#             or_(
#                 models.INPROGRESS.end_time <= to_date_end,
#                 models.INPROGRESS.end_time.is_(None)  # Correct NULL check
#             ),
#             TL_alias.Assigned_To == user_id,  # Ensure correct assignment
#             TL_alias.type_of_activity == "Non-Chargeable",
#             TL_alias.status == 1
#         ).all()

#         total_nonchargeable_time = timedelta()

#         for record in in_progress_records:
#             if record.total_time:
#                 try:
#                     hours, minutes, seconds = map(int, record.total_time.split(':'))
#                     total_nonchargeable_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                 except ValueError as e:
#                     print(f"Error parsing total_time for record {record.id}: {e}")

#         return total_nonchargeable_time

#     # Function to process records and calculate total time
#     def process_records(records, start_time_field, end_time_field, activity):
#         for record in records:
#             start_time = getattr(record, start_time_field)
#             end_time = getattr(record, end_time_field)

#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time as end_time for ongoing activities
#                 else:
#                     continue  # Ignore records that are not ongoing or not on the current date

#             # Get the username from the user table
#             user = db.query(models.User_table).filter(models.User_table.user_id == record.user_id).first()
#             member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'  # Safe fallback

#             # Calculate the time difference
#             time_diff = end_time - start_time

#             # Accumulate time per user and activity
#             user_times[activity][member_name] += time_diff

#     # Fetch and process records for different activities
#     process_records(db.query(models.BREAK).filter(
#         models.BREAK.break_time_start >= picked_date_start,
#         models.BREAK.break_time_start <= to_date_end
#     ).all(), 'break_time_start', 'break_time_end', 'break')

#     process_records(db.query(models.MEETING).filter(
#         models.MEETING.meeting_time_start >= picked_date_start,
#         models.MEETING.meeting_time_start <= to_date_end
#     ).all(), 'meeting_time_start', 'meeting_time_end', 'meeting')

#     process_records(db.query(models.CALL).filter(
#         models.CALL.call_time_start >= picked_date_start,
#         models.CALL.call_time_start <= to_date_end
#     ).all(), 'call_time_start', 'call_time_end', 'call')

#     process_records(db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.start_time >= picked_date_start,
#         models.INPROGRESS.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'in_progress')

#     process_records(db.query(models.WorkSession).filter(
#         models.WorkSession.start_time >= picked_date_start,
#         models.WorkSession.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'idealtime')

#     # Calculate completed and chargeable time after processing all records
#     for member_name in user_times['in_progress'].keys():
#         user_times['completed'][member_name] += get_completed_time(member_name, picked_date_start, to_date_end)
#         user_times['chargeable'][member_name] += get_chargeable_time(member_name, picked_date_start, to_date_end)
#         user_times['non-chargeable'][member_name] += get_nonchargeable_time(member_name, picked_date_start, to_date_end)

#     # Format the total time for each activity and user
#     formatted_total_time = {
#         member_name: {
#             'member_name': member_name,
#             'idealtime': str(user_times['idealtime'][member_name]).split('.')[0] or '00:00:00',
#             'in_progress': str(user_times['in_progress'][member_name]).split('.')[0] or '00:00:00',
#             'break': str(user_times['break'][member_name]).split('.')[0] or '00:00:00',
#             'call': str(user_times['call'][member_name]).split('.')[0] or '00:00:00',
#             'meeting': str(user_times['meeting'][member_name]).split('.')[0] or '00:00:00',
#             'completed': str(user_times['completed'][member_name]).split('.')[0] or '00:00:00',
#             'chargeable': str(user_times['chargeable'][member_name]).split('.')[0] or '00:00:00',
#             'non-chargeable': str(user_times['non-chargeable'][member_name]).split('.')[0] or '00:00:00',
#             'Total Chargeable and Non-Chargeable Time': str(
#                 user_times['chargeable'][member_name] +
#                 user_times['non-chargeable'][member_name]
#             ).split('.')[0] or '00:00:00',
#             'Total Time Taken': str(
#                 user_times['idealtime'][member_name] +
#                 user_times['in_progress'][member_name] +
#                 user_times['break'][member_name] +
#                 user_times['call'][member_name] +
#                 user_times['meeting'][member_name] +
#                 user_times['completed'][member_name]
#             ).split('.')[0] or '00:00:00'
#         } for member_name in user_times['idealtime']
#     }

#     return formatted_total_time


# from datetime import datetime, timedelta
# from collections import defaultdict
# from sqlalchemy.orm import Session, aliased
# from sqlalchemy import or_

# def format_timedelta_to_str(delta: timedelta) -> str:
#     """Convert a timedelta to a string in HH:MM:SS format."""
#     total_seconds = int(delta.total_seconds())
#     hours, remainder = divmod(total_seconds, 3600)
#     minutes, seconds = divmod(remainder, 60)
#     return f"{hours:02}:{minutes:02}:{seconds:02}"

# from datetime import datetime, timedelta
# from collections import defaultdict
# from sqlalchemy.orm import Session, aliased
# from sqlalchemy import or_

# def calculate_total_time(picked_date: str, to_date: str, db: Session) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     current_time = datetime.now()

#     # Initialize user times for each activity
#     user_times = {
#         'idealtime': defaultdict(timedelta),
#         'in_progress': defaultdict(timedelta),
#         'break': defaultdict(timedelta),
#         'meeting': defaultdict(timedelta),
#         'call': defaultdict(timedelta),
#         'completed': defaultdict(timedelta),
#         'chargeable': defaultdict(timedelta),
#         'non-chargeable': defaultdict(timedelta),
#     }

#     def get_completed_time(member_name: str, picked_date_start: datetime, to_date_end: datetime) -> timedelta:
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()

#         if user:
#             user_id = user.user_id  # Ensure this is an integer ID
#             in_progress_records = db.query(models.INPROGRESS).filter(
#                 models.INPROGRESS.user_id == user_id,
#                 models.INPROGRESS.start_time >= picked_date_start,
#                 models.INPROGRESS.start_time <= to_date_end
#             ).all()

#             total_completed_time = timedelta()
#             for record in in_progress_records:
#                 # Convert the total_time string to timedelta
#                 if record.total_time:
#                     try:
#                         hours, minutes, seconds = map(int, record.total_time.split(':'))
#                         total_completed_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                     except ValueError as e:
#                         print(f"Error parsing total_time for record {record.id}: {e}")

#             return total_completed_time
#         else:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()  # Return zero time if user not found

#     def get_chargeable_time(member_name, picked_date_start, to_date_end):
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()

#         if not user:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()  # Return zero if user not found

#         user_id = user.user_id
#         TL_alias = aliased(models.TL)

#         in_progress_records = db.query(models.INPROGRESS).join(
#             TL_alias, TL_alias.Assigned_To == models.INPROGRESS.user_id
#         ).filter(
#             models.INPROGRESS.user_id == user_id,
#             models.INPROGRESS.start_time >= picked_date_start,
#             or_(
#                 models.INPROGRESS.end_time <= to_date_end,
#                 models.INPROGRESS.end_time.is_(None)  # Correct NULL check
#             ),
#             TL_alias.Assigned_To == user_id,  # Ensure correct assignment
#             TL_alias.type_of_activity == "CHARGABLE",
#             TL_alias.status == 1
#         ).all()

#         total_chargeable_time = timedelta()

#         for record in in_progress_records:
#             if record.total_time:
#                 try:
#                     hours, minutes, seconds = map(int, record.total_time.split(':'))
#                     total_chargeable_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                 except ValueError as e:
#                     print(f"Error parsing total_time for record {record.id}: {e}")

#         return total_chargeable_time

#     def get_nonchargeable_time(member_name, picked_date_start, to_date_end):
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()

#         if not user:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()

#         user_id = user.user_id
#         TL_alias = aliased(models.TL)

#         in_progress_records = db.query(models.INPROGRESS).join(
#             TL_alias, TL_alias.Assigned_To == models.INPROGRESS.user_id
#         ).filter(
#             models.INPROGRESS.user_id == user_id,
#             models.INPROGRESS.start_time >= picked_date_start,
#             or_(
#                 models.INPROGRESS.end_time <= to_date_end,
#                 models.INPROGRESS.end_time.is_(None)  # Correct NULL check
#             ),
#             TL_alias.Assigned_To == user_id,  # Ensure correct assignment
#             TL_alias.type_of_activity == "Non-Chargeable",
#             TL_alias.status == 1
#         ).all()

#         total_nonchargeable_time = timedelta()

#         for record in in_progress_records:
#             if record.total_time:
#                 try:
#                     hours, minutes, seconds = map(int, record.total_time.split(':'))
#                     total_nonchargeable_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                 except ValueError as e:
#                     print(f"Error parsing total_time for record {record.id}: {e}")

#         return total_nonchargeable_time

#     # Function to process records and calculate total time
#     def process_records(records, start_time_field, end_time_field, activity):
#         for record in records:
#             start_time = getattr(record, start_time_field)
#             end_time = getattr(record, end_time_field)

#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time as end_time for ongoing activities
#                 else:
#                     continue  # Ignore records that are not ongoing or not on the current date

#             # Get the username from the user table
#             user = db.query(models.User_table).filter(models.User_table.user_id == record.user_id).first()
#             member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'  # Safe fallback

#             # Calculate the time difference
#             time_diff = end_time - start_time

#             # Accumulate time per user and activity
#             user_times[activity][member_name] += time_diff

#     # Fetch and process records for different activities
#     process_records(db.query(models.BREAK).filter(
#         models.BREAK.break_time_start >= picked_date_start,
#         models.BREAK.break_time_start <= to_date_end
#     ).all(), 'break_time_start', 'break_time_end', 'break')

#     process_records(db.query(models.MEETING).filter(
#         models.MEETING.meeting_time_start >= picked_date_start,
#         models.MEETING.meeting_time_start <= to_date_end
#     ).all(), 'meeting_time_start', 'meeting_time_end', 'meeting')

#     process_records(db.query(models.CALL).filter(
#         models.CALL.call_time_start >= picked_date_start,
#         models.CALL.call_time_start <= to_date_end
#     ).all(), 'call_time_start', 'call_time_end', 'call')

#     process_records(db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.start_time >= picked_date_start,
#         models.INPROGRESS.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'in_progress')

#     process_records(db.query(models.WorkSession).filter(
#         models.WorkSession.start_time >= picked_date_start,
#         models.WorkSession.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'idealtime')

#     # Calculate completed and chargeable time after processing all records
#     for member_name in user_times['in_progress'].keys():
#         user_times['completed'][member_name] += get_completed_time(member_name, picked_date_start, to_date_end)
#         user_times['chargeable'][member_name] += get_chargeable_time(member_name, picked_date_start, to_date_end)
#         user_times['non-chargeable'][member_name] += get_nonchargeable_time(member_name, picked_date_start, to_date_end)

#     # Format the total time for each activity and user
#     formatted_total_time = {
#         member_name: {
#             'member_name': member_name,
#             'idealtime': str(user_times['idealtime'][member_name]).split('.')[0] or '00:00:00',
#             'in_progress': str(user_times['in_progress'][member_name]).split('.')[0] or '00:00:00',
#             'break': str(user_times['break'][member_name]).split('.')[0] or '00:00:00',
#             'call': str(user_times['call'][member_name]).split('.')[0] or '00:00:00',
#             'meeting': str(user_times['meeting'][member_name]).split('.')[0] or '00:00:00',
#             'completed': str(user_times['completed'][member_name]).split('.')[0] or '00:00:00',
#             'chargeable': str(user_times['chargeable'][member_name]).split('.')[0] or '00:00:00',
#             'non-chargeable': str(user_times['non-chargeable'][member_name]).split('.')[0] or '00:00:00',
#             'Total Chargeable and Non-Chargeable Time': str(
#                 user_times['chargeable'][member_name] +
#                 user_times['non-chargeable'][member_name]
#             ).split('.')[0] or '00:00:00',
#             'Total Time Taken': str(
#                 user_times['idealtime'][member_name] +
#                 user_times['in_progress'][member_name] +
#                 user_times['break'][member_name] +
#                 user_times['call'][member_name] +
#                 user_times['meeting'][member_name] +
#                 user_times['completed'][member_name]
#             ).split('.')[0] or '00:00:00'
#         } for member_name in user_times['idealtime']
#     }

#     return formatted_total_time
# ------woked on oct22


# from datetime import datetime, timedelta
# from collections import defaultdict
# from sqlalchemy.orm import Session, aliased
# from sqlalchemy import or_

# def format_timedelta_to_str(delta: timedelta) -> str:
#     """Convert a timedelta to a string in HH:MM:SS format."""
#     total_seconds = int(delta.total_seconds())
#     hours, remainder = divmod(total_seconds, 3600)
#     minutes, seconds = divmod(remainder, 60)
#     return f"{hours:02}:{minutes:02}:{seconds:02}"

# from datetime import datetime, timedelta
# from collections import defaultdict
# from sqlalchemy.orm import Session, aliased
# from sqlalchemy import or_

# def calculate_total_time(picked_date: str, to_date: str, db: Session) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     current_time = datetime.now()

#     # Initialize user times for each activity
#     user_times = {
#         'idealtime': defaultdict(timedelta),
#         'in_progress': defaultdict(timedelta),
#         'break': defaultdict(timedelta),
#         'meeting': defaultdict(timedelta),
#         'call': defaultdict(timedelta),
#         'completed': defaultdict(timedelta),
#         'chargeable': defaultdict(timedelta),
#         'non-chargeable': defaultdict(timedelta),
#     }

#     def get_completed_time(member_name: str, picked_date_start: datetime, to_date_end: datetime) -> timedelta:
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()

#         if user:
#             user_id = user.user_id  # Ensure this is an integer ID
#             in_progress_records = db.query(models.INPROGRESS).filter(
#                 models.INPROGRESS.user_id == user_id,
#                 models.INPROGRESS.start_time >= picked_date_start,
#                 models.INPROGRESS.start_time <= to_date_end
#             ).all()

#             total_completed_time = timedelta()
#             for record in in_progress_records:
#                 # Convert the total_time string to timedelta
#                 if record.total_time:
#                     try:
#                         hours, minutes, seconds = map(int, record.total_time.split(':'))
#                         total_completed_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                     except ValueError as e:
#                         print(f"Error parsing total_time for record {record.id}: {e}")

#             return total_completed_time
#         else:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()  # Return zero time if user not found

#     def get_chargeable_time(member_name, picked_date_start, to_date_end):
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()

#         if not user:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()  # Return zero if user not found

#         user_id = user.user_id
#         TL_alias = aliased(models.TL)

#         in_progress_records = db.query(models.INPROGRESS).join(
#             TL_alias, TL_alias.Assigned_To == models.INPROGRESS.user_id
#         ).filter(
#             models.INPROGRESS.user_id == user_id,
#             models.INPROGRESS.start_time >= picked_date_start,
#             or_(
#                 models.INPROGRESS.end_time <= to_date_end,
#                 models.INPROGRESS.end_time.is_(None)  # Correct NULL check
#             ),
#             TL_alias.Assigned_To == user_id,  # Ensure correct assignment
#             TL_alias.type_of_activity == "CHARGABLE",
#             TL_alias.status == 1
#         ).all()

#         total_chargeable_time = timedelta()

#         for record in in_progress_records:
#             if record.total_time:
#                 try:
#                     hours, minutes, seconds = map(int, record.total_time.split(':'))
#                     total_chargeable_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                 except ValueError as e:
#                     print(f"Error parsing total_time for record {record.id}: {e}")

#         return total_chargeable_time

#     def get_nonchargeable_time(member_name, picked_date_start, to_date_end):
#         user = db.query(models.User_table).filter(
#             (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
#         ).first()

#         if not user:
#             print(f"User not found for member_name: {member_name}")
#             return timedelta()

#         user_id = user.user_id
#         TL_alias = aliased(models.TL)

#         in_progress_records = db.query(models.INPROGRESS).join(
#             TL_alias, TL_alias.Assigned_To == models.INPROGRESS.user_id
#         ).filter(
#             models.INPROGRESS.user_id == user_id,
#             models.INPROGRESS.start_time >= picked_date_start,
#             or_(
#                 models.INPROGRESS.end_time <= to_date_end,
#                 models.INPROGRESS.end_time.is_(None)  # Correct NULL check
#             ),
#             TL_alias.Assigned_To == user_id,  # Ensure correct assignment
#             TL_alias.type_of_activity == "Non-Chargeable",
#             TL_alias.status == 1
#         ).all()

#         total_nonchargeable_time = timedelta()

#         for record in in_progress_records:
#             if record.total_time:
#                 try:
#                     hours, minutes, seconds = map(int, record.total_time.split(':'))
#                     total_nonchargeable_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)
#                 except ValueError as e:
#                     print(f"Error parsing total_time for record {record.id}: {e}")

#         return total_nonchargeable_time

#     # Function to process records and calculate total time
#     def process_records(records, start_time_field, end_time_field, activity):
#         for record in records:
#             start_time = getattr(record, start_time_field)
#             end_time = getattr(record, end_time_field)

#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time as end_time for ongoing activities
#                 else:
#                     continue  # Ignore records that are not ongoing or not on the current date

#             # Get the username from the user table
#             user = db.query(models.User_table).filter(models.User_table.user_id == record.user_id).first()
#             member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'  # Safe fallback

#             # Calculate the time difference
#             time_diff = end_time - start_time

#             # Accumulate time per user and activity
#             user_times[activity][member_name] += time_diff

#     # Fetch and process records for different activities
#     process_records(db.query(models.BREAK).filter(
#         models.BREAK.break_time_start >= picked_date_start,
#         models.BREAK.break_time_start <= to_date_end
#     ).all(), 'break_time_start', 'break_time_end', 'break')

#     process_records(db.query(models.MEETING).filter(
#         models.MEETING.meeting_time_start >= picked_date_start,
#         models.MEETING.meeting_time_start <= to_date_end
#     ).all(), 'meeting_time_start', 'meeting_time_end', 'meeting')

#     process_records(db.query(models.CALL).filter(
#         models.CALL.call_time_start >= picked_date_start,
#         models.CALL.call_time_start <= to_date_end
#     ).all(), 'call_time_start', 'call_time_end', 'call')

#     process_records(db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.start_time >= picked_date_start,
#         models.INPROGRESS.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'in_progress')

#     process_records(db.query(models.WorkSession).filter(
#         models.WorkSession.start_time >= picked_date_start,
#         models.WorkSession.start_time <= to_date_end
#     ).all(), 'start_time', 'end_time', 'idealtime')

#     # Calculate completed and chargeable time after processing all records
#     for member_name in user_times['in_progress'].keys():
#         user_times['completed'][member_name] += get_completed_time(member_name, picked_date_start, to_date_end)
#         user_times['chargeable'][member_name] += get_chargeable_time(member_name, picked_date_start, to_date_end)
#         user_times['non-chargeable'][member_name] += get_nonchargeable_time(member_name, picked_date_start, to_date_end)

#     # Format the total time for each activity and user
#     formatted_total_time = {
#         member_name: {
#             'member_name': member_name,
#             'idealtime': str(user_times['idealtime'][member_name]).split('.')[0] or '00:00:00',
#             'in_progress': str(user_times['in_progress'][member_name]).split('.')[0] or '00:00:00',
#             'break': str(user_times['break'][member_name]).split('.')[0] or '00:00:00',
#             'call': str(user_times['call'][member_name]).split('.')[0] or '00:00:00',
#             'meeting': str(user_times['meeting'][member_name]).split('.')[0] or '00:00:00',
#             'completed': str(user_times['completed'][member_name]).split('.')[0] or '00:00:00',
#             'chargeable': str(user_times['chargeable'][member_name]).split('.')[0] or '00:00:00',
#             'non-chargeable': str(user_times['non-chargeable'][member_name]).split('.')[0] or '00:00:00',
#             'Total Chargeable and Non-Chargeable Time': str(
#                 user_times['chargeable'][member_name] +
#                 user_times['non-chargeable'][member_name]
#             ).split('.')[0] or '00:00:00',
#             'Total Time Taken': str(
#                 user_times['idealtime'][member_name] +
#                 user_times['in_progress'][member_name] +
#                 user_times['break'][member_name] +
#                 user_times['call'][member_name] +
#                 user_times['meeting'][member_name] +
#                 user_times['completed'][member_name]
#             ).split('.')[0] or '00:00:00'
#         } for member_name in user_times['idealtime']
#     }

#     return formatted_total_time


# from datetime import datetime, timedelta
# from collections import defaultdict
# from sqlalchemy.orm import Session

# def format_timedelta_to_str(delta: timedelta) -> str:
#     """Convert a timedelta to a string in HH:MM:SS format."""
#     total_seconds = int(delta.total_seconds())
#     hours, remainder = divmod(total_seconds, 3600)
#     minutes, seconds = divmod(remainder, 60)
#     return f"{hours:02}:{minutes:02}:{seconds:02}"

# def calculate_total_time(picked_date: str, to_date: str, db: Session) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     current_time = datetime.now()

#     # Initialize user times for each service
#     user_service_times = defaultdict(lambda: {
#         'in_progress': timedelta(),
#         'completed': timedelta(),
#         'chargeable': timedelta(),
#         'non-chargeable': timedelta(),
#     })

#     def get_completed_status(user_id, service_id):
#         """Check if the service is marked as completed in the TL table."""
#         completed_record = db.query(models.TL).filter(
#             models.TL.Assigned_To == user_id,
#             models.TL.Service_ID == service_id,
#             models.TL.work_status == 'Completed'
#         ).first()
#         return bool(completed_record)  # Return True if found

#     def process_in_progress_records(records):
#         """Process in-progress tasks and accumulate time."""
#         for record in records:
#             start_time = record.start_time
#             end_time = record.end_time or current_time  # Use current time for ongoing tasks
#             user_id = record.user_id
#             service_id = record.Service_ID

#             user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
#             member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

#             time_diff = end_time - start_time

#             # Check if the task is completed
#             is_completed = get_completed_status(user_id, service_id)

#             if is_completed:
#                 # Shift in-progress time to completed
#                 user_service_times[(member_name, service_id)]['completed'] += time_diff
#                 user_service_times[(member_name, service_id)]['in_progress'] = timedelta()  # Reset in-progress time
#             else:
#                 # Accumulate in-progress time for ongoing tasks
#                 user_service_times[(member_name, service_id)]['in_progress'] += time_diff

#             print(f"In-Progress Time for {member_name}, Service {service_id}: {time_diff}")

#     # Fetch and process in-progress records
#     in_progress_records = db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.start_time.between(picked_date_start, to_date_end)
#     ).all()
#     process_in_progress_records(in_progress_records)

#     # Format the total time for output
#     formatted_total_time = {
#         f"{member_name} - Service {service_id}": {
#             'in_progress': format_timedelta_to_str(times['in_progress']),
#             'completed': format_timedelta_to_str(times['completed']),
#             'chargeable': format_timedelta_to_str(times['chargeable']),
#             'non-chargeable': format_timedelta_to_str(times['non-chargeable']),
#         }
#         for (member_name, service_id), times in user_service_times.items()
#     }

#     print("Final Output:", formatted_total_time)  # Debug print

#     return formatted_total_time


# from datetime import datetime, timedelta
# from collections import defaultdict
# from sqlalchemy.orm import Session

# def format_timedelta_to_str(delta: timedelta) -> str:
#     """Convert a timedelta to a string in HH:MM:SS format."""
#     total_seconds = int(delta.total_seconds())
#     hours, remainder = divmod(total_seconds, 3600)
#     minutes, seconds = divmod(remainder, 60)
#     return f"{hours:02}:{minutes:02}:{seconds:02}"

# def calculate_total_time(picked_date: str, to_date: str, db: Session) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     current_time = datetime.now()

#     # Initialize combined times for each user
#     combined_user_times = defaultdict(lambda: {
#         'in_progress': timedelta(),
#         'completed': timedelta(),
#         'chargeable': timedelta(),
#         'non-chargeable': timedelta(),
#     })

#     def get_completed_status(user_id, service_id):
#         """Check if the service is marked as completed in the TL table."""
#         completed_record = db.query(models.TL).filter(
#             models.TL.Assigned_To == user_id,
#             models.TL.Service_ID == service_id,
#             models.TL.work_status == 'Completed'
#         ).first()
#         return bool(completed_record)  # Return True if found

#     def process_in_progress_records(records):
#         """Process in-progress tasks and accumulate time."""
#         for record in records:
#             start_time = record.start_time
#             end_time = record.end_time or current_time  # Use current time for ongoing tasks
#             user_id = record.user_id
#             service_id = record.Service_ID

#             user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
#             member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

#             time_diff = end_time - start_time

#             # Check if the task is completed
#             is_completed = get_completed_status(user_id, service_id)

#             if is_completed:
#                 # Shift in-progress time to completed
#                 combined_user_times[member_name]['completed'] += time_diff
#             else:
#                 # Accumulate in-progress time for ongoing tasks
#                 combined_user_times[member_name]['in_progress'] += time_diff

#             print(f"In-Progress Time for {member_name}, Service {service_id}: {time_diff}")

#     # Fetch and process in-progress records
#     in_progress_records = db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.start_time.between(picked_date_start, to_date_end)
#     ).all()
#     process_in_progress_records(in_progress_records)

#     # Format the total time for output
#     formatted_total_time = {
#         member_name: {
#             'in_progress': format_timedelta_to_str(times['in_progress']),
#             'completed': format_timedelta_to_str(times['completed']),
#             'chargeable': format_timedelta_to_str(times['chargeable']),
#             'non-chargeable': format_timedelta_to_str(times['non-chargeable']),
#         }
#         for member_name, times in combined_user_times.items()
#     }

#     print("Final Output:", formatted_total_time)  # Debug print

#     return formatted_total_time

# ------code work on oct23
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session, aliased

def format_timedelta_to_str(delta: timedelta) -> str:
    """Convert a timedelta to a string in HH:MM:SS format."""
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def get_chargeable_time(member_name: str, picked_date_start: datetime, to_date_end: datetime, db: Session) -> timedelta:
    """Calculate the total chargeable time for a user."""
    # Fetch the user based on the full name
    user = db.query(models.User_table).filter(
        (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
    ).first()

    if not user:
        print(f"User not found for member_name: {member_name}")
        return timedelta()  # Return zero if user not found

    user_id = user.user_id
    TL_alias = aliased(models.TL)

    # Query for in-progress chargeable records
    in_progress_records = db.query(models.INPROGRESS).join(
        TL_alias, TL_alias.Service_ID == models.INPROGRESS.Service_ID  # Ensure the join condition is appropriate
    ).filter(
        models.INPROGRESS.user_id == user_id,
        models.INPROGRESS.start_time >= picked_date_start,
        or_(
            models.INPROGRESS.end_time <= to_date_end,
            models.INPROGRESS.end_time.is_(None)  # Handle ongoing tasks
        ),
        TL_alias.type_of_activity == "CHARGABLE",
        TL_alias.status == 1  # Ensure the task is active
    ).all()

    total_chargeable_time = timedelta()

    # Process chargeable time records
    current_time = datetime.now()
    for record in in_progress_records:
        start_time = record.start_time
        end_time = record.end_time or current_time # Use current time for active sessions

        # Calculate the duration of each task
        time_diff = end_time - start_time
        total_chargeable_time += time_diff

    return total_chargeable_time


def get_nonchargeable_time(member_name, picked_date_start, to_date_end, db: Session) -> timedelta:
    """Calculate the total nonchargeable time for a user."""
    user = db.query(models.User_table).filter(
        (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
    ).first()

    if not user:
        print(f"User not found for member_name: {member_name}")
        return timedelta()  # Return zero if user not found

    user_id = user.user_id
    TL_alias = aliased(models.TL)

    in_progress_records = db.query(models.INPROGRESS).join(
        TL_alias, TL_alias.Assigned_To == models.INPROGRESS.user_id
    ).filter(
        models.INPROGRESS.user_id == user_id,
        models.INPROGRESS.start_time >= picked_date_start,
        or_(
            models.INPROGRESS.end_time <= to_date_end,
            models.INPROGRESS.end_time.is_(None)  # Handle ongoing tasks
        ),
        TL_alias.Assigned_To == user_id,
        TL_alias.type_of_activity == "Non-Chargeable",
        TL_alias.status == 1  # Ensure the task is active
    ).all()

    total_chargeable_time = timedelta()

    # Process chargeable time records
    current_time = datetime.now()
    for record in in_progress_records:
        start_time = record.start_time
        end_time = record.end_time or current_time  # Use current time for active sessions

        time_diff = end_time - start_time
        total_chargeable_time += time_diff

    return total_chargeable_time



def calculate_total_time(picked_date: str, to_date: str, db: Session) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")

    picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
    to_date_end = to_datett.replace(hour=23, minute=59, second=59)

    current_time = datetime.now()

    # Initialize combined times for each user
    combined_user_times = defaultdict(lambda: {
        'in_progress': timedelta(),
        'completed': timedelta(),
        'chargeable': timedelta(),
        'non-chargeable': timedelta(),
        'idealtime': timedelta(),
        'meeting': timedelta(),
        'call': timedelta(), 
        'break': timedelta(), 
    })

    

    def get_completed_status(user_id, service_id):
        """Check if the service is marked as completed in the TL table."""
        completed_record = db.query(models.TL).filter(
            models.TL.Assigned_To == user_id,
            models.TL.Service_ID == service_id,
            models.TL.work_status == 'Completed'
        ).first()
        return bool(completed_record)  # Return True if found

    def process_in_progress_records(records):
        """Process in-progress tasks and accumulate time."""
        for record in records:
            start_time = record.start_time
            end_time = record.end_time or current_time  # Use current time for ongoing tasks
            user_id = record.user_id
            service_id = record.Service_ID

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            time_diff = end_time - start_time

            # Check if the task is completed
            is_completed = get_completed_status(user_id, service_id)

            if is_completed:
                # Shift in-progress time to completed
                combined_user_times[member_name]['completed'] += time_diff
            else:
                # Accumulate in-progress time for ongoing tasks
                combined_user_times[member_name]['in_progress'] += time_diff
        

        # print(f"In-Progress Time for {member_name}, Service {service_id}: {time_diff}")

    # Fetch and process in-progress records
    in_progress_records = db.query(models.INPROGRESS).filter(
        models.INPROGRESS.start_time.between(picked_date_start, to_date_end)
    ).all()
    process_in_progress_records(in_progress_records)

    def process_work_sessions(records, combined_user_times):
        """Process work session records and accumulate ideal time."""
        for record in records:
            start_time = record.start_time
            end_time = record.end_time or datetime.now()  # Use current time if ongoing
            user_id = record.user_id

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            time_diff = end_time - start_time

            # Accumulate ideal time
            combined_user_times[member_name]['idealtime'] += time_diff

            print(f"Ideal Time for {member_name}: {time_diff}")

    # Fetch and process WorkSession records
    work_session_records = db.query(models.WorkSession).filter(
        models.WorkSession.start_time >= picked_date_start,
        models.WorkSession.start_time <= to_date_end
    ).all()

    process_work_sessions(work_session_records, combined_user_times)


    def process_meeting_records(records, combined_user_times):
        
        for record in records:
            meeting_start_time = record.meeting_time_start
            meeting_end_time = record.meeting_time_end or datetime.now()  # Use current time if ongoing
            user_id = record.user_id

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            time_diff = meeting_end_time - meeting_start_time

            # Accumulate meeting time
            combined_user_times[member_name]['meeting'] += time_diff

            print(f"Meeting Time for {member_name}: {time_diff}")


    # Fetch and process meeting records
    meeting_records = db.query(models.MEETING).filter(
        models.MEETING.meeting_time_start >= picked_date_start,
        models.MEETING.meeting_time_start <= to_date_end
    ).all()

    process_meeting_records(meeting_records, combined_user_times)

    def process_call_records(records, combined_user_times):
        """Process call records and accumulate call time."""
        for record in records:
            call_start_time = record.call_time_start
            call_end_time = record.call_time_end or datetime.now()  # Use current time if ongoing
            user_id = record.user_id

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            time_diff = call_end_time - call_start_time

            # Accumulate call time
            combined_user_times[member_name]['call'] += time_diff

            print(f"Call Time for {member_name}: {time_diff}")


    call_records = db.query(models.CALL).filter(
        models.CALL.call_time_start >= picked_date_start,
        models.CALL.call_time_start <= to_date_end
    ).all()

    process_call_records(call_records, combined_user_times)


    def process_break_records(records, combined_user_times):
        """Process break records and accumulate break time."""
        for record in records:
            break_start_time = record.break_time_start
            break_end_time = record.break_time_end or datetime.now()  # Use current time if ongoing
            user_id = record.user_id

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            time_diff = break_end_time - break_start_time

            # Accumulate break time
            combined_user_times[member_name]['break'] += time_diff

            print(f"Break Time for {member_name}: {time_diff}")

    # Fetch and process break records
    break_records = db.query(models.BREAK).filter(
        models.BREAK.break_time_start >= picked_date_start,
        models.BREAK.break_time_start <= to_date_end
    ).all()

    process_break_records(break_records, combined_user_times)

    for member_name in combined_user_times.keys():
        chargeable_time = get_chargeable_time(member_name, picked_date_start, to_date_end, db)
        combined_user_times[member_name]['chargeable'] += chargeable_time
        chargeable_time1 = get_nonchargeable_time(member_name, picked_date_start, to_date_end, db)
        combined_user_times[member_name]['chargeable'] += chargeable_time1

    # Format the total time for output
    formatted_total_time = {
        member_name: {
            'member_name': member_name,
            'idealtime': format_timedelta_to_str(times['idealtime']), 
            'in_progress': format_timedelta_to_str(times['in_progress']),
            'completed': format_timedelta_to_str(times['completed']),
            'meeting': format_timedelta_to_str(times['meeting']),
            'call': format_timedelta_to_str(times['call']),
            'chargeable': format_timedelta_to_str(times['chargeable']),
            'non-chargeable': format_timedelta_to_str(times['non-chargeable']),
            'break': format_timedelta_to_str(times['break']), 
            'Total Time Taken': str(
                    times['idealtime'] +
                    times['in_progress'] +
                    times['break'] +
                    times['call'] +
                    times['meeting'] +
                    times['completed']
                ).split('.')[0] or '00:00:00' ,
            'Total Chargeable and Non-Chargeable Time': format_timedelta_to_str(
                    combined_user_times[member_name]['chargeable'] + combined_user_times[member_name]['non-chargeable']
                )
        }
        for member_name, times in combined_user_times.items()
    }

    print("Final Output:", formatted_total_time)  # Debug print

    return formatted_total_time



# def calculate_total_time_work_session(picked_date: str, to_date: str, db: Session) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     work_session_records = db.query(models.WorkSession).filter(
#         models.WorkSession.start_time >= picked_date_start,
#         models.WorkSession.start_time <= to_date_end
#     ).all()

    

#     user_total_time = defaultdict(timedelta)

#     current_time = datetime.now()

#     for record in work_session_records:
#         start_time = record.start_time

#         if record.end_time:
#             end_time = record.end_time
#             user_total_time[record.user_id] += (end_time - start_time)
#         else:
#             if start_time.date() == current_time.date():
#                 end_time = current_time
#                 user_total_time[record.user_id] += (end_time - start_time)
#             elif start_time.date() < current_time.date():
#                 continue

#     formatted_total_time = {
#         user_id: str(work_total_time).split('.')[0] for user_id, work_total_time in user_total_time.items()
#     }

#     return formatted_total_time



from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session, aliased

def format_timedelta_to_str(delta: timedelta) -> str:
    """Convert a timedelta to a string in HH:MM:SS format."""
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def get_chargeable_time(member_name: str, picked_date_start: datetime, to_date_end: datetime, db: Session) -> timedelta:
    """Calculate the total chargeable time for a user."""
    # Fetch the user based on the full name
    user = db.query(models.User_table).filter(
        (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
    ).first()

    if not user:
        print(f"User not found for member_name: {member_name}")
        return timedelta()  # Return zero if user not found

    user_id = user.user_id
    TL_alias = aliased(models.TL)

    # Query for in-progress chargeable records
    in_progress_records = db.query(models.INPROGRESS).join(
        TL_alias, TL_alias.Service_ID == models.INPROGRESS.Service_ID  # Ensure the join condition is appropriate
    ).filter(
        models.INPROGRESS.user_id == user_id,
        models.INPROGRESS.start_time >= picked_date_start,
        or_(
            models.INPROGRESS.end_time <= to_date_end,
            models.INPROGRESS.end_time.is_(None)  # Handle ongoing tasks
        ),
        TL_alias.type_of_activity == "CHARGABLE",
        TL_alias.status == 1  # Ensure the task is active
    ).all()

    total_chargeable_time = timedelta()

    # Process chargeable time records
    current_time = datetime.now()
    for record in in_progress_records:
        start_time = record.start_time
        end_time = record.end_time
        
        # Check if end_time is None
        if end_time is None:
            # Use current time if start_time is from today
            if start_time.date() == current_time.date():
                end_time = current_time  # Use current time as end_time for ongoing activities
            else:
                continue  # Skip records that are not ongoing
            
        # Calculate time difference
        time_diff = end_time - start_time
        total_chargeable_time += time_diff

    return total_chargeable_time


def get_nonchargeable_time(member_name, picked_date_start, to_date_end, db: Session) -> timedelta:
    """Calculate the total nonchargeable time for a user."""
    user = db.query(models.User_table).filter(
        (models.User_table.firstname + ' ' + models.User_table.lastname) == member_name
    ).first()

    if not user:
        print(f"User not found for member_name: {member_name}")
        return timedelta()  # Return zero if user not found

    user_id = user.user_id
    TL_alias = aliased(models.TL)

    in_progress_records = db.query(models.INPROGRESS).join(
        TL_alias, TL_alias.Assigned_To == models.INPROGRESS.user_id
    ).filter(
        models.INPROGRESS.user_id == user_id,
        models.INPROGRESS.start_time >= picked_date_start,
        or_(
            models.INPROGRESS.end_time <= to_date_end,
            models.INPROGRESS.end_time.is_(None)  # Handle ongoing tasks
        ),
        TL_alias.Assigned_To == user_id,
        TL_alias.type_of_activity == "Non-Chargeable",
        TL_alias.status == 1  # Ensure the task is active
    ).all()

    total_chargeable_time = timedelta()

    # Process chargeable time records
    current_time = datetime.now()
    for record in in_progress_records:
        start_time = record.start_time
        end_time = record.end_time
        
        # Check if end_time is None
        if end_time is None:
            # Use current time if start_time is from today
            if start_time.date() == current_time.date():
                end_time = current_time  # Use current time as end_time for ongoing activities
            else:
                continue  # Skip records that are not ongoing
            
        # Calculate time difference
        time_diff = end_time - start_time
        total_chargeable_time += time_diff

    return total_chargeable_time



def calculate_total_time1ss(picked_date: str, to_date: str, db: Session) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")

    picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
    to_date_end = to_datett.replace(hour=23, minute=59, second=59)

    current_time = datetime.now()

    # Initialize combined times for each user
    combined_user_times = defaultdict(lambda: {
        'in_progress': timedelta(),
        'completed': timedelta(),
        'chargeable': timedelta(),
        'non-chargeable': timedelta(),
        'idealtime': timedelta(),
        'meeting': timedelta(),
        'call': timedelta(), 
        'break': timedelta(), 
    })

    

    def get_completed_status(user_id, service_id):
        """Check if the service is marked as completed in the TL table."""
        completed_record = db.query(models.TL).filter(
            models.TL.Assigned_To == user_id,
            models.TL.Service_ID == service_id,
            models.TL.work_status == 'Completed'
        ).first()
        return bool(completed_record)  # Return True if found

    def process_in_progress_records(records):
        """Process in-progress tasks and accumulate time."""
        for record in records:
            start_time = record.start_time
            end_time = record.end_time or current_time  # Use current time for ongoing tasks
            user_id = record.user_id
            service_id = record.Service_ID

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            # Use current time if end_time is empty
        

            time_diff = end_time - start_time

            # Check if the task is completed
            is_completed = get_completed_status(user_id, service_id)

            if is_completed:
                # Shift in-progress time to completed
                combined_user_times[member_name]['completed'] += time_diff
            else:
                # Accumulate in-progress time for ongoing tasks
                combined_user_times[member_name]['in_progress'] += time_diff
        

        # print(f"In-Progress Time for {member_name}, Service {service_id}: {time_diff}")

    # Fetch and process in-progress records
    # in_progress_records = db.query(models.INPROGRESS).filter(
    #     models.INPROGRESS.start_time.between(picked_date_start, to_date_end)
    # ).all()
    # process_in_progress_records(in_progress_records)
    # Querying in-progress records with adjusted filtering logic
    in_progress_records = db.query(models.INPROGRESS).filter(
        models.INPROGRESS.start_time >= picked_date_start,  # Start time should be greater than or equal to picked_date_start
        models.INPROGRESS.start_time <= to_date_end  # Start time should be less than or equal to to_date_end
    ).all()

    # Process the fetched in-progress records
    process_in_progress_records(in_progress_records)


    def process_work_sessions(records, combined_user_times):
        """Process work session records and accumulate ideal time."""
        for record in records:
            start_time = record.start_time
            end_time = record.end_time or datetime.now()  # Use current time if ongoing
            user_id = record.user_id

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            time_diff = end_time - start_time

            # Accumulate ideal time
            combined_user_times[member_name]['idealtime'] += time_diff

            print(f"Ideal Time for {member_name}: {time_diff}")

    # Fetch and process WorkSession records
    work_session_records = db.query(models.WorkSession).filter(
        models.WorkSession.start_time >= picked_date_start,
        models.WorkSession.start_time <= to_date_end
    ).all()

    process_work_sessions(work_session_records, combined_user_times)


    def process_meeting_records(records, combined_user_times):
        
        for record in records:
            meeting_start_time = record.meeting_time_start
            meeting_end_time = record.meeting_time_end or datetime.now()  # Use current time if ongoing
            user_id = record.user_id

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            time_diff = meeting_end_time - meeting_start_time

            # Accumulate meeting time
            combined_user_times[member_name]['meeting'] += time_diff

            print(f"Meeting Time for {member_name}: {time_diff}")


    # Fetch and process meeting records
    meeting_records = db.query(models.MEETING).filter(
        models.MEETING.meeting_time_start >= picked_date_start,
        models.MEETING.meeting_time_start <= to_date_end
    ).all()

    process_meeting_records(meeting_records, combined_user_times)

    def process_call_records(records, combined_user_times):
        """Process call records and accumulate call time."""
        for record in records:
            call_start_time = record.call_time_start
            call_end_time = record.call_time_end or datetime.now()  # Use current time if ongoing
            user_id = record.user_id

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            time_diff = call_end_time - call_start_time

            # Accumulate call time
            combined_user_times[member_name]['call'] += time_diff

            print(f"Call Time for {member_name}: {time_diff}")


    call_records = db.query(models.CALL).filter(
        models.CALL.call_time_start >= picked_date_start,
        models.CALL.call_time_start <= to_date_end
    ).all()

    process_call_records(call_records, combined_user_times)


    def process_break_records(records, combined_user_times):
        """Process break records and accumulate break time."""
        for record in records:
            break_start_time = record.break_time_start
            break_end_time = record.break_time_end or datetime.now()  # Use current time if ongoing
            user_id = record.user_id

            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()
            member_name = f"{user.firstname} {user.lastname}" if user else 'Unknown User'

            time_diff = break_end_time - break_start_time

            # Accumulate break time
            combined_user_times[member_name]['break'] += time_diff

            print(f"Break Time for {member_name}: {time_diff}")

    # Fetch and process break records
    break_records = db.query(models.BREAK).filter(
        models.BREAK.break_time_start >= picked_date_start,
        models.BREAK.break_time_start <= to_date_end
    ).all()

    process_break_records(break_records, combined_user_times)

    final_output = []
    current_day = datetime.now()
    # Iterate over the combined_user_times dictionary
    for member_name, times in combined_user_times.items():
        # Get chargeable and non-chargeable times separately
        chargeable_time = get_chargeable_time(member_name, picked_date_start, to_date_end, db)
        non_chargeable_time = get_nonchargeable_time(member_name, picked_date_start, to_date_end, db)

        # Accumulate the chargeable and non-chargeable times in their respective fields
        combined_user_times[member_name]['chargeable'] += chargeable_time
        combined_user_times[member_name]['non-chargeable'] += non_chargeable_time

        # Calculate Total Time Taken
        total_time_taken = (
            times['idealtime'] + times['in_progress'] + times['break'] +
            times['call'] + times['meeting'] + times['completed']
        )

        # Calculate Total Chargeable and Non-Chargeable Time
        total_chargeable_non_chargeable = (
            combined_user_times[member_name]['chargeable'] +
            combined_user_times[member_name]['non-chargeable']
        )

        
        # Append formatted result for the current member
        final_output.append({
            'member_name': member_name,
            'idealtime': format_timedelta_to_str(times['idealtime']),
            'date': current_day.strftime("%Y-%m-%d"),
            'in_progress': format_timedelta_to_str(times['in_progress']),
            'completed': format_timedelta_to_str(times['completed']),
            'meeting': format_timedelta_to_str(times['meeting']),
            'call': format_timedelta_to_str(times['call']),
            'chargeable': format_timedelta_to_str(combined_user_times[member_name]['chargeable']),
            'non-chargeable': format_timedelta_to_str(combined_user_times[member_name]['non-chargeable']),
            'break': format_timedelta_to_str(times['break']),
            'Total Time Taken': format_timedelta_to_str(total_time_taken),
            'Total Chargeable and Non-Chargeable Time': format_timedelta_to_str(total_chargeable_non_chargeable)
        })

    print("Final Output:", final_output)  # Debug print
    return final_output


# --------------------------------------------------------------IDEAL TIME CODE END


# ---------------------------------logout status change to Hold- new function.............start
def get_current_time_str_login() -> str:
    """Get the current time as a string formatted for database storage with timezone."""
    current_time = datetime.now()
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


# def get_current_time_str() -> str:
#     """Get the current time as a string formatted for database storage without timezone."""
#     current_time = datetime.now()
#     return current_time.strftime('%Y-%m-%d %H:%M:%S')


def get_current_time_str_with_offset(seconds: int) -> str:
    """Get the current time plus an offset in seconds as a string formatted for database storage."""
    current_time = datetime.now() + timedelta(seconds=seconds)
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


# def is_work_in_progress(db: Session, user_id: int) -> bool:
#     """Check if work is in progress or on break for a given user with a valid Service_ID."""
#     tl_entry = db.query(models.TL).filter(
#         models.TL.assigned_to == user_id,
#         models.TL.work_status.in_(["Work in Progress", "Break", "Clarification Call", "Meeting", "Hold", "End Of Day", "Not Picked"]),
#     ).order_by(models.TL.service_id).all()
    
#     return bool(tl_entry)  # Return True if there are entries, False otherwise


def is_work_in_progress(db: Session, user_id: int) -> bool:
    """Check if work is in progress or on break for a given user with a valid Service_ID."""
    tl_entry = db.query(models.TL).filter(
        models.TL.Assigned_To == user_id,
        models.TL.work_status.in_(["Work in Progress", "Break", "Clarification Call", "Meeting", "Hold", "End Of Day", "Not Picked"]),
    ).order_by(models.TL.Service_ID).all()
    
    return bool(tl_entry) 

def calculate_total_times(start_time: datetime, end_time: datetime) -> str:
    """Calculate the total time worked between start and end times."""
    try:
        # Ensure start_time and end_time are datetime objects
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        total_time_seconds = (end_time - start_time).total_seconds()
        hours, remainder = divmod(total_time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_total_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        return formatted_total_time
    except Exception as e:
        logging.error(f"Error calculating total time: {e}")
        return '0:00:00'

from sqlalchemy import or_  # Import or_



from datetime import datetime, timedelta
from sqlalchemy import or_

def get_current_time_str() -> str:
    """Get the current time as a string formatted for database storage without timezone."""
    current_time = datetime.now()
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


def calculate_total_times(start_time: datetime, end_time: datetime) -> str:
    """Calculate the total time worked between start and end times."""
    try:
        # Ensure start_time and end_time are datetime objects
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        total_time_seconds = (end_time - start_time).total_seconds()
        hours, remainder = divmod(total_time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_total_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        return formatted_total_time
    except Exception as e:
        logging.error(f"Error calculating total time: {e}")
        return '0:00:00'


def logout_time_add(logouttime: str, userid: int, db: Session):
    logging.info(f"Fetching records for user ID: {userid}")

    all_records = db.query(models.TL).filter(
        models.TL.Assigned_To == userid,
        models.TL.work_status.in_(["Break", "Work in Progress", "Clarification Call", "Meeting", "End Of Day", "Hold", "Not Picked", "Completed"])
    ).order_by(models.TL.Service_ID).all()

    logging.info(f"Fetched records: {[record.work_status for record in all_records]}")

    try:
        # Get the latest login entry for the user
        login_entry = db.query(models.login_time).filter(models.login_time.userid == userid).order_by(models.login_time.login_id.desc()).first()

        # Check for "End Of Day" status
        if any(record.work_status == "End Of Day" for record in all_records):
            tl_entry = next(record for record in all_records if record.work_status == "End Of Day")
            logging.info(f"TL entry found for user {userid}, Service_ID: {tl_entry.Service_ID}")

            last_work_session = db.query(models.WorkSession).filter(
                models.WorkSession.user_id == userid,
                models.WorkSession.end_time.is_(None)  # Check only for NULL
            ).order_by(models.WorkSession.id.desc()).first()

            if last_work_session:
                end_time_str = get_current_time_str()  # Adjust end time if necessary
                last_work_session.end_time = end_time_str
                db.commit()
                logging.info(f"End time updated for WorkSession for user {userid}")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
                last_work_session.total_time_worked = total_worked_time
                db.commit()
                logging.info(f"Total working time updated for WorkSession for user {userid}")

            # Update logout time for active login session
            if login_entry:
                login_entry.logout_time = get_current_time_str()
                db.commit()
                logging.info(f"Login end time updated for user {userid}")
            else:
                logging.warning(f"No active login entry found for user {userid}")

        # Check for "Work in Progress" status
        elif any(record.work_status == "Work in Progress" for record in all_records):
            logging.info(f"'Work in Progress' found for user {userid}. Updating status to 'Hold'.")

            # Change the work status from "Work in Progress" to "Hold"
            tl_entry = next(record for record in all_records if record.work_status == "Work in Progress")
            tl_entry.work_status = "Hold"
            db.commit()
            logging.info(f"Work status updated to 'Hold' for user {userid}.")

            # Find the last INPROGRESS entry for the user
            in_progress_entry = (
                db.query(models.INPROGRESS)
                .filter(models.INPROGRESS.user_id == userid, models.INPROGRESS.Service_ID == tl_entry.Service_ID, models.INPROGRESS.end_time.is_(None))
                .order_by(models.INPROGRESS.id.desc())
                .first()
            )

            if in_progress_entry:
                # Update end_time in INPROGRESS table
                in_progress_entry.end_time = datetime.now()  # Set end time to current time
                db.commit()
                logging.info(f"End time updated for INPROGRESS for user {userid}.")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(in_progress_entry.start_time, in_progress_entry.end_time)
                in_progress_entry.total_time = total_worked_time  # Assuming total_time is stored as a string
                db.commit()
                logging.info(f"Total working time updated for INPROGRESS for user {userid}.")

            # Add a new record in the HOLD table with the start time as the current time
            hold_record = models.HOLD(
                Service_ID=tl_entry.Service_ID,
                user_id=userid,
                remarks="WL to H",
                hold_time_start=datetime.now(),  # Use the current time
            )
            db.add(hold_record)
            db.commit()
            logging.info(f"New HOLD record added for user {userid}.")

            # Add a new record in the WorkSession table with the start time as the current time
            work_session_record = models.WorkSession(
                user_id=userid,
                start_time=get_current_time_str(),  # Use the current time
            )
            db.add(work_session_record)
            db.commit()
            logging.info(f"New WorkSession record added for user {userid}.")

            last_work_session = db.query(models.WorkSession).filter(
                models.WorkSession.user_id == userid,
                models.WorkSession.end_time.is_(None)  # Check only for NULL
            ).order_by(models.WorkSession.id.desc()).first()

            if last_work_session:
                end_time_str = get_current_time_str()  # Adjust end time if necessary
                last_work_session.end_time = end_time_str
                db.commit()
                logging.info(f"End time updated for WorkSession for user {userid}")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
                last_work_session.total_time_worked = total_worked_time
                db.commit()
                logging.info(f"Total working time updated for WorkSession for user {userid}")

            # Update logout time for active login session
            if login_entry:
                login_entry.logout_time = get_current_time_str()
                db.commit()
                logging.info(f"Login end time updated for user {userid}")
            else:
   
                logging.warning(f"No active login entry found for user {userid}")


        elif any(record.work_status == "Clarification Call" for record in all_records):
            logging.info(f"'Clarification Call' found for user {userid}. Updating status to 'Hold'.")

            # Change the work status from "Work in Progress" to "Hold"
            tl_entry = next(record for record in all_records if record.work_status == "Clarification Call")
            tl_entry.work_status = "Hold"
            db.commit()
            logging.info(f"Work status updated to 'Hold' for user {userid}.")

            # Find the last Clarification Call entry for the user
            call_entry = (
                db.query(models.CALL)
                .filter(models.CALL.user_id == userid, models.CALL.Service_ID == tl_entry.Service_ID, models.CALL.call_time_end.is_(None))
                .order_by(models.CALL.id.desc())
                .first()
            )

            if call_entry:
                # Update end_time in CALL table
                call_entry.call_time_end = datetime.now()  # Set end time to current time
                db.commit()
                logging.info(f"End time updated for CALL for user {userid}.")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(call_entry.call_time_start, call_entry.call_time_end)
                call_entry.call_total_time = total_worked_time  # Assuming total_time is stored as a string
                db.commit()
                logging.info(f"Total working time updated for CALL for user {userid}.")

            # Add a new record in the HOLD table with the start time as the current time
            hold_record = models.HOLD(
                Service_ID=tl_entry.Service_ID,
                user_id=userid,
                remarks="CL to H",
                hold_time_start=datetime.now(),  # Use the current time
            )
            db.add(hold_record)
            db.commit()
            logging.info(f"New HOLD record added for user {userid}.")

            # Add a new record in the WorkSession table with the start time as the current time
            work_session_record = models.WorkSession(
                user_id=userid,
                start_time=get_current_time_str(),  # Use the current time
            )
            db.add(work_session_record)
            db.commit()
            logging.info(f"New WorkSession record added for user {userid}.")

            last_work_session = db.query(models.WorkSession).filter(
                models.WorkSession.user_id == userid,
                models.WorkSession.end_time.is_(None)  # Check only for NULL
            ).order_by(models.WorkSession.id.desc()).first()

            if last_work_session:
                end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
                last_work_session.end_time = end_time_str
                db.commit()
                logging.info(f"End time updated for WorkSession for user {userid}")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
                last_work_session.total_time_worked = total_worked_time
                db.commit()
                logging.info(f"Total working time updated for WorkSession for user {userid}")

            # Check for an active login session for the user
            login_entry = (
                db.query(models.login_time)
                .filter(
                    models.login_time.userid == userid,
                    or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
                )
                .order_by(models.login_time.login_id.desc())
                .first()
            )

            # Update the logout_time for the active login session
            if login_entry:
                logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
                logging.info(f"Logout time being set: {logouttime}")
                login_entry.logout_time = logouttime
                try:
                    db.commit()
                    logging.info(f"Login end time updated for user {userid}")
                except Exception as e:
                    db.rollback()  # Rollback on error
                    logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
            else:
                logging.warning(f"No active login entry found for user {userid}")


        elif any(record.work_status == "Break" for record in all_records):
            logging.info(f"'Break' found for user {userid}. Updating status to 'Hold'.")

            # Change the work status from "Work in Progress" to "Hold"
            tl_entry = next(record for record in all_records if record.work_status == "Break")
            tl_entry.work_status = "Hold"
            db.commit()
            logging.info(f"Work status updated to 'Hold' for user {userid}.")

            # Find the last Break entry for the user
            break_entry = (
                db.query(models.BREAK)
                .filter(models.BREAK.user_id == userid, models.BREAK.Service_ID == tl_entry.Service_ID, models.BREAK.break_time_end.is_(None))
                .order_by(models.BREAK.id.desc())
                .first()
            )

            if break_entry:
                # Update end_time in BREAK table
                break_entry.break_time_end = datetime.now()  # Set end time to current time
                db.commit()
                logging.info(f"End time updated for BREAK for user {userid}.")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(break_entry.break_time_start, break_entry.break_time_end)
                break_entry.break_total_time = total_worked_time  # Assuming total_time is stored as a string
                db.commit()
                logging.info(f"Total working time updated for BREAK for user {userid}.")

            # Add a new record in the HOLD table with the start time as the current time
            hold_record = models.HOLD(
                Service_ID=tl_entry.Service_ID,
                user_id=userid,
                remarks="BL to H",
                hold_time_start=datetime.now(),  # Use the current time
            )
            db.add(hold_record)
            db.commit()
            logging.info(f"New HOLD record added for user {userid}.")

            # Add a new record in the WorkSession table with the start time as the current time
            work_session_record = models.WorkSession(
                user_id=userid,
                start_time=get_current_time_str(),  # Use the current time
            )
            db.add(work_session_record)
            db.commit()
            logging.info(f"New WorkSession record added for user {userid}.")

            last_work_session = db.query(models.WorkSession).filter(
                models.WorkSession.user_id == userid,
                models.WorkSession.end_time.is_(None)  # Check only for NULL
            ).order_by(models.WorkSession.id.desc()).first()

            if last_work_session:
                end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
                last_work_session.end_time = end_time_str
                db.commit()
                logging.info(f"End time updated for WorkSession for user {userid}")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
                last_work_session.total_time_worked = total_worked_time
                db.commit()
                logging.info(f"Total working time updated for WorkSession for user {userid}")

            # Check for an active login session for the user
            login_entry = (
                db.query(models.login_time)
                .filter(
                    models.login_time.userid == userid,
                    or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
                )
                .order_by(models.login_time.login_id.desc())
                .first()
            )

            # Update the logout_time for the active login session
            if login_entry:
                logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
                logging.info(f"Logout time being set: {logouttime}")
                login_entry.logout_time = logouttime
                try:
                    db.commit()
                    logging.info(f"Login end time updated for user {userid}")
                except Exception as e:
                    db.rollback()  # Rollback on error
                    logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
            else:
                logging.warning(f"No active login entry found for user {userid}")

        
        elif any(record.work_status == "Meeting" for record in all_records):
            logging.info(f"'Meeting' found for user {userid}. Updating status to 'Hold'.")

            # Change the work status from "Work in Progress" to "Hold"
            tl_entry = next(record for record in all_records if record.work_status == "Meeting")
            tl_entry.work_status = "Hold"
            db.commit()
            logging.info(f"Work status updated to 'Hold' for user {userid}.")

            # Find the last Meeting entry for the user
            meeting_entry = (
                db.query(models.MEETING)
                .filter(models.MEETING.user_id == userid, models.MEETING.Service_ID == tl_entry.Service_ID, models.MEETING.meeting_time_end.is_(None))
                .order_by(models.MEETING.id.desc())
                .first()
            )

            if meeting_entry:
                # Update end_time in MEETING table
                meeting_entry.meeting_time_end = datetime.now()  # Set end time to current time
                db.commit()
                logging.info(f"End time updated for MEETING for user {userid}.")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(meeting_entry.meeting_time_start, meeting_entry.meeting_time_end)
                meeting_entry.meet_total_time = total_worked_time  # Assuming total_time is stored as a string
                db.commit()
                logging.info(f"Total working time updated for MEETING for user {userid}.")

            # Add a new record in the HOLD table with the start time as the current time
            hold_record = models.HOLD(
                Service_ID=tl_entry.Service_ID,
                user_id=userid,
                remarks="ML to H",
                hold_time_start=datetime.now(),  # Use the current time
            )
            db.add(hold_record)
            db.commit()
            logging.info(f"New HOLD record added for user {userid}.")

            # Add a new record in the WorkSession table with the start time as the current time
            work_session_record = models.WorkSession(
                user_id=userid,
                start_time=get_current_time_str(),  # Use the current time
            )
            db.add(work_session_record)
            db.commit()
            logging.info(f"New WorkSession record added for user {userid}.")

            last_work_session = db.query(models.WorkSession).filter(
                models.WorkSession.user_id == userid,
                models.WorkSession.end_time.is_(None)  # Check only for NULL
            ).order_by(models.WorkSession.id.desc()).first()

            if last_work_session:
                end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
                last_work_session.end_time = end_time_str
                db.commit()
                logging.info(f"End time updated for WorkSession for user {userid}")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
                last_work_session.total_time_worked = total_worked_time
                db.commit()
                logging.info(f"Total working time updated for WorkSession for user {userid}")

            # Check for an active login session for the user
            login_entry = (
                db.query(models.login_time)
                .filter(
                    models.login_time.userid == userid,
                    or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
                )
                .order_by(models.login_time.login_id.desc())
                .first()
            )

            # Update the logout_time for the active login session
            if login_entry:
                logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
                logging.info(f"Logout time being set: {logouttime}")
                login_entry.logout_time = logouttime
                try:
                    db.commit()
                    logging.info(f"Login end time updated for user {userid}")
                except Exception as e:
                    db.rollback()  # Rollback on error
                    logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
            else:
                logging.warning(f"No active login entry found for user {userid}")

        elif any(record.work_status == "Hold" for record in all_records):
            tl_entry = next(record for record in all_records if record.work_status == "Hold")
            logging.info(f"TL entry found for user {userid}, Service_ID: {tl_entry.Service_ID}")

            last_work_session = db.query(models.WorkSession).filter(
                models.WorkSession.user_id == userid,
                models.WorkSession.end_time.is_(None)  # Check only for NULL
            ).order_by(models.WorkSession.id.desc()).first()

            if last_work_session:
                end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
                last_work_session.end_time = end_time_str
                db.commit()
                logging.info(f"End time updated for WorkSession for user {userid}")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
                last_work_session.total_time_worked = total_worked_time
                db.commit()
                logging.info(f"Total working time updated for WorkSession for user {userid}")

            # Check for an active login session for the user
            login_entry = (
                db.query(models.login_time)
                .filter(
                    models.login_time.userid == userid,
                    or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
                )
                .order_by(models.login_time.login_id.desc())
                .first()
            )

            # Update the logout_time for the active login session
            if login_entry:
                logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
                logging.info(f"Logout time being set: {logouttime}")
                login_entry.logout_time = logouttime
                try:
                    db.commit()
                    logging.info(f"Login end time updated for user {userid}")
                except Exception as e:
                    db.rollback()  # Rollback on error
                    logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
            else:
                logging.warning(f"No active login entry found for user {userid}")

        
        elif any(record.work_status == "Not Picked" for record in all_records):
            tl_entry = next(record for record in all_records if record.work_status == "Not Picked")
            logging.info(f"TL entry found for user {userid}, Service_ID: {tl_entry.Service_ID}")

            last_work_session = db.query(models.WorkSession).filter(
                models.WorkSession.user_id == userid,
                models.WorkSession.end_time.is_(None)  # Check only for NULL
            ).order_by(models.WorkSession.id.desc()).first()

            if last_work_session:
                end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
                last_work_session.end_time = end_time_str
                db.commit()
                logging.info(f"End time updated for WorkSession for user {userid}")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
                last_work_session.total_time_worked = total_worked_time
                db.commit()
                logging.info(f"Total working time updated for WorkSession for user {userid}")

            # Check for an active login session for the user
            login_entry = (
                db.query(models.login_time)
                .filter(
                    models.login_time.userid == userid,
                    or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
                )
                .order_by(models.login_time.login_id.desc())
                .first()
            )

            # Update the logout_time for the active login session
            if login_entry:
                logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
                logging.info(f"Logout time being set: {logouttime}")
                login_entry.logout_time = logouttime
                try:
                    db.commit()
                    logging.info(f"Login end time updated for user {userid}")
                except Exception as e:
                    db.rollback()  # Rollback on error
                    logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
            else:
                logging.warning(f"No active login entry found for user {userid}")

        
        elif any(record.work_status == "Completed" for record in all_records):
            tl_entry = next(record for record in all_records if record.work_status == "Completed")
            logging.info(f"TL entry found for user {userid}, Service_ID: {tl_entry.Service_ID}")

            last_work_session = db.query(models.WorkSession).filter(
                models.WorkSession.user_id == userid,
                models.WorkSession.end_time.is_(None)  # Check only for NULL
            ).order_by(models.WorkSession.id.desc()).first()

            if last_work_session:
                end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
                last_work_session.end_time = end_time_str
                db.commit()
                logging.info(f"End time updated for WorkSession for user {userid}")

                # Calculate the total working time (end_time - start_time)
                total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
                last_work_session.total_time_worked = total_worked_time
                db.commit()
                logging.info(f"Total working time updated for WorkSession for user {userid}")

            # Check for an active login session for the user
            login_entry = (
                db.query(models.login_time)
                .filter(
                    models.login_time.userid == userid,
                    or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
                )
                .order_by(models.login_time.login_id.desc())
                .first()
            )

            # Update the logout_time for the active login session
            if login_entry:
                logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
                logging.info(f"Logout time being set: {logouttime}")
                login_entry.logout_time = logouttime
                try:
                    db.commit()
                    logging.info(f"Login end time updated for user {userid}")
                except Exception as e:
                    db.rollback()  # Rollback on error
                    logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
            else:
                logging.warning(f"No active login entry found for user {userid}")

    except Exception as e:
        db.rollback()  # Rollback on error
        logging.error(f"Error processing logout for user {userid}: {str(e)}")



# def logout_time_add(logouttime: str, userid: int, db: Session):
#     logging.info(f"Fetching records for user ID: {userid}")

#     all_records = db.query(models.TL).filter(
#         models.TL.Assigned_To == userid,
#         models.TL.work_status.in_(["Break", "Work in Progress", "Clarification Call", "Meeting","End Of Day","Hold", "Not Picked","Completed"])
#     ).order_by(models.TL.Service_ID).all()

#     logging.info(f"Fetched records: {[record.work_status for record in all_records]}")

#     try:
#         # Get the latest login entry for the user
#         login_entry = db.query(models.login_time).filter(models.login_time.userid == userid).order_by(models.login_time.login_id.desc()).first()

#         if any(record.work_status == "End Of Day" for record in all_records):
#             tl_entry = next(record for record in all_records if record.work_status == "End Of Day")
#             logging.info(f"TL entry found for user {userid}, Service_ID: {tl_entry.Service_ID}")

#             last_work_session = db.query(models.WorkSession).filter(
#                 models.WorkSession.user_id == userid,
#                 models.WorkSession.end_time.is_(None)  # Check only for NULL
#             ).order_by(models.WorkSession.id.desc()).first()

#             if last_work_session:
#                 end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
#                 last_work_session.end_time = end_time_str
#                 db.commit()
#                 logging.info(f"End time updated for WorkSession for user {userid}")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
#                 last_work_session.total_time_worked = total_worked_time
#                 db.commit()
#                 logging.info(f"Total working time updated for WorkSession for user {userid}")

#             # Check for an active login session for the user
#             login_entry = (
#                 db.query(models.login_time)
#                 .filter(
#                     models.login_time.userid == userid,
#                     or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
#                 )
#                 .order_by(models.login_time.login_id.desc())
#                 .first()
#             )

#             # Update the logout_time for the active login session
#             if login_entry:
#                 logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
#                 logging.info(f"Logout time being set: {logouttime}")
#                 login_entry.logout_time = logouttime
#                 try:
#                     db.commit()
#                     logging.info(f"Login end time updated for user {userid}")
#                 except Exception as e:
#                     db.rollback()  # Rollback on error
#                     logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
#             else:
#                 logging.warning(f"No active login entry found for user {userid}")


#         elif any(record.work_status == "Hold" for record in all_records):
#             tl_entry = next(record for record in all_records if record.work_status == "Hold")
#             logging.info(f"TL entry found for user {userid}, Service_ID: {tl_entry.Service_ID}")

#             last_work_session = db.query(models.WorkSession).filter(
#                 models.WorkSession.user_id == userid,
#                 models.WorkSession.end_time.is_(None)  # Check only for NULL
#             ).order_by(models.WorkSession.id.desc()).first()

#             if last_work_session:
#                 end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
#                 last_work_session.end_time = end_time_str
#                 db.commit()
#                 logging.info(f"End time updated for WorkSession for user {userid}")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
#                 last_work_session.total_time_worked = total_worked_time
#                 db.commit()
#                 logging.info(f"Total working time updated for WorkSession for user {userid}")

#             # Check for an active login session for the user
#             login_entry = (
#                 db.query(models.login_time)
#                 .filter(
#                     models.login_time.userid == userid,
#                     or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
#                 )
#                 .order_by(models.login_time.login_id.desc())
#                 .first()
#             )

#             # Update the logout_time for the active login session
#             if login_entry:
#                 logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
#                 logging.info(f"Logout time being set: {logouttime}")
#                 login_entry.logout_time = logouttime
#                 try:
#                     db.commit()
#                     logging.info(f"Login end time updated for user {userid}")
#                 except Exception as e:
#                     db.rollback()  # Rollback on error
#                     logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
#             else:
#                 logging.warning(f"No active login entry found for user {userid}")

        
#         elif any(record.work_status == "Not Picked" for record in all_records):
#             tl_entry = next(record for record in all_records if record.work_status == "Not Picked")
#             logging.info(f"TL entry found for user {userid}, Service_ID: {tl_entry.Service_ID}")

#             last_work_session = db.query(models.WorkSession).filter(
#                 models.WorkSession.user_id == userid,
#                 models.WorkSession.end_time.is_(None)  # Check only for NULL
#             ).order_by(models.WorkSession.id.desc()).first()

#             if last_work_session:
#                 end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
#                 last_work_session.end_time = end_time_str
#                 db.commit()
#                 logging.info(f"End time updated for WorkSession for user {userid}")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
#                 last_work_session.total_time_worked = total_worked_time
#                 db.commit()
#                 logging.info(f"Total working time updated for WorkSession for user {userid}")

#             # Check for an active login session for the user
#             login_entry = (
#                 db.query(models.login_time)
#                 .filter(
#                     models.login_time.userid == userid,
#                     or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
#                 )
#                 .order_by(models.login_time.login_id.desc())
#                 .first()
#             )

#             # Update the logout_time for the active login session
#             if login_entry:
#                 logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
#                 logging.info(f"Logout time being set: {logouttime}")
#                 login_entry.logout_time = logouttime
#                 try:
#                     db.commit()
#                     logging.info(f"Login end time updated for user {userid}")
#                 except Exception as e:
#                     db.rollback()  # Rollback on error
#                     logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
#             else:
#                 logging.warning(f"No active login entry found for user {userid}")


#         elif any(record.work_status == "Completed" for record in all_records):
#             tl_entry = next(record for record in all_records if record.work_status == "Completed")
#             logging.info(f"TL entry found for user {userid}, Service_ID: {tl_entry.Service_ID}")

#             last_work_session = db.query(models.WorkSession).filter(
#                 models.WorkSession.user_id == userid,
#                 models.WorkSession.end_time.is_(None)  # Check only for NULL
#             ).order_by(models.WorkSession.id.desc()).first()

#             if last_work_session:
#                 end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
#                 last_work_session.end_time = end_time_str
#                 db.commit()
#                 logging.info(f"End time updated for WorkSession for user {userid}")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
#                 last_work_session.total_time_worked = total_worked_time
#                 db.commit()
#                 logging.info(f"Total working time updated for WorkSession for user {userid}")

#             # Check for an active login session for the user
#             login_entry = (
#                 db.query(models.login_time)
#                 .filter(
#                     models.login_time.userid == userid,
#                     or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
#                 )
#                 .order_by(models.login_time.login_id.desc())
#                 .first()
#             )

#             # Update the logout_time for the active login session
#             if login_entry:
#                 logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
#                 logging.info(f"Logout time being set: {logouttime}")
#                 login_entry.logout_time = logouttime
#                 try:
#                     db.commit()
#                     logging.info(f"Login end time updated for user {userid}")
#                 except Exception as e:
#                     db.rollback()  # Rollback on error
#                     logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
#             else:
#                 logging.warning(f"No active login entry found for user {userid}")

        
#         elif any(record.work_status == "Work in Progress" for record in all_records):
#             logging.info(f"'Work in Progress' found for user {userid}. Updating status to 'Hold'.")

#             # Change the work status from "Work in Progress" to "Hold"
#             tl_entry = next(record for record in all_records if record.work_status == "Work in Progress")
#             tl_entry.work_status = "Hold"
#             db.commit()
#             logging.info(f"Work status updated to 'Hold' for user {userid}.")

#             # Find the last INPROGRESS entry for the user
#             in_progress_entry = (
#                 db.query(models.INPROGRESS)
#                 .filter(models.INPROGRESS.user_id == userid, models.INPROGRESS.Service_ID == tl_entry.Service_ID, models.INPROGRESS.end_time.is_(None))
#                 .order_by(models.INPROGRESS.id.desc())
#                 .first()
#             )

#             if in_progress_entry:
#                 # Update end_time in INPROGRESS table
#                 in_progress_entry.end_time = datetime.now()  # Set end time to current time
#                 db.commit()
#                 logging.info(f"End time updated for INPROGRESS for user {userid}.")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(in_progress_entry.start_time, in_progress_entry.end_time)
#                 in_progress_entry.total_time = total_worked_time  # Assuming total_time is stored as a string
#                 db.commit()
#                 logging.info(f"Total working time updated for INPROGRESS for user {userid}.")

#             # Add a new record in the HOLD table with the start time as the current time
#             hold_record = models.HOLD(
#                 Service_ID=tl_entry.Service_ID,
#                 user_id=userid,
#                 remarks="WL to H",
#                 hold_time_start=datetime.now(),  # Use the current time
#             )
#             db.add(hold_record)
#             db.commit()
#             logging.info(f"New HOLD record added for user {userid}.")

#             # Add a new record in the WorkSession table with the start time as the current time
#             work_session_record = models.WorkSession(
#                 user_id=userid,
#                 start_time=get_current_time_str(),  # Use the current time
#             )
#             db.add(work_session_record)
#             db.commit()
#             logging.info(f"New WorkSession record added for user {userid}.")

#             last_work_session = db.query(models.WorkSession).filter(
#                 models.WorkSession.user_id == userid,
#                 models.WorkSession.end_time.is_(None)  # Check only for NULL
#             ).order_by(models.WorkSession.id.desc()).first()

#             if last_work_session:
#                 end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
#                 last_work_session.end_time = end_time_str
#                 db.commit()
#                 logging.info(f"End time updated for WorkSession for user {userid}")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
#                 last_work_session.total_time_worked = total_worked_time
#                 db.commit()
#                 logging.info(f"Total working time updated for WorkSession for user {userid}")

#             # Check for an active login session for the user
#             login_entry = (
#                 db.query(models.login_time)
#                 .filter(
#                     models.login_time.userid == userid,
#                     or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
#                 )
#                 .order_by(models.login_time.login_id.desc())
#                 .first()
#             )

#             # Update the logout_time for the active login session
#             if login_entry:
#                 logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
#                 logging.info(f"Logout time being set: {logouttime}")
#                 login_entry.logout_time = logouttime
#                 try:
#                     db.commit()
#                     logging.info(f"Login end time updated for user {userid}")
#                 except Exception as e:
#                     db.rollback()  # Rollback on error
#                     logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
#             else:
#                 logging.warning(f"No active login entry found for user {userid}")


        
#         elif any(record.work_status == "Clarification Call" for record in all_records):
#             logging.info(f"'Clarification Call' found for user {userid}. Updating status to 'Hold'.")

#             # Change the work status from "Work in Progress" to "Hold"
#             tl_entry = next(record for record in all_records if record.work_status == "Clarification Call")
#             tl_entry.work_status = "Hold"
#             db.commit()
#             logging.info(f"Work status updated to 'Hold' for user {userid}.")

#             # Find the last Clarification Call entry for the user
#             call_entry = (
#                 db.query(models.CALL)
#                 .filter(models.CALL.user_id == userid, models.CALL.Service_ID == tl_entry.Service_ID, models.CALL.call_time_end.is_(None))
#                 .order_by(models.CALL.id.desc())
#                 .first()
#             )

#             if call_entry:
#                 # Update end_time in CALL table
#                 call_entry.call_time_end = datetime.now()  # Set end time to current time
#                 db.commit()
#                 logging.info(f"End time updated for CALL for user {userid}.")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(call_entry.call_time_start, call_entry.call_time_end)
#                 call_entry.call_total_time = total_worked_time  # Assuming total_time is stored as a string
#                 db.commit()
#                 logging.info(f"Total working time updated for CALL for user {userid}.")

#             # Add a new record in the HOLD table with the start time as the current time
#             hold_record = models.HOLD(
#                 Service_ID=tl_entry.Service_ID,
#                 user_id=userid,
#                 remarks="CL to H",
#                 hold_time_start=datetime.now(),  # Use the current time
#             )
#             db.add(hold_record)
#             db.commit()
#             logging.info(f"New HOLD record added for user {userid}.")

#             # Add a new record in the WorkSession table with the start time as the current time
#             work_session_record = models.WorkSession(
#                 user_id=userid,
#                 start_time=get_current_time_str(),  # Use the current time
#             )
#             db.add(work_session_record)
#             db.commit()
#             logging.info(f"New WorkSession record added for user {userid}.")

#             last_work_session = db.query(models.WorkSession).filter(
#                 models.WorkSession.user_id == userid,
#                 models.WorkSession.end_time.is_(None)  # Check only for NULL
#             ).order_by(models.WorkSession.id.desc()).first()

#             if last_work_session:
#                 end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
#                 last_work_session.end_time = end_time_str
#                 db.commit()
#                 logging.info(f"End time updated for WorkSession for user {userid}")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
#                 last_work_session.total_time_worked = total_worked_time
#                 db.commit()
#                 logging.info(f"Total working time updated for WorkSession for user {userid}")

#             # Check for an active login session for the user
#             login_entry = (
#                 db.query(models.login_time)
#                 .filter(
#                     models.login_time.userid == userid,
#                     or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
#                 )
#                 .order_by(models.login_time.login_id.desc())
#                 .first()
#             )

#             # Update the logout_time for the active login session
#             if login_entry:
#                 logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
#                 logging.info(f"Logout time being set: {logouttime}")
#                 login_entry.logout_time = logouttime
#                 try:
#                     db.commit()
#                     logging.info(f"Login end time updated for user {userid}")
#                 except Exception as e:
#                     db.rollback()  # Rollback on error
#                     logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
#             else:
#                 logging.warning(f"No active login entry found for user {userid}")


#         elif any(record.work_status == "Break" for record in all_records):
#             logging.info(f"'Break' found for user {userid}. Updating status to 'Hold'.")

#             # Change the work status from "Work in Progress" to "Hold"
#             tl_entry = next(record for record in all_records if record.work_status == "Break")
#             tl_entry.work_status = "Hold"
#             db.commit()
#             logging.info(f"Work status updated to 'Hold' for user {userid}.")

#             # Find the last Break entry for the user
#             break_entry = (
#                 db.query(models.BREAK)
#                 .filter(models.BREAK.user_id == userid, models.BREAK.Service_ID == tl_entry.Service_ID, models.BREAK.break_time_end.is_(None))
#                 .order_by(models.BREAK.id.desc())
#                 .first()
#             )

#             if break_entry:
#                 # Update end_time in BREAK table
#                 break_entry.break_time_end = datetime.now()  # Set end time to current time
#                 db.commit()
#                 logging.info(f"End time updated for BREAK for user {userid}.")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(break_entry.break_time_start, break_entry.break_time_end)
#                 break_entry.break_total_time = total_worked_time  # Assuming total_time is stored as a string
#                 db.commit()
#                 logging.info(f"Total working time updated for BREAK for user {userid}.")

#             # Add a new record in the HOLD table with the start time as the current time
#             hold_record = models.HOLD(
#                 Service_ID=tl_entry.Service_ID,
#                 user_id=userid,
#                 remarks="BL to H",
#                 hold_time_start=datetime.now(),  # Use the current time
#             )
#             db.add(hold_record)
#             db.commit()
#             logging.info(f"New HOLD record added for user {userid}.")

#             # Add a new record in the WorkSession table with the start time as the current time
#             work_session_record = models.WorkSession(
#                 user_id=userid,
#                 start_time=get_current_time_str(),  # Use the current time
#             )
#             db.add(work_session_record)
#             db.commit()
#             logging.info(f"New WorkSession record added for user {userid}.")

#             last_work_session = db.query(models.WorkSession).filter(
#                 models.WorkSession.user_id == userid,
#                 models.WorkSession.end_time.is_(None)  # Check only for NULL
#             ).order_by(models.WorkSession.id.desc()).first()

#             if last_work_session:
#                 end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
#                 last_work_session.end_time = end_time_str
#                 db.commit()
#                 logging.info(f"End time updated for WorkSession for user {userid}")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
#                 last_work_session.total_time_worked = total_worked_time
#                 db.commit()
#                 logging.info(f"Total working time updated for WorkSession for user {userid}")

#             # Check for an active login session for the user
#             login_entry = (
#                 db.query(models.login_time)
#                 .filter(
#                     models.login_time.userid == userid,
#                     or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
#                 )
#                 .order_by(models.login_time.login_id.desc())
#                 .first()
#             )

#             # Update the logout_time for the active login session
#             if login_entry:
#                 logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
#                 logging.info(f"Logout time being set: {logouttime}")
#                 login_entry.logout_time = logouttime
#                 try:
#                     db.commit()
#                     logging.info(f"Login end time updated for user {userid}")
#                 except Exception as e:
#                     db.rollback()  # Rollback on error
#                     logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
#             else:
#                 logging.warning(f"No active login entry found for user {userid}")

#         elif any(record.work_status == "Meeting" for record in all_records):
#             logging.info(f"'Meeting' found for user {userid}. Updating status to 'Hold'.")

#             # Change the work status from "Work in Progress" to "Hold"
#             tl_entry = next(record for record in all_records if record.work_status == "Meeting")
#             tl_entry.work_status = "Hold"
#             db.commit()
#             logging.info(f"Work status updated to 'Hold' for user {userid}.")

#             # Find the last Meeting entry for the user
#             meeting_entry = (
#                 db.query(models.MEETING)
#                 .filter(models.MEETING.user_id == userid, models.MEETING.Service_ID == tl_entry.Service_ID, models.MEETING.meeting_time_end.is_(None))
#                 .order_by(models.MEETING.id.desc())
#                 .first()
#             )

#             if meeting_entry:
#                 # Update end_time in MEETING table
#                 meeting_entry.meeting_time_end = datetime.now()  # Set end time to current time
#                 db.commit()
#                 logging.info(f"End time updated for MEETING for user {userid}.")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(meeting_entry.meeting_time_start, meeting_entry.meeting_time_end)
#                 meeting_entry.meet_total_time = total_worked_time  # Assuming total_time is stored as a string
#                 db.commit()
#                 logging.info(f"Total working time updated for MEETING for user {userid}.")

#             # Add a new record in the HOLD table with the start time as the current time
#             hold_record = models.HOLD(
#                 Service_ID=tl_entry.Service_ID,
#                 user_id=userid,
#                 remarks="ML to H",
#                 hold_time_start=datetime.now(),  # Use the current time
#             )
#             db.add(hold_record)
#             db.commit()
#             logging.info(f"New HOLD record added for user {userid}.")

#             # Add a new record in the WorkSession table with the start time as the current time
#             work_session_record = models.WorkSession(
#                 user_id=userid,
#                 start_time=get_current_time_str(),  # Use the current time
#             )
#             db.add(work_session_record)
#             db.commit()
#             logging.info(f"New WorkSession record added for user {userid}.")

#             last_work_session = db.query(models.WorkSession).filter(
#                 models.WorkSession.user_id == userid,
#                 models.WorkSession.end_time.is_(None)  # Check only for NULL
#             ).order_by(models.WorkSession.id.desc()).first()

#             if last_work_session:
#                 end_time_str = get_current_time_str_with_offset(2)  # Adjust end time if necessary
#                 last_work_session.end_time = end_time_str
#                 db.commit()
#                 logging.info(f"End time updated for WorkSession for user {userid}")

#                 # Calculate the total working time (end_time - start_time)
#                 total_worked_time = calculate_total_times(last_work_session.start_time, last_work_session.end_time)
#                 last_work_session.total_time_worked = total_worked_time
#                 db.commit()
#                 logging.info(f"Total working time updated for WorkSession for user {userid}")

#             # Check for an active login session for the user
#             login_entry = (
#                 db.query(models.login_time)
#                 .filter(
#                     models.login_time.userid == userid,
#                     or_(models.login_time.logout_time.is_(None), models.login_time.logout_time == ''),  # Check only for NULL or empty
#                 )
#                 .order_by(models.login_time.login_id.desc())
#                 .first()
#             )

#             # Update the logout_time for the active login session
#             if login_entry:
#                 logouttime = get_current_time_str_with_offset(2)  # Set this appropriately
#                 logging.info(f"Logout time being set: {logouttime}")
#                 login_entry.logout_time = logouttime
#                 try:
#                     db.commit()
#                     logging.info(f"Login end time updated for user {userid}")
#                 except Exception as e:
#                     db.rollback()  # Rollback on error
#                     logging.error(f"Failed to update login end time for user {userid}: {str(e)}")
#             else:
#                 logging.warning(f"No active login entry found for user {userid}")


#         else:
#             logging.info(f"No 'Work in Progress' records found for user {userid}")

#     except Exception as e:
#         logging.error(f"An error occurred: {e}")


# ---------------------------------logout status change to Hold- new function.............end



# --------------------------------------loging Tracking code start with username with Fisrt name and last name 07/10/2024 3:19
from sqlalchemy import not_
from datetime import datetime
from sqlalchemy.orm import Session

def get_user_status(picked_date: str, to_date: str, db: Session):
    users = db.query(models.User_table).filter(not_(models.User_table.role.in_(['Admin', 'TL']))).all()

    result = []

    # Convert picked_date and to_date to datetime objects
    try:
        picked_date = datetime.strptime(picked_date, "%Y-%m-%d")
        to_date = datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format"}

    for user in users:
        # Fetch all login records within the specified date range
        login_records = (
            db.query(models.login_time)
            .filter(models.login_time.userid == user.user_id)
            .filter(models.login_time.login_time.between(
                picked_date.strftime("%Y-%m-%d 00:00:00"),
                to_date.strftime("%Y-%m-%d 23:59:59")
            ))
            .order_by(models.login_time.login_id.desc())
            .all()
        )

        full_name = f"{user.firstname} {user.lastname}"

        if login_records:
            found_active_record = False
            
            for index, record in enumerate(login_records):
                # Extract date from login_time
                login_date = record.login_time.split()[0]

                # Parse login_time and logout_time into datetime objects
                try:
                    login_datetime = datetime.strptime(record.login_time, "%Y-%m-%d %H:%M:%S")
                    logout_datetime = datetime.strptime(record.logout_time, "%Y-%m-%d %H:%M:%S") if record.logout_time else None
                except ValueError:
                    login_datetime = logout_datetime = None

                # Calculate duration
                if login_datetime and logout_datetime:
                    duration = logout_datetime - login_datetime
                    duration_str = str(duration)
                else:
                    duration_str = "Not Completed"

                # Determine status logic based on the current record's logout time
                if not found_active_record:
                    if record.logout_time:  # If there's a logout time, mark as Inactive
                        status = "Inactive"
                    else:  # If there's no logout time and it's the latest record, mark as Active
                        status = "Active"
                        found_active_record = True  # Mark that we found an active record
                else:
                    status = "Inactive"  # All previous records are inactive

                logout_time_display = record.logout_time if record.logout_time else "Still Active"

                result.append({
                    "username": full_name,
                    "login_time": record.login_time,
                    "logout_time": logout_time_display,
                    "login_date": login_date,
                    "duration": duration_str,
                    "status": status
                })
        else:
            pass

    return result
# --------------------------------------loging Tracking code end



# ---------------------------------------------update version-1.0------------------------------------------
# ----------------------start udpate version for hold



def hold_start(db: Session, service_id: int, remarks: str, user_id: int):
    # Query the INPROGRESS table to find the current record for the given service_id and user_id
    inprogress_record = db.query(models.INPROGRESS).filter(
        models.INPROGRESS.Service_ID == service_id,
        models.INPROGRESS.user_id == user_id,
        models.INPROGRESS.end_time.is_(None)  # Only check for NULL
    ).first()

    # Check if an INPROGRESS record exists
    if inprogress_record:
        # Update the end time to the current time
        current_datetime = datetime.now()
        inprogress_record.end_time = current_datetime
        
        # Calculate total time
        total_seconds = (current_datetime - inprogress_record.start_time).total_seconds()
        
        # Convert total_seconds to HH:MM:SS format
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format as HH:MM:SS
        total_time_hhmmss = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        # Store total time as HH:MM:SS
        inprogress_record.total_time = total_time_hhmmss
        
        # Commit changes to update INPROGRESS record
        db.commit()
        
        # Update work status in the TL table
        tl_record = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
        if tl_record:
            tl_record.work_status = "Hold"
            db.commit()

    # Insert new record in HOLD table
    current_datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_insert = models.HOLD(Service_ID=service_id, user_id=user_id, hold_time_start=current_datetime_str, remarks=remarks)
    db.add(db_insert)
    db.commit()
    
    return "Success"

def hold_end(db:Session,service_id:int,user_id:int):
    
    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    db_res.work_status = "Work in Progress"
    db.commit()
    
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    db_res2 = db.query(models.HOLD).filter(
        models.HOLD.Service_ID == service_id,
        models.HOLD.user_id == user_id
    ).order_by(
        models.HOLD.id.desc()
    ).first()
    db_res2.hold_time_end = current_datetime_str
    db.commit()

    total_seconds = (db_res2.hold_time_end - db_res2.hold_time_start).total_seconds()
    db_res2.hold_total_time = str(timedelta(seconds=int(total_seconds))).split('.')[0]
    db.commit()

    new_inprogress_record = models.INPROGRESS(
        Service_ID=service_id,
        user_id=user_id,
        start_time=current_datetime 
    )
    db.add(new_inprogress_record)
    db.commit()

    return "Success"


# ----------------------------new hold missing date added on with corn job--------------------------

from datetime import datetime, timedelta

def fetch_hold_data(db: Session):
    print("Fetch Hold Data running...")

    # Fetch records from the TL table where work_status is 'Hold'
    tl_records = db.query(models.TL).filter(models.TL.work_status == 'Hold',models.TL.status == 1).all()
    if not tl_records:
        print("No records found in TL table with work_status 'Hold' and status 1. Exiting function.")
        return []

    hold_service_ids = {tl.Service_ID for tl in tl_records}

    # Fetch the most recent hold records for these services
    hold_records = db.query(models.HOLD).filter(
        models.HOLD.Service_ID.in_(hold_service_ids)
    ).order_by(models.HOLD.id.desc()).all()

    current_datetime = datetime.now()
    current_date = current_datetime.date()

    # Track created hold records to prevent duplicates
    created_records = set()

    for hold_record in hold_records:
        last_hold_start_time = hold_record.hold_time_start

        # Convert start time to datetime if it's a string
        if isinstance(last_hold_start_time, str):
            last_hold_start_time = datetime.strptime(last_hold_start_time, '%Y-%m-%d %H:%M:%S')

        # Print the hold record's current state
        print(f"Processing Hold Record ID {hold_record.id}:")
        print(f"Start Time: {last_hold_start_time}, End Time: {hold_record.hold_time_end}")

        # Update the end time if it's not set
        if last_hold_start_time.date() == current_date and not hold_record.hold_time_end:
            # Set the end time to the end of the current day
            hold_record.hold_time_end = datetime.combine(current_date, datetime.strptime("23:59:59", "%H:%M:%S").time())
            
            # Calculate total time and store it in HH:MM:SS format
            total_time = hold_record.hold_time_end - hold_record.hold_time_start
            hold_record.hold_total_time = str(total_time)

            db.commit()  # Commit the changes after updating
            print(f"Updated hold record {hold_record.id} with end time {hold_record.hold_time_end} and total time {hold_record.hold_total_time}")

        # Create a new hold record for tomorrow if it doesn't exist
        if last_hold_start_time.date() == current_date and hold_record.Service_ID not in created_records:
            existing_record = db.query(models.HOLD).filter(
                models.HOLD.Service_ID == hold_record.Service_ID,
                models.HOLD.user_id == hold_record.user_id,
                models.HOLD.hold_time_start == f"{current_date + timedelta(days=1)} 00:00:00"
            ).first()

            if not existing_record:
                new_hold = models.HOLD(
                    Service_ID=hold_record.Service_ID,
                    user_id=hold_record.user_id,
                    hold_time_start=f"{current_date + timedelta(days=1)} 00:00:00",
                    hold_time_end=None,
                    remarks="New hold record for tomorrow"
                )
                db.add(new_hold)
                created_records.add(hold_record.Service_ID)

                print(f"Created new hold record: Service_ID={new_hold.Service_ID}, user_id={new_hold.user_id}, hold_time_start={new_hold.hold_time_start}")

    db.commit()  # Final commit after processing all records
    print("Hold records created/updated successfully.")


# -----------------checking purpose
# def calculate_total_time_hold(db: Session, picked_date: str, to_date: str) -> dict:
#     # Parse input dates
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     # Define start and end boundaries for filtering
#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     # Query all holds within the date range
#     hold_records = db.query(models.HOLD).filter(
#         models.HOLD.hold_time_start < to_date_end,  # Ensure inclusion of multi-day holds
#         (models.HOLD.hold_time_end == None) | (models.HOLD.hold_time_end >= picked_date_start)
#     ).all()

#     user_total_time = defaultdict(timedelta)  # Store total time per user

#     # Get current time for ongoing holds
#     current_time = datetime.now()

#     for record in hold_records:
#         start_time = record.hold_time_start

#         # Determine the correct end time for each record
#         if record.hold_time_end:
#             end_time = min(record.hold_time_end, to_date_end)  # Cap at to_date_end
#         else:
#             # If no end time, use the current time or to_date_end, whichever is earlier
#             end_time = min(current_time, to_date_end)

#         # Calculate the duration and accumulate it
#         if end_time > picked_date_start:
#             user_total_time[record.user_id] += (end_time - max(start_time, picked_date_start))

#     # Format the total time for each user
#     formatted_total_time = {
#         user_id: str(hold_total_time).split('.')[0] for user_id, hold_total_time in user_total_time.items()
#     }

#     return formatted_total_time


# ----------------------end udpate version for hold


# ----------------------start udpate version for break
  

def break_start(db: Session, service_id: int, user_id: int):
    # Query the INPROGRESS table to find the current record for the given service_id and user_id
    inprogress_record = db.query(models.INPROGRESS).filter(
        models.INPROGRESS.Service_ID == service_id,
        models.INPROGRESS.user_id == user_id,
        models.INPROGRESS.end_time == None  # Only check for NULL
    ).first()
    
    # Check if an INPROGRESS record exists
    if inprogress_record:
        # Update the end time to the current time
        current_datetime = datetime.now()
        inprogress_record.end_time = current_datetime
        
        # Calculate total time
        total_seconds = (current_datetime - inprogress_record.start_time).total_seconds()
        
        # Convert total_seconds to HH:MM:SS format
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format as HH:MM:SS
        total_time_hhmmss = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        # Store total time as HH:MM:SS
        inprogress_record.total_time = total_time_hhmmss
        
        # Commit changes to update INPROGRESS record
        db.commit()

        # Change work status in the TL table
        tl_record = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
        if tl_record:
            tl_record.work_status = "Break"
            db.commit()

        # Create a new record in the BREAK table
        db_insert = models.BREAK(
            Service_ID=service_id,
            user_id=user_id,
            break_time_start=current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(db_insert)
        db.commit()

        return "Success"
    
    return "No ongoing work in progress to take a break."


def break_end(db: Session, service_id: int, user_id: int):
    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    db_res.work_status = "Work in Progress"
    db.commit()
    
    current_datetime = datetime.now()

    db_res2 = db.query(models.BREAK).filter(
        models.BREAK.Service_ID == service_id,
        models.BREAK.user_id == user_id
    ).order_by(
        models.BREAK.id.desc()
    ).first()

    db_res2.break_time_end = current_datetime
    db.commit()

    total_seconds = (db_res2.break_time_end - db_res2.break_time_start).total_seconds()
    db_res2.break_total_time = str(timedelta(seconds=int(total_seconds))).split('.')[0]
    db.commit()

    new_inprogress_record = models.INPROGRESS(
        Service_ID=service_id,
        user_id=user_id,
        start_time=current_datetime 
    )
    db.add(new_inprogress_record)
    db.commit()


    return "BREAK record updated successfully."

       

# ----------------------end udpate version for break


# ----------------------start udpate version for meeting

def meeting_start(db: Session, service_id: int, user_id: int):
    # Query the INPROGRESS table to find the current record for the given service_id and user_id
    inprogress_record = db.query(models.INPROGRESS).filter(
        models.INPROGRESS.Service_ID == service_id,
        models.INPROGRESS.user_id == user_id,
        models.INPROGRESS.end_time == None  # Only check for NULL
    ).first()
    
    # Check if an INPROGRESS record exists
    if inprogress_record:
        # Update the end time to the current time
        current_datetime = datetime.now()
        inprogress_record.end_time = current_datetime
        
        # Calculate total time
        total_seconds = (current_datetime - inprogress_record.start_time).total_seconds()
        
        # Convert total_seconds to HH:MM:SS format
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format as HH:MM:SS
        total_time_hhmmss = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        # Store total time as HH:MM:SS
        inprogress_record.total_time = total_time_hhmmss
        
        # Commit changes to update INPROGRESS record
        db.commit()

        # Change work status in the TL table
        tl_record = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
        if tl_record:
            tl_record.work_status = "Meeting"
            db.commit()

        # Create a new record in the MEETING table
        db_insert = models.MEETING(
            Service_ID=service_id,
            user_id=user_id,
            meeting_time_start=current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(db_insert)
        db.commit()

        return "Success"

    return "No ongoing work in progress to start a meeting."

def meeting_end(db:Session,service_id:int,user_id:int):
    
    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    db_res.work_status = "Work in Progress"
    db.commit()
    
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    db_res2 = db.query(models.MEETING).filter(
        models.MEETING.Service_ID == service_id,
        models.MEETING.user_id == user_id
    ).order_by(
        models.MEETING.id.desc()
    ).first()
    db_res2.meeting_time_end = current_datetime_str
    db.commit()


    total_seconds = (db_res2.meeting_time_end - db_res2.meeting_time_start).total_seconds()
    db_res2.meet_total_time = str(timedelta(seconds=int(total_seconds))).split('.')[0]
    db.commit()

    new_inprogress_record = models.INPROGRESS(
        Service_ID=service_id,
        user_id=user_id,
        start_time=current_datetime 
    )
    db.add(new_inprogress_record)
    db.commit()

    return "Success"


# ----------------------end udpate version for meeting


# ----------------------start udpate version for call

def call_start(db: Session, service_id: int, user_id: int):
    # Query the INPROGRESS table to find the current record for the given service_id and user_id
    inprogress_record = db.query(models.INPROGRESS).filter(
        models.INPROGRESS.Service_ID == service_id,
        models.INPROGRESS.user_id == user_id,
        models.INPROGRESS.end_time.is_(None)  # Only check for NULL
    ).first()
    
    # Check if an INPROGRESS record exists
    if inprogress_record:
        # Update the end time to the current time
        current_datetime = datetime.now()
        inprogress_record.end_time = current_datetime
        
        # Calculate total time
        total_seconds = (current_datetime - inprogress_record.start_time).total_seconds()
        
        # Convert total_seconds to HH:MM:SS format
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format as HH:MM:SS
        total_time_hhmmss = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        # Store total time as HH:MM:SS
        inprogress_record.total_time = total_time_hhmmss
        
        # Commit changes to update INPROGRESS record
        db.commit()
        
        # Update work status in the TL table
        tl_record = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
        if tl_record:
            tl_record.work_status = "Clarification Call"
            db.commit()

    # Insert new record in CALL table
    current_datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_insert = models.CALL(Service_ID=service_id, user_id=user_id, call_time_start=current_datetime_str)
    db.add(db_insert)
    db.commit()
    
    return "Success"


def call_end(db:Session,service_id:int,user_id:int):
    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    db_res.work_status = "Work in Progress"
    db.commit()
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    db_res2 = db.query(models.CALL).filter(
        models.CALL.Service_ID == service_id,
        models.CALL.user_id == user_id
    ).order_by(
        models.CALL.id.desc()
    ).first()
    db_res2.call_time_end = current_datetime_str
    db.commit()

    total_seconds = (db_res2.call_time_end - db_res2.call_time_start).total_seconds()
    db_res2.call_total_time = str(timedelta(seconds=int(total_seconds))).split('.')[0]
    db.commit()

    new_inprogress_record = models.INPROGRESS(
        Service_ID=service_id,
        user_id=user_id,
        start_time=current_datetime 
    )
    db.add(new_inprogress_record)
    db.commit()

    return "Success"


# ----------------------end udpate version for call


# ----------------------start udpate version for inprogress
from datetime import datetime


def inprogress_start(db: Session, service_id: int, type_of_activity: str, no_of_items: str):
    # Query the TL table for the specified service ID
    tl_record = db.query(models.TL).filter(
        models.TL.Service_ID == service_id
    ).first()

    # Update fields in the TL record
    tl_record.type_of_activity = type_of_activity
    tl_record.no_of_items = no_of_items
    tl_record.work_status = "Work in Progress"
    
    current_datetime = datetime.now()
    if not tl_record.working_time:  # Handles None and empty string
        tl_record.working_time = current_datetime  # Store as datetime object
        db.commit()  # Commit after updating TL

    # Query the INPROGRESS table to find an existing record
    db_res = db.query(models.INPROGRESS).filter(
        models.INPROGRESS.Service_ID == service_id,
        models.INPROGRESS.user_id == tl_record.Assigned_To
    ).first()

    # If no INPROGRESS record exists, create a new one
    try:
        if db_res is None:
            db_res = models.INPROGRESS(
                Service_ID=service_id,
                user_id=tl_record.Assigned_To,
                start_time=tl_record.working_time,
            )
            db.add(db_res)
            db.commit()  # Commit the new INPROGRESS entry
    except Exception as e:
        db.rollback()  # Rollback if there's an error
        return f"Failed: {str(e)}"

    return "Success"



# def inprogress_end(db: Session, service_id: int, user_id: int):
#     tl_record = db.query(models.TL).filter(
#         models.TL.Service_ID == service_id,
#         models.TL.Assigned_To == user_id  
#     ).first()

#     if tl_record is None:
#         return "Service ID not found or User not assigned"

#     db_res = db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.Service_ID == service_id,
#         models.INPROGRESS.user_id == user_id
#     ).order_by(
#         models.INPROGRESS.id.desc()
#     ).first()

#     total_seconds = (db_res.end_time - db_res.start_time).total_seconds()
#     db_res.total_time = str(timedelta(seconds=int(total_seconds))).split('.')[0]
#     db.commit()


#     return "Success"


# def inprogress_end(db: Session, service_id: int, user_id: int):
#     # Query the TL table to find the record with the given service ID and assigned user
#     tl_record = db.query(models.TL).filter(
#         models.TL.Service_ID == service_id,
#         models.TL.Assigned_To == user_id  
#     ).first()

#     # Check if the TL record exists
#     if tl_record is None:
#         return "Service ID not found or User not assigned"

#     # Query the INPROGRESS table to get the most recent in-progress record for the user
#     db_res = db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.Service_ID == service_id,
#         models.INPROGRESS.user_id == user_id
#     ).order_by(
#         models.INPROGRESS.id.desc()
#     ).first()

#     # Check the work status of the TL record
#     if tl_record.work_status in ["Break", "Clarification Call", "Meeting", "End Of Day", "Hold"]:
#         # If there is an in-progress record, update its end time
#         if db_res is not None:
#             db_res.end_time = datetime.now()  # Set end time to the current datetime
            
#             # Calculate total time spent in progress
#             total_seconds = (db_res.end_time - db_res.start_time).total_seconds()
#             db_res.total_time = str(timedelta(seconds=int(total_seconds))).split('.')[0] 
#             db.commit()  # Commit the changes to the database
            
#         # Insert new records based on work status
#         current_datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
#         if tl_record.work_status == "Break":
#             db_insert = models.BREAK(Service_ID=service_id, user_id=user_id, break_time_start=current_datetime_str)
#             db.add(db_insert)
#             tl_record.work_status = "Break"  # Ensure the work status is set to "Break"
        
#         elif tl_record.work_status == "Clarification Call":
#             db_insert = models.CLARIFICATION_CALL(Service_ID=service_id, user_id=user_id, clarification_call_time_start=current_datetime_str)
#             db.add(db_insert)
#             tl_record.work_status = "Clarification Call"
        
#         elif tl_record.work_status == "Meeting":
#             db_insert = models.MEETING(Service_ID=service_id, user_id=user_id, meeting_time_start=current_datetime_str)
#             db.add(db_insert)
#             tl_record.work_status = "Meeting"
        
#         elif tl_record.work_status == "End Of Day":
#             db_insert = models.END_OF_DAY(Service_ID=service_id, user_id=user_id, end_time_start=current_datetime_str)
#             db.add(db_insert)
#             tl_record.work_status = "End Of Day"
        
#         elif tl_record.work_status == "Hold":
#             db_insert = models.HOLD(Service_ID=service_id, user_id=user_id, hold_time_start=current_datetime_str, remarks=remarks)
#             db.add(db_insert)
#             tl_record.work_status = "Hold"

#         db.commit()  # Commit the changes for the new record and work status update
        
#         return "INPROGRESS record updated with end time and new record created based on work status"
    
#     return "No valid work status to update"


# def calculate_total_time_inprogress(db: Session, picked_date: str, to_date: str) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")

#     picked_date_start = picked_datett.replace(hour=0, minute=0, second=0)
#     to_date_end = to_datett.replace(hour=23, minute=59, second=59)

#     inprogress_records = db.query(models.INPROGRESS).filter(
#         models.INPROGRESS.start_time >= picked_date_start,
#         models.INPROGRESS.start_time <= to_date_end
#     ).all()

#     user_total_time = defaultdict(timedelta)

#     current_time = datetime.now()

#     for record in inprogress_records:
#         start_time = record.start_time

#         if record.end_time:
#             end_time = record.end_time
#             user_total_time[record.user_id] += (end_time - start_time)
#         else:
#             if start_time.date() == current_time.date():
#                 end_time = current_time
#                 user_total_time[record.user_id] += (end_time - start_time)
#             elif start_time.date() < current_time.date():
#                 continue

#     formatted_total_time = {
#         user_id: str(total_time).split('.')[0] for user_id,  total_time in user_total_time.items()
#     }

#     return formatted_total_time
# ----------------------end udpate version for inprogress



# ----------------------------end of the day
def end_of_day_start(db: Session, service_id: int, user_id: int):
    # Retrieve and update the TL record for the service
    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    db_res.work_status = "End Of Day"
    db.commit()

    # Capture the current time
    current_datetime = datetime.now()

    # Insert new END_OF_DAY record
    db_insert = models.END_OF_DAY(
        Service_ID=service_id,
        user_id=user_id,
        end_time_start=current_datetime
    )
    db.add(db_insert)
    db.commit()

    # Retrieve the latest INPROGRESS record for the service and user
    db_res3 = db.query(models.INPROGRESS).filter(
        models.INPROGRESS.Service_ID == service_id,
        models.INPROGRESS.user_id == user_id
    ).order_by(
        models.INPROGRESS.id.desc()
    ).first()

    # Update the end_time with the current time
    db_res3.end_time = current_datetime  

    # Calculate total time in seconds
    total_seconds = (current_datetime - db_res3.start_time).total_seconds()

    # Convert total_seconds to HH:MM:SS format
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format as HH:MM:SS and store the total time
    total_time_hhmmss = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    db_res3.total_time = total_time_hhmmss

    # Commit changes to update the INPROGRESS record
    db.commit()

    return "Success"


def end_of_day_end(db: Session, service_id: int, user_id: int):
    
    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    db_res.work_status = "Work in Progress"
    
    current_datetime = datetime.now()
    db_res.reallocated_time = current_datetime 
    db.commit()

    db_res2 = db.query(models.END_OF_DAY).filter(
        models.END_OF_DAY.Service_ID == service_id,
        models.END_OF_DAY.user_id == user_id
    ).order_by(
        models.END_OF_DAY.id.desc()
    ).first()

    db_res2.end_time_end = current_datetime  
    db.commit()

    new_inprogress_record = models.INPROGRESS(
        Service_ID=service_id,
        user_id=user_id,
        start_time=current_datetime 
    )
    db.add(new_inprogress_record)
    db.commit()

    return "Success"

# ----------------------end udpate version for endofday

# -----------------------compeleted



# def Completed(db:Session,service_id:int,remarks:str,count:str):
    
#     current_datetime = datetime.now()
#     current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

#     db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
#     db_res.work_status = "Completed"
#     db_res.no_of_items = count
#     db_res.completed_time = current_datetime_str
#     db_res.remarks = remarks
#     db.commit()
#     return "Success"




def Completed(db: Session, service_id: int, count: str):
    # Get the current datetime and formatted string
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    # Check if an INPROGRESS record exists
    inprogress_record = db.query(models.INPROGRESS).filter(
        models.INPROGRESS.Service_ID == service_id,
        models.INPROGRESS.user_id == models.TL.Assigned_To,
        models.INPROGRESS.end_time == None  # Only check for NULL
    ).first()

    if inprogress_record:
        # Update the end time to the current time
        inprogress_record.end_time = current_datetime
        
        # Calculate total time
        total_seconds = (current_datetime - inprogress_record.start_time).total_seconds()
        
        # Convert total_seconds to HH:MM:SS format
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format as HH:MM:SS
        total_time_hhmmss = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        # Store total time as HH:MM:SS
        inprogress_record.total_time = total_time_hhmmss

        # Commit changes for the INPROGRESS record
        db.commit()

    # Now, proceed to complete the work in the TL model
    db_res = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()
    
    if db_res:
        db_res.work_status = "Completed"
        db_res.no_of_items = count
        db_res.completed_time = current_datetime_str
        db.commit()
    
    return "Success"

# ------------------- Call for all user Time Calculation------------------- #

# ------------------user wise report with split data 15/10/2024
# from collections import defaultdict, OrderedDict
# from datetime import datetime, timedelta

# def calculate_end_time_for_user(db: Session, picked_date: str, to_date: str) -> dict:
#     # Parse the input dates
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    
#     # Get current time for ongoing records
#     current_time = datetime.now()

#     # Function to process records for each date
#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field)
            
#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time for ongoing records
#                 else:
#                     continue  # Ignore past incomplete records

#             # Ensure the record matches the specific day
#             if start_time.date() == date:
#                 time_diff = end_time - start_time
#                 username = db.query(models.User_table).filter(
#                     models.User_table.user_id == getattr(record, user_field)
#                 ).first().username

#                 # Accumulate time per user and activity
#                 user_times[username][activity] += time_diff
#                 if activity == 'in_progress':
#                     user_times[username]['total_time_take'] += time_diff

#     # Initialize an OrderedDict to maintain the order of days
#     daily_summaries = OrderedDict()

#     # Iterate over each day in the date range
#     current_day = picked_datett
#     while current_day <= to_datett:
#         # Initialize user time dictionary for this day
#         user_times = defaultdict(lambda: defaultdict(timedelta))
        
#         # Fetch and process records for each activity for this day
#         hold_records = db.query(models.HOLD).filter(
#             models.HOLD.hold_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.HOLD.hold_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'hold', hold_records, 
#                                 'hold_time_start', 'hold_time_end', 'user_id', user_times)

#         break_records = db.query(models.BREAK).filter(
#             models.BREAK.break_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.BREAK.break_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'break', break_records, 
#                                 'break_time_start', 'break_time_end', 'user_id', user_times)

#         meet_records = db.query(models.MEETING).filter(
#             models.MEETING.meeting_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.MEETING.meeting_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'meeting', meet_records, 
#                                 'meeting_time_start', 'meeting_time_end', 'user_id', user_times)

#         call_records = db.query(models.CALL).filter(
#             models.CALL.call_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.CALL.call_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'call', call_records, 
#                                 'call_time_start', 'call_time_end', 'user_id', user_times)

#         inprogress_records = db.query(models.INPROGRESS).filter(
#             models.INPROGRESS.start_time >= current_day.replace(hour=0, minute=0, second=0),
#             models.INPROGRESS.start_time <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'in_progress', inprogress_records, 
#                                 'start_time', 'end_time', 'user_id', user_times)

#         # Format the total time for this day
#         formatted_day_summary = {
#             username: {
#                 'in_progress': str(user_times[username]['in_progress']).split('.')[0],
#                 'break': str(user_times[username]['break']).split('.')[0],
#                 'meeting': str(user_times[username]['meeting']).split('.')[0],
#                 'call': str(user_times[username]['call']).split('.')[0],
#                 'hold': str(user_times[username]['hold']).split('.')[0],
#                 'total_time_take': str(user_times[username]['total_time_take']).split('.')[0]
#             }
#             for username in user_times.keys()
#         }

#         # Store the formatted summary for this day
#         daily_summaries[current_day.strftime("%Y-%m-%d")] = formatted_day_summary

#         # Move to the next day
#         current_day += timedelta(days=1)

#     return daily_summaries



# from collections import defaultdict, OrderedDict
# from datetime import datetime, timedelta
# from sqlalchemy.orm import Session


# def calculate_end_time_for_user(db: Session, picked_date: str, to_date: str) -> dict:
#     # Parse the input dates
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    
#     # Get current time for ongoing records
#     current_time = datetime.now()

#     # Function to process records for each date
#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field)
            
#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time for ongoing records
#                 else:
#                     continue  # Ignore past incomplete records

#             # Ensure the record matches the specific day
#             if start_time.date() == date:
#                 time_diff = end_time - start_time
#                 username = db.query(models.User_table).filter(
#                     models.User_table.user_id == getattr(record, user_field)
#                 ).first().username

#                 # Fetch work status for the assigned user
#                 tl_record = db.query(models.TL).filter(
#                     models.TL.Assigned_To == getattr(record, user_field),
#                     models.TL.status == 1  # Assuming status 1 means active or picked
#                 ).first()
                
#                 work_status = tl_record.work_status if tl_record else 'Not Picked'

#                 # Accumulate time per user and activity
#                 user_times[username][activity] += time_diff
#                 if activity == 'in_progress':
#                     user_times[username]['total_time_take'] += time_diff

#                 # Add work status to the user's data
#                 user_times[username]['status'] = work_status

#     # Initialize an OrderedDict to maintain the order of days
#     daily_summaries = OrderedDict()

#     # Iterate over each day in the date range
#     current_day = picked_datett
#     while current_day <= to_datett:
#         # Initialize user time dictionary for this day
#         user_times = defaultdict(lambda: defaultdict(timedelta))
        
#         # Fetch and process records for each activity for this day
#         hold_records = db.query(models.HOLD).filter(
#             models.HOLD.hold_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.HOLD.hold_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'hold', hold_records, 
#                                 'hold_time_start', 'hold_time_end', 'user_id', user_times)

#         break_records = db.query(models.BREAK).filter(
#             models.BREAK.break_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.BREAK.break_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'break', break_records, 
#                                 'break_time_start', 'break_time_end', 'user_id', user_times)

#         meet_records = db.query(models.MEETING).filter(
#             models.MEETING.meeting_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.MEETING.meeting_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'meeting', meet_records, 
#                                 'meeting_time_start', 'meeting_time_end', 'user_id', user_times)

#         call_records = db.query(models.CALL).filter(
#             models.CALL.call_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.CALL.call_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'call', call_records, 
#                                 'call_time_start', 'call_time_end', 'user_id', user_times)

#         inprogress_records = db.query(models.INPROGRESS).filter(
#             models.INPROGRESS.start_time >= current_day.replace(hour=0, minute=0, second=0),
#             models.INPROGRESS.start_time <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'in_progress', inprogress_records, 
#                                 'start_time', 'end_time', 'user_id', user_times)

#         # Format the total time for this day
#         formatted_day_summary = {
#             username: {
#                 'in_progress': str(user_times[username]['in_progress']).split('.')[0],
#                 'break': str(user_times[username]['break']).split('.')[0],
#                 'meeting': str(user_times[username]['meeting']).split('.')[0],
#                 'call': str(user_times[username]['call']).split('.')[0],
#                 'hold': str(user_times[username]['hold']).split('.')[0],
#                 'total_time_take': str(user_times[username]['total_time_take']).split('.')[0],
#                 'status': user_times[username]['status']  
#             }
#             for username in user_times.keys()
#         }

#         # Store the formatted summary for this day
#         daily_summaries[current_day.strftime("%Y-%m-%d")] = formatted_day_summary

#         # Move to the next day
#         current_day += timedelta(days=1)

#     return daily_summaries



# ---------------working code
# from collections import defaultdict, OrderedDict
# from datetime import datetime, timedelta

# def calculate_end_time_for_user(db: Session, picked_date: str, to_date: str) -> dict:
#     # Parse the input dates
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    
#     # Get current time for ongoing records
#     current_time = datetime.now()

#     # Function to process records for each date
#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field)
            
#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time for ongoing records
#                 else:
#                     continue  # Ignore past incomplete records

#             # Ensure the record matches the specific day
#             if start_time.date() == date:
#                 time_diff = end_time - start_time
#                 username = db.query(models.User_table).filter(
#                     models.User_table.user_id == getattr(record, user_field)
#                 ).first().username


#                 #  Fetch work status for the assigned user
#                 tl_record = db.query(models.TL).filter(
#                     models.TL.Assigned_To == getattr(record, user_field),
#                     models.TL.status == 1  # Assuming status 1 means active or picked
#                 ).first()
                
#                 work_status = tl_record.work_status if tl_record else None

#                 # Accumulate time per user and activity
#                 user_times[username][activity] += time_diff
#                 if activity == 'in_progress':
#                     user_times[username]['total_time_take'] += time_diff

#                 # Add work status to the user's data
#                 user_times[username]['status'] = work_status

#     # Initialize an OrderedDict to maintain the order of days
#     daily_summaries = OrderedDict()

#     # Iterate over each day in the date range
#     current_day = picked_datett
#     while current_day <= to_datett:
#         # Initialize user time dictionary for this day
#         user_times = defaultdict(lambda: defaultdict(timedelta))
        
#         # Fetch and process records for each activity for this day
#         hold_records = db.query(models.HOLD).filter(
#             models.HOLD.hold_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.HOLD.hold_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'hold', hold_records, 
#                                 'hold_time_start', 'hold_time_end', 'user_id', user_times)

#         break_records = db.query(models.BREAK).filter(
#             models.BREAK.break_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.BREAK.break_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'break', break_records, 
#                                 'break_time_start', 'break_time_end', 'user_id', user_times)

#         meet_records = db.query(models.MEETING).filter(
#             models.MEETING.meeting_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.MEETING.meeting_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'meeting', meet_records, 
#                                 'meeting_time_start', 'meeting_time_end', 'user_id', user_times)

#         call_records = db.query(models.CALL).filter(
#             models.CALL.call_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.CALL.call_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'call', call_records, 
#                                 'call_time_start', 'call_time_end', 'user_id', user_times)

#         inprogress_records = db.query(models.INPROGRESS).filter(
#             models.INPROGRESS.start_time >= current_day.replace(hour=0, minute=0, second=0),
#             models.INPROGRESS.start_time <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'in_progress', inprogress_records, 
#                                 'start_time', 'end_time', 'user_id', user_times)

#         # Format the total time for this day
#         formatted_day_summary = {
#             username: {
#                 'in_progress': str(user_times[username]['in_progress']).split('.')[0],
#                 'break': str(user_times[username]['break']).split('.')[0],
#                 'meeting': str(user_times[username]['meeting']).split('.')[0],
#                 'call': str(user_times[username]['call']).split('.')[0],
#                 'hold': str(user_times[username]['hold']).split('.')[0],
#                 'status': user_times[username]['status'],
#                 'total_time_take': str(user_times[username]['total_time_take']).split('.')[0]
#             }
#             for username in user_times.keys()
#         }

#         # Store the formatted summary for this day
#         daily_summaries[current_day.strftime("%Y-%m-%d")] = formatted_day_summary

#         # Move to the next day
#         current_day += timedelta(days=1)

#     return daily_summaries
# ------------------

# from collections import defaultdict, OrderedDict
# from datetime import datetime, timedelta

# def calculate_end_time_for_user(db: Session, picked_date: str, to_date: str) -> dict:
#     # Parse the input dates
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    
#     # Get current time for ongoing records
#     current_time = datetime.now()

#     # Function to process records for each date
#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field)
            
#             # Use current time if end_time is empty
#             if end_time is None:
#                 if start_time.date() == current_time.date():
#                     end_time = current_time  # Use current time for ongoing records
#                 else:
#                     continue  # Ignore past incomplete records

#             # Ensure the record matches the specific day
#             if start_time.date() == date:
#                 time_diff = end_time - start_time
#                 username = db.query(models.User_table).filter(
#                     models.User_table.user_id == getattr(record, user_field)
#                 ).first().username

#                 # Fetch work status for the assigned user
#                 tl_record = db.query(models.TL).filter(
#                     models.TL.Assigned_To == getattr(record, user_field),
#                     models.TL.status == 1  # Assuming status 1 means active or picked
#                 ).first()
                
#                 work_status = tl_record.work_status if tl_record else None

#                 # Accumulate time per user and activity
#                 user_times[username][activity] += time_diff
#                 if activity == 'in_progress':
#                     # Store total in-progress time separately
#                     user_times[username]['total_time_take'] += time_diff
                    
#                     # Step 1: Check work status and update completed time
#                     if work_status == "Completed":
#                         # Step 2: Update completed time to in-progress time
#                         if tl_record:
#                             # Calculate completed time based on in-progress total time
#                             completed_timestamp = start_time + user_times[username]['in_progress']

#                             # Assign the computed timestamp to completed_time
#                             tl_record.completed_time = completed_timestamp
#                             db.commit()  # Commit the update to the database

#                 # Add work status to the user's data
#                 user_times[username]['status'] = work_status

#     # Initialize an OrderedDict to maintain the order of days
#     daily_summaries = OrderedDict()

#     # Iterate over each day in the date range
#     current_day = picked_datett
#     while current_day <= to_datett:
#         # Initialize user time dictionary for this day
#         user_times = defaultdict(lambda: defaultdict(timedelta))
        
#         # Fetch and process records for each activity for this day
#         hold_records = db.query(models.HOLD).filter(
#             models.HOLD.hold_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.HOLD.hold_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'hold', hold_records, 
#                                 'hold_time_start', 'hold_time_end', 'user_id', user_times)

#         break_records = db.query(models.BREAK).filter(
#             models.BREAK.break_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.BREAK.break_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'break', break_records, 
#                                 'break_time_start', 'break_time_end', 'user_id', user_times)

#         meet_records = db.query(models.MEETING).filter(
#             models.MEETING.meeting_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.MEETING.meeting_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'meeting', meet_records, 
#                                 'meeting_time_start', 'meeting_time_end', 'user_id', user_times)

#         call_records = db.query(models.CALL).filter(
#             models.CALL.call_time_start >= current_day.replace(hour=0, minute=0, second=0),
#             models.CALL.call_time_start <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'call', call_records, 
#                                 'call_time_start', 'call_time_end', 'user_id', user_times)

#         inprogress_records = db.query(models.INPROGRESS).filter(
#             models.INPROGRESS.start_time >= current_day.replace(hour=0, minute=0, second=0),
#             models.INPROGRESS.start_time <= current_day.replace(hour=23, minute=59, second=59)
#         ).all()
#         process_records_for_day(current_day.date(), 'in_progress', inprogress_records, 
#                                 'start_time', 'end_time', 'user_id', user_times)

#         # Format the total time for this day
#         formatted_day_summary = {
#             username: {
#                 'in_progress': str(user_times[username]['in_progress']).split('.')[0],
#                 'break': str(user_times[username]['break']).split('.')[0],
#                 'meeting': str(user_times[username]['meeting']).split('.')[0],
#                 'call': str(user_times[username]['call']).split('.')[0],
#                 'hold': str(user_times[username]['hold']).split('.')[0],
#                 'status': user_times[username]['status'],
#                 'total_time_take': str(user_times[username]['total_time_take']).split('.')[0],
#                 'completed_time': str(user_times[username]['total_time_take']).split('.')[0] if user_times[username]['status'] == "Completed" else None
#             }
#             for username in user_times.keys()
#         }

#         # Store the formatted summary for this day
#         daily_summaries[current_day.strftime("%Y-%m-%d")] = formatted_day_summary

#         # Move to the next day
#         current_day += timedelta(days=1)

#     return daily_summaries

from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta


# def calculate_end_time_for_user(db: Session, picked_date: str, to_date: str) -> dict:
#     # Parse input dates
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # Current time for ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field)

#             if end_time is None and start_time.date() == date:
#                 end_time = current_time
#             elif end_time is None:
#                 continue

#             if start_time.date() == date:
#                 time_diff = end_time - start_time
#                 username = db.query(models.User_table).filter(
#                     models.User_table.user_id == getattr(record, user_field)
#                 ).first().username
#                 service_id = getattr(record, 'Service_ID')

#                 # Fetch work status from TL table based on Service ID
#                 tl_record = db.query(models.TL).filter(
#                     models.TL.Service_ID == service_id  # Correctly use Service_ID
#                 ).first()

#                 work_status = tl_record.work_status if tl_record else None

#                 # Initialize user_times if the username is not already there
#                 if username not in user_times:
#                     user_times[username] = defaultdict(lambda: defaultdict(timedelta))

#                 # Accumulate time spent on each activity
#                 user_times[username][service_id][activity] += time_diff

#                 # Handle Completed Status Logic
#                 if work_status == "Completed":
#                     # Check if in_progress time is greater than 0
#                     if user_times[username][service_id]['in_progress'] > timedelta(0):
#                         completed_time = user_times[username][service_id]['in_progress']
#                         user_times[username][service_id]['completed_time'] = str(completed_time).split('.')[0]
                        
#                         # Update the total time taken with the completed time
#                         if 'total_time_take' not in user_times[username][service_id]:
#                             user_times[username][service_id]['total_time_take'] = completed_time
#                         else:
#                             user_times[username][service_id]['total_time_take'] += completed_time
                            
#                         user_times[username][service_id]['in_progress'] = timedelta(0)  # Reset in_progress

#                         # Update TL record with completed time
#                         if tl_record:
#                             tl_record.completed_time = start_time + completed_time
#                             db.commit()

#                 # Store work status and TL metadata
#                 user_times[username][service_id]['status'] = work_status
#                 user_times[username][service_id]['scope'] = tl_record.Scope if tl_record else None
#                 user_times[username][service_id]['subscopes'] = tl_record.From if tl_record else None
#                 user_times[username][service_id]['nature_of_work'] = tl_record.nature_of_work if tl_record else None
#                 user_times[username][service_id]['entity'] = tl_record.name_of_entity if tl_record else None

#     daily_summaries = OrderedDict()

#     current_day = picked_datett
#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field) >= current_day.replace(hour=0, minute=0, second=0),
#                 getattr(model, start_field) <= current_day.replace(hour=23, minute=59, second=59)
#             ).all()
#             process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times)

#         # Format the daily summaries
#         formatted_day_summary = {
#             username: {
#                 service_id: {
#                     'in_progress': str(user_times[username][service_id]['in_progress']).split('.')[0],
#                     'break': str(user_times[username][service_id]['break']).split('.')[0],
#                     'meeting': str(user_times[username][service_id]['meeting']).split('.')[0],
#                     'call': str(user_times[username][service_id]['call']).split('.')[0],
#                     'hold': str(user_times[username][service_id]['hold']).split('.')[0],
#                     'status': user_times[username][service_id]['status'],
#                     'scope': user_times[username][service_id]['scope'],
#                     'subscopes': user_times[username][service_id]['subscopes'],
#                     'nature_of_work': user_times[username][service_id]['nature_of_work'],
#                     'entity': user_times[username][service_id]['entity'],
#                     'total_time_take': str(user_times[username][service_id]['total_time_take']).split('.')[0],
#                     'completed_time': (
#                         str(user_times[username][service_id]['completed_time']).split('.')[0]
#                         if user_times[username][service_id]['status'] == "Completed"
#                         else None
#                     )
#                 }
#                 for service_id in user_times[username]
#             }
#             for username in user_times
#         }

#         daily_summaries[current_day.strftime("%Y-%m-%d")] = formatted_day_summary
#         current_day += timedelta(days=1)

#     return daily_summaries


# def calculate_end_time_for_user(db: Session, picked_date: str, to_date: str) -> dict:
#     # Parse input dates
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # Current time for ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field)

#             if end_time is None and start_time.date() == date:
#                 end_time = current_time
#             elif end_time is None:
#                 continue

#             if start_time.date() == date:
#                 time_diff = end_time - start_time
#                 username = db.query(models.User_table).filter(
#                     models.User_table.user_id == getattr(record, user_field)
#                 ).first().username
#                 service_id = getattr(record, 'Service_ID')

#                 # Fetch work status from TL table based on Service ID
#                 tl_record = db.query(models.TL).filter(
#                     models.TL.Service_ID == service_id
#                 ).first()

#                 work_status = tl_record.work_status if tl_record else None

#                 # Initialize user_times if the username is not already there
#                 if username not in user_times:
#                     user_times[username] = defaultdict(lambda: defaultdict(timedelta))

#                 # Accumulate time spent on each activity
#                 user_times[username][service_id][activity] += time_diff

#                 # Handle Completed Status Logic
#                 if work_status == "Completed":
#                     # Set total_time_take to in_progress time
#                     user_times[username][service_id]['total_time_take'] = user_times[username][service_id]['in_progress']
#                     user_times[username][service_id]['completed_time'] = str(user_times[username][service_id]['total_time_take']).split('.')[0]
                    
#                     # Reset in_progress time
#                     user_times[username][service_id]['in_progress'] = timedelta(0)  # Reset in_progress

#                     # Update TL record with completed time
#                     if tl_record:
#                         tl_record.completed_time = start_time + user_times[username][service_id]['total_time_take']
#                         db.commit()

#                 else:
#                     # For ongoing tasks, set total_time_take to in_progress time
#                     user_times[username][service_id]['total_time_take'] = user_times[username][service_id]['in_progress']
#                     user_times[username][service_id]['completed_time'] = None        

#                 # Store work status and TL metadata
#                 user_times[username][service_id]['status'] = work_status
#                 user_times[username][service_id]['scope'] = tl_record.Scope if tl_record else None
#                 user_times[username][service_id]['subscopes'] = tl_record.From if tl_record else None
#                 user_times[username][service_id]['nature_of_work'] = tl_record.nature_of_work if tl_record else None
#                 user_times[username][service_id]['entity'] = tl_record.name_of_entity if tl_record else None

#     daily_summaries = OrderedDict()

#     current_day = picked_datett
#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field) >= current_day.replace(hour=0, minute=0, second=0),
#                 getattr(model, start_field) <= current_day.replace(hour=23, minute=59, second=59)
#             ).all()
#             process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times)

#         # Format the daily summaries
#         formatted_day_summary = {
#             username: {
#                 service_id: {
#                     'in_progress': str(user_times[username][service_id]['in_progress']).split('.')[0],
#                     'break': str(user_times[username][service_id]['break']).split('.')[0],
#                     'meeting': str(user_times[username][service_id]['meeting']).split('.')[0],
#                     'call': str(user_times[username][service_id]['call']).split('.')[0],
#                     'hold': str(user_times[username][service_id]['hold']).split('.')[0],
#                     'status': user_times[username][service_id]['status'],
#                     'scope': user_times[username][service_id]['scope'],
#                     'subscopes': user_times[username][service_id]['subscopes'],
#                     'nature_of_work': user_times[username][service_id]['nature_of_work'],
#                     'entity': user_times[username][service_id]['entity'],
#                     'total_time_take': str(user_times[username][service_id]['total_time_take']).split('.')[0],
#                     'completed_time': (
#                         str(user_times[username][service_id]['completed_time']).split('.')[0]
#                         if user_times[username][service_id]['status'] == "Completed"
#                         else "0:00:00"
#                     )
#                 }
#                 for service_id in user_times[username]
#             }
#             for username in user_times
#         }

#         daily_summaries[current_day.strftime("%Y-%m-%d")] = formatted_day_summary
#         current_day += timedelta(days=1)

#     return daily_summaries
# -----oct17 code work for current date
# from datetime import datetime, timedelta
# from collections import defaultdict, OrderedDict
# from sqlalchemy.orm import Session


# def str_to_timedelta(time_str):
#     """Convert HH:MM:SS string to timedelta."""
#     if time_str:
#         try:
#             h, m, s = map(int, time_str.split(':'))
#             return timedelta(hours=h, minutes=m, seconds=s)
#         except ValueError:
#             return timedelta(0)  # Handle invalid time strings gracefully
#     return timedelta(0)  # Default to zero if time_str is None


# def format_timedelta_to_str(td):
#     """Format timedelta to HH:MM:SS string."""
#     total_seconds = int(td.total_seconds())
#     hours, remainder = divmod(total_seconds, 3600)
#     minutes, seconds = divmod(remainder, 60)
#     return f"{hours:02}:{minutes:02}:{seconds:02}"


# def calculate_end_time_for_user(db: Session, picked_date: str, to_date: str) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # For ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

#             if start_time.date() > date:  # Skip records not for the current day
#                 continue

#             time_diff = end_time - start_time

#             # Fetch username from User_table based on user_id
#             user = db.query(models.User_table).filter(
#                 models.User_table.user_id == getattr(record, user_field)
#             ).first()
#             username = user.username if user else "Unknown"

#             service_id = getattr(record, 'Service_ID')

#             # Fetch TL record for work status and metadata
#             tl_record = db.query(models.TL).filter(
#                 models.TL.Service_ID == service_id
#             ).first()
#             work_status = tl_record.work_status if tl_record else None

#             if username not in user_times:
#                 user_times[username] = defaultdict(lambda: defaultdict(timedelta))

#             # Accumulate time for each activity
#             user_times[username][service_id][activity] += time_diff

#             # Update total time taken
#             if activity == 'in_progress':
#                 user_times[username][service_id]['total_time_take'] += time_diff

#             if work_status == "Completed":
#                 # Store the completed time as a string in HH:MM:SS format
#                 completed_time = format_timedelta_to_str(user_times[username][service_id]['total_time_take'])
#                 user_times[username][service_id]['completed_time'] = completed_time
#                 # Reset in-progress time
#                 user_times[username][service_id]['in_progress'] = timedelta(0)
#             else:
#                 user_times[username][service_id]['completed_time'] = "00:00:00"

#             user_times[username][service_id].update({
#                 'status': work_status,
#                 'scope': tl_record.Scope if tl_record else None,
#                 'subscopes': tl_record.From if tl_record else None,
#                 'nature_of_work': tl_record.nature_of_work if tl_record else None,
#                 'entity': tl_record.name_of_entity if tl_record else None,
#                 'no_of_items': tl_record.no_of_items if tl_record else None,
#             })

#     daily_summaries = OrderedDict()
#     current_day = picked_datett

#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field) <= current_day.replace(hour=23, minute=59, second=59)
#             ).all()
#             process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times)

#         # Format the summary for the current day
#         formatted_day_summary = {
#             username: {
#                 service_id: {
#                     'in_progress': format_timedelta_to_str(user_times[username][service_id]['in_progress']),
#                     'break': format_timedelta_to_str(user_times[username][service_id]['break']),
#                     'meeting': format_timedelta_to_str(user_times[username][service_id]['meeting']),
#                     'call': format_timedelta_to_str(user_times[username][service_id]['call']),
#                     'hold': format_timedelta_to_str(user_times[username][service_id]['hold']),
#                     'status': user_times[username][service_id]['status'],
#                     'scope': user_times[username][service_id]['scope'],
#                     'subscopes': user_times[username][service_id]['subscopes'],
#                     'nature_of_work': user_times[username][service_id]['nature_of_work'],
#                     'entity': user_times[username][service_id]['entity'],
#                     'no_of_items': user_times[username][service_id]['no_of_items'],
#                     'total_time_take': format_timedelta_to_str(user_times[username][service_id].get('total_time_take', timedelta(0))),
#                     'completed_time': user_times[username][service_id]['completed_time'],
#                 }
#                 for service_id in user_times[username]
#             }
#             for username in user_times
#         }

#         daily_summaries[current_day.strftime("%Y-%m-%d")] = formatted_day_summary
#         current_day += timedelta(days=1)

#     return daily_summaries
# --------------------oct21

# from datetime import datetime, timedelta
# from collections import defaultdict, OrderedDict
# from sqlalchemy.orm import Session

# def str_to_timedelta(time_str):
#     """Convert HH:MM:SS string to timedelta."""
#     if time_str:
#         try:
#             h, m, s = map(int, time_str.split(':'))
#             return timedelta(hours=h, minutes=m, seconds=s)
#         except ValueError:
#             return timedelta(0)  # Handle invalid time strings gracefully
#     return timedelta(0)

# def format_timedelta_to_str(td):
#     """Format timedelta to HH:MM:SS string."""
#     total_seconds = int(td.total_seconds())
#     hours, remainder = divmod(total_seconds, 3600)
#     minutes, seconds = divmod(remainder, 60)
#     return f"{hours:02}:{minutes:02}:{seconds:02}"

# def calculate_end_time_for_user(db: Session, picked_date: str, to_date: str) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # For ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         has_activity_for_day = False  # Track if any valid data exists for the day

#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

#             # Ensure the record falls exactly on the specified date
#             if start_time.date() != date:
#                 continue

#             time_diff = end_time - start_time
#             has_activity_for_day = True  # Mark that valid data exists

#             # Fetch username from User_table
#             user = db.query(models.User_table).filter(
#                 models.User_table.user_id == getattr(record, user_field)
#             ).first()
#             username = user.username if user else "Unknown"

#             service_id = getattr(record, 'Service_ID')

#             # Fetch TL record for work status and metadata
#             tl_record = db.query(models.TL).filter(
#                 models.TL.Service_ID == service_id
#             ).join(models.scope).join(models.sub_scope).join(models.Nature_Of_Work).first()
            
#             work_status = tl_record.work_status if tl_record else None

#             if username not in user_times:
#                 user_times[username] = defaultdict(lambda: defaultdict(timedelta))

#             # Accumulate time for each activity
#             user_times[username][service_id][activity] += time_diff

#             # Update total time taken
#             if activity == 'in_progress':
#                 user_times[username][service_id]['total_time_take'] += time_diff

#             if work_status == "Completed":
#                 completed_time = format_timedelta_to_str(user_times[username][service_id]['total_time_take'])
#                 user_times[username][service_id]['completed_time'] = completed_time
#                 user_times[username][service_id]['in_progress'] = timedelta(0)  # Reset in-progress time
#             else:
#                 user_times[username][service_id]['completed_time'] = "00:00:00"

#             if tl_record:
#                 user_times[username][service_id].update({
#                     'status': work_status,
#                     'scope': tl_record.scope.scope if tl_record else None,
#                     'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
#                     'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
#                     'entity': tl_record.name_of_entity if tl_record else None,
#                     'no_of_items': tl_record.no_of_items if tl_record else None,
#                 })

#         return has_activity_for_day  # Return whether any activity was processed for the day

#     daily_summaries = OrderedDict()
#     current_day = picked_datett

#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Track if any activities were processed for the current day
#         day_has_data = False

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field).between(
#                     current_day.replace(hour=0, minute=0, second=0),
#                     current_day.replace(hour=23, minute=59, second=59)
#                 )
#             ).all()


#             # Process records and check if there was any valid data
#             if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
#                 day_has_data = True

#         # Only add the summary if there was data for the day
#         if day_has_data:
#             formatted_day_summary = {
#                 username: {
#                     service_id: {
#                         'in_progress': format_timedelta_to_str(user_times[username][service_id]['in_progress']),
#                         'break': format_timedelta_to_str(user_times[username][service_id]['break']),
#                         'meeting': format_timedelta_to_str(user_times[username][service_id]['meeting']),
#                         'call': format_timedelta_to_str(user_times[username][service_id]['call']),
#                         'hold': format_timedelta_to_str(user_times[username][service_id]['hold']),
#                         'status': user_times[username][service_id]['status'],
#                         'scope': user_times[username][service_id]['scope'],
#                         'subscopes': user_times[username][service_id]['subscopes'],
#                         'nature_of_work': user_times[username][service_id]['nature_of_work'],
#                         'entity': user_times[username][service_id]['entity'],
#                         'no_of_items': user_times[username][service_id]['no_of_items'],
#                         'total_time_take': format_timedelta_to_str(user_times[username][service_id]['total_time_take']),
#                         'completed_time': user_times[username][service_id]['completed_time'],
#                     }
#                     for service_id in user_times[username]
#                 }
#                 for username in user_times
#             }
#             daily_summaries[current_day.strftime("%Y-%m-%d")] = formatted_day_summary

#         current_day += timedelta(days=1)

#     return daily_summaries

                 

from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from sqlalchemy.orm import Session

def str_to_timedelta(time_str):
    """Convert HH:MM:SS string to timedelta."""
    if time_str:
        try:
            h, m, s = map(int, time_str.split(':'))
            return timedelta(hours=h, minutes=m, seconds=s)
        except ValueError:
            return timedelta(0)  # Handle invalid strings gracefully
    return timedelta(0)

def format_timedelta_to_str(td):
    """Format timedelta to HH:MM:SS string."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user(db: Session, picked_date: str, to_date: str) -> dict:
    """Calculate activity times per user and service for the given date range."""
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        """Process records for each activity."""
        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current time if still ongoing

            if start_time.date() != date:  # Ensure record is for the exact date
                continue

            time_diff = end_time - start_time

            # Fetch user information
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            username = user.username if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for metadata
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).join(models.scope).join(models.sub_scope).join(models.Nature_Of_Work).first()
            
            work_status = tl_record.work_status if tl_record else None

            # Initialize user times dictionary if not present
            if username not in user_times:
                user_times[username] = defaultdict(lambda: defaultdict(timedelta))

            # Accumulate time for the current activity
            user_times[username][service_id][activity] += time_diff

            # Update total time taken for 'in_progress' activities
            if activity == 'in_progress':
                user_times[username][service_id]['total_time_take'] += time_diff

            # Handle completed status
            if work_status == "Completed":
                completed_time = format_timedelta_to_str(user_times[username][service_id]['total_time_take'])
                user_times[username][service_id]['completed_time'] = completed_time
                user_times[username][service_id]['in_progress'] = timedelta(0)  # Reset in-progress time
            else:
                user_times[username][service_id]['completed_time'] = "00:00:00"

            # Add metadata from TL record
            if tl_record:
                user_times[username][service_id].update({
                    'status': work_status,
                    'scope': tl_record.scope.scope,
                    'subscopes': tl_record.sub_scope.sub_scope,
                    'nature_of_work': tl_record._nature_of_work.work_name,
                    'entity': tl_record.name_of_entity,
                    'no_of_items': tl_record.no_of_items,
                })

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records for the day
            process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times)

        # Only add the summary if there was data for the day
        if user_times:
            formatted_day_summary = {
                username: {
                    service_id: {
                        'in_progress': format_timedelta_to_str(user_times[username][service_id]['in_progress']),
                        'break': format_timedelta_to_str(user_times[username][service_id]['break']),
                        'meeting': format_timedelta_to_str(user_times[username][service_id]['meeting']),
                        'call': format_timedelta_to_str(user_times[username][service_id]['call']),
                        'hold': format_timedelta_to_str(user_times[username][service_id]['hold']),
                        'status': user_times[username][service_id]['status'],
                        'scope': user_times[username][service_id]['scope'],
                        'subscopes': user_times[username][service_id]['subscopes'],
                        'nature_of_work': user_times[username][service_id]['nature_of_work'],
                        'entity': user_times[username][service_id]['entity'],
                        'no_of_items': user_times[username][service_id]['no_of_items'],
                        'total_time_take': format_timedelta_to_str(user_times[username][service_id]['total_time_take']),
                        'completed_time': user_times[username][service_id]['completed_time'],
                    }
                    for service_id in user_times[username]
                }
                for username in user_times
            }
            daily_summaries[current_day.strftime("%Y-%m-%d")] = formatted_day_summary

        current_day += timedelta(days=1)

    return daily_summaries


# ------

from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from sqlalchemy.orm import Session

def str_to_timedelta(time_str):
    """Convert HH:MM:SS string to timedelta."""
    if time_str:
        try:
            h, m, s = map(int, time_str.split(':'))
            return timedelta(hours=h, minutes=m, seconds=s)
        except ValueError:
            return timedelta(0)  # Handle invalid strings gracefully
    return timedelta(0)

def format_timedelta_to_str(td):
    """Format timedelta to HH:MM:SS string."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user1s(db: Session, picked_date: str, to_date: str) -> list:
    """Calculate activity times per user and service for the given date range."""
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        """Process records for each activity."""
        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current time if still ongoing

            if start_time.date() != date:  # Ensure record is for the exact date
                continue

            time_diff = end_time - start_time

            # Fetch user information
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            username = user.username if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for metadata
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).join(models.scope).join(models.sub_scope).join(models.Nature_Of_Work).first()
            
            work_status = tl_record.work_status if tl_record else None

            # Initialize user times dictionary if not present
            if username not in user_times:
                user_times[username] = defaultdict(lambda: defaultdict(timedelta))

            # Accumulate time for the current activity
            user_times[username][service_id][activity] += time_diff

            # Update total time taken for 'in_progress' activities
            if activity == 'in_progress':
                user_times[username][service_id]['total_time_take'] += time_diff

            # Handle completed status
            if work_status == "Completed":
                completed_time = format_timedelta_to_str(user_times[username][service_id]['total_time_take'])
                user_times[username][service_id]['completed_time'] = completed_time
                user_times[username][service_id]['in_progress'] = timedelta(0)  # Reset in-progress time
            else:
                user_times[username][service_id]['completed_time'] = "00:00:00"

            # Add metadata from TL record
            if tl_record:
                user_times[username][service_id].update({
                    'status': work_status,
                    'scope': tl_record.scope.scope,
                    'subscopes': tl_record.sub_scope.sub_scope,
                    'nature_of_work': tl_record._nature_of_work.work_name,
                    'entity': tl_record.name_of_entity,
                    'no_of_items': tl_record.no_of_items,
                })

    # Store the final results as a list of dictionaries for the desired output format
    result = []

    # Loop through each day and generate user summaries
    current_day = picked_datett
    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Process records for each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process the records and populate user_times
            process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times)

        # Format the results into the required structure
        for username, services in user_times.items():
            for service_id, data in services.items():
                result.append({
                    "username": username,
                    "Service_ID": service_id,
                    "Date": current_day.strftime("%Y-%m-%d"),
                    "in_progress": format_timedelta_to_str(data['in_progress']),
                    "break": format_timedelta_to_str(data['break']),
                    "meeting": format_timedelta_to_str(data['meeting']),
                    "call": format_timedelta_to_str(data['call']),
                    "hold": format_timedelta_to_str(data['hold']),
                    "status": data['status'],
                    "scope": data['scope'],
                    "subscopes": data['subscopes'],
                    "nature_of_work": data['nature_of_work'],
                    "entity": data['entity'],
                    "no_of_items": data['no_of_items'],
                    "total_time_take": format_timedelta_to_str(data['total_time_take']),
                    "completed_time": data['completed_time']
                })

        current_day += timedelta(days=1)

    return result  # Return the list directly


# -----
def calculate_end_time_for_user2(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch username from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            username = user.username if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).join(models.scope).join(models.sub_scope).join(models.Nature_Of_Work).first()

            # Accumulate time for each activity
            if username not in user_times:
                user_times[username] = defaultdict(lambda: defaultdict(timedelta))

            user_times[username][service_id]['total_time_take'] += time_diff

            # Store scope, sub-scope, and nature of work for the user
            if tl_record:
                user_times[username][service_id].update({
                    'scope': tl_record.scope.scope if tl_record else None,
                    'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:            
        # service_id = getattr(records, 'Service_ID')

            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

        # Process records and check if there was any valid data
        if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
            day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): {
                    username: {
                        'scope': user_times[username][service_id]['scope'],
                        'subscopes': user_times[username][service_id]['subscopes'],
                        'nature_of_work': user_times[username][service_id]['nature_of_work'],
                        'total_time_take': format_timedelta_to_str(user_times[username][service_id]['total_time_take']),
                    }
                    for service_id in user_times[username]
                }
                for username in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries
# -----------------------

# def calculate_end_time_for_user3(db: Session, picked_date: str, to_date: str) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # For ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         has_activity_for_day = False  # Track if any valid data exists for the day

#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

#             # Ensure the record falls exactly on the specified date
#             if start_time.date() != date:
#                 continue

#             time_diff = end_time - start_time
#             has_activity_for_day = True  # Mark that valid data exists

#             # Fetch username from User_table
#             user = db.query(models.User_table).filter(
#                 models.User_table.user_id == getattr(record, user_field)
#             ).first()
#             username = user.username if user else "Unknown"

#             service_id = getattr(record, 'Service_ID')

#             # Fetch TL record for work status and metadata, including entity
#             tl_record = db.query(models.TL).filter(
#                 models.TL.Service_ID == service_id
#             ).first()

#             # Get the entity name and work status
#             entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
#             work_status = tl_record.work_status if tl_record else "Unknown Status"

#             # Accumulate time for each activity
#             if (username, entity_name) not in user_times:
#                 user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

#             user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

#             # Store scope, sub-scope, nature of work, and work status for the user
#             if tl_record:
#                 user_times[(username, entity_name)][service_id].update({
#                     'scope': tl_record.scope.scope if tl_record else None,
#                     'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
#                     'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
#                     'workstatus': work_status,  # Add work status to user times
#                     'entity': entity_name
#                 })

#         return has_activity_for_day  # Return whether any activity was processed for the day

#     daily_summaries = OrderedDict()
#     current_day = picked_datett

#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Track if any activities were processed for the current day
#         day_has_data = False

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field).between(
#                     current_day.replace(hour=0, minute=0, second=0),
#                     current_day.replace(hour=23, minute=59, second=59)
#                 )
#             ).all()

#             # Process records and check if there was any valid data
#             if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
#                 day_has_data = True

#         # Only add the summary if there was data for the day
#         if day_has_data:
#             formatted_day_summary = {
#                 current_day.strftime("%Y-%m-%d"): {
#                     f"{username} ({entity_name})": {  # Include entity name in the summary key
#                         'Entity': user_times[(username, entity_name)][service_id]['entity'],
#                         'scope': user_times[(username, entity_name)][service_id]['scope'],
#                         'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
#                         'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
#                         'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
#                         'workstatus': user_times[(username, entity_name)][service_id]['workstatus'],  # Include work status
#                         'Remarks' : None,
                        
#                     }
#                     for service_id in user_times[(username, entity_name)]
#                 }
#                 for (username, entity_name) in user_times
#             }
#             daily_summaries.update(formatted_day_summary)

#         current_day += timedelta(days=1)

#     return daily_summaries

def calculate_end_time_for_user3(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            
            # Construct the username from firstname and lastname
            if user:
                username = f"{user.firstname}{user.lastname}"  # Concatenate firstname and lastname
            else:
                username = "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and work status
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            work_status = tl_record.work_status if tl_record else "Unknown Status"

            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, entity_name)][service_id].update({
                    'scope': tl_record.scope.scope if tl_record else None,
                    'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                    'workstatus': work_status,  # Add work status to user times
                    'entity': entity_name
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Entity': user_times[(username, entity_name)][service_id]['entity'],
                        'Worked_By': username,  # Add username as a separate field
                        'scope': user_times[(username, entity_name)][service_id]['scope'],
                        'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
                        'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
                        'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
                        'Status': user_times[(username, entity_name)][service_id]['workstatus'],
                        'Remarks': None,
                    }
                    for service_id in user_times[(username, entity_name)]
                ]
                for (username, entity_name) in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries

def calculate_end_time_for_user4(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            
            # Construct the username from firstname and lastname
            if user:
                username = f"{user.firstname}{user.lastname}"  # Concatenate firstname and lastname
            else:
                username = "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and work status
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            work_status = tl_record.work_status if tl_record else "Unknown Status"
            no_of_items = tl_record.no_of_items if tl_record else "N/A"
            # created_on = tl_record.created_on if tl_record else None
            created_on = tl_record.created_on.strftime("%Y-%m-%d") if tl_record.created_on else None  # Format created_on
            completed_date = tl_record.completed_time.strftime("%Y-%m-%d") if tl_record.completed_time else None
            

            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, entity_name)][service_id].update({
                    'scope': tl_record.scope.scope if tl_record else None,
                    'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                    'workstatus': work_status,  # Add work status to user times
                    'entity': entity_name,
                    'no_of_items': no_of_items,
                    'created_on': created_on,
                    'completed_date': completed_date
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Entity': user_times[(username, entity_name)][service_id]['entity'],
                        'scope': user_times[(username, entity_name)][service_id]['scope'],
                        'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
                        'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
                        'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
                        'Count': user_times[(username, entity_name)][service_id]['no_of_items'],
                        'Worked_By': username,  # Add username as a separate field
                        'created_on': user_times[(username, entity_name)][service_id]['created_on'],
                        'Completed_Date': user_times[(username, entity_name)][service_id]['completed_date'],
                        'Remarks': None,
                        'Status': user_times[(username, entity_name)][service_id]['workstatus'],
                    }
                    for service_id in user_times[(username, entity_name)]
                ]
                for (username, entity_name) in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries

def calculate_end_time_for_user5(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            
            # Construct the username from firstname and lastname
            if user:
                username = f"{user.firstname}{user.lastname}"  # Concatenate firstname and lastname
            else:
                username = "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and work status
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            work_status = tl_record.work_status if tl_record else "Unknown Status"
            no_of_items = tl_record.no_of_items if tl_record else "N/A"
            # created_on = tl_record.created_on if tl_record else None
            created_on = tl_record.created_on.strftime("%Y-%m-%d") if tl_record.created_on else None  # Format created_on

            

            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, entity_name)][service_id].update({
                    'scope': tl_record.scope.scope if tl_record else None,
                    'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                    'workstatus': work_status,  # Add work status to user times
                    'entity': entity_name,
                    'no_of_items': no_of_items,
                    'created_on': created_on
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Entity': user_times[(username, entity_name)][service_id]['entity'],
                        'scope': user_times[(username, entity_name)][service_id]['scope'],
                        'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
                        'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
                        'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
                        'Worked_By': username,  # Add username as a separate field
                        'created_Date': user_times[(username, entity_name)][service_id]['created_on'],
                        'Status': user_times[(username, entity_name)][service_id]['workstatus'],
                        'Count': user_times[(username, entity_name)][service_id]['no_of_items'],

                    }
                    for service_id in user_times[(username, entity_name)]
                ]
                for (username, entity_name) in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries

def calculate_end_time_for_user6(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            
            # Construct the username from firstname and lastname
            if user:
                username = f"{user.firstname}{user.lastname}"  # Concatenate firstname and lastname
            else:
                username = "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and work status
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            work_status = tl_record.work_status if tl_record else "Unknown Status"
            # created_on = tl_record.created_on if tl_record else None
            created_on = tl_record.created_on.strftime("%Y-%m-%d") if tl_record.created_on else None  # Format created_on

            

            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, entity_name)][service_id].update({
                    'scope': tl_record.scope.scope if tl_record else None,
                    'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                    'workstatus': work_status,  # Add work status to user times
                    'entity': entity_name,
                    'created_on': created_on
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Entity': user_times[(username, entity_name)][service_id]['entity'],
                        'scope': user_times[(username, entity_name)][service_id]['scope'],
                        'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
                        'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
                        'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
                        'Worked_By': username,  # Add username as a separate field
                        'created_Date': user_times[(username, entity_name)][service_id]['created_on'],
                        'Status': user_times[(username, entity_name)][service_id]['workstatus'],
                        'Remarks': None

                    }
                    for service_id in user_times[(username, entity_name)]
                ]
                for (username, entity_name) in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries




def calculate_end_time_for_user7(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            
            # Construct the username from firstname and lastname
            if user:
                username = f"{user.firstname}{user.lastname}"  # Concatenate firstname and lastname
            else:
                username = "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and work status
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            no_of_items = tl_record.no_of_items if tl_record else "N/A"
            gstintan = tl_record.gst_or_tan if tl_record else "N/A"
            

            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, entity_name)][service_id].update({
                    'gst': gstintan,
                    
                    'entity': entity_name,
                    'no_of_items': no_of_items,
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Name_of_the_Entity': user_times[(username, entity_name)][service_id]['entity'],
                        'GSTIN/TAN': user_times[(username, entity_name)][service_id]['gst'],
                        
                        'Count': user_times[(username, entity_name)][service_id]['no_of_items'],
                        'Remarks': None

                    }
                    for service_id in user_times[(username, entity_name)]
                ]
                for (username, entity_name) in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries









#--------------------cornjob update for totaltime of all table like break,call,metting,hold,inprogress,idealtime

from sqlalchemy import func, and_, cast
from sqlalchemy.types import Interval
from datetime import date
from .models import User_table, TL 

def get_all_user_ids(db: Session):
    return [user.user_id for user in db.query(User_table).all()]  # Fetch all user IDs

# def get_all_service_ids(db: Session):
#     return [service.Service_ID for service in db.query(TL).all()]  # Fetch all service IDs # Fetch all service IDs


def get_all_service_ids(db: Session):
    return [service.Service_ID for service in db.query(models.TL).filter(models.TL.status == 1).all()]


def fetch_total_time(db: Session, user_id: int, service_id: int):
    # Set the current date to today
    current_date = date.today()

    # ------------------- In-progress Time Calculation ------------------- #
    total_inprogress_time = db.query(func.sum(
        cast(models.INPROGRESS.total_time, Interval)
    )).filter(
        and_(
            models.INPROGRESS.user_id == user_id,
            models.INPROGRESS.Service_ID == service_id,
            func.date(models.INPROGRESS.start_time) == current_date
        )
    ).scalar()

    # ------------------- Hold Time Calculation ------------------- #
    total_hold_time = db.query(func.sum(
        cast(models.HOLD.hold_total_time, Interval)
    )).filter(
        and_(
            models.HOLD.user_id == user_id,
            models.HOLD.Service_ID == service_id,
            func.date(models.HOLD.hold_time_start) == current_date
        )
    ).scalar()

    # ------------------- Break Time Calculation ------------------- #
    total_break_time = db.query(func.sum(
        cast(models.BREAK.break_total_time, Interval)
    )).filter(
        and_(
            models.BREAK.user_id == user_id,
            models.BREAK.Service_ID == service_id,
            func.date(models.BREAK.break_time_start) == current_date
        )
    ).scalar()

    # ------------------- Meeting Time Calculation ------------------- #
    total_meeting_time = db.query(func.sum(
        cast(models.MEETING.meet_total_time, Interval)
    )).filter(
        and_(
            models.MEETING.user_id == user_id,
            models.MEETING.Service_ID == service_id,
            func.date(models.MEETING.meeting_time_start) == current_date
        )
    ).scalar()

    # ------------------- Call Time Calculation ------------------- #
    total_call_time = db.query(func.sum(
        cast(models.CALL.call_total_time, Interval)
    )).filter(
        and_(
            models.CALL.user_id == user_id,
            models.CALL.Service_ID == service_id,
            func.date(models.CALL.call_time_start) == current_date
        )
    ).scalar()

    # ------------------- Ideal Time Calculation ------------------- #
    total_ideal_time = db.query(func.sum(
        cast(models.WorkSession.total_time_worked, Interval)
    )).filter(
        and_(
            models.WorkSession.user_id == user_id,
            func.date(models.WorkSession.start_time) == current_date
        )
    ).scalar()

     # ------------------- Ideal Time Calculation ------------------- #
    total_completed_time = db.query(func.sum(
        cast(models.INPROGRESS.total_time, Interval)
    )).filter(
        and_(
            models.INPROGRESS.user_id == user_id,
            models.INPROGRESS.Service_ID == service_id,
            func.date(models.INPROGRESS.start_time) == current_date
        )
    ).scalar()

    # Check if any of the total times are not None or non-zero
    if any(x is not None and x != 0 for x in [total_inprogress_time, total_hold_time, total_break_time, total_meeting_time, total_call_time, total_ideal_time,total_completed_time]):
        # Check for existing entry in TotalTimeTaken
        existing_entry = db.query(models.TotalTimeTaken).filter(
            and_(
                models.TotalTimeTaken.user_id == user_id,
                models.TotalTimeTaken.service_id == service_id,
                models.TotalTimeTaken.date == current_date
            )
        ).first()

        # If entry exists, update it; otherwise, create a new one
        if existing_entry:
            existing_entry.total_inprogress_time = str(total_inprogress_time) if total_inprogress_time else "00:00:00"
            existing_entry.total_hold_time = str(total_hold_time) if total_hold_time else "00:00:00"
            existing_entry.total_break_time = str(total_break_time) if total_break_time else "00:00:00"
            existing_entry.total_meeting_time = str(total_meeting_time) if total_meeting_time else "00:00:00"
            existing_entry.total_call_time = str(total_call_time) if total_call_time else "00:00:00"
            existing_entry.total_ideal_time = str(total_ideal_time) if total_ideal_time else "00:00:00"
            existing_entry.total_completed_time = str(total_completed_time) if total_completed_time else "00:00:00"
        else:
            # Create a new entry with calculated fields
            new_entry = models.TotalTimeTaken(
                user_id=user_id,
                service_id=service_id,
                date=current_date,
                total_inprogress_time=str(total_inprogress_time) if total_inprogress_time else "00:00:00",
                total_hold_time=str(total_hold_time) if total_hold_time else "00:00:00",
                total_break_time=str(total_break_time) if total_break_time else "00:00:00",
                total_meeting_time=str(total_meeting_time) if total_meeting_time else "00:00:00",
                total_call_time=str(total_call_time) if total_call_time else "00:00:00",
                total_ideal_time=str(total_ideal_time) if total_ideal_time else "00:00:00",
                total_completed_time=str(total_completed_time) if total_ideal_time else "00:00:00",
            )
            db.add(new_entry)

        # Commit the db to save changes
        db.commit()


# ------------------------------------end    


















# from sqlalchemy.orm import Session
# from sqlalchemy import and_, func, cast, Interval
# from datetime import date, timedelta
# from sqlalchemy.dialects.postgresql import INTERVAL
# from sqlalchemy import func, and_, cast

# async def fetch_total_time1(db: Session, user_id: int, service_id: int, picked_date: str, to_date: str):
#     # Set the current date to today
#     current_date = date.today()

#     # ------------------- In-progress Time Calculation ------------------- #
#     total_inprogress_time_query = db.query(func.sum(
#         cast(models.INPROGRESS.total_time, INTERVAL)
#     )).filter(
#         and_(
#             models.INPROGRESS.user_id == user_id,
#             models.INPROGRESS.Service_ID == service_id,
#             func.date(models.INPROGRESS.start_time) == current_date
#         )
#     )
    
#     total_inprogress_time = total_inprogress_time_query.scalar() or timedelta(0)

#     # Add logic to handle ongoing records
#     ongoing_time = db.query(
#         func.sum(func.extract('epoch', func.now()) - func.extract('epoch', models.INPROGRESS.start_time))
#     ).filter(
#         and_(
#             models.INPROGRESS.user_id == user_id,
#             models.INPROGRESS.Service_ID == service_id,
#             func.date(models.INPROGRESS.start_time) == current_date,
#             models.INPROGRESS.end_time == None  # No end_time means it's ongoing
#         )
#     ).scalar()

#     if ongoing_time is not None:
#         # Convert ongoing_time from Decimal to float before using it
#         ongoing_time_seconds = float(ongoing_time)  # or use int(ongoing_time) if appropriate
#         total_inprogress_time += timedelta(seconds=ongoing_time_seconds)

#     # ------------------- Hold Time Calculation ------------------- #
#     total_hold_time = db.query(func.sum(
#         cast(models.HOLD.hold_total_time, INTERVAL)
#     )).filter(
#         and_(
#             models.HOLD.user_id == user_id,
#             models.HOLD.Service_ID == service_id,
#             func.date(models.HOLD.hold_time_start) == current_date
#         )
#     ).scalar()

#     # ------------------- Break Time Calculation ------------------- #
#     total_break_time = db.query(func.sum(
#         cast(models.BREAK.break_total_time, INTERVAL)
#     )).filter(
#         and_(
#             models.BREAK.user_id == user_id,
#             models.BREAK.Service_ID == service_id,
#             func.date(models.BREAK.break_time_start) == current_date
#         )
#     ).scalar()

#     # ------------------- Meeting Time Calculation ------------------- #
#     total_meeting_time = db.query(func.sum(
#         cast(models.MEETING.meet_total_time, INTERVAL)
#     )).filter(
#         and_(
#             models.MEETING.user_id == user_id,
#             models.MEETING.Service_ID == service_id,
#             func.date(models.MEETING.meeting_time_start) == current_date
#         )
#     ).scalar()

#     # ------------------- Call Time Calculation ------------------- #
#     total_call_time = db.query(func.sum(
#         cast(models.CALL.call_total_time, INTERVAL)
#     )).filter(
#         and_(
#             models.CALL.user_id == user_id,
#             models.CALL.Service_ID == service_id,
#             func.date(models.CALL.call_time_start) == current_date
#         )
#     ).scalar()

#     # ------------------- Ideal Time Calculation ------------------- #
#     total_ideal_time = db.query(func.sum(
#         cast(models.WorkSession.total_time_worked, INTERVAL)
#     )).filter(
#         and_(
#             models.WorkSession.user_id == user_id,
#             func.date(models.WorkSession.start_time) == current_date
#         )
#     ).scalar()

#     # Check if any of the total times are not None or non-zero
#     if any(x is not None and x != 0 for x in [total_inprogress_time, total_hold_time, total_break_time, total_meeting_time, total_call_time, total_ideal_time]):
#         # Check for existing entry in TotalTimeTaken
#         existing_entry = db.query(models.TotalTimeTaken).filter(
#             and_(
#                 models.TotalTimeTaken.user_id == user_id,
#                 models.TotalTimeTaken.service_id == service_id,
#                 models.TotalTimeTaken.date == current_date
#             )
#         ).first()

#         # If entry exists, update it; otherwise, create a new one
#         if existing_entry:
#             existing_entry.total_inprogress_time = total_inprogress_time
#             existing_entry.total_hold_time = total_hold_time
#             existing_entry.total_break_time = total_break_time
#             existing_entry.total_meeting_time = total_meeting_time
#             existing_entry.total_call_time = total_call_time
#             existing_entry.total_ideal_time = total_ideal_time
#         else:
#             # Create a new entry with calculated fields
#             new_entry = models.TotalTimeTaken(
#                 user_id=user_id,
#                 service_id=service_id,
#                 date=current_date,
#                 total_inprogress_time=total_inprogress_time,
#                 total_hold_time=total_hold_time,
#                 total_break_time=total_break_time,
#                 total_meeting_time=total_meeting_time,
#                 total_call_time=total_call_time,
#                 total_ideal_time=total_ideal_time,
#             )
#             db.add(new_entry)

#         # Commit the db to save changes
#         db.commit()


# --------------------------------elan code end





## Function to reallocate a service
def reallocate_service(db: Session, service_id: int, user_id: int, admin_id: int, current_user_id: int, remarks: str):
    # Fetch the original record
    db_res = db.query(TL).filter(TL.Service_ID == service_id).first()
    
    if not db_res:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update the existing record with reallocation details
    db_res.work_status = "Re-allocated"
    db_res.remarks = remarks
    db_res.reallocated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.commit()

    # Create new record with the same data as the original
    db_insert = TL(
        name_of_entity=db_res.name_of_entity,
        gst_or_tan=db_res.gst_or_tan,
        gst_tan=db_res.gst_tan,
        client_grade=db_res.client_grade,
        Priority=db_res.Priority,
        Assigned_By=db_res.Assigned_By,
        estimated_d_o_d=db_res.estimated_d_o_d,
        estimated_time=db_res.estimated_time,
        Scope=db_res.Scope,
        nature_of_work=db_res.nature_of_work,
        From=db_res.From,
        Actual_d_o_d=db_res.Actual_d_o_d,
        work_status="Not Picked",  # Set initial work status for the new record
        no_of_items=db_res.no_of_items,
        remarks=db_res.remarks,
        completed_time=db_res.completed_time,
        reallocated_by=current_user_id,  # Track who reallocated
        Assigned_To=admin_id,  # New admin assignment
    )

    # Add new record to the session
    db.add(db_insert)
    
    # Commit new records once after the loop
    db.commit()  

    # Log the reallocation
    reallocation_entry = models.REALLOCATED(
        Service_ID=service_id,
        user_id=user_id,
        re_time_start=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    
    # Add the reallocation entry to the session
    db.add(reallocation_entry)
    db.commit()

    return "Success"



# ---------------------------pasupathi rports data 
def calculate_end_time_for_user2(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch username from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            username = user.username if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).join(models.scope).join(models.sub_scope).join(models.Nature_Of_Work).first()

            # Accumulate time for each activity
            if username not in user_times:
                user_times[username] = defaultdict(lambda: defaultdict(timedelta))

            user_times[username][service_id]['total_time_take'] += time_diff

            # Store scope, sub-scope, and nature of work for the user
            if tl_record:
                user_times[username][service_id].update({
                    'scope': tl_record.scope.scope if tl_record else None,
                    'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:            
        # service_id = getattr(records, 'Service_ID')

            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

        # Process records and check if there was any valid data
        if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
            day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): {
                    username: {
                        'scope': user_times[username][service_id]['scope'],
                        'subscopes': user_times[username][service_id]['subscopes'],
                        'nature_of_work': user_times[username][service_id]['nature_of_work'],
                        'total_time_take': format_timedelta_to_str(user_times[username][service_id]['total_time_take']),
                    }
                    for service_id in user_times[username]
                }
                for username in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries
# -----------------------

# def calculate_end_time_for_user3(db: Session, picked_date: str, to_date: str) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # For ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         has_activity_for_day = False  # Track if any valid data exists for the day

#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

#             # Ensure the record falls exactly on the specified date
#             if start_time.date() != date:
#                 continue

#             time_diff = end_time - start_time
#             has_activity_for_day = True  # Mark that valid data exists

#             # Fetch username from User_table
#             user = db.query(models.User_table).filter(
#                 models.User_table.user_id == getattr(record, user_field)
#             ).first()
#             username = user.username if user else "Unknown"

#             service_id = getattr(record, 'Service_ID')

#             # Fetch TL record for work status and metadata, including entity
#             tl_record = db.query(models.TL).filter(
#                 models.TL.Service_ID == service_id
#             ).first()

#             # Get the entity name and work status
#             entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
#             work_status = tl_record.work_status if tl_record else "Unknown Status"

#             # Accumulate time for each activity
#             if (username, entity_name) not in user_times:
#                 user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

#             user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

#             # Store scope, sub-scope, nature of work, and work status for the user
#             if tl_record:
#                 user_times[(username, entity_name)][service_id].update({
#                     'scope': tl_record.scope.scope if tl_record else None,
#                     'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
#                     'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
#                     'workstatus': work_status,  # Add work status to user times
#                     'entity': entity_name
#                 })

#         return has_activity_for_day  # Return whether any activity was processed for the day

#     daily_summaries = OrderedDict()
#     current_day = picked_datett

#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Track if any activities were processed for the current day
#         day_has_data = False

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field).between(
#                     current_day.replace(hour=0, minute=0, second=0),
#                     current_day.replace(hour=23, minute=59, second=59)
#                 )
#             ).all()

#             # Process records and check if there was any valid data
#             if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
#                 day_has_data = True

#         # Only add the summary if there was data for the day
#         if day_has_data:
#             formatted_day_summary = {
#                 current_day.strftime("%Y-%m-%d"): {
#                     f"{username} ({entity_name})": {  # Include entity name in the summary key
#                         'Entity': user_times[(username, entity_name)][service_id]['entity'],
#                         'scope': user_times[(username, entity_name)][service_id]['scope'],
#                         'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
#                         'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
#                         'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
#                         'workstatus': user_times[(username, entity_name)][service_id]['workstatus'],  # Include work status
#                         'Remarks' : None,
                        
#                     }
#                     for service_id in user_times[(username, entity_name)]
#                 }
#                 for (username, entity_name) in user_times
#             }
#             daily_summaries.update(formatted_day_summary)

#         current_day += timedelta(days=1)

#     return daily_summaries

# def calculate_end_time_for_user3(db: Session, picked_date: str, to_date: str) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # For ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         has_activity_for_day = False  # Track if any valid data exists for the day

#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

#             # Ensure the record falls exactly on the specified date
#             if start_time.date() != date:
#                 continue

#             time_diff = end_time - start_time
#             has_activity_for_day = True  # Mark that valid data exists

#             # Fetch user from User_table
#             user = db.query(models.User_table).filter(
#                 models.User_table.user_id == getattr(record, user_field)
#             ).first()
            
#             # Construct the username from firstname and lastname
#             if user:
#                 username = f"{user.firstname}{user.lastname}"  # Concatenate firstname and lastname
#             else:
#                 username = "Unknown"

#             service_id = getattr(record, 'Service_ID')

#             # Fetch TL record for work status and metadata, including entity
#             tl_record = db.query(models.TL).filter(
#                 models.TL.Service_ID == service_id
#             ).first()

#             # Get the entity name and work status
#             entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
#             work_status = tl_record.work_status if tl_record else "Unknown Status"
            
#             # Accumulate time for each activity
#             if (username, entity_name) not in user_times:
#                 user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

#             user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

#             # Store scope, sub-scope, nature of work, and work status for the user
#             if tl_record:
#                 user_times[(username, entity_name)][service_id].update({
#                     'scope': tl_record.scope.scope if tl_record else None,
#                     'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
#                     'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
#                     'workstatus': work_status,  # Add work status to user times
#                     'entity': entity_name
#                 })

#         return has_activity_for_day  # Return whether any activity was processed for the day

#     daily_summaries = OrderedDict()
#     current_day = picked_datett

#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Track if any activities were processed for the current day
#         day_has_data = False

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field).between(
#                     current_day.replace(hour=0, minute=0, second=0),
#                     current_day.replace(hour=23, minute=59, second=59)
#                 )
#             ).all()

#             # Process records and check if there was any valid data
#             if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
#                 day_has_data = True

#         # Only add the summary if there was data for the day
#         if day_has_data:
#             formatted_day_summary = {
#                 current_day.strftime("%Y-%m-%d"): [
#                     {  # Create a list of dictionaries for each user/entity
#                         'Entity': user_times[(username, entity_name)][service_id]['entity'],
#                         'Worked_By': username,  # Add username as a separate field
#                         'scope': user_times[(username, entity_name)][service_id]['scope'],
#                         'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
#                         'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
#                         'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
#                         'Status': user_times[(username, entity_name)][service_id]['workstatus'],
#                         'Remarks': None,
#                     }
#                     for service_id in user_times[(username, entity_name)]
#                 ]
#                 for (username, entity_name) in user_times
#             }
#             daily_summaries.update(formatted_day_summary)

#         current_day += timedelta(days=1)

#     return daily_summaries


from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

def format_timedelta_to_str(td: timedelta) -> str:
    """Format a timedelta to a string in HH:MM:SS format."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user3(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user_id = getattr(record, user_field)  # Extract user_id from the record
            user = db.query(models.User_table).filter(models.User_table.user_id == user_id).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity
            tl_record = db.query(models.TL).filter(models.TL.Service_ID == service_id).first()

            # Get the entity name and work status
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            work_status = tl_record.work_status if tl_record else "Unknown Status"
            
            # Initialize remarks to an empty string for other activity types
            remarks = ""

            # Fetch hold record to get remarks only for hold activity
            if activity == 'hold':
                hold_record = db.query(models.HOLD).filter(
                    models.HOLD.Service_ID == service_id,
                    models.HOLD.user_id == user_id
                ).first()

                if hold_record:
                    remarks = hold_record.remarks if hold_record else ""

            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = {
                    'total_time_take': timedelta(),  # Ensure this is a timedelta
                    'scope': None,
                    'subscopes': None,
                    'nature_of_work': None,
                    'workstatus': work_status,
                    'remarks': remarks,
                    'entity': entity_name
                }

            # Update the accumulated time
            user_times[(username, entity_name)]['total_time_take'] += time_diff

            # Store other details if the TL record exists
            if tl_record:
                user_times[(username, entity_name)].update({
                    'scope': tl_record.scope.scope if tl_record else None,
                    'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(dict)

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {
                        'Entity': user_times[(username, entity_name)]['entity'],
                        'Worked_By': username,  # Add username as a separate field
                        'scope': user_times[(username, entity_name)]['scope'],
                        'subscopes': user_times[(username, entity_name)]['subscopes'],
                        'nature_of_work': user_times[(username, entity_name)]['nature_of_work'],
                        'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)]['total_time_take']),
                        'Status': user_times[(username, entity_name)]['workstatus'],
                        'Remarks': user_times[(username, entity_name)]['remarks'],  # Fetch remarks correctly
                    }
                    for (username, entity_name) in user_times
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries



# def calculate_end_time_for_user4(db: Session, picked_date: str, to_date: str) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # For ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         has_activity_for_day = False  # Track if any valid data exists for the day

#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

#             # Ensure the record falls exactly on the specified date
#             if start_time.date() != date:
#                 continue

#             time_diff = end_time - start_time
#             has_activity_for_day = True  # Mark that valid data exists

#             # Fetch user from User_table
#             user = db.query(models.User_table).filter(
#                 models.User_table.user_id == getattr(record, user_field)
#             ).first()
            
#             # Construct the username from firstname and lastname
#             if user:
#                 username = f"{user.firstname}{user.lastname}"  # Concatenate firstname and lastname
#             else:
#                 username = "Unknown"

#             service_id = getattr(record, 'Service_ID')

#             # Fetch TL record for work status and metadata, including entity
#             tl_record = db.query(models.TL).filter(
#                 models.TL.Service_ID == service_id
#             ).first()

#             # Get the entity name and work status
#             entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
#             work_status = tl_record.work_status if tl_record else "Unknown Status"
#             no_of_items = tl_record.no_of_items if tl_record else "N/A"
#             # created_on = tl_record.created_on if tl_record else None
#             created_on = tl_record.created_on.strftime("%Y-%m-%d") if tl_record.created_on else None  # Format created_on
#             completed_date = tl_record.completed_time.strftime("%Y-%m-%d") if tl_record.completed_time else None
            

#             # Accumulate time for each activity
#             if (username, entity_name) not in user_times:
#                 user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

#             user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

#             # Store scope, sub-scope, nature of work, and work status for the user
#             if tl_record:
#                 user_times[(username, entity_name)][service_id].update({
#                     'scope': tl_record.scope.scope if tl_record else None,
#                     'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
#                     'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
#                     'workstatus': work_status,  # Add work status to user times
#                     'entity': entity_name,
#                     'no_of_items': no_of_items,
#                     'created_on': created_on,
#                     'completed_date': completed_date
#                 })

#         return has_activity_for_day  # Return whether any activity was processed for the day

#     daily_summaries = OrderedDict()
#     current_day = picked_datett

#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Track if any activities were processed for the current day
#         day_has_data = False

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field).between(
#                     current_day.replace(hour=0, minute=0, second=0),
#                     current_day.replace(hour=23, minute=59, second=59)
#                 )
#             ).all()

#             # Process records and check if there was any valid data
#             if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
#                 day_has_data = True

#         # Only add the summary if there was data for the day
#         if day_has_data:
#             formatted_day_summary = {
#                 current_day.strftime("%Y-%m-%d"): [
#                     {  # Create a list of dictionaries for each user/entity
#                         'Entity': user_times[(username, entity_name)][service_id]['entity'],
#                         'scope': user_times[(username, entity_name)][service_id]['scope'],
#                         'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
#                         'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
#                         'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
#                         'Count': user_times[(username, entity_name)][service_id]['no_of_items'],
#                         'Worked_By': username,  # Add username as a separate field
#                         'created_on': user_times[(username, entity_name)][service_id]['created_on'],
#                         'Completed_Date': user_times[(username, entity_name)][service_id]['completed_date'],
#                         'Remarks': None,
#                         'Status': user_times[(username, entity_name)][service_id]['workstatus'],
#                     }
#                     for service_id in user_times[(username, entity_name)]
#                 ]
#                 for (username, entity_name) in user_times
#             }
#             daily_summaries.update(formatted_day_summary)

#         current_day += timedelta(days=1)

#     return daily_summaries


from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

def format_timedelta_to_str(td: timedelta) -> str:
    """Format a timedelta to a string in HH:MM:SS format."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user4(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user_id = getattr(record, user_field)  # Extract user_id from the record
            user = db.query(models.User_table).filter(
                models.User_table.user_id == user_id
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            # Fetch TL record for work status and metadata, including entity
            service_id = getattr(record, 'Service_ID')
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id,
                models.TL.work_status == "Completed"  # Filter by Completed status
            ).first()

            # Proceed only if a completed TL record is found
            if tl_record:
                # Get the entity name and work status
                entity_name = tl_record.name_of_entity
                work_status = tl_record.work_status
                no_of_items = tl_record.no_of_items
                created_on = tl_record.created_on.strftime("%Y-%m-%d") if tl_record.created_on else None
                completed_date = tl_record.completed_time.strftime("%Y-%m-%d") if tl_record.completed_time else None
                
                # Initialize remarks to an empty string for other activity types
                remarks = ""

                # Fetch hold record to get remarks only for hold activity
                if activity == 'hold':
                    hold_record = db.query(models.HOLD).filter(
                        models.HOLD.Service_ID == service_id,
                        models.HOLD.user_id == user_id
                    ).first()

                    if hold_record:
                        remarks = hold_record.remarks if hold_record else ""

                # Accumulate time for each activity
                if (entity_name, username) not in user_times:
                    user_times[(entity_name, username)] = {
                        'total_time_take': timedelta(),
                        'workstatus': work_status,
                        'no_of_items': no_of_items,
                        'created_on': created_on,
                        'completed_date': completed_date,
                        'remarks': remarks,
                        'scope': tl_record.scope.scope if tl_record else None,
                        'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
                        'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                        'activity_count': 0,  # To count the number of activities
                    }

                user_times[(entity_name, username)]['total_time_take'] += time_diff
                user_times[(entity_name, username)]['activity_count'] += 1  # Increment activity count

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(dict)

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each entity/user combination
                        'Entity': entity_name,
                        'Scope': user_times[(entity_name, username)]['scope'],
                        'Subscopes': user_times[(entity_name, username)]['subscopes'],
                        'Nature_of_Work': user_times[(entity_name, username)]['nature_of_work'],
                        'Total_Worked_Hours': format_timedelta_to_str(user_times[(entity_name, username)]['total_time_take']),
                        'Count': user_times[(entity_name, username)]['no_of_items'],
                        'Worked_By': username,  # Add username as a separate field
                        'Created_On': user_times[(entity_name, username)]['created_on'],
                        'Completed_Date': user_times[(entity_name, username)]['completed_date'],
                        'Remarks': user_times[(entity_name, username)]['remarks'],
                        'Status': user_times[(entity_name, username)]['workstatus'],
                    }
                    for (entity_name, username) in user_times
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries



from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

def format_timedelta_to_str(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user5(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity, filter by 'In Progress' status
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id,
                models.TL.work_status == "In Progress"  # Filter only those with 'In Progress' status
            ).first()

            if not tl_record:  # If no 'In Progress' TL record is found, skip this record
                continue

            # Get the entity name and work status
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            work_status = tl_record.work_status if tl_record else "Unknown Status"
            no_of_items = tl_record.no_of_items if tl_record else "N/A"
            created_on = tl_record.created_on.strftime("%Y-%m-%d") if tl_record.created_on else None  # Format created_on

            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, entity_name)][service_id].update({
                    'scope': tl_record.scope.scope if tl_record.scope else None,
                    'subscopes': tl_record.sub_scope.sub_scope if tl_record.sub_scope else None,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record._nature_of_work else None,
                    'workstatus': work_status,  # Add work status to user times
                    'entity': entity_name,
                    'no_of_items': no_of_items,
                    'created_on': created_on
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Entity': user_times[(username, entity_name)][service_id]['entity'],
                        'scope': user_times[(username, entity_name)][service_id]['scope'],
                        'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
                        'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
                        'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
                        'Worked_By': username,  # Add username as a separate field
                        'created_Date': user_times[(username, entity_name)][service_id]['created_on'],
                        'Status': user_times[(username, entity_name)][service_id]['workstatus'],
                        'Count': user_times[(username, entity_name)][service_id]['no_of_items'],
                    }
                    for service_id in user_times[(username, entity_name)]
                ]
                for (username, entity_name) in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries


# def calculate_end_time_for_user6(db: Session, picked_date: str, to_date: str) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # For ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         has_activity_for_day = False  # Track if any valid data exists for the day

#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

#             # Ensure the record falls exactly on the specified date
#             if start_time.date() != date:
#                 continue

#             time_diff = end_time - start_time
#             has_activity_for_day = True  # Mark that valid data exists

#             # Fetch user from User_table
#             user_id = getattr(record, user_field)  # Extract user_id from the record
#             user = db.query(models.User_table).filter(
#                 models.User_table.user_id == user_id
#             ).first()

            
#             # Construct the username from firstname and lastname
#             if user:
#                 username = f"{user.firstname}{user.lastname}"  # Concatenate firstname and lastname
#             else:
#                 username = "Unknown"

#             service_id = getattr(record, 'Service_ID')

#             # Fetch TL record for work status and metadata, including entity
#             tl_record = db.query(models.TL).filter(
#                 models.TL.Service_ID == service_id
#             ).first()
#             hold_record = db.query(models.HOLD).filter(
#                     models.HOLD.Service_ID == service_id,
#                     models.HOLD.user_id == user_id
#                 ).first()

#             remarks = hold_record.remarks if hold_record else ""
            
#             # Get the entity name and work status
#             entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
#             work_status = tl_record.work_status if tl_record else "Unknown Status"
#             # created_on = tl_record.created_on if tl_record else None
#             created_on = tl_record.created_on.strftime("%Y-%m-%d") if tl_record.created_on else None  # Format created_on

            

#             # Accumulate time for each activity
#             if (username, entity_name) not in user_times:
#                 user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

#             user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

#             # Store scope, sub-scope, nature of work, and work status for the user
#             if tl_record:
#                 user_times[(username, entity_name)][service_id].update({
#                     'scope': tl_record.scope.scope if tl_record else None,
#                     'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
#                     'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
#                     'workstatus': work_status,  # Add work status to user times
#                     'entity': entity_name,
#                     'created_on': created_on
#                 })

#         return has_activity_for_day  # Return whether any activity was processed for the day

#     daily_summaries = OrderedDict()
#     current_day = picked_datett

#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Track if any activities were processed for the current day
#         day_has_data = False

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field).between(
#                     current_day.replace(hour=0, minute=0, second=0),
#                     current_day.replace(hour=23, minute=59, second=59)
#                 )
#             ).all()

#             # Process records and check if there was any valid data
#             if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
#                 day_has_data = True

#         # Only add the summary if there was data for the day
#         if day_has_data:
#             formatted_day_summary = {
#                 current_day.strftime("%Y-%m-%d"): [
#                     {  # Create a list of dictionaries for each user/entity
#                         'Entity': user_times[(username, entity_name)][service_id]['entity'],
#                         'scope': user_times[(username, entity_name)][service_id]['scope'],
#                         'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
#                         'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
#                         'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
#                         'Worked_By': username,  # Add username as a separate field
#                         'created_Date': user_times[(username, entity_name)][service_id]['created_on'],
#                         'Status': user_times[(username, entity_name)][service_id]['workstatus'],
#                         'Remarks': None

#                     }
#                     for service_id in user_times[(username, entity_name)]
#                 ]
#                 for (username, entity_name) in user_times
#             }
#             daily_summaries.update(formatted_day_summary)

#         current_day += timedelta(days=1)

#     return daily_summaries

def calculate_end_time_for_user6(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            # Only process completed records
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user_id = getattr(record, user_field)  # Extract user_id from the record
            user = db.query(models.User_table).filter(
                models.User_table.user_id == user_id
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname}{user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, filter by 'Hold' status
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id,
                models.TL.work_status == 'Hold'  # Only fetch records with 'Hold' work status
            ).first()

            # If no TL record or work status isn't 'Hold', skip
            if not tl_record:
                continue

            # Fetch hold record to get remarks
            hold_record = db.query(models.HOLD).filter(
                models.HOLD.Service_ID == service_id,
                models.HOLD.user_id == user_id
            ).first()

            remarks = hold_record.remarks if hold_record else ""

            # Get the entity name and work status
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            work_status = tl_record.work_status if tl_record else "Unknown Status"
            created_on = tl_record.created_on.strftime("%Y-%m-%d") if tl_record and tl_record.created_on else None
            
            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name)][service_id]['total_time_take'] += time_diff

            # Store scope, sub-scope, nature of work, work status, remarks, and created_on for the user
            if tl_record:
                user_times[(username, entity_name)][service_id].update({
                    'scope': tl_record.scope.scope if tl_record else None,
                    'subscopes': tl_record.sub_scope.sub_scope if tl_record else None,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                    'workstatus': work_status,  # Add work status to user times
                    'entity': entity_name,
                    'remarks': remarks,  # Store remarks here
                    'created_on': created_on
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Entity': user_times[(username, entity_name)][service_id]['entity'],
                        'scope': user_times[(username, entity_name)][service_id]['scope'],
                        'subscopes': user_times[(username, entity_name)][service_id]['subscopes'],
                        'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
                        'total_time_take': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['total_time_take']),
                        'Worked_By': username,  # Add username as a separate field
                        'created_Date': user_times[(username, entity_name)][service_id]['created_on'],
                        'Status': user_times[(username, entity_name)][service_id]['workstatus'],
                        'Remarks': user_times[(username, entity_name)][service_id]['remarks']  # Use remarks from user_times
                    }
                    for service_id in user_times[(username, entity_name)]
                ]
                for (username, entity_name) in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries






from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

def format_timedelta_to_str(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user7(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, entity_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user_id = getattr(record, user_field)  # Extract user_id from the record
            user = db.query(models.User_table).filter(
                models.User_table.user_id == user_id
            ).first()
            
            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            hold_record = db.query(models.HOLD).filter(
                models.HOLD.Service_ID == service_id,
                models.HOLD.user_id == user_id
            ).first()

            remarks = hold_record.remarks if hold_record else ""

            # Get the entity name, work status, and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            no_of_items = tl_record.no_of_items if tl_record else "N/A"
            gstintan = tl_record.gst_or_tan if tl_record else "N/A"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"

            # Determine whether the time is chargeable or non-chargeable based on type_of_activity
            chargable_time = timedelta(0)
            non_chargable_time = timedelta(0)

            if type_of_activity == "CHARGABLE":
                chargable_time = time_diff
            elif type_of_activity == "NONCHARGABLE":
                non_chargable_time = time_diff

            # Accumulate time for each entity
            if entity_name not in entity_times:
                entity_times[entity_name] = defaultdict(lambda: defaultdict(timedelta))

            entity_times[entity_name][service_id]['Chargable_Time'] += chargable_time
            entity_times[entity_name][service_id]['Non_Chargable_Time'] += non_chargable_time

            # Store additional details for the entity
            if tl_record:
                entity_times[entity_name][service_id].update({
                    'gst': gstintan,
                    'entity': entity_name,
                    'no_of_items': no_of_items,
                    'remarks': remarks
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        entity_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', entity_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {
                        'Name_of_the_Entity': entity_name,
                        'GSTIN/TAN': entity_times[entity_name][service_id]['gst'],
                        'Chargable_Time': format_timedelta_to_str(entity_times[entity_name][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(entity_times[entity_name][service_id]['Non_Chargable_Time']),
                        'total_time_take': format_timedelta_to_str(
                            entity_times[entity_name][service_id]['Chargable_Time'] +
                            entity_times[entity_name][service_id]['Non_Chargable_Time']
                        ),
                        'Count': entity_times[entity_name][service_id]['no_of_items'],
                        'Remarks': entity_times[entity_name][service_id]['remarks']
                    }
                    for entity_name in entity_times
                    for service_id in entity_times[entity_name]
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries





from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

def calculate_end_time_for_user8(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, records, start_field, end_field, user_field, user_times):
        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            
            # Fetch user from User_table
            user_id = getattr(record, user_field)  # Extract user_id from the record
            user = db.query(models.User_table).filter(
                models.User_table.user_id == user_id
            ).first()
            
            # Construct the username from firstname and lastname
            if user:
                username = f"{user.firstname} {user.lastname}"  # Concatenate firstname and lastname
            else:
                username = "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()
            
            hold_record = db.query(models.HOLD).filter(
                models.HOLD.Service_ID == service_id,
                models.HOLD.user_id == user_id
            ).first()

            remarks = hold_record.remarks if hold_record else ""

            # Get the entity name, nature_of_work, work status, and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            nature_of_work = tl_record._nature_of_work.work_name if tl_record else None

            # Determine whether the time is chargeable or non-chargeable based on type_of_activity
            if tl_record.type_of_activity == "CHARGABLE":
                chargeable_time = time_diff
                non_chargeable_time = timedelta(0)
            else:
                chargeable_time = timedelta(0)
                non_chargeable_time = time_diff

            # Initialize nested structure if not already present
            if (username, entity_name, nature_of_work) not in user_times:
                user_times[(username, entity_name, nature_of_work)] = {
                    'Chargable_Time': timedelta(0),
                    'Non_Chargable_Time': timedelta(0),
                    'Remarks': remarks,
                    'Count': tl_record.no_of_items if tl_record else "N/A",
                    'GSTIN/TAN': tl_record.gst_or_tan if tl_record else "N/A",
                }

            # Accumulate times
            user_times[(username, entity_name, nature_of_work)]['Chargable_Time'] += chargeable_time
            user_times[(username, entity_name, nature_of_work)]['Non_Chargable_Time'] += non_chargeable_time

        return bool(user_times)  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(dict)

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {
                        'Name_of_the_Entity': entity_name,
                        'GSTIN/TAN': user_times[(username, entity_name, nature_of_work)]['GSTIN/TAN'],
                        'nature_of_work': nature_of_work,
                        'Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name, nature_of_work)]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name, nature_of_work)]['Non_Chargable_Time']),
                        'total_time_take': format_timedelta_to_str(
                            user_times[(username, entity_name, nature_of_work)]['Chargable_Time'] +
                            user_times[(username, entity_name, nature_of_work)]['Non_Chargable_Time']
                        ),
                        'Count': user_times[(username, entity_name, nature_of_work)]['Count'],
                        'Remarks': user_times[(username, entity_name, nature_of_work)]['Remarks'],
                    }
                    for (username, entity_name, nature_of_work) in user_times
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries


from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

def format_timedelta_to_str(td: timedelta) -> str:
    """Formats a timedelta object into a string."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user9(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name, work status, and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            scope = tl_record.scope.scope if tl_record else None
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"

            # Determine whether the time is chargeable or non-chargeable based on type_of_activity
            chargable_time = time_diff if type_of_activity == "CHARGABLE" else timedelta(0)
            non_chargable_time = time_diff if type_of_activity == "NONCHARGABLE" else timedelta(0)

            # Accumulate time for each activity based on scope
            if (username, entity_name, scope) not in user_times:
                user_times[(username, entity_name, scope)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name, scope)][service_id]['Chargable_Time'] += chargable_time
            user_times[(username, entity_name, scope)][service_id]['Non_Chargable_Time'] += non_chargable_time

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, entity_name, scope)][service_id].update({
                    'scope': scope
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity/scope
                        'Nature_of_Scope': user_times[(username, entity_name, scope)][service_id]['scope'],
                        'Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name, scope)][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name, scope)][service_id]['Non_Chargable_Time']),
                        'total_time_take': format_timedelta_to_str(
                            user_times[(username, entity_name, scope)][service_id]['Chargable_Time'] +
                            user_times[(username, entity_name, scope)][service_id]['Non_Chargable_Time']
                        ),
                    }
                    for service_id in user_times[(username, entity_name, scope)]
                ]
                for (username, entity_name, scope) in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries


def calculate_end_time_for_user10(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"
            nature_of_work = tl_record._nature_of_work.work_name if tl_record and tl_record._nature_of_work else "Unknown Nature"  # Ensure we get the right nature of work

            # Determine chargable and non-chargable times
            if type_of_activity == "CHARGABLE":
                chargable_time = time_diff
                non_chargable_time = timedelta(0)
            elif type_of_activity == "NONCHARGABLE":
                chargable_time = timedelta(0)
                non_chargable_time = time_diff
            else:
                chargable_time = non_chargable_time = timedelta(0)

            # Initialize user_times if not present
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)][service_id] = {
                    'Chargable_Time': timedelta(0),
                    'Non_Chargable_Time': timedelta(0),
                    'nature_of_work': nature_of_work,  # Store the nature of work here
                    'subscope': str(tl_record.From) if tl_record and tl_record.From else "Unknown",
                }

            user_times[(username, entity_name)][service_id]['Chargable_Time'] += chargable_time
            user_times[(username, entity_name)][service_id]['Non_Chargable_Time'] += non_chargable_time

        return has_activity_for_day


    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {
                        'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],  # Use the stored nature of work
                        'SubScope': 'subscope',
                        'Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['Non_Chargable_Time']),
                        'Total_Time_Taken': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['Chargable_Time'] +
                                                                                user_times[(username, entity_name)][service_id]['Non_Chargable_Time'])
                    }
                    for (username, entity_name) in user_times
                    for service_id in user_times[(username, entity_name)]
                ]
            }

        daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries






def calculate_end_time_for_user11(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            
            # Construct the username from firstname and lastname
            if user:
                username = f"{user.firstname} {user.lastname}"  # Concatenate firstname and lastname
            else:
                username = "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity, scope, subscope, and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name, work status, scope, subscope, and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            scope = tl_record.Scope if tl_record else "N/A"
            subscope = tl_record.From if tl_record else "Unknown Subscope"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"

            # Determine whether the time is chargeable or non-chargeable based on type_of_activity
            if type_of_activity == "CHARGABLE":
                chargeable_time = time_diff
                non_chargeable_time = timedelta(0)
            elif type_of_activity == "NONCHARGABLE":
                chargeable_time = timedelta(0)
                non_chargeable_time = time_diff
            else:
                chargeable_time = timedelta(0)
                non_chargeable_time = timedelta(0)

            # Accumulate time for each activity
            if (username, entity_name, scope, subscope) not in user_times:
                user_times[(username, entity_name, scope, subscope)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name, scope, subscope)][service_id]['Chargable_Time'] += chargeable_time
            user_times[(username, entity_name, scope, subscope)][service_id]['Non_Chargable_Time'] += non_chargeable_time

            # Store scope and subscope for the user
            if tl_record:
                user_times[(username, entity_name, scope, subscope)][service_id].update({
                    'scope': str(scope),
                    'subscope': str(subscope),
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Nature_of_Scope': user_times[(username, entity_name, scope, subscope)][service_id]['scope'],
                        'SubScope': user_times[(username, entity_name, scope, subscope)][service_id]['subscope'],
                        'Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name, scope, subscope)][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name, scope, subscope)][service_id]['Non_Chargable_Time']),
                        'total_time_take': format_timedelta_to_str(
                            user_times[(username, entity_name, scope, subscope)][service_id]['Chargable_Time'] +
                            user_times[(username, entity_name, scope, subscope)][service_id]['Non_Chargable_Time']
                        ),
                    }
                    for (username, entity_name, scope, subscope) in user_times
                    for service_id in user_times[(username, entity_name, scope, subscope)]
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries


from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

def format_timedelta_to_str(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user12(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            
            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name, work status, and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            subscope_id = tl_record.From if tl_record else "N/A"
            scope_id = tl_record.Scope if tl_record else "N/A"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"
            no_of_items = tl_record.no_of_items if tl_record else "N/A"

            # Fetch names of Nature_of_Scope and SubScope based on IDs
            nature_of_scope = db.query(models.scope).filter(models.scope.scope_id == scope_id).first()
            subscope = db.query(models.sub_scope).filter(models.sub_scope.sub_scope_id == subscope_id).first()

            nature_of_scope_name = nature_of_scope.scope if nature_of_scope else "N/A"
            subscope_name = subscope.sub_scope if subscope else "N/A"

            # Determine whether the time is chargeable or non-chargeable based on type_of_activity
            if type_of_activity == "CHARGABLE":
                chargable_time = time_diff
                non_chargable_time = timedelta(0)
            elif type_of_activity == "NONCHARGABLE":
                chargable_time = timedelta(0)
                non_chargable_time = time_diff
            else:
                chargable_time = timedelta(0)
                non_chargable_time = timedelta(0)

            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name)][service_id]['Chargable_Time'] += chargable_time
            user_times[(username, entity_name)][service_id]['Non_Chargable_Time'] += non_chargable_time

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, entity_name)][service_id].update({
                    'scope': nature_of_scope_name,
                    'subscope': subscope_name,
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                    'no_of_items': no_of_items,
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Nature_of_Scope': user_times[(username, entity_name)][service_id]['scope'],
                        'SubScope': user_times[(username, entity_name)][service_id]['subscope'],
                        'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
                        'Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['Non_Chargable_Time']),
                        'total_time_taken': format_timedelta_to_str(
                            user_times[(username, entity_name)][service_id]['Chargable_Time'] +
                            user_times[(username, entity_name)][service_id]['Non_Chargable_Time']
                        ),
                        'Count': user_times[(username, entity_name)][service_id]['no_of_items'],
                    }
                    for service_id in user_times[(username, entity_name)]
                ]
                for (username, entity_name) in user_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries




# def calculate_end_time_for_user13(db: Session, picked_date: str, to_date: str) -> dict:
#     picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
#     to_datett = datetime.strptime(to_date, "%Y-%m-%d")
#     current_time = datetime.now()  # For ongoing activities

#     def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
#         has_activity_for_day = False  # Track if any valid data exists for the day

#         for record in records:
#             start_time = getattr(record, start_field)
#             end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

#             # Ensure the record falls exactly on the specified date
#             if start_time.date() != date:
#                 continue

#             time_diff = end_time - start_time
#             has_activity_for_day = True  # Mark that valid data exists

#             # Fetch user from User_table
#             user = db.query(models.User_table).filter(
#                 models.User_table.user_id == getattr(record, user_field)
#             ).first()
            
#             # Construct the username from firstname and lastname
#             if user:
#                 username = f"{user.firstname} {user.lastname}"  # Concatenate firstname and lastname
#             else:
#                 username = "Unknown"

#             service_id = getattr(record, 'Service_ID')

#             # Fetch TL record for work status and metadata, including entity and type_of_activity
#             tl_record = db.query(models.TL).filter(
#                 models.TL.Service_ID == service_id
#             ).first()

#             # Get the entity name, work status, and type_of_activity
#             entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
#             no_of_items = tl_record.no_of_items if tl_record else "N/A"
#             gstintan = tl_record.gst_or_tan if tl_record else "N/A"
#             type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"
#             estimated_time = tl_record.estimated_time if tl_record else "00:00:00"

#             # Determine whether the time is chargable or non-chargable based on type_of_activity
#             if type_of_activity == "CHARGABLE":
#                 chargable_time = time_diff
#                 non_chargable_time = timedelta(0)
#             else:
#                 None

#             if type_of_activity == "NONCHARGABLE":
#                 chargable_time = timedelta(0)
#                 non_chargable_time = time_diff
#             else:
#                 None
            


#             # Accumulate time for each activity
#             if (username, entity_name) not in user_times:
#                 user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

#             user_times[(username, entity_name)][service_id]['Chargable_Time'] += chargable_time
#             user_times[(username, entity_name)][service_id]['Non_Chargable_Time'] += non_chargable_time

#             # Store scope, sub-scope, nature of work, and work status for the user
#             if tl_record:
#                 user_times[(username, entity_name)][service_id].update({
#                     'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,

#                     'gst': gstintan,
#                     'entity': entity_name,
#                     'no_of_items': no_of_items,
#                     'estimated_time': estimated_time,
#                 })
    
#         return has_activity_for_day  # Return whether any activity was processed for the day

#     # Main function that generates the daily summaries
#     daily_summaries = OrderedDict()
#     current_day = picked_datett

#     while current_day <= to_datett:
#         user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

#         # Track if any activities were processed for the current day
#         day_has_data = False

#         # Process each activity type
#         for activity, model, start_field, end_field in [
#             ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
#             ('break', models.BREAK, 'break_time_start', 'break_time_end'),
#             ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
#             ('call', models.CALL, 'call_time_start', 'call_time_end'),
#             ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
#         ]:
#             records = db.query(model).filter(
#                 getattr(model, start_field).between(
#                     current_day.replace(hour=0, minute=0, second=0),
#                     current_day.replace(hour=23, minute=59, second=59)
#                 )
#             ).all()

#             # Process records and check if there was any valid data
#             if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
#                 day_has_data = True

#         # Only add the summary if there was data for the day
#         if day_has_data:
#             formatted_day_summary = {
#                 current_day.strftime("%Y-%m-%d"): [
#                     {  # Create a list of dictionaries for each user/entity
#                         'Name_of_the_Entity': user_times[(username, entity_name)][service_id]['entity'],
#                         'GSTIN/TAN': user_times[(username, entity_name)][service_id]['gst'],
#                         'nature_of_work': user_times[(username, entity_name)][service_id]['nature_of_work'],
#                         'estimated_time': user_times[(username, entity_name)][service_id]['estimated_time'],
#                         'Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['Chargable_Time']),
#                         'Non_Chargable_Time': format_timedelta_to_str(user_times[(username, entity_name)][service_id]['Non_Chargable_Time']),
#                         'total_time_take': format_timedelta_to_str(
#                             user_times[(username, entity_name)][service_id]['Chargable_Time'] +
#                             user_times[(username, entity_name)][service_id]['Non_Chargable_Time']
#                         ),
#                         'Count': user_times[(username, entity_name)][service_id]['no_of_items'],
#                         'Remarks': None
#                     }
#                     for service_id in user_times[(username, entity_name)]
#                 ]
#                 for (username, entity_name) in user_times
#             }
#             daily_summaries.update(formatted_day_summary)

#         current_day += timedelta(days=1)

#     return daily_summaries


from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models  # Import your models

def format_timedelta_to_str(td: timedelta) -> str:
    """Helper function to format timedelta to a string."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user13(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, entity_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"
            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and other required data
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            no_of_items = tl_record.no_of_items if tl_record else "N/A"
            gstintan = tl_record.gst_or_tan if tl_record else "N/A"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"
            estimated_time = tl_record.estimated_time if tl_record else "00:00:00"

            # Initialize chargable and non-chargable time
            chargable_time = timedelta(0)
            non_chargable_time = timedelta(0)

            # Determine whether the time is chargable or non-chargable based on type_of_activity
            if type_of_activity == "CHARGABLE":
                chargable_time = time_diff
            elif type_of_activity == "NONCHARGABLE":
                non_chargable_time = time_diff
            
            # Accumulate time for each activity under the specific entity
            if entity_name not in entity_times:
                entity_times[entity_name] = defaultdict(lambda: defaultdict(timedelta))

            entity_times[entity_name][service_id]['Chargable_Time'] += chargable_time
            entity_times[entity_name][service_id]['Non_Chargable_Time'] += non_chargable_time

            # Store additional data from TL record
            if tl_record:
                entity_times[entity_name][service_id].update({
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                    'gst': gstintan,
                    'no_of_items': no_of_items,
                    'estimated_time': estimated_time,
                })

            # Fetch hold record for remarks
            hold_record = db.query(models.HOLD).filter(
                models.HOLD.Service_ID == service_id,
                models.HOLD.user_id == getattr(record, user_field)  # Fix user_id reference
            ).first()

            remarks = hold_record.remarks if hold_record else ""
            entity_times[entity_name][service_id]['Remarks'] = remarks
            
        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        entity_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', entity_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each entity
                        'Entity_Name': entity_name,
                        'GSTIN/TAN': entity_times[entity_name][service_id]['gst'],
                        'Service_ID': service_id,
                        'estimated_time': entity_times[entity_name][service_id]['estimated_time'],
                        'Chargable_Time': format_timedelta_to_str(entity_times[entity_name][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(entity_times[entity_name][service_id]['Non_Chargable_Time']),
                        'total_time_taken': format_timedelta_to_str(
                            entity_times[entity_name][service_id]['Chargable_Time'] +
                            entity_times[entity_name][service_id]['Non_Chargable_Time']
                        ),
                        'Count': entity_times[entity_name][service_id]['no_of_items'],
                        'Remarks': entity_times[entity_name][service_id].get('Remarks', None),
                    }
                    for service_id in entity_times[entity_name]
                ]
                for entity_name in entity_times
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries




from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

def format_timedelta_to_str(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def calculate_end_time_for_user14(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name, work status, and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            gstintan = tl_record.gst_or_tan if tl_record else "N/A"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"

            # Determine whether the time is chargable or non-chargable based on type_of_activity
            if type_of_activity == "CHARGABLE":
                chargable_time = time_diff
                non_chargable_time = timedelta(0)
            elif type_of_activity == "NONCHARGABLE":
                chargable_time = timedelta(0)
                non_chargable_time = time_diff
            else:
                chargable_time = timedelta(0)
                non_chargable_time = timedelta(0)

            # Accumulate time for each activity
            if (username, entity_name) not in user_times:
                user_times[(username, entity_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, entity_name)][service_id]['Chargable_Time'] += chargable_time
            user_times[(username, entity_name)][service_id]['Non_Chargable_Time'] += non_chargable_time

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, entity_name)][service_id].update({
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                    'gst': gstintan,
                    'entity': entity_name,
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        # Only add the summary if there was data for the day
        if day_has_data:
            for (username, entity_name), services in user_times.items():
                formatted_day_summary = {
                    current_day.strftime("%Y-%m-%d"): [
                        {
                            'Name_of_the_Team_Member': username,
                            'Name_of_the_Entity': entity_name,
                            'GSTIN/TAN': services[service_id]['gst'],
                            'Chargable_Time': format_timedelta_to_str(services[service_id]['Chargable_Time']),
                            'Non_Chargable_Time': format_timedelta_to_str(services[service_id]['Non_Chargable_Time']),
                            'Total_Time_Taken': format_timedelta_to_str(
                                services[service_id]['Chargable_Time'] +
                                services[service_id]['Non_Chargable_Time']
                            ),
                        }
                        for service_id in services
                    ]
                }
                daily_summaries.update(formatted_day_summary)


        current_day += timedelta(days=1)

    return daily_summaries

from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

def calculate_end_time_for_user15(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()

            # Construct the username from firstname and lastname
            if user:
                username = f"{user.firstname} {user.lastname}"  # Concatenate firstname and lastname
            else:
                username = "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name, work status, and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            gstintan = tl_record.gst_or_tan if tl_record else "N/A"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"

            # Initialize chargeable and non-chargeable times
            chargable_time = timedelta(0)
            non_chargable_time = timedelta(0)

            # Determine whether the time is chargeable or non-chargeable based on type_of_activity
            if type_of_activity == "CHARGABLE":
                chargable_time = time_diff
            elif type_of_activity == "NONCHARGABLE":
                non_chargable_time = time_diff

            # Accumulate time for each activity
            nature_of_work = tl_record._nature_of_work.work_name if tl_record else "Unknown"
            user_key = (username, nature_of_work)

            if user_key not in user_times:
                user_times[user_key] = defaultdict(lambda: defaultdict(timedelta))

            user_times[user_key][service_id]['Chargable_Time'] += chargable_time
            user_times[user_key][service_id]['Non_Chargable_Time'] += non_chargable_time

            # Store additional information for the user
            if tl_record:
                user_times[user_key][service_id].update({
                    'gst': gstintan,
                    'entity': entity_name,
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/nature of work
                        'Name_of_the_Team_Member': username,
                        'Nature_of_work': nature_of_work,
                        'Chargable_Time': format_timedelta_to_str(user_times[(username, nature_of_work)][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(user_times[(username, nature_of_work)][service_id]['Non_Chargable_Time']),
                        'total_time_taken': format_timedelta_to_str(
                            user_times[(username, nature_of_work)][service_id]['Chargable_Time'] +
                            user_times[(username, nature_of_work)][service_id]['Non_Chargable_Time']
                        ),
                    }
                    for (username, nature_of_work) in user_times.keys()
                    for service_id in user_times[(username, nature_of_work)]
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries


def calculate_end_time_for_user16(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name, work status, and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            gstintan = tl_record.gst_or_tan if tl_record else "N/A"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"
            estimated_time = tl_record.estimated_time if tl_record else "00:00:00"

            # Initialize chargable and non-chargable times
            chargable_time = timedelta(0)
            non_chargable_time = timedelta(0)

            # Determine whether the time is chargable or non-chargable based on type_of_activity
            if type_of_activity == "CHARGABLE":
                chargable_time = time_diff
            elif type_of_activity == "NONCHARGABLE":
                non_chargable_time = time_diff

            # Accumulate time for each activity
            if (username, tl_record._nature_of_work.work_name if tl_record else "Unknown") not in user_times:
                user_times[(username, tl_record._nature_of_work.work_name if tl_record else "Unknown")] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, tl_record._nature_of_work.work_name if tl_record else "Unknown")][service_id]['Chargable_Time'] += chargable_time
            user_times[(username, tl_record._nature_of_work.work_name if tl_record else "Unknown")][service_id]['Non_Chargable_Time'] += non_chargable_time

            # Store scope, sub-scope, nature of work, and work status for the user
            if tl_record:
                user_times[(username, tl_record._nature_of_work.work_name if tl_record else "Unknown")][service_id].update({
                    'nature_of_work': tl_record._nature_of_work.work_name if tl_record else None,
                    'estimated_time': estimated_time,
                    'gst': gstintan,
                    'entity': entity_name,
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity
                        'Name_of_the_Team_Member': username,
                        'Nature_of_Work': nature_of_work,
                        'Name_of_the_Entity': user_times[(username, nature_of_work)][service_id]['entity'],
                        'GSTIN/TAN': user_times[(username, nature_of_work)][service_id]['gst'],
                        'Estimated_Time': user_times[(username, nature_of_work)][service_id]['estimated_time'],
                        'Chargable_Time': format_timedelta_to_str(user_times[(username, nature_of_work)][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(user_times[(username, nature_of_work)][service_id]['Non_Chargable_Time']),
                        'Total_Time_Taken': format_timedelta_to_str(
                            user_times[(username, nature_of_work)][service_id]['Chargable_Time'] +
                            user_times[(username, nature_of_work)][service_id]['Non_Chargable_Time']
                        ),
                    }
                    for (username, nature_of_work) in user_times
                    for service_id in user_times[(username, nature_of_work)]
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries



from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

def calculate_end_time_for_user17(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()
            
            # Construct the username from firstname and lastname
            if user:
                username = f"{user.firstname} {user.lastname}"  # Concatenate firstname and lastname
            else:
                username = "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name, work status, and type_of_activity
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            gstintan = tl_record.gst_or_tan if tl_record else "N/A"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"
            estimated_time = tl_record.estimated_time if tl_record else "00:00:00"

            # Convert estimated_time (string) to timedelta
            estimated_time_timedelta = timedelta(
                hours=int(estimated_time.split(':')[0]),
                minutes=int(estimated_time.split(':')[1])
            )

            # Determine whether the time is chargable or non-chargable based on type_of_activity
            if type_of_activity == "CHARGABLE":
                chargable_time = time_diff
                non_chargable_time = timedelta(0)
            elif type_of_activity == "NONCHARGABLE":
                chargable_time = timedelta(0)
                non_chargable_time = time_diff
            else:
                chargable_time = non_chargable_time = timedelta(0)
            
            # Calculate the difference between Chargable_Time and estimated_time
            time_difference = estimated_time_timedelta - chargable_time

            # Accumulate time for each activity
            if (username, tl_record._nature_of_work.work_name) not in user_times:
                user_times[(username, tl_record._nature_of_work.work_name)] = defaultdict(lambda: defaultdict(timedelta))

            user_times[(username, tl_record._nature_of_work.work_name)][service_id]['Chargable_Time'] += chargable_time
            user_times[(username, tl_record._nature_of_work.work_name)][service_id]['Non_Chargable_Time'] += non_chargable_time
            user_times[(username, tl_record._nature_of_work.work_name)][service_id]['Difference'] = time_difference

            # Store additional metadata
            if tl_record:
                user_times[(username, tl_record._nature_of_work.work_name)][service_id].update({
                    'estimated_time': estimated_time,
                    'gst': gstintan,
                    'entity': entity_name,
                })

        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {  # Create a list of dictionaries for each user/entity and nature of work
                        'Name_of_the_Team_Member': username,
                        'Nature_of_work': nature_of_work,
                        'Chargable_Time': format_timedelta_to_str(user_times[(username, nature_of_work)][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(user_times[(username, nature_of_work)][service_id]['Non_Chargable_Time']),
                        'Difference': format_timedelta_to_str(user_times[(username, nature_of_work)][service_id]['Difference']),
                        'estimated_time': user_times[(username, nature_of_work)][service_id]['estimated_time'],
                    }
                    for (username, nature_of_work) in user_times
                    for service_id in user_times[(username, nature_of_work)]
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries



from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta



def calculate_end_time_for_user18(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, user_times):
        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                print(f"Skipping record: {record} - not on date {date}")  # Debugging line
                continue

            time_diff = end_time - start_time

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the nature of work
            nature_of_work = tl_record._nature_of_work.work_name if tl_record and tl_record._nature_of_work else "Unknown"

            # Use a combined key of username and nature of work
            key = (username, nature_of_work)

            # Initialize the key in user_times if not already present
            if key not in user_times:
                user_times[key] = {
                    'total_time': timedelta(),
                    'entity_counts': set()  # Use a set to count unique entities
                }

            # Accumulate time for each user/entity by summing the time differences
            user_times[key]['total_time'] += time_diff
            
            # Add the entity to the set of entity_counts
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            if entity_name != "Unknown Entity":
                user_times[key]['entity_counts'].add(entity_name)

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        user_times = defaultdict(lambda: {'total_time': timedelta(), 'entity_counts': set()})

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            print(f"Records for {activity} on {current_day}: {records}")  # Debugging line

            # Process records for the day
            process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', user_times)

        # Only add the summary if there was data for the day
        if user_times:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {
                        'Name_of_the_Team_Member': username,
                        'Nature_of_work': nature_of_work,
                        'Total_time': str(data['total_time'].seconds // 3600).zfill(2) + ':' + \
                                      str((data['total_time'].seconds // 60) % 60).zfill(2) + ':' + \
                                      str(data['total_time'].seconds % 60).zfill(2),  # Convert timedelta to HH:MM:SS format
                        'Entity_Counts': len(data['entity_counts'])  # Count of unique entities
                    }
                    for (username, nature_of_work), data in user_times.items()
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries



from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict


from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from sqlalchemy.orm import Session

from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

def calculate_end_time_for_user19(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, entity_times):
        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time

            # Fetch user from User_table
            user_id = getattr(record, user_field)  # Extract user_id from the record
            user = db.query(models.User_table).filter(
                models.User_table.user_id == user_id
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and other required data
            if tl_record:
                entity_name = tl_record.name_of_entity
                gstin_tan = tl_record.gst_or_tan
                nature_of_work = tl_record._nature_of_work.work_name if tl_record._nature_of_work else "Unknown"
                work_start_date = tl_record.Assigned_Date
                work_end_date = tl_record.completed_time

                # Ensure work_start_date and work_end_date are datetime objects
                if isinstance(work_start_date, str):
                    work_start_date = datetime.strptime(work_start_date, "%Y-%m-%d")
                if isinstance(work_end_date, str):
                    work_end_date = datetime.strptime(work_end_date, "%Y-%m-%d")

                no_days_taken_completed = (work_end_date - work_start_date).days if work_start_date and work_end_date else 0
                count = tl_record.no_of_items or 0  # Assume it’s stored as a string, convert if necessary
                hold_record = db.query(models.HOLD).filter(
                    models.HOLD.Service_ID == service_id,
                    models.HOLD.user_id == user_id
                ).first()

                remarks = hold_record.remarks if hold_record else ""

                # Use the entity name as the primary key
                key = entity_name

                # Initialize the key in entity_times if not already present
                if key not in entity_times:
                    entity_times[key] = {
                        'total_time': timedelta(),
                        'nature_of_work': nature_of_work,
                        'users': set(),  # Track users associated with this entity
                        'gst': gstin_tan,
                        'work_start_date': work_start_date,
                        'work_end_date': work_end_date,
                        'no_of_items': count,
                        'remarks': remarks,
                        'no_days_taken_completed': no_days_taken_completed,
                    }

                # Accumulate time for each entity
                entity_times[key]['total_time'] += time_diff
                
                # Add the user to the set of users for this entity
                entity_times[key]['users'].add(username)

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        entity_times = defaultdict(lambda: {
            'total_time': timedelta(),
            'nature_of_work': None,
            'users': set(),
            'gst': None,
            'work_start_date': None,
            'work_end_date': None,
            'no_of_items': 0,
            'remarks': None,
            'no_days_taken_completed': 0,
        })

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records for the day
            process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', entity_times)

        # Only add the summary if there was data for the day
        if entity_times:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {
                        'Name_of_the_Entity': entity,
                        'GSTIN/TAN': data['gst'],
                        'Nature_of_work': data['nature_of_work'],
                        'Workin_started_date': data['work_start_date'].strftime("%Y-%m-%d") if data['work_start_date'] else None,
                        'work_end_date': data['work_end_date'].strftime("%Y-%m-%d") if data['work_end_date'] else None,
                        'No_days_taken_completed': f"{data['no_days_taken_completed']} day{'s' if data['no_days_taken_completed'] != 1 else ''}",
                        'Count': data['no_of_items'],
                        'Remarks': data['remarks'],
                        'Total_Time': str(data['total_time'].seconds // 3600).zfill(2) + ':' + \
                                      str((data['total_time'].seconds // 60) % 60).zfill(2) + ':' + \
                                      str(data['total_time'].seconds % 60).zfill(2),  # Convert timedelta to HH:MM:SS format
                        'Users': ', '.join(data['users']),  # List of users associated with this entity
                    }
                    for entity, data in entity_times.items()
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries



from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models  # Import your models

def calculate_end_time_for_user20(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, activity, records, start_field, end_field, user_field, entity_times):
        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time

            # Fetch user from User_table
            user_id = getattr(record, user_field)  # Extract user_id from the record
            user = db.query(models.User_table).filter(
                models.User_table.user_id == user_id
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"

            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and other required data
            if tl_record:
                entity_name = tl_record.name_of_entity
                gstin_tan = tl_record.gst_or_tan
                nature_of_work = tl_record._nature_of_work.work_name if tl_record._nature_of_work else "Unknown"
                work_start_date = tl_record.Assigned_Date
                work_end_date = tl_record.completed_time

                # Ensure work_start_date and work_end_date are datetime objects
                if isinstance(work_start_date, str):
                    work_start_date = datetime.strptime(work_start_date, "%Y-%m-%d")
                if isinstance(work_end_date, str):
                    work_end_date = datetime.strptime(work_end_date, "%Y-%m-%d")

                no_days_taken_completed = (work_end_date - work_start_date).days if work_start_date and work_end_date else 0
                count = tl_record.no_of_items or 0  # Assume it’s stored as a string, convert if necessary

                # Fetch remarks from the HOLD table
                hold_record = db.query(models.HOLD).filter(
                    models.HOLD.Service_ID == service_id,
                    models.HOLD.user_id == user_id
                ).first()

                remarks = hold_record.remarks if hold_record else ""

                # Fetch estimated and actual delivery dates
                estimated_date_of_delivery = tl_record.estimated_d_o_d
                actual_date_of_delivery = tl_record.Actual_d_o_d
                adherence_of_delivery = "Adhered" if actual_date_of_delivery <= estimated_date_of_delivery else "Not Adhered"

                # Use a combined key of entity name and nature of work
                key = (entity_name, nature_of_work)

                # Initialize the key in entity_times if not already present
                if key not in entity_times:
                    entity_times[key] = {
                        'total_time': timedelta(),
                        'nature_of_work': nature_of_work,
                        'user_counts': set(),  # Use a set to count unique users
                        'gst': gstin_tan,
                        'work_start_date': work_start_date,
                        'work_end_date': work_end_date,
                        'no_of_items': count,
                        'remarks': remarks,
                        'no_days_taken_completed': no_days_taken_completed,
                        'estimated_date_of_delivery': estimated_date_of_delivery,
                        'actual_date_of_delivery': actual_date_of_delivery,
                        'adherence_of_delivery': adherence_of_delivery,
                    }

                # Accumulate time for each entity by summing the time differences
                entity_times[key]['total_time'] += time_diff

                # Add the user to the set of user_counts
                entity_times[key]['user_counts'].add(username)

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        entity_times = defaultdict(lambda: {'total_time': timedelta(), 'nature_of_work': None, 'user_counts': set()})

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records for the day
            process_records_for_day(current_day.date(), activity, records, start_field, end_field, 'user_id', entity_times)

        # Only add the summary if there was data for the day
        if entity_times:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): [
                    {
                        'Name_of_the_Entity': entity,
                        'GSTIN/TAN': data['gst'],
                        'Nature_of_work': data['nature_of_work'],
                        'Estimated_date_of_Delivery': data['estimated_date_of_delivery'],
                        'Actual_date_of_delivery': data['actual_date_of_delivery'],
                        'Adherence_of_Delivery': data['adherence_of_delivery'],
                        'No_days_taken_completed': f"{data['no_days_taken_completed']} day{'s' if data['no_days_taken_completed'] != 1 else ''}",
                        'Count': data['no_of_items'],
                        'Remarks': data['remarks'],
                        'Total_Time': str(data['total_time']),
                        'User_Count': len(data['user_counts']),  # Count of unique users
                    }
                    for (entity, _), data in entity_times.items()
                ]
            }
            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries

def calculate_end_time_for_user21(db: Session, picked_date: str, to_date: str) -> dict:
    picked_datett = datetime.strptime(picked_date, "%Y-%m-%d")
    to_datett = datetime.strptime(to_date, "%Y-%m-%d")
    current_time = datetime.now()  # For ongoing activities

    def process_records_for_day(date, records, start_field, end_field, user_field, entity_times):
        has_activity_for_day = False  # Track if any valid data exists for the day

        for record in records:
            start_time = getattr(record, start_field)
            end_time = getattr(record, end_field) or current_time  # Use current_time if ongoing

            # Ensure the record falls exactly on the specified date
            if start_time.date() != date:
                continue

            time_diff = end_time - start_time
            has_activity_for_day = True  # Mark that valid data exists

            # Fetch user from User_table
            user = db.query(models.User_table).filter(
                models.User_table.user_id == getattr(record, user_field)
            ).first()

            # Construct the username from firstname and lastname
            username = f"{user.firstname} {user.lastname}" if user else "Unknown"
            service_id = getattr(record, 'Service_ID')

            # Fetch TL record for work status and metadata, including entity and type_of_activity
            tl_record = db.query(models.TL).filter(
                models.TL.Service_ID == service_id
            ).first()

            # Get the entity name and other required data
            entity_name = tl_record.name_of_entity if tl_record else "Unknown Entity"
            no_of_items = tl_record.no_of_items if tl_record else "N/A"
            gstintan = tl_record.gst_or_tan if tl_record else "N/A"
            type_of_activity = tl_record.type_of_activity if tl_record else "Unknown"
            estimated_time = tl_record.estimated_time if tl_record else "00:00:00"

            # Fetch nature of work name from the Nature_Of_Work table
            nature_of_work_name = db.query(models.Nature_Of_Work).filter(
                models.Nature_Of_Work.work_id == tl_record.nature_of_work
            ).first()
            nature_of_work = nature_of_work_name.work_name if nature_of_work_name else "Unknown Work"

            # Initialize chargable and non-chargable time
            chargable_time = timedelta(0)
            non_chargable_time = timedelta(0)

            # Determine whether the time is chargable or non-chargable based on type_of_activity
            if type_of_activity == "CHARGABLE":
                chargable_time = time_diff
            elif type_of_activity == "NONCHARGABLE":
                non_chargable_time = time_diff
            
            # Accumulate time for each activity under the specific entity
            if entity_name not in entity_times:
                entity_times[entity_name] = {}

            if service_id not in entity_times[entity_name]:
                entity_times[entity_name][service_id] = {
                    'Chargable_Time': timedelta(0),
                    'Non_Chargable_Time': timedelta(0),
                    'nature_of_work': nature_of_work,
                    'gst': gstintan,
                    'no_of_items': no_of_items,
                    'estimated_time': estimated_time,
                    'Remarks': ""
                }

            entity_times[entity_name][service_id]['Chargable_Time'] += chargable_time
            entity_times[entity_name][service_id]['Non_Chargable_Time'] += non_chargable_time

            # Fetch hold record for remarks
            hold_record = db.query(models.HOLD).filter(
                models.HOLD.Service_ID == service_id,
                models.HOLD.user_id == getattr(record, user_field)  # Fix user_id reference
            ).first()

            remarks = hold_record.remarks if hold_record else ""
            entity_times[entity_name][service_id]['Remarks'] = remarks
            
        return has_activity_for_day  # Return whether any activity was processed for the day

    # Main function that generates the daily summaries
    daily_summaries = OrderedDict()
    current_day = picked_datett

    while current_day <= to_datett:
        entity_times = defaultdict(lambda: defaultdict(lambda: defaultdict(timedelta)))

        # Track if any activities were processed for the current day
        day_has_data = False

        # Process each activity type
        for activity, model, start_field, end_field in [
            ('hold', models.HOLD, 'hold_time_start', 'hold_time_end'),
            ('break', models.BREAK, 'break_time_start', 'break_time_end'),
            ('meeting', models.MEETING, 'meeting_time_start', 'meeting_time_end'),
            ('call', models.CALL, 'call_time_start', 'call_time_end'),
            ('in_progress', models.INPROGRESS, 'start_time', 'end_time'),
        ]:
            records = db.query(model).filter(
                getattr(model, start_field).between(
                    current_day.replace(hour=0, minute=0, second=0),
                    current_day.replace(hour=23, minute=59, second=59)
                )
            ).all()

            # Process records and check if there was any valid data
            if process_records_for_day(current_day.date(), records, start_field, end_field, 'user_id', entity_times):
                day_has_data = True

        # Only add the summary if there was data for the day
        if day_has_data:
            formatted_day_summary = {
                current_day.strftime("%Y-%m-%d"): []
            }
            for entity_name in entity_times:
                for service_id in entity_times[entity_name]:
                    formatted_day_summary[current_day.strftime("%Y-%m-%d")].append({
                        'Entity_Name': entity_name,
                        'GSTIN/TAN': entity_times[entity_name][service_id]['gst'],
                        'Nature_of_Work': entity_times[entity_name][service_id]['nature_of_work'],
                        'Estimated_Time': entity_times[entity_name][service_id]['estimated_time'],
                        'Chargable_Time': format_timedelta_to_str(entity_times[entity_name][service_id]['Chargable_Time']),
                        'Non_Chargable_Time': format_timedelta_to_str(entity_times[entity_name][service_id]['Non_Chargable_Time']),
                        'Total_Time_Taken': format_timedelta_to_str(
                            entity_times[entity_name][service_id]['Chargable_Time'] +
                            entity_times[entity_name][service_id]['Non_Chargable_Time']
                        ),
                        'Count': entity_times[entity_name][service_id]['no_of_items'],
                        'Remarks': entity_times[entity_name][service_id]['Remarks'],
                    })

            daily_summaries.update(formatted_day_summary)

        current_day += timedelta(days=1)

    return daily_summaries
