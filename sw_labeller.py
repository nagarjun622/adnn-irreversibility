import re
import hashlib

TEMP_TOLERANCE = 1.0          # degrees C: temperatures drift slowly as time passes
BRANCH = [5, 3, 3]            # how many undo candidates we try at depth 1, 2, 3
MAX_DEPTH = 3

# verbs we use for test actions, and verbs we allow as undo actions
ACTION_VERBS = ["open", "close", "activate", "deactivate", "pick up", "put down",
                "move", "pour", "dunk", "mix", "eat", "flush", "go to"]
UNDO_VERBS = ["open", "close", "activate", "deactivate", "pick up", "put down",
              "move", "go to"]
NO_OP_ACTION = "look around"   # costs one step of time but changes nothing
# for each verb: which verbs can plausibly undo it
INVERSE = {"open": ["close"], "close": ["open"],
           "activate": ["deactivate"], "deactivate": ["activate"],
           "pick up": ["put down", "move"], "put down": ["pick up"],
           "move": ["pick up", "move"], "go to": ["go to"]}


# ---------- comparing two world states ----------
def get_leaves(node, path=""):
    """Flatten the object tree into (path, value) pairs, ignoring IDs."""
    out = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "uuid":
                continue
            if isinstance(key, str):
                key = re.sub(r"-\d+$", "", key)
            out += get_leaves(value, path + "/" + str(key))
    elif isinstance(node, list):
        for item in node:
            out += get_leaves(item, path + "[]")
    else:
        out.append((path, node))
    return out


def collect_nodes(node, ancestors=()):
    """Walk the object tree. Returns (name, ancestor names, own properties) for every object."""
    found = []
    for child in (node.get("contents") or {}).values():
        name = child.get("name", "")
        own = {k: v for k, v in child.items() if k not in ("contents", "uuid")}
        found.append((name, ancestors, own))
        found += collect_nodes(child, ancestors + (name,))
    return found


def get_slice(env, focus):
    """The part of the world that matters for an action:
    the agent's room (and everything in it), plus every object whose name
    contains one of the `focus` words. Far-away parts of the world can change
    by themselves, so we ignore them.
    Returns (list of (key, value), temperatures by key)."""
    nodes = collect_nodes(env.getObjectTree())
    agent_room = None
    for name, ancestors, own in nodes:
        if name == "agent" and ancestors:
            agent_room = ancestors[-1]
            break

    core = []
    temps = {}
    for name, ancestors, own in nodes:
        in_agent_room = agent_room is not None and agent_room in ancestors
        mentioned = any(word in name for word in focus)
        if not (in_agent_room or mentioned):
            continue
        parent = ancestors[-1] if ancestors else "world"
        for path, value in get_leaves(own):
            key = f"{name}@{parent}{path}"
            if path.endswith("/temperatureC"):
                temps.setdefault(key, []).append(value)
            else:
                if isinstance(value, float):
                    value = round(value, 1)
                core.append((key, value))
    core.sort(key=repr)
    for key in temps:
        temps[key].sort()
    return core, temps


def get_signature(env, focus):
    """(hash of everything except temperature, temperatures by key)."""
    core, temps = get_slice(env, focus)
    text = repr((env.look(), env.inventory(), core))
    return hashlib.md5(text.encode()).hexdigest(), temps


def core_equal(sig_a, sig_b):
    """Same everything except (possibly) temperatures."""
    return sig_a[0] == sig_b[0] and sig_a[1].keys() == sig_b[1].keys()


def same_state(sig_a, sig_b, tol=TEMP_TOLERANCE):
    if not core_equal(sig_a, sig_b):
        return False
    for path in sig_a[1]:
        list_a, list_b = sig_a[1][path], sig_b[1][path]
        if len(list_a) != len(list_b):
            return False
        for x, y in zip(list_a, list_b):
            if abs(x - y) > tol:
                return False
    return True


# ---------- helpers ----------
def replay(env, task, variation, actions):
    """ScienceWorld has no save/restore, so rebuild a state by replaying."""
    env.load(task, variation, "")
    env.reset()
    for action in actions:
        env.step(action)


def verb_of(action, verbs=ACTION_VERBS):
    for verb in verbs:
        if action.startswith(verb + " "):
            return verb
    return None


def objects_from_action(action):
    """Read the objects out of the action text itself.
    'move metal pot to sink' -> ['metal pot', 'sink']"""
    verb = verb_of(action)
    if verb is None:
        return []
    rest = action[len(verb) + 1:]
    parts = re.split(r"\s+(?:to|into|in|on|from|with)\s+", rest)
    return [part.strip() for part in parts if part.strip()]


