# import schedule
# import time
# from API.Controller.top_gainers_loosers import fetch_and_store_gainers_loosers

# def job():
#     print("⏰ Running NSE gainers/loosers cron...")
#     fetch_and_store_gainers_loosers("gainers")
#     fetch_and_store_gainers_loosers("loosers")

# # Run every N minutes
# schedule.every(1).minutes.do(job)
# # schedule.every(3).minutes.do(job)
# # schedule.every(5).minutes.do(job)
# # schedule.every(15).minutes.do(job)

# print("✅ Cron started...")
# while True:
#     schedule.run_pending()
#     time.sleep(1)
