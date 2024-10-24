from collections import defaultdict
import datetime
import logging
from operator import and_
import threading
from typing import Dict
from fastapi import Depends,FastAPI,HTTPException,Form,UploadFile,Response
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
# from typing import Annotated
from typing_extensions import Annotated,List
from datetime import datetime, timedelta
import pandas as pd
from src import crud, models, schemas
from src.database import SessionLocal, engine
from fastapi.responses import StreamingResponse
import json
import io
from io import BytesIO
import csv
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from urllib.parse import unquote
import base64
import uuid

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "" with the origins you want to allow
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Add other HTTP methods as needed
    allow_headers=["*"],  # Allow all headers
)
# ----------------------------------------------------------------------------------------

@app.post("/insert_nature_of_work",response_model=str)
def nature_of_work(work_name:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.insert_nature_of_work(db,work_name)

@app.get("/get_nature_of_work",response_model=List[schemas.Nature_Of_Work])
def nature_of_work(db: Session = Depends(get_db)):
     return crud.get_nature_of_work(db)

@app.delete("/delete_nature_of_work",response_model=str)
def nature_of_work(work_id:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.delete_nature_of_work(db,work_id)

@app.put("/update_nature_of_work",response_model=str)
def nature_of_work(work_id:Annotated[int,Form()],work_name:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.update_nature_of_work(db,work_name,work_id)

# ----------------------------------------------------------------------------------------

@app.post("/insert_user",response_model=str)
def insert_user(username:Annotated[str,Form()],role:Annotated[str,Form()],firstname:Annotated[str,Form()],lastname:Annotated[str,Form()],location:Annotated[str,Form()],db:Session=Depends(get_db)):
     return crud.insert_user(db,username,role,firstname,lastname,location)

@app.get("/get_user",response_model=List[schemas.User_table])
def nature_of_work(db:Session = Depends(get_db)):
     return crud.get_user(db)

@app.delete("/delete_user",response_model=str)
def nature_of_work(user_id:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.delete_user(db,user_id)

@app.put("/update_user",response_model=str)
def nature_of_work(user_id:Annotated[int,Form()],user_name:Annotated[str,Form()],user_role:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.update_user(db,user_id,user_name,user_role)

# ----------------------------------------------------------------------------------------

@app.post("/login_user",response_model=List[schemas.User_table])
def login_user(username:Annotated[str,Form()],password:Annotated[str,Form()],db:Session=Depends(get_db)):
     return crud.login_check(db,username,password)

# ----------------------------------------------------------------------------------------

@app.post("/tl_insert",response_model=str)
def tl (name_of_entity:Annotated[str,Form()],gst_or_tan:Annotated[str,Form()],gst_tan:Annotated[str,Form()],client_grade:Annotated[str,Form()],Priority:Annotated[str,Form()],Assigned_By:Annotated[int,Form()],estimated_d_o_d:Annotated[str,Form()],estimated_time:Annotated[str,Form()],Assigned_To:Annotated[int,Form()],Scope:Annotated[int,Form()],nature_of_work:Annotated[int,Form()],From:Annotated[int,Form()],Actual_d_o_d:Annotated[str,Form()],db:Session=Depends(get_db)):
     return crud.tl_insert(db,name_of_entity,gst_or_tan,gst_tan,client_grade,Priority,Assigned_By,estimated_d_o_d,estimated_time,Assigned_To,Scope,nature_of_work,From,Actual_d_o_d)

@app.post("/tl_insert_bulk",response_model=str)
def tl_insert_bulk(file:UploadFile,db:Session=Depends(get_db)):
     return crud.tl_insert_bulk(db,file)

# ----------------------------------------------------------------------------------------

@app.post("/tm_get",response_model=list)
def tm_get(user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.get_work(db,user_id)

@app.post("/tl_get",response_model=list)
def tm_get(picked_date:Annotated[str,Form()],to_date:Annotated[str,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.get_work_tl(picked_date,to_date,db,user_id)

# ----------------------------------------------------------------------------------------

# @app.post("/start")
# def start(service_id:Annotated[int,Form()],type_of_activity:Annotated[str,Form()],no_of_items:Annotated[str,Form()],db:Session=Depends(get_db)):
#      return crud.start(db,service_id,type_of_activity,no_of_items)

@app.post("/reallocated")
def reallocated(service_id:Annotated[int,Form()],remarks:Annotated[str,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.reallocated(db,service_id,remarks,user_id)

# ----------------------------------------------------------------------------------------

@app.post("/get_count",response_model=list)
def get_count(user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.get_count(db,user_id)

@app.post("/get_count_tl",response_model=list)
def get_count_tl(user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.get_count_tl(db,user_id)

# ----------------------------------------------------------------------------------------

# @app.get("/break_check")
# def break_check(db:Session=Depends(get_db)):
#      return crud.get_break_time_info(db)

# ----------------------------------------------------------------------------------------

@app.post("/get_reports")
async def get_reports(response:Response,fields:Annotated[str,Form()],db:Session=Depends(get_db)):
     df = await crud.get_reports(db,fields)
     excel_output = BytesIO()
     with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
          df.to_excel(writer, index=False, sheet_name='Sheet1')
     excel_output.seek(0)
     response.headers["Content-Disposition"] = "attachment; filename=data.xlsx"
     response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
     return Response(content=excel_output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# @app.post("/break_start")
# def break_start(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.break_start(db,service_id,'',user_id)

# @app.post("/break_end")
# def break_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.break_end(db,service_id,user_id)

# @app.post("/call_start")
# def call_start(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.call_start(db,service_id,'',user_id)

# @app.post("/call_end")
# def call_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.call_end(db,service_id,user_id)

# @app.post("/end_of_day_start")
# def end_of_day_start(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.end_of_day_start(db,service_id,'',user_id)

# @app.post("/end_of_day_end")
# def end_of_day_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.end_of_day_end(db,service_id,user_id)

# @app.post("/hold_start")
# def hold_start(service_id:Annotated[int,Form()],remarks:Annotated[str,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.hold_start(db,service_id,remarks,user_id)

# @app.post("/hold_end")
# def hold_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.hold_end(db,service_id,user_id)

# @app.post("/meeting_start")
# def meeting_start(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.meeting_start(db,service_id,'',user_id)

# @app.post("/meeting_end")
# def meeting_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.meeting_end(db,service_id,user_id)

# @app.post("/Completed")
# def Completed(service_id:Annotated[int,Form()],count:Annotated[int,Form()],db:Session=Depends(get_db)):
#      return crud.Completed(db,service_id,count)



@app.post("/User_Wise_Day_Wise_Part_1")
def User_Wise_Day_Wise_Part_1(picked_date:Annotated[str,Form()],to_date:Annotated[str,Form()],db:Session=Depends(get_db)):
     return crud.User_Wise_Day_Wise_Part_1(db,picked_date,to_date)

@app.post("/insert_tds",response_model=str)
def tds(tds:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.insert_tds(db,tds)

@app.get("/get_tds",response_model=List[schemas.tds])
def tds(db: Session = Depends(get_db)):
     return crud.get_tds(db)

@app.delete("/delete_tds",response_model=str)
def tds(tds_id:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.delete_tds(db,tds_id)

@app.put("/update_tds",response_model=str)
def tds(tds_id:Annotated[int,Form()],tds:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.update_tds(db,tds,tds_id)

@app.post("/insert_gst",response_model=str)
def gst(gst:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.insert_gst(db,gst)

@app.get("/get_gst",response_model=List[schemas.gst])
def gst(db: Session = Depends(get_db)):
     return crud.get_gst(db)

@app.delete("/delete_gst",response_model=str)
def gst(gst_id:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.delete_gst(db,gst_id)

@app.put("/update_gst",response_model=str)
def gst(gst_id:Annotated[int,Form()],gst:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.update_gst(db,gst,gst_id)

@app.delete("/delete_entity",response_model=str)
def delete_entity(record_service_id:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.delete_entity(db,record_service_id)

@app.post("/reallocated_end")
def reallocated_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.reallocated_end(db,service_id,user_id)


@app.post("/reportsnew")
def lastfivereports(picked_date:Annotated[str,Form()],to_date:Annotated[str,Form()],report_name:Annotated[str,Form()],db:Session=Depends(get_db)):
     return crud.lastfivereports(db,picked_date,to_date,report_name)

@app.post("/Hold_Wise_Part")
def Hold_Wise_Part(picked_date:Annotated[str,Form()],to_date:Annotated[str,Form()],db:Session=Depends(get_db)):
     return crud.Hold_Wise_Day_Wise_Part(db,picked_date,to_date)


@app.post("/reportstotal")
def totalfivereports(picked_date:Annotated[str,Form()],to_date:Annotated[str,Form()],report_name:Annotated[str,Form()],db:Session=Depends(get_db)):
     return crud.totalfivereports(db,picked_date,to_date,report_name)

def base64_decode(encoded_str):
    decoded_bytes = base64.b64decode(encoded_str)
    return decoded_bytes

def decrypt_data(key: bytes, enc_data: str) -> bytes:
    enc_data_bytes = base64_decode(enc_data)
    iv = enc_data_bytes[:AES.block_size]
    ct = enc_data_bytes[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt


private_key = b'MAHIMA1234560987'

@app.post("/login_user_check")
def login_user_check(token:Annotated[str,Form()],db:Session=Depends(get_db)):
     encripted_data = unquote(token)
     decrypted_data = json.loads(decrypt_data(private_key, encripted_data))

     token = decrypted_data['token']
     employeeid = decrypted_data['user']
     name = decrypted_data['name']
     location1 = decrypted_data['location']
     user_type = decrypted_data['user_type']

     if user_type == "customer":
          pass
     else:
          return crud.login_check(db,employeeid,"jaa")
     

@app.post("/scopes/")
def scope_add(scope:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.scope_add(scope,db)

@app.delete("/scope_delete/")
def scope_delete(scope_id:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.scope_delete(scope_id,db)

@app.get("/get_scope")
def gst(db: Session = Depends(get_db)):
     return crud.get_scope(db)


@app.put("/update_scopes")
def update_scope(scope_id:Annotated[int,Form()], new_scope:Annotated[str,Form()], db: Session = Depends(get_db)):
    result = crud.scope_update(scope_id, new_scope, db)
    if result == "Success":
        return "Success"
    elif result == "Scope not found":
        raise HTTPException(status_code=404, detail="Scope not found")
    else:
        raise HTTPException(status_code=500, detail="Failed to update scope")
    
@app.post("/sub_scopes/")
def sub_scope_add(scope_id:Annotated[int,Form()], sub_scope:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.sub_scope_add(scope_id,sub_scope,db)

@app.delete("/sub_scope_delete/")
def sub_scope_delete(sub_scope_id:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.sub_scope_delete(sub_scope_id,db)

@app.put("/update_sub_scopes")
def update_sub_scope(sub_scope_id:Annotated[int,Form()], new_scope:Annotated[str,Form()], db: Session = Depends(get_db)):
    result = crud.sub_scope_update(sub_scope_id,new_scope, db)
    
    if result == "Success":
        return "Success"
    elif result == "Scope not found":
        raise HTTPException(status_code=404, detail="Scope not found")
    else:
        raise HTTPException(status_code=500, detail="Failed to update scope")
    
@app.post("/get_sub_scope")
def subscope(scope_id:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.get_sub_scope(scope_id,db)

@app.post("/logintime")
def logintime_add(logtime:Annotated[str,Form()],userid:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.logintime_add(logtime,userid,db)

@app.post("/logouttime")
def logout_time_add(logouttime:Annotated[str,Form()],userid:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.logout_time_add(logouttime,userid,db)

@app.post("/entityadd")
def entityadd(entityname:Annotated[str,Form()],tanorgst:Annotated[str,Form()],tanvalue:Annotated[str,Form()],db: Session = Depends(get_db)):
     return crud.entityadd(entityname,tanorgst,tanvalue,db)

@app.get("/get_entitydata")
def gst(db: Session = Depends(get_db)):
     return crud.get_entity_data(db)

@app.post("/get_filter_entitydata")
def get_filter_entitydata(id:Annotated[int,Form()],db: Session = Depends(get_db)):
     return crud.get_filter_entitydata(id,db)



# --------------------------------elan code start------------------------------------- 

#-----------------------lOGIN LOGOUT TRACKING------------------------------------------
@app.post("/get_user_status", response_model=List[schemas.UserStatus])
def get_filtered_user_status(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    return crud.get_user_status(picked_date, to_date, db)
#-----------------------lOGIN LOGOUT TRACKING------------------------------------------


#-----------------------------------hold automation for missing date----pip install APScheduler--------------------------
from apscheduler.schedulers.background import BackgroundScheduler
import logging

def job_wrapper_update_start_time():
    db = SessionLocal()  # Create a new session
    try:
        # Call your function here (e.g., update start time logic)
        print("Updating start time...")
        crud.fetch_hold_data(db)
        # Add your logic to update the start time
    except Exception as e:
        print(f"Error updating start time: {e}")
    finally:
        db.close()  # Ensure the session is closed

# Set up a scheduler
scheduler = BackgroundScheduler()

# Add the job to the scheduler
scheduler.add_job(
    job_wrapper_update_start_time,
    trigger='cron',
    hour=17,  # Runs daily at 23 PM or night 11 PM
    minute=56,  # Run exactly at the start of the hour
    timezone='Asia/Kolkata'  
)

# Start the scheduler and print a message
scheduler.start()
print("Scheduler started for hold missing date.")

# Optionally, you can add a shutdown handler to stop the scheduler gracefully
def shutdown_scheduler():
    scheduler.shutdown()
    print("Scheduler stopped for hold missing date.")
    logging.info("Scheduler stopped for hold missing date.")

# Example of how you might call shutdown_scheduler when needed
# shutdown_scheduler()  # Uncomment this line when you want to stop the scheduler.

# --------------------------------end



# ---------------------------Work status  automatic break,hold,work in progres,call and metting------------------------------

from apscheduler.schedulers.background import BackgroundScheduler

def time_check_loop():
    db = SessionLocal()
    try:
        crud.check_and_update_work_status(db)
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    # Start the scheduler when FastAPI starts
    scheduler = BackgroundScheduler()

    # Schedule the job to run every day at 8:55 PM IST
    scheduler.add_job(
        time_check_loop,  # function to call
        trigger='cron',  # cron scheduling
        hour=12,  # 21 PM or night 9 PM
        minute=50,  # 0 minutes
        timezone='Asia/Kolkata'  # Set the timezone to IST
    )

    # Start the scheduler
    scheduler.start()
    logging.info("Scheduler started for 9:00 PM IST.")

    # Ensure the scheduler shuts down with the application
    @app.on_event("shutdown")
    async def shutdown_event():
        scheduler.shutdown()
        logging.info("Scheduler stopped.")

# ------------------------------------- automatic------------------------------


# -------------------------------------logout automatic------------------------------
  
from apscheduler.schedulers.background import BackgroundScheduler

def time_check_logout(db: Session):
    crud.time_check_logout(db)

@app.on_event("startup")
async def startup_event():
    # Start the scheduler on FastAPI startup
    
    scheduler = BackgroundScheduler()

    # Schedule the job to run every day at 21:00 IST (9 PM)
    scheduler.add_job(
        lambda: time_check_logout(SessionLocal()),
        trigger='cron',
        hour=12,
        minute=50,
        timezone='Asia/Kolkata'
    )
    
    # Start the scheduler
    scheduler.start()

    logging.info("Scheduler started for 9 PM IST.")

    # Ensuring proper shutdown
    @app.on_event("shutdown")
    async def shutdown_event():
        scheduler.shutdown()
        logging.info("Scheduler stopped.")
# --------------------------------end



# ------------------------hold
@app.post("/hold_start")
def hold_start(service_id:Annotated[int,Form()],remarks:Annotated[str,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.hold_start(db,service_id,remarks,user_id)

@app.post("/hold_end")
def hold_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.hold_end(db,service_id,user_id)


# --------------checking purpose
# @app.post("/calculate_total_time_hold/")
# def get_total_time(
#     picked_date: Annotated[str, Form()],
#     to_date: Annotated[str, Form()],
#     db: Session = Depends(get_db)
# ):
#     # Call the function from crud to get the total time
#     hold_total_time = crud.calculate_total_time_hold(db, picked_date, to_date)
#     return hold_total_time

# ------------------------break
@app.post("/break_start")
def break_start(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.break_start(db,service_id,user_id)

@app.post("/break_end")
def break_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.break_end(db,service_id,user_id)


# ------------------------meeting
@app.post("/meeting_start")
def meeting_start(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.meeting_start(db,service_id,user_id)

@app.post("/meeting_end")
def meeting_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.meeting_end(db,service_id,user_id)

# ------------------------call
@app.post("/call_start")
def call_start(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.call_start(db,service_id,user_id)

@app.post("/call_end")
def call_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.call_end(db,service_id,user_id)

# ------------------------inprogress

@app.post("/start")
def start(service_id:Annotated[int,Form()],type_of_activity:Annotated[str,Form()],no_of_items:Annotated[str,Form()],db:Session=Depends(get_db)):
     return crud.inprogress_start(db,service_id,type_of_activity,no_of_items)

# ------------------------end of the day
@app.post("/end_of_day_start")
def end_of_day_start(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.end_of_day_start(db,service_id,user_id)

@app.post("/end_of_day_end")
def end_of_day_end(service_id:Annotated[int,Form()],user_id:Annotated[int,Form()],db:Session=Depends(get_db)):
     return crud.end_of_day_end(db,service_id,user_id)



# -----------------------completed

@app.post("/Completed")
def Completed(
    service_id: Annotated[int, Form()],
    count: Annotated[int, Form()], 
    db: Session = Depends(get_db)
):
    return crud.Completed(db, service_id, count)  



# ------------------------idealtimecalculation
@app.post("/idealtimecalculation")
def idealtimecalculation(userid: Annotated[int, Form()], check_status: Annotated[str, Form()], db: Session = Depends(get_db)):
    return crud.idealtime(userid, check_status, db)


@app.post("/calculate_teamwise_total_time")
def calculate_teamwise_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    # Call the CRUD function to calculate total time for all users
    total_time = crud.calculate_total_time(picked_date, to_date, db)
    return total_time



# ----ouput
@app.post("/teamwise_total_time")
def calculate_total_time1ss(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    # Call the CRUD function to calculate total time for all users
    total_time = crud.calculate_total_time1ss(picked_date, to_date, db)
    return total_time
# -----------------------

# -----------------------total time for all user in userwise reporst

@app.post("/calculate_total_time_userwise", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user(db, picked_date, to_date)
    return total_times

# ----ouput
@app.get("/usercalculate-end-time11", response_model=List[dict])
async def get_calculated_time(
    picked_date: str, 
    to_date: str, 
    db: Session = Depends(get_db)
):
    # Call your function to calculate the end time
    result = crud.calculate_end_time_for_user1s(db, picked_date, to_date)
    return result

# -----------------corn job to fetch the value in all table--------- 

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

def update_total_time_job():
    db = next(get_db())
    user_ids = crud.get_all_user_ids(db)  
    service_ids = crud.get_all_service_ids(db)  
    for user_id in user_ids:
        for service_id in service_ids:
            crud.fetch_total_time(db, user_id, service_id)  
    db.close()  

scheduler.add_job(update_total_time_job, CronTrigger(hour=11, minute=3))
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()





# -----------------

from sqlalchemy.exc import IntegrityError



# FastAPI endpoint to trigger reallocation
@app.post("/reallocate/{service_id}")
def reallocate_service_endpoint(service_id: int, user_id: int, admin_id: int, current_user_id: int, remarks: str, db: Session = Depends(get_db)):
    # Call the reallocation logic
    return crud.reallocate_service(db, service_id, user_id, admin_id, current_user_id, remarks)

@app.get("/admin-tasks/{admin_id}")
def get_reallocated_tasks(admin_id: int, db: Session = Depends(get_db)):
    tasks = db.query(models.TL).filter(
        models.TL.Assigned_To == admin_id,
        models.TL.reallocated_by.isnot(None)  # Only tasks that were reallocated
    ).all()

    if not tasks:
        raise HTTPException(status_code=404, detail="No reallocated tasks found")

    return tasks



# @app.post("/update-total-time/")
# async def update_total_time(
#     picked_date: Annotated[str, Form()],
#     to_date: Annotated[str, Form()],
#     db: Session = Depends(get_db)
# ):
#     # Fetch service and user IDs from TL table
#     tl_record = db.query(models.TL).filter(
#         and_(
#             models.TL.Assigned_To.isnot(None),  # Ensure Assigned_To is not null
#             models.TL.status == 1  # Only fetch active records
#         )
#     ).first()  # Assuming you want the first matching record

#     if not tl_record:
#         return {"message": "No active service found."}

#     service_id = tl_record.Service_ID
#     user_id = tl_record.Assigned_To

#     # Fetch total time using the fetched user_id and service_id
#     await crud.fetch_total_time1(db, user_id, service_id, picked_date, to_date)

#     return {
#         "message": "Total time updated successfully",
#         "picked_date": picked_date,
#         "to_date": to_date,
#         "service_id": service_id,
#         "user_id": user_id
#     }


# -----pasupathi reports------------------
@app.post("/User_Wise-Day_wise_part2", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user2(db, picked_date, to_date)
    return total_times

@app.post("/Entity_Day_Wise", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user3(db, picked_date, to_date)
    return total_times

@app.post("/Entity-Completed_status_utilization", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user4(db, picked_date, to_date)
    return total_times

@app.post("/Entity-Inprogress_status_utilization", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user5(db, picked_date, to_date)
    return total_times

@app.post("/Entity-Hold_status_utilization", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user6(db, picked_date, to_date)
    return total_times

@app.post("/Entity_Wise_total_time_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user7(db, picked_date, to_date)
    return total_times

@app.post("/Entity_cum_nature_of_work_wise_total_time_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user8(db, picked_date, to_date)
    return total_times

@app.post("/Scope_wise_Time_Taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user9(db, picked_date, to_date)
    return total_times

@app.post("/Scope_cum_Subscope_time_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user10(db, picked_date, to_date)
    return total_times


@app.post("/Subscope_wise_time_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user11(db, picked_date, to_date)
    return total_times

@app.post("/Subscope_cum_nature_of_work_time_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user12(db, picked_date, to_date)
    return total_times

@app.post("/Entity_wise_Estimated_time_vs_Total_time_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user21(db, picked_date, to_date)
    return total_times

@app.post("/Entity_cum_serviceid_wise_Estimated_time_vs_Total_time_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user13(db, picked_date, to_date)
    return total_times

@app.post("/Team_member_cum_Entity_wise_Total_Time_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user14(db, picked_date, to_date)
    return total_times

@app.post("/Team_member_cum_Nature_of_work_wise_Total_Time_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user15(db, picked_date, to_date)
    return total_times

@app.post("/Team_member_cum_Nature_of_work_wise_Estimated_Time_vs_Total_Time", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user16(db, picked_date, to_date)
    return total_times

@app.post("/Team_member_cum_Nature_of_work_wise_Estimated_Time_vs_chargable", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user17(db, picked_date, to_date)
    return total_times

@app.post("/Team_member_cum_Nature_of_work_with_no.of.entity", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user18(db, picked_date, to_date)
    return total_times


@app.post("/Entity_wise_no_of_days_taken", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user19(db, picked_date, to_date)
    return total_times


@app.post("/Entity_wise_estimated_vs_Actual_DateOfDelivery", response_model=dict)
def get_total_time(
    picked_date: Annotated[str, Form()],
    to_date: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    total_times = crud.calculate_end_time_for_user20(db, picked_date, to_date)
    return total_times