from concurrent.futures import ThreadPoolExecutor, as_completed

class TaskManager:
    """
    A class to manage and execute tasks concurrently using a thread pool.

    Attributes:
        executor (ThreadPoolExecutor): The thread pool executor used to submit tasks.
        futures (list): A list to track the futures representing the tasks.

    Methods:
        add_task(func, *args, **kwargs): Adds a task to the executor for concurrent execution.
        get_results(): Collects and returns the results of all completed tasks.
        shutdown(): Shuts down the thread pool executor.
    """

    def __init__(self):
        """
        Initializes the TaskManager instance with a thread pool executor and an empty list of futures.
        """

        self.executor = ThreadPoolExecutor()
        self.futures = []

    def add_task(self, func, *args, **kwargs):
        """
        Adds a task to the thread pool executor for concurrent execution.

        Args:
            func (callable): The function to be executed concurrently.
            *args: Variable length argument list to be passed to the function.
            **kwargs: Arbitrary keyword arguments to be passed to the function.

        Returns:
            concurrent.futures.Future: A future object representing the task's execution.
        """

        future = self.executor.submit(func, *args, **kwargs)
        self.futures.append(future)
        return future

    def get_results(self):
        """
        Collects and returns the results of all completed tasks.

        Returns:
            list: A list containing the results of all completed tasks. If a task raises an exception,
            the exception is included in the list.
        """

        results = []
        for future in as_completed(self.futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(e)
        return results

    def shutdown(self):
        """
        Shuts down the thread pool executor and waits for all tasks to complete.

        This method ensures that no new tasks are accepted, and it waits for all currently running
        tasks to finish before shutting down the executor.
        """
        
        self.executor.shutdown(wait=True)
