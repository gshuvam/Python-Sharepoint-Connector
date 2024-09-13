from concurrent.futures import ThreadPoolExecutor, as_completed

class TaskManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor()
        self.futures = []

    def add_task(self, func, *args, **kwargs):
        future = self.executor.submit(func, *args, **kwargs)
        self.futures.append(future)
        return future

    def get_results(self):
        results = []
        for future in as_completed(self.futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(e)
        return results

    def shutdown(self):
        self.executor.shutdown(wait=True)
