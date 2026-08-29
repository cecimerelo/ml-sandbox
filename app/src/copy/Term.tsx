import Tooltip from '@mui/material/Tooltip';
import Box from '@mui/material/Box';
import { useId, useState } from 'react';

import { GLOSSARY } from './glossary';

/**
 * A term of art, marked as having a definition and carrying it.
 *
 * **The marking is the point.** A definition behind an unmarked word only reaches a reader
 * who already suspects the word means something they do not know — and someone who thinks
 * "noise" means loud sounds has no reason to suspect anything. The dotted underline says
 * "there is more here" before the reader has to work out that there might be.
 *
 * Opens on hover, on focus and on tap. Hover alone would put the definition out of reach
 * of anyone on a phone or navigating by keyboard, which is a strange thing to do to the
 * one part of the interface that exists to help people who are stuck.
 *
 * `aria-describedby` carries the definition to a screen reader whether or not the visual
 * popup ever appears.
 */
export function Term({ name }: { name: string }) {
  const entry = GLOSSARY[name];
  const id = useId();
  const [open, setOpen] = useState(false);

  // A missing entry is a copy bug, not something to paper over at runtime: silently
  // rendering the bare word would hide it from everyone except whoever wrote it.
  if (!entry) throw new Error(`No glossary entry for "${name}".`);

  return (
    <Tooltip
      title={entry.definition}
      open={open}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      describeChild
      enterTouchDelay={0}
      leaveTouchDelay={6000}
      id={id}
    >
      <Box
        component="button"
        type="button"
        aria-describedby={open ? id : undefined}
        onClick={() => setOpen((wasOpen) => !wasOpen)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        sx={{
          font: 'inherit',
          color: 'inherit',
          background: 'none',
          border: 'none',
          p: 0,
          cursor: 'help',
          // Dotted rather than solid: a solid underline reads as a link, and this does not
          // navigate anywhere.
          borderBottom: '1px dotted',
          borderColor: 'text.secondary',
        }}
      >
        {entry.term}
      </Box>
    </Tooltip>
  );
}
