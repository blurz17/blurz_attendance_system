from pydantic import BaseModel



class Mail_send_Mode(BaseModel):
    emails:list[str]
  