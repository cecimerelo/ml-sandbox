import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormLabel from '@mui/material/FormLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Typography from '@mui/material/Typography';

import { renderCopy } from '../copy/render';
import type { Option } from './options';
import { spacing } from '../theme/tokens';

interface Props<T extends string> {
  id: string;
  label: string;
  explanation: string;
  options: Option<T>[];
  value: T | '';
  onChange: (value: T) => void;
}

/**
 * One question, its answers, and the explanation that belongs to it.
 *
 * **The explanation is always visible** (FR-1.6) and sits close to its control — four
 * pixels below, so it reads as attached to this question rather than floating between two.
 * It is not a tooltip and not behind an icon: education that has to be asked for reaches
 * the people who already knew.
 *
 * It is also outside the tab order. A keyboard user moves field to field; making them
 * traverse prose between every control would be a tax on the people who can least afford
 * one. The text is still read by a screen reader through `aria-describedby`.
 */
export function Question<T extends string>({
  id,
  label,
  explanation,
  options,
  value,
  onChange,
}: Props<T>) {
  const explanationId = `${id}-explanation`;

  return (
    <FormControl sx={{ mb: `${spacing.fieldGap}px`, display: 'block' }}>
      <FormLabel id={`${id}-label`} sx={{ color: 'text.primary', fontWeight: 500 }}>
        {label}
      </FormLabel>
      <RadioGroup
        aria-labelledby={`${id}-label`}
        aria-describedby={explanationId}
        value={value}
        onChange={(event) => onChange(event.target.value as T)}
        row
      >
        {options.map((option) => (
          <FormControlLabel
            key={option.value}
            value={option.value}
            control={<Radio />}
            label={option.label}
          />
        ))}
      </RadioGroup>
      <Typography
        id={explanationId}
        variant="body2"
        color="text.secondary"
        sx={{ mt: 0.5 }}
      >
        {renderCopy(explanation)}
      </Typography>
    </FormControl>
  );
}
