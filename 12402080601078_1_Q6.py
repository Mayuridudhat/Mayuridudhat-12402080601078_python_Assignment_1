"""
Q6. Python Module Dependency Resolver
-------------------------------------
Run   : python Enrollment_1_Q6.py < samples/q6.in

Edge line "A imports B" (the word "imports" is optional - the first and last
word of the line are used) means B must be loaded before A.

* Kahn's algorithm with a min-heap -> lexicographically smallest valid order.
* Duplicate edges are ignored with a set.
* If some modules can never be loaded, a cycle exists.  One cycle is found by
  starting at the smallest unloaded module and repeatedly following an import
  to another unloaded module until a module repeats.

Output : the loading order on one line, or
         CYCLE
         m1 m2 ... mk      (m1 imports m2, ..., mk imports m1)

Time  : O((n + e) log n)     Space : O(n + e)
"""
import heapq
import sys


def resolve(modules, edges):
    """Return ('ORDER', [..]) or ('CYCLE', [..])."""
    deps = {m: [] for m in modules}          # module -> modules it imports
    dependents = {m: [] for m in modules}    # module -> modules that import it
    for importer, imported in edges:
        for name in (importer, imported):    # tolerate modules missing from the list
            if name not in deps:
                deps[name] = []
                dependents[name] = []
        deps[importer].append(imported)
        dependents[imported].append(importer)

    unmet = {m: len(d) for m, d in deps.items()}
    ready = [m for m, c in unmet.items() if c == 0]
    heapq.heapify(ready)

    order = []
    while ready:
        module = heapq.heappop(ready)
        order.append(module)
        for importer in dependents[module]:
            unmet[importer] -= 1
            if unmet[importer] == 0:
                heapq.heappush(ready, importer)

    if len(order) == len(deps):
        return "ORDER", order

    # ---- cycle extraction: every unloaded module imports another unloaded one
    loaded = set(order)
    current = min(m for m in deps if m not in loaded)
    position, path = {}, []
    while current not in position:
        position[current] = len(path)
        path.append(current)
        current = min(d for d in deps[current] if d not in loaded)
    return "CYCLE", path[position[current]:]


def main():
    lines = sys.stdin.read().split("\n")
    try:
        n, e = map(int, lines[0].split())
        modules = [ln.strip() for ln in lines[1:1 + n]]
        edge_set = set()                       # removes duplicate imports
        for line in lines[1 + n: 1 + n + e]:
            words = line.split()
            if len(words) < 2:
                raise ValueError(f"bad edge line: {line!r}")
            edge_set.add((words[0], words[-1]))
    except (ValueError, IndexError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        sys.exit(1)

    kind, result = resolve(set(modules), sorted(edge_set))
    if kind == "ORDER":
        print(" ".join(result))
    else:
        print("CYCLE")
        print(" ".join(result))


if __name__ == "__main__":
    main()
