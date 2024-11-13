'''
YODA (Your Open DAta)
EU CEF Action 2019-ES-IA-0121
University of Cantabria
Developer: Johnny Choque (jchoque@tlmat.unican.es)

Fork:
BEOPEN 2023
Developer: Marco Sajeva (sajeva.marco01@gmail.com)
'''

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
import logging 
from mqa_submits import submitRouter
from mqa_getters import getRouter
from mqa_delete import deleteRouter


app = FastAPI(title="BeOpen mqa-scoring")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# api to get the current version
@app.get("/version")
async def get_version():
  return {"version": "1.3.0"}

# if __name__ == "__main__":
#   main()


app.include_router(submitRouter, prefix='/submit')
app.include_router(getRouter, prefix='/get')
app.include_router(deleteRouter, prefix='/delete')

appPort = os.getenv("PORT", 8000)
if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=appPort)
    # uvicorn.run(app, host='localhost', port=appPort)