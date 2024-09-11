from concurrent.futures import ThreadPoolExecutor
from custom_logger import thread_local


class PropagatingThreadPoolExecutor(ThreadPoolExecutor):
    def submit(self, fn, *args, **kwargs):
        # Capture the current thread's context
        context = getattr(thread_local, 'context', None)

        # Wrapper function to run with the captured context
        def wrapper(*args, **kwargs):
            # Set the context in the new thread
            thread_local.context = context
            try:
                return fn(*args, **kwargs)
            finally:
                # Clean up context after task completion
                if hasattr(thread_local, 'context'):
                    del thread_local.context

        # Submit the task to the ThreadPoolExecutor
        return super().submit(wrapper, *args, **kwargs)


