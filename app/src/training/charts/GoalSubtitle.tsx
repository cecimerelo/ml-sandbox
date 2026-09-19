import type React from 'react';

/** The "what am I looking at" line, plus a bold "what good looks like" line on its own
 * row underneath — the goal a reader should check the chart against. */
export function GoalSubtitle({
  description,
  goal,
}: {
  description: string;
  goal: React.ReactNode;
}) {
  return (
    <>
      {description}
      <br />
      <strong>👀 Goal: {goal}</strong>
    </>
  );
}
