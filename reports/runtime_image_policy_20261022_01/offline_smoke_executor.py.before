"""Bounded PowerShell boundary executor. Admission disabled; mock tests only."""
import os
from pathlib import Path
import subprocess
import time
import uuid

EXECUTION_ADMITTED = False


def construct_boundary_backend(*, receipt, **executor_arguments):
    if not EXECUTION_ADMITTED:
        raise RuntimeError('PowerShell boundary construction not admitted')
    executor = PowerShellBoundaryExecutor(**executor_arguments)
    from scripts.matched_baseline.offline_smoke_windows_backend import WindowsBoundaryBackend
    # The existing backend's injected-executor interface is shared, not a claim
    # of synthetic operation. This factory binds the genuine implementation.
    return WindowsBoundaryBackend(powershell_path=executor.program,script_path=executor.script,
        receipt=receipt,executor=executor)


class PowerShellBoundaryExecutor:
    def __init__(self, *, powershell_path, script_path, evidence_directory,
                 environment, timeout_seconds=30, output_limit_bytes=1024*1024,
                 process_factory=None, clock=None, pause=None):
        if not EXECUTION_ADMITTED:
            raise RuntimeError('PowerShell executor not admitted')
        self.program,self.script = str(powershell_path),str(script_path)
        if not Path(self.program).is_absolute() or not Path(self.script).is_absolute():
            raise ValueError('Absolute PowerShell and script paths required')
        self.directory = Path(evidence_directory)
        if not self.directory.is_absolute() or not self.directory.is_dir():
            raise ValueError('Existing absolute evidence directory required')
        if type(timeout_seconds) is not int or timeout_seconds <= 0 or type(output_limit_bytes) is not int or output_limit_bytes <= 0:
            raise ValueError('Positive executor limits required')
        if type(environment) is not dict or any(type(k) is not str or type(v) is not str or not k or '=' in k or '\0' in k+v for k,v in environment.items()):
            raise ValueError('Explicit valid executor environment required')
        if len({key.upper() for key in environment}) != len(environment):
            raise ValueError('Duplicate executor environment key')
        if process_factory is None and os.name != 'nt':
            raise RuntimeError('Windows executor required')
        from scripts.matched_baseline.offline_preflight import CleanChildEnvironmentBuilder
        self.environment = {key.upper():value for key,value in CleanChildEnvironmentBuilder.build(environment).items()
                            if key.upper() not in {'PYTHONPATH','PYTHONHOME'}}
        self.timeout,self.limit = timeout_seconds,output_limit_bytes
        self.factory,self.clock,self.pause = process_factory or subprocess.Popen,clock or time.monotonic,pause or time.sleep

    def __call__(self, command):
        if not EXECUTION_ADMITTED:
            raise RuntimeError('PowerShell executor not admitted')
        if type(command) is not list or len(command) != 9 or command[:5] != [self.program,'-NoProfile','-NonInteractive','-File',self.script] or command[5] != '-Operation' or command[6] not in {'environment','query','create','remove'} or command[7] != '-PayloadBase64' or any(type(arg) is not str or '\0' in arg for arg in command):
            raise ValueError('Unreviewed boundary command')
        from scripts.matched_baseline.offline_preflight import IntegrityLifecycleManager
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(self.directory)
        stem = self.directory/('boundary_'+command[6]+'_'+uuid.uuid4().hex)
        outpath,errpath = Path(str(stem)+'.stdout'),Path(str(stem)+'.stderr')
        process = None
        with outpath.open('xb') as stdout,errpath.open('xb') as stderr:
            try:
                process = self.factory(command,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                    env=dict(self.environment),shell=False,close_fds=True,creationflags=0x08000000)
                started = self.clock()
                while True:
                    if outpath.stat().st_size+errpath.stat().st_size > self.limit:
                        raise RuntimeError('Boundary output limit exceeded')
                    code = process.poll()
                    if code is not None:
                        break
                    if self.clock()-started >= self.timeout:
                        raise TimeoutError('Boundary operation timeout')
                    self.pause(0.02)
            except BaseException:
                if process is not None:
                    # Only this owned PowerShell process is terminated. No tree
                    # guarantee is claimed; reviewed script must not spawn tools.
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=5)
                raise
        rawout,rawerr = outpath.read_bytes(),errpath.read_bytes()
        if len(rawout)+len(rawerr) > self.limit:
            raise RuntimeError('Boundary output limit exceeded')
        if type(code) is not int:
            raise RuntimeError('Invalid PowerShell exit status')
        return code,rawout.decode('utf-8-sig',errors='strict'),rawerr.decode('utf-8-sig',errors='strict')
