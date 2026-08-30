import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useState } from 'react';

import { Question } from '../form/Question';
import {
  FEATURE_TYPES,
  MISSING,
  TASKS,
  classBalanceOptions,
  isClassification,
} from '../form/options';
import type { ClassBalanceAnswer } from '../form/options';
import type { Task } from '../api/types';
import { DetectedField } from './DetectedField';
import type { Detection } from './types';
import { spacing } from '../theme/tokens';

/**
 * Shape A: what the file said, laid out for the user to confirm or correct.
 *
 * **Row and feature counts are read-only.** They are facts about the file, not opinions
 * someone can hold — a person cannot meaningfully disagree that their CSV has 388 rows,
 * and offering them the chance to would imply the reading might be a matter of taste.
 * Everything else is a judgement the file does not fully settle, so everything else is
 * editable.
 */
export function DetectedFields({
  detection,
  answers,
  onChange,
}: {
  detection: Detection;
  answers: { task: Task; feature_types: string; missing: string; class_balance: ClassBalanceAnswer | '' };
  onChange: (field: string, value: string) => void;
}) {
  const [confirmed, setConfirmed] = useState<Set<string>>(new Set());
  const confirm = (field: string) =>
    setConfirmed((current) => new Set(current).add(field));

  const uncertain = (field: string) => detection.uncertain.includes(field);
  const classificationAsked = isClassification(answers.task);

  return (
    <Box sx={{ mb: `${spacing.sectionGap}px` }}>
      {/* Read-only, and stated first: the two things the file settles outright. */}
      <DetectedField
        label="How many rows"
        detail={`${detection.n_rows.toLocaleString()} rows · ${detection.rows}`}
        detected={false}
        uncertain={false}
        confirmed
        onConfirm={() => undefined}
      >
        {detection.dropped_rows > 0 && (
          <Typography variant="body2" color="text.secondary">
            {detection.dropped_rows.toLocaleString()} row
            {detection.dropped_rows === 1 ? '' : 's'} left out — the column you are
            predicting is blank there, so there is no answer to learn from.
          </Typography>
        )}
      </DetectedField>

      <DetectedField
        label="How many columns to predict from"
        detail={`${detection.n_features.toLocaleString()} columns · ${detection.features}`}
        detected={false}
        uncertain={false}
        confirmed
        onConfirm={() => undefined}
      />

      {/* Confirmable, because the file does not settle these on its own. */}
      <DetectedField
        label="What kind of prediction"
        detail="detected from your file"
        uncertain={uncertain('task')}
        confirmed={confirmed.has('task')}
        onConfirm={() => confirm('task')}
      >
        <Question
          id="detected.task"
          label=""
          explanation=""
          options={TASKS}
          value={answers.task}
          onChange={(value) => onChange('task', value)}
        />
      </DetectedField>

      <DetectedField
        label="What kind of columns"
        detail="detected from your file"
        uncertain={uncertain('feature_types')}
        confirmed={confirmed.has('feature_types')}
        onConfirm={() => confirm('feature_types')}
      >
        <Question
          id="detected.feature_types"
          label=""
          explanation=""
          options={FEATURE_TYPES}
          value={answers.feature_types}
          onChange={(value) => onChange('feature_types', value)}
        />
      </DetectedField>

      <DetectedField
        label="How much is missing"
        detail={`${(detection.missing_rate * 100).toFixed(1)}% of cells · ${detection.missing}`}
        uncertain={uncertain('missing')}
        confirmed={confirmed.has('missing')}
        onConfirm={() => confirm('missing')}
      >
        <Question
          id="detected.missing"
          label=""
          explanation=""
          options={MISSING}
          value={answers.missing}
          onChange={(value) => onChange('missing', value)}
        />
      </DetectedField>

      {/* Hidden for a number, and its answer retained — the same rule as Shape B. */}
      {classificationAsked && (
        <DetectedField
          label="Are the categories about the same size"
          detail={
            detection.n_classes
              ? `${detection.n_classes} categories · ${detection.class_balance}`
              : 'detected from your file'
          }
          uncertain={uncertain('class_balance')}
          confirmed={confirmed.has('class_balance')}
          onConfirm={() => confirm('class_balance')}
        >
          <Question
            id="detected.class_balance"
            label=""
            explanation=""
            options={classBalanceOptions(answers.task)}
            value={answers.class_balance}
            onChange={(value) => onChange('class_balance', value)}
          />
        </DetectedField>
      )}
    </Box>
  );
}
