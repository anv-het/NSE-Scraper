import threading
import uvicorn
from Loader.server import apiserver
from Utils.config_reader import configure
from Services.cron_jobs import CronJobManager

if __name__ == '__main__':
    # Start cron job scheduler in a background thread
    cron_manager = CronJobManager()
    threading.Thread(target=cron_manager.run_cron_jobs, daemon=True).start()

    # Start API server
    uvicorn.run(apiserver, host=configure.get("SERVER", "HOST"), port=configure.getint("SERVER", "PORT"))

