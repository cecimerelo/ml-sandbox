import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import { useState } from 'react';
import type React from 'react';

import { FORM_QUESTIONS } from '../copy/catalogue';
import type { RecommendationRequest, Task } from '../api/types';
import { Question } from './Question';
import {
  EXPLAINABILITY,
  FEATURES,
  FEATURE_TYPES,
  MISSING,
  ROWS,
  SUSPICION,
  TASKS,
  classBalanceOptions,
  isClassification,
  toEngineBand,
} from './options';
import type { ClassBalanceAnswer } from './options';
import type { Detection } from '../detect/types';

/** Form field to the name the detector uses when it flags one as uncertain. */
const DETECTED_FIELD: Partial<Record<keyof Answers, string>> = {
  task: 'task',
  feature_types: 'feature_types',
  missing: 'missing',
  class_balance: 'class_balance',
};

/**
 * Block 1 in advice-only mode: every answer manual and banded (FR-1.3).
 *
 * Two behaviours here are load-bearing rather than incidental.
 *
 * **Nothing recomputes on change** (FR-1.7). The dashboard updates when the user asks it
 * to, and only then. A page that rearranges itself while someone is still deciding makes
 * the answer they were about to give feel like it was already wrong.
 *
 * **Class balance is retained, not cleared.** Switching to a number hides the question;
 * switching back restores what was said. The alternative punishes a user for exploring,
 * which is the one thing the form should be safe for.
 */

type Answers = {
  task: Task | '';
  rows: string;
  features: string;
  feature_types: string;
  missing: string;
  class_balance: ClassBalanceAnswer | '';
  explainability: string;
  suspects_non_linearity: string;
  suspects_interactions: string;
};

const EMPTY: Answers = {
  task: '',
  rows: '',
  features: '',
  feature_types: '',
  missing: '',
  class_balance: '',
  explainability: '',
  suspects_non_linearity: '',
  suspects_interactions: '',
};

const copy = Object.fromEntries(FORM_QUESTIONS.map((q) => [q.id, q]));

