from pydantic import BaseModel
import json
from datetime import date
from typing import Optional

class Nature_Of_Work(BaseModel):
    work_id:int
    work_name:str
    work_status:int

class User_table(BaseModel):
    user_id:int
    username:str
    password:str
    role:str
    firstname:str
    lastname:str
    location:str
    user_status:int

class tds(BaseModel):
    tds_id:int
    tds:str
    tds_status:int

class gst(BaseModel):
    gst_id:int
    gst:str
    gst_status:int


class TLInsert(BaseModel):
    name_of_entity: str
    gst_or_tan: str
    gst_tan: str
    client_grade: str
    Priority: str
    Assigned_By: int
    estimated_d_o_d: str
    estimated_time: str
    Assigned_To: int
    Scope: int
    nature_of_work: int
    From: int
    Actual_d_o_d: str
    
#-----------------------lOGIN LOGOUT TRACKING------------------------------------------

class UserStatus(BaseModel):
    username: str
    login_time: str
    logout_time: str
    login_date: str
    duration: str
    status: str

class FetchTotalTimeResponse(BaseModel):
    message: str
    user_id: int
    service_id: int
    date: str  
    total_inprogress_time: str
    total_hold_time: str
    total_break_time: str
    total_meeting_time: str
    total_call_time: str
    total_ideal_time: str
    total_completed_time: str






from pydantic import BaseModel
from typing import Dict, Optional

class UserTimeResponse(BaseModel):
    member_name: str
    idealtime: str
    in_progress: str
    break_time: str
    call_time: str
    meeting_time: str
    completed_time: str
    chargeable_time: str
    non_chargeable_time: str
    total_time: str

class TotalTimeResponse(BaseModel):
    total_times: Dict[str, UserTimeResponse]