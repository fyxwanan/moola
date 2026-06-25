import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

def get_db():
    return db_instance.db

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db_instance.db = db_instance.client[settings.DATABASE_NAME]
    logger.info(f"Connected to MongoDB database: {settings.DATABASE_NAME}")
    
    # Initialize default categories
    await init_default_categories()
    # Create indexes
    await create_database_indexes()

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db_instance.client:
        db_instance.client.close()
    logger.info("MongoDB connection closed.")

async def init_default_categories():
    categories_col = db_instance.db["categories"]
    # Check if system categories exist
    count = await categories_col.count_documents({"owner_id": None})
    if count > 0:
        return
        
    logger.info("Preloading default system categories...")
    default_categories = [
        # Expenses
        {"name": "餐饮", "type": "expense", "icon": "Utensils", "color": "#EF4444", "owner_id": None},
        {"name": "购物", "type": "expense", "icon": "ShoppingBag", "color": "#EC4899", "owner_id": None},
        {"name": "交通", "type": "expense", "icon": "Car", "color": "#3B82F6", "owner_id": None},
        {"name": "娱乐", "type": "expense", "icon": "Gamepad2", "color": "#8B5CF6", "owner_id": None},
        {"name": "住房", "type": "expense", "icon": "Home", "color": "#F59E0B", "owner_id": None},
        {"name": "水电", "type": "expense", "icon": "Droplet", "color": "#06B6D4", "owner_id": None},
        {"name": "医疗", "type": "expense", "icon": "HeartPulse", "color": "#10B981", "owner_id": None},
        {"name": "教育", "type": "expense", "icon": "GraduationCap", "color": "#6366F1", "owner_id": None},
        {"name": "其他支出", "type": "expense", "icon": "HelpCircle", "color": "#6B7280", "owner_id": None},
        
        # Incomes
        {"name": "工资", "type": "income", "icon": "Briefcase", "color": "#10B981", "owner_id": None},
        {"name": "奖金", "type": "income", "icon": "Award", "color": "#F59E0B", "owner_id": None},
        {"name": "投资", "type": "income", "icon": "TrendingUp", "color": "#3B82F6", "owner_id": None},
        {"name": "兼职", "type": "income", "icon": "Wallet", "color": "#8B5CF6", "owner_id": None},
        {"name": "其他收入", "type": "income", "icon": "Banknote", "color": "#6B7280", "owner_id": None},
    ]
    
    await categories_col.insert_many(default_categories)
    logger.info("Default system categories preloaded successfully.")

async def create_database_indexes():
    # Ensure users.username is unique
    await db_instance.db["users"].create_index("username", unique=True)
    
    # Drop unique index on email if it exists to allow empty email registrations
    try:
        indexes = await db_instance.db["users"].index_information()
        for idx_name, idx_info in indexes.items():
            # Check if index contains "email"
            if idx_name != "_id_" and "email" in dict(idx_info.get("key", {})):
                logger.info(f"Dropping index: {idx_name}")
                await db_instance.db["users"].drop_index(idx_name)
    except Exception as e:
        logger.warning(f"Error dropping email index: {e}")

    # Record query indexes
    await db_instance.db["records"].create_index([("user_id", 1), ("record_date", -1)])
    await db_instance.db["records"].create_index([("project_id", 1), ("record_date", -1)])
    
    # TTL index on files collection: expire after 30 days of last access (2592000 seconds)
    await db_instance.db["files"].create_index("last_accessed_at", expireAfterSeconds=2592000)
    
    logger.info("Database indexes verified/created.")
