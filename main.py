from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from database import citas_collection, verificar_conexion
from models import CitaMedicaCreate, CitaMedicaResponse, CitaMedicaUpdate

app = FastAPI(title="API Asíncrona - Centro Médico (Daniel Ovalle)", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_db_client():
    await verificar_conexion()


@app.get("/", tags=["Estado"])
async def root():
    return {
        "message": "API de Citas Médicas funcionando correctamente con FastAPI y Motor"
    }


@app.post(
    "/citas/",
    response_model=CitaMedicaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Citas Médicas"],
)
async def crear_cita(cita: CitaMedicaCreate):
    resultado = await citas_collection.insert_one(cita.model_dump())
    if not resultado.acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MongoDB no confirmó el guardado de la cita",
        )

    cita_creada = await citas_collection.find_one({"_id": resultado.inserted_id})
    if cita_creada is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La cita fue enviada a MongoDB, pero no se pudo recuperar",
        )
    return cita_creada


@app.get("/citas/", response_model=list[CitaMedicaResponse], tags=["Citas Médicas"])
async def listar_citas():
    citas = []
    async for cita in citas_collection.find():
        citas.append(cita)
    return citas


@app.get("/citas/{id}", response_model=CitaMedicaResponse, tags=["Citas Médicas"])
async def obtener_cita(id: str):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="El ID proporcionado no es válido")

    cita = await citas_collection.find_one({"_id": obj_id})
    if not cita:
        raise HTTPException(status_code=404, detail="Cita médica no encontrada")
    return cita


@app.put("/citas/{id}", response_model=CitaMedicaResponse, tags=["Citas Médicas"])
async def actualizar_cita(id: str, cita_upd: CitaMedicaUpdate):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="El ID proporcionado no es válido")

    datos_a_actualizar = {
        k: v for k, v in cita_upd.model_dump(exclude_unset=True).items()
    }

    if not datos_a_actualizar:
        raise HTTPException(
            status_code=400, detail="No se enviaron datos para actualizar"
        )

    resultado = await citas_collection.update_one(
        {"_id": obj_id}, {"$set": datos_a_actualizar}
    )

    if resultado.matched_count == 0:
        raise HTTPException(
            status_code=404, detail="Cita médica no encontrada para actualizar"
        )

    cita_actualizada = await citas_collection.find_one({"_id": obj_id})
    return cita_actualizada


@app.delete("/citas/{id}", status_code=status.HTTP_200_OK, tags=["Citas Médicas"])
async def eliminar_cita(id: str):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="El ID proporcionado no es válido")

    resultado = await citas_collection.delete_one({"_id": obj_id})

    if resultado.deleted_count == 0:
        raise HTTPException(
            status_code=404, detail="Cita médica no encontrada para eliminar"
        )

    return {"message": "Cita médica eliminada exitosamente"}
