"""Shot clock: the 60-day ADU decision deadline.

Gov. Code § 66317(a)(3): the permitting agency must approve or deny a completed
ADU application within 60 days when there is an existing dwelling on the lot.
Plain date math, no AI. Shown as an estimate: completeness and tolling rules vary.
"""
from dataclasses import dataclass
from datetime import date, timedelta

ADU_DECISION_DAYS = 60


@dataclass
class ShotClock:
    complete_date: date
    due_date: date
    days_left: int  # negative = overdue

    @property
    def overdue(self) -> bool:
        return self.days_left < 0

    def summary(self) -> str:
        if self.overdue:
            return (f"Application complete {self.complete_date:%b %d, %Y}. The city had to approve or deny "
                    f"by {self.due_date:%b %d, %Y}: {-self.days_left} days overdue (Gov. Code § 66317(a)(3)).")
        return (f"Application complete {self.complete_date:%b %d, %Y}. The city must approve or deny "
                f"by {self.due_date:%b %d, %Y}: {self.days_left} days left (Gov. Code § 66317(a)(3)).")


def shot_clock(complete_date: date, today: date | None = None, days: int = ADU_DECISION_DAYS) -> ShotClock:
    today = today or date.today()
    due = complete_date + timedelta(days=days)
    return ShotClock(complete_date=complete_date, due_date=due, days_left=(due - today).days)


if __name__ == "__main__":
    c = shot_clock(date(2026, 8, 1), today=date(2026, 11, 7))
    assert c.due_date == date(2026, 9, 30) and c.overdue and c.days_left == -38, c
    c2 = shot_clock(date(2026, 10, 1), today=date(2026, 11, 7))
    assert not c2.overdue and c2.days_left == 23, c2
    print("deadlines.py OK:", c.summary())
