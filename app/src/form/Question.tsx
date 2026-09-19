import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormLabel from '@mui/material/FormLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Typography from '@mui/material/Typography';

import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import { renderCopy } from '../copy/render';
import type { Option } from './options';
import { chrome, spacing } from '../theme/tokens';

interface Props<T extends string> {
  id: string;
  label: string;
  explanation: string;
  options: Option<T>[];
  value: T | '';
  onChange: (value: T) => void;

  /**
   * What the file said, when there is one.
   *
   * The answer is filled in and the question stays where it was. Showing a detected value
   * beside the question it answers would put two controls for one thing on the page, and
   * the user would have to work out which one counts.
   */
  detected?: string;
  /** The file did not settle this one (FR-8.2). Cleared by editing or by saying so. */
  uncertain?: boolean;
  onConfirm?: () => void;
  /**
   * The answer contradicts something the file settles with certainty — not a judgement
   * call like `uncertain`, which the user can wave through with "Looks right". This one
   * has no such button: the file's own column type isn't a matter of opinion, so the
   * fix is to change the answer, and the caller keeps the submit button disabled while
   * this is set.
   */
  error?: string;
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
  detected,
  uncertain = false,
  onConfirm,
  error,
}: Props<T>) {
  const explanationId = `${id}-explanation`;

  return (
    <FormControl sx={{ mb: `${spacing.fieldGap}px`, display: 'block' }}>
      {/* Bold rather than medium. The label and its explanation sit four pixels apart so
          they read as one unit, and at 500 the question did not separate from the prose
          under it — the eye had nothing to anchor each block to when scanning down. */}
      <FormLabel id={`${id}-label`} sx={{ color: 'text.primary', fontWeight: 700 }}>
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
      {/* Provenance sits above the explanation, because it changes how the explanation
          should be read: a question already answered from the file is being checked, not
          answered. */}
      {error && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
          <ErrorOutlineIcon fontSize="small" aria-hidden color="error" />
          <Typography variant="body2" component="span" color="error">
            {error}
          </Typography>
        </Box>
      )}

      {uncertain && !error && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
          <WarningAmberIcon fontSize="small" aria-hidden sx={{ color: chrome.unsure.hex }} />
          <Typography variant="body2" component="span" sx={{ color: chrome.unsure.hex }}>
            We&apos;re not sure about this one — please check it.
          </Typography>
          {onConfirm && (
            <Button size="small" onClick={onConfirm}>
              Looks right
            </Button>
          )}
        </Box>
      )}

      {detected && !uncertain && !error && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
          <AutoAwesomeIcon fontSize="small" aria-hidden sx={{ color: chrome.detected.hex }} />
          <Typography variant="body2" component="span" sx={{ color: chrome.detected.hex }}>
            {detected}
          </Typography>
        </Box>
      )}

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
