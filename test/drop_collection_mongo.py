from pymongo import MongoClient

def drop_collections():
    """Drop specified collections from the MongoDB database."""

    """
    [DATABASE]
    # MongoDB connection string with authentication
    MONGO_URI = mongodb://sa:963852@192.168.102.120:27017
    DATABASE_NAME = WEB_SCRAPING 

    """
    # Connect to MongoDB (change the URI if needed)
    client = MongoClient('mongodb://sa:963852@192.168.102.120:27017')
    
    # Replace with your database name
    db = client['WEB_SCRAPING']

    collections_to_drop = [
        'nse_advances_declines',
        'nse_large_deals',
        'nse_most_active_contracts',
        'nse_most_active_equities',
        'nse_most_active_underlying',
        'nse_new_listings',
        'nse_week_52_data',
        'nse_indices_data',
        'nse_price_band_hitters',
        'nse_stock_events',
        'nse_gainers_losers',
        'nse_top_gainers_losers',
        'nse_forthcoming_listings',
        'nse_adv_decl_unch',
        'advances_declines_unchanged',
        'nse_52_week_high_low',
        'nse_52_week_high_low_data',
        'indices_data',
        #we have to delete old collection anme also 
        'advances_declines',
        'gainers_losers',
        'large_deals',
        'forthcoming_listings',
        'top_gainers_losers',
        'most_active_contracts',
        'most_active_equities',
        'most_active_underlying',
        'new_listings',
        'week_52_data',
        'price_band_hitters',
        'stock_events',
        'most_active_securities'
        ]

    for coll_name in collections_to_drop:
        if coll_name in db.list_collection_names():
            db[coll_name].drop()
            print(f"Dropped collection: {coll_name}")
        else:
            print(f"Collection not found: {coll_name}")

if __name__ == '__main__':
    drop_collections()