def find_parent(node, target, parent=None):
    """Name of the container that holds the object called `target`."""
    if isinstance(node, dict):
        if node.get("name") == target:
            return parent
        here = node.get("name", parent)
        for value in node.values():
            result = find_parent(value, target, here)
            if result is not None:
                return result
    elif isinstance(node, list):
        for item in node:
            result = find_parent(item, target, parent)
            if result is not None:
                return result
    return None


def pick_undo_candidates(valid_actions, objects, origins, limit, last_verb):
    """Choose a few plausible undo actions instead of trying all of them."""
    first_object = objects[0] if objects else None
    scored = []
    for action in valid_actions:
        verb = verb_of(action, UNDO_VERBS)
        if verb is None:
            continue
        mentioned = [o for o in objects
                     if re.search(r"\b" + re.escape(o) + r"\b", action)]
        if not mentioned:
            continue
        score = 1
        if first_object in mentioned:
            score += 2                      # acts on the thing that was changed
        if any(o in action for o in origins):
            score += 2                      # puts something back where it was
        if verb in INVERSE.get(last_verb, []):
            score += 3                      # the obvious opposite verb
        scored.append((score, action))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [action for _, action in scored[:limit]]


def sample_actions(valid_actions, how_many, rng, must_include=None):
    """Pick test actions, mixing different verbs."""
    by_verb = {}
    for action in valid_actions:
        verb = verb_of(action)
        if verb:
            by_verb.setdefault(verb, []).append(action)
    pool = {v: rng.sample(acts, len(acts)) for v, acts in by_verb.items()}
    chosen = []
    if must_include and must_include in valid_actions:
        chosen.append(must_include)
    while len(chosen) < how_many and any(pool.values()):
        for verb in list(pool):
            if pool[verb] and len(chosen) < how_many:
                candidate = pool[verb].pop()
                if candidate not in chosen:
                    chosen.append(candidate)
    return chosen


# ---------- the undo search ----------
def undo_search(env, task, variation, history, action, object_names=None):
    """Apply `action`, then search for a way back using at most 3 undo actions.

    The world changes by itself as time passes (a fountain fills, and so on),
    so we do NOT compare with the state before the action. We compare with the
    state we would have reached if the agent had done nothing for the same
    number of steps."""
    objects = objects_from_action(action)
    focus = objects + ["agent"]              # what we compare: these objects + the agent's room

    replay(env, task, variation, history)
    tree_before = env.getObjectTree()

    # what the world looks like after 1, 2, 3, 4 steps of doing nothing
    baselines = [None]
    for _ in range(MAX_DEPTH + 1):
        env.step(NO_OP_ACTION)
        baselines.append(get_signature(env, focus))

    lookup = objects + (["agent"] if action.startswith("go to") else [])
    origins = set()
    for obj in lookup:
        parent = find_parent(tree_before, obj)
        if parent is not None:
            origins.add(parent)
    if action.startswith("go to"):
        objects = objects + sorted(origins)   # the room we came from

    replay(env, task, variation, history)
    env.step(action)
    sig_after = get_signature(env, focus)
    result = {"changed": not same_state(sig_after, baselines[1]),
              "exact_depth": None, "partial_depth": None, "probes": 0}
    if not result["changed"]:
        return result

    seen = [sig_after]
    frontier = [[]]                          # each entry is a list of undo actions
    for depth in range(1, MAX_DEPTH + 1):
        reference = baselines[depth + 1]     # "did nothing" after the same number of steps
        next_frontier = []
        for path in frontier:
            replay(env, task, variation, history + [action] + path)
            valid = env.get_valid_action_object_combinations()
            last = path[-1] if path else action
            candidates = pick_undo_candidates(valid, objects, origins,
                                              BRANCH[depth - 1], verb_of(last))
            for i, candidate in enumerate(candidates):
                if i > 0:                    # go back to the state after `path`
                    replay(env, task, variation, history + [action] + path)
                env.step(candidate)
                result["probes"] += 1
                sig = get_signature(env, focus)
                if same_state(sig, reference):
                    result["exact_depth"] = depth
                    return result
                if core_equal(sig, reference) and result["partial_depth"] is None:
                    result["partial_depth"] = depth
                if not any(same_state(sig, s) for s in seen):
                    seen.append(sig)
                    next_frontier.append(path + [candidate])
        frontier = next_frontier
    return result


def labels_from_search(result):
    """Labels for horizons 1, 2 and 3 (how many undo actions we allow)."""
    if not result["changed"]:
        return None                           # nothing happened, nothing to label
    labels = {}
    for h in (1, 2, 3):
        if result["exact_depth"] is not None and result["exact_depth"] <= h:
            labels[h] = "reversible"
        elif result["partial_depth"] is not None and result["partial_depth"] <= h:
            labels[h] = "partial"
        else:
            labels[h] = "irreversible"
    return labels
