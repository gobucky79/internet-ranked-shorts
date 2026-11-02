"""Weekly stats bot (Sundays): how last week's Shorts did, written to reports/<date>.md.

Uses YouTube Analytics (views, % viewed, likes, subs gained per Short) and falls back to plain view counts from the
Data API if Analytics isn't available.
"""
import datetime as dt, os

from bot.google_api import Google, YT, YTA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    g = Google()
    ch = g.get(f"{YT}/channels", part="id,snippet,statistics,contentDetails", mine="true")["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = g.get(f"{YT}/playlistItems", part="contentDetails", playlistId=uploads, maxResults=50)["items"]
    ids = [i["contentDetails"]["videoId"] for i in items]
    vids = {v["id"]: v for v in g.get(f"{YT}/videos", part="snippet,statistics,status",
                                      id=",".join(ids))["items"]} if ids else {}

    end = dt.date.today()
    start = end - dt.timedelta(days=7)
    rows, analytics_ok = [], True
    try:
        rep = g.get(YTA, ids="channel==MINE", startDate=start.isoformat(), endDate=end.isoformat(),
                    metrics="views,averageViewPercentage,likes,subscribersGained", dimensions="video",
                    sort="-views", maxResults=25)
        for vid, views, pct, likes, subs in rep.get("rows", []):
            title = vids.get(vid, {}).get("snippet", {}).get("title", vid)
            rows.append((title, int(views), float(pct), int(likes), int(subs), vid))
    except Exception as e:                                  # analytics scope missing or channel too new
        analytics_ok = False
        print(f"analytics unavailable ({e}); using view totals")
        for vid, v in vids.items():
            pub = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00")).date()
            if pub >= start:
                s = v["statistics"]
                rows.append((v["snippet"]["title"], int(s.get("viewCount", 0)), None, int(s.get("likeCount", 0)),
                             None, vid))
        rows.sort(key=lambda r: -r[1])

    st = ch["statistics"]
    lines = [f"# Weekly report — {start} to {end}", "",
             f"**Channel:** {ch['snippet']['title']} · {int(st.get('subscriberCount', 0)):,} subscribers · "
             f"{int(st.get('viewCount', 0)):,} total views", ""]
    if rows:
        total = sum(r[1] for r in rows)
        lines += [f"**Views this week (top Shorts):** {total:,}", ""]
        if analytics_ok:
            lines += ["| Short | Views | Avg % viewed | Likes | Subs gained |", "|---|---:|---:|---:|---:|"]
            lines += [f"| [{t}](https://youtube.com/shorts/{v}) | {vw:,} | {p:.0f}% | {lk:,} | {sb:+,} |"
                      for t, vw, p, lk, sb, v in rows]
        else:
            lines += ["| Short (posted this week) | Views so far | Likes |", "|---|---:|---:|"]
            lines += [f"| [{t}](https://youtube.com/shorts/{v}) | {vw:,} | {lk:,} |" for t, vw, _, lk, _, v in rows]
        best = rows[0]
        lines += ["", "## Takeaways", f"- Best Short: **{best[0]}** with {best[1]:,} views."]
        if analytics_ok and len(rows) >= 3:
            held = max(rows, key=lambda r: r[2])
            low = min(rows, key=lambda r: r[2])
            lines += [f"- Held viewers best: **{held[0]}** ({held[2]:.0f}% viewed) — make more like this.",
                      f"- Lost viewers fastest: **{low[0]}** ({low[2]:.0f}% viewed) — avoid that kind of clip/topic."]
            avg = sum(r[2] for r in rows) / len(rows)
            lines.append(f"- Average viewed this week: {avg:.0f}% (over 100% means people are rewatching).")
    else:
        lines.append("No Shorts got views this week.")
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    path = os.path.join(ROOT, "reports", f"{end}.md")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
