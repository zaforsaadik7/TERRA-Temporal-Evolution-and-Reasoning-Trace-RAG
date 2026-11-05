"""Parent composition, synthetic dependencies only; no production CLI enabled."""
from scripts.matched_baseline.offline_smoke_runner import SmokeRunner
from scripts.matched_baseline.offline_smoke_windows_assembly import assemble_windows_dispatch


def assemble_parent_runner(*, kernel, cwd, clock, pause, runner_arguments,
                           is_synthetic=True):
    if is_synthetic is not True:
        raise RuntimeError('Authentic parent assembly not admitted')
    if type(runner_arguments) is not dict or 'execute_child' in runner_arguments or 'is_synthetic' in runner_arguments:
        raise ValueError('Parent owns child dispatch and execution mode')
    config = runner_arguments['config']
    attempted = False

    def dispatch(receipt, capture_path, child_config, environment):
        nonlocal attempted
        if attempted:
            raise RuntimeError('Parent child dispatch retry forbidden')
        attempted = True
        if child_config is not config:
            raise ValueError('Parent/child configuration identity mismatch')
        # Called only by SmokeRunner after its approval, integrity, boundary,
        # lock and saved-request stages. No eager capture/API construction.
        child_dispatch = assemble_windows_dispatch(kernel=kernel,cwd=cwd,
            capture_path=capture_path,config=config,clock=clock,pause=pause)
        return child_dispatch(receipt,capture_path,config,environment)

    return SmokeRunner(**runner_arguments,execute_child=dispatch,is_synthetic=True)


def main(argv=None):
    print('BLOCKED: authentic parent admission and frozen packet pending')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
