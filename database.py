from decouple import config
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = str(config("MONGODB_URL", default="mongodb://localhost:27017"))
DATABASE_NAME = str(config("DATABASE_NAME", default="Centro_Medico"))

client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

citas_collection = database["citas"]


async def verificar_conexion():
    await client.admin.command("ping")

    colecciones = await database.list_collection_names()
    if citas_collection.name not in colecciones:
        await database.create_collection(citas_collection.name)

    print(
        f"MongoDB listo - Base de datos: '{DATABASE_NAME}', "
        f"colección: '{citas_collection.name}'"
    )
    return True
