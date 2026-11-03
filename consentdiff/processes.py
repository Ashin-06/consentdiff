"""Own exactly one worker process tree, including browser descendants."""
import os
import signal
import subprocess
import threading


class ProcessTree:
    """Windows kill-on-close job; POSIX isolated process group.

    The worker waits for stdin, so it cannot launch Chrome before assignment to
    the job. The non-inheritable job handle belongs to Python: abrupt Python
    termination also closes it and kills the entire Windows worker tree.
    """
    def __init__(self, args, **kwargs):
        self._job = None
        self._closed = False
        self._lock = threading.Lock()
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs['start_new_session'] = True
        self.process = subprocess.Popen(args, **kwargs)
        if os.name == 'nt':
            try:
                self._assign_windows_job()
            except BaseException:
                self.process.kill()
                self.process.communicate(timeout=5)
                raise

    def _assign_windows_job(self):
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                ('flags', wintypes.DWORD), ('minimum_working_set', ctypes.c_size_t), ('maximum_working_set', ctypes.c_size_t),
                ('active_process_limit', wintypes.DWORD), ('affinity', ctypes.c_size_t),
                ('priority_class', wintypes.DWORD), ('scheduling_class', wintypes.DWORD)]

        class IOCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [('basic', BasicLimits), ('io', IOCounters), ('process_memory', ctypes.c_size_t),
                ('job_memory', ctypes.c_size_t), ('peak_process_memory', ctypes.c_size_t), ('peak_job_memory', ctypes.c_size_t)]

        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel.SetInformationJobObject.restype = wintypes.BOOL
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.CreateJobObjectW(None, None)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            if not kernel.AssignProcessToJobObject(handle, int(self.process._handle)):
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            kernel.CloseHandle(handle)
            raise
        self._kernel, self._job = kernel, handle

    def close(self):
        """Idempotent: kill owned descendants even if the worker has exited."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            if os.name == 'nt':
                if self._job is not None:
                    self._kernel.CloseHandle(self._job)
                    self._job = None
            else:
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


class WorkerControl:
    def __init__(self):
        self.cancelled = threading.Event()
        self._lock = threading.Lock()
        self._tree = None

    def attach(self, tree):
        with self._lock:
            self._tree = tree
            if self.cancelled.is_set():
                tree.close()

    def detach(self):
        with self._lock:
            self._tree = None

    def cancel(self):
        self.cancelled.set()
        with self._lock:
            if self._tree is not None:
                self._tree.close()
