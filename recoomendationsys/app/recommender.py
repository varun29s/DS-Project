"""Hybrid reel recommender (the ML engine).

Scores candidate reels for a user by blending several normalized signals:

    score = W_TREND  * trending          (popularity x recency decay)
          + W_FOLLOW * follows_author    (social graph)
          + W_AUTHOR * author_affinity   (creators you've liked before)
          + W_TOPIC  * hashtag_overlap   (content-based)
          + W_COLLAB * collaborative     (users with similar taste)
          + W_EXPLORE* random            (diversity / exploration)

Each component is min-max normalized across the candidate pool, weighted, and
summed. Already-seen reels are excluded (with a fallback so the feed is never
empty). Pure SQL + Python — no ML libraries required.
"""
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Follow, Reel, ReelLike, ReelView

CANDIDATE_LIMIT = 500

LIKE_WEIGHT = 3.0
VIEW_WEIGHT = 1.0
HALF_LIFE_HOURS = 48.0

WEIGHTS = {
    "trending": 1.0,
    "follow": 1.6,
    "author": 1.2,
    "topic": 1.4,
    "collab": 1.5,
    "explore": 0.4,
}

REASON_TEXT = {
    "follow": "From someone you follow",
    "collab": "Liked by people with similar taste",
    "author": "More from a creator you like",
    "trending": "Popular right now",
    "explore": "Suggested for you",
}

_HASHTAG_RE = re.compile(r"#(\w+)")


def _hashtags(text: str | None) -> list[str]:
    return [h.lower() for h in _HASHTAG_RE.findall(text)] if text else []


def _normalize(values: dict[int, float]) -> dict[int, float]:
    if not values:
        return {}
    lo, hi = min(values.values()), max(values.values())
    if hi - lo < 1e-9:
        return {k: 0.0 for k in values}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def _reason(parts: dict[str, float], reel: Reel, user_topics: Counter) -> str:
    dominant = max(parts, key=parts.get)
    if dominant == "topic":
        shared = [t for t in _hashtags(reel.caption) if user_topics.get(t)]
        if shared:
            return f"Based on #{shared[0]}"
        dominant = "trending"
    if parts.get(dominant, 0) <= 0:
        return "Suggested for you"
    return REASON_TEXT.get(dominant, "Suggested for you")


def recommend(
    db: Session, user_id: int, limit: int = 20, exclude_seen: bool = True
) -> list[dict]:
    """Return ranked items: ``[{reel_id, score, reason}]`` (best first)."""
    candidates = list(
        db.scalars(
            select(Reel)
            .where(Reel.user_id != user_id)
            .order_by(Reel.created_at.desc())
            .limit(CANDIDATE_LIMIT)
        ).all()
    )
    if not candidates:
        return []
    cand_ids = [r.id for r in candidates]

    like_counts = {
        rid: c
        for rid, c in db.execute(
            select(ReelLike.reel_id, func.count())
            .where(ReelLike.reel_id.in_(cand_ids))
            .group_by(ReelLike.reel_id)
        )
    }
    view_counts = {
        rid: int(s)
        for rid, s in db.execute(
            select(ReelView.reel_id, func.coalesce(func.sum(ReelView.count), 0))
            .where(ReelView.reel_id.in_(cand_ids))
            .group_by(ReelView.reel_id)
        )
    }

    followed = set(
        db.scalars(select(Follow.following_id).where(Follow.follower_id == user_id)).all()
    )
    liked_reel_ids = set(
        db.scalars(select(ReelLike.reel_id).where(ReelLike.user_id == user_id)).all()
    )
    seen_ids = set(
        db.scalars(select(ReelView.reel_id).where(ReelView.user_id == user_id)).all()
    )

    author_affinity: Counter = Counter()
    user_topics: Counter = Counter()
    if liked_reel_ids:
        for r in db.scalars(select(Reel).where(Reel.id.in_(liked_reel_ids))):
            author_affinity[r.user_id] += 1
            for tag in _hashtags(r.caption):
                user_topics[tag] += 1

    collab_scores: dict[int, float] = defaultdict(float)
    if liked_reel_ids:
        neighbor_weights = {
            uid: w
            for uid, w in db.execute(
                select(ReelLike.user_id, func.count())
                .where(ReelLike.reel_id.in_(liked_reel_ids), ReelLike.user_id != user_id)
                .group_by(ReelLike.user_id)
            )
        }
        if neighbor_weights:
            rows = db.execute(
                select(ReelLike.reel_id, ReelLike.user_id).where(
                    ReelLike.reel_id.in_(cand_ids),
                    ReelLike.user_id.in_(list(neighbor_weights.keys())),
                )
            )
            for reel_id, neighbor_id in rows:
                collab_scores[reel_id] += neighbor_weights.get(neighbor_id, 0)

    now = datetime.now(timezone.utc)
    c_trend, c_author, c_topic, c_collab = {}, {}, {}, {}
    c_follow: dict[int, float] = {}
    for r in candidates:
        engagement = LIKE_WEIGHT * like_counts.get(r.id, 0) + VIEW_WEIGHT * view_counts.get(r.id, 0)
        created = r.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_hours = max((now - created).total_seconds() / 3600.0, 0.0)
        c_trend[r.id] = engagement * (0.5 ** (age_hours / HALF_LIFE_HOURS))
        c_follow[r.id] = 1.0 if r.user_id in followed else 0.0
        c_author[r.id] = float(author_affinity.get(r.user_id, 0))
        c_topic[r.id] = float(sum(user_topics.get(t, 0) for t in _hashtags(r.caption)))
        c_collab[r.id] = collab_scores.get(r.id, 0.0)

    n_trend = _normalize(c_trend)
    n_author = _normalize(c_author)
    n_topic = _normalize(c_topic)
    n_collab = _normalize(c_collab)

    scored = []
    for r in candidates:
        parts = {
            "trending": WEIGHTS["trending"] * n_trend.get(r.id, 0.0),
            "follow": WEIGHTS["follow"] * c_follow[r.id],
            "author": WEIGHTS["author"] * n_author.get(r.id, 0.0),
            "topic": WEIGHTS["topic"] * n_topic.get(r.id, 0.0),
            "collab": WEIGHTS["collab"] * n_collab.get(r.id, 0.0),
            "explore": WEIGHTS["explore"] * random.random(),
        }
        scored.append((r, sum(parts.values()), parts))

    fresh = [t for t in scored if t[0].id not in seen_ids] if exclude_seen else list(scored)
    if len(fresh) < limit:
        leftover = sorted(
            (t for t in scored if t[0].id in seen_ids), key=lambda t: t[1], reverse=True
        )
        fresh = fresh + leftover

    fresh.sort(key=lambda t: t[1], reverse=True)

    return [
        {"reel_id": r.id, "score": round(score, 4), "reason": _reason(parts, r, user_topics)}
        for r, score, parts in fresh[:limit]
    ]
