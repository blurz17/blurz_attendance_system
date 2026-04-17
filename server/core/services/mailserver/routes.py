from fastapi import APIRouter
from .schema import Mail_send_Mode
from .service import welcome_message,mail
mail_router = APIRouter()

@mail_router.post('/welcome')
async def sending_mail(mails:Mail_send_Mode):
    
  
    recepients = mails.emails
    message =await welcome_message(recepients=recepients)
    
    await mail.send_message(message)
    return {'message':'Email has been sent'}
    
    