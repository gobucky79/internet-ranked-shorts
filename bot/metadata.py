"""Title / description / tags for a Short, built from the day's plan (plans/<slug>.json)."""
import re

BASE_TAGS = ["shorts", "funny", "funny videos", "try not to laugh", "ranking", "internet ranked", "funniest moments"]


def file_number(name):
    """'2.mp4', 'clip 2.mov', '2 - baby lemon.mp4' -> 2 (matches the numbered list in the daily package)."""
    m = re.match(r"\D*?(\d{1,2})(?!\d)", name)
    return int(m.group(1)) if m else None


def credits_for(plan, used_files):
    clips = plan.get("clips", [])
    by_n = {c.get("n"): c for c in clips}
    nums = [file_number(f) for f in used_files]
    if nums and all(n in by_n for n in nums):
        chosen = [by_n[n] for n in nums]
    else:                      # files weren't numbered: credit every channel in the plan rather than miss one
        chosen = clips
    seen, out = set(), []
    for c in chosen:
        ch = c.get("channel")
        if ch and ch not in seen:
            seen.add(ch)
            out.append(ch)
    return out


def build(plan, used_files):
    title = plan.get("title") or f"Ranking Funniest {plan.get('topic', 'Moments')}"
    if not title.lower().startswith("ranking funniest"):
        title = f"Ranking Funniest {title}"
    title = title.strip()
    if "#shorts" not in title.lower() and len(title) <= 90:
        title += " #shorts"

    channels = credits_for(plan, used_files)
    desc = plan.get("description") or f"{title.replace(' #shorts', '')} — which one got you? Comment your #1 👇"
    credit_line = "Clips: " + ", ".join(channels) if channels else ""
    if credit_line and "clips:" not in desc.lower() and "credit" not in desc.lower():
        desc = f"{desc}\n\n{credit_line}"
    if "#shorts" not in desc.lower():
        desc += "\n\n#shorts #funny #trynottolaugh"

    tags, seen = [], set()
    topic_words = [t.strip() for t in re.split(r"[,|]", plan.get("topic", "")) if t.strip()]
    for t in plan.get("tags", []) + topic_words + BASE_TAGS:
        k = t.lower().lstrip("#")
        if k and k not in seen:
            seen.add(k)
            tags.append(k)
    while len(",".join(tags)) > 480:      # YouTube caps tags at ~500 characters total
        tags.pop()
    return {"title": title, "description": desc, "tags": tags, "credits": channels}
