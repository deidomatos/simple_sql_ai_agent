import argparse
import logging
from .api.app import start as start_api
from .database.seed import seed_database

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the SQL Agent application.
    """
    parser = argparse.ArgumentParser(description="SQL Agent")
    parser.add_argument("--seed", action="store_true", help="Seed the database")
    parser.add_argument("--api", action="store_true", help="Start the API server")
    
    args = parser.parse_args()
    
    if args.seed:
        logger.info("Seeding the database...")
        seed_database()
        logger.info("Database seeded successfully")
    
    if args.api:
        logger.info("Starting the API server...")
        start_api()
    
    # If no arguments are provided, start the API server
    if not args.seed and not args.api:
        logger.info("No arguments provided, starting the API server...")
        start_api()

if __name__ == "__main__":
    main()