export function ProblemForm({
  onSubmit,
  detection,
}: {
  onSubmit: (request: RecommendationRequest) => void;
  /**
   * What was read from an uploaded file, when there is one.
   *
   * The answers arrive filled in and the questions stay where they were. Rendering the
   * detections as their own block put two controls for each question on the page and left
   * the user to work out which one counted.
   */
  detection?: Detection | null;
}) {
  const [answers, setAnswers] = useState<Answers>(EMPTY);
  const [confirmed, setConfirmed] = useState<Set<string>>(new Set());
  const [filledFrom, setFilledFrom] = useState<Detection | null>(null);

  // A new reading replaces the answers it covers; the three always-asked questions are
  // untouched, because the file has nothing to say about what the user needs.
  if (detection && detection !== filledFrom) {
    setFilledFrom(detection);
    setConfirmed(new Set());
    setAnswers((current) => ({
      ...current,
      task: detection.task,
      rows: detection.rows,
      features: detection.features,
      feature_types: detection.feature_types,
      missing: detection.missing,
      class_balance:
        detection.class_balance === 'not applicable'
          ? ''
          : (detection.class_balance as ClassBalanceAnswer),
    }));
  }
  if (!detection && filledFrom) {
    // The readings go with the file they came from. Left behind, they are answers the
    // user never gave, with nothing on screen saying where they came from — and the
    // caption that used to explain them has gone with the detection.
    //
    // The three always-asked questions survive: they were the user's own answers, and a
    // file failing to load is no reason to make someone say again what they need.
    setFilledFrom(null);
    setConfirmed(new Set());
    setAnswers((current) => ({
      ...current,
      task: '',
      rows: '',
      features: '',
      feature_types: '',
      missing: '',
      class_balance: '',
    }));
  }
  const set = <K extends keyof Answers>(key: K) => (value: Answers[K]) =>
    setAnswers((current) => ({ ...current, [key]: value }));

  const classificationAsked = answers.task !== '' && isClassification(answers.task);

  // Only what is on screen can be required. The class-balance question is not missing when
  // it is not being asked, and a button that stays inert for an invisible reason is a
  // button nobody can un-stick.
  const required: (keyof Answers)[] = [
    'task',
    'rows',
    'features',
    'feature_types',
    'missing',
    'explainability',
    'suspects_non_linearity',
    'suspects_interactions',
    ...(classificationAsked ? (['class_balance'] as const) : []),
  ];
  const missing = required.filter((key) => answers[key] === '');
  const complete = missing.length === 0;

  const submit = () => {
    if (!complete) return;
    onSubmit({
      task: answers.task as Task,
      rows: answers.rows as RecommendationRequest['rows'],
      features: answers.features as RecommendationRequest['features'],
      feature_types: answers.feature_types as RecommendationRequest['feature_types'],
      missing: answers.missing as RecommendationRequest['missing'],
      // A number has no classes, so the honest value is the one that says the question
      // does not apply — not a default standing in for an answer nobody gave.
      class_balance: classificationAsked
        ? toEngineBand(answers.class_balance as ClassBalanceAnswer)
        : 'not applicable',
      explainability: answers.explainability as RecommendationRequest['explainability'],
      suspects_non_linearity:
        answers.suspects_non_linearity as RecommendationRequest['suspects_non_linearity'],
      suspects_interactions:
        answers.suspects_interactions as RecommendationRequest['suspects_interactions'],
    });
  };

  const question = (
    id: string,
    options: { value: string; label: string }[],
    key: keyof Answers,
    detail?: string,
  ) => {
    const field = DETECTED_FIELD[key];
    const unsure = Boolean(field && detection?.uncertain.includes(field) && !confirmed.has(key));
    return (
      <Question
        id={id}
        label={copy[id]?.label ?? id}
        explanation={copy[id]?.explanation ?? ''}
        options={options}
        value={answers[key]}
        onChange={(value) => {
          // Editing a flagged answer is itself a confirmation: the user has looked.
          setConfirmed((current) => new Set(current).add(key));
          set(key)(value);
        }}
        {...(detection && detail ? { detected: detail } : {})}
        {...(unsure ? { uncertain: true, onConfirm: () => setConfirmed((c) => new Set(c).add(key)) } : {})}
      />
    );
  };

  return (
    <Box component="form" onSubmit={(e) => { e.preventDefault(); submit(); }} noValidate>
      {question('form.prediction-type', TASKS, 'task', 'detected from your file')}
      {question(
        'form.rows',
        ROWS,
        'rows',
        detection ? `${detection.n_rows.toLocaleString()} rows in your file` : undefined,
      )}
      {question(
        'form.features',
        FEATURES,
        'features',
        detection ? `${detection.n_features.toLocaleString()} columns in your file` : undefined,
      )}
      {question('form.feature-types', FEATURE_TYPES, 'feature_types', 'detected from your file')}
      {question(
        'form.missing',
        MISSING,
        'missing',
        detection ? `${(detection.missing_rate * 100).toFixed(1)}% of cells are blank` : undefined,
      )}

      {/* Rendered only for categories. The answer survives being hidden. */}
      {classificationAsked &&
        question(
          'form.class-balance',
          classBalanceOptions(answers.task as Task),
          'class_balance',
          detection?.n_classes ? `${detection.n_classes} categories in your file` : undefined,
        )}

      {question('form.explainability', EXPLAINABILITY, 'explainability')}
      {question('form.non-linearity', SUSPICION, 'suspects_non_linearity')}
      {question('form.interactions', SUSPICION, 'suspects_interactions')}

      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <Tooltip
          title={
            complete ? '' : `${missing.length} question${missing.length === 1 ? '' : 's'} left`
          }
          // Describes, never labels. Left to its default, MUI makes the tooltip text the
          // button's accessible name, so a screen reader announces "8 questions left"
          // where the button says "Get Recommendation" — the reason replacing the thing.
          describeChild
        >
          {/* `aria-disabled`, not `disabled`: a disabled button is unfocusable, so the
              tooltip explaining why it is inert would be unreachable by exactly the people
              who most need it. */}
          <Button
            type="submit"
            variant="contained"
            size="large"
            aria-disabled={!complete}
            onClick={(event: React.MouseEvent) => {
              if (!complete) event.preventDefault();
            }}
            sx={{ opacity: complete ? 1 : 0.5 }}
          >
            Get Recommendation
          </Button>
        </Tooltip>
      </Box>
    </Box>
  );
}
