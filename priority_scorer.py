from datetime import datetime, date


class WeightConfig:
    DEADLINE_WEIGHT = 0.5
    COMPLEXITY_WEIGHT = 0.3
    IDLE_WEIGHT = 0.2
    MAX_DEADLINE_DAYS = 30
    MAX_IDLE_DAYS = 14

    @classmethod
    def validate(cls):
        return (
            abs(cls.DEADLINE_WEIGHT + cls.COMPLEXITY_WEIGHT + cls.IDLE_WEIGHT - 1.0)
            < 0.001
        )


class PriorityResult:
    def __init__(self, task_id, score, dc, cc, ic, rank=0):
        self.task_id = task_id
        self.score = round(score, 4)
        self.deadline_component = round(dc, 4)
        self.complexity_component = round(cc, 4)
        self.idle_component = round(ic, 4)
        self.rank = rank

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "score": self.score,
            "deadline_component": self.deadline_component,
            "complexity_component": self.complexity_component,
            "idle_component": self.idle_component,
            "rank": self.rank,
        }


class PriorityScorer:
    def __init__(self, config=None):
        self.config = config or WeightConfig()

    def score(self, task):
        d = self._deadline(task)
        c = self._complexity(task)
        i = self._idle(task)
        total = (
            self.config.DEADLINE_WEIGHT * d
            + self.config.COMPLEXITY_WEIGHT * c
            + self.config.IDLE_WEIGHT * i
        )
        return PriorityResult(task["id"], total, d, c, i)

    def _deadline(self, task):
        dl = task.get("deadline")
        if not dl:
            return 0.1
        try:
            days = (date.fromisoformat(dl) - date.today()).days
            if days <= 0:
                return 1.0
            return max(
                0.0,
                min(
                    1.0,
                    (self.config.MAX_DEADLINE_DAYS - days)
                    / self.config.MAX_DEADLINE_DAYS,
                ),
            )
        except:
            return 0.1

    def _complexity(self, task):
        return max(1, min(5, int(task.get("complexity", 3)))) / 5.0

    def _idle(self, task):
        la = task.get("last_active")
        if not la:
            return 0.5
        try:
            days = (datetime.now() - datetime.fromisoformat(la)).days
            return max(0.0, min(1.0, days / self.config.MAX_IDLE_DAYS))
        except:
            return 0.5


class SuggestionEngine:
    def __init__(self, scorer=None):
        self.scorer = scorer or PriorityScorer()

    def rank_tasks(self, tasks):
        active = [t for t in tasks if t.get("status") != "COMPLETE"]
        results = sorted(
            [self.scorer.score(t) for t in active], key=lambda r: r.score, reverse=True
        )
        for i, r in enumerate(results):
            r.rank = i + 1
        return results

    def get_top_suggestion(self, tasks):
        ranked = self.rank_tasks(tasks)
        if not ranked:
            return None
        top = ranked[0]
        match = next((t for t in tasks if t["id"] == top.task_id), None)
        if match:
            match = dict(match)
            match["priority_score"] = top.score
            match["priority_result"] = top.to_dict()
        return match

    def get_ranked_list(self, tasks):
        rmap = {r.task_id: r for r in self.rank_tasks(tasks)}
        out = []
        for t in tasks:
            row = dict(t)
            if t["id"] in rmap:
                r = rmap[t["id"]]
                row["priority_score"] = r.score
                row["priority_rank"] = r.rank
                row["priority_result"] = r.to_dict()
            else:
                row["priority_score"] = 0.0
                row["priority_rank"] = 999
                row["priority_result"] = None
            out.append(row)
        return sorted(out, key=lambda x: x["priority_rank"])
