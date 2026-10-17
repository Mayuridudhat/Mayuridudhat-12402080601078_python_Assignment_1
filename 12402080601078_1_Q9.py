"""
Q9. Threaded Job Scheduler Simulation
-------------------------------------
Run   : python Enrollment_1_Q9.py < samples/q9.in

Rules implemented
  * Higher priority runs first; equal priority -> earlier arrival; then input order.
  * A job can only start after it has arrived.
  * When several workers are free, the lowest worker id takes the job.
  * Each job occupies one worker for `duration` time units.
  * `resources` is read, validated and kept in the job record, but the
    assignment does not define a shared resource pool, so it does not
    limit scheduling (assumption stated in README).

Design
  The simulation is event-driven (deterministic), so results do not depend on
  OS thread timing.  Job hand-out goes through `JobDispatcher`, which protects
  the ready-queue with a threading.Lock - this is the synchronization point
  that would be shared by real worker threads.

Output : job_id worker start finish   (in arrival order), then AVG_WAIT x.xx

Time  : O(n log n)     Space : O(n + w)
"""
import heapq
import sys
import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    arrival: int
    job_id: str
    priority: int
    duration: int
    resources: int
    order: int          # position in the input, used as final tie-breaker


class JobDispatcher:
    """Thread-safe priority queue of ready jobs."""

    def __init__(self):
        self._heap = []
        self._lock = threading.Lock()

    def submit(self, job):
        with self._lock:
            heapq.heappush(self._heap, (-job.priority, job.arrival, job.order, job))

    def take(self):
        """Atomically remove and return the best ready job (or None)."""
        with self._lock:
            return heapq.heappop(self._heap)[3] if self._heap else None

    def empty(self):
        with self._lock:
            return not self._heap


def read_jobs(lines):
    try:
        w, n = map(int, lines[0].split())
        if not (1 <= w <= 64 and n >= 1):
            raise ValueError("w must be 1..64 and n >= 1")
        jobs = []
        for order, line in enumerate(lines[1:1 + n]):
            arrival, job_id, priority, duration, resources = line.split()
            job = Job(int(arrival), job_id, int(priority), int(duration), int(resources), order)
            if job.arrival < 0 or job.duration < 1 or job.resources < 1:
                raise ValueError(f"invalid values for job {job_id}")
            jobs.append(job)
        if len(jobs) != n:
            raise ValueError("fewer job lines than n")
    except (ValueError, IndexError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        sys.exit(1)
    return w, jobs


def simulate(w, jobs):
    """Return {job.order: (worker_id, start, finish)} and the average wait."""
    pending = sorted(jobs, key=lambda j: (j.arrival, j.order))
    workers = [(0, wid) for wid in range(1, w + 1)]      # (free_time, worker_id)
    heapq.heapify(workers)
    dispatcher = JobDispatcher()
    schedule, total_wait, i = {}, 0, 0

    while len(schedule) < len(jobs):
        free_time, worker_id = workers[0]
        now = free_time
        if dispatcher.empty() and i < len(pending):
            now = max(now, pending[i].arrival)          # idle until next arrival
        while i < len(pending) and pending[i].arrival <= now:
            dispatcher.submit(pending[i])
            i += 1
        job = dispatcher.take()
        heapq.heappop(workers)
        start, finish = now, now + job.duration
        schedule[job.order] = (worker_id, start, finish)
        total_wait += start - job.arrival
        heapq.heappush(workers, (finish, worker_id))
    return schedule, total_wait / len(jobs)


def main():
    lines = [ln for ln in sys.stdin.read().split("\n") if ln.strip()]
    w, jobs = read_jobs(lines)
    schedule, avg_wait = simulate(w, jobs)
    for job in sorted(jobs, key=lambda j: (j.arrival, j.order)):
        worker_id, start, finish = schedule[job.order]
        print(f"{job.job_id} W{worker_id} {start} {finish}")
    print(f"AVG_WAIT {avg_wait:.2f}")


if __name__ == "__main__":
    main()
